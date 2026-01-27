"""
Test script for harmonization functionality.

This script allows testing the harmonization module by:
1. Parsing a transaction file
2. Detecting duplicates against existing database
3. Optionally requiring confirmation before insertion

Usage:
    python backend/scripts/test_harmonization.py <file_path> [--bank-name BANK_NAME] [--account-name ACCOUNT_NAME] [--require-confirmation]
    
Examples:
    python backend/scripts/test_harmonization.py examples/intesa_transactions.xlsx --bank-name intesa --account-name "Main Account"
    python backend/scripts/test_harmonization.py examples/allianz_transactions.xls --bank-name Allianz --account-name "Savings" --require-confirmation
"""
import argparse
import sys
import logging
from pathlib import Path

# Add parent directory to path to allow imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import SessionLocal
from app.transactions_preprocessing import TransactionsFileParser, dataframe_to_list
from app.transactions_preprocessing_intesa import IntesaParser
from app.transactions_preprocessing_allianz import AllianzParser
from app.transactions_preprocessing import register_transactions_parser
from app import harmonization

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def extract_bank_name_from_filename(filename: str) -> str:
    """
    Try to extract bank name from filename.
    
    Args:
        filename: Name of the file
        
    Returns:
        Bank name if detected, None otherwise
    """
    filename_lower = filename.lower()
    
    if 'intesa' in filename_lower:
        return 'intesa'
    elif 'allianz' in filename_lower:
        return 'Allianz'
    
    return None


def register_all_parsers():
    """Register all available bank parsers."""
    intesa_parser = IntesaParser()
    allianz_parser = AllianzParser()
    
    register_transactions_parser(intesa_parser)
    register_transactions_parser(allianz_parser)
    
    logger.info("Registered parsers: Intesa, Allianz")


def main():
    """Main function to test harmonization."""
    parser = argparse.ArgumentParser(
        description='Test harmonization functionality with a transaction file',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    parser.add_argument(
        'file_path',
        type=str,
        help='Path to the transaction file to process'
    )
    
    parser.add_argument(
        '--bank-name',
        type=str,
        default=None,
        help='Bank name (intesa, Allianz). If not provided, will try to extract from filename.'
    )
    
    parser.add_argument(
        '--account-name',
        type=str,
        default=None,
        required=True,
        help='Account name (required). Must match account names in assets_history.'
    )
    
    parser.add_argument(
        '--require-confirmation',
        action='store_true',
        help='Require user confirmation before inserting transactions (review mode)'
    )
    
    args = parser.parse_args()
    
    # Validate file path
    file_path = Path(args.file_path)
    if not file_path.exists():
        logger.error(f"File not found: {file_path}")
        sys.exit(1)
    
    # Determine bank name
    bank_name = args.bank_name
    if not bank_name:
        bank_name = extract_bank_name_from_filename(file_path.name)
        if bank_name:
            logger.info(f"Extracted bank name from filename: {bank_name}")
        else:
            logger.error(
                f"Could not determine bank name from filename '{file_path.name}'. "
                "Please provide --bank-name argument."
            )
            sys.exit(1)
    else:
        logger.info(f"Using provided bank name: {bank_name}")
    
    # Get account name (required)
    account_name = args.account_name
    if not account_name:
        logger.error("Account name is required. Please provide --account-name argument.")
        sys.exit(1)
    logger.info(f"Using account name: {account_name}")
    
    # Register parsers
    register_all_parsers()
    
    # Parse file
    logger.info(f"Parsing file: {file_path}")
    file_parser = TransactionsFileParser()
    
    try:
        df = file_parser.parse_file(file_path, bank_name=bank_name)
        logger.info(f"Successfully parsed {len(df)} transactions from file")
    except Exception as e:
        logger.error(f"Error parsing file: {e}")
        sys.exit(1)
    
    # Add account_name to DataFrame (parsers don't include it, it comes from frontend/CLI)
    df['account_name'] = account_name
    
    # Convert to StandardizedTransaction list
    transactions = dataframe_to_list(df)
    logger.info(f"Converted to {len(transactions)} StandardizedTransaction objects")
    
    # Get database session
    db = SessionLocal()
    
    try:
        # Run harmonization
        logger.info("Starting harmonization process...")
        if args.require_confirmation:
            logger.info("Review mode enabled - duplicates will be displayed for confirmation")
        
        result = harmonization.harmonize_and_insert(
            db=db,
            transactions=transactions,
            bank_name=bank_name,
            account_name=account_name,
            require_confirmation=args.require_confirmation
        )
        
        # Display results
        print("\n" + "=" * 60)
        print("HARMONIZATION RESULTS")
        print("=" * 60)
        print(f"Bank: {bank_name}")
        print(f"Account: {account_name}")
        print(f"Last observation date: {result['last_obs_date'] or 'No previous transactions'}")
        print(f"Transactions processed: {len(transactions)}")
        print(f"New transactions inserted: {result['inserted']}")
        print(f"Duplicate transactions skipped: {result['skipped']}")
        print(f"Confirmation required: {args.require_confirmation}")
        print(f"User confirmed: {result['confirmed']}")
        print("=" * 60)
        
        if result['inserted'] > 0:
            logger.info(f"Successfully inserted {result['inserted']} new transactions")
        
        if result['skipped'] > 0:
            logger.warning(f"Skipped {result['skipped']} duplicate transactions")
        
    except Exception as e:
        logger.error(f"Error during harmonization: {e}", exc_info=True)
        db.rollback()
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()
