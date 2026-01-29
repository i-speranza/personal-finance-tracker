"""Upload API endpoints for transaction file processing."""
import shutil
import logging
from pathlib import Path
from datetime import date
from typing import List, Optional, Any, Dict
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from pydantic import BaseModel

from ..database import get_db
from ..models import Transaction
from ..transactions_preprocessing import (
    TransactionsFileParser,
    get_transactions_parser_registry,
    StandardizedTransaction
)
from ..harmonization import detect_duplicates

# Import parsers to register them
from ..transactions_preprocessing_intesa import IntesaParser
from ..transactions_preprocessing_allianz import AllianzParser
from ..transactions_preprocessing import register_transactions_parser

logger = logging.getLogger(__name__)

router = APIRouter()

# Register parsers on import
register_transactions_parser(IntesaParser())
register_transactions_parser(AllianzParser())

# Data directory for storing raw files
DATA_DIR = Path(__file__).parent.parent.parent / "data"
DATA_DIR.mkdir(exist_ok=True)


# Pydantic models for request/response
class UploadWarning(BaseModel):
    """Warning from upload processing."""
    type: str  # 'filtered_row', 'duplicate', 'parsing_error'
    message: str
    details: Optional[Dict[str, Any]] = None


class ParsedTransaction(BaseModel):
    """Parsed transaction data."""
    bank_name: str
    account_name: str
    date: date
    amount: float
    description: Optional[str] = None
    details: Optional[str] = None
    category: Optional[str] = None
    transaction_type: Optional[str] = None
    is_special: bool = False


class PreprocessingResult(BaseModel):
    """Result from preprocessing step."""
    transactions: List[ParsedTransaction]
    warnings: List[UploadWarning]
    date_range: Dict[str, str]  # first_date, last_date
    saved_filename: str


class HarmonizationResult(BaseModel):
    """Result from harmonization step."""
    new_transactions: List[ParsedTransaction]
    duplicate_transactions: List[ParsedTransaction]


class TransactionToCommit(BaseModel):
    """Transaction ready to be committed."""
    bank_name: str
    account_name: str
    date: date
    amount: float
    description: Optional[str] = None
    details: Optional[str] = None
    category: Optional[str] = None
    transaction_type: Optional[str] = None
    is_special: bool = False


class CommitRequest(BaseModel):
    """Request to commit transactions."""
    transactions: List[TransactionToCommit]


class CommitResult(BaseModel):
    """Result from commit step."""
    inserted_count: int
    message: str


