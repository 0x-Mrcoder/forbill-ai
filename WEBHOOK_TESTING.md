# WhatsApp Webhook Testing Guide

## 1. Setup ngrok (if not installed)

```bash
# Download ngrok
wget https://bin.equinox.io/c/bNyj1mQVY4c/ngrok-v3-stable-linux-amd64.tgz

# Extract
tar -xvzf ngrok-v3-stable-linux-amd64.tgz

# Move to PATH
sudo mv ngrok /usr/local/bin/

# Add your authtoken (get from https://dashboard.ngrok.com/)
ngrok config add-authtoken YOUR_AUTHTOKEN
```

## 2. Start the Application

```bash
# Activate virtual environment
cd "/home/mrcoder/Documents/Workstation/ForBill/ForBill AI"
source venv/bin/activate

# Start FastAPI server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## 3. Start ngrok Tunnel

In a new terminal:
```bash
ngrok http 8000
```

You'll get a public URL like: `https://abcd-1234.ngrok.io`

## 4. Configure Meta WhatsApp Webhook

1. Go to Meta Developer Console: https://developers.facebook.com/apps/3226882497473467/
2. Navigate to WhatsApp > Configuration
3. In **Webhook** section, click "Edit"
4. Enter:
   - **Callback URL**: `https://your-ngrok-url.ngrok.io/webhooks/whatsapp`
   - **Verify Token**: `forbill_webhook_secret_2025` (from .env)
5. Click "Verify and Save"
6. Subscribe to webhook fields:
   - ✅ messages
   - ✅ message_status (optional)

## 5. Test the Integration

### Test 1: Send a message to your WhatsApp Business number
Send: `Hi`

Expected Response:
```
👋 Welcome to ForBill!

I'm your virtual assistant for bill payments and airtime purchases.

Quick Menu:
1️⃣ Buy Airtime
2️⃣ Buy Data
3️⃣ Pay Bills
4️⃣ Check Balance
5️⃣ Transaction History

Reply with a number or type 'help' for more options.
```

### Test 2: Send help command
Send: `help`

Expected Response:
```
📱 ForBill - Available Commands

Services:
• Airtime Purchase
• Data Bundles
• Electricity Bills
• Cable TV Subscriptions
• Wallet Management

How to use:
Just reply with the number from the menu or describe what you need!

Example: 'Buy 1000 airtime' or 'Check my balance'
```

### Test 3: Send any other text
Send: `Test message`

Expected Response:
```
You said: Test message

I'm still learning! Type 'help' to see what I can do.
```

## 6. Monitor Logs

### Application Logs
```bash
# Watch FastAPI logs
tail -f logs/forbill_2025-11-07.log
```

### Check Webhook Logs in Database
```bash
sqlite3 forbill.db "SELECT * FROM webhook_logs ORDER BY created_at DESC LIMIT 5;"
```

## 7. Debugging Tips

### Check if server is running:
```bash
curl http://localhost:8000/health
```

### Test webhook verification manually:
```bash
curl "http://localhost:8000/webhooks/whatsapp?hub.mode=subscribe&hub.verify_token=forbill_webhook_secret_2025&hub.challenge=test123"
```

Expected: `test123`

### Send test webhook payload:
```bash
curl -X POST http://localhost:8000/webhooks/whatsapp \
  -H "Content-Type: application/json" \
  -d '{
    "object": "whatsapp_business_account",
    "entry": [{
      "changes": [{
        "value": {
          "messages": [{
            "id": "test_msg_123",
            "from": "2349012345678",
            "timestamp": "1699999999",
            "type": "text",
            "text": {
              "body": "Hello"
            }
          }]
        }
      }]
    }]
  }'
```

## 8. Troubleshooting

### Issue: Webhook verification fails
- Check that WHATSAPP_VERIFY_TOKEN in .env matches the token in Meta console
- Ensure ngrok URL is correct and accessible

### Issue: No response to messages
- Check that WHATSAPP_ACCESS_TOKEN is valid
- Verify WHATSAPP_PHONE_NUMBER_ID is correct
- Check application logs for errors

### Issue: Messages not being received
- Ensure webhook is subscribed to "messages" field in Meta console
- Check that ngrok tunnel is still active
- Verify the webhook URL is correct

## 9. Production Deployment

Once tested locally, deploy to Railway:

```bash
# Commit changes
git add .
git commit -m "Add WhatsApp webhook integration"
git push

# Railway will auto-deploy
# Update Meta webhook URL to: https://your-app.railway.app/webhooks/whatsapp
```

## API Endpoints

- **GET** `/` - Root endpoint
- **GET** `/health` - Health check
- **GET** `/webhooks/whatsapp` - Webhook verification
- **POST** `/webhooks/whatsapp` - Receive messages
- **GET** `/docs` - API documentation (dev only)

## Environment Variables Required

```env
WHATSAPP_ACCESS_TOKEN=your_access_token
WHATSAPP_PHONE_NUMBER_ID=909930968862908
WHATSAPP_VERIFY_TOKEN=forbill_webhook_secret_2025
WHATSAPP_APP_ID=3226882497473467
```
