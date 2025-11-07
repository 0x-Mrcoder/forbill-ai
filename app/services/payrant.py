"""Payrant payment gateway integration"""

import httpx
from typing import Dict, Any, Optional
from loguru import logger

from app.config import settings
from app.models.user import User


class PayrantService:
    """Service for Payrant virtual account and payment operations"""
    
    def __init__(self):
        self.base_url = settings.PAYRANT_BASE_URL
        self.api_key = settings.PAYRANT_API_KEY
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    async def create_virtual_account(
        self,
        user: User,
        account_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a virtual account for user
        
        Args:
            user: User object
            account_name: Custom account name (optional)
            
        Returns:
            Dictionary with virtual account details
        """
        # Use user's name or phone as account name
        if not account_name:
            account_name = user.name if user.name else f"ForBill-{user.phone_number[-4:]}"
        
        payload = {
            "account_reference": f"FORBILL-{user.id}-{user.phone_number[-4:]}",
            "account_name": account_name,
            "customer_name": user.name or user.phone_number,
            "customer_phone": user.phone_number,
            "customer_email": user.email,
            "bvn": user.nin if hasattr(user, 'nin') else None,  # Optional
            "webhook_url": f"{settings.BASE_URL}/webhooks/payrant"
        }
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.base_url}/virtual-accounts",
                    headers=self.headers,
                    json=payload
                )
                response.raise_for_status()
                
                result = response.json()
                logger.info(f"Virtual account created for user {user.id}: {result}")
                
                return {
                    "success": True,
                    "account_number": result.get("account_number"),
                    "account_name": result.get("account_name"),
                    "bank_name": result.get("bank_name", "Payrant Bank"),
                    "account_reference": result.get("account_reference"),
                    "data": result
                }
                
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error creating virtual account: {e.response.text}")
            return {
                "success": False,
                "error": e.response.text,
                "status_code": e.response.status_code
            }
        except Exception as e:
            logger.error(f"Error creating virtual account: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_virtual_account(self, account_reference: str) -> Dict[str, Any]:
        """
        Get virtual account details
        
        Args:
            account_reference: Account reference
            
        Returns:
            Dictionary with account details
        """
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{self.base_url}/virtual-accounts/{account_reference}",
                    headers=self.headers
                )
                response.raise_for_status()
                
                result = response.json()
                return {
                    "success": True,
                    "data": result
                }
                
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error fetching virtual account: {e.response.text}")
            return {
                "success": False,
                "error": e.response.text,
                "status_code": e.response.status_code
            }
        except Exception as e:
            logger.error(f"Error fetching virtual account: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_transaction_status(self, transaction_reference: str) -> Dict[str, Any]:
        """
        Check payment transaction status
        
        Args:
            transaction_reference: Transaction reference
            
        Returns:
            Dictionary with transaction status
        """
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{self.base_url}/transactions/{transaction_reference}",
                    headers=self.headers
                )
                response.raise_for_status()
                
                result = response.json()
                return {
                    "success": True,
                    "status": result.get("status"),
                    "amount": result.get("amount"),
                    "data": result
                }
                
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error checking transaction: {e.response.text}")
            return {
                "success": False,
                "error": e.response.text,
                "status_code": e.response.status_code
            }
        except Exception as e:
            logger.error(f"Error checking transaction: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def verify_webhook_signature(
        self,
        payload: Dict[str, Any],
        signature: str
    ) -> bool:
        """
        Verify Payrant webhook signature
        
        Args:
            payload: Webhook payload
            signature: Signature from header
            
        Returns:
            True if valid, False otherwise
        """
        # TODO: Implement actual signature verification
        # This depends on Payrant's webhook signature method
        # Usually involves HMAC-SHA256 with secret key
        
        import hashlib
        import hmac
        import json
        
        try:
            # Convert payload to canonical string
            payload_string = json.dumps(payload, sort_keys=True, separators=(',', ':'))
            
            # Calculate expected signature
            expected_signature = hmac.new(
                self.api_key.encode(),
                payload_string.encode(),
                hashlib.sha256
            ).hexdigest()
            
            # Compare signatures
            return hmac.compare_digest(expected_signature, signature)
            
        except Exception as e:
            logger.error(f"Error verifying webhook signature: {e}")
            return False
    
    async def get_account_balance(self) -> Dict[str, Any]:
        """
        Get Payrant account balance
        
        Returns:
            Dictionary with balance info
        """
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{self.base_url}/balance",
                    headers=self.headers
                )
                response.raise_for_status()
                
                result = response.json()
                return {
                    "success": True,
                    "balance": result.get("balance"),
                    "data": result
                }
                
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error fetching balance: {e.response.text}")
            return {
                "success": False,
                "error": e.response.text
            }
        except Exception as e:
            logger.error(f"Error fetching balance: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }


# Singleton instance
payrant_service = PayrantService()
