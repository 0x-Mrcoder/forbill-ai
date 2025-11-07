"""
WhatsApp Webhook Endpoints
Handles webhook verification and incoming messages from Meta WhatsApp Cloud API
"""
from fastapi import APIRouter, Request, HTTPException, Query
from typing import Dict, Any
from loguru import logger
import hmac
import hashlib

from app.config import settings
from app.models.webhook_log import WebhookLog, WebhookSource
from app.database import SessionLocal
from app.services.whatsapp import whatsapp_service

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


@router.get("/whatsapp")
async def verify_whatsapp_webhook(
    request: Request,
    hub_mode: str = Query(None, alias="hub.mode"),
    hub_verify_token: str = Query(None, alias="hub.verify_token"),
    hub_challenge: str = Query(None, alias="hub.challenge")
) -> Any:
    """
    WhatsApp webhook verification endpoint (GET)
    
    Meta will call this endpoint with verification parameters
    to verify the webhook URL during setup
    """
    logger.info(f"Webhook verification request - mode: {hub_mode}, token: {hub_verify_token}")
    
    # Verify that the mode is 'subscribe' and token matches
    if hub_mode == "subscribe" and hub_verify_token == settings.WHATSAPP_VERIFY_TOKEN:
        logger.info("Webhook verification successful")
        # Return the challenge to verify the webhook
        return int(hub_challenge)
    else:
        logger.warning(f"Webhook verification failed - Invalid token or mode")
        raise HTTPException(status_code=403, detail="Verification failed")


@router.post("/whatsapp")
async def receive_whatsapp_webhook(request: Request) -> Dict[str, str]:
    """
    WhatsApp webhook endpoint (POST)
    
    Receives incoming messages and status updates from WhatsApp
    """
    try:
        # Get raw body for signature verification
        body = await request.body()
        payload = await request.json()
        
        # Log webhook payload
        logger.info(f"Received WhatsApp webhook: {payload}")
        
        # Store webhook in database for debugging
        db = SessionLocal()
        try:
            webhook_log = WebhookLog(
                source=WebhookSource.WHATSAPP,
                payload=payload,
                status="received"
            )
            db.add(webhook_log)
            db.commit()
        except Exception as e:
            logger.error(f"Error logging webhook: {str(e)}")
            db.rollback()
        finally:
            db.close()
        
        # Verify signature (optional but recommended for production)
        # signature = request.headers.get("X-Hub-Signature-256", "")
        # if not verify_webhook_signature(body, signature):
        #     raise HTTPException(status_code=401, detail="Invalid signature")
        
        # Process the webhook
        await process_whatsapp_webhook(payload)
        
        # Must return 200 OK quickly to avoid timeout
        return {"status": "ok"}
        
    except Exception as e:
        logger.error(f"Error processing WhatsApp webhook: {str(e)}")
        # Still return 200 to avoid retries from Meta
        return {"status": "error", "message": str(e)}


async def process_whatsapp_webhook(payload: Dict[str, Any]) -> None:
    """
    Process incoming WhatsApp webhook events
    
    Handles:
    - Incoming messages
    - Message status updates (sent, delivered, read)
    - User profile updates
    """
    try:
        # Extract entry data
        entry = payload.get("entry", [])
        if not entry:
            logger.warning("No entry data in webhook payload")
            return
        
        for item in entry:
            changes = item.get("changes", [])
            
            for change in changes:
                value = change.get("value", {})
                
                # Handle incoming messages
                if "messages" in value:
                    messages = value.get("messages", [])
                    
                    for message in messages:
                        await handle_incoming_message(message, value)
                
                # Handle message status updates
                if "statuses" in value:
                    statuses = value.get("statuses", [])
                    
                    for status in statuses:
                        await handle_message_status(status)
    
    except Exception as e:
        logger.error(f"Error in process_whatsapp_webhook: {str(e)}")
        raise


async def handle_incoming_message(message: Dict[str, Any], value: Dict[str, Any]) -> None:
    """
    Handle incoming message from user
    
    Extracts message details and routes to appropriate handler
    """
    try:
        message_id = message.get("id")
        from_number = message.get("from")
        timestamp = message.get("timestamp")
        message_type = message.get("type")
        
        # Get contact name if available
        contacts = value.get("contacts", [])
        contact_name = contacts[0].get("profile", {}).get("name", "") if contacts else ""
        
        logger.info(f"Incoming message from {from_number} ({contact_name}): type={message_type}")
        
        # Mark message as read
        await whatsapp_service.mark_message_as_read(message_id)
        
        # Extract message content based on type
        message_content = ""
        
        if message_type == "text":
            message_content = message.get("text", {}).get("body", "")
        
        elif message_type == "button":
            # User clicked an interactive button
            message_content = message.get("button", {}).get("text", "")
        
        elif message_type == "interactive":
            # User selected from a list or clicked a button
            interactive = message.get("interactive", {})
            if interactive.get("type") == "button_reply":
                message_content = interactive.get("button_reply", {}).get("title", "")
            elif interactive.get("type") == "list_reply":
                message_content = interactive.get("list_reply", {}).get("title", "")
        
        else:
            logger.info(f"Unsupported message type: {message_type}")
            await whatsapp_service.send_text_message(
                to=from_number,
                message="Sorry, I can only process text messages at the moment. Please send a text command."
            )
            return
        
        logger.info(f"Message content: {message_content}")
        
        # TODO: Route to command parser and conversation handler
        # For now, send a test response
        await whatsapp_service.send_text_message(
            to=from_number,
            message=f"Hello {contact_name}! I received your message: '{message_content}'\n\nI'm ForBill, your bill payment assistant. Command parser coming soon!"
        )
        
    except Exception as e:
        logger.error(f"Error handling incoming message: {str(e)}")
        raise


async def handle_message_status(status: Dict[str, Any]) -> None:
    """
    Handle message status updates (sent, delivered, read, failed)
    """
    try:
        message_id = status.get("id")
        status_type = status.get("status")
        timestamp = status.get("timestamp")
        recipient = status.get("recipient_id")
        
        logger.debug(f"Message {message_id} status: {status_type} (to: {recipient})")
        
        # TODO: Update message status in database if needed
        # This is useful for tracking message delivery
        
    except Exception as e:
        logger.error(f"Error handling message status: {str(e)}")


def verify_webhook_signature(payload: bytes, signature: str) -> bool:
    """
    Verify webhook signature from Meta
    
    Args:
        payload: Raw request body
        signature: X-Hub-Signature-256 header value
        
    Returns:
        True if signature is valid
    """
    try:
        # Remove 'sha256=' prefix from signature
        if signature.startswith("sha256="):
            signature = signature[7:]
        
        # Calculate expected signature
        app_secret = settings.WHATSAPP_APP_SECRET
        expected_signature = hmac.new(
            app_secret.encode(),
            payload,
            hashlib.sha256
        ).hexdigest()
        
        # Compare signatures
        return hmac.compare_digest(expected_signature, signature)
        
    except Exception as e:
        logger.error(f"Error verifying webhook signature: {str(e)}")
        return False
