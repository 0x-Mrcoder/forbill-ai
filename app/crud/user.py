"""User CRUD operations"""

from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import desc
from loguru import logger
import secrets
import string

from app.models.user import User
from app.models.preference import UserPreference
from app.models.transaction import Transaction


def generate_referral_code(length: int = 8) -> str:
    """
    Generate a unique referral code
    
    Args:
        length: Length of the code (default: 8)
        
    Returns:
        Alphanumeric referral code
    """
    characters = string.ascii_uppercase + string.digits
    # Exclude confusing characters: 0, O, I, 1
    characters = characters.replace('0', '').replace('O', '').replace('I', '').replace('1', '')
    return ''.join(secrets.choice(characters) for _ in range(length))


def generate_unique_referral_code(db: Session, max_attempts: int = 10) -> str:
    """
    Generate a unique referral code that doesn't exist in database
    
    Args:
        db: Database session
        max_attempts: Maximum attempts to generate unique code
        
    Returns:
        Unique referral code
        
    Raises:
        RuntimeError: If unable to generate unique code
    """
    for _ in range(max_attempts):
        code = generate_referral_code()
        existing = db.query(User).filter(User.referral_code == code).first()
        if not existing:
            return code
    
    raise RuntimeError("Unable to generate unique referral code")


def get_user_by_phone(db: Session, phone_number: str) -> Optional[User]:
    """
    Get user by phone number
    
    Args:
        db: Database session
        phone_number: User's phone number
        
    Returns:
        User object or None
    """
    return db.query(User).filter(User.phone_number == phone_number).first()


def get_user_by_id(db: Session, user_id: int) -> Optional[User]:
    """
    Get user by ID
    
    Args:
        db: Database session
        user_id: User ID
        
    Returns:
        User object or None
    """
    return db.query(User).filter(User.id == user_id).first()


def get_user_by_referral_code(db: Session, referral_code: str) -> Optional[User]:
    """
    Get user by referral code
    
    Args:
        db: Database session
        referral_code: Referral code
        
    Returns:
        User object or None
    """
    return db.query(User).filter(User.referral_code == referral_code).first()


def create_user(
    db: Session,
    phone_number: str,
    full_name: Optional[str] = None,
    referred_by_code: Optional[str] = None
) -> User:
    """
    Create a new user with default settings
    
    Args:
        db: Database session
        phone_number: User's phone number (international format)
        full_name: User's full name (optional)
        referred_by_code: Referral code of referrer (optional)
        
    Returns:
        Created User object
    """
    # Generate unique referral code
    referral_code = generate_unique_referral_code(db)
    
    # Handle referrer - store their code if valid
    referred_by_code_value = None
    if referred_by_code:
        referrer = get_user_by_referral_code(db, referred_by_code)
        if referrer:
            referred_by_code_value = referred_by_code  # Store the code itself
            logger.info(f"User referred by: {referrer.phone_number} (code: {referred_by_code})")
    
    # Create user
    user = User(
        phone_number=phone_number,
        name=full_name,  # Note: model uses 'name' not 'full_name'
        referral_code=referral_code,
        wallet_balance=0.0,
        is_active=True,
        referred_by=referred_by_code_value  # Store the referral code, not ID
    )
    
    db.add(user)
    db.commit()
    db.refresh(user)
    
    # Create default preferences
    preferences = UserPreference(
        user_id=user.id,
        notify_on_transaction=True
    )
    db.add(preferences)
    db.commit()
    
    logger.info(f"Created new user: {phone_number} (ID: {user.id}, Code: {referral_code})")
    
    return user


def get_or_create_user(
    db: Session,
    phone_number: str,
    full_name: Optional[str] = None,
    referred_by_code: Optional[str] = None
) -> tuple[User, bool]:
    """
    Get existing user or create new one
    
    Args:
        db: Database session
        phone_number: User's phone number
        full_name: User's full name (optional)
        referred_by_code: Referral code (optional)
        
    Returns:
        Tuple of (User object, is_new boolean)
    """
    user = get_user_by_phone(db, phone_number)
    
    if user:
        return user, False
    
    user = create_user(db, phone_number, full_name, referred_by_code)
    return user, True


