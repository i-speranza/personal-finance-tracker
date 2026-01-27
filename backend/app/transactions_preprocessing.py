"""File parsing and standardization with bank-specific preprocessing."""
import pandas as pd
from pathlib import Path
from typing import List, Dict, Optional, Any
from datetime import date, datetime
from abc import ABC, abstractmethod
import logging

from .file_reader import FileReader

logger = logging.getLogger(__name__)


class StandardizedTransaction:
    """Standardized transaction data structure."""
    
    def __init__(
        self,
        bank_name: str,
        account_name: str,
        date: date,
        amount: float,
        description: Optional[str] = None,
        details: Optional[str] = None,
        category: Optional[str] = None,
        transaction_type: Optional[str] = None,
        is_special: bool = False
    ):
        self.bank_name = bank_name
        self.account_name = account_name
        self.date = date
        self.amount = amount
        self.description = description
        self.details = details
        self.category = category
        self.transaction_type = transaction_type
        self.is_special = is_special
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for database insertion."""
        return {
            "bank_name": self.bank_name,
            "account_name": self.account_name,
            "date": self.date,
            "amount": self.amount,
            "description": self.description,
            "details": self.details,
            "category": self.category,
            "transaction_type": self.transaction_type,
            "is_special": self.is_special
        }


def dataframe_to_list(df: pd.DataFrame) -> List[StandardizedTransaction]:
    """
    Convert a DataFrame with standardized transaction columns to a list of StandardizedTransaction objects.
    
    Args:
        df: DataFrame with columns: bank_name, account_name, date, amount, description, details, 
            category, transaction_type, is_special 
            
    Returns:
        List of StandardizedTransaction objects
    """
    transactions = []
    
    for _, row in df.iterrows():
        try:
            # Extract date - handle both date and datetime types
            trans_date = row['date']
            if isinstance(trans_date, pd.Timestamp):
                trans_date = trans_date.date()
            elif isinstance(trans_date, datetime):
                trans_date = trans_date.date()
            elif not isinstance(trans_date, date):
                # Try to parse if it's a string
                trans_date = pd.to_datetime(trans_date).date()
            
            transaction = StandardizedTransaction(
                bank_name=str(row['bank_name']) if pd.notna(row.get('bank_name')) else None,
                account_name=str(row['account_name']) if pd.notna(row.get('account_name')) else None,
                date=trans_date,
                amount=float(row['amount']) if pd.notna(row.get('amount')) else 0.0,
                description=str(row['description']) if pd.notna(row.get('description')) else None,
                details=str(row['details']) if pd.notna(row.get('details')) else None,
                category=str(row['category']) if pd.notna(row.get('category')) else None,
                transaction_type=str(row['transaction_type']) if pd.notna(row.get('transaction_type')) else None,
                is_special=bool(row['is_special']) if pd.notna(row.get('is_special')) else False
            )
            transactions.append(transaction)
        except Exception as e:
            logger.warning(f"Skipping row due to error in dataframe_to_list: {e}")
            continue
    
    return transactions


class BankTransactionsParser(ABC):
    """Abstract base class for bank-specific parsers."""
    def __init__(self, skiprows: Optional[int] = None, skipfooter: Optional[int] = None):
        self.skiprows = skiprows
        self.skipfooter = skipfooter
    
    @abstractmethod
    def get_bank_name(self) -> str:
        """Return the bank name this parser handles."""
        pass
    
    @abstractmethod
    def can_parse(self, df: pd.DataFrame, filename: Optional[str] = None) -> bool:
        """
        Check if this parser can handle the given DataFrame.
        
        Args:
            df: The DataFrame to check
            filename: Optional filename for additional context
            
        Returns:
            True if this parser can handle the file, False otherwise
        """
        pass
    
    @abstractmethod
    def parse(self, df: pd.DataFrame, filename: Optional[str] = None) -> pd.DataFrame:
        """
        Parse the DataFrame and return standardized transactions as a DataFrame.
        
        Args:
            df: The DataFrame to parse
            filename: Optional filename for additional context
            
        Returns:
            DataFrame with standardized transaction columns:
            - bank_name: str
            - date: date/datetime
            - amount: float
            - description: str (nullable)
            - details: str (nullable)
            - category: str (nullable)
            - transaction_type: str (nullable)
            - is_special: bool
        """
        pass
    
    def normalize_date(self, date_value: Any) -> date:
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
                for fmt in ["%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y", "%d-%m-%Y", "%Y/%m/%d"]:
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
    
    def normalize_amount(self, amount_value: Any) -> float:
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
            cleaned = amount_value.strip().replace(",", "").replace(" ", "")
            # Remove common currency symbols
            for symbol in ["$", "€", "£", "₹", "Rs", "rs"]:
                cleaned = cleaned.replace(symbol, "")
            
            try:
                return float(cleaned)
            except ValueError as e:
                raise ValueError(f"Could not convert amount '{amount_value}' to float: {e}")
        
        try:
            return float(amount_value)
        except Exception as e:
            raise ValueError(f"Could not convert to float: {amount_value} - {e}")


class TransactionsParserRegistry:
    """Registry for bank-specific parsers."""
    
    def __init__(self):
        self._parsers: List[BankTransactionsParser] = []
    
    def register(self, parser: BankTransactionsParser):
        """Register a bank parser."""
        self._parsers.append(parser)
        logger.info(f"Registered parser for bank: {parser.get_bank_name()}")
    
    def get_parser_by_bank_name(self, bank_name: str) -> Optional[BankTransactionsParser]:
        """Get parser by bank name."""
        for parser in self._parsers:
            if parser.get_bank_name().lower() == bank_name.lower():
                return parser
        return None


# Global parser registry instance
_transactions_parser_registry = TransactionsParserRegistry()


def register_transactions_parser(parser: BankTransactionsParser):
    """Register a bank parser in the global registry."""
    _transactions_parser_registry.register(parser)


def get_transactions_parser_registry() -> TransactionsParserRegistry:
    """Get the global parser registry."""
    return _transactions_parser_registry


class TransactionsFileParser:
    """Main file parser that handles file reading and routing to bank parsers."""
    
    def __init__(self, parser_registry: Optional[TransactionsParserRegistry] = None):
        self.registry = parser_registry or _transactions_parser_registry
        self.file_reader = FileReader()
        self._current_parser: Optional[BankTransactionsParser] = None
    
    def parse_file(
        self,
        file_path: Path,
        bank_name: str
    ) -> pd.DataFrame:
        """
        Parse a file and return standardized transactions as a DataFrame.
        
        Args:
            file_path: Path to the file to parse
            bank_name: Bank name to force a specific parser
            
        Returns:
            DataFrame with standardized transaction columns:
            - bank_name: str
            - date: date/datetime
            - amount: float
            - description: str (nullable)
            - details: str (nullable)
            - category: str (nullable)
            - transaction_type: str (nullable)
            - is_special: bool
            
        Raises:
            ValueError: If file cannot be parsed or no suitable parser found
        """        
        # Find appropriate parser
        if bank_name:
            parser = self.registry.get_parser_by_bank_name(bank_name)
            if not parser:
                raise ValueError(f"No parser registered for bank: {bank_name}")
        else:
            raise ValueError(
                f"No suitable parser found for file: {file_path.name}. "
                "Please register a parser for this bank format."
            )
        
        # Store parser reference for raw data access
        self._current_parser = parser
        
        # Read file
        df = self.file_reader.read_file(file_path, skiprows=parser.skiprows, skipfooter=parser.skipfooter)
        
        if df.empty:
            raise ValueError("File is empty or contains no data")

        # Parse using the selected parser
        try:
            result_df = parser.parse(df)
            logger.info(f"Parsed {len(result_df)} transactions from {file_path.name}")
        except Exception as e:
            logger.error(f"Error parsing file {file_path.name} with parser {parser.get_bank_name()}: {e}")
            raise

        # Check if there are duplicate transactions, if so raise a warning displaying the duplicate transactions and sum the amounts
        if result_df.duplicated().any():
            duplicate_transactions = result_df[result_df.duplicated(keep=False)]
            logger.warning(f"Duplicate transactions found: \n{duplicate_transactions}\n. Summing the amounts.")
            result_df = result_df.groupby([c for c in result_df.columns if c not in 'amount'])['amount'].sum().reset_index()

        return result_df
    
    def get_raw_dataframe(self) -> Optional[pd.DataFrame]:
        """
        Get the raw DataFrame before preprocessing from the last parsed file.
        
        Returns:
            Raw DataFrame as it was read from the file, or None if not available.
            The DataFrame contains the original bank-specific columns before any preprocessing.
        """
        if self._current_parser and hasattr(self._current_parser, 'get_raw_dataframe'):
            return self._current_parser.get_raw_dataframe()
        return None


# Example bank parser implementation (for testing and as a template)
class ExampleBankTransactionsParser(BankTransactionsParser):
    """
    Example bank transactions parser implementation.
    """
    
    def get_bank_name(self) -> str:
        return "Example Bank"
    
    def can_parse(self, df: pd.DataFrame, filename: Optional[str] = None) -> bool:
        return True
    
    def parse(self, df: pd.DataFrame) -> pd.DataFrame:
        transactions_data = []
        
        # Clean column names (lowercase, strip whitespace)
        df.columns = df.columns.str.lower().str.strip()
        
        # Map columns to standard fields
        # Adjust these mappings based on actual bank format
        date_col = "date"
        amount_col = "amount"
        description_col = "description"
        category_col = "category"
        
        for _, row in df.iterrows():
            try:
                # Extract and normalize data
                trans_date = self.normalize_date(row[date_col])
                amount = self.normalize_amount(row[amount_col])
                description = str(row[description_col]) if pd.notna(row.get(description_col)) else None
                category = str(row[category_col]) if pd.notna(row.get(category_col)) else None
                
                transactions_data.append({
                    "bank_name": self.get_bank_name(),
                    "date": trans_date,
                    "amount": amount,
                    "description": description,
                    "details": None,
                    "category": category,
                    "transaction_type": None,
                    "is_special": False
                })
            except Exception as e:
                logger.warning(f"Skipping row due to error: {e}")
                continue
        
        # Convert to DataFrame
        result_df = pd.DataFrame(transactions_data)
        return result_df


# Register example parser (can be removed or kept for testing)
# register_parser(ExampleBankParser())
