"""User preferences model - Store user-specific settings"""

from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.database import Base


class UserPreference(Base):
    """User preferences and settings"""
    
    __tablename__ = "user_preferences"
    
    # Primary key
    id = Column(Integer, primary_key=True, index=True)
    
    # User reference (one-to-one)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    
    # Network preferences
    default_network = Column(String(20), nullable=True)  # MTN, GLO, AIRTEL, 9MOBILE
    
    # Favorite numbers (comma-separated for now, could be JSON in production)
    favorite_numbers = Column(Text, nullable=True)  # "08012345678,08087654321"
    
    # Last used services
    last_airtime_amount = Column(Integer, nullable=True)
    last_data_plan = Column(String(50), nullable=True)
    last_network = Column(String(20), nullable=True)
    
    # Cable TV
    saved_smartcard = Column(String(50), nullable=True)
    saved_cable_provider = Column(String(50), nullable=True)
    
    # Electricity
    saved_meter_number = Column(String(50), nullable=True)
    saved_meter_type = Column(String(20), nullable=True)  # prepaid/postpaid
    saved_electricity_provider = Column(String(50), nullable=True)
    
    # Notification preferences
    notify_on_transaction = Column(Boolean, default=True)
    notify_on_low_balance = Column(Boolean, default=True)
    low_balance_threshold = Column(Integer, default=500)  # Notify when balance < 500
    
    # Relationships
    user = relationship("User", back_populates="preferences")
    
    def __repr__(self):
        return f"<UserPreference(user_id={self.user_id}, network={self.default_network})>"
