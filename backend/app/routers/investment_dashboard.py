"""Read-only aggregate dashboard for the investment portfolio."""
from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from ..database import get_db
from ..investment_dashboard import build_investment_dashboard
from ..schemas import InvestmentDashboardResponse

router = APIRouter()


@router.get("/", response_model=InvestmentDashboardResponse)
def get_investment_dashboard(
    as_of_date: Optional[date] = Query(None, description="Snapshot date; defaults to latest quote date among open positions."),
    unit_chart_asset_pk: Optional[int] = Query(None, description="Asset PK for unit valore vs unit controvalore chart."),
    db: Session = Depends(get_db),
):
    """
    Snapshot metrics, per-position rows, geographic mix, time series, and XIRR.

    IRR uses purchase/sell cash amounts in portfolio currency (fees included); `plus_minus` is not used.
    """
    raw = build_investment_dashboard(db, as_of_date=as_of_date, unit_chart_asset_pk=unit_chart_asset_pk)
    return InvestmentDashboardResponse.model_validate(raw)
