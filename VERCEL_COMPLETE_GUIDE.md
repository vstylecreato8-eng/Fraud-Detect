# Complete Vercel Deployment Guide - Fraud Guard

This guide walks you through deploying Fraud Guard completely to Vercel with both frontend and backend working together.

---

## Part 1: Prepare Your GitHub Repository

### Step 1.1: Ensure code is committed and pushed
```powershell
cd "d:\Semester 3\Kecerdasan Buatan\transact-safe-check-main"
git status
git add .
git commit -m "Ready for Vercel deployment"
git push origin main
```

✅ Verify: Go to https://github.com/jojowilliam707-create/Fraud-Guard-Detection → You should see all latest changes

---

## Part 2: Deploy Frontend on Vercel

### Step 2.1: Sign in to Vercel
1. Go to https://vercel.com
2. Click **Sign Up** or **Sign In**
3. Select **Continue with GitHub**
4. Authorize Vercel to access your GitHub repositories

### Step 2.2: Import Your Project
1. After signing in, click **Add New** → **Project**
2. Click **Import Git Repository**
3. Paste your repo URL: `https://github.com/jojowilliam707-create/Fraud-Guard-Detection`
4. Click **Continue**

### Step 2.3: Configure Build Settings
You should see auto-detected settings:
- **Framework Preset:** Vite ✅
- **Build Command:** `npm run build` ✅
- **Output Directory:** `dist` ✅
- **Install Command:** `npm install` ✅

✅ These are correct! Don't change them.

### Step 2.4: Add Environment Variables
Before deploying, add the API URL:

