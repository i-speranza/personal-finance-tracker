# Example Files

This directory contains example transaction files for testing and demonstration purposes.

## Purpose

- **Testing**: Use these files to test your preprocessing code
- **Documentation**: Demonstrate how the app handles different file formats
- **Development**: Reference files for developing new bank parsers

## Important Notes

⚠️ **Never commit real personal financial data to version control!**

- Use anonymized data only
- Replace real account numbers with fake ones
- Use sample transaction amounts
- Remove or anonymize any personal identifiers

## Usage

Example code to load and test with these files:

```python
from pathlib import Path
from app.file_reader import FileReader
from app.transactions_preprocessing import TransactionsFileParser

# Load an example file
example_path = Path(__file__).parent / "example_transactions.xlsx"
reader = FileReader()
df = reader.read_file(example_path)

# Parse it
parser = TransactionsFileParser()
transactions = parser.parse_file(example_path)
```
