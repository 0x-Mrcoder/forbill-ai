"""Tests for wallet service"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime

from app.database import Base
from app.models.user import User
from app.models.transaction import Transaction, TransactionType, TransactionStatus
from app.services.wallet import wallet_service


# Create in-memory database for testing
TEST_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture
def db():
    """Create test database"""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def test_user(db):
    """Create test user"""
    user = User(
        phone_number="2348012345678",
        name="Test User",
        wallet_balance=0.0,
        referral_code="TESTCODE",
        is_active=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def test_get_balance(db, test_user):
    """Test getting wallet balance"""
    balance_info = wallet_service.get_balance(db, test_user.id)
    
    assert balance_info is not None
    assert balance_info["user_id"] == test_user.id
    assert balance_info["balance"] == 0.0
    assert balance_info["phone_number"] == test_user.phone_number
    assert balance_info["is_active"] == True


def test_get_balance_invalid_user(db):
    """Test getting balance for non-existent user"""
    with pytest.raises(ValueError):
        wallet_service.get_balance(db, 999)


def test_credit_wallet(db, test_user):
    """Test crediting wallet"""
    transaction = wallet_service.credit_wallet(
        db=db,
        user_id=test_user.id,
        amount=1000.0,
        description="Test credit"
    )
    
    assert transaction is not None
    assert transaction.user_id == test_user.id
    assert transaction.amount == 1000.0
    assert transaction.type == TransactionType.WALLET_FUNDING
    assert transaction.status == TransactionStatus.COMPLETED
    
    # Check user balance updated
    db.refresh(test_user)
    assert test_user.wallet_balance == 1000.0


def test_credit_wallet_with_reference(db, test_user):
    """Test crediting wallet with custom reference"""
    transaction = wallet_service.credit_wallet(
        db=db,
        user_id=test_user.id,
        amount=500.0,
        description="Test credit",
        reference="CUSTOM-REF-123"
    )
    
    assert transaction.reference == "CUSTOM-REF-123"


def test_credit_wallet_invalid_amount(db, test_user):
    """Test crediting wallet with invalid amount"""
    with pytest.raises(ValueError, match="Amount must be positive"):
        wallet_service.credit_wallet(
            db=db,
            user_id=test_user.id,
            amount=-100.0,
            description="Invalid credit"
        )
    
    # Balance should not change
    db.refresh(test_user)
    assert test_user.wallet_balance == 0.0


def test_debit_wallet(db, test_user):
    """Test debiting wallet"""
    # First credit some amount
    wallet_service.credit_wallet(db, test_user.id, 1000.0, "Initial credit")
    
    # Now debit
    transaction = wallet_service.debit_wallet(
        db=db,
        user_id=test_user.id,
        amount=300.0,
        description="Buy airtime",
        transaction_type=TransactionType.AIRTIME
    )
    
    assert transaction is not None
    assert transaction.amount == 300.0
    assert transaction.type == TransactionType.AIRTIME
    
    # Check balance reduced
    db.refresh(test_user)
    assert test_user.wallet_balance == 700.0


def test_debit_wallet_insufficient_balance(db, test_user):
    """Test debiting wallet with insufficient balance"""
    with pytest.raises(ValueError, match="Insufficient balance"):
        wallet_service.debit_wallet(
            db=db,
            user_id=test_user.id,
            amount=500.0,
            transaction_type=TransactionType.AIRTIME,
            description="Buy airtime"
        )
    
    # Balance should not change
    db.refresh(test_user)
    assert test_user.wallet_balance == 0.0


def test_get_transaction_history(db, test_user):
    """Test getting transaction history"""
    # Create multiple transactions
    wallet_service.credit_wallet(db, test_user.id, 1000.0, "Credit 1")
    wallet_service.credit_wallet(db, test_user.id, 500.0, "Credit 2")
    wallet_service.debit_wallet(
        db, test_user.id, 300.0, "Airtime", TransactionType.AIRTIME
    )
    
    # Get history
    transactions = wallet_service.get_transaction_history(db, test_user.id)
    
    assert len(transactions) == 3
    # Check all transaction types are present
    types = [t.type for t in transactions]
    assert TransactionType.WALLET_FUNDING in types
    assert TransactionType.AIRTIME in types


def test_get_transaction_history_with_type_filter(db, test_user):
    """Test getting transaction history with type filter"""
    # Create different transaction types
    wallet_service.credit_wallet(db, test_user.id, 1000.0, "Credit")
    wallet_service.debit_wallet(
        db, test_user.id, 300.0, "Airtime", TransactionType.AIRTIME
    )
    wallet_service.debit_wallet(
        db, test_user.id, 200.0, "Data", TransactionType.DATA
    )
    
    # Filter by airtime only
    transactions = wallet_service.get_transaction_history(
        db, test_user.id, transaction_type=TransactionType.AIRTIME
    )
    
    assert len(transactions) == 1
    assert transactions[0].type == TransactionType.AIRTIME


def test_get_transaction_history_with_limit(db, test_user):
    """Test getting transaction history with limit"""
    # Create many transactions
    for i in range(10):
        wallet_service.credit_wallet(db, test_user.id, 100.0, f"Credit {i}")
    
    # Get only 5
    transactions = wallet_service.get_transaction_history(db, test_user.id, limit=5)
    
    assert len(transactions) == 5


def test_update_transaction_status(db, test_user):
    """Test updating transaction status"""
    # Create transaction
    transaction = wallet_service.credit_wallet(
        db, test_user.id, 1000.0, "Test credit"
    )
    
    # Update status to pending
    updated = wallet_service.update_transaction_status(
        db=db,
        transaction_id=transaction.id,
        status=TransactionStatus.PENDING,
        provider_response="Processing payment"
    )
    
    assert updated is not None
    
    # Verify update
    db.refresh(transaction)
    assert transaction.status == TransactionStatus.PENDING
    assert transaction.provider_response == "Processing payment"


def test_refund_transaction(db, test_user):
    """Test refunding a transaction"""
    # Credit wallet and make a purchase
    wallet_service.credit_wallet(db, test_user.id, 1000.0, "Initial credit")
    purchase = wallet_service.debit_wallet(
        db, test_user.id, 300.0, "Airtime purchase", TransactionType.AIRTIME
    )
    
    initial_balance = test_user.wallet_balance
    
    # Refund the transaction
    refund_transaction = wallet_service.refund_transaction(
        db=db,
        transaction_id=purchase.id,
        reason="Service failure"
    )
    
    assert refund_transaction is not None
    
    # Check purchase marked as reversed
    db.refresh(purchase)
    assert purchase.status == TransactionStatus.REVERSED
    
    # Check balance refunded
    db.refresh(test_user)
    assert test_user.wallet_balance == initial_balance + 300.0


def test_refund_transaction_invalid_id(db, test_user):
    """Test refunding non-existent transaction"""
    refund = wallet_service.refund_transaction(db=db, transaction_id=999, reason="Test")
    assert refund is None


def test_get_wallet_summary(db, test_user):
    """Test getting wallet summary"""
    # Create various transactions
    wallet_service.credit_wallet(db, test_user.id, 1000.0, "Credit 1")
    wallet_service.credit_wallet(db, test_user.id, 500.0, "Credit 2")
    wallet_service.debit_wallet(
        db, test_user.id, 300.0, "Airtime", TransactionType.AIRTIME
    )
    wallet_service.debit_wallet(
        db, test_user.id, 200.0, "Data", TransactionType.DATA
    )
    
    # Get summary
    summary = wallet_service.get_wallet_summary(db, test_user.id)
    
    assert summary is not None
    assert summary["current_balance"] == 1000.0
    assert summary["total_funded"] == 1500.0
    # Debits are PENDING status, so total_spent only counts COMPLETED
    assert summary["total_spent"] == 0.0  
    assert summary["total_transactions"] == 4
    assert summary["completed_transactions"] == 2  # Only the credits are completed
    assert summary["pending_transactions"] == 2  # The debits are pending


def test_check_sufficient_balance(db, test_user):
    """Test checking sufficient balance"""
    # Credit wallet
    wallet_service.credit_wallet(db, test_user.id, 1000.0, "Credit")
    
    # Check sufficient
    result = wallet_service.check_sufficient_balance(db, test_user.id, 500.0)
    assert result["has_sufficient_balance"] == True
    assert result["shortfall"] == 0
    
    # Check insufficient
    result = wallet_service.check_sufficient_balance(db, test_user.id, 1500.0)
    assert result["has_sufficient_balance"] == False
    assert result["shortfall"] == 500.0


def test_get_transaction_by_reference(db, test_user):
    """Test getting transaction by reference"""
    # Create transaction
    transaction = wallet_service.credit_wallet(
        db=db,
        user_id=test_user.id,
        amount=1000.0,
        description="Test",
        reference="TEST-REF-123"
    )
    
    # Find by reference
    found = wallet_service.get_transaction_by_reference(db, "TEST-REF-123")
    
    assert found is not None
    assert found.id == transaction.id
    assert found.reference == "TEST-REF-123"


def test_get_transaction_by_reference_not_found(db):
    """Test getting non-existent transaction by reference"""
    found = wallet_service.get_transaction_by_reference(db, "NONEXISTENT")
    assert found is None


def test_multiple_users_isolation(db):
    """Test that wallet operations are isolated per user"""
    # Create two users
    user1 = User(
        phone_number="2348012345678",
        name="User 1",
        wallet_balance=0.0,
        referral_code="USER1",
        is_active=True
    )
    user2 = User(
        phone_number="2348087654321",
        name="User 2",
        wallet_balance=0.0,
        referral_code="USER2",
        is_active=True
    )
    db.add_all([user1, user2])
    db.commit()
    db.refresh(user1)
    db.refresh(user2)
    
    # Credit user1
    wallet_service.credit_wallet(db, user1.id, 1000.0, "Credit user1")
    
    # Check balances
    db.refresh(user1)
    db.refresh(user2)
    assert user1.wallet_balance == 1000.0
    assert user2.wallet_balance == 0.0
    
    # Check transaction history
    user1_txns = wallet_service.get_transaction_history(db, user1.id)
    user2_txns = wallet_service.get_transaction_history(db, user2.id)
    
    assert len(user1_txns) == 1
    assert len(user2_txns) == 0
