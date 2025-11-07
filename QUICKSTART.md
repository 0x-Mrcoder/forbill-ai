# Quick Deployment Commands

## Step 1: Create GitHub Repository

### Option A: Use the automated script
```bash
./deploy.sh
```

### Option B: Manual setup

1. **Create GitHub Repository**
   - Go to: https://github.com/new
   - Repository name: `forbill-ai`
   - Description: "Smart WhatsApp Bill Payment Bot for Nigeria"
   - Choose: Public or Private
   - DO NOT check "Initialize with README"
   - Click "Create repository"

2. **Push your code**
   ```bash
   # Replace YOUR_USERNAME with your GitHub username
   git remote add origin https://github.com/YOUR_USERNAME/forbill-ai.git
   git branch -M main
   git push -u origin main
   ```

## Step 2: Deploy to Railway

### Quick Deploy (Recommended)

1. **Go to Railway**
   - Visit: https://railway.app
   - Sign in with GitHub

2. **Create New Project**
   - Click "New Project"
   - Select "Deploy from GitHub repo"
   - Choose `forbill-ai` repository
   - Railway auto-detects configuration ✨

3. **Add PostgreSQL Database**
   - Click "New" → "PostgreSQL"
   - `DATABASE_URL` is automatically configured

4. **Add Environment Variables**
   - Click on your service → Variables tab
   - Add these variables (copy from your .env file):

   ```
   APP_NAME=ForBill
   ENVIRONMENT=production
   DEBUG=False
   SECRET_KEY=your-secret-key-here
   
   # WhatsApp
   WHATSAPP_API_URL=https://graph.facebook.com/v18.0
   WHATSAPP_TOKEN=your_token_here
   WHATSAPP_PHONE_NUMBER_ID=your_id_here
   WHATSAPP_VERIFY_TOKEN=your_verify_token_here
   WHATSAPP_BUSINESS_ACCOUNT_ID=your_account_id_here
   
   # Payrant
   PAYRANT_BASE_URL=https://api.payrant.ng/v1
   PAYRANT_SECRET_KEY=your_secret_key_here
   PAYRANT_PUBLIC_KEY=your_public_key_here
   
   # TopUpMate  
   TOPUPMATE_BASE_URL=https://api.topupmate.ng/v1
   TOPUPMATE_API_KEY=your_api_key_here
   TOPUPMATE_PUBLIC_KEY=your_public_key_here
   ```

5. **Deploy!**
   - Railway automatically builds and deploys
   - Wait for "Success" status
   - Copy your app URL: `https://forbill-ai-production.up.railway.app`

## Step 3: Configure Webhooks

### WhatsApp Webhook

1. Go to: https://developers.facebook.com
2. Your App → WhatsApp → Configuration
3. Click "Edit" on Webhook
4. Callback URL: `https://your-app.railway.app/webhooks/whatsapp`
5. Verify Token: (same as `WHATSAPP_VERIFY_TOKEN`)
6. Click "Verify and Save"
7. Subscribe to: `messages`

### Payrant Webhook

1. Go to Payrant Dashboard
2. Settings → Webhooks
3. Add URL: `https://your-app.railway.app/webhooks/payrant`
4. Enable: `payment.success`, `transaction.success`

## Step 4: Test Your Deployment

```bash
# Test health endpoint
curl https://your-app.railway.app/health

# Should return:
# {"status":"healthy","app":"ForBill"}
```

Send a WhatsApp message to your bot:
```
Hi
```

You should receive a welcome message! 🎉

## Troubleshooting

### Check Logs
```bash
# In Railway dashboard
Settings → Deployments → View Logs
```

### Common Issues

**Build Failed**
- Check if all files are pushed to GitHub
- Verify `railway.json` exists
- Check logs for specific error

**App Crashes**
- Verify all environment variables are set
- Check DATABASE_URL is configured
- Review application logs

**Webhook Not Working**
- Verify webhook URL is accessible
- Check verify token matches exactly
- Test webhook with curl
- Check WhatsApp webhook logs

**Database Error**
- Ensure PostgreSQL is added
- Run migrations: `railway run alembic upgrade head`
- Check DATABASE_URL format

## Need Help?

1. Check logs: Railway Dashboard → Logs
2. Review: `DEPLOYMENT.md` (detailed guide)
3. Test endpoints: `/health`, `/docs`
4. Verify environment variables are set correctly

---

**You're all set!** 🚀

Your ForBill bot should now be live and processing payments via WhatsApp!
