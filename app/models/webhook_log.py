"""Webhook log model - Track all webhook events"""

from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, Enum
from sqlalchemy.sql import func
import enum
from app.database import Base


class WebhookSource(str, enum.Enum):
    """Webhook source"""
    WHATSAPP = "whatsapp"
    PAYRANT = "payrant"
    TOPUPMATE = "topupmate"


class WebhookLog(Base):
    """Log all webhook events for debugging"""
    
    __tablename__ = "webhook_logs"
    
    # Primary key
    id = Column(Integer, primary_key=True, index=True)
    
    # Source
    source = Column(Enum(WebhookSource), nullable=False, index=True)
    
    # Event details
    event_type = Column(String(50), nullable=True)
    event_id = Column(String(100), nullable=True, index=True)
    
    # Request data
    method = Column(String(10), nullable=False)  # GET, POST
    headers = Column(Text, nullable=True)  # JSON string
    payload = Column(Text, nullable=True)  # JSON string
    query_params = Column(Text, nullable=True)
    
    # Response
    response_status = Column(Integer, nullable=True)
    response_body = Column(Text, nullable=True)
    
    # Processing
    processed = Column(Boolean, default=False)
    error = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    processed_at = Column(DateTime(timezone=True), nullable=True)
    
    def __repr__(self):
        return f"<WebhookLog(id={self.id}, source={self.source}, type={self.event_type})>"
