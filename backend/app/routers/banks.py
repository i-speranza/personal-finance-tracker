"""Bank API endpoints."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from ..database import get_db
from ..models import Bank
from ..schemas import Bank as BankSchema, BankCreate

router = APIRouter()


@router.get("/", response_model=List[BankSchema])
async def get_banks(
    db: Session = Depends(get_db),
):
    """Get all banks."""
    banks = db.query(Bank).order_by(Bank.name).all()
    return banks


@router.get("/{bank_id}", response_model=BankSchema)
async def get_bank(
    bank_id: int,
    db: Session = Depends(get_db),
):
    """Get a single bank by ID."""
    bank = db.query(Bank).filter(Bank.id == bank_id).first()
    if not bank:
        raise HTTPException(status_code=404, detail="Bank not found")
    return bank


@router.post("/", response_model=BankSchema, status_code=201)
async def create_bank(
    bank: BankCreate,
    db: Session = Depends(get_db),
):
    """Create a new bank."""
    # Check if bank with same name already exists
    existing_bank = db.query(Bank).filter(Bank.name == bank.name).first()
    if existing_bank:
        raise HTTPException(status_code=400, detail="Bank with this name already exists")
    
    db_bank = Bank(**bank.dict())
    db.add(db_bank)
    db.commit()
    db.refresh(db_bank)
    return db_bank
