"""WhatsApp webhook endpoint"""

from fastapi import APIRouter, Request, HTTPException, Query
from fastapi.responses import PlainTextResponse
from loguru import logger
from app.config import settings
from app.services.whatsapp import whatsapp_service
from app.services.commands import parse_command, CommandType
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
    Handle incoming text message with command parsing
    
    Args:
        from_number: Sender's phone number
        text: Message text
    """
    # Parse the command
    parsed = parse_command(text)
    command_type = parsed["command_type"]
    
    logger.info(f"Command from {from_number}: {command_type.value} - {parsed}")
    
    # Route to appropriate handler
    if command_type == CommandType.GREETING:
        await handle_greeting(from_number)
    
    elif command_type == CommandType.HELP:
        await handle_help(from_number)
    
    elif command_type == CommandType.BALANCE:
        await handle_balance_check(from_number)
    
    elif command_type == CommandType.AIRTIME:
        await handle_airtime_purchase(from_number, parsed)
    
    elif command_type == CommandType.DATA:
        await handle_data_purchase(from_number, parsed)
    
    elif command_type == CommandType.ELECTRICITY:
        await handle_electricity_payment(from_number, parsed)
    
    elif command_type == CommandType.CABLE_TV:
        await handle_cable_subscription(from_number, parsed)
    
    elif command_type == CommandType.HISTORY:
        await handle_transaction_history(from_number)
    
    elif command_type == CommandType.REFERRAL:
        await handle_referral_info(from_number)
    
    else:
        await handle_unknown_command(from_number, text)


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


# ============================================================================
# COMMAND HANDLERS
# ============================================================================

async def handle_greeting(from_number: str):
    """Send welcome message"""
    welcome_message = (
        "👋 *Welcome to ForBill!*\n\n"
        "I'm your virtual assistant for bill payments and airtime purchases.\n\n"
        "*Quick Commands:*\n"
        "• Buy 1000 airtime\n"
        "• Buy data\n"
        "• Check balance\n"
        "• History\n"
        "• Help\n\n"
        "Just type what you need, and I'll help you!"
    )
    await whatsapp_service.send_text_message(
        to=from_number,
        message=welcome_message
    )


async def handle_help(from_number: str):
    """Send help menu"""
    help_message = (
        "📱 *ForBill - Command Guide*\n\n"
        "*💳 Airtime:*\n"
        "• Buy 1000 airtime\n"
        "• Recharge 500\n"
        "• Top up 2000\n\n"
        "*📶 Data:*\n"
        "• Buy data\n"
        "• Buy 1GB MTN\n"
        "• 2GB Airtel\n\n"
        "*💡 Electricity:*\n"
        "• Buy electricity\n"
        "• Pay 5000 light\n\n"
        "*📺 Cable TV:*\n"
        "• Pay DSTV\n"
        "• Subscribe GOTV\n\n"
        "*💰 Wallet:*\n"
        "• Balance\n"
        "• History\n"
        "• Referral\n\n"
        "Type your command to get started!"
    )
    await whatsapp_service.send_text_message(
        to=from_number,
        message=help_message
    )


async def handle_balance_check(from_number: str):
    """Check wallet balance (placeholder - will implement with user service)"""
    # TODO: Implement actual balance check from database
    await whatsapp_service.send_text_message(
        to=from_number,
        message=(
            "💰 *Your Wallet*\n\n"
            "Balance: ₦0.00\n\n"
            "_To fund your wallet, I'll send you a virtual account number soon!_\n\n"
            "Type 'help' for available services."
        )
    )


async def handle_airtime_purchase(from_number: str, parsed: dict):
    """Handle airtime purchase request"""
    amount = parsed.get("amount")
    phone = parsed.get("phone_number", from_number)
    
    if not amount:
        # Ask for amount
        await whatsapp_service.send_text_message(
            to=from_number,
            message=(
                "📱 *Airtime Purchase*\n\n"
                "How much airtime would you like to buy?\n\n"
                "Example: 'Buy 1000 airtime'\n\n"
                "Min: ₦50 | Max: ₦50,000"
            )
        )
        return
    
    # Check for errors
    if "error" in parsed:
        await whatsapp_service.send_text_message(
            to=from_number,
            message=f"❌ {parsed['error']}"
        )
        return
    
    # Confirm purchase
    confirmation_msg = (
        f"📱 *Confirm Airtime Purchase*\n\n"
        f"Amount: ₦{amount:,}\n"
        f"Phone: {phone}\n\n"
        f"_Coming soon! We're still setting up payment processing._\n\n"
        f"Type 'help' for other available commands."
    )
    await whatsapp_service.send_text_message(
        to=from_number,
        message=confirmation_msg
    )


async def handle_data_purchase(from_number: str, parsed: dict):
    """Handle data bundle purchase request"""
    network = parsed.get("network")
    data_size = parsed.get("data_size_display")
    
    if not network or not data_size:
        # Show data options
        await whatsapp_service.send_text_message(
            to=from_number,
            message=(
                "📶 *Data Bundles*\n\n"
                "Which network and plan would you like?\n\n"
                "*Examples:*\n"
                "• Buy 1GB MTN\n"
                "• 2GB Airtel\n"
                "• 500MB Glo\n\n"
                "*Networks:* MTN, Airtel, Glo, 9mobile"
            )
        )
        return
    
    # Show confirmation
    confirmation_msg = (
        f"📶 *Confirm Data Purchase*\n\n"
        f"Network: {network.upper()}\n"
        f"Data: {data_size}\n"
        f"Phone: {parsed.get('phone_number', from_number)}\n\n"
        f"_Coming soon! We're still setting up the data service._\n\n"
        f"Type 'help' for other commands."
    )
    await whatsapp_service.send_text_message(
        to=from_number,
        message=confirmation_msg
    )


async def handle_electricity_payment(from_number: str, parsed: dict):
    """Handle electricity bill payment request"""
    amount = parsed.get("amount")
    
    if not amount:
        await whatsapp_service.send_text_message(
            to=from_number,
            message=(
                "💡 *Electricity Payment*\n\n"
                "How much would you like to pay?\n\n"
                "Example: 'Buy 5000 electricity'\n\n"
                "Min: ₦100"
            )
        )
        return
    
    await whatsapp_service.send_text_message(
        to=from_number,
        message=(
            f"💡 *Electricity Payment*\n\n"
            f"Amount: ₦{amount:,}\n\n"
            f"_Coming soon! We're setting up electricity payments._\n\n"
            f"Type 'help' for available commands."
        )
    )


async def handle_cable_subscription(from_number: str, parsed: dict):
    """Handle cable TV subscription request"""
    provider = parsed.get("provider", "Cable TV")
    
    await whatsapp_service.send_text_message(
        to=from_number,
        message=(
            f"📺 *{provider.upper()} Subscription*\n\n"
            f"_Coming soon! We're setting up cable TV payments._\n\n"
            f"Supported: DSTV, GOTV, Startimes\n\n"
            f"Type 'help' for available commands."
        )
    )


async def handle_transaction_history(from_number: str):
    """Show transaction history (placeholder)"""
    # TODO: Implement actual transaction history from database
    await whatsapp_service.send_text_message(
        to=from_number,
        message=(
            "📊 *Transaction History*\n\n"
            "You have no transactions yet.\n\n"
            "Start by buying airtime or data!\n\n"
            "Type 'help' to see available services."
        )
    )


async def handle_referral_info(from_number: str):
    """Show referral information (placeholder)"""
    # TODO: Implement actual referral info from database
    await whatsapp_service.send_text_message(
        to=from_number,
        message=(
            "🎁 *Referral Program*\n\n"
            "Your Referral Code: _Coming soon!_\n\n"
            "Earn 5% commission on every transaction your referrals make!\n\n"
            "Share ForBill with friends and start earning.\n\n"
            "Type 'help' for other commands."
        )
    )


async def handle_unknown_command(from_number: str, text: str):
    """Handle unknown commands"""
    await whatsapp_service.send_text_message(
        to=from_number,
        message=(
            f"🤔 I didn't understand: _{text}_\n\n"
            f"*Try these commands:*\n"
            f"• Buy 1000 airtime\n"
            f"• Buy data\n"
            f"• Balance\n"
            f"• History\n"
            f"• Help\n\n"
            f"Type 'help' for the full menu."
        )
    )

