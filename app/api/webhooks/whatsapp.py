"""WhatsApp webhook endpoint"""

from fastapi import APIRouter, Request, HTTPException, Query
from fastapi.responses import PlainTextResponse
from loguru import logger
from app.config import settings
from app.services.whatsapp import whatsapp_service
from app.services.commands import parse_command, CommandType
from app.services.payrant import payrant_service
from app.services.wallet import wallet_service
from app.services.topupmate import topupmate_service
from app.models.webhook_log import WebhookLog, WebhookSource
from app.models.user import User
from app.models.transaction import TransactionType, TransactionStatus
from app.database import SessionLocal
from app.crud.user import get_or_create_user, get_user_by_phone, get_user_transactions
from app.utils.helpers import format_currency
import json
import asyncio

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
    Process an incoming WhatsApp message with user registration
    
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
        
        # Get or create user (auto-registration)
        db = SessionLocal()
        try:
            user, is_new = get_or_create_user(db, from_number)
            
            if is_new:
                logger.info(f"🎉 New user registered: {from_number} (ID: {user.id})")
                # Send welcome message for new users
                await send_welcome_message(from_number, user)
        except Exception as e:
            logger.error(f"Error with user registration: {e}")
            user = None
        finally:
            db.close()
        
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


async def send_welcome_message(from_number: str, user):
    """Send welcome message to new users"""
    welcome_message = (
        f"🎉 *Welcome to ForBill, {user.name or 'Friend'}!*\n\n"
        f"Your account has been created successfully!\n\n"
        f"*Your Details:*\n"
        f"📱 Phone: {user.phone_number}\n"
        f"💰 Wallet: {format_currency(user.wallet_balance)}\n"
        f"🎁 Referral Code: `{user.referral_code}`\n\n"
        f"*What you can do:*\n"
        f"• Buy Airtime & Data\n"
        f"• Pay Electricity Bills\n"
        f"• Subscribe to Cable TV\n"
        f"• Earn referral bonuses\n\n"
        f"Type *help* to see all commands!"
    )
    await whatsapp_service.send_text_message(
        to=from_number,
        message=welcome_message
    )
    
    # Create virtual account in background
    asyncio.create_task(create_virtual_account_for_user(user))


async def create_virtual_account_for_user(user):
    """Create virtual account for user (background task)"""
    try:
        db = SessionLocal()
        try:
            # Check if already has account
            if user.virtual_account_number:
                logger.info(f"User {user.id} already has virtual account")
                return
            
            # Create account reference
            account_reference = f"FORBILL-{user.id}-{user.phone_number[-4:]}"
            
            # Create virtual account
            result = await payrant_service.create_virtual_account(
                customer_name=user.name or user.phone_number,
                customer_email=f"{user.phone_number}@forbill.app",
                customer_phone=user.phone_number,
                account_reference=account_reference
            )
            
            if result:
                # Update user with account details
                user.virtual_account_number = result.get("account_number")
                user.virtual_account_name = result.get("account_name")
                user.virtual_account_bank = result.get("bank_name", "Payrant")
                db.commit()
                
                logger.info(f"Virtual account created for user {user.id}")
                
                # Send account details
                account_msg = (
                    f"🏦 *Your Virtual Account*\n\n"
                    f"Bank: {user.virtual_account_bank}\n"
                    f"Account Number: *{user.virtual_account_number}*\n"
                    f"Account Name: {user.virtual_account_name}\n\n"
                    f"💡 Transfer any amount to fund your wallet!\n"
                    f"Your account will be credited instantly."
                )
                
                await whatsapp_service.send_text_message(
                    to=user.phone_number,
                    message=account_msg
                )
        finally:
            db.close()
    except Exception as e:
        logger.error(f"Error creating virtual account: {e}")


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
    """Check wallet balance with real user data"""
    db = SessionLocal()
    try:
        user = get_user_by_phone(db, from_number)
        
        if not user:
            await whatsapp_service.send_text_message(
                to=from_number,
                message="❌ User not found. Please send 'hi' to register."
            )
            return
        
        # Include virtual account details if available
        funding_info = ""
        if user.virtual_account_number and user.virtual_account_name:
            funding_info = (
                f"*Virtual Account*\n"
                f"Bank: {user.virtual_account_bank or 'Payrant'}\n"
                f"Account: {user.virtual_account_number}\n"
                f"Name: {user.virtual_account_name}\n\n"
                f"Transfer any amount to fund your wallet!\n\n"
            )
        else:
            funding_info = "💡 Setting up your virtual account...\n\n"
        
        balance_msg = (
            f"💰 *Your Wallet*\n\n"
            f"Balance: *{format_currency(user.wallet_balance)}*\n"
            f"Account Status: {'✅ Active' if user.is_active else '❌ Inactive'}\n\n"
            f"{funding_info}"
            f"🎁 *Referral Code:* `{user.referral_code}`\n"
            f"Share and earn 5% on every transaction!\n\n"
            f"Type *help* for available services."
        )
        
        await whatsapp_service.send_text_message(
            to=from_number,
            message=balance_msg
        )
    except Exception as e:
        logger.error(f"Error checking balance: {e}")
        await whatsapp_service.send_text_message(
            to=from_number,
            message="❌ Error checking balance. Please try again."
        )
    finally:
        db.close()


