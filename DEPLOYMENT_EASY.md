# Easy Deployment Guide - Share Your Transport Emission Tool

## Option 1: Ngrok (Easiest - 5 Minutes) ⚡

**Perfect for**: Quick demos, testing, temporary sharing

### Steps:

1. **Download Ngrok**
   - Go to https://ngrok.com/download
   - Download for Windows
   - Extract `ngrok.exe` to any folder

2. **Sign up (Free)**
   - Go to https://dashboard.ngrok.com/signup
   - Get your auth token

3. **Setup Ngrok**
   ```bash
   # In terminal, navigate to where you extracted ngrok.exe
   ngrok config add-authtoken YOUR_AUTH_TOKEN
   ```

4. **Expose Backend**
   ```bash
   ngrok http 8000
   ```
   - Copy the URL (e.g., `https://abc123.ngrok.io`)

5. **Update Frontend .env**
   ```bash
   REACT_APP_BACKEND_URL=https://abc123.ngrok.io
   ```

6. **In a new terminal, expose Frontend**
   ```bash
   ngrok http 3000
   ```
   - Copy this URL and share it!

**Pros**:
- ✅ Free
- ✅ Instant setup
- ✅ HTTPS included
- ✅ Works anywhere

**Cons**:
- ❌ URL changes every time you restart (free plan)
- ❌ Requires keeping your computer running

---

## Option 2: Render (Easy - 15 Minutes) 🌐

**Perfect for**: Permanent hosting, professional sharing

### Steps:

1. **Create GitHub Account** (if you don't have)
   - Go to https://github.com/signup

2. **Push Code to GitHub**
   ```bash
   cd C:\Users\shrir\OneDrive\Desktop\arantree\Transport-emission-tool-main
   git init
   git add .
   git commit -m "Initial commit"
   git branch -M main
   git remote add origin YOUR_GITHUB_REPO_URL
   git push -u origin main
   ```

3. **Sign up for Render**
   - Go to https://render.com
   - Sign up with GitHub

4. **Deploy Backend**
   - Click "New +" → "Web Service"
   - Connect your GitHub repo
   - Settings:
     - **Name**: transport-emission-backend
     - **Environment**: Docker
     - **Dockerfile path**: ./Dockerfile
     - **Instance type**: Free
   - Environment Variables (Add these):
     ```
     MONGO_URL=mongodb+srv://shrirengarajan_db_user:TW5vbTKvelkMcteJ@cluster0.kv3r07.mongodb.net/
     DB_NAME=carbonroute
     GOOGLE_MAPS_API_KEY=AIzaSyBJv0JGQimJcxiuv7AP3YlfWLUJqQkEkq0
     CORS_ORIGINS=*
     ```
   - Click "Create Web Service"
   - Wait ~5 minutes, copy the URL (e.g., `https://transport-emission-backend.onrender.com`)

5. **Deploy Frontend**
   - Click "New +" → "Static Site"
   - Connect same GitHub repo
   - Settings:
     - **Name**: transport-emission-frontend
     - **Branch**: main
     - **Root Directory**: frontend
     - **Build Command**: `npm install --legacy-peer-deps && npm run build`
     - **Publish Directory**: build
   - Environment Variables:
     ```
     REACT_APP_BACKEND_URL=https://your-backend-url.onrender.com
     ```
   - Click "Create Static Site"
   - Wait ~5 minutes, get your public URL!

**Pros**:
- ✅ Free tier available
- ✅ Permanent URLs
- ✅ Auto-deploys from GitHub
- ✅ HTTPS included
- ✅ No computer needed to stay on

**Cons**:
- ❌ Free tier sleeps after 15 min of inactivity (wakes up in ~30 seconds)
- ❌ Requires GitHub account

---

## Option 3: Railway (Easy - 15 Minutes) 🚂

**Perfect for**: Quick deployment, better performance than Render

### Steps:

1. **Sign up for Railway**
   - Go to https://railway.app
   - Sign up with GitHub

2. **Create New Project**
   - Click "New Project"
   - Select "Deploy from GitHub repo"
   - Choose your repo

3. **Add MongoDB URL to Environment**
   ```
   MONGO_URL=mongodb+srv://shrirengarajan_db_user:TW5vbTKvelkMcteJ@cluster0.kv3r07.mongodb.net/
   DB_NAME=carbonroute
   GOOGLE_MAPS_API_KEY=AIzaSyBJv0JGQimJcxiuv7AP3YlfWLUJqQkEkq0
   ```

4. **Get Your Public URL**
   - Railway auto-detects and deploys
   - Click on the deployment to get public URL

**Pros**:
- ✅ $5 free credit/month
- ✅ Better uptime than Render
- ✅ Faster cold starts
- ✅ Automatic HTTPS

**Cons**:
- ❌ Requires credit card for free tier
- ❌ Limited free credits

---

## Option 4: Vercel + Railway (Recommended - 20 Minutes) ⭐

**Perfect for**: Best free option, production-ready

### Backend (Railway):

1. Sign up at https://railway.app
2. Create new project from GitHub repo
3. Set environment variables (MongoDB, API keys)
4. Get backend URL

### Frontend (Vercel):

1. Sign up at https://vercel.com
2. Click "Add New Project"
3. Import from GitHub
4. Root Directory: `frontend`
5. Build Command: `npm run build`
6. Environment Variables:
   ```
   REACT_APP_BACKEND_URL=https://your-railway-backend-url
   ```
7. Deploy!

**Pros**:
- ✅ Completely free
- ✅ Excellent performance
- ✅ Auto-deploys from GitHub
- ✅ Best uptime
- ✅ Custom domain support

**Cons**:
- ❌ Requires 2 separate deployments

---

## Quick Comparison

| Service | Time | Free Tier | Uptime | Best For |
|---------|------|-----------|--------|----------|
| **Ngrok** | 5 min | Yes | While PC on | Quick demos |
| **Render** | 15 min | Yes | Sleeps after 15 min | Simple deploy |
| **Railway** | 15 min | $5/month | Good | Better performance |
| **Vercel + Railway** | 20 min | Yes | Excellent | Production use |

---

## My Recommendation:

### For immediate sharing (today):
**Use Ngrok** - Takes 5 minutes, anyone can access immediately

### For permanent hosting (share forever):
**Use Vercel (frontend) + Railway (backend)** - Best free option, professional quality

---

## Need Help?

Let me know which option you'd like to use and I can help you set it up step by step!
