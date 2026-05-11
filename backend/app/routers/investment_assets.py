"""CRUD and CSV import for investment portfolio assets."""
import csv
import io
from datetime import date
from typing import List, Optional

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from ..database import get_db
from ..date_parse import parse_flexible_date
from ..models import InvestmentPortfolioAsset, InvPortfolioKind, InvPortfolioClass, InvPortfolioStatus
from ..schemas import (
    InvestmentPortfolioAssetCreate,
    InvestmentPortfolioAssetUpdate,
    InvestmentPortfolioAssetResponse,
    InvestmentPortfolioImportResult,
    InvPortfolioKindSchema,
    InvPortfolioClassSchema,
    InvPortfolioStatusSchema,
    _geo_sum_ok,
    GEO_SUM_TOLERANCE,
)

router = APIRouter()


def _kind(s: InvPortfolioKindSchema) -> InvPortfolioKind:
    return InvPortfolioKind(s.value)


def _cls(s: InvPortfolioClassSchema) -> InvPortfolioClass:
    return InvPortfolioClass(s.value)


def _status(s: InvPortfolioStatusSchema) -> InvPortfolioStatus:
    return InvPortfolioStatus(s.value)


@router.get("/", response_model=List[InvestmentPortfolioAssetResponse])
def list_assets(db: Session = Depends(get_db)):
    return db.query(InvestmentPortfolioAsset).order_by(InvestmentPortfolioAsset.asset_id).all()


