"""Pydantic schemas for request/response validation."""
from pydantic import BaseModel, Field, ConfigDict, model_validator
from typing import Optional, List, Dict
from datetime import date, datetime
from enum import Enum


class InvestmentTypeEnum(str, Enum):
    """Investment type enumeration."""
    ONE_TIME = "one_time"
    SIP = "sip"


class WithdrawalTypeEnum(str, Enum):
    """Withdrawal type enumeration."""
    IN = "in"
    OUT = "out"


class AssetTypeEnum(str, Enum):
    """Asset type enumeration."""
    CASH = "cash"
    INVESTMENT = "investment"


# Asset Type Reference Schemas
class AssetTypeRefBase(BaseModel):
    """Base asset type reference schema."""
    name: str
    display_name: str


class AssetTypeRefCreate(AssetTypeRefBase):
    """Schema for creating an asset type."""
    pass


class AssetTypeRef(AssetTypeRefBase):
    """Schema for asset type response."""
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


# Transaction Schemas
class TransactionBase(BaseModel):
    """Base transaction schema."""
    bank_name: str
    account_name: str
    date: date
    amount: float
    description: Optional[str] = None
    details: Optional[str] = None
    category: Optional[str] = None
    transaction_type: Optional[str] = None
    is_special: bool = False


class TransactionCreate(TransactionBase):
    """Schema for creating a transaction."""
    pass


class TransactionUpdate(BaseModel):
    """Schema for updating a transaction."""
    bank_name: Optional[str] = None
    account_name: Optional[str] = None
    date: Optional[date] = None
    amount: Optional[float] = None
    description: Optional[str] = None
    category: Optional[str] = None
    details: Optional[str] = None
    transaction_type: Optional[str] = None
    is_special: Optional[bool] = None


class Transaction(TransactionBase):
    """Schema for transaction response."""
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Investment Product Schemas
class InvestmentProductBase(BaseModel):
    """Base investment product schema."""
    product_name: str
    bank_name: str
    start_date: date
    end_date: Optional[date] = None
    investment_type: InvestmentTypeEnum


class InvestmentProductCreate(InvestmentProductBase):
    """Schema for creating an investment product."""
    pass


class InvestmentProductUpdate(BaseModel):
    """Schema for updating an investment product."""
    product_name: Optional[str] = None
    bank_name: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    investment_type: Optional[InvestmentTypeEnum] = None


class InvestmentProduct(InvestmentProductBase):
    """Schema for investment product response."""
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# SIP Plan Schemas
class SIPPlanBase(BaseModel):
    """Base SIP plan schema."""
    product_id: int
    start_date: date
    end_date: Optional[date] = None
    monthly_contribution: float


class SIPPlanCreate(SIPPlanBase):
    """Schema for creating a SIP plan."""
    pass


class SIPPlanUpdate(BaseModel):
    """Schema for updating a SIP plan."""
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    monthly_contribution: Optional[float] = None


class SIPPlan(SIPPlanBase):
    """Schema for SIP plan response."""
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Investment Observation Schemas
class InvestmentObservationBase(BaseModel):
    """Base investment observation schema."""
    product_id: int
    observation_date: date
    num_shares: float
    total_invested: float
    current_value: float


class InvestmentObservationCreate(InvestmentObservationBase):
    """Schema for creating an investment observation."""
    pass


class InvestmentObservationUpdate(BaseModel):
    """Schema for updating an investment observation."""
    observation_date: Optional[date] = None
    num_shares: Optional[float] = None
    total_invested: Optional[float] = None
    current_value: Optional[float] = None


class InvestmentObservation(InvestmentObservationBase):
    """Schema for investment observation response."""
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


# Investment Withdrawal Schemas
class InvestmentWithdrawalBase(BaseModel):
    """Base investment withdrawal schema."""
    bank_name: str
    date: date
    type: WithdrawalTypeEnum
    amount: float
    description: Optional[str] = None


class InvestmentWithdrawalCreate(InvestmentWithdrawalBase):
    """Schema for creating an investment withdrawal."""
    pass


class InvestmentWithdrawal(InvestmentWithdrawalBase):
    """Schema for investment withdrawal response."""
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


# Assets History Schemas
class AssetsHistoryBase(BaseModel):
    """Base assets history schema."""
    account_name: str
    bank_name: str
    asset_type: AssetTypeEnum
    date: date
    amount: float


