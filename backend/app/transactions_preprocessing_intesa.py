"""
Preprocessing module for Intesa bank transactions.

This file contains the IntesaParser class, which is a subclass of BankTransactionsParser.
It is used to parse Intesa bank transactions.
"""
import logging
logger = logging.getLogger(__name__)

from pathlib import Path
from .transactions_preprocessing import (
    BankTransactionsParser,
    TransactionsFileParser,
    register_transactions_parser,
    dataframe_to_list
)
from .transaction_type_mappings import (
    TRANSACTION_MAP_INTESA,
    DEFAULT_TRANSACTION_TYPE_INTESA,
    CARTA_PREPAGATA,
    PAGAMENTO_CON_CARTA
)
import pandas as pd
from typing import Optional


class IntesaParser(BankTransactionsParser):
    """
    Intesa bank parser.
    """
    def __init__(self):
        super().__init__(skiprows=18, skipfooter=0)
        self._raw_df: Optional[pd.DataFrame] = None
    
    def get_bank_name(self) -> str:
        return "intesa"  
    
    def can_parse(self, df: pd.DataFrame, filename: Optional[str] = None) -> bool:
        """
        Implement logic to detect if this file is from Intesa bank.
        
        Examples:
        - Check for specific column names
        - Check for specific values in cells
        - Check filename pattern
        """
        df.columns = df.columns.str.lower().str.strip()

        return "data" in df.columns and "importo" in df.columns

    def _extract_description_intesa(self, operazione: str, dettagli: str, conto_o_carta: str) -> str:
        """
        Extract the description from the operation and details.
        """
        if "Conto" in conto_o_carta or conto_o_carta.strip() == "":
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
            if "SUPERFLASH" not in conto_o_carta.upper():
                logger.warning(f"Could not extract description for operazione: {operazione} with details: {dettagli} and conto o carta: {conto_o_carta}. Defaulting to details.")
            return dettagli
    
        # Default fallback
        return dettagli if dettagli else operazione

    def _extract_transaction_type_intesa(self, operazione: str, dettagli: str, conto_o_carta: str) -> str:
        """
        Extract the transaction type from the operation and details.
        
        Uses TRANSACTION_MAP_INTESA to map operazione.lower() to transaction type.
        Checks for substring matches in the mapping keys.
        """
        operazione_lower = operazione.lower().strip()
        
        # Check if it's a card payment (not from account)
        if conto_o_carta and "Conto" not in conto_o_carta and conto_o_carta.strip() != "":
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
        return DEFAULT_TRANSACTION_TYPE_INTESA
    
    def get_raw_dataframe(self) -> Optional[pd.DataFrame]:
        """
        Get the raw DataFrame before preprocessing.
        
        Returns:
            Raw DataFrame as it was read from the file, or None if not available
        """
        return self._raw_df
    
    def parse(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Parse your bank's specific format.
        
        Steps:
        1. Clean column names
        2. Store raw DataFrame before any modifications (except for the colnames)
        3. Map bank columns to standard fields
        4. Normalize dates and amounts
        5. Create DataFrame with standardized transaction columns
        """
        transactions_data = []
        
        # Clean column names
        df.columns = df.columns.str.lower().str.strip()

        # Store raw DataFrame before any modifications (deep copy to preserve original)
        self._raw_df = df.copy(deep=True)
        
        # check if there are rows where operazione == "Disposizione Di Bonifico", 
        # if so, display a warning with those rows and remove them, since there is no corresponding transaction in the details
        if df[df['operazione'] == "Disposizione Di Bonifico"].shape[0] > 0:
            logger.warning("There are rows where operazione == 'Disposizione Di Bonifico'")
            logger.warning(df[df['operazione'] == "Disposizione Di Bonifico"])
            df = df[df['operazione'] != "Disposizione Di Bonifico"]

        df['descrizione'] = df.apply(lambda row: self._extract_description_intesa(row['operazione'], row['dettagli'], row['conto o carta']), axis=1)
        df['tipo_transazione'] = df.apply(lambda row: self._extract_transaction_type_intesa(row['operazione'], row['dettagli'], row['conto o carta']), axis=1)
        df['dettagli'] = df['dettagli'] + " - " + df['conto o carta']
        # Map your bank's columns to standard fields
        # Adjust these based on your actual file format
        date_col = "data"  # Your bank's date column
        amount_col = "importo"  # Your bank's amount column
        description_col = "descrizione"  # Your bank's description column
        details_col = "dettagli"
        category_col = "categoria"  
        transaction_type_col = "tipo_transazione"
        
        for _, row in df.iterrows():
            try:
                # Extract and normalize
                trans_date = self.normalize_date(row[date_col])
                amount = self.normalize_amount(row[amount_col])
                description = str(row[description_col]) if pd.notna(row.get(description_col)) else None
                details = str(row[details_col]) if pd.notna(row.get(details_col)) else None
                category = str(row[category_col]) if pd.notna(row.get(category_col)) else None
                transaction_type = str(row[transaction_type_col].strip()) if pd.notna(row.get(transaction_type_col)) else None  
                
                transactions_data.append({
                    "bank_name": self.get_bank_name(),
                    "date": trans_date,
                    "amount": amount,
                    "description": description,
                    "details": details,
                    "category": category,
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
    intesa_parser = IntesaParser()
    register_transactions_parser(intesa_parser)
    
    # Step 2: Create a TransactionsFileParser instance
    parser = TransactionsFileParser()    
    
    # Step 3: Parse a file
    example_file = Path(__file__).parent.parent / "examples" / "intesa_transactions_example.xlsx"    
    
    try:
        df = parser.parse_file(example_file, bank_name="intesa")
        print(df)
        # Convert to list of dicts for display
        transactions = dataframe_to_list(df)
        print([tt.to_dict() for tt in transactions])
            
    except ValueError as e:
        print(f"Error parsing file: {e}")


if __name__ == "__main__":
    # Run examples
    example_usage()
