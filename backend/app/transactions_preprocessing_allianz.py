"""
Preprocessing module for Allianz bank transactions.

This file contains the AllianzParser class, which is a subclass of BankTransactionsParser.
It is used to parse Allianz bank transactions.
"""

from pathlib import Path
from .transactions_preprocessing import (
    BankTransactionsParser,
    TransactionsFileParser,
    register_transactions_parser,
    dataframe_to_list
)
import pandas as pd
from typing import Optional


class AllianzParser(BankTransactionsParser):
    """
    Allianz bank parser.
    """
    def __init__(self):
        super().__init__(skiprows=3, skipfooter=4)
    
    def get_bank_name(self) -> str:
        return "Allianz"  
    
    def can_parse(self, df: pd.DataFrame, filename: Optional[str] = None) -> bool:
        """
        Implement logic to detect if this file is from Allianz bank.
        
        Examples:
        - Check for specific column names
        - Check for specific values in cells
        - Check filename pattern
        """
        df.columns = df.columns.str.lower().str.strip()

        return "importo" in df.columns

    def _extract_description_allianz(self, details: str) -> str:
        """
        Extract the description from the details.
        """
        transaction_type = details.split('-')[0].strip()

        if transaction_type == "Pagam. POS":
            # split on dash, take the second part and keep only the part after "ORE"
            time_info = "ORE " + details.split('-')[1].strip().split('ORE')[1].strip()
            # split on dash, take the third part and keep only the part before "CARTA"
            transaction_info = details.split('-')[2].strip().split('CARTA')[0].strip()
            return "POS" + " - " + transaction_info + " - " + time_info
        elif transaction_type == "Addeb. diretto":
            # split on dash, take the second part
            return "Addeb. diretto" + " - " + details.split('-')[1].strip()
        elif transaction_type == "Bancomat":
            # split on dash, take the second part and keep only the part after "ORE" and before "CARTA"
            transaction_info = "ORE " + details.split('-')[1].strip().split('ORE')[1].strip()
            transaction_info = transaction_info.split('CARTA')[0].strip()
            return "Prelievo contanti" + " - " + transaction_info
        elif transaction_type == "Bonif. v/fav.":
            # remove the word starting with "RIF:"
            return "Bonif. ricevuto" + " - " + ' '.join([word for word in details.split() if not word.startswith("RIF:")])
        elif transaction_type == "Disposizione":
            # remove the word starting with "RIF:"
            return "Bonif. effettuato" + " - " + ' '.join([word for word in details.split() if not word.startswith("RIF:")])
        else:
            return ' '.join(details.split())
    
    def parse(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Parse your bank's specific format.
        
        Steps:
        1. Clean column names
        2. Map bank columns to standard fields
        3. Normalize dates and amounts
        4. Create DataFrame with standardized transaction columns
        """
        transactions_data = []
        
        # Clean column names
        df.columns = df.columns.str.lower().str.strip()

        df['importo'] = df['dare euro'].fillna(0) + df['avere euro'].fillna(0) 
        df['dettagli'] = df['descrizione']
        df['descrizione'] = df['dettagli'].apply(self._extract_description_allianz)

        df['tipo_transazione'] = df['descrizione'].apply(lambda x: x.split('-')[0].strip())
        # Map your bank's columns to standard fields
        # Adjust these based on your actual file format
        date_col = "data contabile"  # Your bank's date column
        amount_col = "importo"  # Your bank's amount column
        description_col = "descrizione"  # Your bank's description column
        details_col = "dettagli"
        transaction_type_col = "tipo_transazione"
        for _, row in df.iterrows():
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
                    "is_special": False
                })
            except Exception as e:
                # Log and skip invalid rows
                print(f"Skipping row: {e}")
                continue
        
        # Convert to DataFrame
        result_df = pd.DataFrame(transactions_data)
        return result_df


def example_usage():
    """Example of how to use the preprocessing module."""
    
    # Step 1: Create and register your parser
    Allianz_parser = AllianzParser()
    register_transactions_parser(Allianz_parser)
    
    # Step 2: Create a TransactionsFileParser instance
    parser = TransactionsFileParser()    
    
    # Step 3: Parse a file
    example_file = Path(__file__).parent.parent / "examples" / "allianz_transactions_example.xls"    
    
    try:
        df = parser.parse_file(example_file, bank_name="Allianz")
        print(df)
        # Convert to list of dicts for display
        transactions = dataframe_to_list(df)
        print([tt.to_dict() for tt in transactions])
            
    except ValueError as e:
        print(f"Error parsing file: {e}")


if __name__ == "__main__":
    # Run examples
    example_usage()
