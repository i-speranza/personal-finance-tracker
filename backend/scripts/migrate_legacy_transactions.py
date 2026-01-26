"""
One-time migration script from CSV files.

This script is very use-case specific and personal. It migrates legacy transaction
data from a CSV file with specific column structure, applying bank-specific preprocessing
for Intesa and Allianz banks.

Expected CSV columns:
- Date, Operazione, Dettagli, Tipo_transazione, Categoria, Importo, Transazione_speciale, Banca
"""
import sys
import argparse
import logging
from pathlib import Path
from typing import Optional
from datetime import date, datetime
import pandas as pd

# Add parent directory to path to import app modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import SessionLocal, engine, Base
from app import models  # noqa: F401 - Import to register models with Base
from app.models import Transaction
from app.transaction_type_mappings import (
    TRANSACTION_MAP_INTESA,
    TRANSACTION_MAP_ALLIANZ,
    DEFAULT_TRANSACTION_TYPE_INTESA,
    DEFAULT_TRANSACTION_TYPE_ALLIANZ,
    CARTA_PREPAGATA,
    PAGAMENTO_CON_CARTA
)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def _extract_description_intesa(operazione: str, dettagli: str, tipo_transazione: str) -> str:
    """
    Extract the description from the operation and details for Intesa bank.
    
    Note: In the original parser, this used 'conto_o_carta' but for legacy CSV,
    we use 'tipo_transazione' which should contain similar information.
    """
    if "Conto" in tipo_transazione or tipo_transazione.strip() == "":
        if operazione.strip().upper() == "ACCREDITO BEU CON CONTABILE":
            return dettagli
        if "Addebito Diretto" in operazione:
            return operazione
        if "Carta N." in dettagli:
            return "Pagam. POS - " + operazione
        if "Bonifico Disposto A Favore Di" in operazione or "Bonifico Istantaneo Da Voi Disposto A Favore Di" in operazione:
            # keep everything in details after "Bonifico Da Voi Disposto A Favore Di"
            if "Bonifico Da Voi Disposto A Favore Di" in dettagli:
                return "Bonifico a " + dettagli.split("Bonifico Da Voi Disposto A Favore Di")[1].strip()
            return "Bonifico a " + dettagli
        if "Bonifico Disposto Da" in operazione or "Bonifico Istantaneo Disposto Da" in operazione:
            # dettagli string is like "COD.[]DISP. [16 digits] [CASH/OTHR/SECU] [reason] Bonifico A Vostro Favore"
            # we need to extract the reason
            if "Bonifico A Vostro Favore" in dettagli:
                reason = dettagli[:32].split("Bonifico A Vostro Favore")[0].strip()
                return operazione + " - " + reason
            return operazione + " - " + dettagli
        if "canone" in operazione.lower():
            return operazione.capitalize() + " - " + dettagli
        if "imposta di bollo" in operazione.lower():
            return operazione.capitalize() + " - " + dettagli
        if "investimento" in operazione.lower():
            return "Investimento" + " - " + dettagli
        if "BANCOMAT PAY" in operazione.upper():
            return "BANCOMAT Pay - " + dettagli
        if "Pagamento Delega F24" in operazione or "Pagamento Mav" in operazione:
            return operazione + " - " + dettagli
        if "premio polizza" in operazione.lower():
            return operazione.capitalize() + " - " + dettagli.capitalize()
        if "stipendio" in operazione.lower():
            if "STIPENDIO" in dettagli:
                salary_info = dettagli.split("STIPENDIO")[1].strip()
                salary_info = salary_info.split("Bonifico A Vostro Favore")[0].strip()
                return "Stipendio" + " - " + salary_info
            return "Stipendio" + " - " + dettagli
        if "assegn" in operazione.lower():
            return operazione + " - " + dettagli
    else:
        if "SUPERFLASH" not in tipo_transazione.upper():
            logger.warning(f"Could not extract description for operazione: {operazione} with details: {dettagli} and tipo_transazione: {tipo_transazione}. Defaulting to details.")
        return dettagli
    
    # Default fallback
    return dettagli if dettagli else operazione


