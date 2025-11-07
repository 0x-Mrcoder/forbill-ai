# Railway Deployment Troubleshooting

## Health Check Failing - Common Issues

### 1. Database Not Connected ✓ FIXED
**Problem:** App starts but can't connect to database
**Solution:** Added `start.sh` script that:
- Waits for database to be ready
- Runs migrations automatically
- Then starts the app

### 2. Environment Variables Missing
**Check these are set in Railway:**

```bash
# Required Variables
DATABASE_URL              # Auto-set by Railway PostgreSQL
SECRET_KEY               # Your app secret key
DEBUG                    # Set to "False"
ENVIRONMENT              # Set to "production"

# WhatsApp (REQUIRED)
WHATSAPP_API_URL         # https://graph.facebook.com/v18.0
WHATSAPP_TOKEN           # Your Meta token
WHATSAPP_PHONE_NUMBER_ID # Your phone number ID
WHATSAPP_VERIFY_TOKEN    # Your verify token

# Payrant (REQUIRED)
PAYRANT_BASE_URL         # https://api.payrant.ng/v1
PAYRANT_SECRET_KEY       # Your secret key
PAYRANT_PUBLIC_KEY       # Your public key

# TopUpMate (REQUIRED)
TOPUPMATE_BASE_URL       # https://api.topupmate.ng/v1
TOPUPMATE_API_KEY        # Your API key
TOPUPMATE_PUBLIC_KEY     # Your public key
```

### 3. How to Check Railway Logs

1. Go to your Railway dashboard
2. Click on your service
3. Go to "Deployments" tab
4. Click on the latest deployment
5. Click "View Logs"

Look for these common errors:

**"No module named 'app'"**
- Your code isn't being copied correctly
- Check if .dockerignore is blocking files

**"Connection refused" or "Database error"**
- DATABASE_URL not set
- PostgreSQL service not added
- Database migrations not run

**"Invalid token" or "Authentication failed"**
- Missing environment variables
- Check WHATSAPP_TOKEN, PAYRANT_SECRET_KEY, etc.

**"Port already in use"**
- Should not happen on Railway
- Railway automatically assigns $PORT

### 4. Quick Fixes

**Redeploy with new changes:**
```bash
git add .
git commit -m "fix: update Railway configuration"
git push origin main
```

**Force rebuild on Railway:**
- Go to Settings → General
- Click "Redeploy"

**Check database connection:**
```bash
# In Railway dashboard, open "PostgreSQL" service
# Copy DATABASE_URL
# Make sure it's automatically linked to your app
```

### 5. Verify Your Setup

**Step-by-step checklist:**

- [ ] PostgreSQL service added to project
- [ ] DATABASE_URL appears in your app's variables
- [ ] All environment variables copied from .env
- [ ] WhatsApp credentials are correct
- [ ] Payrant credentials are correct
- [ ] TopUpMate credentials are correct
- [ ] Latest code pushed to GitHub (with start.sh)
- [ ] Railway redeployed with latest code

### 6. Test Locally First

Before deploying, test that your app works:

```bash
# Start locally
uvicorn app.main:app --reload

# In another terminal, test health endpoint
curl http://localhost:8000/health
# Should return: {"status":"healthy","app":"ForBill"}

# Test database connection
curl http://localhost:8000/docs
# Should show API documentation
```

### 7. Contact Support

If issues persist:

1. **Railway Discord:** https://discord.gg/railway
2. **Check Railway Status:** https://status.railway.app
3. **Review Railway Docs:** https://docs.railway.app

### 8. Common Railway Issues

**Build succeeds but health check fails:**
- App is crashing on startup
- Check logs for Python errors
- Verify all imports work
- Test database migrations

**"Service unavailable" error:**
- App not binding to correct port
- Should use: `--port $PORT` (Railway sets this)
- Check start.sh uses: `${PORT:-8000}`

**Deployment takes too long:**
- Normal for first deployment (installing dependencies)
- Should be faster on subsequent deploys
- Railway caches dependencies

---

## Current Configuration

✅ **start.sh** - Handles database wait + migrations
✅ **railway.json** - Uses start.sh as entry point
✅ **Procfile** - Backup configuration
✅ **requirements.txt** - All dependencies listed
✅ **.gitignore** - Excludes unnecessary files

## Next Steps After This Fix

1. Commit and push changes:
   ```bash
   git add .
   git commit -m "fix: add Railway startup script with database wait"
   git push origin main
   ```

2. Railway will auto-deploy (or click "Redeploy")

3. Watch the logs - you should see:
   ```
   🚀 Starting ForBill Application...
   ⏳ Waiting for database...
   ✅ Database is ready!
   🔄 Running database migrations...
   ✅ Starting uvicorn server...
   ```

4. Health check should pass! 🎉
