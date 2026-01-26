"""Pydantic schemas for request/response validation."""
from pydantic import BaseModel, Field
from typing import Optional, List
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


# Transaction Schemas
class TransactionBase(BaseModel):
    """Base transaction schema."""
    bank_name: str
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


class AssetsHistory(AssetsHistoryBase):
    """Schema for assets history response."""
    id: int
    created_at: datetime
    updated_at: datetime

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