@router.post("/preprocess", response_model=PreprocessingResult)
async def preprocess_file(
    file: UploadFile = File(...),
    bank_name: str = Form(...),
    account_name: str = Form(...),
    db: Session = Depends(get_db)
):
    """
    Preprocess an uploaded transaction file.
    
    - Parses the file using the appropriate bank parser
    - Returns parsed transactions with warnings
    - Saves the raw file with standardized naming
    """
    # Validate file extension
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")
    
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in ['.xlsx', '.xls', '.csv']:
        raise HTTPException(
            status_code=400, 
            detail=f"Unsupported file type: {file_ext}. Supported: .xlsx, .xls, .csv"
        )
    
    # Check if parser exists for the bank
    registry = get_transactions_parser_registry()
    parser = registry.get_parser_by_bank_name(bank_name)
    if not parser:
        raise HTTPException(
            status_code=400, 
            detail=f"No parser registered for bank: {bank_name}. Available: intesa, allianz"
        )
    
    # Save uploaded file temporarily
    temp_path = DATA_DIR / f"temp_{file.filename}"
    try:
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        warnings: List[UploadWarning] = []
        
        # Parse the file
        file_parser = TransactionsFileParser()
        
        # Parse file
        try:
            df = file_parser.parse_file(temp_path, bank_name=bank_name)
        except Exception as e:
            warnings.append(UploadWarning(
                type="parsing_error",
                message=f"Error parsing file: {str(e)}",
                details={"error": str(e)}
            ))
            raise HTTPException(status_code=400, detail=f"Error parsing file: {str(e)}")
        
        if df.empty:
            raise HTTPException(status_code=400, detail="No transactions found in file")
        
        # Add account_name to transactions
        df['account_name'] = account_name
        
        # Check for duplicates within the file
        duplicate_mask = df.duplicated(subset=['date', 'amount', 'description'], keep=False)
        if duplicate_mask.any():
            dup_count = duplicate_mask.sum()
            warnings.append(UploadWarning(
                type="duplicate",
                message=f"Found {dup_count} duplicate transactions within the file",
                details={"count": int(dup_count)}
            ))
        
        # Get date range
        first_date = df['date'].min()
        last_date = df['date'].max()
        
        # Format dates for filename
        first_date_str = first_date.strftime('%Y_%m_%d') if hasattr(first_date, 'strftime') else str(first_date).replace('-', '_')
        last_date_str = last_date.strftime('%Y_%m_%d') if hasattr(last_date, 'strftime') else str(last_date).replace('-', '_')
        
        # Generate standardized filename
        safe_bank = bank_name.lower().replace(' ', '_')
        safe_account = account_name.lower().replace(' ', '_')
        new_filename = f"{safe_bank}_{safe_account}_from_{first_date_str}_to_{last_date_str}{file_ext}"
        final_path = DATA_DIR / new_filename
        
        # Move temp file to final location (overwrite if exists)
        if final_path.exists():
            final_path.unlink()
        shutil.move(str(temp_path), str(final_path))
        
        # Convert to list of ParsedTransaction
        transactions = []
        for _, row in df.iterrows():
            trans_date = row['date']
            if hasattr(trans_date, 'date'):
                trans_date = trans_date.date()
            elif hasattr(trans_date, 'strftime'):
                pass  # already a date
            
            transactions.append(ParsedTransaction(
                bank_name=str(row['bank_name']),
                account_name=account_name,
                date=trans_date,
                amount=float(row['amount']),
                description=str(row['description']) if row.get('description') else None,
                details=str(row['details']) if row.get('details') else None,
                category=str(row['category']) if row.get('category') else None,
                transaction_type=str(row['transaction_type']) if row.get('transaction_type') else None,
                is_special=bool(row.get('is_special', False))
            ))
        
        return PreprocessingResult(
            transactions=transactions,
            warnings=warnings,
            date_range={
                "first_date": str(first_date),
                "last_date": str(last_date)
            },
            saved_filename=new_filename
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in preprocess: {e}")
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")
    finally:
        # Clean up temp file if it still exists
        if temp_path.exists():
            temp_path.unlink()


@router.post("/harmonize", response_model=HarmonizationResult)
async def harmonize_transactions(
    transactions: List[ParsedTransaction],
    db: Session = Depends(get_db)
):
    """
    Harmonize parsed transactions against existing database.
    
    - Checks for duplicates in the database
    - Returns new transactions and duplicates separately
    """
    if not transactions:
        return HarmonizationResult(
            new_transactions=[],
            duplicate_transactions=[]
        )
    
    # Convert to StandardizedTransaction objects for detect_duplicates
    standardized = []
    for t in transactions:
        standardized.append(StandardizedTransaction(
            bank_name=t.bank_name,
            account_name=t.account_name,
            date=t.date,
            amount=t.amount,
            description=t.description,
            details=t.details,
            category=t.category,
            transaction_type=t.transaction_type,
            is_special=t.is_special
        ))
    
    # Detect duplicates
    new_transactions_std, duplicate_info_list = detect_duplicates(db, standardized)
    
    # Convert back to ParsedTransaction
    new_transactions = []
    for t in new_transactions_std:
        new_transactions.append(ParsedTransaction(
            bank_name=t.bank_name,
            account_name=t.account_name,
            date=t.date,
            amount=t.amount,
            description=t.description,
            details=t.details,
            category=t.category,
            transaction_type=t.transaction_type,
            is_special=t.is_special
        ))
    
    # Convert duplicates info to ParsedTransaction
    duplicate_transactions = []
    for d in duplicate_info_list:
        duplicate_transactions.append(ParsedTransaction(
            bank_name=d['bank_name'],
            account_name=d['account_name'],
            date=d['date'],
            amount=d['amount'],
            description=d.get('description'),
            details=d.get('details'),
            category=d.get('category'),
            transaction_type=d.get('transaction_type'),
            is_special=False
        ))
    
    return HarmonizationResult(
        new_transactions=new_transactions,
        duplicate_transactions=duplicate_transactions
    )


@router.post("/commit", response_model=CommitResult)
async def commit_transactions(
    request: CommitRequest,
    db: Session = Depends(get_db)
):
    """
    Commit reviewed transactions to the database.
    
    - Inserts all provided transactions
    - Returns count of inserted transactions
    """
    if not request.transactions:
        return CommitResult(
            inserted_count=0,
            message="No transactions to commit"
        )
    
    inserted_count = 0
    try:
        for t in request.transactions:
            db_transaction = Transaction(
                bank_name=t.bank_name,
                account_name=t.account_name,
                date=t.date,
                amount=t.amount,
                description=t.description,
                details=t.details,
                category=t.category,
                transaction_type=t.transaction_type,
                is_special=t.is_special
            )
            db.add(db_transaction)
            inserted_count += 1
        
        db.commit()
        
        return CommitResult(
            inserted_count=inserted_count,
            message=f"Successfully committed {inserted_count} transactions"
        )
    except Exception as e:
        db.rollback()
        logger.error(f"Error committing transactions: {e}")
        raise HTTPException(status_code=500, detail=f"Error committing transactions: {str(e)}")
