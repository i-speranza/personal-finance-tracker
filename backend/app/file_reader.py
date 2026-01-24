"""
File reader module for handling files.

This module provides functionality to read and parse files in various formats (Excel and CSV).
It includes automatic file type detection, encoding handling for CSV files, and support for reading multiple Excel sheets.
"""

import pandas as pd
from pathlib import Path
from typing import Optional
import logging

logger = logging.getLogger(__name__)    

class FileReader:
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

    def read_file(self, file_path: Path, skiprows: Optional[int] = None, skipfooter: Optional[int] = None) -> pd.DataFrame:
        """
        Read file into pandas DataFrame.

        Args:
            file_path: Path to the file
            skiprows: Optional number of rows to skip from the top
            skipfooter: Optional number of rows to skip from the bottom
        Returns:
            pandas DataFrame
        """
        file_type = self.detect_file_type(file_path)

        try:
            if file_type == 'excel':
                # Try reading all sheets, return first non-empty one
                excel_file = pd.ExcelFile(file_path)
                for sheet_name in excel_file.sheet_names:
                    df = pd.read_excel(file_path, sheet_name=sheet_name, skiprows=skiprows, skipfooter=skipfooter)
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