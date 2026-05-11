"""SQLAlchemy database models."""
from sqlalchemy import Column, Integer, String, Float, Boolean, Date, DateTime, ForeignKey, Enum as SQLEnum, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from .database import Base


class InvestmentType(str, enum.Enum):
    """Investment type enumeration."""
    ONE_TIME = "one_time"
    SIP = "sip"


class WithdrawalType(str, enum.Enum):
    """Withdrawal type enumeration."""
    IN = "in"
    OUT = "out"


class AssetType(str, enum.Enum):
    """Asset type enumeration."""
    CASH = "cash"
    INVESTMENT = "investment"


class InvPortfolioKind(str, enum.Enum):
    """Portfolio instrument kind (TODO: type)."""
    fund = "fund"
    bond = "bond"
    share = "share"


class InvPortfolioClass(str, enum.Enum):
    """Portfolio instrument class (TODO: class)."""
    share = "share"
    bond = "bond"
    commodity = "commodity"


class InvPortfolioStatus(str, enum.Enum):
    """Lifecycle status for portfolio instruments."""
    active = "active"
    sold = "sold"
    special = "special"


class InvPortfolioTxType(str, enum.Enum):
    """Buy/sell for portfolio trades."""
    purchase = "purchase"
    sell = "sell"


class AssetTypeRef(Base):
    """Dynamic asset type reference table."""
    __tablename__ = "asset_types"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False, index=True)  # e.g., "cash", "investment", "crypto"
    display_name = Column(String, nullable=False)  # e.g., "Cash", "Investment", "Crypto"
    created_at = Column(DateTime, default=func.now())


class Bank(Base):
    """Bank reference table."""
    __tablename__ = "banks"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False, index=True)
    display_name = Column(String, nullable=False)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())


class Account(Base):
    """Account reference table."""
    __tablename__ = "accounts"

    id = Column(Integer, primary_key=True, index=True)
    bank_name = Column(String, nullable=False, index=True)
    account_name = Column(String, nullable=False, index=True)
    asset_type = Column(SQLEnum(AssetType), nullable=True, index=True)  # cash or investment
    status = Column(Boolean, default=True, nullable=False)  # True=live, False=closed
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Composite unique constraint on (bank_name, account_name)
    __table_args__ = (
        Index('idx_accounts_bank_account', 'bank_name', 'account_name', unique=True),
    )


class Transaction(Base):
    """Transaction table."""
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    bank_name = Column(String, nullable=False, index=True)
    account_name = Column(String, nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)
    amount = Column(Float, nullable=False)
    description = Column(String)
    details = Column(String)
    category = Column(String)
    transaction_type = Column(String)
    is_special = Column(Boolean, default=False)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())


class IntesaRawTransaction(Base):
    """Raw Intesa transaction data before preprocessing."""
    __tablename__ = "intesa_raw_transactions"

    id = Column(Integer, primary_key=True, index=True)
    transaction_id = Column(Integer, ForeignKey("transactions.id"), nullable=True, unique=True, index=True)
    data = Column(Date, nullable=False, index=True)
    operazione = Column(String)
    dettagli = Column(String)
    conto_o_carta = Column(String)
    contabilizzazione = Column(String)
    categoria = Column(String)
    valuta = Column(String)
    importo = Column(Float, nullable=False)
    created_at = Column(DateTime, default=func.now())

    # Relationship
    transaction = relationship("Transaction", backref="intesa_raw_transaction", uselist=False)


class AllianzRawTransaction(Base):
    """Raw Allianz transaction data before preprocessing."""
    __tablename__ = "allianz_raw_transactions"

    id = Column(Integer, primary_key=True, index=True)
    transaction_id = Column(Integer, ForeignKey("transactions.id"), nullable=True, unique=True, index=True)
    data_contabile = Column(Date, nullable=False, index=True)
    data_valuta = Column(Date)
    descrizione = Column(String)
    importo = Column(Float, nullable=False)
    created_at = Column(DateTime, default=func.now())

    # Relationship
    transaction = relationship("Transaction", backref="allianz_raw_transaction", uselist=False)


class InvestmentProduct(Base):
    """Investment product table."""
    __tablename__ = "investment_products"

    id = Column(Integer, primary_key=True, index=True)
    product_name = Column(String, nullable=False, index=True)
    bank_name = Column(String, nullable=False, index=True)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=True)
    investment_type = Column(SQLEnum(InvestmentType), nullable=False)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relationships
    sip_plan = relationship("SIPPlan", back_populates="product", uselist=False)
    observations = relationship("InvestmentObservation", back_populates="product", cascade="all, delete-orphan")


