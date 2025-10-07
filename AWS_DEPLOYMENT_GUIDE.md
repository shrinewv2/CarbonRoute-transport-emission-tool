# AWS CI/CD Deployment Guide for CarbonRoute

## Overview
This guide will help you deploy the CarbonRoute application to AWS with automatic CI/CD pipeline that deploys changes within 5-8 minutes of pushing to GitHub.

## Architecture
- **Frontend**: AWS Amplify (React app)
- **Backend**: AWS Elastic Beanstalk (FastAPI)
- **Database**: MongoDB Atlas (already configured)
- **CI/CD**: GitHub → AWS (auto-deploy on push)

---

## Prerequisites

### 1. AWS Account Setup
- Create AWS account at https://aws.amazon.com
- Set up IAM user with permissions:
  - `AWSElasticBeanstalkFullAccess`
  - `AmplifyFullAccess`
  - `IAMFullAccess`

### 2. Install AWS CLI
```bash
# Windows
msiexec.exe /i https://awscli.amazonaws.com/AWSCLIV2.msi

# Configure AWS CLI
aws configure
# Enter: AWS Access Key ID, Secret Access Key, Region (us-east-1)
```

### 3. Install EB CLI
```bash
pip install awsebcli
```

### 4. GitHub Repository
- Create new repository on GitHub
- We'll push code in next steps

---

## Step 1: Push Code to GitHub (5 minutes)

```bash
# Initialize git (already done)
git add .
git commit -m "Prepare for AWS deployment with CI/CD pipeline"

# Create GitHub repo (do this on GitHub.com first)
# Then connect:
git remote add origin https://github.com/YOUR_USERNAME/carbonroute.git
git branch -M main
git push -u origin main
```

---

## Step 2: Deploy Backend to Elastic Beanstalk (20 minutes)

### A. Initialize Elastic Beanstalk

```bash
cd backend
eb init

# Follow prompts:
# - Select region: us-east-1
# - Application name: carbonroute-backend
# - Platform: Python 3.11
# - Do you want to set up SSH? Yes
```

### B. Create Environment

```bash
eb create carbonroute-backend-prod

# This will:
# - Create EC2 instance
# - Install dependencies from requirements.txt
# - Deploy your FastAPI app
# Wait 5-10 minutes for deployment
```

### C. Set Environment Variables

```bash
eb setenv MONGODB_URI="your_mongodb_atlas_connection_string"
eb setenv GOOGLE_MAPS_API_KEY="your_google_maps_api_key"
eb setenv SEAROUTE_API_KEY="your_searoute_api_key"
```

### D. Get Backend URL

```bash
eb status

# Copy the CNAME (e.g., carbonroute-backend-prod.us-east-1.elasticbeanstalk.com)
```

---

## Step 3: Deploy Frontend to AWS Amplify (15 minutes)

### A. Via AWS Console (Easiest)

1. Go to https://console.aws.amazon.com/amplify
2. Click **"New app"** → **"Host web app"**
3. Select **GitHub** as source
4. Authorize AWS Amplify to access your GitHub
5. Select repository: `carbonroute`
6. Select branch: `main`
7. Build settings:
   - Build command: `npm run build`
   - Base directory: `frontend`
   - Output directory: `build`
8. **Advanced settings** → Environment variables:
   ```
   REACT_APP_API_URL=https://YOUR_BACKEND_URL.elasticbeanstalk.com
   ```
9. Click **"Save and deploy"**
10. Wait 5-8 minutes for build

### B. Via AWS CLI (Alternative)

```bash
# Create Amplify app
aws amplify create-app --name carbonroute --repository https://github.com/YOUR_USERNAME/carbonroute

# Connect branch
aws amplify create-branch --app-id YOUR_APP_ID --branch-name main

# Start deployment
aws amplify start-job --app-id YOUR_APP_ID --branch-name main --job-type RELEASE
```

---

## Step 4: Configure Backend CORS (5 minutes)

Update `backend/server.py` to allow your Amplify domain:

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "https://YOUR_AMPLIFY_DOMAIN.amplifyapp.com"  # Add this
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

