"""WhatsApp webhook endpoint"""

from fastapi import APIRouter, Request, HTTPException, Query
from fastapi.responses import PlainTextResponse
from loguru import logger
from app.config import settings
from app.services.whatsapp import whatsapp_service
from app.models.webhook_log import WebhookLog, WebhookSource
from app.database import SessionLocal
import json

router = APIRouter()


@router.get("/whatsapp")
async def verify_webhook(
    request: Request,
    mode: str = Query(alias="hub.mode"),
    token: str = Query(alias="hub.verify_token"),
    challenge: str = Query(alias="hub.challenge")
):
    """
    Webhook verification endpoint for Meta WhatsApp
    Meta will send a GET request with verification parameters
    """
    logger.info(f"Webhook verification request: mode={mode}, token={token}")
    
    # Verify the token matches our configured token
    if mode == "subscribe" and token == settings.WHATSAPP_VERIFY_TOKEN:
        logger.info("Webhook verified successfully!")
        return PlainTextResponse(content=challenge, status_code=200)
    else:
        logger.warning(f"Webhook verification failed! Token mismatch.")
        raise HTTPException(status_code=403, detail="Verification failed")


@router.post("/whatsapp")
async def receive_webhook(request: Request):
    """
    Receive incoming WhatsApp messages and events
    """
    try:
        # Get the raw body
        body = await request.json()
        logger.info(f"Received webhook: {json.dumps(body, indent=2)}")
        
        # Log webhook to database
        db = SessionLocal()
        try:
            webhook_log = WebhookLog(
                source=WebhookSource.WHATSAPP,
                method="POST",
                headers=json.dumps(dict(request.headers)),
                payload=json.dumps(body),
                processed=False
            )
            db.add(webhook_log)
            db.commit()
        except Exception as e:
            logger.error(f"Failed to log webhook: {e}")
        finally:
            db.close()
        
        # Process the webhook
        if body.get("object") == "whatsapp_business_account":
            entries = body.get("entry", [])
            
            for entry in entries:
                changes = entry.get("changes", [])
                
                for change in changes:
                    value = change.get("value", {})
                    
                    # Check if there are messages
                    if "messages" in value:
                        messages = value.get("messages", [])
                        
                        for message in messages:
                            await process_incoming_message(message, value)
                    
                    # Check for status updates
                    if "statuses" in value:
                        statuses = value.get("statuses", [])
                        for status in statuses:
                            logger.info(f"Message status update: {status}")
        
        return {"status": "received"}
    
    except Exception as e:
        logger.error(f"Error processing webhook: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


async def process_incoming_message(message: dict, value: dict):
    """
    Process an incoming WhatsApp message
    
    Args:
        message: Message object from webhook
        value: Value object containing metadata
    """
    try:
        message_id = message.get("id")
        from_number = message.get("from")
        timestamp = message.get("timestamp")
        message_type = message.get("type")
        
        logger.info(f"Processing message from {from_number}: type={message_type}")
        
        # Mark message as read
        try:
            await whatsapp_service.mark_message_as_read(message_id)
        except Exception as e:
            logger.warning(f"Failed to mark message as read: {e}")
        
        # Handle different message types
        if message_type == "text":
            text_body = message.get("text", {}).get("body", "")
            logger.info(f"Text message: {text_body}")
            
            # Send a simple response (we'll implement command parsing later)
            await handle_text_message(from_number, text_body)
        
        elif message_type == "interactive":
            interactive = message.get("interactive", {})
            interactive_type = interactive.get("type")
            
            if interactive_type == "button_reply":
                button_id = interactive.get("button_reply", {}).get("id")
                button_title = interactive.get("button_reply", {}).get("title")
                logger.info(f"Button clicked: {button_id} - {button_title}")
                await handle_button_click(from_number, button_id, button_title)
            
            elif interactive_type == "list_reply":
                list_id = interactive.get("list_reply", {}).get("id")
                list_title = interactive.get("list_reply", {}).get("title")
                logger.info(f"List item selected: {list_id} - {list_title}")
                await handle_list_selection(from_number, list_id, list_title)
        
        else:
            logger.info(f"Unsupported message type: {message_type}")
            await whatsapp_service.send_text_message(
                to=from_number,
                message="Sorry, I can only process text messages at the moment."
            )
    
    except Exception as e:
        logger.error(f"Error processing message: {str(e)}")


async def handle_text_message(from_number: str, text: str):
    """
    Handle incoming text message
    
    Args:
        from_number: Sender's phone number
        text: Message text
    """
    text_lower = text.lower().strip()
    
    # Simple greeting response
    if text_lower in ["hi", "hello", "hey", "start"]:
        welcome_message = (
            "👋 *Welcome to ForBill!*\n\n"
            "I'm your virtual assistant for bill payments and airtime purchases.\n\n"
            "*Quick Menu:*\n"
            "1️⃣ Buy Airtime\n"
            "2️⃣ Buy Data\n"
            "3️⃣ Pay Bills\n"
            "4️⃣ Check Balance\n"
            "5️⃣ Transaction History\n\n"
            "Reply with a number or type 'help' for more options."
        )
        await whatsapp_service.send_text_message(
            to=from_number,
            message=welcome_message
        )
    
    elif text_lower == "help":
        help_message = (
            "📱 *ForBill - Available Commands*\n\n"
            "*Services:*\n"
            "• Airtime Purchase\n"
            "• Data Bundles\n"
            "• Electricity Bills\n"
            "• Cable TV Subscriptions\n"
            "• Wallet Management\n\n"
            "*How to use:*\n"
            "Just reply with the number from the menu or describe what you need!\n\n"
            "Example: 'Buy 1000 airtime' or 'Check my balance'"
        )
        await whatsapp_service.send_text_message(
            to=from_number,
            message=help_message
        )
    
    else:
        # Default response for now
        await whatsapp_service.send_text_message(
            to=from_number,
            message=f"You said: {text}\n\nI'm still learning! Type 'help' to see what I can do."
        )


async def handle_button_click(from_number: str, button_id: str, button_title: str):
    """Handle interactive button clicks"""
    await whatsapp_service.send_text_message(
        to=from_number,
        message=f"You clicked: {button_title}"
    )


async def handle_list_selection(from_number: str, list_id: str, list_title: str):
    """Handle interactive list selections"""
    await whatsapp_service.send_text_message(
        to=from_number,
        message=f"You selected: {list_title}"
    )
