# MQTT Broker Setup and Configuration Guide

## Overview

This emergency response system now uses **Mosquitto MQTT broker** for efficient, scalable messaging between the backend and service providers. MQTT provides:

- **Better scalability** for multiple concurrent services
- **Quality of Service (QoS)** levels for reliable message delivery
- **Reduced server load** with pub/sub pattern
- **Lower bandwidth** usage compared to WebSocket for some scenarios

## Architecture

### Hybrid Messaging System
- **MQTT**: Backend ↔ Service Providers (hospitals, fire stations, police)
- **WebSocket (Socket.IO)**: Backend ↔ Web Users (emergency request creators)

This hybrid approach provides the best of both worlds: efficient MQTT for backend services and easy WebSocket integration for web browsers.

## Prerequisites

- Docker and Docker Compose (recommended) **OR** Mosquitto installed locally
- Python 3.8+
- Existing emergency response system setup

## Installation Options

### Option 1: Docker (Recommended)

1. **Start Mosquitto broker using Docker Compose:**

```bash
cd emergency-response-system
docker-compose up -d mosquitto
```

2. **Verify broker is running:**

```bash
docker ps | grep mosquitto
```

You should see the container running on ports 1883 (MQTT) and 9001 (WebSocket MQTT).

3. **View broker logs:**

```bash
docker-compose logs -f mosquitto
```

### Option 2: Local Installation (Windows)

1. **Download Mosquitto:**
   - Visit: https://mosquitto.org/download/
   - Download Windows installer
   - Install to default location

2. **Configure Mosquitto:**
   - Copy `mosquitto/config/mosquitto.conf` to Mosquitto installation directory
   - Or use the provided config directly

3. **Start Mosquitto:**

```cmd
mosquitto -c mosquitto/config/mosquitto.conf -v
```

### Option 3: Local Installation (Linux/Mac)

```bash
# Install Mosquitto
sudo apt-get install mosquitto mosquitto-clients  # Ubuntu/Debian
brew install mosquitto  # macOS

# Start with custom config
mosquitto -c mosquitto/config/mosquitto.conf -v
```

## Configuration

### Mosquitto Configuration File

Located at: `mosquitto/config/mosquitto.conf`

Key settings:
```conf
# MQTT Protocol
listener 1883
protocol mqtt
allow_anonymous true

# WebSocket Protocol (optional, for web-based MQTT clients)
listener 9001
protocol websockets
allow_anonymous true

# Persistence
persistence true
persistence_location /mosquitto/data/

# Logging
log_dest file /mosquitto/log/mosquitto.log
log_type all
```

### Backend Configuration

Located at: `3_BACKEND/app/config.py`

```python
# MQTT settings
MQTT_BROKER_HOST: str = "localhost"  # Change to Docker container name if using Docker
MQTT_BROKER_PORT: int = 1883
MQTT_WEBSOCKET_PORT: int = 9001
MQTT_KEEPALIVE: int = 60
```

### Environment Variables

Create/update `.env` file:

```env
MQTT_BROKER_HOST=localhost
MQTT_BROKER_PORT=1883
MQTT_WEBSOCKET_PORT=9001
```

## MQTT Topics Structure

The system uses the following topic hierarchy:

### Request Topics
- `emergency/requests/new/{service_type}`
  - `emergency/requests/new/ambulance` - New ambulance requests
  - `emergency/requests/new/fire` - New fire requests
  - `emergency/requests/new/police` - New police requests

### Assignment Topics
- `emergency/requests/assigned/{request_id}` - Request assignment notifications
- `emergency/requests/reserve/{request_id}` - Reserve/standby notifications

### Service Topics
- `emergency/services/status/{service_id}` - Service-specific notifications

### System Topics
- `emergency/system/broadcast` - System-wide announcements

## Database Schema Updates

Run the schema update to support reserve services:

```bash
# Connect to PostgreSQL
psql -U emergency_app -d emergency_response

# Run the update script
\i 2_DATABASE/postgis/5_update_schema_for_reserve.sql
```

This adds support for `reserve` and `canceled` response types in the `service_responses` table.

## Python Dependencies

Install required Python package:

```bash
pip install paho-mqtt==2.1.0
```

Or use the updated `requirements.txt`:

```bash
pip install -r requirements.txt
```

## Starting the System

### Full System Startup (Docker)

```bash
# Start all services
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f
```

### Manual Startup

