"""
Helper functions for inserting raw bank transaction data.

This module provides functions to insert raw transaction data from banks
before preprocessing, linking them to processed transactions.
"""
import logging
from typing import Optional, Dict, Any
from datetime import date, datetime
import pandas as pd
from sqlalchemy.orm import Session

from .models import IntesaRawTransaction, AllianzRawTransaction, Transaction

logger = logging.getLogger(__name__)


def _normalize_date(date_value: Any) -> date:
    """
    Normalize various date formats to date object.
    
    Args:
        date_value: Date in various formats (string, datetime, date, etc.)
        
    Returns:
        date object
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


def _normalize_amount(amount_value: Any) -> float:
    """
    Normalize various amount formats to float.
    
    Args:
        amount_value: Amount in various formats (string, number, etc.)
        
    Returns:
        float value
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


def insert_intesa_raw_transaction(
    raw_row: Dict[str, Any],
    transaction_id: int,
    db: Session
) -> IntesaRawTransaction:
    """
    Insert a single raw Intesa transaction linked to a processed transaction.
    
    Args:
        raw_row: Dictionary containing raw Intesa data with keys:
            - data (date or string)
            - operazione (str, optional)
            - dettagli (str, optional)
            - conto_o_carta (str, optional)
            - contabilizzazione (str, optional)
            - categoria (str, optional)
            - valuta (str, optional)
            - importo (float or string)
        transaction_id: ID of the processed Transaction to link to
        db: Database session
        
    Returns:
        Created IntesaRawTransaction object
    """
    # Normalize date
    raw_date = _normalize_date(raw_row.get('data'))
    
    # Normalize amount
    raw_amount = _normalize_amount(raw_row.get('importo'))
    
    raw_transaction = IntesaRawTransaction(
        transaction_id=transaction_id,
        data=raw_date,
        operazione=str(raw_row.get('operazione')).strip() or None,
        dettagli=str(raw_row.get('dettagli')).strip() or None,
        conto_o_carta=str(raw_row.get('conto o carta')).strip() or None,
        contabilizzazione=str(raw_row.get('contabilizzazione')).strip() or None,
        categoria=str(raw_row.get('categoria')).strip() or None,
        valuta=str(raw_row.get('valuta')).strip() or None,
        importo=raw_amount
    )
    
    db.add(raw_transaction)
    return raw_transaction


def insert_allianz_raw_transaction(
    raw_row: Dict[str, Any],
    transaction_id: int,
    db: Session
) -> AllianzRawTransaction:
    """
    Insert a single raw Allianz transaction linked to a processed transaction.
    
    Args:
        raw_row: Dictionary containing raw Allianz data with keys:
            - data_contabile (date or string)
            - data_valuta (date or string, optional)
            - descrizione (str, optional)
            - importo (float or string)
        transaction_id: ID of the processed Transaction to link to
        db: Database session
        
    Returns:
        Created AllianzRawTransaction object
    """
    # Normalize dates
    data_contabile = _normalize_date(raw_row.get('data contabile'))
    data_valuta = None
    if raw_row.get('data valuta'):
        try:
            data_valuta = _normalize_date(raw_row.get('data valuta'))
        except Exception:
            data_valuta = None
    
    # Normalize amount - Allianz uses 'dare euro' and 'avere euro' which are combined
    # But in raw data, we should store the original importo if available
    # Otherwise calculate from dare/avere
    if 'importo' in raw_row or 'Importo' in raw_row:
        raw_amount = _normalize_amount(raw_row.get('importo'))
    else:
        raise ValueError("Could not determine importo from raw_row")
    
    raw_transaction = AllianzRawTransaction(
        transaction_id=transaction_id,
        data_contabile=data_contabile,
        data_valuta=data_valuta,
        descrizione=str(raw_row.get('descrizione')).strip() or None,
        importo=raw_amount
    )
    
    db.add(raw_transaction)
    return raw_transaction


def insert_raw_transactions_from_dataframe(
    raw_df: pd.DataFrame,
    processed_transactions: list[Transaction],
    bank_name: str,
    db: Session
) -> list:
    """
    Insert raw transactions from a DataFrame, linking them to processed transactions.
    
    This function matches raw rows to processed transactions by index.
    It handles cases where some rows may have been filtered during preprocessing.
    
    Args:
        raw_df: Raw DataFrame before preprocessing
        processed_transactions: List of Transaction objects that were created
        bank_name: Bank name ("intesa" or "Allianz")
        db: Database session
        
    Returns:
        List of created raw transaction objects
    """
    created_raw_transactions = []
    
    # Normalize bank name for comparison
    bank_name_lower = bank_name.lower().strip()
    
    # Match by index - assumes preprocessing preserves order (except for filtered rows)
    # We'll match by trying to find corresponding rows
    processed_index = 0
    
    for raw_idx, raw_row in raw_df.iterrows():
        # Skip if we've processed all transactions
        if processed_index >= len(processed_transactions):
            logger.warning(f"More raw rows than processed transactions. Skipping raw row {raw_idx}")
            continue
        
        transaction = processed_transactions[processed_index]
        
        try:
            if bank_name_lower == "intesa" or bank_name_lower == "banca intesa":
                raw_trans = insert_intesa_raw_transaction(
                    raw_row.to_dict(),
                    transaction.id,
                    db
                )
            elif bank_name_lower == "allianz":
                raw_trans = insert_allianz_raw_transaction(
                    raw_row.to_dict(),
                    transaction.id,
                    db
                )
            else:
                logger.warning(f"Unknown bank name: {bank_name}. Skipping raw transaction insertion.")
                continue
            
            created_raw_transactions.append(raw_trans)
            processed_index += 1
            
        except Exception as e:
            logger.error(f"Error inserting raw transaction for row {raw_idx}: {e}")
            # Continue to next transaction
            processed_index += 1
            continue
    
    return created_raw_transactions
