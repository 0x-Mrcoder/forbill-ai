"""Pydantic schemas for User model"""

from pydantic import BaseModel, Field, validator
from datetime import datetime
from typing import Optional


class UserBase(BaseModel):
    """Base user schema"""
    phone_number: str = Field(..., min_length=10, max_length=15)
    name: Optional[str] = None
    email: Optional[str] = None


class UserCreate(UserBase):
    """Schema for creating a user"""
    nin: Optional[str] = Field(None, min_length=11, max_length=11)
    referred_by: Optional[str] = None  # Referral code


class UserUpdate(BaseModel):
    """Schema for updating user"""
    name: Optional[str] = None
    email: Optional[str] = None
    default_network: Optional[str] = None
    nin: Optional[str] = None


class UserResponse(UserBase):
    """Schema for user response"""
    id: int
    wallet_balance: float
    virtual_account_number: Optional[str] = None
    virtual_account_name: Optional[str] = None
    referral_code: Optional[str] = None
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


class UserWalletResponse(BaseModel):
    """Schema for wallet balance response"""
    user_id: int
    phone_number: str
    wallet_balance: float
    virtual_account_number: Optional[str] = None
    
    class Config:
        from_attributes = True
