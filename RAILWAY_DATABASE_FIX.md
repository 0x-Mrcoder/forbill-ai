# 🚨 DATABASE CONNECTION ERROR - SOLUTION

## Error: `[Errno 111] Connect call failed ('127.0.0.1', 5432)`

This means your app is trying to connect to `localhost` instead of Railway's PostgreSQL.

## ✅ SOLUTION (2 steps):

### Step 1: Add PostgreSQL Database to Railway

1. Go to your Railway project: https://railway.app/project/YOUR_PROJECT
2. Click **"+ New"** button (top right)
3. Select **"Database"**
4. Click **"Add PostgreSQL"**
5. Wait for it to provision (takes ~30 seconds)

### Step 2: Verify DATABASE_URL is Set

1. Click on your **forbill-ai service** (not the database)
2. Go to **"Variables"** tab
3. You should see `DATABASE_URL` automatically appear
4. If not, click **"Settings"** → **"Connect"** → Select PostgreSQL database

**Railway will automatically redeploy after adding the database!**

---

## 🔍 How to Verify It's Working

After adding PostgreSQL, check the deployment logs. You should see:

```
🚀 Starting ForBill Application...
🔧 Activating virtual environment...
🔍 Checking environment variables...
✅ DATABASE_URL is set
✅ PORT: 8000
🔄 Running database migrations...
✅ Migrations completed successfully
✅ Starting uvicorn server on port 8000...
```

Then the health check should pass! ✅

---

## 🎯 Visual Guide

```
Your Railway Project
│
├── 📦 forbill-ai (your app)
│   ├── Variables
│   │   ├── DATABASE_URL ← Should appear automatically
│   │   ├── WHATSAPP_TOKEN ← You need to add these
│   │   ├── PAYRANT_SECRET_KEY
│   │   └── TOPUPMATE_API_KEY
│   └── Settings
│       └── Connect → PostgreSQL ← Link them here
│
└── 🗄️ PostgreSQL (database)
    └── Automatically provides DATABASE_URL
```

---

## ⚠️ Still Not Working?

### Check 1: Is PostgreSQL Running?
- Click on PostgreSQL service
- Status should be "Active" (green)
- If it says "Crashed", restart it

### Check 2: Is DATABASE_URL Visible?
- Go to forbill-ai → Variables
- Search for `DATABASE_URL`
- Should look like: `postgresql://postgres:password@host:port/railway`

### Check 3: Are Services Connected?
- Go to forbill-ai → Settings → Connect
- PostgreSQL should be checked/enabled

---

## 🔄 Force Reconnection

If DATABASE_URL exists but still failing:

1. Go to forbill-ai service
2. Click **Settings** → **General**
3. Scroll down
4. Click **"Redeploy"** button

This will restart your app with fresh connections.

---

## 📞 Need More Help?

If you've added PostgreSQL and it's still failing:

1. **Copy the full deployment logs** from Railway
2. **Check if other environment variables are missing**
   - See `RAILWAY_ENV_VARS.md` for full list
3. **Verify your Procfile and railway.json** exist in repo

The error `Connect call failed ('127.0.0.1', 5432)` specifically means DATABASE_URL is either:
- Not set at all
- Set to a localhost URL (wrong)
- Empty string

**Adding the PostgreSQL service will fix this automatically!**