1. Scroll down to **Environment Variables**
2. Click **Add**
3. Fill in:
   - **Name:** `VITE_API_URL`
   - **Value:** `http://localhost:5000` (temporary, we'll update this later)
4. Click **Add**
5. Click **Deploy**

⏳ Wait 2-5 minutes for deployment to complete

✅ You'll get a Vercel URL like: `https://fraud-guard-detection.vercel.app`

### Step 2.5: Verify Frontend Deployed
1. Click the Vercel URL
2. You should see the Fraud Guard app loaded
3. (API will fail at this point - that's normal, we'll fix it next)

---

## Part 3: Deploy Backend on Railway (or Similar Service)

Railway is free, easy, and works perfectly with Flask. Here's how:

### Step 3.1: Create Railway Account
1. Go to https://railway.app
2. Click **Login** → **Login with GitHub**
3. Authorize Railway

### Step 3.2: Create New Project
1. Click **New Project**
2. Select **Deploy from GitHub repo**
3. Search and select: `Fraud-Guard-Detection`
4. Click **Deploy**

⏳ Railway will auto-detect Python and deploy

### Step 3.3: Configure Railway Environment Variables
1. In Railway dashboard, click your project
2. Go to **Variables** tab
3. Add these variables:
   ```
   FLASK_ENV=production
   FLASK_HOST=0.0.0.0
   FLASK_PORT=5000
   ```
4. Click **Save**

### Step 3.4: Get Your Backend URL
1. In Railway, go to **Settings** tab
2. Look for **Domains** section
3. Click **Generate Domain**
4. Copy the URL (looks like: `https://fraud-guard-api-production.up.railway.app`)
5. **Save this URL!** You'll need it next

⏳ Wait for deployment to complete (2-3 minutes)

### Step 3.5: Test Backend is Working
1. Open your Railway URL in browser
2. Add `/api/health` to the end
3. Example: `https://fraud-guard-api-production.up.railway.app/api/health`
4. You should see: `{"status": "healthy", "model_loaded": true, ...}`

✅ Backend is deployed!

---

## Part 4: Connect Frontend to Backend

### Step 4.1: Update Vercel Environment Variable
1. Go back to https://vercel.com
2. Select your **Fraud-Guard-Detection** project
3. Go to **Settings** → **Environment Variables**
4. Find `VITE_API_URL`
5. Change the value from `http://localhost:5000` to your Railway URL
   - Example: `https://fraud-guard-api-production.up.railway.app`
6. Click **Save** or **Update**

### Step 4.2: Redeploy Frontend
1. Go to **Deployments** tab
2. Click the latest deployment (at the top)
3. Click **Redeploy**
4. Wait 1-2 minutes for rebuild

✅ Frontend now knows where backend is!

### Step 4.3: Test End-to-End
1. Open your Vercel URL
2. Try uploading a CSV file or entering transaction data
3. Click **Predict**
4. You should see fraud prediction results
5. No "Failed to fetch" error! 🎉

---

## Part 5: Troubleshooting

### Issue: Still Getting "Failed to Fetch"

**Check 1: Verify backend URL is correct**
```
Open in browser: https://your-railway-url/api/health
Should see JSON response, not error
```

**Check 2: Check Vercel environment variable**
1. Vercel → Settings → Environment Variables
2. Make sure `VITE_API_URL` matches your Railway URL exactly
3. Redeploy after changing

**Check 3: Check Railway logs**
1. Railway dashboard → Your project
2. Click **Logs** tab
3. Look for errors (usually model loading issues)

**Check 4: Verify model file is in GitHub**
```powershell
cd "d:\Semester 3\Kecerdasan Buatan\transact-safe-check-main"
git ls-files | findstr model
```
Should show: `model/Credit.pickle`

If not, push it:
```powershell
git add model/Credit.pickle
git commit -m "Add model file for Railway deployment"
git push origin main
```

### Issue: Model Not Loading on Railway

Railway may not have the model file if it's in .gitignore.

**Solution:** Create a Railway build script

1. Create file: `build.sh` in root directory
```bash
#!/bin/bash
pip install -r requirements.txt
# Model will be downloaded or copied
echo "Build complete"
```

2. Or upload model file directly to Railway:
   - Railway dashboard → Variables
   - Add `MODEL_PATH` variable pointing to where model is stored

---

## Summary: What Happens After Deployment

```
User opens Vercel URL
     ↓
Frontend loads (HTML/CSS/JS from Vercel CDN)
     ↓
User uploads CSV or enters transaction
     ↓
Frontend sends request to: https://your-railway-url/api/predict
     ↓
Railway backend receives request
     ↓
Backend loads model and makes prediction
     ↓
Backend returns JSON result
     ↓
Frontend displays fraud prediction 🎉
```

---

## Quick Reference: All URLs You Need

After deployment, you'll have:

| Service | URL | Purpose |
|---------|-----|---------|
| Frontend | https://fraud-guard-detection.vercel.app | User interface |
| Backend | https://fraud-guard-api-*.railway.app | API endpoints |
| Frontend Health Check | https://fraud-guard-detection.vercel.app | Should load app |
| Backend Health Check | https://fraud-guard-api-*.railway.app/api/health | Should return JSON |

---

## Environment Variables Summary

### Vercel Environment Variables
```
VITE_API_URL = https://your-railway-backend-url
```

### Railway Environment Variables
```
FLASK_ENV = production
FLASK_HOST = 0.0.0.0
FLASK_PORT = 5000
```

---

## Important Notes

⚠️ **Model File Size**: If `Credit.pickle` is > 100MB:
- Railway may reject it
- Solution: Compress or use .gitattributes LFS

✅ **CORS**: Already configured in Flask to allow Railway → Vercel communication

✅ **Free Tier**: Both Vercel and Railway offer free tiers (perfect for testing)

---

## Next Steps

1. ✅ Make sure code is pushed to GitHub
2. ✅ Sign up for Railway (free tier is fine)
3. ✅ Deploy to Railway first (backend)
4. ✅ Get Railway URL
5. ✅ Update Vercel environment variable
6. ✅ Redeploy Vercel
7. ✅ Test the deployed app

Your Fraud Guard app will be **live on the internet** and anyone with the Vercel link can use it! 🌐

