"""
One-time migration script from CSV files.

This script migrates legacy assets history data from a CSV file with specific column structure.

Expected CSV columns:
- Asset (maps to account_name)
- Date
- Banca (maps to bank_name)
- Tipo (maps to asset_type: cash/investment)
- Importo (maps to amount)
"""
import sys
import argparse
import logging
from pathlib import Path
from datetime import date, datetime
import pandas as pd

# Add parent directory to path to import app modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import SessionLocal, engine, Base
from app import models  # noqa: F401 - Import to register models with Base
from app.models import AssetsHistory, AssetType

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


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


def process_legacy_csv(csv_path: Path) -> tuple[pd.DataFrame, list]:
    """
    Read and process the legacy CSV file.
    
    Returns:
        Tuple of (DataFrame with standardized asset history columns, error_rows list)
    """
    logger.info(f"Reading CSV file: {csv_path}")
    
    # Read CSV
    try:
        df = pd.read_csv(csv_path)
    except Exception as e:
        logger.error(f"Error reading CSV file: {e}")
        raise
    
    # Validate required columns
    required_columns = ['Asset', 'Date', 'Banca', 'Tipo', 'Importo']
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        raise ValueError(f"Missing required columns: {missing_columns}")
    
    logger.info(f"Found {len(df)} rows in CSV")
    
    # Process each row
    processed_rows = []
    error_rows = []
    
    for idx, row in df.iterrows():
        try:
            # Get account name
            account_name = str(row['Asset']).strip() if pd.notna(row['Asset']) else None
            if not account_name:
                raise ValueError("Account name (Asset) cannot be empty")
            
            # Get bank name and normalize
            bank_name = str(row['Banca']).strip().lower() if pd.notna(row['Banca']) else None
            if not bank_name:
                raise ValueError("Bank name (Banca) cannot be empty")
            
            # Normalize date
            asset_date = normalize_date(row['Date'])
            
            # Get asset type (values are already "cash" or "investment")
            tipo_str = str(row['Tipo']).strip().lower() if pd.notna(row['Tipo']) else None
            if not tipo_str:
                raise ValueError("Asset type (Tipo) cannot be empty")
            if tipo_str not in ["cash", "investment"]:
                raise ValueError(f"Invalid asset type: {tipo_str}. Expected 'cash' or 'investment'")
            asset_type = AssetType.CASH if tipo_str == "cash" else AssetType.INVESTMENT
            
            # Normalize amount
            amount = normalize_amount(row['Importo'])
            
            processed_rows.append({
                'account_name': account_name,
                'bank_name': bank_name,
                'asset_type': asset_type,
                'date': asset_date,
                'amount': amount
            })
            
        except Exception as e:
            logger.error(f"Error processing row {idx}: {e}")
            error_rows.append({'row_index': idx, 'error': str(e), 'row_data': row.to_dict()})
            continue
    
    if error_rows:
        logger.warning(f"Failed to process {len(error_rows)} rows. See error details above.")
    
    # Create DataFrame
    result_df = pd.DataFrame(processed_rows)
    logger.info(f"Successfully processed {len(result_df)} asset history entries")
    
    return result_df, error_rows


def save_preview(df: pd.DataFrame, output_path: Path):
    """Save processed dataframe to CSV for preview."""
    # Convert enum to string for CSV export
    preview_df = df.copy()
    preview_df['asset_type'] = preview_df['asset_type'].apply(lambda x: x.value if hasattr(x, 'value') else str(x))
    preview_df.to_csv(output_path, index=False)
    logger.info(f"Preview saved to: {output_path}")


def print_summary(df: pd.DataFrame):
    """Print summary statistics of processed asset history."""
    print("\n" + "="*60)
    print("MIGRATION PREVIEW SUMMARY")
    print("="*60)
    print(f"Total asset history entries: {len(df)}")
    print(f"Date range: {df['date'].min()} to {df['date'].max()}")
    print(f"\nBank distribution:")
    print(df['bank_name'].value_counts().to_string())
    print(f"\nAsset type distribution:")
    asset_type_counts = df['asset_type'].apply(lambda x: x.value if hasattr(x, 'value') else str(x)).value_counts()
    print(asset_type_counts.to_string())
    print(f"\nAccount distribution:")
    print(df['account_name'].value_counts().to_string())
    print(f"\nTotal amount by asset type:")
    for asset_type in df['asset_type'].unique():
        asset_type_str = asset_type.value if hasattr(asset_type, 'value') else str(asset_type)
        total = df[df['asset_type'] == asset_type]['amount'].sum()
        print(f"  {asset_type_str}: €{total:,.2f}")
    print("="*60 + "\n")


def insert_assets_history(df: pd.DataFrame) -> tuple[int, int]:
    """
    Insert asset history entries into database, skipping duplicates.
    
    Returns:
        Tuple of (inserted_count, skipped_count)
    """
    # Drop and recreate the assets_history table to match new schema
    # This is necessary because SQLAlchemy doesn't alter existing tables
    logger.info("Dropping existing assets_history table (if any) to recreate with new schema...")
    AssetsHistory.__table__.drop(engine, checkfirst=True)
    logger.info("Creating assets_history table with new schema...")
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created/verified")
    
    db = SessionLocal()
    inserted_count = 0
    skipped_count = 0
    
    try:
        for _, row in df.iterrows():
            # Check for duplicates
            existing = db.query(AssetsHistory).filter(
                AssetsHistory.bank_name == row['bank_name'],
                AssetsHistory.account_name == row['account_name'],
                AssetsHistory.asset_type == row['asset_type'],
                AssetsHistory.date == row['date']
            ).first()
            
            if existing:
                logger.debug(f"Skipping duplicate asset history: {row['account_name']} ({row['asset_type'].value}) on {row['date']}")
                skipped_count += 1
                continue
            
            # Create new asset history entry
            asset_history = AssetsHistory(
                account_name=row['account_name'],
                bank_name=row['bank_name'],
                asset_type=row['asset_type'],
                date=row['date'],
                amount=row['amount']
            )
            
            db.add(asset_history)
            inserted_count += 1
        
        db.commit()
        logger.info(f"Successfully inserted {inserted_count} asset history entries, skipped {skipped_count} duplicates")
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error inserting asset history: {e}")
        raise
    finally:
        db.close()
    
    return inserted_count, skipped_count


def main():
    """Main function to run the migration script."""
    parser = argparse.ArgumentParser(
        description='Migrate legacy assets history data from CSV to database'
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
        logger.error("No asset history entries to process")
        sys.exit(1)
    
    # Save preview
    preview_path = Path(__file__).parent / "migrated_assets_history_preview.csv"
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
            inserted, skipped = insert_assets_history(df)
            print(f"\n✅ Migration complete!")
            print(f"   Inserted: {inserted} asset history entries")
            print(f"   Skipped (duplicates): {skipped} entries")
        except Exception as e:
            logger.error(f"Error inserting asset history: {e}")
            sys.exit(1)
    else:
        print("\n✅ Preview generated. Use without --preview-only to insert to database.")


if __name__ == "__main__":
    main()
