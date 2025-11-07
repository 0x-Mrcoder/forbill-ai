"""Wallet management service"""

from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from loguru import logger
from datetime import datetime

from app.models.user import User
from app.models.transaction import Transaction, TransactionType, TransactionStatus
from app.crud.user import get_user_by_id, get_user_by_phone, update_user_balance
from app.utils.helpers import generate_reference, format_currency


class WalletService:
    """Service for managing user wallet operations"""
    
    def __init__(self):
        pass
    
    def get_balance(self, db: Session, user_id: int) -> Dict[str, Any]:
        """
        Get user's wallet balance
        
        Args:
            db: Database session
            user_id: User ID
            
        Returns:
            Dictionary with balance and account info
        """
        user = get_user_by_id(db, user_id)
        if not user:
            raise ValueError(f"User {user_id} not found")
        
        return {
            "user_id": user.id,
            "phone_number": user.phone_number,
            "balance": user.wallet_balance,
            "balance_formatted": format_currency(user.wallet_balance),
            "virtual_account": user.virtual_account_number,
            "virtual_account_name": user.virtual_account_name,
            "is_active": user.is_active
        }
    
    def credit_wallet(
        self,
        db: Session,
        user_id: int,
        amount: float,
        description: str,
        reference: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Transaction:
        """
        Credit user's wallet
        
        Args:
            db: Database session
            user_id: User ID
            amount: Amount to credit
            description: Transaction description
            reference: Transaction reference (auto-generated if not provided)
            metadata: Additional transaction metadata
            
        Returns:
            Created Transaction object
        """
        if amount <= 0:
            raise ValueError("Amount must be positive")
        
        user = get_user_by_id(db, user_id)
        if not user:
            raise ValueError(f"User {user_id} not found")
        
        # Generate reference if not provided
        if not reference:
            reference = generate_reference("CREDIT")
        
        # Create transaction record
        transaction = Transaction(
            user_id=user_id,
            type=TransactionType.WALLET_FUNDING,
            amount=amount,
            status=TransactionStatus.COMPLETED,
            reference=reference,
            description=description,
            provider_response=str(metadata) if metadata else None
        )
        
        db.add(transaction)
        
        # Update user balance
        update_user_balance(db, user_id, amount, "add")
        
        db.commit()
        db.refresh(transaction)
        
        logger.info(f"Credited ₦{amount:,.2f} to user {user_id}. Ref: {reference}")
        
        return transaction
    
    def debit_wallet(
        self,
        db: Session,
        user_id: int,
        amount: float,
        description: str,
        transaction_type: TransactionType,
        reference: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Transaction:
        """
        Debit user's wallet
        
        Args:
            db: Database session
            user_id: User ID
            amount: Amount to debit
            description: Transaction description
            transaction_type: Type of transaction
            reference: Transaction reference (auto-generated if not provided)
            metadata: Additional transaction metadata
            
        Returns:
            Created Transaction object
            
        Raises:
            ValueError: If insufficient balance
        """
        if amount <= 0:
            raise ValueError("Amount must be positive")
        
        user = get_user_by_id(db, user_id)
        if not user:
            raise ValueError(f"User {user_id} not found")
        
        # Check balance
        if user.wallet_balance < amount:
            raise ValueError(
                f"Insufficient balance. Available: {format_currency(user.wallet_balance)}, "
                f"Required: {format_currency(amount)}"
            )
        
        # Generate reference if not provided
        if not reference:
            reference = generate_reference(transaction_type.value.upper())
        
        # Create transaction record
        transaction = Transaction(
            user_id=user_id,
            type=transaction_type,
            amount=amount,
            status=TransactionStatus.PENDING,
            reference=reference,
            description=description,
            provider_response=str(metadata) if metadata else None
        )
        
        db.add(transaction)
        
        # Deduct from balance
        update_user_balance(db, user_id, amount, "subtract")
        
        db.commit()
        db.refresh(transaction)
        
        logger.info(f"Debited ₦{amount:,.2f} from user {user_id}. Ref: {reference}")
        
        return transaction
    
    def get_transaction_history(
        self,
        db: Session,
        user_id: int,
        limit: int = 20,
        offset: int = 0,
        transaction_type: Optional[TransactionType] = None,
        status: Optional[TransactionStatus] = None
    ) -> List[Transaction]:
        """
        Get user's transaction history
        
        Args:
            db: Database session
            user_id: User ID
            limit: Number of transactions to return
            offset: Offset for pagination
            transaction_type: Filter by transaction type
            status: Filter by status
            
        Returns:
            List of Transaction objects
        """
        query = db.query(Transaction).filter(Transaction.user_id == user_id)
        
        if transaction_type:
            query = query.filter(Transaction.type == transaction_type)
        
        if status:
            query = query.filter(Transaction.status == status)
        
        transactions = (
            query
            .order_by(Transaction.created_at.desc())
            .limit(limit)
            .offset(offset)
            .all()
        )
        
        return transactions
    
    def get_transaction_by_reference(
        self,
        db: Session,
        reference: str
    ) -> Optional[Transaction]:
        """
        Get transaction by reference
        
        Args:
            db: Database session
            reference: Transaction reference
            
        Returns:
            Transaction object or None
        """
        return db.query(Transaction).filter(Transaction.reference == reference).first()
    
    def update_transaction_status(
        self,
        db: Session,
        transaction_id: int,
        status: TransactionStatus,
        provider_response: Optional[str] = None,
        provider_reference: Optional[str] = None
    ) -> Transaction:
        """
        Update transaction status
        
        Args:
            db: Database session
            transaction_id: Transaction ID
            status: New status
            provider_response: Response from service provider
            provider_reference: Provider's transaction reference
            
        Returns:
            Updated Transaction object
        """
        transaction = db.query(Transaction).filter(Transaction.id == transaction_id).first()
        if not transaction:
            raise ValueError(f"Transaction {transaction_id} not found")
        
        old_status = transaction.status
        transaction.status = status
        
        if provider_response:
            transaction.provider_response = provider_response
        
        if provider_reference:
            transaction.provider_reference = provider_reference
        
        db.commit()
        db.refresh(transaction)
        
        logger.info(
            f"Updated transaction {transaction_id} status: {old_status.value} -> {status.value}"
        )
        
        return transaction
    
    def refund_transaction(
        self,
        db: Session,
        transaction_id: int,
        reason: str
    ) -> Optional[Transaction]:
        """
        Refund a transaction
        
        Args:
            db: Database session
            transaction_id: Transaction ID to refund
            reason: Refund reason
            
        Returns:
            Refund transaction object or None if original not found
        """
        try:
            transaction = db.query(Transaction).filter(Transaction.id == transaction_id).first()
            if not transaction:
                logger.warning(f"Transaction {transaction_id} not found for refund")
                return None
            
            if transaction.status == TransactionStatus.REVERSED:
                logger.warning(f"Transaction {transaction_id} already reversed")
                return None
            
            # Mark as reversed
            transaction.status = TransactionStatus.REVERSED
            transaction.provider_response = f"REFUNDED: {reason}"
            
            # Credit back to wallet
            update_user_balance(db, transaction.user_id, transaction.amount, "add")
            
            db.commit()
            db.refresh(transaction)
            
            logger.info(
                f"Refunded transaction {transaction_id}. Amount: ₦{transaction.amount:,.2f}. "
                f"Reason: {reason}"
            )
            
            return transaction
        
        except Exception as e:
            logger.error(f"Error refunding transaction: {str(e)}")
            db.rollback()
            return None
    
    def get_wallet_summary(
        self,
        db: Session,
        user_id: int
    ) -> Dict[str, Any]:
        """
        Get comprehensive wallet summary
        
        Args:
            db: Database session
            user_id: User ID
            
        Returns:
            Dictionary with wallet summary
        """
        user = get_user_by_id(db, user_id)
        if not user:
            raise ValueError(f"User {user_id} not found")
        
        # Get transaction counts by status
        total_transactions = db.query(Transaction).filter(
            Transaction.user_id == user_id
        ).count()
        
        completed_transactions = db.query(Transaction).filter(
            Transaction.user_id == user_id,
            Transaction.status == TransactionStatus.COMPLETED
        ).count()
        
        pending_transactions = db.query(Transaction).filter(
            Transaction.user_id == user_id,
            Transaction.status == TransactionStatus.PENDING
        ).count()
        
        failed_transactions = db.query(Transaction).filter(
            Transaction.user_id == user_id,
            Transaction.status == TransactionStatus.FAILED
        ).count()
        
        # Calculate total spent (completed transactions only)
        from sqlalchemy import func
        total_spent = db.query(func.sum(Transaction.amount)).filter(
            Transaction.user_id == user_id,
            Transaction.status == TransactionStatus.COMPLETED,
            Transaction.type != TransactionType.WALLET_FUNDING
        ).scalar() or 0.0
        
        # Calculate total funded
        total_funded = db.query(func.sum(Transaction.amount)).filter(
            Transaction.user_id == user_id,
            Transaction.status == TransactionStatus.COMPLETED,
            Transaction.type == TransactionType.WALLET_FUNDING
        ).scalar() or 0.0
        
        return {
            "user_id": user.id,
            "phone_number": user.phone_number,
            "current_balance": user.wallet_balance,
            "current_balance_formatted": format_currency(user.wallet_balance),
            "total_transactions": total_transactions,
            "completed_transactions": completed_transactions,
            "pending_transactions": pending_transactions,
            "failed_transactions": failed_transactions,
            "total_spent": total_spent,
            "total_spent_formatted": format_currency(total_spent),
            "total_funded": total_funded,
            "total_funded_formatted": format_currency(total_funded),
            "virtual_account": user.virtual_account_number,
            "account_status": "Active" if user.is_active else "Inactive"
        }
    
    def check_sufficient_balance(
        self,
        db: Session,
        user_id: int,
        required_amount: float
    ) -> Dict[str, Any]:
        """
        Check if user has sufficient balance
        
        Args:
            db: Database session
            user_id: User ID
            required_amount: Required amount
            
        Returns:
            Dictionary with balance check result
        """
        user = get_user_by_id(db, user_id)
        if not user:
            raise ValueError(f"User {user_id} not found")
        
        has_sufficient = user.wallet_balance >= required_amount
        shortfall = max(0, required_amount - user.wallet_balance)
        
        return {
            "has_sufficient_balance": has_sufficient,
            "current_balance": user.wallet_balance,
            "required_amount": required_amount,
            "shortfall": shortfall,
            "shortfall_formatted": format_currency(shortfall) if shortfall > 0 else None
        }
    
    def get_transaction_by_reference(
        self,
        db: Session,
        reference: str
    ) -> Optional[Transaction]:
        """
        Get transaction by reference number
        
        Args:
            db: Database session
            reference: Transaction reference
            
        Returns:
            Transaction if found, None otherwise
        """
        try:
            transaction = db.query(Transaction).filter(
                Transaction.reference == reference
            ).first()
            
            return transaction
        
        except Exception as e:
            logger.error(f"Error getting transaction by reference: {str(e)}")
            return None


# Singleton instance
wallet_service = WalletService()