@router.get("/by-key/{asset_id}", response_model=InvestmentPortfolioAssetResponse)
def get_asset_by_key(asset_id: str, db: Session = Depends(get_db)):
    row = db.query(InvestmentPortfolioAsset).filter(InvestmentPortfolioAsset.asset_id == asset_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Asset not found")
    return row


@router.get("/{asset_pk}", response_model=InvestmentPortfolioAssetResponse)
def get_asset(asset_pk: int, db: Session = Depends(get_db)):
    row = db.query(InvestmentPortfolioAsset).filter(InvestmentPortfolioAsset.id == asset_pk).first()
    if not row:
        raise HTTPException(status_code=404, detail="Asset not found")
    return row


@router.post("/", response_model=InvestmentPortfolioAssetResponse, status_code=201)
def create_asset(body: InvestmentPortfolioAssetCreate, db: Session = Depends(get_db)):
    if db.query(InvestmentPortfolioAsset).filter(InvestmentPortfolioAsset.asset_id == body.asset_id).first():
        raise HTTPException(status_code=400, detail=f"asset_id already exists: {body.asset_id}")
    row = InvestmentPortfolioAsset(
        asset_id=body.asset_id.strip(),
        asset_name=body.asset_name.strip(),
        isin=body.isin,
        ticker=body.ticker,
        issuer=body.issuer,
        broker=body.broker,
        inv_kind=_kind(body.type),
        inv_class=_cls(body.asset_class),
        market=body.market,
        status=_status(body.status),
        currency=body.currency,
        tax_rate=body.tax_rate,
        default_exchange_rate=body.default_exchange_rate,
        perc_usa=body.perc_usa,
        perc_eu=body.perc_eu,
        perc_other_developed=body.perc_other_developed,
        perc_emerging=body.perc_emerging,
        perc_other=body.perc_other,
        expiration_date=body.expiration_date,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def _validate_merged_asset(
    *,
    inv_kind: InvPortfolioKind,
    expiration_date: Optional[date],
    perc_usa: float,
    perc_eu: float,
    perc_other_developed: float,
    perc_emerging: float,
    perc_other: float,
):
    if not _geo_sum_ok(perc_usa, perc_eu, perc_other_developed, perc_emerging, perc_other):
        s = perc_usa + perc_eu + perc_other_developed + perc_emerging + perc_other
        raise HTTPException(
            status_code=400,
            detail=f"Geographic percentages must sum to 100 (within {GEO_SUM_TOLERANCE}), got {s}",
        )
    if inv_kind == InvPortfolioKind.bond and expiration_date is None:
        raise HTTPException(status_code=400, detail="expiration_date is required when type is bond")


@router.put("/{asset_pk}", response_model=InvestmentPortfolioAssetResponse)
def update_asset(asset_pk: int, body: InvestmentPortfolioAssetUpdate, db: Session = Depends(get_db)):
    row = db.query(InvestmentPortfolioAsset).filter(InvestmentPortfolioAsset.id == asset_pk).first()
    if not row:
        raise HTTPException(status_code=404, detail="Asset not found")

    data = body.model_dump(exclude_unset=True)
    if "asset_id" in data and data["asset_id"]:
        new_key = str(data["asset_id"]).strip()
        other = (
            db.query(InvestmentPortfolioAsset)
            .filter(InvestmentPortfolioAsset.asset_id == new_key, InvestmentPortfolioAsset.id != asset_pk)
            .first()
        )
        if other:
            raise HTTPException(status_code=400, detail=f"asset_id already exists: {new_key}")
        row.asset_id = new_key

    if "asset_name" in data and data["asset_name"] is not None:
        row.asset_name = str(data["asset_name"]).strip()
    for opt in ("isin", "ticker", "issuer", "broker", "market", "currency"):
        if opt in data and data[opt] is not None:
            setattr(row, opt, data[opt])
    if "tax_rate" in data and data["tax_rate"] is not None:
        row.tax_rate = data["tax_rate"]
    if "default_exchange_rate" in data and data["default_exchange_rate"] is not None:
        row.default_exchange_rate = data["default_exchange_rate"]
    if body.status is not None and "status" in data:
        row.status = _status(body.status)

    if body.type is not None and "type" in data:
        row.inv_kind = _kind(body.type)
    if body.asset_class is not None and "asset_class" in data:
        row.inv_class = _cls(body.asset_class)
    if "expiration_date" in data:
        row.expiration_date = data["expiration_date"]

    for k in ("perc_usa", "perc_eu", "perc_other_developed", "perc_emerging", "perc_other"):
        if k in data and data[k] is not None:
            setattr(row, k, data[k])

    _validate_merged_asset(
        inv_kind=row.inv_kind,
        expiration_date=row.expiration_date,
        perc_usa=row.perc_usa,
        perc_eu=row.perc_eu,
        perc_other_developed=row.perc_other_developed,
        perc_emerging=row.perc_emerging,
        perc_other=row.perc_other,
    )

    db.commit()
    db.refresh(row)
    return row


@router.delete("/{asset_pk}", status_code=204)
def delete_asset(asset_pk: int, db: Session = Depends(get_db)):
    row = db.query(InvestmentPortfolioAsset).filter(InvestmentPortfolioAsset.id == asset_pk).first()
    if not row:
        raise HTTPException(status_code=404, detail="Asset not found")
    db.delete(row)
    db.commit()
    return None


def _parse_float(val: str, default: float = 0.0) -> float:
    if val is None or str(val).strip() == "":
        return default
    return float(str(val).strip().replace(",", "."))


def _parse_date(val: Optional[str]) -> Optional[date]:
    return parse_flexible_date(val, required=False)


@router.post("/import-csv", response_model=InvestmentPortfolioImportResult)
async def import_assets_csv(file: UploadFile = File(...), db: Session = Depends(get_db)):
    raw = await file.read()
    text = raw.decode("utf-8-sig", errors="replace")
    reader = csv.DictReader(io.StringIO(text))
    result = InvestmentPortfolioImportResult()

    required = {"asset_id", "asset_name", "type", "class"}
    if not reader.fieldnames:
        result.errors.append("CSV has no header row")
        return result
    missing = required - {h.strip() for h in reader.fieldnames if h}
    if missing:
        result.errors.append(f"Missing columns: {sorted(missing)}")
        return result

    for i, row in enumerate(reader, start=2):
        try:
            aid = (row.get("asset_id") or "").strip()
            if not aid:
                result.skipped += 1
                continue
            create_kwargs = {
                "asset_id": aid,
                "asset_name": (row.get("asset_name") or "").strip() or aid,
                "isin": (row.get("isin") or "").strip() or None,
                "ticker": (row.get("ticker") or "").strip() or None,
                "issuer": (row.get("issuer") or "").strip() or None,
                "broker": (row.get("broker") or "").strip() or None,
                "type": InvPortfolioKindSchema((row.get("type") or "").strip().lower()),
                "asset_class": InvPortfolioClassSchema((row.get("class") or "").strip().lower()),
                "market": (row.get("market") or "Borsa Italiana").strip(),
                "status": InvPortfolioStatusSchema((row.get("status") or "active").strip().lower()),
                "currency": (row.get("currency") or "EUR").strip(),
                "tax_rate": _parse_float(row.get("tax_rate"), 0.26),
                "default_exchange_rate": _parse_float(row.get("default_exchange_rate"), 1.0),
                "perc_usa": _parse_float(row.get("perc_usa"), 0.0),
                "perc_eu": _parse_float(row.get("perc_eu"), 0.0),
                "perc_other_developed": _parse_float(row.get("perc_other_developed"), 0.0),
                "perc_emerging": _parse_float(row.get("perc_emerging"), 0.0),
                "perc_other": _parse_float(row.get("perc_other"), 0.0),
                "expiration_date": _parse_date(row.get("expiration_date")),
            }
            body = InvestmentPortfolioAssetCreate(**create_kwargs)
            existing = db.query(InvestmentPortfolioAsset).filter(InvestmentPortfolioAsset.asset_id == body.asset_id).first()
            if existing:
                update = InvestmentPortfolioAssetUpdate(
                    asset_name=body.asset_name,
                    isin=body.isin,
                    ticker=body.ticker,
                    issuer=body.issuer,
                    broker=body.broker,
                    type=body.type,
                    asset_class=body.asset_class,
                    market=body.market,
                    status=body.status,
                    currency=body.currency,
                    tax_rate=body.tax_rate,
                    default_exchange_rate=body.default_exchange_rate,
                    perc_usa=body.perc_usa,
                    perc_eu=body.perc_eu,
                    perc_other_developed=body.perc_other_developed,
                    perc_emerging=body.perc_emerging,
                    perc_other=body.perc_other,
                    expiration_date=body.expiration_date,
                )
                update_asset(existing.id, update, db)
                result.updated += 1
            else:
                create_asset(body, db)
                result.created += 1
        except HTTPException as he:
            result.errors.append(f"Row {i}: {he.detail}")
        except Exception as e:  # noqa: BLE001
            result.errors.append(f"Row {i}: {e}")

    return result