class AssetsHistoryCreate(AssetsHistoryBase):
    """Schema for creating an assets history entry."""
    pass


class AssetsHistoryUpdate(BaseModel):
    """Schema for updating an assets history entry."""
    amount: Optional[float] = None


class AssetsHistory(AssetsHistoryBase):
    """Schema for assets history response."""
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Intesa Raw Transaction Schemas
class IntesaRawTransactionBase(BaseModel):
    """Base Intesa raw transaction schema."""
    data: date
    operazione: Optional[str] = None
    dettagli: Optional[str] = None
    conto_o_carta: Optional[str] = None
    contabilizzazione: Optional[str] = None
    categoria: Optional[str] = None
    valuta: Optional[str] = None
    importo: float


class IntesaRawTransactionCreate(IntesaRawTransactionBase):
    """Schema for creating an Intesa raw transaction."""
    transaction_id: Optional[int] = None


class IntesaRawTransaction(IntesaRawTransactionBase):
    """Schema for Intesa raw transaction response."""
    id: int
    transaction_id: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True


# Allianz Raw Transaction Schemas
class AllianzRawTransactionBase(BaseModel):
    """Base Allianz raw transaction schema."""
    data_contabile: date
    data_valuta: Optional[date] = None
    descrizione: Optional[str] = None
    importo: float


class AllianzRawTransactionCreate(AllianzRawTransactionBase):
    """Schema for creating an Allianz raw transaction."""
    transaction_id: Optional[int] = None


class AllianzRawTransaction(AllianzRawTransactionBase):
    """Schema for Allianz raw transaction response."""
    id: int
    transaction_id: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True


# Bank Schema
class BankBase(BaseModel):
    """Base bank schema."""
    name: str
    display_name: str


class BankCreate(BankBase):
    """Schema for creating a bank."""
    pass


class Bank(BankBase):
    """Schema for bank response."""
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Account Schema
class AccountBase(BaseModel):
    """Base account schema."""
    bank_name: str
    account_name: str
    asset_type: Optional[AssetTypeEnum] = None  # cash or investment
    status: bool = True  # True=live, False=closed


class AccountCreate(AccountBase):
    """Schema for creating an account."""
    pass


class AccountUpdate(BaseModel):
    """Schema for updating an account."""
    bank_name: Optional[str] = None
    account_name: Optional[str] = None
    asset_type: Optional[AssetTypeEnum] = None
    status: Optional[bool] = None


class Account(AccountBase):
    """Schema for account response."""
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# --- Investment portfolio (assets + trades) ---

GEO_SUM_TOLERANCE = 0.02


class InvPortfolioKindSchema(str, Enum):
    fund = "fund"
    bond = "bond"
    share = "share"


class InvPortfolioClassSchema(str, Enum):
    share = "share"
    bond = "bond"
    commodity = "commodity"


class InvPortfolioStatusSchema(str, Enum):
    active = "active"
    sold = "sold"
    special = "special"


class InvPortfolioTxTypeSchema(str, Enum):
    purchase = "purchase"
    sell = "sell"


def _geo_sum_ok(
    perc_usa: float,
    perc_eu: float,
    perc_other_developed: float,
    perc_emerging: float,
    perc_other: float,
) -> bool:
    s = perc_usa + perc_eu + perc_other_developed + perc_emerging + perc_other
    return abs(s - 100.0) <= GEO_SUM_TOLERANCE