Commit and push:
```bash
git add backend/server.py
git commit -m "Add Amplify domain to CORS"
git push
```

**Backend auto-deploys in 3-5 minutes!**

---

## Step 5: Update Frontend API URL (5 minutes)

Update `frontend/src/App.js`:

```javascript
const API_URL = process.env.REACT_APP_API_URL || "http://localhost:8000";
```

In AWS Amplify console:
1. Go to your app → **Environment variables**
2. Add:
   ```
   REACT_APP_API_URL=https://YOUR_BACKEND_URL.elasticbeanstalk.com
   ```
3. Click **"Save"**
4. Amplify will auto-rebuild (3-5 minutes)

---

## Step 6: Test Deployment (10 minutes)

1. Open your Amplify URL: `https://YOUR_APP.amplifyapp.com`
2. Test calculator functionality
3. Check dashboard displays data
4. Verify chart rendering

---

## CI/CD Pipeline is Now Active! 🎉

### How It Works:

1. **Make changes locally**
2. **Commit and push to GitHub**:
   ```bash
   git add .
   git commit -m "Update feature"
   git push
   ```
3. **AWS auto-deploys**:
   - Amplify detects push
   - Builds frontend (3-4 min)
   - Elastic Beanstalk deploys backend (2-4 min)
   - Live in **5-8 minutes total**

### Monitoring Deployments:

**Frontend (Amplify)**:
```bash
# Via console
https://console.aws.amazon.com/amplify

# Via CLI
aws amplify list-apps
aws amplify list-jobs --app-id YOUR_APP_ID --branch-name main
```

**Backend (Elastic Beanstalk)**:
```bash
# Via CLI
eb status
eb logs

# Via console
https://console.aws.amazon.com/elasticbeanstalk
```

---

## Cost Estimate (Monthly)

- **Amplify**: $0-5 (free tier covers most traffic)
- **Elastic Beanstalk**: 
  - t3.micro: ~$8-15
  - Load balancer: ~$16
- **MongoDB Atlas**: Free tier (M0)
- **Data transfer**: ~$1-5

**Total: ~$25-40/month**

### Cost Optimization:
- Use t3.micro instance (free tier eligible for 12 months)
- Single instance (not load balanced) for development
- Enable auto-scaling only if needed

---

## Troubleshooting

### Backend not deploying?
```bash
eb logs
# Check for errors in requirements.txt or server.py
```

### Frontend build failing?
- Check Amplify console → Build logs
- Verify `frontend/package.json` scripts
- Ensure all dependencies are in package.json

### CORS errors?
- Add Amplify domain to backend CORS origins
- Redeploy backend: `git push`

### Environment variables not working?
- Amplify: Must start with `REACT_APP_`
- EB: Set via `eb setenv KEY=value`

---

## Commands Reference

### Elastic Beanstalk
```bash
eb status              # Check deployment status
eb logs                # View logs
eb deploy              # Manual deploy
eb setenv KEY=value    # Set environment variable
eb ssh                 # SSH into instance
eb terminate           # Delete environment (careful!)
```

### AWS Amplify
```bash
aws amplify list-apps
aws amplify get-app --app-id YOUR_ID
aws amplify start-job --app-id YOUR_ID --branch-name main --job-type RELEASE
```

### Git Workflow
```bash
git add .
git commit -m "Description"
git push                # Triggers auto-deploy!
```

---

## Next Steps

1. **Custom Domain**: Configure Route 53 for custom domain
2. **SSL Certificate**: AWS Certificate Manager (free)
3. **Monitoring**: CloudWatch for logs and metrics
4. **Backup**: Database backup strategy
5. **Staging Environment**: Create separate branch/environment for testing

---

## Support

- **AWS Documentation**: https://docs.aws.amazon.com
- **Elastic Beanstalk**: https://docs.aws.amazon.com/elasticbeanstalk
- **Amplify**: https://docs.amplify.aws

---

**Deployment Date**: 2025-10-07
**Author**: Arantree Consulting Services
