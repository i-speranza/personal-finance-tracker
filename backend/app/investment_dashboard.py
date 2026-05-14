"""Aggregate investment portfolio dashboard (snapshot, geo, time series, XIRR)."""
from __future__ import annotations

from collections import defaultdict
from datetime import date
from typing import DefaultDict, Dict, List, Optional, Sequence, Tuple

from sqlalchemy import func
from sqlalchemy.orm import Session

from .investment_cost_basis import replay_position_at_cutoff
from .models import (
    InvestmentPortfolioAsset,
    InvestmentPortfolioMarketQuote,
    InvestmentPortfolioTransaction,
    InvPortfolioKind,
    InvPortfolioStatus,
    InvPortfolioTxType,
)

_QTY_EPS = 1e-9
_GEO_ATTRS = (
    ("usa", "perc_usa"),
    ("eu", "perc_eu"),
    ("other_developed", "perc_other_developed"),
    ("emerging", "perc_emerging"),
    ("other", "perc_other"),
)


def _broker_label(broker: Optional[str]) -> str:
    return broker if broker and broker.strip() else "—"


def _txn_cashflow_portfolio_currency(tx: InvestmentPortfolioTransaction, bond_scale: bool) -> float:
    """Purchase: negative outflow; sell: positive inflow (before terminal). IRR ignores plus_minus."""
    q = float(tx.quantity) / 100.0 if bond_scale else float(tx.quantity)
    gross = q * float(tx.unit_price) * float(tx.exchange_rate)
    fees = float(tx.fees or 0.0)
    if tx.transaction_type == InvPortfolioTxType.purchase:
        return -(gross + fees)
    return gross - fees


def _merge_flows_by_date(flows: List[Tuple[date, float]]) -> Tuple[List[date], List[float]]:
    merged: DefaultDict[date, float] = defaultdict(float)
    for d, c in flows:
        merged[d] += c
    dates = sorted(merged.keys())
    return dates, [merged[d] for d in dates]


def _xnpv(rate: float, amounts: Sequence[float], dates: Sequence[date]) -> float:
    if rate <= -1.0:
        return float("nan")
    t0 = dates[0]
    s = 0.0
    for cf, d in zip(amounts, dates):
        exp = (d - t0).days / 365.0
        s += cf / ((1.0 + rate) ** exp)
    return s


def compute_xirr(flows: List[Tuple[date, float]]) -> Optional[float]:
    """
    Annualized XIRR (365-day basis). Amounts are merged by calendar date.
    Returns None if not bracketed or degenerate.
    """
    if len(flows) < 2:
        return None
    dates, amounts = _merge_flows_by_date(flows)
    if len(dates) < 2:
        return None
    pos = sum(a for a in amounts if a > 0)
    neg = sum(a for a in amounts if a < 0)
    if pos < 1e-12 or neg > -1e-12:
        return None

    def npv(r: float) -> float:
        return _xnpv(r, amounts, dates)

    v0 = npv(0.0)
    if abs(v0) < 1e-9:
        return 0.0

    lo, hi = -0.9999, 10.0
    v_lo, v_hi = npv(lo), npv(hi)
    expand = 0
    while v_lo * v_hi > 0 and expand < 40:
        hi *= 2.0
        v_hi = npv(hi)
        expand += 1
    if v_lo * v_hi > 0:
        lo = -0.999999
        v_lo = npv(lo)
    if v_lo * v_hi > 0:
        return None

    for _ in range(100):
        mid = (lo + hi) / 2.0
        v_mid = npv(mid)
        if abs(v_mid) < 1e-8:
            return mid
        if v_lo * v_mid <= 0:
            hi, v_hi = mid, v_mid
        else:
            lo, v_lo = mid, v_mid
    return (lo + hi) / 2.0


def _asset_irr(
    txs: List[InvestmentPortfolioTransaction],
    as_of: date,
    terminal_mv: float,
    bond_scale: bool,
) -> Optional[float]:
    flows: List[Tuple[date, float]] = []
    for tx in txs:
        if tx.trade_date > as_of:
            continue
        flows.append((tx.trade_date, _txn_cashflow_portfolio_currency(tx, bond_scale)))
    flows.append((as_of, terminal_mv))
    return compute_xirr(flows)


def _portfolio_irr(
    txs_by_asset: Dict[int, List[InvestmentPortfolioTransaction]],
    asset_pks: Sequence[int],
    as_of: date,
    terminal_total_mv: float,
    bond_by_pk: Dict[int, bool],
) -> Optional[float]:
    flows: List[Tuple[date, float]] = []
    for apk in asset_pks:
        bs = bond_by_pk.get(apk, False)
        for tx in txs_by_asset.get(apk, []):
            if tx.trade_date > as_of:
                continue
            flows.append((tx.trade_date, _txn_cashflow_portfolio_currency(tx, bs)))
    flows.append((as_of, terminal_total_mv))
    return compute_xirr(flows)


