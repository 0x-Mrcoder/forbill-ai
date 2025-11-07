# Railway Deployment Guide

## Prerequisites
- Railway account (https://railway.app)
- GitHub account
- All API credentials ready

## Step 1: Prepare Repository

1. Ensure all changes are committed:
```bash
git status
git add -A
git commit -m "Production ready"
```

## Step 2: Create GitHub Repository

1. Go to https://github.com/new
2. Repository name: `forbill-ai`
3. Description: "Smart WhatsApp Bill Payment Bot for Nigeria"
4. Choose: Public or Private
5. DO NOT initialize with README (we already have one)
6. Click "Create repository"

## Step 3: Push to GitHub

```bash
# Add GitHub remote
git remote add origin https://github.com/YOUR_USERNAME/forbill-ai.git

# Push to GitHub
git branch -M main
git push -u origin main
```

## Step 4: Deploy to Railway

### Option A: Via Railway Dashboard (Recommended)

1. Go to https://railway.app
2. Click "New Project"
3. Select "Deploy from GitHub repo"
4. Choose your `forbill-ai` repository
5. Railway will auto-detect the configuration from `railway.json`

### Option B: Via Railway CLI

```bash
# Install Railway CLI
npm install -g @railway/cli

# Login
railway login

# Link to project
railway link

# Deploy
railway up
```

## Step 5: Configure Environment Variables

In Railway dashboard, go to Variables and add:

### Required Variables
```
DATABASE_URL=postgresql://...  (Railway provides this automatically)
APP_NAME=ForBill
ENVIRONMENT=production
DEBUG=False
SECRET_KEY=your-secret-key-here

# WhatsApp
WHATSAPP_API_URL=https://graph.facebook.com/v18.0
WHATSAPP_TOKEN=your_token
WHATSAPP_PHONE_NUMBER_ID=your_id
WHATSAPP_VERIFY_TOKEN=your_verify_token
WHATSAPP_BUSINESS_ACCOUNT_ID=your_account_id

# Payrant
PAYRANT_BASE_URL=https://api.payrant.ng/v1
PAYRANT_SECRET_KEY=your_secret
PAYRANT_PUBLIC_KEY=your_public_key

# TopUpMate
TOPUPMATE_BASE_URL=https://api.topupmate.ng/v1
TOPUPMATE_API_KEY=your_api_key
TOPUPMATE_PUBLIC_KEY=your_public_key

# CORS (optional)
CORS_ORIGINS=*
```

## Step 6: Add PostgreSQL Database

1. In Railway dashboard, click "New"
2. Select "Database" → "PostgreSQL"
3. Railway will automatically set `DATABASE_URL`

## Step 7: Run Migrations

```bash
# Connect to Railway environment
railway run alembic upgrade head
```

Or add to your `railway.json`:
```json
{
  "build": {
    "builder": "NIXPACKS"
  },
  "deploy": {
    "startCommand": "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port $PORT",
    "healthcheckPath": "/health",
    "healthcheckTimeout": 100,
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 10
  }
}
```

## Step 8: Configure WhatsApp Webhook

1. Get your Railway URL: `https://your-app.railway.app`
2. Go to Meta Developer Console
3. WhatsApp → Configuration → Webhook
4. Set Callback URL: `https://your-app.railway.app/webhooks/whatsapp`
5. Set Verify Token: (same as `WHATSAPP_VERIFY_TOKEN`)
6. Subscribe to webhook fields: `messages`

## Step 9: Test Deployment

### 1. Health Check
```bash
curl https://your-app.railway.app/health
```

Expected response:
```json
{"status": "healthy", "app": "ForBill"}
```

### 2. Test WhatsApp Webhook
Send a test message to your WhatsApp number:
```
Hi
```

### 3. Check Logs
```bash
railway logs
```

## Step 10: Configure Payrant Webhook

1. Login to Payrant dashboard
2. Settings → Webhooks
3. Add webhook URL: `https://your-app.railway.app/webhooks/payrant`
4. Enable webhook events: `payment.success`, `transaction.success`

## Troubleshooting

### Issue: App crashes on startup
**Solution**: Check logs for missing environment variables
```bash
railway logs
```

### Issue: Database connection failed
**Solution**: Ensure PostgreSQL is running and `DATABASE_URL` is set
```bash
railway variables
```

### Issue: WhatsApp webhook not working
**Solution**: 
1. Verify webhook URL is accessible
2. Check verify token matches
3. Review webhook logs in Meta dashboard

### Issue: Migrations not running
**Solution**: Run manually
```bash
railway run alembic upgrade head
```

## Monitoring

### View Logs
```bash
railway logs --tail
```

### View Metrics
Check Railway dashboard for:
- CPU usage
- Memory usage
- Request count
- Response times

### Set up Alerts
1. Railway dashboard → Settings → Notifications
2. Configure alerts for:
   - High error rate
   - Service down
   - Memory issues

## Scaling

### Vertical Scaling
Railway dashboard → Settings → Resources
- Increase memory
- Increase CPU

### Horizontal Scaling
Not needed initially. Consider when:
- Traffic > 1000 requests/minute
- Response time > 2 seconds

## Maintenance

### Deploy Updates
```bash
git push origin main
# Railway auto-deploys on push
```

### Rollback
Railway dashboard → Deployments → Select previous → Rollback

### Backup Database
```bash
railway run pg_dump $DATABASE_URL > backup.sql
```

## Security Checklist

- [ ] All API keys in environment variables
- [ ] `DEBUG=False` in production
- [ ] Database backups configured
- [ ] HTTPS enabled (automatic on Railway)
- [ ] Webhook signature verification enabled
- [ ] Rate limiting configured (if needed)

## Next Steps

1. ✅ Deploy to Railway
2. ⏳ Test all services
3. ⏳ Monitor for 24 hours
4. ⏳ Set up error tracking (Sentry)
5. ⏳ Configure domain (optional)

## Support

- Railway Docs: https://docs.railway.app
- Railway Discord: https://discord.gg/railway
- Project Issues: https://github.com/YOUR_USERNAME/forbill-ai/issues

---

**Deployment Status**: 🚀 Ready to deploy!
