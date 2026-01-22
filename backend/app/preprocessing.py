"""File parsing and standardization with bank-specific preprocessing."""
import pandas as pd
from pathlib import Path
from typing import List, Dict, Optional, Any
from datetime import date, datetime
from abc import ABC, abstractmethod
import logging

logger = logging.getLogger(__name__)


class StandardizedTransaction:
    """Standardized transaction data structure."""
    
    def __init__(
        self,
        bank_name: str,
        date: date,
        amount: float,
        description: Optional[str] = None,
        category: Optional[str] = None,
        is_special: bool = False
    ):
        self.bank_name = bank_name
        self.date = date
        self.amount = amount
        self.description = description
        self.category = category
        self.is_special = is_special
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for database insertion."""
        return {
            "bank_name": self.bank_name,
            "date": self.date,
            "amount": self.amount,
            "description": self.description,
            "category": self.category,
            "is_special": self.is_special
        }


class BankParser(ABC):
    """Abstract base class for bank-specific parsers."""
    
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
    def parse(self, df: pd.DataFrame, filename: Optional[str] = None) -> List[StandardizedTransaction]:
        """
        Parse the DataFrame and return standardized transactions.
        
        Args:
            df: The DataFrame to parse
            filename: Optional filename for additional context
            
        Returns:
            List of StandardizedTransaction objects
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


class ParserRegistry:
    """Registry for bank-specific parsers."""
    
    def __init__(self):
        self._parsers: List[BankParser] = []
    
    def register(self, parser: BankParser):
        """Register a bank parser."""
        if not isinstance(parser, BankParser):
            raise ValueError("Parser must be an instance of BankParser")
        self._parsers.append(parser)
        logger.info(f"Registered parser for bank: {parser.get_bank_name()}")
    
    def find_parser(self, df: pd.DataFrame, filename: Optional[str] = None) -> Optional[BankParser]:
        """
        Find the appropriate parser for the given DataFrame.
        
        Args:
            df: The DataFrame to parse
            filename: Optional filename for additional context
            
        Returns:
            BankParser instance if found, None otherwise
        """
        for parser in self._parsers:
            try:
                if parser.can_parse(df, filename):
                    logger.info(f"Found parser for bank: {parser.get_bank_name()}")
                    return parser
            except Exception as e:
                logger.warning(f"Error checking parser {parser.get_bank_name()}: {e}")
                continue
        
        logger.warning("No suitable parser found for the file")
        return None
    
    def get_parser_by_bank_name(self, bank_name: str) -> Optional[BankParser]:
        """Get parser by bank name."""
        for parser in self._parsers:
            if parser.get_bank_name().lower() == bank_name.lower():
                return parser
        return None


# Global parser registry instance
_parser_registry = ParserRegistry()


def register_parser(parser: BankParser):
    """Register a bank parser in the global registry."""
    _parser_registry.register(parser)


def get_parser_registry() -> ParserRegistry:
    """Get the global parser registry."""
    return _parser_registry


class FileParser:
    """Main file parser that handles file reading and routing to bank parsers."""
    
    def __init__(self, parser_registry: Optional[ParserRegistry] = None):
        self.registry = parser_registry or _parser_registry
    
    def detect_file_type(self, file_path: Path) -> str:
        """
        Detect file type from extension.
        
        Args:
            file_path: Path to the file
            
        Returns:
            File type: 'excel', 'csv', or raises ValueError
        """
        suffix = file_path.suffix.lower()
        if suffix in ['.xlsx', '.xls']:
            return 'excel'
        elif suffix == '.csv':
            return 'csv'
        else:
            raise ValueError(f"Unsupported file type: {suffix}. Supported: .xlsx, .xls, .csv")
    
    def read_file(self, file_path: Path) -> pd.DataFrame:
        """
        Read file into pandas DataFrame.
        
        Args:
            file_path: Path to the file
            
        Returns:
            pandas DataFrame
        """
        file_type = self.detect_file_type(file_path)
        
        try:
            if file_type == 'excel':
                # Try reading all sheets, return first non-empty one
                excel_file = pd.ExcelFile(file_path)
                for sheet_name in excel_file.sheet_names:
                    df = pd.read_excel(file_path, sheet_name=sheet_name)
                    if not df.empty:
                        logger.info(f"Read sheet '{sheet_name}' from {file_path.name}")
                        return df
                raise ValueError("No data found in Excel file")
            else:  # CSV
                # Try different encodings
                encodings = ['utf-8', 'latin-1', 'iso-8859-1', 'cp1252']
                for encoding in encodings:
                    try:
                        df = pd.read_csv(file_path, encoding=encoding)
                        logger.info(f"Read CSV file {file_path.name} with encoding {encoding}")
                        return df
                    except UnicodeDecodeError:
                        continue
                raise ValueError(f"Could not read CSV file with any supported encoding: {file_path}")
        except Exception as e:
            logger.error(f"Error reading file {file_path}: {e}")
            raise
    
    def parse_file(
        self,
        file_path: Path,
        bank_name: Optional[str] = None
    ) -> List[StandardizedTransaction]:
        """
        Parse a file and return standardized transactions.
        
        Args:
            file_path: Path to the file to parse
            bank_name: Optional bank name to force a specific parser
            
        Returns:
            List of StandardizedTransaction objects
            
        Raises:
            ValueError: If file cannot be parsed or no suitable parser found
        """
        # Read file
        df = self.read_file(file_path)
        
        if df.empty:
            raise ValueError("File is empty or contains no data")
        
        # Find appropriate parser
        if bank_name:
            parser = self.registry.get_parser_by_bank_name(bank_name)
            if not parser:
                raise ValueError(f"No parser registered for bank: {bank_name}")
        else:
            parser = self.registry.find_parser(df, filename=file_path.name)
            if not parser:
                raise ValueError(
                    f"No suitable parser found for file: {file_path.name}. "
                    "Please register a parser for this bank format."
                )
        
        # Parse using the selected parser
        try:
            transactions = parser.parse(df, filename=file_path.name)
            logger.info(f"Parsed {len(transactions)} transactions from {file_path.name}")
            return transactions
        except Exception as e:
            logger.error(f"Error parsing file {file_path.name} with parser {parser.get_bank_name()}: {e}")
            raise


# Example bank parser implementation (for testing and as a template)
class ExampleBankParser(BankParser):
    """
    Example bank parser implementation.
    
    This serves as a template for creating bank-specific parsers.
    Developers should create similar parsers for their banks.
    """
    
    def get_bank_name(self) -> str:
        return "example_bank"
    
    def can_parse(self, df: pd.DataFrame, filename: Optional[str] = None) -> bool:
        """
        Check if this is an Example Bank file.
        
        Example: Check for specific column names or patterns.
        """
        # Example: Check for specific columns
        required_columns = ["date", "amount", "description"]
        return all(col.lower() in [c.lower() for c in df.columns] for col in required_columns)
    
    def parse(self, df: pd.DataFrame, filename: Optional[str] = None) -> List[StandardizedTransaction]:
        """
        Parse Example Bank format.
        
        Expected columns:
        - date: Transaction date
        - amount: Transaction amount
        - description: Transaction description
        - category: Optional category
        """
        transactions = []
        
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
                
                transaction = StandardizedTransaction(
                    bank_name=self.get_bank_name(),
                    date=trans_date,
                    amount=amount,
                    description=description,
                    category=category,
                    is_special=False  # Default, can be customized
                )
                transactions.append(transaction)
            except Exception as e:
                logger.warning(f"Skipping row due to error: {e}")
                continue
        
        return transactions


# Register example parser (can be removed or kept for testing)
# register_parser(ExampleBankParser())
