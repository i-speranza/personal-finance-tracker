"""Raw transactions router for viewing bank-specific raw data."""
from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import IntesaRawTransaction, AllianzRawTransaction
from ..schemas import IntesaRawTransaction as IntesaRawTransactionSchema
from ..schemas import AllianzRawTransaction as AllianzRawTransactionSchema

router = APIRouter(prefix="/raw-transactions", tags=["Raw Transactions"])


@router.get("/intesa", response_model=List[IntesaRawTransactionSchema])
def get_intesa_raw_transactions(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=10000, ge=1, le=50000),
    db: Session = Depends(get_db)
):
    """Get all Intesa raw transactions."""
    query = db.query(IntesaRawTransaction).order_by(IntesaRawTransaction.data.desc())
    return query.offset(skip).limit(limit).all()


@router.get("/allianz", response_model=List[AllianzRawTransactionSchema])
def get_allianz_raw_transactions(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=10000, ge=1, le=50000),
    db: Session = Depends(get_db)
):
    """Get all Allianz raw transactions."""
    query = db.query(AllianzRawTransaction).order_by(AllianzRawTransaction.data_contabile.desc())
    return query.offset(skip).limit(limit).all()


@router.get("/intesa/count")
def get_intesa_count(db: Session = Depends(get_db)):
    """Get count of Intesa raw transactions."""
    return {"count": db.query(IntesaRawTransaction).count()}


@router.get("/allianz/count")
def get_allianz_count(db: Session = Depends(get_db)):
    """Get count of Allianz raw transactions."""
    return {"count": db.query(AllianzRawTransaction).count()}