class InvestmentPortfolioAssetBase(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    asset_id: str = Field(..., min_length=1, max_length=128)
    asset_name: str = Field(..., min_length=1)
    isin: Optional[str] = None
    ticker: Optional[str] = None
    issuer: Optional[str] = None
    broker: Optional[str] = None
    type: InvPortfolioKindSchema
    asset_class: InvPortfolioClassSchema = Field(..., alias="class")
    market: str = "Borsa Italiana"
    status: InvPortfolioStatusSchema = InvPortfolioStatusSchema.active
    currency: str = "EUR"
    tax_rate: float = Field(default=0.26, ge=0, le=1)
    default_exchange_rate: float = Field(default=1.0, gt=0)
    perc_usa: float = Field(default=0.0, ge=0, le=100)
    perc_eu: float = Field(default=0.0, ge=0, le=100)
    perc_other_developed: float = Field(default=0.0, ge=0, le=100)
    perc_emerging: float = Field(default=0.0, ge=0, le=100)
    perc_other: float = Field(default=0.0, ge=0, le=100)
    expiration_date: Optional[date] = None

    @model_validator(mode="after")
    def validate_geo_and_bond(self):
        if not _geo_sum_ok(
            self.perc_usa,
            self.perc_eu,
            self.perc_other_developed,
            self.perc_emerging,
            self.perc_other,
        ):
            s = (
                self.perc_usa
                + self.perc_eu
                + self.perc_other_developed
                + self.perc_emerging
                + self.perc_other
            )
            raise ValueError(f"Geographic percentages must sum to 100 (within {GEO_SUM_TOLERANCE}), got {s}")
        if self.type == InvPortfolioKindSchema.bond and self.expiration_date is None:
            raise ValueError("expiration_date is required when type is bond")
        return self


class InvestmentPortfolioAssetCreate(InvestmentPortfolioAssetBase):
    pass


class InvestmentPortfolioAssetUpdate(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    asset_id: Optional[str] = Field(default=None, min_length=1, max_length=128)
    asset_name: Optional[str] = None
    isin: Optional[str] = None
    ticker: Optional[str] = None
    issuer: Optional[str] = None
    broker: Optional[str] = None
    type: Optional[InvPortfolioKindSchema] = None
    asset_class: Optional[InvPortfolioClassSchema] = Field(default=None, alias="class")
    market: Optional[str] = None
    status: Optional[InvPortfolioStatusSchema] = None
    currency: Optional[str] = None
    tax_rate: Optional[float] = Field(default=None, ge=0, le=1)
    default_exchange_rate: Optional[float] = Field(default=None, gt=0)
    perc_usa: Optional[float] = Field(default=None, ge=0, le=100)
    perc_eu: Optional[float] = Field(default=None, ge=0, le=100)
    perc_other_developed: Optional[float] = Field(default=None, ge=0, le=100)
    perc_emerging: Optional[float] = Field(default=None, ge=0, le=100)
    perc_other: Optional[float] = Field(default=None, ge=0, le=100)
    expiration_date: Optional[date] = None


class InvestmentPortfolioAssetResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        ser_json_by_alias=True,
    )

    id: int
    asset_id: str
    asset_name: str
    isin: Optional[str]
    ticker: Optional[str]
    issuer: Optional[str]
    broker: Optional[str]
    inv_kind: InvPortfolioKindSchema = Field(serialization_alias="type")
    inv_class: InvPortfolioClassSchema = Field(serialization_alias="class")
    market: str
    status: InvPortfolioStatusSchema
    currency: str
    tax_rate: float
    default_exchange_rate: float
    perc_usa: float
    perc_eu: float
    perc_other_developed: float
    perc_emerging: float
    perc_other: float
    expiration_date: Optional[date]
    created_at: datetime
    updated_at: datetime
    current_average_unit_cost: Optional[float] = None


class InvestmentPortfolioTransactionCreate(BaseModel):
    asset_pk: int
    trade_date: date
    transaction_type: InvPortfolioTxTypeSchema
    quantity: float = Field(..., gt=0)
    unit_price: float
    exchange_rate: float = Field(default=1.0, gt=0)
    fees: float = Field(default=0.0, ge=0)
    plus_minus: Optional[float] = None

    @model_validator(mode="after")
    def sell_requires_plus_minus(self):
        if self.transaction_type == InvPortfolioTxTypeSchema.sell and self.plus_minus is None:
            raise ValueError("plus_minus is required for sell transactions (taxable margin)")
        return self


class InvestmentPortfolioTransactionUpdate(BaseModel):
    trade_date: Optional[date] = None
    transaction_type: Optional[InvPortfolioTxTypeSchema] = None
    quantity: Optional[float] = None
    unit_price: Optional[float] = None
    exchange_rate: Optional[float] = Field(default=None, gt=0)
    fees: Optional[float] = Field(default=None, ge=0)
    plus_minus: Optional[float] = None

    @model_validator(mode="after")
    def quantity_positive_when_set(self):
        if self.quantity is not None and self.quantity <= 0:
            raise ValueError("quantity must be greater than 0")
        return self


class InvestmentPortfolioTransactionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    asset_pk: int
    trade_date: date
    transaction_type: InvPortfolioTxTypeSchema
    quantity: float
    unit_price: float
    exchange_rate: float
    fees: float
    plus_minus: float
    average_unit_cost_after_trade: Optional[float] = None
    created_at: datetime
    updated_at: datetime


class InvestmentPortfolioImportResult(BaseModel):
    created: int = 0
    updated: int = 0
    skipped: int = 0
    errors: List[str] = Field(default_factory=list)


class InvestmentPortfolioMarketQuoteLine(BaseModel):
    asset_pk: int = Field(..., ge=1)
    market_unit_price: float = Field(..., ge=0)


class InvestmentPortfolioMarketQuotesBulk(BaseModel):
    as_of_date: date
    quotes: List[InvestmentPortfolioMarketQuoteLine]


class InvestmentPortfolioMarketQuotesBulkResult(BaseModel):
    upserted: int = 0
    errors: List[str] = Field(default_factory=list)


class InvestmentPortfolioMarketQuoteResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    as_of_date: date
    asset_pk: int
    market_unit_price: float
    created_at: datetime
    updated_at: datetime


# --- Investment portfolio dashboard (read-only aggregate) ---


class InvestmentDashboardBrokerTotal(BaseModel):
    broker: str
    total_controvalore: float
    total_controvalore_after_tax: float


class InvestmentDashboardPositionRow(BaseModel):
    asset_pk: int
    asset_id: str
    asset_name: str
    broker: Optional[str] = None
    shares: float
    unit_valore_with_fees: Optional[float] = None
    total_valore_with_fees: Optional[float] = None
    unit_valore_no_fees: Optional[float] = None
    total_valore_no_fees: Optional[float] = None
    unit_controvalore: Optional[float] = None
    total_controvalore: Optional[float] = None
    total_controvalore_after_tax: Optional[float] = None
    pct_gain_loss_real: Optional[float] = None
    pct_gain_loss_no_fees: Optional[float] = None
    irr: Optional[float] = None
    has_quote: bool = False


class InvestmentDashboardGeoAllocation(BaseModel):
    valore_pct: Dict[str, float]
    controvalore_pct: Dict[str, float]


class InvestmentDashboardGeoByClassRow(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    asset_class: InvPortfolioClassSchema = Field(..., alias="class", serialization_alias="class")
    valore_pct: Dict[str, float]
    controvalore_pct: Dict[str, float]


class InvestmentDashboardClassMixRow(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    asset_class: InvPortfolioClassSchema = Field(..., alias="class", serialization_alias="class")
    valore_pct: float
    controvalore_pct: float


class InvestmentDashboardTimeseriesPoint(BaseModel):
    date: date
    total_valore_with_fees: float
    total_controvalore: float


class InvestmentDashboardUnitPoint(BaseModel):
    date: date
    unit_valore_with_fees: Optional[float] = None
    unit_valore_no_fees: Optional[float] = None
    unit_controvalore: float


class InvestmentDashboardUnitAssetSeries(BaseModel):
    asset_pk: int
    asset_id: str
    asset_name: str
    points: List[InvestmentDashboardUnitPoint] = Field(default_factory=list)


class InvestmentDashboardResponse(BaseModel):
    as_of_date: Optional[date] = None
    currency: str = "EUR"
    totals_by_broker: List[InvestmentDashboardBrokerTotal] = Field(default_factory=list)
    portfolio_irr: Optional[float] = None
    positions: List[InvestmentDashboardPositionRow] = Field(default_factory=list)
    geo_allocation: InvestmentDashboardGeoAllocation
    geo_allocation_by_class: List[InvestmentDashboardGeoByClassRow] = Field(default_factory=list)
    class_mix: List[InvestmentDashboardClassMixRow] = Field(default_factory=list)
    timeseries: List[InvestmentDashboardTimeseriesPoint] = Field(default_factory=list)
    unit_timeseries: List[InvestmentDashboardUnitPoint] = Field(default_factory=list)
    unit_timeseries_by_asset: List[InvestmentDashboardUnitAssetSeries] = Field(default_factory=list)
    unit_chart_asset_pk: Optional[int] = None
    empty_detail: Optional[str] = None
