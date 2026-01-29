"""Account API endpoints."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, distinct
from typing import List, Optional
from datetime import date
from pydantic import BaseModel

from ..database import get_db
from ..models import Account, Transaction, AssetsHistory, AssetType
from ..schemas import Account as AccountSchema, AccountCreate, AccountUpdate, AssetTypeEnum


class AccountWithLastDate(BaseModel):
    """Account with last transaction date."""
    id: int
    bank_name: str
    account_name: str
    asset_type: Optional[AssetTypeEnum] = None
    status: bool
    last_transaction_date: Optional[date] = None

    class Config:
        from_attributes = True


class SyncAccountsResult(BaseModel):
    """Result from syncing accounts from assets history."""
    created_count: int
    updated_count: int
    accounts: List[AccountSchema]


router = APIRouter()


@router.post("/sync-from-assets-history", response_model=SyncAccountsResult)
async def sync_accounts_from_assets_history(
    db: Session = Depends(get_db),
):
    """
    Sync accounts table from assets_history table.
    Creates new accounts if they don't exist and updates asset_type if different.
    """
    # Get distinct account combinations from assets_history
    assets_accounts = db.query(
        AssetsHistory.bank_name,
        AssetsHistory.account_name,
        AssetsHistory.asset_type
    ).distinct().all()
    
    created_count = 0
    updated_count = 0
    result_accounts = []
    
    for bank_name, account_name, asset_type in assets_accounts:
        # Check if account already exists
        existing_account = db.query(Account).filter(
            Account.bank_name == bank_name,
            Account.account_name == account_name
        ).first()
        
        if existing_account:
            # Update asset_type if different
            if existing_account.asset_type != asset_type:
                existing_account.asset_type = asset_type
                updated_count += 1
            result_accounts.append(existing_account)
        else:
            # Create new account
            new_account = Account(
                bank_name=bank_name,
                account_name=account_name,
                asset_type=asset_type,
                status=True
            )
            db.add(new_account)
            db.flush()
            created_count += 1
            result_accounts.append(new_account)
    
    db.commit()
    
    # Refresh all accounts
    for account in result_accounts:
        db.refresh(account)
    
    return SyncAccountsResult(
        created_count=created_count,
        updated_count=updated_count,
        accounts=result_accounts
    )


@router.get("/", response_model=List[AccountSchema])
async def get_accounts(
    bank_name: Optional[str] = None,
    asset_type: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """Get all accounts, optionally filtered by bank_name and/or asset_type."""
    query = db.query(Account)
    
    if bank_name:
        query = query.filter(Account.bank_name == bank_name)
    
    if asset_type:
        query = query.filter(Account.asset_type == asset_type)
    
    accounts = query.order_by(Account.bank_name, Account.account_name).all()
    return accounts


@router.get("/last-transaction-dates", response_model=List[AccountWithLastDate])
async def get_accounts_with_last_transaction_dates(
    active_only: bool = True,
    asset_type: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """
    Get all accounts with their last transaction date.
    
    - active_only: If True (default), only return active accounts (status=True)
    - asset_type: Filter by asset type ('cash' or 'investment')
    """
    # Build query for accounts
    query = db.query(Account)
    if active_only:
        query = query.filter(Account.status == True)
    if asset_type:
        query = query.filter(Account.asset_type == asset_type)
    
    accounts = query.order_by(Account.bank_name, Account.account_name).all()
    
    # Get last transaction date for each account
    result = []
    for account in accounts:
        last_date = db.query(func.max(Transaction.date)).filter(
            Transaction.bank_name == account.bank_name,
            Transaction.account_name == account.account_name
        ).scalar()
        
        result.append(AccountWithLastDate(
            id=account.id,
            bank_name=account.bank_name,
            account_name=account.account_name,
            asset_type=account.asset_type,
            status=account.status,
            last_transaction_date=last_date
        ))
    
    return result


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
