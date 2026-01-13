# Emergency Response System - Setup Guide

This guide will help you set up and run the Emergency Response System on your local machine.

---

## 📋 Table of Contents

1. [Prerequisites](#prerequisites)
2. [Database Setup](#database-setup)
3. [Backend Setup](#backend-setup)
4. [Frontend Setup](#frontend-setup)
5. [Running the Application](#running-the-application)
6. [Testing the System](#testing-the-system)
7. [Troubleshooting](#troubleshooting)

---

## ✅ Prerequisites

Before you begin, ensure you have the following installed:

### Required Software

| Software | Version | Download Link |
|----------|---------|---------------|
| **Python** | 3.9+ | https://www.python.org/downloads/ |
| **PostgreSQL** | 14+ | https://www.postgresql.org/download/ |
| **PostGIS Extension** | 3.x | Included with PostgreSQL installer |
| **MongoDB** | 6.0+ | https://www.mongodb.com/try/download/community |
| **Mosquitto MQTT Broker** | 2.x | https://mosquitto.org/download/ |
| **Web Browser** | Latest | Chrome, Firefox, or Edge |

### Verify Installations

```bash
# Check Python version
python --version

# Check PostgreSQL
psql --version

# Check MongoDB
mongod --version

# Check Mosquitto
mosquitto -h
```

---

## 🗄️ Database Setup

### Step 1: Start PostgreSQL

```bash
# Windows
# PostgreSQL should start automatically as a service
# Or manually start via Services app

# Linux/Mac
sudo systemctl start postgresql
```

### Step 2: Create PostgreSQL Database with PostGIS

```bash
# Login to PostgreSQL
psql -U postgres

# Create database
CREATE DATABASE emergency_response;

# Connect to the database
\c emergency_response

# Enable PostGIS extension
CREATE EXTENSION postgis;

# Verify PostGIS installation
SELECT PostGIS_Version();

# Exit
\q
```

### Step 3: Start MongoDB

```bash
# Windows
# MongoDB should start automatically as a service
# Or run manually:
mongod --dbpath "C:\data\db"

# Linux/Mac
sudo systemctl start mongod
```

### Step 4: Start Mosquitto MQTT Broker

```bash
# Windows
# Open Command Prompt as Administrator
mosquitto -v

# Linux/Mac
sudo systemctl start mosquitto

# Or run manually
mosquitto -v
```

**Note**: Keep Mosquitto running in a separate terminal window.

---

## 🔧 Backend Setup

### Step 1: Navigate to Backend Directory

```bash
cd emergency-response-system/3_BACKEND
```

### Step 2: Create Virtual Environment

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

### Step 3: Install Python Dependencies

```bash
# Install all required packages
pip install -r requirements.txt
```

**Required packages** (automatically installed):
- fastapi
- uvicorn
- psycopg2-binary
- pymongo
- paho-mqtt
- python-jose[cryptography]
- passlib[bcrypt]
- python-multipart
- python-socketio
- httpx

### Step 4: Configure Database Connection

Edit `app/config.py` if needed (default settings should work):

```python
# PostgreSQL Configuration
POSTGRES_HOST = "localhost"
POSTGRES_PORT = 5432
POSTGRES_DB = "emergency_response"
POSTGRES_USER = "postgres"
POSTGRES_PASSWORD = "your_password_here"  # Change this!

# MongoDB Configuration
MONGODB_URL = "mongodb://localhost:27017"
MONGODB_DB = "emergency_response"

# MQTT Configuration
MQTT_BROKER = "localhost"
MQTT_PORT = 1883
```

### Step 5: Initialize Database Schema

```bash
# Run the main application (it will create tables automatically)
python main.py
```

**Note**: On first run, the application will:
- Create all necessary PostgreSQL tables
- Set up spatial indexes for location queries
- Initialize MongoDB collections

Press `Ctrl+C` to stop after seeing "Application startup complete".

---

## 🌐 Frontend Setup

### Step 1: Navigate to Frontend Directory

```bash
cd emergency-response-system/4_FRONTEND
```

### Step 2: Start Python HTTP Server

The frontend is a static web application that requires a simple HTTP server.

```bash
# Start server on port 3000
python -m http.server 3000
```

**Alternative**: If port 3000 is busy:

```bash
# Use a different port
python -m http.server 8080
```

**Note**: Keep the HTTP server running in a separate terminal window.

---

## 🚀 Running the Application

You need **4 terminal windows** running simultaneously:

### Terminal 1: Mosquitto MQTT Broker

```bash
mosquitto -v
```

**Expected output**:
```
1234567890: mosquitto version 2.x starting
1234567890: Opening ipv4 listen socket on port 1883
```

### Terminal 2: Backend API Server

```bash
cd emergency-response-system/3_BACKEND
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac
python main.py
```

**Expected output**:
```
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### Terminal 3: Frontend HTTP Server

```bash
cd emergency-response-system/4_FRONTEND
python -m http.server 3000
```

**Expected output**:
```
Serving HTTP on :: port 3000 (http://[::]:3000/) ...
```

### Terminal 4: MongoDB (if not running as service)

```bash
mongod --dbpath "C:\data\db"
```

**Note**: If MongoDB is running as a Windows service, you can skip this terminal.

---

## 🧪 Testing the System

### Step 1: Access the Application

Open your web browser and navigate to:

| Interface | URL |
|-----------|-----|
| **User Interface** (Citizens) | http://localhost:3000/4_FRONTEND/user/index.html |
| **Service Provider Interface** | http://localhost:3000/4_FRONTEND/service/login.html |
| **API Documentation** | http://localhost:8000/docs |

### Step 2: Register a Service Provider

1. Go to: http://localhost:3000/4_FRONTEND/service/register.html
2. Fill in the registration form:
   - **Service Name**: Kwong Wah Hospital
   - **Service Type**: Hospital
   - **Email**: hospital@test.com
   - **Password**: test123456
   - **Phone**: +852 1234 5678
   - **Address**: Hong Kong
   - **Latitude**: 22.31428962
   - **Longitude**: 114.17210018
   - **Available Units**: 5

3. Click **Register**
4. You will be automatically logged in

### Step 3: Test Emergency Request (User Interface)

1. Open a new browser window/tab
2. Go to: http://localhost:3000/4_FRONTEND/user/index.html
3. Click **"Share My Location"** or click anywhere on the map
4. Click one of the emergency buttons:
   - 🚑 **Medical Emergency** (Ambulance)
   - 🚒 **Fire Emergency**
   - 🚓 **Police Emergency**

### Step 4: Accept Request (Service Provider Interface)

1. In the service provider dashboard, you should see a notification for the new request
2. Click **"Accept"** button
3. **Route visualization** will appear showing:
   - Colored route path from service to user
   - Animated vehicle (ambulance/fire truck/police car) traveling along the route
   - Route takes 45 seconds to complete

### Step 5: View Animation on User Interface

1. On the user interface, you will see:
   - Route path displayed
   - Animated vehicle traveling toward your location
   - Request status updated to "Validated"

---

## 🔍 Troubleshooting

### Issue 1: Backend won't start

**Error**: `ModuleNotFoundError: No module named 'fastapi'`

**Solution**:
```bash
# Ensure virtual environment is activated
venv\Scripts\activate
pip install -r requirements.txt
```

### Issue 2: PostgreSQL connection failed

**Error**: `psycopg2.OperationalError: could not connect to server`

**Solution**:
1. Check if PostgreSQL is running:
   ```bash
   # Windows - Check services
   services.msc
   # Look for "postgresql-x64-14" and ensure it's running
   ```

2. Verify credentials in `app/config.py`
3. Test connection:
   ```bash
   psql -U postgres -d emergency_response
   ```

### Issue 3: MongoDB connection failed

**Error**: `pymongo.errors.ServerSelectionTimeoutError`

**Solution**:
```bash
# Start MongoDB
mongod --dbpath "C:\data\db"

# Or check Windows service
services.msc  # Look for MongoDB
```

### Issue 4: Mosquitto MQTT not working

**Error**: `Connection refused` or MQTT messages not received

**Solution**:
```bash
# Kill any existing Mosquitto processes
taskkill /F /IM mosquitto.exe  # Windows
# pkill mosquitto  # Linux/Mac

# Start fresh
mosquitto -v
```

### Issue 5: Frontend shows "Failed to fetch"

**Error**: Network errors when clicking emergency buttons

**Solution**:
1. Verify backend is running on port 8000
2. Check browser console for CORS errors
3. Ensure you're accessing via `http://localhost:3000`, not `file://`

### Issue 6: Route animation not appearing

**Error**: No route or car animation after accepting request

**Solution**:
1. Clear browser cache (Ctrl+Shift+R)
2. Check browser console for JavaScript errors
3. Verify `route-animation.js` is loaded:
   ```javascript
   // Open browser console and type:
   typeof showRouteAndAnimate
   // Should return "function"
   ```

### Issue 7: Service location not showing on map

**Error**: Service provider marker missing on dashboard

**Solution**:
1. Logout and login again to refresh coordinates
2. Check browser console for coordinate values:
   ```javascript
   console.log(localStorage.getItem('serviceLat'))
   console.log(localStorage.getItem('serviceLng'))
   ```
3. Ensure coordinates are valid numbers, not "NaN"

---

## 📊 Verification Checklist

Use this checklist to verify everything is working:

- [ ] PostgreSQL is running and PostGIS is enabled
- [ ] MongoDB is running
- [ ] Mosquitto MQTT broker is running (port 1883)
- [ ] Backend API is running (http://localhost:8000)
- [ ] Frontend HTTP server is running (http://localhost:3000)
- [ ] Service provider can register and login
- [ ] Service provider sees their location marker on dashboard
- [ ] User can set location on map
- [ ] User can create emergency requests
- [ ] Service provider receives real-time notifications
- [ ] Service provider can accept requests
- [ ] Route visualization appears on both interfaces
- [ ] Car animation travels from service to user location
- [ ] Animation completes at exact user location

---

## 🎯 Quick Start (Summary)

```bash
# Terminal 1: Start Mosquitto
mosquitto -v

# Terminal 2: Start Backend
cd 3_BACKEND
venv\Scripts\activate
python main.py

# Terminal 3: Start Frontend
cd 4_FRONTEND
python -m http.server 3000

# Browser: Open application
# User: http://localhost:3000/4_FRONTEND/user/index.html
# Service: http://localhost:3000/4_FRONTEND/service/login.html
```

---

## 📞 Support

If you encounter issues not covered in this guide:

1. Check the browser console (F12) for JavaScript errors
2. Check backend logs in the terminal running `python main.py`
3. Verify all services are running: PostgreSQL, MongoDB, Mosquitto
4. Review the `DOCUMENTATION.md` file for architecture details

---

## 🔄 Stopping the Application

To properly shut down the system:

1. **Stop Frontend**: Press `Ctrl+C` in Terminal 3
2. **Stop Backend**: Press `Ctrl+C` in Terminal 2
3. **Stop Mosquitto**: Press `Ctrl+C` in Terminal 1
4. **Stop MongoDB** (if running manually): Press `Ctrl+C` in Terminal 4

---

**Last Updated**: December 2024
**Version**: 1.0.0