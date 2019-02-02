#!/usr/bin/python3

import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)
import pandas as pd
import re
import itertools
import pdftotext
import click
import os

# Set encoding to be sure we're using UTF-8 and not ascii. Note this is the proper encoding for US only.
os.environ["LC_ALL"] = "en_US.utf-8"

@click.command()
@click.version_option('1.0')
@click.argument('input_files', nargs=-1, required=1)
@click.argument('output_file', nargs=1, required=1)
def parse_pdf(input_files, output_file):
    """Convert AccuVote OS Ballot PDF to CSV

    Examples:
        python3 cvr-parser.py INPUT_FILE OUTPUT_FILE
        python3 cvr-parser.py INPUT_FILE1 INPUT_FILE2 INPUT_FILE3 OUTPUT_FILE
    """

    # Every file returns a dataframe and stores it in this list
    file_dataframes = []
    for input_file in input_files:
        with open(input_file, "rb") as f:
            pdf = pdftotext.PDF(f)

        # Every page returns a dataframe. They are all stored in this list
        page_dataframes = []
        for page in pdf:
            page_lines = page.split('\n')

            # We'll be separating the columns first and putting them in separate lists
            col1 = []
            col2 = []

            for line in page_lines:
                # This is the part of the whole line where it is possible that the next column could start
                col2_line_target = line[30:]
                # Searching through the right (target) half of the line for delimiters that mark second column start
                split_dict = re.split('(\[ \]|\[X\]|Vote For|UNDERVOTE|\d+ - )', col2_line_target)
                col2_row = ''
                # Sometimes we only have one column. In that case we move on, but if split_dict>1, we know there are two.
                if len(split_dict)>1:
                    # Taking note of the delimiter so we can use it to split the line
                    split_delimiter = ''.join(split_dict[-2:])
                    col2_row = split_dict[-2:]
                    col2_row = ''.join(col2_row).strip()
                    # Get the left half by delimiting on right half
                    left_half = line.split(split_delimiter)
                    if len(left_half)>1:
                        col1_row = ''.join(left_half).strip()
                else:
                    # No processing if there is only one column
                    col1_row = line.strip()
                # Build the column lists up line by line
                col1.append(col1_row)
                col2.append(col2_row)

            # Header info is always first two rows of first column
            header1 = col1[0]
            header2 = col1[1]

            # These are the columns with extraneous header/space removed
            col1_only = col1[2:]
            col2_only = col2[2:]
            # Create line lists and a giant string for the whole page
            col_concat = col1_only + col2_only
            contests_string = '\n'.join(col_concat)

            # Find all contest names with regex. They always look like "10 - U.S. President". Just to be safe we are doing
            # lookahead for a new line at the end.
            contest_names = re.findall('\d+ - .+(?=\n)', contests_string)
            # Clever way to group the line list up into contests on a delimiter.
            contest_bodies = [list(y) for x, y in itertools.groupby(col_concat, lambda z: re.search('^\d+ - \w+', z)) if not x]

            parsed_contests = []
            # Iterate through each contest, find the option chosen designated by [X] string
            for i, contest_name in enumerate(contest_names):
                contest_body = contest_bodies[i]
                # Handles the case where there is no option_chosen
                option_chosen = ''
                for option in contest_body:
                    if '[X]' in option or 'UNDERVOTE' in option:
                        option_chosen = option.replace('[X]', '').strip()
                # Creating a list of contest results and appending it to a list of all contests on page which easily converts to dataframe
                contest_result = [
                    contest_name,
                    option_chosen,
                ]
                parsed_contests.append(contest_result)

            # Convert to dataframe and transpose
            df_contests = pd.DataFrame(parsed_contests).T

            # Turning the first row into the header
            df_contests.columns = df_contests.iloc[0]
            # Removing extraneous first row now that it is the header
            df_contests = df_contests.loc[1].T

            # Adding in the header strings we gathered before
            df_contests['HeaderLine1'] = header1
            df_contests['HeaderLine2'] = header2

            #Adding this page's dataframe to the big list of page dataframes
            page_dataframes.append(df_contests)

        # Combine all page dataframes into one huge document dataframe, transpose
        df_page = pd.concat(page_dataframes, axis=1).T

        # Append file dataframe to list of all file dataframes
        file_dataframes.append(df_page)

    # Combine all file dataframes into a big dataframe
    df_files = pd.concat(file_dataframes)
    
    # Removing header columns so subsequent columns can be sorted by their beginning numbers
    cols = [column for column in df_files.columns if 'Header' not in column]
    sorted_cols = sorted(cols, key=lambda x: int(re.sub("\D", "", x.split(' - ')[0])))

    # Add the header columns back to the beginning of the column list
    sorted_cols = ['HeaderLine1', 'HeaderLine2'] + sorted_cols

    # Applying column list to the dataframe
    df_files = df_files[sorted_cols]

    # Generate output_file csv without default numbered index column
    df_files.to_csv(output_file, index=False)
    input_file_count = len(input_files)

    if input_file_count == 1:
        pluralize_file = 'file'
    else:
        pluralize_file = 'files'

    success_string = f'Successfully converted {input_file_count} {pluralize_file} ({df_files.HeaderLine1.count()} ballots).'
    click.echo(success_string)

if __name__ == "__main__":
    parse_pdf()