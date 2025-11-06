"""Application configuration settings"""

from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # Environment
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    
    # App Info
    APP_NAME: str = "ForBill"
    APP_VERSION: str = "1.0.0"
    
    # Database
    DATABASE_URL: str = "sqlite:///./forbill.db"  # Default to SQLite for local dev
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # WhatsApp Meta API
    WHATSAPP_ACCESS_TOKEN: str
    WHATSAPP_PHONE_NUMBER_ID: str
    WHATSAPP_BUSINESS_ACCOUNT_ID: str
    WHATSAPP_PHONE_NUMBER: str
    WHATSAPP_APP_ID: str = "3226882497473467"
    WHATSAPP_VERIFY_TOKEN: str
    WHATSAPP_APP_SECRET: Optional[str] = None
    WHATSAPP_API_VERSION: str = "v18.0"
    
    # TopUpMate VTU API
    TOPUPMATE_API_KEY: str
    TOPUPMATE_BASE_URL: str = "https://connect.topupmate.com/api/"
    
    # Payrant Payment Gateway
    PAYRANT_API_KEY: str
    PAYRANT_BASE_URL: str = "https://api-core.payrant.com/"
    
    # Security
    SECRET_KEY: str = "development-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_HOURS: int = 24
    
    # CORS
    CORS_ORIGINS: str = "*"
    
    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 20
    RATE_LIMIT_PER_HOUR: int = 500
    
    # Transaction Limits
    MIN_AIRTIME_AMOUNT: int = 50
    MAX_AIRTIME_AMOUNT: int = 50000
    MIN_WALLET_BALANCE: int = 0
    MAX_TRANSACTION_AMOUNT: int = 100000
    
    # Referral Rewards
    REFERRAL_BONUS: int = 100  # Bonus amount in Naira
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Global settings instance
settings = Settings()
