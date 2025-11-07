"""Payrant payment webhook handler"""

from fastapi import APIRouter, Request, HTTPException, Header
from loguru import logger
from typing import Optional

from app.database import SessionLocal
from app.services.payrant import payrant_service
from app.services.wallet import wallet_service
from app.services.whatsapp import whatsapp_service
from app.crud.user import get_user_by_id
from app.models.webhook_log import WebhookLog, WebhookSource
from app.utils.helpers import format_currency
import json

router = APIRouter()


@router.post("/payrant")
async def receive_payrant_webhook(
    request: Request,
    x_payrant_signature: Optional[str] = Header(None)
):
    """
    Receive Payrant payment webhooks
    
    Handles:
    - Virtual account funding
    - Payment confirmations
    - Transaction updates
    """
    try:
        # Get the raw body
        body = await request.json()
        logger.info(f"Received Payrant webhook: {json.dumps(body, indent=2)}")
        
        # Log webhook to database
        db = SessionLocal()
        try:
            webhook_log = WebhookLog(
                source=WebhookSource.PAYMENT,
                method="POST",
                headers=json.dumps(dict(request.headers)),
                payload=json.dumps(body),
                processed=False
            )
            db.add(webhook_log)
            db.commit()
            webhook_log_id = webhook_log.id
        except Exception as e:
            logger.error(f"Failed to log webhook: {e}")
            webhook_log_id = None
        
        # Verify signature (if enabled)
        if x_payrant_signature:
            is_valid = payrant_service.verify_webhook_signature(body, x_payrant_signature)
            if not is_valid:
                logger.warning("Invalid webhook signature")
                # In production, you might want to reject invalid signatures
                # raise HTTPException(status_code=403, detail="Invalid signature")
        
        # Process webhook based on event type
        event_type = body.get("event", body.get("type", "unknown"))
        
        if event_type in ["payment.success", "transaction.success", "credit"]:
            await handle_successful_payment(db, body)
        
        elif event_type in ["payment.failed", "transaction.failed"]:
            await handle_failed_payment(db, body)
        
        else:
            logger.info(f"Unhandled webhook event type: {event_type}")
        
        # Mark webhook as processed
        if webhook_log_id:
            try:
                webhook_log = db.query(WebhookLog).filter(WebhookLog.id == webhook_log_id).first()
                if webhook_log:
                    webhook_log.processed = True
                    db.commit()
            except Exception as e:
                logger.error(f"Failed to update webhook log: {e}")
        
        db.close()
        
        return {"status": "received", "message": "Webhook processed successfully"}
    
    except Exception as e:
        logger.error(f"Error processing Payrant webhook: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


async def handle_successful_payment(db: SessionLocal, payload: dict):
    """
    Handle successful payment webhook
    
    Args:
        db: Database session
        payload: Webhook payload
    """
    try:
        # Extract payment details
        amount = float(payload.get("amount", 0))
        reference = payload.get("reference", payload.get("transaction_reference"))
        account_reference = payload.get("account_reference")
        customer_name = payload.get("customer_name")
        narration = payload.get("narration", "Wallet Funding")
        
        if amount <= 0:
            logger.warning("Invalid payment amount in webhook")
            return
        
        # Find user by account reference
        # Format: FORBILL-{user_id}-{last4}
        if account_reference and account_reference.startswith("FORBILL-"):
            parts = account_reference.split("-")
            if len(parts) >= 2:
                user_id = int(parts[1])
                
                user = get_user_by_id(db, user_id)
                if not user:
                    logger.error(f"User {user_id} not found for payment")
                    return
                
                # Check for duplicate transaction (idempotency)
                existing = wallet_service.get_transaction_by_reference(db, reference)
                if existing:
                    logger.info(f"Transaction {reference} already processed")
                    return
                
                # Credit wallet
                transaction = wallet_service.credit_wallet(
                    db=db,
                    user_id=user_id,
                    amount=amount,
                    description=f"Wallet Funding - {narration}",
                    reference=reference,
                    metadata=payload
                )
                
                logger.info(
                    f"Wallet credited: User {user_id}, Amount: ₦{amount:,.2f}, "
                    f"Ref: {reference}"
                )
                
                # Send WhatsApp notification
                try:
                    notification_msg = (
                        f"✅ *Payment Received!*\n\n"
                        f"Amount: *{format_currency(amount)}*\n"
                        f"New Balance: *{format_currency(user.wallet_balance)}*\n"
                        f"Reference: {reference}\n\n"
                        f"Your wallet has been funded successfully!\n"
                        f"Type *help* to see what you can do."
                    )
                    
                    await whatsapp_service.send_text_message(
                        to=user.phone_number,
                        message=notification_msg
                    )
                except Exception as e:
                    logger.error(f"Failed to send WhatsApp notification: {e}")
                
    except Exception as e:
        logger.error(f"Error handling successful payment: {str(e)}")


async def handle_failed_payment(db: SessionLocal, payload: dict):
    """
    Handle failed payment webhook
    
    Args:
        db: Database session
        payload: Webhook payload
    """
    try:
        reference = payload.get("reference", payload.get("transaction_reference"))
        reason = payload.get("reason", payload.get("message", "Unknown error"))
        
        logger.warning(f"Payment failed: Ref {reference}, Reason: {reason}")
        
        # Update transaction if exists
        transaction = wallet_service.get_transaction_by_reference(db, reference)
        if transaction:
            from app.models.transaction import TransactionStatus
            wallet_service.update_transaction_status(
                db=db,
                transaction_id=transaction.id,
                status=TransactionStatus.FAILED,
                provider_response=reason
            )
        
    except Exception as e:
        logger.error(f"Error handling failed payment: {str(e)}")
