# Quick Start Guide - MQTT & Reserve Notifications

## 🚀 New Features

Your emergency response system now includes:

1. **Mosquitto MQTT Broker** - Efficient pub/sub messaging for services
2. **Reserve/Standby Notifications** - Backup services stay informed
3. **Enhanced Distance Calculation** - Real road routing for accuracy

## 📋 Prerequisites

- Python 3.8+
- PostgreSQL with PostGIS
- MongoDB
- Docker (optional, recommended for MQTT)

## ⚡ Quick Setup (5 minutes)

### Step 1: Update Dependencies

```bash
cd 3_BACKEND
pip install -r requirements.txt
```

This installs `paho-mqtt==2.1.0` along with existing dependencies.

### Step 2: Start MQTT Broker

**Option A: Docker (Recommended)**
```bash
docker-compose up -d mosquitto
```

**Option B: Local Mosquitto**
```bash
mosquitto -c mosquitto/config/mosquitto.conf -v
```

### Step 3: Update Database Schema

```bash
# Connect to your PostgreSQL database
psql -U emergency_app -d emergency_response

# Run the schema update
\i 2_DATABASE/postgis/5_update_schema_for_reserve.sql

# Exit
\q
```

### Step 4: Start Backend

```bash
cd 3_BACKEND
python -m uvicorn app.main:sio_app --reload --host 0.0.0.0 --port 8000
```

You should see:
```
🚀 Starting Emergency Response System...
📊 PostgreSQL: localhost:5432
📊 MongoDB: localhost:27017
📡 MQTT Broker: localhost:1883
✅ MQTT broker connected
```

### Step 5: Test the System

Open three browser windows:

1. **Service 1**: http://localhost:8000/service/ (Login as Hospital A)
2. **Service 2**: http://localhost:8000/service/ (Login as Hospital B)
3. **User**: http://localhost:8000/user/ (Create emergency request)

## 🧪 Testing Reserve Notifications

### Test Scenario

1. **Login to two services** (e.g., two hospitals)
2. **Create an emergency request** as a user
3. **Both services accept within 2 seconds**
4. **Observe:**
   - Nearest service: "✅ Request assigned to you!"
   - Farther service: "⏸️ Request assigned to [Hospital Name] - You're on reserve"

### Expected Results

**Assigned Service (Nearest):**
```
Status: ✅ Assigned
Distance: 2.5 km
ETA: 8 minutes
```

**Reserve Service (Backup):**
```
Status: ⏸️ RESERVE #1
Handled by: City General Hospital
Your Distance: 3.1 km
Assigned Distance: 2.5 km
Message: You're on reserve/standby
```

## 📊 Verify MQTT is Working

### Check MQTT Connection

```bash
curl http://localhost:8000/health
```

Expected response:
```json
{
  "status": "healthy",
  "database_connected": true,
  "mongodb_connected": true,
  "mqtt_connected": true,  ← Should be true
  "version": "1.0.0"
}
```

### Monitor MQTT Messages

In a separate terminal:

```bash
# Subscribe to all emergency topics
mosquitto_sub -h localhost -t "emergency/#" -v
```

Now create an emergency request - you should see messages flowing:
```
emergency/requests/new/ambulance {"request_id": "REQ-ABC123", ...}
emergency/requests/assigned/REQ-ABC123 {"assigned_service_id": "HOSP-001", ...}
emergency/requests/reserve/REQ-ABC123 {"reserve_service_ids": [...], ...}
```

## 🔧 Configuration

### Change MQTT Broker Host

Edit `3_BACKEND/app/config.py`:

```python
MQTT_BROKER_HOST: str = "localhost"  # or "mosquitto" for Docker
MQTT_BROKER_PORT: int = 1883
```

Or use environment variables in `.env`:
```env
MQTT_BROKER_HOST=localhost
MQTT_BROKER_PORT=1883
```

### Adjust Acceptance Window

Edit `3_BACKEND/app/routers/requests.py` (line ~287):

```python
# Change from 2 seconds to 5 seconds
recent = db.get_recent_accepts(response.request_id, seconds=5)
```

## 📱 Frontend Updates

The service dashboard now shows two sections:

### Pending Requests
- New requests waiting for response
- Accept/Reject buttons
- Real-time updates via WebSocket

### Reserve/Standby
- Requests you accepted but weren't assigned
- Shows which service was assigned
- Distance comparison
- Dismiss button

## 🐛 Troubleshooting

### MQTT Not Connecting

```bash
# Check if Mosquitto is running
docker ps | grep mosquitto

# Check logs
docker-compose logs mosquitto

# Test connection
mosquitto_sub -h localhost -p 1883 -t test/topic
```

### Reserve Notifications Not Showing

1. Clear browser cache and refresh
2. Check browser console for errors
3. Verify WebSocket connection (should show "🟢 Connected")

### Distance Calculation Fails

The system automatically falls back to straight-line distance if OSRM fails. Check logs:

```bash
# Backend logs will show:
INFO - Using OSRM routing for distance calculation
# OR
WARNING - OSRM unavailable, using straight-line distance
```

## 📚 Documentation

For more details, see:

- **[MQTT_SETUP.md](MQTT_SETUP.md)** - Complete MQTT configuration guide
- **[RESERVE_NOTIFICATIONS.md](RESERVE_NOTIFICATIONS.md)** - Reserve system deep dive
- **[README.md](README.md)** - Main project documentation

## 🎯 What's Different?

### Before
1. User creates request
2. Services receive notification
3. First to accept gets assigned
4. Others get "request taken" message

### After
1. User creates request
2. Services receive notification (WebSocket + MQTT)
3. Multiple services can accept within 2-second window
4. **System calculates real distances using road routing**
5. **Nearest service gets assigned**
6. **Other services become reserves with full context**
7. Reserve services stay informed until request completes

## 🚀 Next Steps

1. **Monitor Performance**: Check `/api/stats` endpoint
2. **Analyze Reserve Patterns**: Query reserve services in database
3. **Customize Timeouts**: Adjust 2-second window to your needs
4. **Add Analytics**: Track response times and distances
5. **Scale Up**: Add more MQTT subscribers for increased load

## 💡 Pro Tips

- **Test with real coordinates** in your deployment area
- **Monitor MQTT topics** to understand message flow
- **Keep OSRM routing** enabled for accurate distances
- **Review reserve rates** to optimize service placement
- **Use Docker** for easy MQTT broker management

## ❓ Common Questions

**Q: Do I need to change my existing code?**
A: No! The system is backward compatible. MQTT runs alongside WebSocket.

**Q: What happens if MQTT broker goes down?**
A: WebSocket continues to work. Services still receive notifications.

**Q: Can I use MQTT for user requests too?**
A: The current implementation uses WebSocket for users (better browser support) and MQTT for services (better efficiency).

**Q: How do I disable reserve notifications?**
A: You can't disable them, but services can immediately dismiss reserve notifications in the UI.

**Q: Are distances accurate?**
A: Yes! The system uses OSRM for real road routing, which accounts for actual road networks.

## 📞 Support

For issues or questions:
1. Check logs: `docker-compose logs -f`
2. Verify health: `curl localhost:8000/health`
3. Test MQTT: `mosquitto_sub -h localhost -t "emergency/#"`
4. Review documentation in this repository

---

**Ready to go? Start with Step 1 above! 🎉**