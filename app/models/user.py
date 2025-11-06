"""User model - Stores user information and wallet data"""

from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class User(Base):
    """User model for ForBill customers"""
    
    __tablename__ = "users"
    
    # Primary key
    id = Column(Integer, primary_key=True, index=True)
    
    # User details
    phone_number = Column(String(15), unique=True, index=True, nullable=False)
    name = Column(String(100), nullable=True)
    email = Column(String(100), nullable=True)
    
    # Wallet
    wallet_balance = Column(Float, default=0.0, nullable=False)
    
    # Payrant virtual account details
    virtual_account_number = Column(String(20), nullable=True)
    virtual_account_name = Column(String(100), nullable=True)
    account_reference = Column(String(100), unique=True, nullable=True)
    
    # User preferences
    default_network = Column(String(20), nullable=True)  # MTN, GLO, AIRTEL, 9MOBILE
    
    # Referral
    referral_code = Column(String(20), unique=True, index=True, nullable=True)
    referred_by = Column(String(20), nullable=True)  # Referral code of referrer
    referral_bonus_claimed = Column(Boolean, default=False)
    
    # NIN for Payrant (optional - can be added later)
    nin = Column(String(11), nullable=True)
    
    # Status
    is_active = Column(Boolean, default=True)
    is_blocked = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_activity = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    transactions = relationship("Transaction", back_populates="user", cascade="all, delete-orphan")
    preferences = relationship("UserPreference", back_populates="user", uselist=False, cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<User(id={self.id}, phone={self.phone_number}, balance={self.wallet_balance})>"
