"""
Preprocessing module for FinecoBank transactions.

This file contains the FinecoBankParser class, which is a subclass of BankTransactionsParser.
It is used to parse FinecoBank transactions.
"""

from pathlib import Path
from .transactions_preprocessing import (
    BankTransactionsParser,
    TransactionsFileParser,
    register_transactions_parser,
    dataframe_to_list
)
from .transaction_type_mappings import (
    TRANSACTION_MAP_FINECO,
    DEFAULT_TRANSACTION_TYPE_FINECO
)
import pandas as pd
import logging
import argparse
from typing import Optional

logger = logging.getLogger(__name__)

class FinecoBankParser(BankTransactionsParser):
    """
    FinecoBank parser.
    """
    def __init__(self):
        super().__init__(skiprows=12, skipfooter=0)
        self._raw_df: Optional[pd.DataFrame] = None
    
    def get_bank_name(self) -> str:
        return "fineco"  # Use lowercase for consistency  
    
    def can_parse(self, df: pd.DataFrame, filename: Optional[str] = None) -> bool:
        """
        Implement logic to detect if this file is from FinecoBank.
        
        Examples:
        - Check for specific column names
        - Check for specific values in cells
        - Check filename pattern
        """
        df.columns = df.columns.str.lower().str.strip()
        
        return "data_valuta" in df.columns

    def _extract_transaction_type_finecobank(self, raw_transaction_type: str, amount: float) -> str:
        """
        Extract the transaction type from details for FinecoBank.
        
        Uses TRANSACTION_MAP_FINECO to map transaction_type.lower() (first part before dash)
        to standardized transaction type.
        """
        raw_transaction_type = raw_transaction_type.lower().strip()

        if "bonifico" in raw_transaction_type:
            if amount > 0:
                raw_transaction_type = "bonifico ricevuto"
            else:
                raw_transaction_type = "bonifico effettuato"

        # Look up in mapping
        if raw_transaction_type in TRANSACTION_MAP_FINECO:
            return TRANSACTION_MAP_FINECO[raw_transaction_type]
        
        else:
            logger.warning(f"Transaction type not found in mapping: {raw_transaction_type}")
            return raw_transaction_type if raw_transaction_type else DEFAULT_TRANSACTION_TYPE_FINECO
    
    def get_raw_dataframe(self) -> Optional[pd.DataFrame]:
        """
        Get the raw DataFrame before preprocessing.
        
        Returns:
            Raw DataFrame as it was read from the file, or None if not available
        """
        return self._raw_df
    
    def parse(self, df: pd.DataFrame, filename: Optional[str] = None) -> pd.DataFrame:
        """
        Parse your bank's specific format.
        
        Steps:
        1. Clean column names
        2. Store raw DataFrame before any modifications
        3. Map bank columns to standard fields
        4. Normalize dates and amounts
        5. Create DataFrame with standardized transaction columns
        """
        
        # Clean column names
        df.columns = df.columns.str.lower().str.strip()
        
        # Store raw DataFrame before any other modifications (deep copy to preserve original)
        self._raw_df = df.copy(deep=True)
        
        transactions_data = []

        df['dettagli'] = df['descrizione_completa']  
        df['importo'] = df['entrate'].fillna(0) + df['uscite'].fillna(0)
        df['tipo_transazione'] = df.apply(lambda row: self._extract_transaction_type_finecobank(row['descrizione'], row['importo']), axis=1)

        date_col = "data_valuta"
        amount_col = "importo"
        description_col = "dettagli" # description is the same as details for the time being
        details_col = "dettagli"
        transaction_type_col = "tipo_transazione"
        
        for idx, row in df.iterrows():
            try:
                # Extract and normalize
                trans_date = self.normalize_date(row[date_col])
                amount = self.normalize_amount(row[amount_col])
                description = str(row[description_col]) if pd.notna(row.get(description_col)) else None
                details = str(row[details_col]) if pd.notna(row.get(details_col)) else None
                transaction_type = str(row[transaction_type_col]) if pd.notna(row.get(transaction_type_col)) else None
                
                transactions_data.append({
                    "bank_name": self.get_bank_name(),
                    "date": trans_date,
                    "amount": amount,
                    "description": description,
                    "details": details,
                    "transaction_type": transaction_type,
                    "is_special": False,
                    "_raw_idx": idx  # Preserve original index for raw data matching
                })
            except Exception as e:
                # Log and skip invalid rows
                print(f"Skipping row: {e}")
                continue
        
        # Convert to DataFrame
        result_df = pd.DataFrame(transactions_data)
        return result_df


def example_usage(file_path: Path):
    """Example of how to use the preprocessing module."""
    
    # Step 1: Create and register your parser
    finecobank_parser = FinecoBankParser()
    register_transactions_parser(finecobank_parser)
    
    # Step 2: Create a TransactionsFileParser instance
    parser = TransactionsFileParser()    
    
    # Step 3: Parse a file
    try:
        df = parser.parse_file(file_path, bank_name="fineco")
        print(df)
        # Convert to list of dicts for display
        transactions = dataframe_to_list(df)
        print([tt.to_dict() for tt in transactions])
            
    except ValueError as e:
        print(f"Error parsing file: {e}")


if __name__ == "__main__":
    # Parse command line arguments
    arg_parser = argparse.ArgumentParser(description="Parse FinecoBank transaction file")
    arg_parser.add_argument(
        "file_path",
        type=str,
        help="Path to the FinecoBank transaction file to parse"
    )
    
    args = arg_parser.parse_args()
    file_path = Path(args.file_path)
    
    # Validate file exists
    if not file_path.exists():
        print(f"Error: File not found: {file_path}")
        exit(1)
    
    # Run example with file from command line
    example_usage(file_path)