def _extract_transaction_type_intesa(operazione: str, dettagli: str, tipo_transazione: str) -> str:
    """
    Extract the transaction type from the operation and details for Intesa bank.
    
    Uses TRANSACTION_MAP_INTESA to map operazione.lower() to transaction type.
    Checks for substring matches in the mapping keys.
    
    Note: In the original parser, this used 'conto_o_carta' but for legacy CSV,
    we use 'tipo_transazione' which should contain similar information.
    """
    operazione_lower = operazione.lower().strip()
    
    # Check if it's a card payment (not from account)
    if tipo_transazione and "Conto" not in tipo_transazione and tipo_transazione.strip() != "":
        return CARTA_PREPAGATA
    
    # Special case: check for "Carta N." in dettagli (this is checked in dettagli, not operazione)
    if dettagli and "Carta N." in dettagli:
        return TRANSACTION_MAP_INTESA.get("carta n.", PAGAMENTO_CON_CARTA)
    
    # Try exact match first
    if operazione_lower in TRANSACTION_MAP_INTESA:
        return TRANSACTION_MAP_INTESA[operazione_lower]
    
    # Try substring matches (check if any mapping key is contained in operazione_lower)
    # Sort by length (longest first) to match more specific patterns first
    for key in sorted(TRANSACTION_MAP_INTESA.keys(), key=len, reverse=True):
        if key in operazione_lower:
            return TRANSACTION_MAP_INTESA[key]
    
    # Default fallback
    return tipo_transazione if tipo_transazione else DEFAULT_TRANSACTION_TYPE_INTESA


def _extract_description_allianz(operazione: str) -> str:
    """
    Extract the description from the operation for Allianz bank.
    """
    details = operazione
    transaction_type = details.split('-')[0].strip()

    if transaction_type == "Pagam. POS":
        # split on dash, take the second part and keep only the part after "ORE"
        if len(details.split('-')) > 1 and 'ORE' in details.split('-')[1]:
            time_info = "ORE " + details.split('-')[1].strip().split('ORE')[1].strip()
            # split on dash, take the third part and keep only the part before "CARTA"
            if len(details.split('-')) > 2:
                transaction_info = details.split('-')[2].strip().split('CARTA')[0].strip()
                return "POS" + " - " + transaction_info + " - " + time_info
        return "POS" + " - " + details
    elif transaction_type == "Addeb. diretto":
        # split on dash, take the second part
        if len(details.split('-')) > 1:
            return "Addeb. diretto" + " - " + details.split('-')[1].strip()
        return "Addeb. diretto" + " - " + details
    elif transaction_type == "Bancomat":
        # split on dash, take the second part and keep only the part after "ORE" and before "CARTA"
        if len(details.split('-')) > 1 and 'ORE' in details.split('-')[1]:
            transaction_info = "ORE " + details.split('-')[1].strip().split('ORE')[1].strip()
            transaction_info = transaction_info.split('CARTA')[0].strip()
            return "Prelievo contanti" + " - " + transaction_info
        return "Prelievo contanti" + " - " + details
    elif transaction_type == "Bonif. v/fav.":
        # remove the word starting with "RIF:"
        return (' '.join([word for word in details.split() if not word.startswith("RIF:")])).replace("Bonif. v/fav.", "Bonif. ricevuto")
    elif transaction_type == "Disposizione":
        # remove the word starting with "RIF:"
        return (' '.join([word for word in details.split() if not word.startswith("RIF:")])).replace("Disposizione", "Bonif. effettuato")
    else:
        return ' '.join(details.split())

def _extract_transaction_type_allianz(operazione: str) -> str:
    """
    Extract the transaction type from operazione for Allianz bank.
    
    Uses TRANSACTION_MAP_ALLIANZ to map transaction_type.lower() (first part before dash)
    to standardized transaction type.
    """
    if '-' in operazione:
        transaction_type = operazione.split('-')[0].strip()
        transaction_type_lower = transaction_type.lower()
        
        # Look up in mapping
        if transaction_type_lower in TRANSACTION_MAP_ALLIANZ:
            return TRANSACTION_MAP_ALLIANZ[transaction_type_lower]
        
        # If not found, return the original transaction_type
        return transaction_type
    else:
        # No dash, return the whole operazione stripped or default
        return operazione.strip() if operazione else DEFAULT_TRANSACTION_TYPE_ALLIANZ


def normalize_date(date_value) -> date:
    """
    Normalize various date formats to date object.
    """
    if isinstance(date_value, date):
        return date_value
    if isinstance(date_value, datetime):
        return date_value.date()
    if pd.isna(date_value):
        raise ValueError("Date value is NaN")
    
    # Try parsing as string
    if isinstance(date_value, str):
        try:
            # Try common date formats
            for fmt in ["%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y", "%d-%m-%Y", "%Y/%m/%d", "%d.%m.%Y"]:
                try:
                    return datetime.strptime(date_value.strip(), fmt).date()
                except ValueError:
                    continue
            # Fallback to pandas parsing
            return pd.to_datetime(date_value).date()
        except Exception as e:
            logger.warning(f"Could not parse date '{date_value}': {e}")
            raise ValueError(f"Invalid date format: {date_value}")
    
    # Try pandas conversion
    try:
        return pd.to_datetime(date_value).date()
    except Exception as e:
        raise ValueError(f"Could not convert to date: {date_value} - {e}")