1. **Start Mosquitto:**
```bash
docker-compose up -d mosquitto
# OR
mosquitto -c mosquitto/config/mosquitto.conf -v
```

2. **Start Backend:**
```bash
cd 3_BACKEND
python -m uvicorn app.main:sio_app --reload --host 0.0.0.0 --port 8000
```

3. **Access Frontend:**
- User Interface: http://localhost:8000/user/
- Service Dashboard: http://localhost:8000/service/

## Testing MQTT Connection

### Using mosquitto_sub (Subscribe to test)

```bash
# Subscribe to all emergency requests
mosquitto_sub -h localhost -t "emergency/#" -v

# Subscribe to specific request type
mosquitto_sub -h localhost -t "emergency/requests/new/ambulance" -v
```

### Using mosquitto_pub (Publish test message)

```bash
# Publish test message
mosquitto_pub -h localhost -t "emergency/system/broadcast" -m '{"test": "message"}'
```

### Using Python Script

```python
import paho.mqtt.client as mqtt
import json

def on_connect(client, userdata, flags, rc):
    print(f"Connected with result code {rc}")
    client.subscribe("emergency/#")

def on_message(client, userdata, msg):
    print(f"Topic: {msg.topic}")
    print(f"Message: {msg.payload.decode()}")

client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

client.connect("localhost", 1883, 60)
client.loop_forever()
```

## Health Checking

Check system health via API:

```bash
curl http://localhost:8000/health
```

Expected response:
```json
{
  "status": "healthy",
  "database_connected": true,
  "mongodb_connected": true,
  "mqtt_connected": true,
  "version": "1.0.0"
}
```

## Troubleshooting

### MQTT Broker Not Connecting

1. **Check if broker is running:**
```bash
docker ps | grep mosquitto
# OR
netstat -an | grep 1883
```

2. **Check broker logs:**
```bash
docker-compose logs mosquitto
# OR
tail -f mosquitto/log/mosquitto.log
```

3. **Test connection:**
```bash
mosquitto_sub -h localhost -p 1883 -t test/topic -v
```

### Backend Not Connecting to MQTT

1. **Check backend logs** for MQTT connection errors
2. **Verify MQTT_BROKER_HOST** in config (use `mosquitto` if using Docker, `localhost` if local)
3. **Check firewall** - ensure port 1883 is open
4. **Restart backend** after changing config

### Messages Not Being Received

1. **Check topic subscriptions** - verify service is subscribed to correct topics
2. **Check QoS levels** - default is QoS 1 (at least once delivery)
3. **Check broker logs** for message delivery info
4. **Verify service is registered** via WebSocket first

## Security Considerations (Production)

For production deployment, update `mosquitto.conf`:

```conf
# Disable anonymous access
allow_anonymous false

# Add authentication
password_file /mosquitto/config/passwd

# Enable TLS
listener 8883
cafile /mosquitto/certs/ca.crt
certfile /mosquitto/certs/server.crt
keyfile /mosquitto/certs/server.key
```

Create password file:
```bash
mosquitto_passwd -c mosquitto/config/passwd admin
```

## Performance Tuning

For high-traffic scenarios, adjust in `mosquitto.conf`:

```conf
# Increase max connections
max_connections 1000

# Increase message queue
max_queued_messages 10000

# Increase inflight messages
max_inflight_messages 100

# Adjust persistence frequency
autosave_interval 300
```

## Monitoring

### Monitor Active Connections

```bash
# View connected clients
docker exec -it emergency_mqtt_broker mosquitto_sub -h localhost -t '$SYS/#' -v
```

### Monitor Message Flow

```bash
# Subscribe to all emergency topics
mosquitto_sub -h localhost -t 'emergency/#' -v
```

### System Statistics

MQTT provides system stats on `$SYS` topics:
- `$SYS/broker/clients/connected` - Number of connected clients
- `$SYS/broker/messages/received` - Total messages received
- `$SYS/broker/messages/sent` - Total messages sent
- `$SYS/broker/load/messages/received/1min` - Message rate

## Additional Resources

- [Mosquitto Documentation](https://mosquitto.org/documentation/)
- [Paho MQTT Python Client](https://www.eclipse.org/paho/index.php?page=clients/python/index.php)
- [MQTT Protocol Specification](http://docs.oasis-open.org/mqtt/mqtt/v3.1.1/mqtt-v3.1.1.html)