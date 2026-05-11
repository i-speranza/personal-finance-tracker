"""CRUD and CSV import for investment portfolio transactions."""
import csv
import io
from datetime import date
from typing import List, Optional

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from sqlalchemy.orm import Session

from ..database import get_db
from ..date_parse import parse_flexible_date
from ..models import InvestmentPortfolioAsset, InvestmentPortfolioTransaction, InvPortfolioTxType
from ..schemas import (
    InvestmentPortfolioTransactionCreate,
    InvestmentPortfolioTransactionUpdate,
    InvestmentPortfolioTransactionResponse,
    InvestmentPortfolioImportResult,
    InvPortfolioTxTypeSchema,
)

router = APIRouter()


def _tx_type(s: InvPortfolioTxTypeSchema) -> InvPortfolioTxType:
    return InvPortfolioTxType(s.value)


@router.get("/", response_model=List[InvestmentPortfolioTransactionResponse])
def list_transactions(
    asset_pk: Optional[int] = Query(None),
    db: Session = Depends(get_db),
):
    q = db.query(InvestmentPortfolioTransaction)
    if asset_pk is not None:
        q = q.filter(InvestmentPortfolioTransaction.asset_pk == asset_pk)
    return q.order_by(
        InvestmentPortfolioTransaction.trade_date.desc(),
        InvestmentPortfolioTransaction.id.desc(),
    ).all()


@router.get("/{tx_id}", response_model=InvestmentPortfolioTransactionResponse)
def get_transaction(tx_id: int, db: Session = Depends(get_db)):
    row = db.query(InvestmentPortfolioTransaction).filter(InvestmentPortfolioTransaction.id == tx_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return row


@router.post("/", response_model=InvestmentPortfolioTransactionResponse, status_code=201)
def create_transaction(body: InvestmentPortfolioTransactionCreate, db: Session = Depends(get_db)):
    asset = db.query(InvestmentPortfolioAsset).filter(InvestmentPortfolioAsset.id == body.asset_pk).first()
    if not asset:
        raise HTTPException(status_code=400, detail="asset_pk not found")

    if body.transaction_type == InvPortfolioTxTypeSchema.purchase:
        plus_minus = 0.0
    else:
        plus_minus = float(body.plus_minus)  # validated by schema

    row = InvestmentPortfolioTransaction(
        asset_pk=body.asset_pk,
        trade_date=body.trade_date,
        transaction_type=_tx_type(body.transaction_type),
        quantity=body.quantity,
        unit_price=body.unit_price,
        exchange_rate=body.exchange_rate,
        fees=body.fees,
        plus_minus=plus_minus,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


@router.put("/{tx_id}", response_model=InvestmentPortfolioTransactionResponse)
def update_transaction(tx_id: int, body: InvestmentPortfolioTransactionUpdate, db: Session = Depends(get_db)):
    row = db.query(InvestmentPortfolioTransaction).filter(InvestmentPortfolioTransaction.id == tx_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Transaction not found")

    data = body.model_dump(exclude_unset=True)
    old_type = row.transaction_type

    if "plus_minus" in data and data["plus_minus"] is None:
        raise HTTPException(
            status_code=400,
            detail="plus_minus cannot be null; omit the field to keep the current value",
        )

    if "trade_date" in data:
        row.trade_date = data["trade_date"]
    if body.transaction_type is not None and "transaction_type" in data:
        row.transaction_type = _tx_type(body.transaction_type)
    if "quantity" in data and data["quantity"] is not None:
        row.quantity = data["quantity"]
    if "unit_price" in data and data["unit_price"] is not None:
        row.unit_price = data["unit_price"]
    if "exchange_rate" in data and data["exchange_rate"] is not None:
        row.exchange_rate = data["exchange_rate"]
    if "fees" in data and data["fees"] is not None:
        row.fees = data["fees"]
    if "plus_minus" in data and data["plus_minus"] is not None:
        row.plus_minus = data["plus_minus"]

    if row.transaction_type == InvPortfolioTxType.purchase:
        row.plus_minus = 0.0
    elif row.transaction_type == InvPortfolioTxType.sell:
        if old_type != InvPortfolioTxType.sell and "plus_minus" not in data:
            raise HTTPException(
                status_code=400,
                detail="plus_minus is required when changing transaction type to sell",
            )

    db.commit()
    db.refresh(row)
    return row


@router.delete("/{tx_id}", status_code=204)
def delete_transaction(tx_id: int, db: Session = Depends(get_db)):
    row = db.query(InvestmentPortfolioTransaction).filter(InvestmentPortfolioTransaction.id == tx_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Transaction not found")
    db.delete(row)
    db.commit()
    return None


def _parse_float(val, default: float = 0.0) -> float:
    if val is None or str(val).strip() == "":
        return default
    return float(str(val).strip().replace(",", "."))


def _parse_date(val) -> date:
    d = parse_flexible_date(None if val is None else str(val).strip(), required=True)
    assert d is not None
    return d


@router.post("/import-csv", response_model=InvestmentPortfolioImportResult)
async def import_transactions_csv(file: UploadFile = File(...), db: Session = Depends(get_db)):
    raw = await file.read()
    text = raw.decode("utf-8-sig", errors="replace")
    reader = csv.DictReader(io.StringIO(text))
    result = InvestmentPortfolioImportResult()

    required = {"asset_id", "date", "transaction_type", "quantity", "unit_price"}
    if not reader.fieldnames:
        result.errors.append("CSV has no header row")
        return result
    headers = {h.strip() for h in reader.fieldnames if h}
    missing = required - headers
    if missing:
        result.errors.append(f"Missing columns: {sorted(missing)}")
        return result

    for i, row in enumerate(reader, start=2):
        try:
            aid = (row.get("asset_id") or "").strip()
            if not aid:
                result.skipped += 1
                continue
            asset = db.query(InvestmentPortfolioAsset).filter(InvestmentPortfolioAsset.asset_id == aid).first()
            if not asset:
                result.errors.append(f"Row {i}: unknown asset_id {aid}")
                continue

            tx_kind = InvPortfolioTxTypeSchema((row.get("transaction_type") or "").strip().lower())
            plus_raw = row.get("plus_minus")
            plus_val = None
            if plus_raw is not None and str(plus_raw).strip() != "":
                plus_val = _parse_float(plus_raw)
            if tx_kind == InvPortfolioTxTypeSchema.sell and plus_val is None:
                raise HTTPException(status_code=400, detail="plus_minus is required for sell rows")

            body = InvestmentPortfolioTransactionCreate(
                asset_pk=asset.id,
                trade_date=_parse_date(row.get("date")),
                transaction_type=tx_kind,
                quantity=_parse_float(row.get("quantity")),
                unit_price=_parse_float(row.get("unit_price")),
                exchange_rate=_parse_float(row.get("exchange_rate"), 1.0),
                fees=_parse_float(row.get("fees"), 0.0),
                plus_minus=plus_val,
            )
            create_transaction(body, db)
            result.created += 1
        except HTTPException as he:
            db.rollback()
            result.errors.append(f"Row {i}: {he.detail}")
        except Exception as e:  # noqa: BLE001
            db.rollback()
            result.errors.append(f"Row {i}: {e}")

    return result