class SIPPlan(Base):
    """SIP plan table."""
    __tablename__ = "sip_plans"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("investment_products.id"), nullable=False, unique=True)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=True)
    monthly_contribution = Column(Float, nullable=False)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relationships
    product = relationship("InvestmentProduct", back_populates="sip_plan")


class InvestmentObservation(Base):
    """Investment observation table."""
    __tablename__ = "investment_observations"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("investment_products.id"), nullable=False, index=True)
    observation_date = Column(Date, nullable=False, index=True)
    num_shares = Column(Float, nullable=False)
    total_invested = Column(Float, nullable=False)
    current_value = Column(Float, nullable=False)
    created_at = Column(DateTime, default=func.now())

    # Relationships
    product = relationship("InvestmentProduct", back_populates="observations")


class InvestmentWithdrawal(Base):
    """Investment withdrawal table."""
    __tablename__ = "investment_withdrawals"

    id = Column(Integer, primary_key=True, index=True)
    bank_name = Column(String, nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)
    type = Column(SQLEnum(WithdrawalType), nullable=False)
    amount = Column(Float, nullable=False)
    description = Column(String)
    created_at = Column(DateTime, default=func.now())


class AssetsHistory(Base):
    """Assets history table."""
    __tablename__ = "assets_history"

    id = Column(Integer, primary_key=True, index=True)
    account_name = Column(String, nullable=False, index=True)
    bank_name = Column(String, nullable=False, index=True)
    asset_type = Column(SQLEnum(AssetType), nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)
    amount = Column(Float, nullable=False)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Composite index for efficient queries
    __table_args__ = (
        Index('idx_assets_history_bank_account_type_date', 'bank_name', 'account_name', 'asset_type', 'date'),
    )


class InvestmentPortfolioAsset(Base):
    """User-defined investment asset (fund/share/bond) for portfolio tracking."""

    __tablename__ = "investment_portfolio_assets"

    id = Column(Integer, primary_key=True, index=True)
    asset_id = Column(String, unique=True, nullable=False, index=True)
    asset_name = Column(String, nullable=False)
    isin = Column(String, nullable=True, index=True)
    ticker = Column(String, nullable=True, index=True)
    issuer = Column(String, nullable=True)
    broker = Column(String, nullable=True)
    inv_kind = Column(SQLEnum(InvPortfolioKind), nullable=False, index=True)
    inv_class = Column(SQLEnum(InvPortfolioClass), nullable=False)
    market = Column(String, nullable=False, default="Borsa Italiana")
    status = Column(SQLEnum(InvPortfolioStatus), nullable=False, default=InvPortfolioStatus.active, index=True)
    currency = Column(String, nullable=False, default="EUR")
    tax_rate = Column(Float, nullable=False, default=0.26)
    default_exchange_rate = Column(Float, nullable=False, default=1.0)
    perc_usa = Column(Float, nullable=False, default=0.0)
    perc_eu = Column(Float, nullable=False, default=0.0)
    perc_other_developed = Column(Float, nullable=False, default=0.0)
    perc_emerging = Column(Float, nullable=False, default=0.0)
    perc_other = Column(Float, nullable=False, default=0.0)
    expiration_date = Column(Date, nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    transactions = relationship(
        "InvestmentPortfolioTransaction",
        back_populates="asset",
        cascade="all, delete-orphan",
        order_by="InvestmentPortfolioTransaction.trade_date, InvestmentPortfolioTransaction.id",
    )


class InvestmentPortfolioTransaction(Base):
    """Purchase/sell line for a portfolio asset."""

    __tablename__ = "investment_portfolio_transactions"

    id = Column(Integer, primary_key=True, index=True)
    asset_pk = Column(Integer, ForeignKey("investment_portfolio_assets.id"), nullable=False, index=True)
    trade_date = Column(Date, nullable=False, index=True)
    transaction_type = Column(SQLEnum(InvPortfolioTxType), nullable=False, index=True)
    quantity = Column(Float, nullable=False)
    unit_price = Column(Float, nullable=False)
    exchange_rate = Column(Float, nullable=False, default=1.0)
    fees = Column(Float, nullable=False, default=0.0)
    # Taxable margin on sell (loss or gain); user-provided. Purchases store 0.
    plus_minus = Column(Float, nullable=False, default=0.0)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    asset = relationship("InvestmentPortfolioAsset", back_populates="transactions")

    __table_args__ = (Index("idx_inv_portfolio_tx_asset_date", "asset_pk", "trade_date"),)
