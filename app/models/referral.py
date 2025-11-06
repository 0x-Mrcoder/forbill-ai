"""Referral model - Track user referrals and rewards"""

from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class Referral(Base):
    """Referral tracking model"""
    
    __tablename__ = "referrals"
    
    # Primary key
    id = Column(Integer, primary_key=True, index=True)
    
    # Referrer (user who invited)
    referrer_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    referrer_code = Column(String(20), nullable=False, index=True)
    
    # Referee (user who was invited)
    referee_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    referee_phone = Column(String(15), nullable=False)
    
    # Reward details
    reward_amount = Column(Float, default=0.0)
    reward_status = Column(String(20), default="pending")  # pending, paid, cancelled
    reward_paid_at = Column(DateTime(timezone=True), nullable=True)
    
    # Status
    is_valid = Column(Boolean, default=True)  # False if referee is blocked/fraudulent
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    def __repr__(self):
        return f"<Referral(referrer_id={self.referrer_id}, referee_id={self.referee_id}, reward={self.reward_amount})>"