def normalize_amount(amount_value) -> float:
    """
    Normalize various amount formats to float.
    """
    if pd.isna(amount_value):
        raise ValueError("Amount value is NaN")
    
    if isinstance(amount_value, (int, float)):
        return float(amount_value)
    
    if isinstance(amount_value, str):
        # Remove currency symbols, commas, spaces
        cleaned = amount_value.strip().replace(",", ".").replace(" ", "")
        # Remove common currency symbols
        for symbol in ["$", "€", "£", "₹", "Rs", "rs", "EUR", "eur"]:
            cleaned = cleaned.replace(symbol, "")
        
        try:
            return float(cleaned)
        except ValueError as e:
            raise ValueError(f"Could not convert amount '{amount_value}' to float: {e}")
    
    try:
        return float(amount_value)
    except Exception as e:
        raise ValueError(f"Could not convert to float: {amount_value} - {e}")


def process_legacy_csv(csv_path: Path) -> pd.DataFrame:
    """
    Read and process the legacy CSV file, applying bank-specific preprocessing.
    
    Returns:
        DataFrame with standardized transaction columns
    """
    logger.info(f"Reading CSV file: {csv_path}")
    
    # Read CSV
    try:
        df = pd.read_csv(csv_path)
    except Exception as e:
        logger.error(f"Error reading CSV file: {e}")
        raise
    
    # Validate required columns
    required_columns = ['Date', 'Operazione', 'Dettagli', 'Tipo_transazione', 
                       'Categoria', 'Importo', 'Transazione_speciale', 'Banca']
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        raise ValueError(f"Missing required columns: {missing_columns}")
    
    logger.info(f"Found {len(df)} rows in CSV")
    
    # Process each row
    processed_rows = []
    error_rows = []
    
    for idx, row in df.iterrows():
        try:
            # Get bank name and normalize
            bank_name = str(row['Banca']).strip().lower()
            
            # Normalize date
            trans_date = normalize_date(row['Date'])
            
            # Normalize amount
            amount = normalize_amount(row['Importo'])
            
            # Get category
            category = str(row['Categoria']).strip() if pd.notna(row['Categoria']) else None
            
            # Get is_special (convert to boolean)
            is_special = False
            if pd.notna(row['Transazione_speciale']):
                trans_spec = str(row['Transazione_speciale']).strip().lower()
                is_special = trans_spec in ['true', '1', 'yes', 'sì', 'si']
            
            # Apply bank-specific preprocessing
            operazione = str(row['Operazione']).strip() if pd.notna(row['Operazione']) else ""
            dettagli = str(row['Dettagli']).strip() if pd.notna(row['Dettagli']) else ""
            tipo_transazione = str(row['Tipo_transazione']).strip() if pd.notna(row['Tipo_transazione']) else ""
            
            # Get details based on bank
            # For Intesa: details from Dettagli column
            # For Allianz: details from Operazione column
            if bank_name == "intesa" or bank_name == "banca intesa":
                details = dettagli
                description = _extract_description_intesa(operazione, dettagli, tipo_transazione)
                transaction_type = _extract_transaction_type_intesa(operazione, dettagli, tipo_transazione)
            elif bank_name == "allianz":
                details = operazione
                description = _extract_description_allianz(operazione)
                transaction_type = _extract_transaction_type_allianz(operazione)
            else:
                logger.error(f"Unknown bank '{bank_name}' for row {idx}, using raw data")
                continue
            
            processed_rows.append({
                'bank_name': bank_name,
                'date': trans_date,
                'amount': amount,
                'description': description,
                'details': details,
                'category': category,
                'transaction_type': transaction_type,
                'is_special': is_special
            })
            
        except Exception as e:
            logger.error(f"Error processing row {idx}: {e}")
            error_rows.append({'row_index': idx, 'error': str(e), 'row_data': row.to_dict()})
            continue
    
    if error_rows:
        logger.warning(f"Failed to process {len(error_rows)} rows. See error details above.")
    
    # Create DataFrame
    result_df = pd.DataFrame(processed_rows)
    logger.info(f"Successfully processed {len(result_df)} transactions")
    
    return result_df, error_rows


