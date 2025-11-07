# Railway Environment Variables Checklist

## ⚠️ CRITICAL: These MUST be set in Railway Dashboard

Go to: Your Service → Variables tab

### Database (Auto-configured)
- `DATABASE_URL` - Automatically set when you add PostgreSQL service

### Application Settings
```
APP_NAME=ForBill
ENVIRONMENT=production
DEBUG=False
SECRET_KEY=your-secret-key-here-change-this-in-production
```

### WhatsApp Configuration (REQUIRED)
```
WHATSAPP_API_URL=https://graph.facebook.com/v18.0
WHATSAPP_TOKEN=your_whatsapp_token_from_meta
WHATSAPP_PHONE_NUMBER_ID=your_phone_number_id
WHATSAPP_VERIFY_TOKEN=your_custom_verify_token
WHATSAPP_BUSINESS_ACCOUNT_ID=your_business_account_id
```

### Payrant Configuration (REQUIRED)
```
PAYRANT_BASE_URL=https://api.payrant.ng/v1
PAYRANT_SECRET_KEY=your_payrant_secret_key
PAYRANT_PUBLIC_KEY=your_payrant_public_key
```

### TopUpMate Configuration (REQUIRED)
```
TOPUPMATE_BASE_URL=https://api.topupmate.ng/v1
TOPUPMATE_API_KEY=your_topupmate_api_key
TOPUPMATE_PUBLIC_KEY=your_topupmate_public_key
```

---

## 🔍 How to Add Variables in Railway

1. Go to your Railway project
2. Click on your service (forbill-ai)
3. Go to "Variables" tab
4. Click "New Variable"
5. Enter variable name and value
6. Click "Add"
7. Repeat for all variables above

**After adding all variables, Railway will automatically redeploy!**

---

## ✅ Quick Copy-Paste Template

Replace the values with your actual credentials, then paste in Railway:

```
APP_NAME=ForBill
ENVIRONMENT=production
DEBUG=False
SECRET_KEY=generate-a-random-secret-key-here
WHATSAPP_API_URL=https://graph.facebook.com/v18.0
WHATSAPP_TOKEN=YOUR_TOKEN_HERE
WHATSAPP_PHONE_NUMBER_ID=YOUR_PHONE_ID
WHATSAPP_VERIFY_TOKEN=YOUR_VERIFY_TOKEN
WHATSAPP_BUSINESS_ACCOUNT_ID=YOUR_BUSINESS_ID
PAYRANT_BASE_URL=https://api.payrant.ng/v1
PAYRANT_SECRET_KEY=YOUR_PAYRANT_SECRET
PAYRANT_PUBLIC_KEY=YOUR_PAYRANT_PUBLIC
TOPUPMATE_BASE_URL=https://api.topupmate.ng/v1
TOPUPMATE_API_KEY=YOUR_TOPUPMATE_KEY
TOPUPMATE_PUBLIC_KEY=YOUR_TOPUPMATE_PUBLIC
```

---

## 🚨 Common Mistakes

❌ **Missing DATABASE_URL**
- Solution: Add PostgreSQL service in Railway (New → Database → PostgreSQL)

❌ **Wrong format for DATABASE_URL**
- Should be: `postgresql://user:pass@host:port/dbname`
- Railway sets this automatically

❌ **Typos in variable names**
- Copy exactly from the list above
- Variable names are case-sensitive

❌ **Missing required variables**
- App won't start without WhatsApp, Payrant, or TopUpMate credentials

---

## 📝 How to Get Your Credentials

### WhatsApp (Meta/Facebook)
1. Go to https://developers.facebook.com
2. Your App → WhatsApp → API Setup
3. Copy: Token, Phone Number ID, Business Account ID
4. Create a verify token (any random string)

### Payrant
1. Go to https://payrant.ng
2. Login to dashboard
3. Settings → API Keys
4. Copy: Secret Key, Public Key

### TopUpMate
1. Go to https://topupmate.ng
2. Login to dashboard
3. Settings → API Credentials
4. Copy: API Key, Public Key

---

## 🔐 Generate SECRET_KEY

Run this locally:
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

Copy the output and use it as your SECRET_KEY.
