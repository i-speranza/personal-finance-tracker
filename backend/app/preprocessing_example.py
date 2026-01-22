"""
Example usage of the preprocessing module.

This file demonstrates how to:
1. Create a custom bank parser
2. Register it
3. Use the FileParser to parse files

Developers should create their own parser classes following this pattern.
"""

from pathlib import Path
from .preprocessing import (
    BankParser,
    StandardizedTransaction,
    FileParser,
    register_parser,
    get_parser_registry
)
import pandas as pd
from typing import Optional


class MyBankParser(BankParser):
    """
    Example custom bank parser.
    
    Replace this with your actual bank's format.
    """
    
    def get_bank_name(self) -> str:
        return "my_bank"  # Replace with your bank name
    
    def can_parse(self, df: pd.DataFrame, filename: Optional[str] = None) -> bool:
        """
        Implement logic to detect if this file is from your bank.
        
        Examples:
        - Check for specific column names
        - Check for specific values in cells
        - Check filename pattern
        """
        # Example: Check for specific columns
        columns_lower = [col.lower() for col in df.columns]
        return "transaction_date" in columns_lower and "amount" in columns_lower
    
    def parse(self, df: pd.DataFrame, filename: Optional[str] = None) -> list[StandardizedTransaction]:
        """
        Parse your bank's specific format.
        
        Steps:
        1. Clean column names
        2. Map bank columns to standard fields
        3. Normalize dates and amounts
        4. Create StandardizedTransaction objects
        """
        transactions = []
        
        # Clean column names
        df.columns = df.columns.str.lower().str.strip()
        
        # Map your bank's columns to standard fields
        # Adjust these based on your actual file format
        date_col = "transaction_date"  # Your bank's date column
        amount_col = "amount"  # Your bank's amount column
        description_col = "description"  # Your bank's description column
        category_col = "category"  # Optional
        
        for _, row in df.iterrows():
            try:
                # Extract and normalize
                trans_date = self.normalize_date(row[date_col])
                amount = self.normalize_amount(row[amount_col])
                description = str(row[description_col]) if pd.notna(row.get(description_col)) else None
                category = str(row[category_col]) if pd.notna(row.get(category_col)) else None
                
                # Create standardized transaction
                transaction = StandardizedTransaction(
                    bank_name=self.get_bank_name(),
                    date=trans_date,
                    amount=amount,
                    description=description,
                    category=category,
                    is_special=False  # Set based on your logic
                )
                transactions.append(transaction)
            except Exception as e:
                # Log and skip invalid rows
                print(f"Skipping row: {e}")
                continue
        
        return transactions


def example_usage():
    """Example of how to use the preprocessing module."""
    
    # Step 1: Create and register your parser
    my_parser = MyBankParser()
    register_parser(my_parser)
    
    # Step 2: Create a FileParser instance
    parser = FileParser()
    
    # Step 3: Parse a file
    file_path = Path("path/to/your/bank/statement.xlsx")
    try:
        transactions = parser.parse_file(file_path)
        print(f"Parsed {len(transactions)} transactions")
        
        # Step 4: Use the transactions (e.g., insert into database)
        for trans in transactions:
            print(f"{trans.date}: {trans.amount} - {trans.description}")
            # Insert into database using trans.to_dict()
            
    except ValueError as e:
        print(f"Error parsing file: {e}")


def example_with_specific_bank():
    """Example of parsing with a specific bank parser."""
    
    parser = FileParser()
    file_path = Path("path/to/your/bank/statement.csv")
    
    # Force a specific bank parser
    try:
        transactions = parser.parse_file(file_path, bank_name="my_bank")
        print(f"Parsed {len(transactions)} transactions")
    except ValueError as e:
        print(f"Error: {e}")


def example_testing_parser():
    """Example of testing a parser with sample data."""
    
    # Create sample DataFrame matching your bank's format
    sample_data = pd.DataFrame({
        "transaction_date": ["2024-01-15", "2024-01-16", "2024-01-17"],
        "amount": [100.50, -50.25, 200.00],
        "description": ["Purchase", "Refund", "Salary"],
        "category": ["Expense", "Income", "Income"]
    })
    
    # Create and test parser
    my_parser = MyBankParser()
    
    # Test can_parse
    if my_parser.can_parse(sample_data):
        print("Parser can handle this format!")
        
        # Test parsing
        transactions = my_parser.parse(sample_data)
        print(f"Parsed {len(transactions)} transactions")
        
        for trans in transactions:
            print(f"{trans.date}: {trans.amount} - {trans.description}")
    else:
        print("Parser cannot handle this format")


if __name__ == "__main__":
    # Run examples
    example_testing_parser()
