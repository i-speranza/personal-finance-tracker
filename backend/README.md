# Personal Finance Tracker - Backend

Backend API and data processing for the Personal Finance Tracker application.

## Overview

This backend handles:
- Transaction preprocessing from bank-specific file formats
- Database models and schemas
- API endpoints (to be implemented)
- Legacy data migration

## Installation

```bash
# Install dependencies
poetry install

# Or with pip
pip install -r requirements.txt
```

## Database

The application uses SQLite by default. The database file is stored in `data/finance.db`.

To initialize the database:
```bash
python run.py
```

## Transaction Preprocessing

The backend supports parsing transaction files from different banks. Currently supported banks:
- **Intesa**: Parses Excel files with specific format
- **Allianz**: Parses Excel files with specific format

### Usage

```python
from pathlib import Path
from app.transactions_preprocessing import TransactionsFileParser
from app.transactions_preprocessing_intesa import IntesaParser
from app.transactions_preprocessing_allianz import AllianzParser

# Register parsers
intesa_parser = IntesaParser()
allianz_parser = AllianzParser()
register_transactions_parser(intesa_parser)
register_transactions_parser(allianz_parser)

# Parse a file
parser = TransactionsFileParser()
df = parser.parse_file(Path("path/to/file.xlsx"), bank_name="intesa")
```

## Legacy Data Migration

⚠️ **IMPORTANT**: The `migrate_legacy.py` script is **very use-case specific and personal**. It is designed to migrate legacy transaction data from a specific CSV format that may not be applicable to other users.

### CSV Format

The migration script expects a CSV file with the following columns:
- `Date`: Transaction date
- `Operazione`: Operation description (bank-specific)
- `Dettagli`: Additional details
- `Tipo_transazione`: Transaction type indicator
- `Categoria`: Transaction category
- `Importo`: Transaction amount
- `Transazione_speciale`: Special transaction flag (boolean-like)
- `Banca`: Bank name (should be "intesa", "banca intesa", or "allianz")

### Usage

```bash
# Generate preview only (does not insert to database)
python backend/scripts/migrate_legacy.py path/to/legacy_transactions.csv --preview-only

# Migrate with confirmation prompt
python backend/scripts/migrate_legacy.py path/to/legacy_transactions.csv

# Migrate without confirmation prompt
python backend/scripts/migrate_legacy.py path/to/legacy_transactions.csv --force
```

### Process

1. **Read CSV**: The script reads the legacy CSV file
2. **Preprocessing**: Applies bank-specific preprocessing:
   - **Intesa**: Uses `_extract_description_intesa` and `_extract_transaction_type_intesa` functions
   - **Allianz**: Uses `_extract_description_allianz` function
3. **Preview**: Generates a preview CSV file (`migrated_transactions_preview.csv`) and prints summary statistics
4. **Database Insertion**: Inserts transactions into the database, skipping duplicates based on:
   - `bank_name`
   - `date`
   - `amount`
   - `description`

### Output

- **Preview CSV**: Saved to `backend/scripts/migrated_transactions_preview.csv`
- **Summary**: Printed to console showing:
  - Total transactions
  - Date range
  - Bank distribution
  - Transaction types
  - Special transactions count
  - Total amount
- **Errors**: Any rows that could not be processed are logged with details

### Notes

- Duplicate transactions (same bank, date, amount, description) are automatically skipped
- Rows that fail processing are logged but don't stop the migration
- The script validates required columns before processing
- Date and amount formats are automatically normalized

## Development

### Project Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── database.py          # Database connection and session
│   ├── models.py            # SQLAlchemy models
│   ├── schemas.py           # Pydantic schemas
│   ├── main.py              # FastAPI application
│   ├── transactions_preprocessing.py        # Base parser classes
│   ├── transactions_preprocessing_intesa.py # Intesa bank parser
│   └── transactions_preprocessing_allianz.py # Allianz bank parser
├── scripts/
│   └── migrate_legacy.py    # Legacy data migration script
├── examples/                # Example transaction files
└── README.md                # This file
```

## License

[Add your license here]
