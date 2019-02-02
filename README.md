# cvr-parser
App to parse and transform Cast Vote Record files.

## Requirements
- Python 3
- pandas
- click
- pdftotext

## Installation
Install platform-specific pdftotext library dependencies according to [pdftotext docs](https://pypi.org/project/pdftotext/)
```bash
pip3 install pdftotext
pip3 install pandas click
```

## Usage
Parse one or many input pdf's into one output csv.

```bash
cvr-parser.py [OPTIONS] INPUT_FILES... OUTPUT_FILE
Options:
  --version  Show the version and exit.
  --help     Show this message and exit.
```

## Examples
```bash
cvr-parser.py INPUT_FILE OUTPUT_FILE
cvr-parser.py INPUT_FILE1 INPUT_FILE2 INPUT_FILE3 OUTPUT_FILE
```

