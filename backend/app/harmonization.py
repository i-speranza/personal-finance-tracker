"""Merge new data with existing data."""
import logging
from typing import List, Dict, Optional, Tuple, Any
from datetime import date
from sqlalchemy.orm import Session
from sqlalchemy import func

from .models import Transaction
from .transactions_preprocessing import StandardizedTransaction

logger = logging.getLogger(__name__)


def get_last_observation_date(db: Session, bank_name: str, account_name: str) -> Optional[date]:
    """
    Query the maximum date from transactions table filtered by bank_name and account_name.
    
    Args:
        db: Database session
        bank_name: Bank name to filter by
        account_name: Account name to filter by
        
    Returns:
        Maximum date if transactions exist, None otherwise
    """
    try:
        result = db.query(func.max(Transaction.date)).filter(
            Transaction.bank_name == bank_name,
            Transaction.account_name == account_name
        ).scalar()
        return result
    except Exception as e:
        logger.error(f"Error getting last observation date for {bank_name}/{account_name}: {e}")
        return None


def detect_duplicates(
    db: Session, 
    transactions: List[StandardizedTransaction]
) -> Tuple[List[StandardizedTransaction], List[Dict[str, Any]]]:
    """
    Detect duplicate transactions by checking against existing database records.
    
    Duplicates are identified by exact match on:
    - bank_name
    - account_name
    - date
    - amount
    - description
    
    Args:
        db: Database session
        transactions: List of StandardizedTransaction objects to check
        
    Returns:
        Tuple of (new_transactions, duplicate_info_list)
        - new_transactions: List of transactions that don't exist in DB
        - duplicate_info_list: List of dicts with duplicate transaction details
    """
    new_transactions = []
    duplicate_info_list = []
    
    for transaction in transactions:
        try:
            # Check if transaction exists in database
            existing = db.query(Transaction).filter(
                Transaction.bank_name == transaction.bank_name,
                Transaction.account_name == transaction.account_name,
                Transaction.date == transaction.date,
                Transaction.amount == transaction.amount,
                Transaction.description == transaction.description
            ).first()
            
            if existing:
                # Transaction is a duplicate
                duplicate_info_list.append({
                    "bank_name": transaction.bank_name,
                    "account_name": transaction.account_name,
                    "date": transaction.date,
                    "amount": transaction.amount,
                    "description": transaction.description,
                    "details": transaction.details,
                    "category": transaction.category,
                    "transaction_type": transaction.transaction_type
                })
            else:
                # Transaction is new
                new_transactions.append(transaction)
                
        except Exception as e:
            logger.error(f"Error checking duplicate for transaction {transaction.date} {transaction.description}: {e}")
            # On error, treat as new transaction (safer to include than exclude)
            new_transactions.append(transaction)
    
    return new_transactions, duplicate_info_list


def display_duplicates(duplicates: List[Dict[str, Any]], bank_name: str, account_name: str, last_obs_date: Optional[date]) -> None:
    """
    Format and display duplicate transactions in a readable format.
    
    Args:
        duplicates: List of duplicate transaction dictionaries
        bank_name: Bank name
        account_name: Account name
        last_obs_date: Last observation date (for display)
    """
    print("\n" + "=" * 60)
    print("DUPLICATE TRANSACTIONS FOUND")
    print("=" * 60)
    print(f"Bank: {bank_name}")
    print(f"Account: {account_name}")
    if last_obs_date:
        print(f"Last observation date: {last_obs_date}")
    else:
        print("Last observation date: No previous transactions")
    
    print(f"\nFound {len(duplicates)} duplicate transaction(s):\n")
    
    # Print header
    print(f"{'#':<4} {'Date':<12} {'Amount':<12} {'Description':<40}")
    print("-" * 70)
    
    # Print each duplicate
    for idx, dup in enumerate(duplicates, 1):
        date_str = str(dup['date']) if dup['date'] else 'N/A'
        amount_str = f"{dup['amount']:>11.2f}" if dup['amount'] is not None else 'N/A'
        desc_str = (dup['description'] or 'N/A')[:38]  # Truncate if too long
        
        print(f"{idx:<4} {date_str:<12} {amount_str:<12} {desc_str:<40}")
    
    print("=" * 60 + "\n")