def _build_unit_timeseries_for_asset(
    asset_pk: int,
    quote_map: Dict[Tuple[int, date], float],
    resolved_as_of: date,
    txs_by_asset: Dict[int, List[InvestmentPortfolioTransaction]],
    bond_by_pk: Dict[int, bool],
) -> List[dict]:
    u_dates = sorted({d for (apk, d) in quote_map if apk == asset_pk and d <= resolved_as_of})
    if not u_dates:
        return []
    utxs = txs_by_asset[asset_pk]
    ubs = bond_by_pk[asset_pk]
    out: List[dict] = []
    for d in u_dates:
        sh, av_w, av_x = replay_position_at_cutoff(utxs, d, bond_scale=ubs)
        px = float(quote_map[(asset_pk, d)])
        out.append(
            {
                "date": d,
                "unit_valore_with_fees": av_w if sh > _QTY_EPS else None,
                "unit_valore_no_fees": av_x if sh > _QTY_EPS else None,
                "unit_controvalore": px,
            }
        )
    return out


def build_investment_dashboard(
    db: Session,
    as_of_date: Optional[date] = None,
    unit_chart_asset_pk: Optional[int] = None,
) -> dict:
    """
    Build dashboard payload as a plain dict (router maps to Pydantic).

    - Positions: active assets with net shares > 0 at as_of (trade_date <= as_of).
    - Charts universe: active assets with net shares > 0 today (full history replay).
    - IRR: all trades on active assets with trade_date <= as_of; terminal = sum of MV at as_of
      for positions with shares > 0 at as_of.
    - Bonds (inv_kind bond): quantities follow the Italian nominal ×100 convention — effective units are
      stored quantity ÷ 100 for cost, totals, charts, and IRR (same as the Data tab).
    """
    active_assets: List[InvestmentPortfolioAsset] = (
        db.query(InvestmentPortfolioAsset)
        .filter(InvestmentPortfolioAsset.status == InvPortfolioStatus.active)
        .order_by(InvestmentPortfolioAsset.asset_id)
        .all()
    )
    if not active_assets:
        return _empty_payload("no_active_assets")

    bond_by_pk: Dict[int, bool] = {a.id: (a.inv_kind == InvPortfolioKind.bond) for a in active_assets}

    asset_ids = [a.id for a in active_assets]
    all_txs: List[InvestmentPortfolioTransaction] = (
        db.query(InvestmentPortfolioTransaction)
        .filter(InvestmentPortfolioTransaction.asset_pk.in_(asset_ids))
        .order_by(InvestmentPortfolioTransaction.trade_date, InvestmentPortfolioTransaction.id)
        .all()
    )
    txs_by_asset: Dict[int, List[InvestmentPortfolioTransaction]] = defaultdict(list)
    for tx in all_txs:
        txs_by_asset[tx.asset_pk].append(tx)

    current_shares: Dict[int, float] = {}
    for a in active_assets:
        sh, _, _ = replay_position_at_cutoff(txs_by_asset[a.id], None, bond_scale=bond_by_pk[a.id])
        current_shares[a.id] = sh

    chart_asset_pks = {a.id for a in active_assets if current_shares[a.id] > _QTY_EPS}

    max_q = None
    if chart_asset_pks:
        max_q = (
            db.query(func.max(InvestmentPortfolioMarketQuote.as_of_date))
            .filter(InvestmentPortfolioMarketQuote.asset_pk.in_(chart_asset_pks))
            .scalar()
        )

    resolved_as_of = as_of_date if as_of_date is not None else max_q
    if resolved_as_of is None:
        return _empty_payload("no_market_quotes_for_open_positions")

    quote_rows: List[InvestmentPortfolioMarketQuote] = (
        db.query(InvestmentPortfolioMarketQuote)
        .filter(InvestmentPortfolioMarketQuote.asset_pk.in_(asset_ids))
        .all()
    )
    quote_map: Dict[Tuple[int, date], float] = {}
    dates_by_asset: DefaultDict[int, List[date]] = defaultdict(list)
    for q in quote_rows:
        quote_map[(q.asset_pk, q.as_of_date)] = float(q.market_unit_price)
        dates_by_asset[q.asset_pk].append(q.as_of_date)

    currency = active_assets[0].currency or "EUR"

    # --- Positions at resolved_as_of ---
    position_assets = [a for a in active_assets if _shares_at(txs_by_asset[a.id], resolved_as_of, bond_by_pk[a.id]) > _QTY_EPS]

    rows_out: List[dict] = []
    total_mv = 0.0
    broker_acc: DefaultDict[str, Dict[str, float]] = defaultdict(lambda: {"cont": 0.0, "after": 0.0})

    geo_num_val: DefaultDict[str, float] = defaultdict(float)
    geo_num_cont: DefaultDict[str, float] = defaultdict(float)
    geo_by_class_val: DefaultDict[str, DefaultDict[str, float]] = defaultdict(lambda: defaultdict(float))
    geo_by_class_cont: DefaultDict[str, DefaultDict[str, float]] = defaultdict(lambda: defaultdict(float))
    class_sum_tv: DefaultDict[str, float] = defaultdict(float)
    class_sum_tc: DefaultDict[str, float] = defaultdict(float)

    for a in position_assets:
        txs = txs_by_asset[a.id]
        bs = bond_by_pk[a.id]
        sh, u_w, u_x = replay_position_at_cutoff(txs, resolved_as_of, bond_scale=bs)
        price = quote_map.get((a.id, resolved_as_of))
        has_quote = price is not None
        tv_w = sh * u_w if u_w is not None else None
        tv_x = sh * u_x if u_x is not None else None
        unit_c = float(price) if price is not None else None
        tc = sh * unit_c if unit_c is not None else None
        tax_r = float(a.tax_rate or 0.0)
        after_tax = None
        if tc is not None and tv_w is not None:
            gain = max(0.0, tc - tv_w)
            after_tax = tc - gain * tax_r
        pct_real = None
        if tc is not None and tv_w is not None and abs(tv_w) > _QTY_EPS:
            pct_real = (tc - tv_w) / tv_w * 100.0
        pct_nf = None
        if tc is not None and tv_x is not None and tv_w is not None and abs(tv_w) > _QTY_EPS:
            pct_nf = (tc - tv_x) / tv_w * 100.0

        term_mv = tc if tc is not None else 0.0
        irr_one = _asset_irr(txs, resolved_as_of, term_mv, bs)

        bl = _broker_label(a.broker)
        if tc is not None:
            broker_acc[bl]["cont"] += tc
            if after_tax is not None:
                broker_acc[bl]["after"] += after_tax
        cls = a.inv_class.value
        if tv_w is not None:
            class_sum_tv[cls] += tv_w
            for key, attr in _GEO_ATTRS:
                p = float(getattr(a, attr, 0.0) or 0.0) / 100.0
                geo_num_val[key] += tv_w * p
                geo_by_class_val[cls][key] += tv_w * p
        if tc is not None:
            class_sum_tc[cls] += tc
            for key, attr in _GEO_ATTRS:
                p = float(getattr(a, attr, 0.0) or 0.0) / 100.0
                geo_num_cont[key] += tc * p
                geo_by_class_cont[cls][key] += tc * p

        if tc is not None:
            total_mv += tc

        rows_out.append(
            {
                "asset_pk": a.id,
                "asset_id": a.asset_id,
                "asset_name": a.asset_name,
                "broker": a.broker,
                "shares": sh,
                "unit_valore_with_fees": u_w,
                "total_valore_with_fees": tv_w,
                "unit_valore_no_fees": u_x,
                "total_valore_no_fees": tv_x,
                "unit_controvalore": unit_c,
                "total_controvalore": tc,
                "total_controvalore_after_tax": after_tax,
                "pct_gain_loss_real": pct_real,
                "pct_gain_loss_no_fees": pct_nf,
                "irr": irr_one,
                "has_quote": has_quote,
            }
        )

    sum_tv = sum(r["total_valore_with_fees"] or 0.0 for r in rows_out)
    sum_tc = sum(r["total_controvalore"] or 0.0 for r in rows_out)

    class_mix: List[dict] = []
    for cls in sorted(set(class_sum_tv.keys()) | set(class_sum_tc.keys())):
        stv = class_sum_tv[cls]
        stc = class_sum_tc[cls]
        if stv <= _QTY_EPS and stc <= _QTY_EPS:
            continue
        class_mix.append(
            {
                "class": cls,
                "valore_pct": (stv / sum_tv * 100.0) if sum_tv > _QTY_EPS else 0.0,
                "controvalore_pct": (stc / sum_tc * 100.0) if sum_tc > _QTY_EPS else 0.0,
            }
        )

    geo_val_pct = {k: (geo_num_val[k] / sum_tv * 100.0) if sum_tv > _QTY_EPS else 0.0 for k, _ in _GEO_ATTRS}
    geo_cont_pct = {k: (geo_num_cont[k] / sum_tc * 100.0) if sum_tc > _QTY_EPS else 0.0 for k, _ in _GEO_ATTRS}

    geo_allocation_by_class: List[dict] = []
    for cls in sorted(set(class_sum_tv.keys()) | set(class_sum_tc.keys())):
        stv = class_sum_tv[cls]
        stc = class_sum_tc[cls]
        if stv <= _QTY_EPS and stc <= _QTY_EPS:
            continue
        geo_allocation_by_class.append(
            {
                "class": cls,
                "valore_pct": {
                    k: (geo_by_class_val[cls][k] / stv * 100.0) if stv > _QTY_EPS else 0.0 for k, _ in _GEO_ATTRS
                },
                "controvalore_pct": {
                    k: (geo_by_class_cont[cls][k] / stc * 100.0) if stc > _QTY_EPS else 0.0 for k, _ in _GEO_ATTRS
                },
            }
        )

    totals_by_broker = [
        {"broker": bk, "total_controvalore": v["cont"], "total_controvalore_after_tax": v["after"]}
        for bk, v in sorted(broker_acc.items(), key=lambda x: x[0])
    ]

    irr_asset_pks = [a.id for a in active_assets if txs_by_asset[a.id]]
    portfolio_irr = _portfolio_irr(txs_by_asset, irr_asset_pks, resolved_as_of, total_mv, bond_by_pk)

    # --- Portfolio time series (dates from quotes for chart universe, capped at as_of) ---
    ts_dates: Set[date] = set()
    for apk in chart_asset_pks:
        for d in dates_by_asset.get(apk, []):
            if d <= resolved_as_of:
                ts_dates.add(d)
    ts_sorted = sorted(ts_dates)

    timeseries: List[dict] = []
    for d in ts_sorted:
        tv_sum = 0.0
        tc_sum = 0.0
        for apk in chart_asset_pks:
            txs = txs_by_asset[apk]
            bs = bond_by_pk[apk]
            sh, av_w, _ = replay_position_at_cutoff(txs, d, bond_scale=bs)
            if sh <= _QTY_EPS or av_w is None:
                continue
            px = quote_map.get((apk, d))
            if px is None:
                continue
            tv_sum += sh * av_w
            tc_sum += sh * float(px)
        timeseries.append(
            {
                "date": d,
                "total_valore_with_fees": tv_sum,
                "total_controvalore": tc_sum,
            }
        )

    # --- Default unit chart asset: largest controvalore at as_of among open positions ---
    default_unit_pk: Optional[int] = None
    best_tc = -1.0
    for r in rows_out:
        tc = r["total_controvalore"]
        if tc is not None and tc > best_tc:
            best_tc = tc
            default_unit_pk = r["asset_pk"]
    chosen_unit = unit_chart_asset_pk if unit_chart_asset_pk is not None else default_unit_pk
    if chosen_unit is not None and chosen_unit not in {a.id for a in active_assets}:
        chosen_unit = default_unit_pk

    unit_ts: List[dict] = (
        _build_unit_timeseries_for_asset(chosen_unit, quote_map, resolved_as_of, txs_by_asset, bond_by_pk)
        if chosen_unit is not None
        else []
    )

    asset_by_pk = {a.id: a for a in active_assets}
    unit_timeseries_by_asset: List[dict] = []
    for apk in sorted(chart_asset_pks):
        pts = _build_unit_timeseries_for_asset(apk, quote_map, resolved_as_of, txs_by_asset, bond_by_pk)
        if not pts:
            continue
        meta = asset_by_pk.get(apk)
        unit_timeseries_by_asset.append(
            {
                "asset_pk": apk,
                "asset_id": meta.asset_id if meta else str(apk),
                "asset_name": meta.asset_name if meta else "",
                "points": pts,
            }
        )

    return {
        "as_of_date": resolved_as_of,
        "currency": currency,
        "totals_by_broker": totals_by_broker,
        "portfolio_irr": portfolio_irr,
        "positions": rows_out,
        "geo_allocation": {"valore_pct": geo_val_pct, "controvalore_pct": geo_cont_pct},
        "geo_allocation_by_class": geo_allocation_by_class,
        "class_mix": class_mix,
        "timeseries": timeseries,
        "unit_timeseries": unit_ts,
        "unit_timeseries_by_asset": unit_timeseries_by_asset,
        "unit_chart_asset_pk": chosen_unit,
        "empty_detail": None,
    }


def _shares_at(txs: List[InvestmentPortfolioTransaction], as_of: date, bond_scale: bool) -> float:
    sh, _, _ = replay_position_at_cutoff(txs, as_of, bond_scale=bond_scale)
    return sh


def _empty_payload(reason: str) -> dict:
    return {
        "as_of_date": None,
        "currency": "EUR",
        "totals_by_broker": [],
        "portfolio_irr": None,
        "positions": [],
        "geo_allocation": {
            "valore_pct": {k: 0.0 for k, _ in _GEO_ATTRS},
            "controvalore_pct": {k: 0.0 for k, _ in _GEO_ATTRS},
        },
        "geo_allocation_by_class": [],
        "class_mix": [],
        "timeseries": [],
        "unit_timeseries": [],
        "unit_timeseries_by_asset": [],
        "unit_chart_asset_pk": None,
        "empty_detail": reason,
    }
