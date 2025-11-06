"""Service catalog model - Store available services and plans"""

from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text, Enum
from sqlalchemy.sql import func
import enum
from app.database import Base


class ServiceType(str, enum.Enum):
    """Service types"""
    AIRTIME = "airtime"
    DATA = "data"
    CABLE_TV = "cable_tv"
    ELECTRICITY = "electricity"
    EXAM_PIN = "exam_pin"


class Service(Base):
    """Service catalog - Available services and pricing"""
    
    __tablename__ = "services"
    
    # Primary key
    id = Column(Integer, primary_key=True, index=True)
    
    # Service details
    type = Column(Enum(ServiceType), nullable=False, index=True)
    provider = Column(String(50), nullable=False)  # MTN, DSTV, IKEDC, etc.
    provider_id = Column(String(20), nullable=True)  # ID from TopUpMate API
    
    # Plan details
    plan_id = Column(String(50), nullable=True, index=True)  # Data plan ID from API
    plan_name = Column(String(200), nullable=False)  # "1GB MTN Data", "DSTV Compact"
    plan_code = Column(String(50), nullable=True)
    
    # Pricing
    price = Column(Float, nullable=False)
    original_price = Column(Float, nullable=True)  # For showing discounts
    
    # Additional details
    validity = Column(String(50), nullable=True)  # "30 days", "1 month"
    description = Column(Text, nullable=True)
    
    # Status
    is_available = Column(Boolean, default=True)
    is_popular = Column(Boolean, default=False)
    
    # Metadata
    extra_data = Column(Text, nullable=True)  # JSON string for additional info
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def __repr__(self):
        return f"<Service(id={self.id}, type={self.type}, plan={self.plan_name}, price={self.price})>"
