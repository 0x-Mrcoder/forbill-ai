"""Admin action log model - Track admin activities"""

from sqlalchemy import Column, Integer, String, DateTime, Text, Float
from sqlalchemy.sql import func
from app.database import Base


class AdminLog(Base):
    """Log admin actions for audit trail"""
    
    __tablename__ = "admin_logs"
    
    # Primary key
    id = Column(Integer, primary_key=True, index=True)
    
    # Admin details
    admin_username = Column(String(50), nullable=False, index=True)
    admin_ip = Column(String(50), nullable=True)
    
    # Action details
    action_type = Column(String(50), nullable=False, index=True)  # credit_wallet, block_user, etc.
    target_user_id = Column(Integer, nullable=True)
    target_phone = Column(String(15), nullable=True)
    
    # Details
    amount = Column(Float, nullable=True)  # For wallet adjustments
    description = Column(Text, nullable=True)
    extra_data = Column(Text, nullable=True)  # JSON string (renamed from metadata to avoid SQLAlchemy conflict)
    
    # Timestamp
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    def __repr__(self):
        return f"<AdminLog(id={self.id}, admin={self.admin_username}, action={self.action_type})>"
