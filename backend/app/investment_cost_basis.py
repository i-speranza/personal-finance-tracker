"""Weighted-average acquisition cost for investment portfolio trades (portfolio currency per unit)."""
from __future__ import annotations

from typing import List, Optional

from sqlalchemy.orm import Session

from .models import InvestmentPortfolioTransaction, InvPortfolioTxType

# Treat as zero when comparing float quantities
_QTY_EPS = 1e-9


def _purchase_unit_cost_in_portfolio_currency(tx: InvestmentPortfolioTransaction) -> float:
    """Full acquisition cost per unit in portfolio currency: (qty × price × FX + fees) / qty."""
    qty = float(tx.quantity)
    if qty <= _QTY_EPS:
        return float(tx.unit_price) * float(tx.exchange_rate)
    gross = qty * float(tx.unit_price) * float(tx.exchange_rate) + float(tx.fees or 0.0)
    return gross / qty


def recalculate_average_unit_costs_for_asset(db: Session, asset_pk: int) -> Optional[float]:
    """
    Replay all trades for asset_pk in chronological order and set average_unit_cost_after_trade
    on purchase rows only (null on sells). Each purchase blends (quantity × unit_price × exchange_rate + fees) / quantity
    into the running weighted average. Returns current average if net quantity > 0.
    """
    rows: List[InvestmentPortfolioTransaction] = (
        db.query(InvestmentPortfolioTransaction)
        .filter(InvestmentPortfolioTransaction.asset_pk == asset_pk)
        .order_by(InvestmentPortfolioTransaction.trade_date, InvestmentPortfolioTransaction.id)
        .all()
    )

    shares_held = 0.0
    avg_unit: Optional[float] = None

    for tx in rows:
        if tx.transaction_type == InvPortfolioTxType.purchase:
            ep = _purchase_unit_cost_in_portfolio_currency(tx)
            qty = float(tx.quantity)
            if shares_held <= _QTY_EPS:
                new_avg = ep
            else:
                new_avg = (avg_unit * shares_held + ep * qty) / (shares_held + qty)
            tx.average_unit_cost_after_trade = new_avg
            avg_unit = new_avg
            shares_held += qty
        else:
            tx.average_unit_cost_after_trade = None
            shares_held -= float(tx.quantity)

    db.flush()
    if shares_held > _QTY_EPS and avg_unit is not None:
        return avg_unit
    return None


def recalculate_average_unit_costs_for_all_assets(db: Session) -> None:
    """Backfill or repair cost-basis snapshots for every asset that has portfolio transactions."""
    pks = (
        db.query(InvestmentPortfolioTransaction.asset_pk)
        .distinct()
        .order_by(InvestmentPortfolioTransaction.asset_pk)
        .all()
    )
    for (apk,) in pks:
        recalculate_average_unit_costs_for_asset(db, int(apk))


def current_average_unit_cost_without_flush(db: Session, asset_pk: int) -> Optional[float]:
    """
    Read-only replay for API responses (does not persist or flush).
    Caller must not rely on side effects on ORM instances.
    """
    rows: List[InvestmentPortfolioTransaction] = (
        db.query(InvestmentPortfolioTransaction)
        .filter(InvestmentPortfolioTransaction.asset_pk == asset_pk)
        .order_by(InvestmentPortfolioTransaction.trade_date, InvestmentPortfolioTransaction.id)
        .all()
    )
    shares_held = 0.0
    avg_unit: Optional[float] = None
    for tx in rows:
        if tx.transaction_type == InvPortfolioTxType.purchase:
            ep = _purchase_unit_cost_in_portfolio_currency(tx)
            qty = float(tx.quantity)
            if shares_held <= _QTY_EPS:
                new_avg = ep
            else:
                new_avg = (avg_unit * shares_held + ep * qty) / (shares_held + qty)
            avg_unit = new_avg
            shares_held += qty
        else:
            shares_held -= float(tx.quantity)
    if shares_held > _QTY_EPS and avg_unit is not None:
        return avg_unit
    return None
