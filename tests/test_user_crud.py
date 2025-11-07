"""Tests for user CRUD operations"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base
from app.crud.user import (
    create_user,
    get_user_by_phone,
    get_user_by_id,
    get_user_by_referral_code,
    get_or_create_user,
    update_user_balance,
    generate_referral_code,
    generate_unique_referral_code,
    update_user_profile,
    get_user_preferences,
    update_user_preferences,
)
from app.models.user import User
from app.models.preference import UserPreference


# Create in-memory SQLite database for testing
TEST_DATABASE_URL = "sqlite:///:memory:"


@pytest.fixture
def db_session():
    """Create a test database session"""
    engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    session = TestingSessionLocal()
    yield session
    
    session.close()
    Base.metadata.drop_all(bind=engine)


class TestUserCRUD:
    """Test suite for user CRUD operations"""
    
    def test_generate_referral_code(self):
        """Test referral code generation"""
        code = generate_referral_code()
        assert len(code) == 8
        assert code.isalnum()
        assert code.isupper()
        
        # Should not contain confusing characters
        assert '0' not in code
        assert 'O' not in code
        assert 'I' not in code
        assert '1' not in code
    
    def test_generate_unique_referral_code(self, db_session):
        """Test unique referral code generation"""
        code1 = generate_unique_referral_code(db_session)
        assert len(code1) == 8
        
        # Create user with first code
        user1 = create_user(db_session, "2348012345678")
        
        # Generate another code - should be different
        code2 = generate_unique_referral_code(db_session)
        assert code2 != user1.referral_code
    
    def test_create_user(self, db_session):
        """Test user creation"""
        phone = "2348012345678"
        user = create_user(db_session, phone, full_name="Test User")
        
        assert user.id is not None
        assert user.phone_number == phone
        assert user.name == "Test User"
        assert user.wallet_balance == 0.0
        assert user.is_active is True
        assert len(user.referral_code) == 8
        assert user.referred_by is None
        
        # Check preferences were created
        prefs = get_user_preferences(db_session, user.id)
        assert prefs is not None
        assert prefs.notify_on_transaction is True
    
    def test_create_user_with_referral(self, db_session):
        """Test user creation with referral code"""
        # Create referrer
        referrer = create_user(db_session, "2348011111111", full_name="Referrer")
        
        # Create new user with referral code
        new_user = create_user(
            db_session, 
            "2348022222222",
            full_name="New User",
            referred_by_code=referrer.referral_code
        )
        
        # referred_by stores the referral code, not the ID
        assert new_user.referred_by == referrer.referral_code
    
    def test_get_user_by_phone(self, db_session):
        """Test getting user by phone number"""
        phone = "2348012345678"
        user = create_user(db_session, phone)
        
        found_user = get_user_by_phone(db_session, phone)
        assert found_user is not None
        assert found_user.id == user.id
        assert found_user.phone_number == phone
        
        # Test non-existent user
        not_found = get_user_by_phone(db_session, "2349999999999")
        assert not_found is None
    
    def test_get_user_by_id(self, db_session):
        """Test getting user by ID"""
        user = create_user(db_session, "2348012345678")
        
        found_user = get_user_by_id(db_session, user.id)
        assert found_user is not None
        assert found_user.id == user.id
        
        # Test non-existent ID
        not_found = get_user_by_id(db_session, 99999)
        assert not_found is None
    
    def test_get_user_by_referral_code(self, db_session):
        """Test getting user by referral code"""
        user = create_user(db_session, "2348012345678")
        
        found_user = get_user_by_referral_code(db_session, user.referral_code)
        assert found_user is not None
        assert found_user.id == user.id
        
        # Test non-existent code
        not_found = get_user_by_referral_code(db_session, "INVALID")
        assert not_found is None
    
    def test_get_or_create_user_existing(self, db_session):
        """Test get_or_create with existing user"""
        phone = "2348012345678"
        user = create_user(db_session, phone)
        
        found_user, is_new = get_or_create_user(db_session, phone)
        assert not is_new
        assert found_user.id == user.id
    
    def test_get_or_create_user_new(self, db_session):
        """Test get_or_create with new user"""
        phone = "2348012345678"
        
        user, is_new = get_or_create_user(db_session, phone, full_name="Test User")
        assert is_new
        assert user.phone_number == phone
        assert user.name == "Test User"
    
    def test_update_user_balance_add(self, db_session):
        """Test adding to user balance"""
        user = create_user(db_session, "2348012345678")
        assert user.wallet_balance == 0.0
        
        updated_user = update_user_balance(db_session, user.id, 1000.0, "add")
        assert updated_user.wallet_balance == 1000.0
        
        updated_user = update_user_balance(db_session, user.id, 500.0, "add")
        assert updated_user.wallet_balance == 1500.0
    
    def test_update_user_balance_subtract(self, db_session):
        """Test subtracting from user balance"""
        user = create_user(db_session, "2348012345678")
        
        # Add some balance first
        update_user_balance(db_session, user.id, 1000.0, "add")
        
        # Subtract
        updated_user = update_user_balance(db_session, user.id, 300.0, "subtract")
        assert updated_user.wallet_balance == 700.0
    
    def test_update_user_balance_insufficient(self, db_session):
        """Test subtracting more than available balance"""
        user = create_user(db_session, "2348012345678")
        
        # Add some balance
        update_user_balance(db_session, user.id, 500.0, "add")
        
        # Try to subtract more
        with pytest.raises(ValueError, match="Insufficient balance"):
            update_user_balance(db_session, user.id, 1000.0, "subtract")
    
    def test_update_user_profile(self, db_session):
        """Test updating user profile"""
        user = create_user(db_session, "2348012345678")
        
        updated_user = update_user_profile(
            db_session,
            user.id,
            full_name="Updated Name",
            email="test@example.com"
        )
        
        assert updated_user.name == "Updated Name"
        assert updated_user.email == "test@example.com"
    
    def test_update_user_preferences(self, db_session):
        """Test updating user preferences"""
        user = create_user(db_session, "2348012345678")
        
        prefs = update_user_preferences(
            db_session,
            user.id,
            default_network="mtn",
            notify_on_transaction=False,
            saved_smartcard="1234567890",
            saved_meter_number="0987654321"
        )
        
        assert prefs.default_network == "mtn"
        assert prefs.notify_on_transaction is False
        assert prefs.saved_smartcard == "1234567890"
        assert prefs.saved_meter_number == "0987654321"
    
    def test_multiple_users(self, db_session):
        """Test creating multiple users"""
        user1 = create_user(db_session, "2348011111111", full_name="User One")
        user2 = create_user(db_session, "2348022222222", full_name="User Two")
        user3 = create_user(db_session, "2348033333333", full_name="User Three")
        
        assert user1.id != user2.id != user3.id
        assert user1.referral_code != user2.referral_code != user3.referral_code
        
        # Verify all can be retrieved
        assert get_user_by_phone(db_session, "2348011111111") is not None
        assert get_user_by_phone(db_session, "2348022222222") is not None
        assert get_user_by_phone(db_session, "2348033333333") is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
