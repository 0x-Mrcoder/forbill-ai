"""Pydantic schemas"""

from app.schemas.user import (
    UserBase,
    UserCreate,
    UserUpdate,
    UserResponse,
    UserWalletResponse
)
from app.schemas.transaction import (
    TransactionBase,
    TransactionCreate,
    TransactionResponse,
    TransactionListResponse
)
from app.schemas.service import (
    AirtimePurchaseRequest,
    DataPurchaseRequest,
    ElectricityPaymentRequest,
    CableTVPaymentRequest,
    WalletFundRequest,
    WalletTransferRequest
)

__all__ = [
    "UserBase",
    "UserCreate",
    "UserUpdate",
    "UserResponse",
    "UserWalletResponse",
    "TransactionBase",
    "TransactionCreate",
    "TransactionResponse",
    "TransactionListResponse",
    "AirtimePurchaseRequest",
    "DataPurchaseRequest",
    "ElectricityPaymentRequest",
    "CableTVPaymentRequest",
    "WalletFundRequest",
    "WalletTransferRequest",
]
