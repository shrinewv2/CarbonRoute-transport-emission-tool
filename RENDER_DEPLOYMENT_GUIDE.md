# 🚀 Render Deployment Guide for CarbonRoute

## Prerequisites Checklist
- ✅ GitHub account
- ✅ Render account (free)
- ✅ MongoDB Atlas connection string
- ✅ Google Maps API key

---

## Part 1: YOUR TASKS (What You Need to Do)

### Step 1: Create GitHub Repository

1. Go to https://github.com/new
2. Create a new repository:
   - **Repository name**: `transport-emission-tool` (or any name you prefer)
   - **Visibility**: Public (for free Render deployment)
   - **DO NOT** initialize with README (we already have code)
3. Click "Create repository"
4. **COPY the repository URL** - you'll need this!
   - It will look like: `https://github.com/YOUR_USERNAME/transport-emission-tool.git`

### Step 2: Sign up for Render

1. Go to https://render.com
2. Click "Get Started for Free"
3. **Sign up with GitHub** (this makes deployment easier)
4. Verify your email address

### Step 3: Provide Information

Once you complete Steps 1-2, provide me with:
- ✅ Your GitHub repository URL
- ✅ Confirmation that you've signed up for Render

Then I'll help you with the Git commands and Render configuration!

---

## Part 2: GIT COMMANDS (I'll Help You Run These)

Once you provide the GitHub URL, run these commands:

```bash
# Initialize Git
cd C:\Users\shrir\OneDrive\Desktop\arantree\Transport-emission-tool-main
git init

# Add all files
git add .

# Create first commit
git commit -m "Initial commit: CarbonRoute - Transport Emission Calculator"

# Add your GitHub repository
git remote add origin YOUR_GITHUB_URL_HERE

# Push to GitHub
git branch -M main
git push -u origin main
```

---

## Part 3: RENDER DEPLOYMENT (Step-by-Step)

### A. Deploy Backend (Web Service)

1. **In Render Dashboard**:
   - Click "New +" → "Web Service"
   - Connect your GitHub repository
   - Select the repository you just created

2. **Configure Backend**:
   - **Name**: `carbonroute-backend`
   - **Region**: Choose closest to you (e.g., Singapore, Oregon)
   - **Branch**: `main`
   - **Root Directory**: `backend`
   - **Environment**: `Docker`
   - **Instance Type**: `Free`

3. **Environment Variables** - Click "Add Environment Variable" for each:
   ```
   MONGO_URL = mongodb+srv://shrirengarajan_db_user:TW5vbTKvelkMcteJ@cluster0.kv3r07.mongodb.net/
   DB_NAME = carbonroute
   GOOGLE_MAPS_API_KEY = AIzaSyBJv0JGQimJcxiuv7AP3YlfWLUJqQkEkq0
   CORS_ORIGINS = *
   ```

4. **Click "Create Web Service"**
   - Wait 5-10 minutes for deployment
   - **COPY the backend URL** (e.g., `https://carbonroute-backend.onrender.com`)

### B. Deploy Frontend (Static Site)

1. **In Render Dashboard**:
   - Click "New +" → "Static Site"
   - Connect the SAME GitHub repository

2. **Configure Frontend**:
   - **Name**: `carbonroute-frontend`
   - **Branch**: `main`
   - **Root Directory**: `frontend`
   - **Build Command**: `npm install --legacy-peer-deps && npm run build`
   - **Publish Directory**: `build`

3. **Environment Variables**:
   ```
   REACT_APP_BACKEND_URL = YOUR_BACKEND_URL_FROM_STEP_A
   ```
   Example: `https://carbonroute-backend.onrender.com`

4. **Click "Create Static Site"**
   - Wait 5-10 minutes for deployment
   - **COPY the frontend URL** (e.g., `https://carbonroute-frontend.onrender.com`)

---

## Part 4: UPDATE BACKEND CORS (Important!)

After frontend is deployed:

1. Go back to your **Backend Web Service** in Render
2. Click "Environment"
3. Update `CORS_ORIGINS`:
   ```
   CORS_ORIGINS = https://YOUR_FRONTEND_URL.onrender.com,http://localhost:3000
   ```
4. Click "Save Changes"
5. Render will automatically redeploy

---

## Part 5: UPLOAD LOGO

After deployment:

1. In your GitHub repository, create folder: `frontend/public/assets/`
2. Upload your logo file: `Arantree_logo_upscaled.png`
3. Commit and push:
   ```bash
   git add frontend/public/assets/Arantree_logo_upscaled.png
   git commit -m "Add Arantree logo"
   git push
   ```
4. Render will auto-redeploy with the logo!

---

## 🎯 Summary of URLs You'll Get

After deployment, you'll have:
- **Backend API**: `https://carbonroute-backend.onrender.com`
- **Frontend App**: `https://carbonroute-frontend.onrender.com`
- **Share this URL** with anyone! ↑

---

## ⚠️ Important Notes

### Free Tier Limitations:
- Services sleep after 15 minutes of inactivity
- First request after sleep takes ~30 seconds to wake up
- 750 hours/month of uptime (more than enough!)

### MongoDB Atlas:
- Make sure Network Access allows: `0.0.0.0/0` (all IPs)
- Your connection string is already configured

### Custom Domain (Optional):
If you want a custom domain like `carbonroute.arantree.com`:
1. Buy domain or use existing
2. In Render → Your Static Site → "Custom Domains"
3. Add domain and follow DNS instructions

---

## 🆘 Troubleshooting

### Backend won't start:
- Check Environment Variables are correct
- Check MongoDB connection string
- View logs in Render dashboard

### Frontend shows "Failed to fetch":
- Check CORS_ORIGINS includes frontend URL
- Check backend URL in frontend env variables
- Wait for backend to wake up (if sleeping)

### Logo not showing:
- Check file path: `frontend/public/assets/Arantree_logo_upscaled.png`
- Check file name is exact (case-sensitive)
- Clear browser cache

---

## 📞 Ready to Deploy?

**Your Next Steps:**
1. ✅ Create GitHub repository
2. ✅ Sign up for Render
3. ✅ Provide me with your GitHub URL
4. ✅ I'll help you push the code and configure everything!

Let's get your app live! 🚀
