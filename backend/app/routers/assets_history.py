"""Assets History API endpoints."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date

from ..database import get_db
from ..models import AssetsHistory
from ..schemas import AssetsHistory as AssetsHistorySchema, AssetsHistoryCreate

router = APIRouter()


@router.get("/", response_model=List[AssetsHistorySchema])
async def get_assets_history(
    bank_name: Optional[str] = None,
    account_name: Optional[str] = None,
    asset_type: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: Session = Depends(get_db),
):
    """Get all assets history entries, optionally filtered."""
    query = db.query(AssetsHistory)
    
    if bank_name:
        query = query.filter(AssetsHistory.bank_name == bank_name)
    
    if account_name:
        query = query.filter(AssetsHistory.account_name == account_name)
    
    if asset_type:
        query = query.filter(AssetsHistory.asset_type == asset_type)
    
    if start_date:
        query = query.filter(AssetsHistory.date >= start_date)
    
    if end_date:
        query = query.filter(AssetsHistory.date <= end_date)
    
    assets = query.order_by(AssetsHistory.date, AssetsHistory.bank_name, AssetsHistory.account_name).all()
    return assets


@router.get("/{asset_id}", response_model=AssetsHistorySchema)
async def get_asset_history(
    asset_id: int,
    db: Session = Depends(get_db),
):
    """Get a single assets history entry by ID."""
    asset = db.query(AssetsHistory).filter(AssetsHistory.id == asset_id).first()
    if not asset:
        raise HTTPException(status_code=404, detail="Assets history entry not found")
    return asset


@router.post("/", response_model=AssetsHistorySchema, status_code=201)
async def create_asset_history(
    asset: AssetsHistoryCreate,
    db: Session = Depends(get_db),
):
    """Create a new assets history entry."""
    db_asset = AssetsHistory(**asset.dict())
    db.add(db_asset)
    db.commit()
    db.refresh(db_asset)
    return db_asset


@router.put("/{asset_id}", response_model=AssetsHistorySchema)
async def update_asset_history(
    asset_id: int,
    asset_update: AssetsHistoryCreate,
    db: Session = Depends(get_db),
):
    """Update an existing assets history entry."""
    db_asset = db.query(AssetsHistory).filter(AssetsHistory.id == asset_id).first()
    if not db_asset:
        raise HTTPException(status_code=404, detail="Assets history entry not found")
    
    # Update all fields
    update_data = asset_update.dict()
    for field, value in update_data.items():
        setattr(db_asset, field, value)
    
    db.commit()
    db.refresh(db_asset)
    return db_asset


@router.delete("/{asset_id}", status_code=204)
async def delete_asset_history(
    asset_id: int,
    db: Session = Depends(get_db),
):
    """Delete an assets history entry."""
    db_asset = db.query(AssetsHistory).filter(AssetsHistory.id == asset_id).first()
    if not db_asset:
        raise HTTPException(status_code=404, detail="Assets history entry not found")
    
    db.delete(db_asset)
    db.commit()
    return None
