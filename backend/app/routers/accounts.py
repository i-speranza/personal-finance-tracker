"""Account API endpoints."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional

from ..database import get_db
from ..models import Account
from ..schemas import Account as AccountSchema, AccountCreate, AccountUpdate

router = APIRouter()


@router.get("/", response_model=List[AccountSchema])
async def get_accounts(
    bank_name: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """Get all accounts, optionally filtered by bank_name."""
    query = db.query(Account)
    
    if bank_name:
        query = query.filter(Account.bank_name == bank_name)
    
    accounts = query.order_by(Account.bank_name, Account.account_name).all()
    return accounts


@router.get("/{account_id}", response_model=AccountSchema)
async def get_account(
    account_id: int,
    db: Session = Depends(get_db),
):
    """Get a single account by ID."""
    account = db.query(Account).filter(Account.id == account_id).first()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    return account


@router.post("/", response_model=AccountSchema, status_code=201)
async def create_account(
    account: AccountCreate,
    db: Session = Depends(get_db),
):
    """Create a new account."""
    # Check if account already exists
    existing_account = db.query(Account).filter(
        Account.bank_name == account.bank_name,
        Account.account_name == account.account_name
    ).first()
    if existing_account:
        raise HTTPException(status_code=400, detail="Account already exists")
    
    db_account = Account(**account.dict())
    db.add(db_account)
    db.commit()
    db.refresh(db_account)
    return db_account


@router.put("/{account_id}", response_model=AccountSchema)
async def update_account(
    account_id: int,
    account_update: AccountUpdate,
    db: Session = Depends(get_db),
):
    """Update an existing account."""
    db_account = db.query(Account).filter(Account.id == account_id).first()
    if not db_account:
        raise HTTPException(status_code=404, detail="Account not found")
    
    # Update only provided fields
    update_data = account_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_account, field, value)
    
    db.commit()
    db.refresh(db_account)
    return db_account
