# 🚨 CRITICAL: Railway Deployment Issue & Solution

## Current Problem

Your Railway deployment is failing because:
**❌ PostgreSQL database is NOT added to your Railway project**

The error `Connect call failed ('127.0.0.1', 5432)` means DATABASE_URL is not set.

---

## ✅ COMPLETE SOLUTION (5 Steps)

### Step 1: Add PostgreSQL Database (REQUIRED)

1. Open your Railway project: https://railway.app
2. Find your `forbill-ai` project
3. Click **"+ New"** (top right of project)
4. Select **"Database"**
5. Click **"Add PostgreSQL"**
6. Wait 30-60 seconds for provisioning

### Step 2: Link Database to Your App

1. Click on your **forbill-ai** service (the main app, not database)
2. Go to **"Settings"** tab
3. Scroll to **"Service Connections"** or **"Connect"**
4. Enable/check the **PostgreSQL** database
5. Click **"Save"** or it auto-saves

### Step 3: Verify DATABASE_URL Appears

1. Still in **forbill-ai** service
2. Go to **"Variables"** tab
3. Look for `DATABASE_URL` - should appear automatically
4. Format: `postgresql://postgres:xxxx@xxxx.railway.internal:5432/railway`

**If you don't see DATABASE_URL:**
- Go back to Step 2 and ensure connection is made
- Or manually click "Add Variable" and reference the PostgreSQL service

### Step 4: Add Required Environment Variables

In the **Variables** tab of forbill-ai service, add these:

**Copy these from your local `.env` file:**

```bash
# Required Application Variables
SECRET_KEY=your-secret-key-here
ENVIRONMENT=production
DEBUG=False

# WhatsApp (REQUIRED)
WHATSAPP_API_URL=https://graph.facebook.com/v18.0
WHATSAPP_TOKEN=your_whatsapp_token
WHATSAPP_PHONE_NUMBER_ID=your_phone_id
WHATSAPP_VERIFY_TOKEN=your_verify_token
WHATSAPP_BUSINESS_ACCOUNT_ID=your_business_id

# Payrant (REQUIRED)
PAYRANT_BASE_URL=https://api.payrant.ng/v1
PAYRANT_SECRET_KEY=your_payrant_secret
PAYRANT_PUBLIC_KEY=your_payrant_public

# TopUpMate (REQUIRED)
TOPUPMATE_BASE_URL=https://api.topupmate.ng/v1
TOPUPMATE_API_KEY=your_topupmate_key
TOPUPMATE_PUBLIC_KEY=your_topupmate_public
```

**How to add:**
- Click "New Variable" button
- Enter name (e.g., `WHATSAPP_TOKEN`)
- Paste value
- Repeat for each variable

### Step 5: Trigger Redeploy

After adding all variables, Railway should auto-redeploy.

**If not:**
1. Go to **"Deployments"** tab
2. Click **"Redeploy"** on the latest deployment
3. Or click **"Deploy Now"** button

---

## ✅ Expected Successful Deployment Logs

After adding PostgreSQL and variables, you should see:

```
🚀 Starting ForBill Application...
🔧 Activating virtual environment...
🔍 Checking environment variables...
✅ DATABASE_URL is set
✅ PORT: 8000
🔄 Running database migrations...
INFO  [alembic.runtime.migration] Context impl PostgresqlImpl.
INFO  [alembic.runtime.migration] Will assume transactional DDL.
INFO  [alembic.runtime.migration] Running upgrade -> base
✅ Migrations completed successfully
✅ Starting uvicorn server on port 8000...
INFO:     Started server process [1]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

Then health check passes: ✅

---

## 🎯 Visual Railway Setup

```
Your Railway Project Dashboard
│
├── 📦 forbill-ai (your app service)
│   │
│   ├── 📁 Variables Tab
│   │   ├── DATABASE_URL (auto-added after Step 2)
│   │   ├── WHATSAPP_TOKEN (you add)
│   │   ├── WHATSAPP_PHONE_NUMBER_ID (you add)
│   │   ├── PAYRANT_SECRET_KEY (you add)
│   │   ├── TOPUPMATE_API_KEY (you add)
│   │   └── ... (other variables)
│   │
│   ├── ⚙️  Settings Tab
│   │   └── Connect → ✓ PostgreSQL (enable this)
│   │
│   └── 🚀 Deployments Tab
│       └── Shows deployment status & logs
│
└── 🗄️  PostgreSQL (database service)
    └── Status: Active ✓
```

---

## 🔍 Troubleshooting

### Issue: "DATABASE_URL is not set" error persists

**Solution:**
1. Verify PostgreSQL service exists and is Active (green status)
2. Click PostgreSQL service → copy the connection URL
3. Manually add it to forbill-ai:
   - Go to forbill-ai → Variables
   - Click "New Variable"
   - Name: `DATABASE_URL`
   - Value: paste the PostgreSQL URL
   - Format: `postgresql://postgres:password@host.railway.internal:5432/railway`

### Issue: "Migrations failed" error

**Solution:**
- DATABASE_URL format is correct (check for typos)
- PostgreSQL service is running (not crashed)
- Try restarting PostgreSQL service

### Issue: "Module not found" errors

**Solution:**
- Verify `requirements.txt` is in your repo
- Check Railway build logs show "pip install -r requirements.txt"
- Ensure all dependencies installed successfully

### Issue: Health check still failing after everything

**Solution:**
1. Check **Deployments → View Logs** for Python errors
2. Verify ALL required environment variables are set
3. Test locally first: `uvicorn app.main:app --reload`
4. Check if port conflicts (Railway sets $PORT automatically)

---

## 📋 Checklist Before Next Deploy

- [ ] PostgreSQL database added to Railway project
- [ ] PostgreSQL status is "Active" (green)
- [ ] forbill-ai service connected to PostgreSQL
- [ ] DATABASE_URL appears in forbill-ai Variables tab
- [ ] All WhatsApp variables added (TOKEN, PHONE_ID, etc.)
- [ ] All Payrant variables added (SECRET_KEY, PUBLIC_KEY)
- [ ] All TopUpMate variables added (API_KEY, PUBLIC_KEY)
- [ ] SECRET_KEY is set (not empty)
- [ ] Latest code deployed (commit a0feb19 or later)
- [ ] Watched deployment logs for errors

---

## 🎉 Success Indicators

✅ Build completes successfully  
✅ start.sh shows "DATABASE_URL is set"  
✅ Migrations run without errors  
✅ Uvicorn starts on correct port  
✅ Health check passes (shows "healthy")  
✅ Service status: "Active" (green)  

---

## 💡 Pro Tips

1. **Railway auto-deploys on git push** - any commit to main triggers rebuild
2. **Variables cause redeploy** - adding/changing variables triggers automatic redeploy
3. **Check logs in real-time** - Deployments tab shows live logs
4. **PostgreSQL takes time** - first provision can take 1-2 minutes
5. **Variables are encrypted** - safe to store API keys

---

## 📞 Still Stuck?

**Copy your Railway deployment logs and check:**
1. Is PostgreSQL service visible in your project?
2. What does the Variables tab show? (list all variable names, not values)
3. What error appears in the deployment logs?

The #1 cause of this error is: **PostgreSQL not added to Railway project**

**Once you add PostgreSQL, everything should work!** ✅
