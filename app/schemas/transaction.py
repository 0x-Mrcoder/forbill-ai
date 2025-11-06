"""Pydantic schemas for Transaction model"""

from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
from app.models.transaction import TransactionType, TransactionStatus


class TransactionBase(BaseModel):
    """Base transaction schema"""
    type: TransactionType
    amount: float = Field(..., gt=0)
    description: Optional[str] = None


class TransactionCreate(TransactionBase):
    """Schema for creating a transaction"""
    network: Optional[str] = None
    recipient_phone: Optional[str] = None
    plan_id: Optional[str] = None
    meter_number: Optional[str] = None
    smartcard_number: Optional[str] = None
    idempotency_key: Optional[str] = None


class TransactionResponse(TransactionBase):
    """Schema for transaction response"""
    id: int
    user_id: int
    reference: str
    status: TransactionStatus
    previous_balance: Optional[float] = None
    new_balance: Optional[float] = None
    network: Optional[str] = None
    recipient_phone: Optional[str] = None
    plan_name: Optional[str] = None
    token: Optional[str] = None
    provider_reference: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class TransactionListResponse(BaseModel):
    """Schema for transaction list"""
    transactions: list[TransactionResponse]
    total: int
    page: int
    page_size: int
