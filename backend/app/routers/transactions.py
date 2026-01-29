"""Transaction API endpoints."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import date

from ..database import get_db
from ..models import Transaction
from ..schemas import Transaction as TransactionSchema, TransactionCreate, TransactionUpdate

router = APIRouter()


@router.get("/", response_model=List[TransactionSchema])
async def get_transactions(
    skip: int = Query(0, ge=0),
    limit: Optional[int] = Query(None, ge=1),
    bank_name: Optional[str] = None,
    account_name: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """Get all transactions with optional filtering."""
    query = db.query(Transaction)
    
    # Apply filters
    if bank_name:
        query = query.filter(Transaction.bank_name == bank_name)
    if account_name:
        query = query.filter(Transaction.account_name == account_name)
    if start_date:
        try:
            start = date.fromisoformat(start_date)
            query = query.filter(Transaction.date >= start)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid start_date format. Use YYYY-MM-DD")
    if end_date:
        try:
            end = date.fromisoformat(end_date)
            query = query.filter(Transaction.date <= end)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid end_date format. Use YYYY-MM-DD")
    
    # Order by date descending
    query = query.order_by(Transaction.date.desc())
    
    # Apply pagination (if limit is provided)
    if limit:
        transactions = query.offset(skip).limit(limit).all()
    else:
        # If no limit, fetch all (with offset)
        transactions = query.offset(skip).all()
    
    return transactions


@router.get("/types", response_model=List[str])
async def get_transaction_types(db: Session = Depends(get_db)):
    """Get all distinct transaction types."""
    result = db.query(Transaction.transaction_type).distinct().filter(
        Transaction.transaction_type.isnot(None),
        Transaction.transaction_type != ""
    ).order_by(Transaction.transaction_type).all()
    return [r[0] for r in result]


@router.get("/{transaction_id}", response_model=TransactionSchema)
async def get_transaction(
    transaction_id: int,
    db: Session = Depends(get_db),
):
    """Get a single transaction by ID."""
    transaction = db.query(Transaction).filter(Transaction.id == transaction_id).first()
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return transaction


@router.post("/", response_model=TransactionSchema, status_code=201)
async def create_transaction(
    transaction: TransactionCreate,
    db: Session = Depends(get_db),
):
    """Create a new transaction."""
    db_transaction = Transaction(**transaction.dict())
    db.add(db_transaction)
    db.commit()
    db.refresh(db_transaction)
    return db_transaction


@router.put("/{transaction_id}", response_model=TransactionSchema)
async def update_transaction(
    transaction_id: int,
    transaction_update: TransactionUpdate,
    db: Session = Depends(get_db),
):
    """Update an existing transaction."""
    db_transaction = db.query(Transaction).filter(Transaction.id == transaction_id).first()
    if not db_transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    # Update only provided fields
    update_data = transaction_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_transaction, field, value)
    
    db.commit()
    db.refresh(db_transaction)
    return db_transaction


@router.delete("/{transaction_id}", status_code=204)
async def delete_transaction(
    transaction_id: int,
    db: Session = Depends(get_db),
):
    """Delete a transaction."""
    db_transaction = db.query(Transaction).filter(Transaction.id == transaction_id).first()
    if not db_transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    db.delete(db_transaction)
    db.commit()
    return None