def update_user_balance(
    db: Session,
    user_id: int,
    amount: float,
    operation: str = "add"
) -> User:
    """
    Update user's wallet balance
    
    Args:
        db: Database session
        user_id: User ID
        amount: Amount to add or subtract
        operation: 'add' or 'subtract'
        
    Returns:
        Updated User object
        
    Raises:
        ValueError: If insufficient balance for subtraction
    """
    user = get_user_by_id(db, user_id)
    if not user:
        raise ValueError(f"User {user_id} not found")
    
    if operation == "add":
        user.wallet_balance += amount
        logger.info(f"Added ₦{amount:,.2f} to user {user_id}. New balance: ₦{user.wallet_balance:,.2f}")
    elif operation == "subtract":
        if user.wallet_balance < amount:
            raise ValueError(f"Insufficient balance. Available: ₦{user.wallet_balance:,.2f}, Required: ₦{amount:,.2f}")
        user.wallet_balance -= amount
        logger.info(f"Deducted ₦{amount:,.2f} from user {user_id}. New balance: ₦{user.wallet_balance:,.2f}")
    else:
        raise ValueError(f"Invalid operation: {operation}")
    
    db.commit()
    db.refresh(user)
    
    return user


def get_user_transactions(
    db: Session,
    user_id: int,
    limit: int = 10,
    offset: int = 0
) -> List[Transaction]:
    """
    Get user's transaction history
    
    Args:
        db: Database session
        user_id: User ID
        limit: Number of transactions to return
        offset: Offset for pagination
        
    Returns:
        List of Transaction objects
    """
    return (
        db.query(Transaction)
        .filter(Transaction.user_id == user_id)
        .order_by(desc(Transaction.created_at))
        .limit(limit)
        .offset(offset)
        .all()
    )


def update_user_profile(
    db: Session,
    user_id: int,
    full_name: Optional[str] = None,
    email: Optional[str] = None
) -> User:
    """
    Update user profile information
    
    Args:
        db: Database session
        user_id: User ID
        full_name: New full name (optional)
        email: New email (optional)
        
    Returns:
        Updated User object
    """
    user = get_user_by_id(db, user_id)
    if not user:
        raise ValueError(f"User {user_id} not found")
    
    if full_name is not None:
        user.name = full_name  # Note: model uses 'name' not 'full_name'
    
    if email is not None:
        user.email = email
    
    db.commit()
    db.refresh(user)
    
    logger.info(f"Updated profile for user {user_id}")
    
    return user


def deactivate_user(db: Session, user_id: int) -> User:
    """
    Deactivate a user account
    
    Args:
        db: Database session
        user_id: User ID
        
    Returns:
        Updated User object
    """
    user = get_user_by_id(db, user_id)
    if not user:
        raise ValueError(f"User {user_id} not found")
    
    user.is_active = False
    db.commit()
    db.refresh(user)
    
    logger.info(f"Deactivated user {user_id}")
    
    return user


def get_user_preferences(db: Session, user_id: int) -> Optional[UserPreference]:
    """
    Get user's preferences
    
    Args:
        db: Database session
        user_id: User ID
        
    Returns:
        UserPreference object or None
    """
    return db.query(UserPreference).filter(UserPreference.user_id == user_id).first()


def update_user_preferences(
    db: Session,
    user_id: int,
    default_network: Optional[str] = None,
    notify_on_transaction: Optional[bool] = None,
    saved_smartcard: Optional[str] = None,
    saved_meter_number: Optional[str] = None
) -> UserPreference:
    """
    Update user preferences
    
    Args:
        db: Database session
        user_id: User ID
        default_network: Preferred network
        notify_on_transaction: Enable/disable transaction notifications
        saved_smartcard: Saved smartcard number
        saved_meter_number: Saved meter number
        
    Returns:
        Updated UserPreference object
    """
    preferences = get_user_preferences(db, user_id)
    if not preferences:
        # Create if doesn't exist
        preferences = UserPreference(user_id=user_id)
        db.add(preferences)
    
    if default_network is not None:
        preferences.default_network = default_network
    
    if notify_on_transaction is not None:
        preferences.notify_on_transaction = notify_on_transaction
    
    if saved_smartcard is not None:
        preferences.saved_smartcard = saved_smartcard
    
    if saved_meter_number is not None:
        preferences.saved_meter_number = saved_meter_number
    
    db.commit()
    db.refresh(preferences)
    
    logger.info(f"Updated preferences for user {user_id}")
    
    return preferences
