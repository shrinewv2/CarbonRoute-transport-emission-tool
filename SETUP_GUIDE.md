# Transport Emission Tool - Setup Guide

## ✅ Current Status

**Frontend**: Running on http://localhost:3000
**Backend**: Running on http://localhost:8000
**MongoDB**: ⚠️ Not connected (needs setup)

## 🚀 Quick Start Summary

All dependencies are installed and both servers are running! However, you need to set up MongoDB to fully use the application.

## 📋 What's Working

- ✅ Python 3.13.5 installed
- ✅ Node.js v22.19.0 installed
- ✅ Backend dependencies installed
- ✅ Frontend dependencies installed
- ✅ Frontend accessible at http://localhost:3000
- ✅ Backend server running at http://localhost:8000
- ✅ Google Maps API integration (for location search)

## ⚠️ What Needs Setup

### MongoDB Setup (Choose ONE option)

#### Option 1: MongoDB Atlas (Cloud - Easiest, Recommended)

1. Go to https://www.mongodb.com/cloud/atlas/register
2. Create a free account
3. Create a new cluster (choose M0 FREE tier)
4. In Security > Network Access: Add IP Address → "Allow Access from Anywhere" (0.0.0.0/0)
5. In Security > Database Access: Create a database user with username and password
6. Click "Connect" → "Connect your application"
7. Copy the connection string (looks like: `mongodb+srv://<username>:<password>@cluster.mongodb.net/`)
8. Update `backend\.env` file:
   ```
   MONGO_URL=mongodb+srv://<username>:<password>@cluster0.xxxxx.mongodb.net/?retryWrites=true&w=majority
   DB_NAME=carbonroute
   ```
9. Restart the backend server (see commands below)

#### Option 2: Install MongoDB Locally (Windows)

1. Download MongoDB Community Server from: https://www.mongodb.com/try/download/community
2. Install with default settings
3. Start MongoDB service:
   - Open Services (Win+R, type `services.msc`)
   - Find "MongoDB Server" and start it
   OR run: `mongod --dbpath C:\data\db`
4. The backend is already configured for localhost MongoDB
5. Restart the backend server

## 🔧 Managing the Servers

### To Stop Servers:
Press `Ctrl+C` in each terminal window

### To Start Backend:
```bash
cd backend
uvicorn server:app --host 0.0.0.0 --port 8000
```

### To Start Frontend:
```bash
cd frontend
npm start
```

## 📝 Environment Variables

### Backend (.env already created)
Location: `backend\.env`
```
MONGO_URL=mongodb://localhost:27017/  # Change this for MongoDB Atlas
DB_NAME=carbonroute
GOOGLE_MAPS_API_KEY=AIzaSyBJv0JGQimJcxiuv7AP3YlfWLUJqQkEkq0
CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
```

### Frontend (.env already created)
Location: `frontend\.env`
```
REACT_APP_BACKEND_URL=http://localhost:8000
```

## 🧪 Testing the Application

Once MongoDB is connected:

1. Open http://localhost:3000 in your browser
2. The app should load without errors
3. Try creating a new shipment to test the full functionality

## 📚 Features

- **Transport Emission Calculator**: Calculate CO2 emissions for different transport modes
- **Route Planning**: Support for road, rail, air, and water transport
- **GHG Category Tracking**: Upstream, downstream, and company-owned emissions
- **Analytics Dashboard**: View emission trends and cost analysis
- **Multi-modal Transport**: Combine different transport modes in one shipment

## 🌐 AWS Deployment (Optional)

For AWS deployment instructions, see: `deployment/aws-deploy-guide.md`

## 🐛 Troubleshooting

### Backend shows MongoDB connection error
- Ensure MongoDB is running (local) or connection string is correct (Atlas)
- Check firewall settings

### Frontend won't start
- Delete `node_modules` and `package-lock.json`
- Run `npm install --legacy-peer-deps` again

### Port already in use
- Backend: Change port in uvicorn command: `--port 8001`
- Frontend: Set PORT environment variable: `set PORT=3001` (Windows)

## 📞 Support

For issues, check:
- Backend logs in the terminal
- Frontend browser console (F12)
- MongoDB connection status

---

**Next Steps:**
1. Set up MongoDB (choose Atlas for easiest setup)
2. Restart backend after updating MONGO_URL
3. Open http://localhost:3000 and start using the app!
