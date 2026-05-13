"""Mark-to-market portfolio valuations (user-entered unit prices by date)."""
from datetime import date
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import InvestmentPortfolioAsset, InvestmentPortfolioMarketQuote
from ..schemas import (
    InvestmentPortfolioMarketQuotesBulk,
    InvestmentPortfolioMarketQuotesBulkResult,
    InvestmentPortfolioMarketQuoteResponse,
)

router = APIRouter()


@router.post("/bulk", response_model=InvestmentPortfolioMarketQuotesBulkResult)
def bulk_upsert_market_quotes(body: InvestmentPortfolioMarketQuotesBulk, db: Session = Depends(get_db)):
    errors: List[str] = []
    upserted = 0
    for line in body.quotes:
        asset = db.query(InvestmentPortfolioAsset).filter(InvestmentPortfolioAsset.id == line.asset_pk).first()
        if not asset:
            errors.append(f"unknown asset_pk {line.asset_pk}")
            continue
        existing = (
            db.query(InvestmentPortfolioMarketQuote)
            .filter(
                InvestmentPortfolioMarketQuote.as_of_date == body.as_of_date,
                InvestmentPortfolioMarketQuote.asset_pk == line.asset_pk,
            )
            .first()
        )
        if existing:
            existing.market_unit_price = line.market_unit_price
        else:
            db.add(
                InvestmentPortfolioMarketQuote(
                    as_of_date=body.as_of_date,
                    asset_pk=line.asset_pk,
                    market_unit_price=line.market_unit_price,
                )
            )
        upserted += 1
    db.commit()
    return InvestmentPortfolioMarketQuotesBulkResult(upserted=upserted, errors=errors)


@router.get("/", response_model=List[InvestmentPortfolioMarketQuoteResponse])
def list_market_quotes(
    as_of_date: Optional[date] = Query(None),
    asset_pk: Optional[int] = Query(None),
    db: Session = Depends(get_db),
):
    q = db.query(InvestmentPortfolioMarketQuote)
    if as_of_date is not None:
        q = q.filter(InvestmentPortfolioMarketQuote.as_of_date == as_of_date)
    if asset_pk is not None:
        q = q.filter(InvestmentPortfolioMarketQuote.asset_pk == asset_pk)
    if as_of_date is None and asset_pk is None:
        raise HTTPException(status_code=400, detail="Provide query as_of_date and/or asset_pk")
    return q.order_by(
        InvestmentPortfolioMarketQuote.as_of_date.desc(),
        InvestmentPortfolioMarketQuote.asset_pk,
    ).all()
