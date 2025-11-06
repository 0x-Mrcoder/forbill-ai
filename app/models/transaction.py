"""Transaction model - Records all payment transactions"""

from sqlalchemy import Column, Integer, String, Float, DateTime, Text, Enum, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from app.database import Base


class TransactionType(str, enum.Enum):
    """Transaction types"""
    AIRTIME = "airtime"
    DATA = "data"
    ELECTRICITY = "electricity"
    CABLE_TV = "cable_tv"
    EXAM_PIN = "exam_pin"
    WALLET_FUNDING = "wallet_funding"
    WALLET_TRANSFER = "wallet_transfer"
    REFERRAL_BONUS = "referral_bonus"
    ADMIN_CREDIT = "admin_credit"
    ADMIN_DEBIT = "admin_debit"


class TransactionStatus(str, enum.Enum):
    """Transaction status"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    REVERSED = "reversed"


class Transaction(Base):
    """Transaction model for all financial operations"""
    
    __tablename__ = "transactions"
    
    # Primary key
    id = Column(Integer, primary_key=True, index=True)
    
    # User reference
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # Transaction details
    reference = Column(String(100), unique=True, index=True, nullable=False)
    type = Column(Enum(TransactionType), nullable=False, index=True)
    status = Column(Enum(TransactionStatus), default=TransactionStatus.PENDING, index=True)
    
    # Amounts
    amount = Column(Float, nullable=False)
    previous_balance = Column(Float, nullable=True)
    new_balance = Column(Float, nullable=True)
    
    # Service details
    service_provider = Column(String(50), nullable=True)  # TopUpMate, Payrant, etc.
    network = Column(String(20), nullable=True)  # MTN, GLO, AIRTEL, 9MOBILE
    recipient_phone = Column(String(15), nullable=True)  # For airtime/data
    
    # Specific service data
    plan_id = Column(String(50), nullable=True)  # Data plan ID
    plan_name = Column(String(100), nullable=True)  # e.g., "1GB MTN"
    
    # For bills
    meter_number = Column(String(50), nullable=True)  # Electricity meter
    smartcard_number = Column(String(50), nullable=True)  # Cable TV
    account_number = Column(String(50), nullable=True)  # General purpose
    
    # Response data
    provider_reference = Column(String(100), nullable=True)  # Reference from VTU provider
    provider_response = Column(Text, nullable=True)  # Full response JSON
    token = Column(Text, nullable=True)  # Electricity token, exam pin, etc.
    
    # Additional info
    description = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)
    
    # Idempotency
    idempotency_key = Column(String(100), unique=True, nullable=True, index=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="transactions")
    
    def __repr__(self):
        return f"<Transaction(id={self.id}, ref={self.reference}, type={self.type}, status={self.status})>"