async def handle_airtime_purchase(from_number: str, parsed: dict):
    """Handle airtime purchase request"""
    db = SessionLocal()
    try:
        # Get user
        user = get_user_by_phone(db, from_number)
        if not user:
            await whatsapp_service.send_text_message(
                to=from_number,
                message="❌ Please send 'hi' to register first."
            )
            return
        
        amount = parsed.get("amount")
        phone = parsed.get("phone_number", from_number)
        network = parsed.get("network")
        
        if not amount:
            await whatsapp_service.send_text_message(
                to=from_number,
                message=(
                    "📱 *Airtime Purchase*\n\n"
                    "How much airtime would you like to buy?\n\n"
                    "Example: 'Buy 1000 airtime for 08012345678'\n\n"
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
        
        # Detect network from phone number if not specified
        if not network:
            phone_prefix = phone[3:6] if phone.startswith("234") else phone[:4]
            network_map = {
                "0803": "MTN", "0806": "MTN", "0810": "MTN", "0813": "MTN", "0814": "MTN",
                "0816": "MTN", "0903": "MTN", "0906": "MTN", "0913": "MTN", "0916": "MTN",
                "0805": "GLO", "0807": "GLO", "0811": "GLO", "0815": "GLO", "0905": "GLO",
                "0802": "AIRTEL", "0808": "AIRTEL", "0812": "AIRTEL", "0902": "AIRTEL", "0907": "AIRTEL",
                "0809": "9MOBILE", "0817": "9MOBILE", "0818": "9MOBILE", "0909": "9MOBILE"
            }
            network = network_map.get(phone_prefix, "MTN")  # Default to MTN
        
        # Check wallet balance
        balance_check = wallet_service.check_sufficient_balance(db, user.id, amount)
        if not balance_check["has_sufficient_balance"]:
            await whatsapp_service.send_text_message(
                to=from_number,
                message=(
                    f"❌ *Insufficient Balance*\n\n"
                    f"Required: {format_currency(amount)}\n"
                    f"Available: {format_currency(balance_check['current_balance'])}\n"
                    f"Shortfall: {balance_check['shortfall_formatted']}\n\n"
                    f"💡 Type *balance* to fund your wallet"
                )
            )
            return
        
        # Send processing message
        await whatsapp_service.send_text_message(
            to=from_number,
            message=(
                f"⏳ *Processing Airtime Purchase...*\n\n"
                f"Amount: {format_currency(amount)}\n"
                f"Phone: {phone}\n"
                f"Network: {network}\n\n"
                f"Please wait..."
            )
        )
        
        # Debit wallet
        transaction = wallet_service.debit_wallet(
            db=db,
            user_id=user.id,
            amount=amount,
            description=f"Airtime purchase - {phone}",
            transaction_type=TransactionType.AIRTIME
        )
        
        # Store transaction details
        transaction.recipient_phone = phone
        transaction.network = network
        transaction.service_provider = "TopUpMate"
        db.commit()
        
        # Purchase airtime from TopUpMate
        result = await topupmate_service.buy_airtime(
            phone_number=phone,
            amount=amount,
            network=network
        )
        
        if result.get("success"):
            # Update transaction status
            wallet_service.update_transaction_status(
                db=db,
                transaction_id=transaction.id,
                status=TransactionStatus.COMPLETED,
                provider_response=str(result),
                provider_reference=result.get("provider_reference")
            )
            
            await whatsapp_service.send_text_message(
                to=from_number,
                message=(
                    f"✅ *Airtime Purchase Successful!*\n\n"
                    f"Amount: {format_currency(amount)}\n"
                    f"Phone: {phone}\n"
                    f"Network: {network}\n"
                    f"Reference: {transaction.reference}\n\n"
                    f"New Balance: {format_currency(user.wallet_balance)}\n\n"
                    f"Thank you for using ForBill! 💚"
                )
            )
        else:
            # Refund on failure
            wallet_service.refund_transaction(
                db=db,
                transaction_id=transaction.id,
                reason=result.get("message", "Purchase failed")
            )
            
            await whatsapp_service.send_text_message(
                to=from_number,
                message=(
                    f"❌ *Airtime Purchase Failed*\n\n"
                    f"{result.get('message')}\n\n"
                    f"Your wallet has been refunded.\n"
                    f"Reference: {transaction.reference}\n\n"
                    f"Please try again or contact support."
                )
            )
    
    except Exception as e:
        logger.error(f"Error processing airtime purchase: {str(e)}")
        await whatsapp_service.send_text_message(
            to=from_number,
            message="❌ An error occurred. Please try again later."
        )
    finally:
        db.close()


async def handle_data_purchase(from_number: str, parsed: dict):
    """Handle data bundle purchase request"""
    db = SessionLocal()
    try:
        # Get user
        user = get_user_by_phone(db, from_number)
        if not user:
            await whatsapp_service.send_text_message(
                to=from_number,
                message="❌ Please send 'hi' to register first."
            )
            return
        
        network = parsed.get("network")
        data_size_mb = parsed.get("data_size_mb")
        phone = parsed.get("phone_number", from_number)
        
        if not network or not data_size_mb:
            await whatsapp_service.send_text_message(
                to=from_number,
                message=(
                    "📶 *Data Bundles*\n\n"
                    "Which network and plan would you like?\n\n"
                    "*Examples:*\n"
                    "• Buy 1GB MTN\n"
                    "• 2GB Airtel for 08012345678\n"
                    "• 500MB Glo\n\n"
                    "*Networks:* MTN, Airtel, Glo, 9mobile"
                )
            )
            return
        
        # Send "fetching plans" message
        await whatsapp_service.send_text_message(
            to=from_number,
            message=f"📶 Fetching {network.upper()} data plans..."
        )
        
        # Get data plans
        plans_result = await topupmate_service.get_data_plans(network=network)
        
        if not plans_result.get("success") or not plans_result.get("plans"):
            await whatsapp_service.send_text_message(
                to=from_number,
                message="❌ Unable to fetch data plans. Please try again."
            )
            return
        
        # Find matching plan (exact match or closest size)
        plans = plans_result["plans"]
        matching_plan = None
        
        # Try exact match first
        for plan in plans:
            plan_size = plan.get("size_mb", 0)
            if plan_size == data_size_mb:
                matching_plan = plan
                break
        
        # If no exact match, find closest
        if not matching_plan:
            sorted_plans = sorted(plans, key=lambda p: abs(p.get("size_mb", 0) - data_size_mb))
            if sorted_plans:
                matching_plan = sorted_plans[0]
        
        if not matching_plan:
            await whatsapp_service.send_text_message(
                to=from_number,
                message=f"❌ No matching data plan found for {parsed.get('data_size_display')}"
            )
            return
        
        plan_id = matching_plan["plan_id"]
        plan_name = matching_plan["name"]
        plan_amount = matching_plan["price"]
        
        # Check wallet balance
        balance_check = wallet_service.check_sufficient_balance(db, user.id, plan_amount)
        if not balance_check["has_sufficient_balance"]:
            await whatsapp_service.send_text_message(
                to=from_number,
                message=(
                    f"❌ *Insufficient Balance*\n\n"
                    f"Plan: {plan_name}\n"
                    f"Required: {format_currency(plan_amount)}\n"
                    f"Available: {format_currency(balance_check['current_balance'])}\n"
                    f"Shortfall: {balance_check['shortfall_formatted']}\n\n"
                    f"� Type *balance* to fund your wallet"
                )
            )
            return
        
        # Send processing message
        await whatsapp_service.send_text_message(
            to=from_number,
            message=(
                f"⏳ *Processing Data Purchase...*\n\n"
                f"Plan: {plan_name}\n"
                f"Amount: {format_currency(plan_amount)}\n"
                f"Phone: {phone}\n"
                f"Network: {network.upper()}\n\n"
                f"Please wait..."
            )
        )
        
        # Debit wallet
        transaction = wallet_service.debit_wallet(
            db=db,
            user_id=user.id,
            amount=plan_amount,
            description=f"Data purchase - {plan_name}",
            transaction_type=TransactionType.DATA
        )
        
        # Store transaction details
        transaction.recipient_phone = phone
        transaction.network = network.upper()
        transaction.plan_id = plan_id
        transaction.plan_name = plan_name
        transaction.service_provider = "TopUpMate"
        db.commit()
        
        # Purchase data from TopUpMate
        result = await topupmate_service.buy_data(
            phone_number=phone,
            plan_id=plan_id,
            network=network
        )
        
        if result.get("success"):
            # Update transaction status
            wallet_service.update_transaction_status(
                db=db,
                transaction_id=transaction.id,
                status=TransactionStatus.COMPLETED,
                provider_response=str(result),
                provider_reference=result.get("provider_reference")
            )
            
            await whatsapp_service.send_text_message(
                to=from_number,
                message=(
                    f"✅ *Data Purchase Successful!*\n\n"
                    f"Plan: {plan_name}\n"
                    f"Amount: {format_currency(plan_amount)}\n"
                    f"Phone: {phone}\n"
                    f"Network: {network.upper()}\n"
                    f"Reference: {transaction.reference}\n\n"
                    f"New Balance: {format_currency(user.wallet_balance)}\n\n"
                    f"Thank you for using ForBill! 💚"
                )
            )
        else:
            # Refund on failure
            wallet_service.refund_transaction(
                db=db,
                transaction_id=transaction.id,
                reason=result.get("message", "Purchase failed")
            )
            
            await whatsapp_service.send_text_message(
                to=from_number,
                message=(
                    f"❌ *Data Purchase Failed*\n\n"
                    f"{result.get('message')}\n\n"
                    f"Your wallet has been refunded.\n"
                    f"Reference: {transaction.reference}\n\n"
                    f"Please try again or contact support."
                )
            )
    
    except Exception as e:
        logger.error(f"Error processing data purchase: {str(e)}")
        await whatsapp_service.send_text_message(
            to=from_number,
            message="❌ An error occurred. Please try again later."
        )
    finally:
        db.close()


async def handle_electricity_payment(from_number: str, parsed: dict):
    """Handle electricity bill payment request"""
    db = SessionLocal()
    try:
        # Get user
        user = get_user_by_phone(db, from_number)
        if not user:
            await whatsapp_service.send_text_message(
                to=from_number,
                message="❌ Please send 'hi' to register first."
            )
            return
        
        amount = parsed.get("amount")
        meter_number = parsed.get("meter_number")
        disco = parsed.get("disco", "IKEDC")  # Default disco
        
        if not amount:
            await whatsapp_service.send_text_message(
                to=from_number,
                message=(
                    "💡 *Electricity Payment*\n\n"
                    "Please provide:\n"
                    "• Amount (₦1,000 - ₦100,000)\n"
                    "• Meter number\n\n"
                    "*Examples:*\n"
                    "• Buy 5000 electricity for 1234567890\n"
                    "• Pay 10000 light 9876543210\n\n"
                    "*Supported:* IKEDC, EKEDC, AEDC, PHED, etc."
                )
            )
            return
        
        if not meter_number:
            await whatsapp_service.send_text_message(
                to=from_number,
                message=(
                    "💡 *Meter Number Required*\n\n"
                    f"You want to buy {format_currency(amount)} electricity.\n\n"
                    "Please provide your meter number:\n"
                    "Example: 'Buy 5000 electricity for 1234567890'"
                )
            )
            return
        
        # Check wallet balance
        balance_check = wallet_service.check_sufficient_balance(db, user.id, amount)
        if not balance_check["has_sufficient_balance"]:
            await whatsapp_service.send_text_message(
                to=from_number,
                message=(
                    f"❌ *Insufficient Balance*\n\n"
                    f"Required: {format_currency(amount)}\n"
                    f"Available: {format_currency(balance_check['current_balance'])}\n"
                    f"Shortfall: {balance_check['shortfall_formatted']}\n\n"
                    f"💡 Type *balance* to fund your wallet"
                )
            )
            return
        
        # Verify meter number first
        await whatsapp_service.send_text_message(
            to=from_number,
            message=f"🔍 Verifying meter number {meter_number}..."
        )
        
        verification = await topupmate_service.verify_meter_number(
            meter_number=meter_number,
            disco=disco,
            meter_type="prepaid"
        )
        
        if not verification.get("success"):
            await whatsapp_service.send_text_message(
                to=from_number,
                message=(
                    f"❌ *Invalid Meter Number*\n\n"
                    f"{verification.get('message', 'Unable to verify meter')}\n\n"
                    f"Please check the meter number and try again."
                )
            )
            return
        
        customer_name = verification.get("customer_name", "Customer")
        
        # Send processing message
        await whatsapp_service.send_text_message(
            to=from_number,
            message=(
                f"⏳ *Processing Electricity Payment...*\n\n"
                f"Customer: {customer_name}\n"
                f"Meter: {meter_number}\n"
                f"Amount: {format_currency(amount)}\n"
                f"Disco: {disco}\n\n"
                f"Please wait..."
            )
        )
        
        # Debit wallet
        transaction = wallet_service.debit_wallet(
            db=db,
            user_id=user.id,
            amount=amount,
            description=f"Electricity - {meter_number}",
            transaction_type=TransactionType.ELECTRICITY
        )
        
        # Store transaction details
        transaction.meter_number = meter_number
        transaction.service_provider = "TopUpMate"
        db.commit()
        
        # Purchase electricity token
        result = await topupmate_service.buy_electricity(
            meter_number=meter_number,
            amount=amount,
            disco=disco,
            meter_type="prepaid",
            customer_phone=from_number
        )
        
        if result.get("success"):
            # Update transaction status
            wallet_service.update_transaction_status(
                db=db,
                transaction_id=transaction.id,
                status=TransactionStatus.COMPLETED,
                provider_response=str(result),
                provider_reference=result.get("provider_reference")
            )
            
            # Store token
            transaction.token = result.get("token")
            db.commit()
            
            token = result.get("token", "N/A")
            units = result.get("units", "N/A")
            
            await whatsapp_service.send_text_message(
                to=from_number,
                message=(
                    f"✅ *Electricity Purchase Successful!*\n\n"
                    f"Customer: {customer_name}\n"
                    f"Meter: {meter_number}\n"
                    f"Amount: {format_currency(amount)}\n"
                    f"Units: {units} kWh\n\n"
                    f"🔑 *Token:* `{token}`\n\n"
                    f"Reference: {transaction.reference}\n"
                    f"New Balance: {format_currency(user.wallet_balance)}\n\n"
                    f"Thank you for using ForBill! 💚"
                )
            )
        else:
            # Refund on failure
            wallet_service.refund_transaction(
                db=db,
                transaction_id=transaction.id,
                reason=result.get("message", "Purchase failed")
            )
            
            await whatsapp_service.send_text_message(
                to=from_number,
                message=(
                    f"❌ *Electricity Purchase Failed*\n\n"
                    f"{result.get('message')}\n\n"
                    f"Your wallet has been refunded.\n"
                    f"Reference: {transaction.reference}\n\n"
                    f"Please try again or contact support."
                )
            )
    
    except Exception as e:
        logger.error(f"Error processing electricity payment: {str(e)}")
        await whatsapp_service.send_text_message(
            to=from_number,
            message="❌ An error occurred. Please try again later."
        )
    finally:
        db.close()


async def handle_cable_subscription(from_number: str, parsed: dict):
    """Handle cable TV subscription request"""
    db = SessionLocal()
    try:
        # Get user
        user = get_user_by_phone(db, from_number)
        if not user:
            await whatsapp_service.send_text_message(
                to=from_number,
                message="❌ Please send 'hi' to register first."
            )
            return
        
        provider = parsed.get("provider")
        smartcard_number = parsed.get("smartcard_number")
        
        if not provider:
            await whatsapp_service.send_text_message(
                to=from_number,
                message=(
                    "📺 *Cable TV Subscription*\n\n"
                    "Which service would you like to subscribe to?\n\n"
                    "*Examples:*\n"
                    "• Pay DSTV for 1234567890\n"
                    "• Subscribe GOTV 9876543210\n"
                    "• Renew Startimes 5555555555\n\n"
                    "*Supported:* DSTV, GOTV, Startimes"
                )
            )
            return
        
        if not smartcard_number:
            await whatsapp_service.send_text_message(
                to=from_number,
                message=(
                    f"📺 *{provider.upper()} Subscription*\n\n"
                    f"Please provide your smartcard/IUC number:\n\n"
                    f"Example: 'Pay {provider} for 1234567890'"
                )
            )
            return
        
        # Verify smartcard first
        await whatsapp_service.send_text_message(
            to=from_number,
            message=f"🔍 Verifying {provider.upper()} smartcard {smartcard_number}..."
        )
        
        verification = await topupmate_service.verify_smartcard(
            smartcard_number=smartcard_number,
            service_type=provider
        )
        
        if not verification.get("success"):
            await whatsapp_service.send_text_message(
                to=from_number,
                message=(
                    f"❌ *Invalid Smartcard Number*\n\n"
                    f"{verification.get('message', 'Unable to verify smartcard')}\n\n"
                    f"Please check the number and try again."
                )
            )
            return
        
        customer_name = verification.get("customer_name", "Customer")
        current_bouquet = verification.get("current_bouquet", "N/A")
        
        # Get available packages
        await whatsapp_service.send_text_message(
            to=from_number,
            message=f"📺 Fetching {provider.upper()} packages..."
        )
        
        packages_result = await topupmate_service.get_cable_packages(service_type=provider)
        
        if not packages_result.get("success") or not packages_result.get("packages"):
            await whatsapp_service.send_text_message(
                to=from_number,
                message=f"❌ Unable to fetch {provider.upper()} packages. Please try again."
            )
            return
        
        packages = packages_result["packages"]
        
        # Format packages list
        packages_list = f"📺 *{provider.upper()} Packages*\n\n"
        packages_list += f"Customer: {customer_name}\n"
        packages_list += f"Smartcard: {smartcard_number}\n"
        packages_list += f"Current: {current_bouquet}\n\n"
        packages_list += "*Available Packages:*\n"
        
        for idx, pkg in enumerate(packages[:10], 1):  # Show first 10
            pkg_name = pkg.get("name", "Unknown")
            pkg_price = pkg.get("price", 0)
            packages_list += f"{idx}. {pkg_name} - {format_currency(pkg_price)}\n"
        
        packages_list += f"\n💡 To subscribe, reply with the package number (1-{min(10, len(packages))})"
        
        await whatsapp_service.send_text_message(
            to=from_number,
            message=packages_list
        )
        
        # Store state for package selection (in a real app, use session storage)
        # For now, we'll just show the message
        # TODO: Implement state management for multi-step flows
        
    except Exception as e:
        logger.error(f"Error processing cable subscription: {str(e)}")
        await whatsapp_service.send_text_message(
            to=from_number,
            message="❌ An error occurred. Please try again later."
        )
    finally:
        db.close()


async def handle_cable_purchase(from_number: str, smartcard_number: str, package_code: str, provider: str):
    """Complete cable TV purchase after package selection"""
    db = SessionLocal()
    try:
        user = get_user_by_phone(db, from_number)
        if not user:
            return
        
        # Get package details
        packages_result = await topupmate_service.get_cable_packages(service_type=provider)
        if not packages_result.get("success"):
            return
        
        packages = packages_result["packages"]
        selected_package = next((p for p in packages if p.get("code") == package_code), None)
        
        if not selected_package:
            await whatsapp_service.send_text_message(
                to=from_number,
                message="❌ Invalid package selected."
            )
            return
        
        package_name = selected_package["name"]
        package_amount = selected_package["price"]
        
        # Check wallet balance
        balance_check = wallet_service.check_sufficient_balance(db, user.id, package_amount)
        if not balance_check["has_sufficient_balance"]:
            await whatsapp_service.send_text_message(
                to=from_number,
                message=(
                    f"❌ *Insufficient Balance*\n\n"
                    f"Package: {package_name}\n"
                    f"Required: {format_currency(package_amount)}\n"
                    f"Available: {format_currency(balance_check['current_balance'])}\n"
                    f"Shortfall: {balance_check['shortfall_formatted']}\n\n"
                    f"💡 Type *balance* to fund your wallet"
                )
            )
            return
        
        # Send processing message
        await whatsapp_service.send_text_message(
            to=from_number,
            message=(
                f"⏳ *Processing {provider.upper()} Subscription...*\n\n"
                f"Package: {package_name}\n"
                f"Amount: {format_currency(package_amount)}\n"
                f"Smartcard: {smartcard_number}\n\n"
                f"Please wait..."
            )
        )
        
        # Debit wallet
        transaction = wallet_service.debit_wallet(
            db=db,
            user_id=user.id,
            amount=package_amount,
            description=f"{provider.upper()} - {package_name}",
            transaction_type=TransactionType.CABLE_TV
        )
        
        # Store transaction details
        transaction.smartcard_number = smartcard_number
        transaction.service_provider = "TopUpMate"
        db.commit()
        
        # Purchase cable TV subscription
        result = await topupmate_service.buy_cabletv(
            smartcard_number=smartcard_number,
            package_code=package_code,
            service_type=provider,
            customer_phone=from_number
        )
        
        if result.get("success"):
            # Update transaction status
            wallet_service.update_transaction_status(
                db=db,
                transaction_id=transaction.id,
                status=TransactionStatus.COMPLETED,
                provider_response=str(result),
                provider_reference=result.get("provider_reference")
            )
            
            renewal_date = result.get("renewal_date", "N/A")
            
            await whatsapp_service.send_text_message(
                to=from_number,
                message=(
                    f"✅ *{provider.upper()} Subscription Successful!*\n\n"
                    f"Package: {package_name}\n"
                    f"Amount: {format_currency(package_amount)}\n"
                    f"Smartcard: {smartcard_number}\n"
                    f"Renewal: {renewal_date}\n\n"
                    f"Reference: {transaction.reference}\n"
                    f"New Balance: {format_currency(user.wallet_balance)}\n\n"
                    f"Thank you for using ForBill! 💚"
                )
            )
        else:
            # Refund on failure
            wallet_service.refund_transaction(
                db=db,
                transaction_id=transaction.id,
                reason=result.get("message", "Purchase failed")
            )
            
            await whatsapp_service.send_text_message(
                to=from_number,
                message=(
                    f"❌ *{provider.upper()} Subscription Failed*\n\n"
                    f"{result.get('message')}\n\n"
                    f"Your wallet has been refunded.\n"
                    f"Reference: {transaction.reference}\n\n"
                    f"Please try again or contact support."
                )
            )
    
    except Exception as e:
        logger.error(f"Error completing cable purchase: {str(e)}")
    finally:
        db.close()


async def handle_transaction_history(from_number: str):
    """Show transaction history with real data"""
    db = SessionLocal()
    try:
        user = get_user_by_phone(db, from_number)
        
        if not user:
            await whatsapp_service.send_text_message(
                to=from_number,
                message="❌ User not found. Please send 'hi' to register."
            )
            return
        
        transactions = get_user_transactions(db, user.id, limit=5)
        
        if not transactions:
            await whatsapp_service.send_text_message(
                to=from_number,
                message=(
                    "📊 *Transaction History*\n\n"
                    "You have no transactions yet.\n\n"
                    "Start by buying airtime or data!\n\n"
                    "Type 'help' to see available services."
                )
            )
            return
        
        # Format transaction history
        history_text = "📊 *Recent Transactions*\n\n"
        
        for txn in transactions:
            status_emoji = {
                "pending": "⏳",
                "completed": "✅",
                "failed": "❌",
                "cancelled": "🚫"
            }.get(txn.status.value, "❓")
            
            history_text += (
                f"{status_emoji} *{txn.transaction_type.value.upper()}*\n"
                f"Amount: {format_currency(txn.amount)}\n"
                f"Status: {txn.status.value.title()}\n"
                f"Date: {txn.created_at.strftime('%b %d, %Y %I:%M %p')}\n"
                f"Ref: {txn.reference[:12]}...\n\n"
            )
        
        history_text += f"\n💰 Current Balance: *{format_currency(user.wallet_balance)}*"
        
        await whatsapp_service.send_text_message(
            to=from_number,
            message=history_text
        )
    except Exception as e:
        logger.error(f"Error fetching history: {e}")
        await whatsapp_service.send_text_message(
            to=from_number,
            message="❌ Error fetching transaction history. Please try again."
        )
    finally:
        db.close()


async def handle_referral_info(from_number: str):
    """Show referral information with real data"""
    db = SessionLocal()
    try:
        user = get_user_by_phone(db, from_number)
        
        if not user:
            await whatsapp_service.send_text_message(
                to=from_number,
                message="❌ User not found. Please send 'hi' to register."
            )
            return
        
        # Count referrals (users who used this user's referral code)
        referral_count = db.query(User).filter(User.referred_by == user.referral_code).count()
        
        referral_msg = (
            f"🎁 *Referral Program*\n\n"
            f"*Your Referral Code:* `{user.referral_code}`\n\n"
            f"📊 *Stats:*\n"
            f"• Total Referrals: {referral_count}\n"
            f"• Earnings: Coming soon!\n\n"
            f"💰 *How it works:*\n"
            f"1. Share your code with friends\n"
            f"2. They register with your code\n"
            f"3. You earn 5% on their transactions!\n\n"
            f"*Share this message:*\n"
            f"_Join ForBill and get instant bill payments! Use my code *{user.referral_code}* when you register._\n\n"
            f"Type 'help' for more commands."
        )
        
        await whatsapp_service.send_text_message(
            to=from_number,
            message=referral_msg
        )
    except Exception as e:
        logger.error(f"Error fetching referral info: {e}")
        await whatsapp_service.send_text_message(
            to=from_number,
            message="❌ Error fetching referral info. Please try again."
        )
    finally:
        db.close()
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

