"""Pydantic schemas for Service requests"""

from pydantic import BaseModel, Field
from typing import Optional


class AirtimePurchaseRequest(BaseModel):
    """Schema for airtime purchase"""
    network: str = Field(..., description="Network name: MTN, GLO, AIRTEL, 9MOBILE")
    amount: float = Field(..., gt=49, lt=50001, description="Amount between 50 and 50000")
    phone_number: Optional[str] = Field(None, description="Phone number (defaults to user's number)")


class DataPurchaseRequest(BaseModel):
    """Schema for data purchase"""
    network: str = Field(..., description="Network name: MTN, GLO, AIRTEL, 9MOBILE")
    plan_id: str = Field(..., description="Data plan ID from service catalog")
    phone_number: Optional[str] = Field(None, description="Phone number (defaults to user's number)")


class ElectricityPaymentRequest(BaseModel):
    """Schema for electricity payment"""
    provider: str = Field(..., description="Provider ID or name")
    meter_number: str = Field(..., min_length=10, max_length=20)
    meter_type: str = Field(..., description="prepaid or postpaid")
    amount: float = Field(..., gt=499, description="Amount (minimum 500)")


class CableTVPaymentRequest(BaseModel):
    """Schema for cable TV subscription"""
    provider: str = Field(..., description="Provider ID: DSTV, GOTV, STARTIMES")
    smartcard_number: str = Field(..., min_length=8, max_length=15)
    plan_id: str = Field(..., description="Plan ID from service catalog")
    sub_type: str = Field(default="renew", description="renew or change")


class WalletFundRequest(BaseModel):
    """Schema for wallet funding"""
    amount: float = Field(..., gt=0, description="Amount to fund")


class WalletTransferRequest(BaseModel):
    """Schema for wallet transfer"""
    recipient_phone: str = Field(..., min_length=10, max_length=15)
    amount: float = Field(..., gt=0)
    note: Optional[str] = None