def harmonize_and_insert(
    db: Session,
    transactions: List[StandardizedTransaction],
    bank_name: str,
    account_name: str,
    require_confirmation: bool = False
) -> Dict[str, Any]:
    """
    Main entry point for harmonization: detect duplicates and insert new transactions.
    
    Args:
        db: Database session
        transactions: List of StandardizedTransaction objects to process
        bank_name: Bank name (used for logging and last observation date)
        account_name: Account name (used for logging and last observation date)
        require_confirmation: If True, display duplicates and wait for user confirmation
        
    Returns:
        Dictionary with statistics:
        {
            "inserted": int,
            "skipped": int,
            "last_obs_date": Optional[date],
            "confirmed": bool
        }
    """
    if not transactions:
        logger.info("No transactions to harmonize")
        return {
            "inserted": 0,
            "skipped": 0,
            "last_obs_date": None,
            "confirmed": False
        }
    
    # Get last observation date
    last_obs_date = get_last_observation_date(db, bank_name, account_name)
    
    if last_obs_date:
        logger.info(f"Last observation date for {bank_name}/{account_name}: {last_obs_date}")
    else:
        logger.info(f"Last observation date for {bank_name}/{account_name}: No previous transactions")
    
    # Detect duplicates
    new_transactions, duplicate_info_list = detect_duplicates(db, transactions)
    
    logger.info(f"Found {len(duplicate_info_list)} duplicate transactions")
    
    # If no new transactions, return early
    if not new_transactions:
        logger.info("No new transactions to insert (all are duplicates)")
        return {
            "inserted": 0,
            "skipped": len(duplicate_info_list),
            "last_obs_date": last_obs_date,
            "confirmed": False
        }
    
    # If review mode is enabled, display duplicates and ask for confirmation
    confirmed = True
    if require_confirmation:
        if duplicate_info_list:
            display_duplicates(duplicate_info_list, bank_name, account_name, last_obs_date)
        
        print(f"Proceed with insertion of {len(new_transactions)} new transaction(s)? (y/n): ", end="")
        try:
            user_input = input().strip().lower()
            if user_input in ['y', 'yes']:
                confirmed = True
                logger.info("User confirmed insertion")
            else:
                confirmed = False
                logger.info("User declined insertion")
        except (EOFError, KeyboardInterrupt):
            logger.warning("User interrupted confirmation prompt")
            confirmed = False
    
    # Insert new transactions if confirmed
    inserted_count = 0
    if confirmed:
        try:
            for transaction in new_transactions:
                try:
                    db_transaction = Transaction(
                        bank_name=transaction.bank_name,
                        account_name=transaction.account_name,
                        date=transaction.date,
                        amount=transaction.amount,
                        description=transaction.description,
                        details=transaction.details,
                        category=transaction.category,
                        transaction_type=transaction.transaction_type,
                        is_special=transaction.is_special
                    )
                    db.add(db_transaction)
                    inserted_count += 1
                except Exception as e:
                    logger.error(f"Error inserting transaction {transaction.date} {transaction.description}: {e}")
                    continue
            
            db.commit()
            logger.info(f"Successfully inserted {inserted_count} transactions")
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error during transaction insertion: {e}")
            raise
    else:
        logger.info("Skipping insertion (not confirmed or all duplicates)")
    
    # Log duplicates
    for dup in duplicate_info_list:
        logger.warning(
            f"Skipping duplicate transaction - "
            f"Bank: {dup['bank_name']}, "
            f"Account: {dup['account_name']}, "
            f"Date: {dup['date']}, "
            f"Amount: {dup['amount']}, "
            f"Description: {dup['description']}"
        )
    
    logger.info(
        f"Harmonization complete - "
        f"Inserted: {inserted_count} transactions, "
        f"Skipped: {len(duplicate_info_list)} duplicates"
    )
    
    return {
        "inserted": inserted_count,
        "skipped": len(duplicate_info_list),
        "last_obs_date": last_obs_date,
        "confirmed": confirmed
    }
