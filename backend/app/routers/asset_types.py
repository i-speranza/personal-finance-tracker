"""Asset Types router."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from ..database import get_db
from .. import models, schemas

router = APIRouter()


@router.get("/", response_model=List[schemas.AssetTypeRef])
def get_asset_types(db: Session = Depends(get_db)):
    """Get all asset types."""
    return db.query(models.AssetTypeRef).order_by(models.AssetTypeRef.name).all()


@router.post("/", response_model=schemas.AssetTypeRef)
def create_asset_type(
    asset_type: schemas.AssetTypeRefCreate,
    db: Session = Depends(get_db)
):
    """Create a new asset type."""
    # Check if asset type with same name already exists
    existing = db.query(models.AssetTypeRef).filter(
        models.AssetTypeRef.name == asset_type.name.lower()
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Asset type with this name already exists")
    
    db_asset_type = models.AssetTypeRef(
        name=asset_type.name.lower(),
        display_name=asset_type.display_name
    )
    db.add(db_asset_type)
    db.commit()
    db.refresh(db_asset_type)
    return db_asset_type


@router.delete("/{asset_type_id}")
def delete_asset_type(asset_type_id: int, db: Session = Depends(get_db)):
    """Delete an asset type (only if not in use)."""
    asset_type = db.query(models.AssetTypeRef).filter(
        models.AssetTypeRef.id == asset_type_id
    ).first()
    
    if not asset_type:
        raise HTTPException(status_code=404, detail="Asset type not found")
    
    # Check if asset type is in use by any account
    account_count = db.query(models.Account).filter(
        models.Account.asset_type == asset_type.name
    ).count()
    
    if account_count > 0:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot delete asset type '{asset_type.display_name}' - it is used by {account_count} account(s)"
        )
    
    # Check if asset type is in use by any assets history entry
    history_count = db.query(models.AssetsHistory).filter(
        models.AssetsHistory.asset_type == asset_type.name
    ).count()
    
    if history_count > 0:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot delete asset type '{asset_type.display_name}' - it is used by {history_count} assets history entry/entries"
        )
    
    db.delete(asset_type)
    db.commit()
    return {"message": "Asset type deleted successfully"}