def save_preview(df: pd.DataFrame, output_path: Path):
    """Save processed dataframe to CSV for preview."""
    df.to_csv(output_path, index=False)
    logger.info(f"Preview saved to: {output_path}")


def print_summary(df: pd.DataFrame):
    """Print summary statistics of processed transactions."""
    print("\n" + "="*60)
    print("MIGRATION PREVIEW SUMMARY")
    print("="*60)
    print(f"Total transactions: {len(df)}")
    print(f"Date range: {df['date'].min()} to {df['date'].max()}")
    print(f"\nBank distribution:")
    print(df['bank_name'].value_counts().to_string())
    print(f"\nTransaction types:")
    print(df.groupby(['transaction_type','bank_name']).size().to_string())
    print(f"\nSpecial transactions: {df['is_special'].sum()}")
    print(f"Total amount: €{df['amount'].sum():,.2f}")
    print("="*60 + "\n")


def insert_transactions(df: pd.DataFrame) -> tuple[int, int]:
    """
    Insert transactions into database, skipping duplicates.
    
    Returns:
        Tuple of (inserted_count, skipped_count)
    """
    # Ensure database tables exist
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created/verified")
    
    db = SessionLocal()
    inserted_count = 0
    skipped_count = 0
    
    try:
        for _, row in df.iterrows():
            # Check for duplicates
            existing = db.query(Transaction).filter(
                Transaction.bank_name == row['bank_name'],
                Transaction.date == row['date'],
                Transaction.amount == row['amount'],
                Transaction.description == row['description']
            ).first()
            
            if existing:
                logger.debug(f"Skipping duplicate transaction: {row['description']} on {row['date']}")
                skipped_count += 1
                continue
            
            # Create new transaction
            transaction = Transaction(
                bank_name=row['bank_name'],
                date=row['date'],
                amount=row['amount'],
                description=row['description'],
                details=row['details'],
                category=row['category'],
                transaction_type=row['transaction_type'],
                is_special=row['is_special']
            )
            
            db.add(transaction)
            inserted_count += 1
        
        db.commit()
        logger.info(f"Successfully inserted {inserted_count} transactions, skipped {skipped_count} duplicates")
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error inserting transactions: {e}")
        raise
    finally:
        db.close()
    
    return inserted_count, skipped_count


def main():
    """Main function to run the migration script."""
    parser = argparse.ArgumentParser(
        description='Migrate legacy transaction data from CSV to database'
    )
    parser.add_argument('csv_file', type=str, help='Path to the legacy CSV file')
    parser.add_argument('--preview-only', action='store_true',
                       help='Only generate preview, do not insert to database')
    parser.add_argument('--force', action='store_true',
                       help='Skip preview confirmation prompt')
    
    args = parser.parse_args()
    
    csv_path = Path(args.csv_file)
    if not csv_path.exists():
        logger.error(f"CSV file not found: {csv_path}")
        sys.exit(1)
    
    # Process CSV
    try:
        df, error_rows = process_legacy_csv(csv_path)
    except Exception as e:
        logger.error(f"Error processing CSV: {e}")
        sys.exit(1)
    
    if df.empty:
        logger.error("No transactions to process")
        sys.exit(1)
    
    # Save preview
    preview_path = Path(__file__).parent / "migrated_transactions_preview.csv"
    save_preview(df, preview_path)
    
    # Print summary
    print_summary(df)
    
    # Report errors if any
    if error_rows:
        print(f"\n⚠️  WARNING: {len(error_rows)} rows could not be processed:")
        for err_row in error_rows[:10]:  # Show first 10 errors
            print(f"  Row {err_row['row_index']}: {err_row['error']}")
        if len(error_rows) > 10:
            print(f"  ... and {len(error_rows) - 10} more errors")
        print()
    
    # Insert to database if not preview-only
    if not args.preview_only:
        if not args.force:
            response = input("Proceed with database insertion? (yes/no): ")
            if response.lower() not in ['yes', 'y']:
                logger.info("Migration cancelled by user")
                sys.exit(0)
        
        try:
            inserted, skipped = insert_transactions(df)
            print(f"\n✅ Migration complete!")
            print(f"   Inserted: {inserted} transactions")
            print(f"   Skipped (duplicates): {skipped} transactions")
        except Exception as e:
            logger.error(f"Error inserting transactions: {e}")
            sys.exit(1)
    else:
        print("\n✅ Preview generated. Use without --preview-only to insert to database.")


if __name__ == "__main__":
    main()
