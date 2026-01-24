"""SQLAlchemy database models."""
from sqlalchemy import Column, Integer, String, Float, Boolean, Date, DateTime, ForeignKey, Enum as SQLEnum
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


class Bank(Base):
    """Bank reference table."""
    __tablename__ = "banks"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False, index=True)
    display_name = Column(String, nullable=False)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())


class Transaction(Base):
    """Transaction table."""
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    bank_name = Column(String, nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)
    amount = Column(Float, nullable=False)
    description = Column(String)
    category = Column(String)
    transaction_type = Column(String)
    is_special = Column(Boolean, default=False)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())


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
    bank_name = Column(String, nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)
    total_cash = Column(Float, nullable=False)
    total_investments = Column(Float, nullable=False)
    total_assets = Column(Float, nullable=False)
    created_at = Column(DateTime, default=func.now())
