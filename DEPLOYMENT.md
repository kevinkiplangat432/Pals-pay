# PalsPay Deployment Guide

## 🚀 Backend Deployment (Render)

### Step 1: Create Render Account
1. Go to https://render.com
2. Sign up with GitHub
3. Connect your GitHub repository

### Step 2: Create PostgreSQL Database
1. Click "New +" → "PostgreSQL"
2. Name: `palspay-db`
3. Database: `palspay_production`
4. User: `palspay_user`
5. Region: Oregon (or closest to you)
6. Plan: Free
7. Click "Create Database"
8. **Copy the Internal Database URL** (starts with `postgresql://`)

### Step 3: Deploy Backend
1. Click "New +" → "Web Service"
2. Connect your GitHub repo: `Pals-pay`
3. Configure:
   - **Name**: `palspay-backend`
   - **Region**: Oregon
   - **Branch**: `main`
   - **Root Directory**: `backend`
   - **Runtime**: Python 3
   - **Build Command**: `./build.sh`
   - **Start Command**: `gunicorn run:app`
   - **Plan**: Free

4. **Add Environment Variables**:
   ```
   FLASK_ENV=production
   DEBUG=False
   SECRET_KEY=[Click "Generate" button]
   JWT_SECRET_KEY=[Click "Generate" button]
   DATABASE_URL=[Paste Internal Database URL from Step 2]
   
   # CORS - Update after frontend deployment
   CORS_ORIGINS=https://your-frontend.vercel.app
   
   # Email
   EMAIL_ENABLED=true
   EMAIL_SENDER=kiplangatkevin335@gmail.com
   EMAIL_PASSWORD=lznevvglsremomgz
   SMTP_HOST=smtp.gmail.com
   SMTP_PORT=587
   
   # M-Pesa (Update with your credentials)
   MPESA_CONSUMER_KEY=WrqbhQmUYwYnroG0LksVpqNsdY6AdV9Xl25CjLhm1RKMqYuW
   MPESA_CONSUMER_SECRET=yHAzIJPbov6h3rOFo26WEcMFvTDyWp7DKetQvx2GGJZ9RBDSxdpTBGWnFW2OQ2Xa
   MPESA_SHORTCODE=174379
   MPESA_PASSKEY=your-passkey
   MPESA_API_URL=https://sandbox.safaricom.co.ke
   MPESA_CALLBACK_URL=https://palspay-backend.onrender.com/api/v1/mpesa/callback
   MPESA_B2C_RESULT_URL=https://palspay-backend.onrender.com/api/v1/mpesa/b2c/result
   MPESA_B2C_TIMEOUT_URL=https://palspay-backend.onrender.com/api/v1/mpesa/b2c/timeout
   MPESA_INITIATOR_NAME=testapi
   MPESA_ENVIRONMENT=sandbox
   
   # Flutterwave (Update with your credentials)
   FLUTTERWAVE_PUBLIC_KEY=your-key
   FLUTTERWAVE_SECRET_KEY=your-secret
   FLUTTERWAVE_ENCRYPTION_KEY=your-key
   
   # Other
   LOGIN_OTP_REQUIRED=true
   LOG_LEVEL=INFO
   ```

5. Click "Create Web Service"
6. Wait for deployment (5-10 minutes)
7. **Check logs** - You should see:
   ```
   Running database migrations...
   Seeding admin user...
   ✓ Admin user created successfully
   Build completed successfully!
   ```
8. **Copy your backend URL**: `https://palspay-backend.onrender.com`

**Admin Login Credentials:**
- Email: `kiplangatkevin335@gmail.com`
- Password: `bd2876qwac`

---

## 🌐 Frontend Deployment (Vercel)

### Step 1: Create Vercel Account
1. Go to https://vercel.com
2. Sign up with GitHub
3. Import your repository

### Step 2: Deploy Frontend
1. Click "Add New" → "Project"
2. Import `Pals-pay` repository
3. Configure:
   - **Framework Preset**: Vite
   - **Root Directory**: `frontend`
   - **Build Command**: `npm run build`
   - **Output Directory**: `dist`

4. **Add Environment Variables**:
   ```
   VITE_API_BASE_URL=https://palspay-backend.onrender.com/api/v1
   VITE_APP_NAME=PalsPay
   VITE_APP_ENV=production
   ```

5. Click "Deploy"
6. Wait for deployment (2-3 minutes)
7. **Copy your frontend URL**: `https://palspay.vercel.app`

### Step 3: Update Backend CORS
1. Go back to Render dashboard
2. Open your backend service
3. Go to "Environment"
4. Update `CORS_ORIGINS`:
   ```
   CORS_ORIGINS=https://palspay.vercel.app,https://www.palspay.vercel.app
   ```
5. Save changes (will trigger redeploy)

---

## ✅ Post-Deployment Checklist

### Backend
- [ ] Database connected successfully
- [ ] Migrations ran successfully
- [ ] Health check endpoint works: `https://palspay-backend.onrender.com/`
- [ ] API endpoints responding
- [ ] Environment variables set correctly
- [ ] Logs show no errors

### Frontend
- [ ] Site loads correctly
- [ ] Can access login/signup pages
- [ ] API calls working
- [ ] No console errors
- [ ] Logo displays correctly
- [ ] Responsive on mobile

### Integration
- [ ] Frontend can connect to backend
- [ ] Login/signup works
- [ ] JWT tokens working
- [ ] CORS configured correctly
- [ ] M-Pesa callbacks reachable (test with ngrok first)

---

## 🔧 Testing Production

### Test Backend API
```bash
# Health check
curl https://palspay-backend.onrender.com/

# Test auth endpoint
curl https://palspay-backend.onrender.com/api/v1/auth/countries
```

### Test Frontend
1. Visit: https://palspay.vercel.app
2. Try signup
3. Try login
4. Check wallet page
5. Test transactions

---

## 🐛 Troubleshooting

### Backend Issues
- **500 Error**: Check Render logs for Python errors
- **Database Error**: Verify DATABASE_URL is correct
- **Migration Failed**: Run manually: `flask db upgrade`
- **CORS Error**: Update CORS_ORIGINS with frontend URL

### Frontend Issues
- **API Error**: Check VITE_API_BASE_URL is correct
- **Blank Page**: Check browser console for errors
- **Build Failed**: Check Node version (use 18+)

### Common Fixes
```bash
# Backend: View logs
# Go to Render dashboard → Your service → Logs

# Frontend: Redeploy
# Go to Vercel dashboard → Your project → Deployments → Redeploy
```

---

## 🔐 Security Notes

1. **Never commit .env files**
2. **Use strong SECRET_KEY and JWT_SECRET_KEY**
3. **Enable HTTPS only** (both platforms do this automatically)
4. **Update M-Pesa callback URLs** to production URLs
5. **Set DEBUG=False** in production
6. **Monitor logs** for suspicious activity

---

## 💰 Cost Estimate

### Free Tier Limits
- **Render**: 750 hours/month (enough for 1 service)
- **Vercel**: Unlimited deployments, 100GB bandwidth
- **PostgreSQL**: 1GB storage, 97 hours/month

### Upgrade When Needed
- Render: $7/month (keeps service always on)
- Vercel: $20/month (more bandwidth, custom domains)
- Database: $7/month (always on, more storage)

---

## 📞 Support

- Render Docs: https://render.com/docs
- Vercel Docs: https://vercel.com/docs
- Issues: Check logs first, then contact support

---

**Ready to deploy? Start with Step 1 of Backend Deployment!**
