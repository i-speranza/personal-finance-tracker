"""Weighted-average acquisition cost for investment portfolio trades (portfolio currency per unit)."""
from __future__ import annotations

from datetime import date
from typing import Iterable, List, Optional, Tuple

from sqlalchemy.orm import Session

from .models import InvestmentPortfolioAsset, InvestmentPortfolioTransaction, InvPortfolioKind, InvPortfolioTxType

# Treat as zero when comparing float quantities
_QTY_EPS = 1e-9


def _effective_trade_quantity(tx: InvestmentPortfolioTransaction, bond_scale: bool) -> float:
    """Italian bond listings: stored nominal is ×100 vs EUR notionals — divide for money math."""
    q = float(tx.quantity)
    return q / 100.0 if bond_scale else q


def _purchase_unit_cost_in_portfolio_currency(tx: InvestmentPortfolioTransaction, bond_scale: bool = False) -> float:
    """Full acquisition cost per unit in portfolio currency: (qty × price × FX + fees) / qty."""
    qty = _effective_trade_quantity(tx, bond_scale)
    if qty <= _QTY_EPS:
        return float(tx.unit_price) * float(tx.exchange_rate)
    gross = qty * float(tx.unit_price) * float(tx.exchange_rate) + float(tx.fees or 0.0)
    return gross / qty


def _purchase_unit_ex_fees_in_portfolio_currency(tx: InvestmentPortfolioTransaction) -> float:
    """Acquisition price per unit excluding fees: unit_price × exchange_rate."""
    return float(tx.unit_price) * float(tx.exchange_rate)


def replay_position_at_cutoff(
    rows: Iterable[InvestmentPortfolioTransaction],
    cutoff_date: Optional[date] = None,
    bond_scale: bool = False,
) -> Tuple[float, Optional[float], Optional[float]]:
    """
    Replay purchases/sells in chronological order, optionally stopping after cutoff_date (inclusive).

    When bond_scale is True, trade quantities are divided by 100 (Italian nominal convention).

    Returns (net_shares_held, average_unit_cost_with_fees, average_unit_cost_ex_fees).
    Averages are None when net shares are ~0.
    """
    sorted_rows = sorted(rows, key=lambda t: (t.trade_date, t.id))
    shares_held = 0.0
    avg_with: Optional[float] = None
    avg_ex: Optional[float] = None

    for tx in sorted_rows:
        if cutoff_date is not None and tx.trade_date > cutoff_date:
            continue
        if tx.transaction_type == InvPortfolioTxType.purchase:
            qty = _effective_trade_quantity(tx, bond_scale)
            ep_w = _purchase_unit_cost_in_portfolio_currency(tx, bond_scale)
            ep_x = _purchase_unit_ex_fees_in_portfolio_currency(tx)
            if shares_held <= _QTY_EPS:
                new_w, new_x = ep_w, ep_x
            else:
                new_w = (avg_with * shares_held + ep_w * qty) / (shares_held + qty)
                new_x = (avg_ex * shares_held + ep_x * qty) / (shares_held + qty) if avg_ex is not None else ep_x
            avg_with, avg_ex = new_w, new_x
            shares_held += qty
        else:
            shares_held -= _effective_trade_quantity(tx, bond_scale)

    if shares_held <= _QTY_EPS:
        return 0.0, None, None
    return shares_held, avg_with, avg_ex


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

    asset = db.query(InvestmentPortfolioAsset).filter(InvestmentPortfolioAsset.id == asset_pk).first()
    bond_scale = bool(asset and asset.inv_kind == InvPortfolioKind.bond)

    shares_held = 0.0
    avg_unit: Optional[float] = None

    for tx in rows:
        if tx.transaction_type == InvPortfolioTxType.purchase:
            ep = _purchase_unit_cost_in_portfolio_currency(tx, bond_scale)
            qty = _effective_trade_quantity(tx, bond_scale)
            if shares_held <= _QTY_EPS:
                new_avg = ep
            else:
                new_avg = (avg_unit * shares_held + ep * qty) / (shares_held + qty)
            tx.average_unit_cost_after_trade = new_avg
            avg_unit = new_avg
            shares_held += qty
        else:
            tx.average_unit_cost_after_trade = None
            shares_held -= _effective_trade_quantity(tx, bond_scale)

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
    asset = db.query(InvestmentPortfolioAsset).filter(InvestmentPortfolioAsset.id == asset_pk).first()
    bond_scale = bool(asset and asset.inv_kind == InvPortfolioKind.bond)
    shares, avg_w, _ = replay_position_at_cutoff(rows, cutoff_date=None, bond_scale=bond_scale)
    if shares > _QTY_EPS and avg_w is not None:
        return avg_w
    return None


def current_average_unit_cost_ex_fees_without_flush(db: Session, asset_pk: int) -> Optional[float]:
    """Weighted-average unit acquisition cost excluding purchase fees (portfolio currency per unit)."""
    rows: List[InvestmentPortfolioTransaction] = (
        db.query(InvestmentPortfolioTransaction)
        .filter(InvestmentPortfolioTransaction.asset_pk == asset_pk)
        .order_by(InvestmentPortfolioTransaction.trade_date, InvestmentPortfolioTransaction.id)
        .all()
    )
    asset = db.query(InvestmentPortfolioAsset).filter(InvestmentPortfolioAsset.id == asset_pk).first()
    bond_scale = bool(asset and asset.inv_kind == InvPortfolioKind.bond)
    shares, _, avg_x = replay_position_at_cutoff(rows, cutoff_date=None, bond_scale=bond_scale)
    if shares > _QTY_EPS and avg_x is not None:
        return avg_x
    return None
