# Emergency Response System - Complete Documentation

A comprehensive real-time emergency response system that connects citizens with emergency services (hospitals, fire stations, police stations) using geospatial technology, WebSocket communication, and MQTT messaging.

---

## 📋 Table of Contents

1. [Project Overview](#project-overview)
2. [System Architecture](#system-architecture)
3. [Technology Stack](#technology-stack)
4. [Database Design](#database-design)
5. [Backend Architecture](#backend-architecture)
6. [Frontend Architecture](#frontend-architecture)
7. [Communication Mechanisms](#communication-mechanisms)
8. [Core Features](#core-features)
9. [API Endpoints](#api-endpoints)
10. [Security](#security)
11. [Geospatial Features](#geospatial-features)
12. [Real-time Updates](#real-time-updates)
13. [Route Visualization](#route-visualization)
14. [FIFO Assignment Algorithm](#fifo-assignment-algorithm)
15. [Data Flow](#data-flow)
16. [Code Structure](#code-structure)

---

## 🎯 Project Overview

### Purpose

The Emergency Response System is a real-time geospatial application designed to:
- Allow citizens to request emergency assistance (medical, fire, police)
- Connect users with the nearest available emergency service providers
- Provide real-time location tracking and route visualization
- Enable efficient emergency response coordination
- Support multiple service providers responding to the same emergency

### Key Capabilities

1. **Real-time Emergency Requests**: Citizens can request help with their exact location
2. **Geospatial Service Discovery**: Automatically find nearby service providers
3. **Live Route Visualization**: Display animated routes from service providers to users
4. **FIFO Assignment Algorithm**: Fair assignment when multiple services accept simultaneously
5. **Reserve/Standby System**: Keep backup services notified in case primary service fails
6. **Dual Communication Protocols**: WebSocket for web clients, MQTT for IoT devices
7. **No Authentication Required for Users**: Emergency access without login barriers

---

## 🏗️ System Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         CLIENT LAYER                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────────┐              ┌──────────────────┐        │
│  │  User Interface  │              │  Service Provider│        │
│  │  (Citizen)       │              │  Dashboard       │        │
│  │                  │              │                  │        │
│  │  - Emergency Map │              │  - Request Queue │        │
│  │  - Location      │              │  - Accept/Reject │        │
│  │  - Route View    │              │  - Route View    │        │
│  └────────┬─────────┘              └────────┬─────────┘        │
│           │                                 │                   │
│           │        WebSocket / HTTP         │                   │
│           └─────────────┬───────────────────┘                   │
│                         │                                        │
└─────────────────────────┼────────────────────────────────────────┘
                          │
┌─────────────────────────┼────────────────────────────────────────┐
│                         │      APPLICATION LAYER                 │
├─────────────────────────┼────────────────────────────────────────┤
│                         │                                        │
│                    ┌────▼────┐                                  │
│                    │ FastAPI │                                  │
│                    │ Backend │                                  │
│                    └────┬────┘                                  │
│                         │                                        │
│        ┌────────────────┼────────────────┐                      │
│        │                │                │                       │
│   ┌────▼─────┐   ┌─────▼──────┐  ┌─────▼──────┐               │
│   │ REST API │   │  WebSocket │  │ MQTT Client │               │
│   │ Endpoints│   │  Manager   │  │             │               │
│   └──────────┘   └────────────┘  └─────┬───────┘               │
│                                         │                        │
└─────────────────────────────────────────┼────────────────────────┘
                                          │
┌─────────────────────────────────────────┼────────────────────────┐
│                         MESSAGE BROKER LAYER                      │
├─────────────────────────────────────────┼────────────────────────┤
│                                         │                         │
│                               ┌─────────▼─────────┐              │
│                               │ Mosquitto MQTT    │              │
│                               │ Broker (Port 1883)│              │
│                               └───────────────────┘              │
│                                                                   │
└───────────────────────────────────────────────────────────────────┘
                          │
┌─────────────────────────┼────────────────────────────────────────┐
│                         │       DATA LAYER                       │
├─────────────────────────┼────────────────────────────────────────┤
│                         │                                        │
│        ┌────────────────┼────────────────┐                      │
│        │                │                │                       │
│   ┌────▼──────────┐  ┌─▼──────────┐  ┌──▼────────────┐         │
│   │  PostgreSQL   │  │  MongoDB   │  │  Redis (opt)  │         │
│   │  + PostGIS    │  │            │  │               │         │
│   │               │  │            │  │               │         │
│   │ - Services    │  │ - Logs     │  │ - Cache       │         │
│   │ - Requests    │  │ - Events   │  │ - Sessions    │         │
│   │ - Responses   │  │ - Metrics  │  │               │         │
│   │ - Locations   │  │            │  │               │         │
│   └───────────────┘  └────────────┘  └───────────────┘         │
│                                                                   │
└───────────────────────────────────────────────────────────────────┘
```

### Component Interaction Flow

```
1. USER CREATES REQUEST
   User Interface → HTTP POST → FastAPI → PostgreSQL
                              ↓
                         WebSocket → Service Providers
                              ↓
                          MQTT Publish → IoT Devices

2. SERVICE ACCEPTS REQUEST
   Service Dashboard → HTTP POST → FastAPI → Lock (FIFO)
                                           ↓
                                    Distance Calculation
                                           ↓
                              Assign Nearest / Notify Reserves
                                           ↓
                         WebSocket → User & All Services
                                           ↓
                                    Route Visualization

3. ROUTE ANIMATION
   Frontend → OSRM API → Route Coordinates
           ↓
   Leaflet Map → Animated Car Marker → Exact Destination
```

---

## 💻 Technology Stack

### Backend Technologies

| Technology | Version | Purpose |
|------------|---------|---------|
| **Python** | 3.9+ | Primary programming language |
| **FastAPI** | 0.104+ | High-performance web framework |
| **Uvicorn** | 0.24+ | ASGI server |
| **PostgreSQL** | 14+ | Primary relational database |
| **PostGIS** | 3.x | Geospatial extension for PostgreSQL |
| **MongoDB** | 6.0+ | Document database for logs |
| **Mosquitto** | 2.x | MQTT message broker |
| **Socket.IO** | 5.x | WebSocket communication |
| **Paho MQTT** | 1.6+ | Python MQTT client |
| **psycopg2** | 2.9+ | PostgreSQL adapter |
| **PyMongo** | 4.x | MongoDB driver |
| **python-jose** | 3.3+ | JWT token handling |
| **passlib** | 1.7+ | Password hashing (bcrypt) |
| **httpx** | 0.25+ | Async HTTP client |

### Frontend Technologies

| Technology | Version | Purpose |
|------------|---------|---------|
| **HTML5** | - | Structure |
| **CSS3** | - | Styling |
| **JavaScript** | ES6+ | Client-side logic |
| **Leaflet.js** | 1.9.4 | Interactive maps |
| **Esri Leaflet** | 3.0.12 | ArcGIS basemaps |
| **Socket.IO Client** | 4.6.0 | WebSocket client |
| **Leaflet Polyline Decorator** | 1.6.0 | Route arrows |
| **OSRM API** | v1 | Route calculation |

### External APIs

| Service | Purpose |
|---------|---------|
| **OSRM (Open Source Routing Machine)** | Real road routing |
| **ArcGIS Basemaps** | Map tiles (no API key required) |
| **Nominatim (OpenStreetMap)** | Reverse geocoding (coordinates → address) |

---

## 🗄️ Database Design

### PostgreSQL Schema

#### 1. service_providers Table

Stores registered emergency service providers.

```sql
CREATE TABLE service_providers (
    id SERIAL PRIMARY KEY,
    service_id VARCHAR(20) UNIQUE NOT NULL,
    service_name VARCHAR(100) NOT NULL,
    service_type VARCHAR(20) NOT NULL CHECK (service_type IN ('hospital', 'fire_station', 'police_station')),
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    contact_phone VARCHAR(20),
    address TEXT,
    latitude NUMERIC(10, 8) NOT NULL,
    longitude NUMERIC(11, 8) NOT NULL,
    location GEOMETRY(POINT, 4326), -- PostGIS geometry column
    available_units INTEGER DEFAULT 1,
    is_online BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Spatial index for fast location queries
CREATE INDEX idx_service_location ON service_providers USING GIST(location);

-- Index for service type filtering
CREATE INDEX idx_service_type ON service_providers(service_type);
```

**Key Features**:
- `service_id`: Unique identifier (e.g., HOSP-ABC123, FIRE-DEF456, POL-GHI789)
- `location`: PostGIS POINT geometry for spatial queries
- `available_units`: Number of ambulances/fire trucks/police cars available
- Spatial index (GIST) enables fast "find nearest services" queries

#### 2. emergency_requests Table

Stores all emergency requests from users.

```sql
CREATE TABLE emergency_requests (
    id SERIAL PRIMARY KEY,
    request_id VARCHAR(30) UNIQUE NOT NULL,
    request_type VARCHAR(20) NOT NULL CHECK (request_type IN ('ambulance', 'fire', 'police')),
    user_phone VARCHAR(20),
    user_note TEXT,
    latitude NUMERIC(10, 8) NOT NULL,
    longitude NUMERIC(11, 8) NOT NULL,
    location GEOMETRY(POINT, 4326), -- PostGIS geometry column
    address TEXT,
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'accepted', 'canceled', 'completed')),
    assigned_service_id VARCHAR(20),
    estimated_arrival_time INTEGER,
    distance_km NUMERIC(10, 2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (assigned_service_id) REFERENCES service_providers(service_id)
);

-- Spatial index for location-based queries
CREATE INDEX idx_request_location ON emergency_requests USING GIST(location);

-- Index for status filtering
CREATE INDEX idx_request_status ON emergency_requests(status);

-- Index for request type
CREATE INDEX idx_request_type ON emergency_requests(request_type);
```

**Key Features**:
- `request_id`: Unique identifier (e.g., REQ-ABC123DEF456)
- `request_type`: Maps to service_type (ambulance→hospital, fire→fire_station, police→police_station)
- `location`: PostGIS POINT for spatial queries
- `status`: Workflow states (pending → accepted → completed)

#### 3. service_responses Table

Tracks which services accepted/rejected each request.

```sql
CREATE TABLE service_responses (
    id SERIAL PRIMARY KEY,
    request_id VARCHAR(30) NOT NULL,
    service_id VARCHAR(20) NOT NULL,
    response_type VARCHAR(20) NOT NULL CHECK (response_type IN ('accepted', 'rejected', 'reserve', 'canceled')),
    distance_km NUMERIC(10, 2),
    estimated_time_minutes INTEGER,
    response_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_reserve BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (request_id) REFERENCES emergency_requests(request_id),
    FOREIGN KEY (service_id) REFERENCES service_providers(service_id)
);

-- Composite index for querying responses by request
CREATE INDEX idx_responses_request ON service_responses(request_id, response_time);

-- Index for service responses
CREATE INDEX idx_responses_service ON service_responses(service_id);
```

**Key Features**:
- Tracks ALL responses (accept/reject) for analytics
- `response_time`: Timestamp of acceptance/rejection
- `is_reserve`: TRUE if service is on standby (not primary responder)
- Enables FIFO logic: multiple accepts within 2-second window

### MongoDB Collections

#### 1. service_logs Collection

```json
{
    "_id": ObjectId("..."),
    "service_id": "HOSP-ABC123",
    "action": "login",
    "timestamp": ISODate("2024-12-31T10:30:00Z"),
    "details": {
        "ip_address": "192.168.1.100",
        "user_agent": "Mozilla/5.0...",
        "service_name": "Kwong Wah Hospital"
    }
}
```

**Indexes**:
```javascript
db.service_logs.createIndex({ "service_id": 1, "timestamp": -1 })
db.service_logs.createIndex({ "action": 1 })
```

#### 2. request_logs Collection

```json
{
    "_id": ObjectId("..."),
    "request_id": "REQ-ABC123",
    "event": "created",
    "timestamp": ISODate("2024-12-31T10:30:00Z"),
    "data": {
        "request_type": "ambulance",
        "location": {
            "latitude": 22.3193,
            "longitude": 114.1694
        },
        "user_phone": "+852 1234 5678"
    }
}
```

**Purpose**: Analytics, auditing, debugging

---

## 🏛️ Backend Architecture

### Project Structure

```
3_BACKEND/
├── app/
│   ├── __init__.py
│   ├── main.py                    # FastAPI application entry point
│   ├── config.py                  # Configuration settings
│   ├── models.py                  # Pydantic models
│   │
│   ├── auth/
│   │   ├── __init__.py
│   │   ├── jwt_handler.py         # JWT token creation/verification
│   │   └── password.py            # Password hashing (bcrypt)
│   │
│   ├── database/
│   │   ├── __init__.py
│   │   ├── postgis.py             # PostgreSQL + PostGIS operations
│   │   └── mongodb.py             # MongoDB logging operations
│   │
│   ├── mqtt/
│   │   ├── __init__.py
│   │   └── mqtt_manager.py        # MQTT client and pub/sub
│   │
│   ├── websocket/
│   │   ├── __init__.py
│   │   └── manager.py             # WebSocket connection manager
│   │
│   ├── services/
│   │   ├── __init__.py
│   │   └── distance_calculator.py # OSRM distance/ETA calculation
│   │
│   └── routers/
│       ├── __init__.py
│       ├── auth.py                # /api/auth/* endpoints
│       ├── requests.py            # /api/requests/* endpoints
│       └── services.py            # /api/services/* endpoints
│
├── main.py                        # Application entry point
└── requirements.txt               # Python dependencies
```

### Core Components

#### 1. FastAPI Application (main.py)

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import socketio

# Create FastAPI app
app = FastAPI(
    title="Emergency Response System",
    description="Real-time emergency response coordination",
    version="1.0.0"
)

# CORS middleware for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Socket.IO integration
sio = socketio.AsyncServer(
    async_mode='asgi',
    cors_allowed_origins='*',
    logger=True,
    engineio_logger=True
)

# Include routers
app.include_router(auth_router)
app.include_router(requests_router)
app.include_router(services_router)
```

#### 2. PostgreSQL + PostGIS Manager (database/postgis.py)

**Key Methods**:

```python
class PostgreSQLDatabase:

    def get_nearest_services(self, latitude, longitude, service_type, limit=5):
        """
        Find nearest services using PostGIS ST_Distance

        Uses SRID 4326 (WGS84) for accurate geographic distance calculation
        """
        query = """
            SELECT
                service_id, service_name, service_type,
                latitude, longitude, contact_phone, available_units,
                ST_Distance(
                    location::geography,
                    ST_SetSRID(ST_MakePoint(%s, %s), 4326)::geography
                ) / 1000.0 AS distance_km
            FROM service_providers
            WHERE service_type = %s AND is_online = TRUE
            ORDER BY distance_km
            LIMIT %s
        """
        # Returns services sorted by distance (nearest first)

    def create_emergency_request(self, request_data):
        """
        Create emergency request with PostGIS geometry
        """
        query = """
            INSERT INTO emergency_requests
            (request_id, request_type, latitude, longitude, location, ...)
            VALUES (%s, %s, %s, %s, ST_SetSRID(ST_MakePoint(%s, %s), 4326), ...)
            RETURNING *
        """
        # ST_MakePoint creates PostGIS POINT geometry
```

**PostGIS Features Used**:
- `ST_MakePoint(lng, lat)`: Create point geometry
- `ST_SetSRID(..., 4326)`: Set coordinate system (WGS84)
- `ST_Distance(geom1::geography, geom2::geography)`: Calculate real-world distance in meters
- `GIST` index: Spatial index for fast nearest-neighbor queries

#### 3. WebSocket Manager (websocket/manager.py)

```python
class ConnectionManager:
    """Manages WebSocket connections for real-time updates"""

    def __init__(self):
        self.active_connections = {}
        self.service_connections = {}  # service_id → sid
        self.user_connections = {}     # user_id → sid

    async def broadcast_to_services(self, service_type, event, data):
        """Broadcast to all services of a specific type"""
        for service_id, sid in self.service_connections.items():
            service = db.get_service_by_id(service_id)
            if service and service['service_type'] == service_type:
                await sio.emit(event, data, room=sid)

    async def notify_service(self, service_id, event, data):
        """Send message to specific service"""
        if service_id in self.service_connections:
            sid = self.service_connections[service_id]
            await sio.emit(event, data, room=sid)

    async def notify_user(self, user_id, event, data):
        """Send message to specific user"""
        if user_id in self.user_connections:
            sid = self.user_connections[user_id]
            await sio.emit(event, data, room=sid)
```

**Events**:
- `new_emergency_request`: Notify all services of new request
- `request_assigned_to_you`: Notify service they were chosen
- `request_assigned`: Notify user their request was accepted
- `request_reserve_standby`: Notify reserve services
- `request_canceled`: Notify all parties of cancellation

#### 4. MQTT Manager (mqtt/mqtt_manager.py)

```python
class MQTTManager:
    """MQTT client for IoT device communication"""

    def __init__(self, broker="localhost", port=1883):
        self.client = mqtt.Client()
        self.client.connect(broker, port)
        self.client.loop_start()

    async def publish_new_request(self, service_type, request_data):
        """Publish new request to MQTT topic"""
        topic = f"emergency/{service_type}/new_request"
        payload = json.dumps(request_data)
        self.client.publish(topic, payload, qos=1)

    async def publish_request_assigned(self, request_id, assignment_data):
        """Notify IoT devices of request assignment"""
        topic = f"emergency/assignments/{request_id}"
        payload = json.dumps(assignment_data)
        self.client.publish(topic, payload, qos=1)
```

**MQTT Topics**:
```
emergency/ambulance/new_request
emergency/fire/new_request
emergency/police/new_request
emergency/assignments/{request_id}
emergency/reserves/{request_id}
```

#### 5. Distance Calculator (services/distance_calculator.py)

```python
async def calculate_distance_and_eta(from_lat, from_lng, to_lat, to_lng):
    """
    Calculate route distance and ETA using OSRM

    Returns:
        - distance_km: Real road distance in kilometers
        - eta_minutes: Estimated travel time in minutes
    """
    osrm_url = f"https://router.project-osrm.org/route/v1/driving/{from_lng},{from_lat};{to_lng},{to_lat}"

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(osrm_url, timeout=5.0)
            data = response.json()

            route = data['routes'][0]
            distance_km = route['distance'] / 1000.0  # meters → km
            eta_minutes = round(route['duration'] / 60.0)  # seconds → minutes

            return distance_km, eta_minutes

    except Exception as e:
        # Fallback: Haversine formula (straight-line distance)
        distance_km = haversine_distance(from_lat, from_lng, to_lat, to_lng)
        eta_minutes = round(distance_km * 2)  # Estimate: 30 km/h avg speed
        return distance_km, eta_minutes
```

---

## 🌐 Frontend Architecture

### Project Structure

```
4_FRONTEND/
├── user/                          # Citizen interface
│   ├── index.html                 # Main user page
│   ├── login.html                 # User login (optional)
│   ├── css/
│   │   └── styles.css
│   └── js/
│       ├── map.js                 # Map initialization
│       ├── location.js            # Geolocation handling
│       ├── requests.js            # Emergency request creation
│       └── route-animation.js     # Route visualization
│
└── service/                       # Service provider interface
    ├── login.html                 # Service provider login
    ├── register.html              # Service provider registration
    ├── dashboard.html             # Main dashboard
    ├── css/
    │   └── dashboard.css
    └── js/
        ├── auth.js                # Authentication logic
        ├── service.js             # Request handling
        ├── map.js                 # Map display
        └── route-animation.js     # Route visualization
```

### Key Frontend Components

#### 1. Map Initialization (Leaflet + ArcGIS)

```javascript
function initMap() {
    // Create map centered on Hong Kong
    map = L.map('map').setView([22.3193, 114.1694], 11);

    // Add ArcGIS basemap (no API key required)
    L.esri.basemapLayer('Streets').addTo(map);

    // Add layer control for different basemaps
    const basemaps = {
        'Streets': L.esri.basemapLayer('Streets'),
        'Satellite': L.esri.basemapLayer('Imagery'),
        'Topographic': L.esri.basemapLayer('Topographic'),
        'Dark Gray': L.esri.basemapLayer('DarkGray')
    };

    L.control.layers(basemaps).addTo(map);

    // Add geocoding search
    const searchControl = L.esri.Geocoding.geosearch({
        position: 'topright',
        placeholder: 'Search for address...'
    }).addTo(map);
}
```

#### 2. Route Animation Module (route-animation.js)

**Complete workflow**:

```javascript
async function showRouteAndAnimate(params) {
    const { fromLat, fromLng, toLat, toLng, serviceType, routeColor, animationDuration } = params;

    // Step 1: Fetch route from OSRM
    const routeData = await fetchRoute(fromLat, fromLng, toLat, toLng);

    // Step 2: Ensure route ends at exact destination
    const lastCoord = routeData.coordinates[routeData.coordinates.length - 1];
    const distanceToDestination = calculateDistance(lastCoord[0], lastCoord[1], toLat, toLng);

    if (distanceToDestination > 0.01) { // More than 10 meters away
        routeData.coordinates.push([toLat, toLng]); // Add exact destination
    }

    // Step 3: Display route on map
    const routeLine = L.polyline(routeData.coordinates, {
        color: routeColor,
        weight: 5,
        opacity: 0.7
    }).addTo(map);

    // Step 4: Add directional arrows
    L.polylineDecorator(routeLine, {
        patterns: [{
            offset: '10%',
            repeat: '15%',
            symbol: L.Symbol.arrowHead({ pixelSize: 10 })
        }]
    }).addTo(map);

    // Step 5: Create animated car marker
    const carIcon = L.divIcon({
        html: `<div style="font-size:30px">${getServiceEmoji(serviceType)}</div>`
    });

    const carMarker = L.marker([fromLat, fromLng], { icon: carIcon }).addTo(map);

    // Step 6: Animate car along route
    animateCarMovement(carMarker, routeData.coordinates, animationDuration);
}

function animateCarMovement(marker, coordinates, duration) {
    const totalSteps = coordinates.length;
    const stepDelay = duration / totalSteps;
    let currentIndex = 0;

    const interval = setInterval(() => {
        if (currentIndex >= totalSteps - 1) {
            clearInterval(interval);
            return;
        }

        const current = coordinates[currentIndex];
        const next = coordinates[currentIndex + 1];

        // Calculate rotation angle
        const angle = calculateBearing(current[0], current[1], next[0], next[1]);

        // Move marker
        marker.setLatLng(next);

        // Rotate car icon
        const element = marker.getElement();
        element.querySelector('div').style.transform = `rotate(${angle}deg)`;

        currentIndex++;
    }, stepDelay);
}
```

**Features**:
- Real road routing via OSRM API
- Guaranteed arrival at exact destination
- Directional car rotation based on bearing
- Customizable animation speed (default: 45 seconds)
- Service-specific vehicle icons (🚑/🚒/🚓)

#### 3. WebSocket Client

```javascript
// Connect to backend
const socket = io('http://localhost:8000');

// Register user for notifications
socket.emit('register_user', {
    user_id: `USER-${requestId}`,
    request_id: requestId
});

// Listen for request assignment
socket.on('request_assigned', (data) => {
    console.log('Request assigned:', data);

    // Find original user location from notification
    const notif = notifications.find(n => n.id === data.request_id);

    // Show route animation
    showRouteAndAnimate({
        fromLat: data.service_location.latitude,
        fromLng: data.service_location.longitude,
        toLat: notif.userLocation.latitude,  // Use ORIGINAL location
        toLng: notif.userLocation.longitude,
        serviceType: data.service_type,
        animationDuration: 45000  // 45 seconds
    });
});
```

---

## 📡 Communication Mechanisms

### 1. WebSocket Communication (Socket.IO)

**Purpose**: Real-time bidirectional communication for web clients

**Connection Flow**:
```
1. Client connects: socket.connect()
2. Server assigns session ID (sid)
3. Client registers: socket.emit('register_user', { user_id, request_id })
4. Server maps user_id → sid
5. Server can now send targeted messages
```

**Events**:

| Event | Direction | Payload | Purpose |
|-------|-----------|---------|---------|
| `register_user` | Client → Server | `{ user_id, request_id }` | Register user for notifications |
| `register_service` | Client → Server | `{ service_id, service_type }` | Register service for requests |
| `new_emergency_request` | Server → Services | `{ request_id, location, type }` | Broadcast new request |
| `request_assigned_to_you` | Server → Service | `{ request_id, distance, eta }` | Notify assigned service |
| `request_assigned` | Server → User | `{ service_name, service_location, eta }` | Notify user of acceptance |
| `request_reserve_standby` | Server → Services | `{ request_id, assigned_to }` | Notify reserve services |
| `request_canceled` | Server → All | `{ request_id, reason }` | Notify cancellation |

### 2. MQTT Communication

**Purpose**: Lightweight pub/sub for IoT devices (ambulances, fire trucks, etc.)

**Topic Structure**:
```
emergency/
├── ambulance/
│   ├── new_request          (service subscribes)
│   └── assignments/+        (service subscribes)
├── fire/
│   ├── new_request
│   └── assignments/+
├── police/
│   ├── new_request
│   └── assignments/+
└── global/
    └── system_status
```

**QoS Levels**:
- QoS 0: Fire-and-forget (system status)
- QoS 1: At-least-once delivery (emergency requests)
- QoS 2: Exactly-once delivery (critical assignments)

### 3. HTTP REST API

**Purpose**: Stateless request/response for data operations

**Authentication**: JWT Bearer tokens

```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

---

## 🎯 Core Features

### 1. Emergency Request Creation (No Login Required)

**User Flow**:
1. User opens application
2. Clicks "Share My Location" or clicks on map
3. Selects emergency type (🚑 Medical / 🚒 Fire / 🚓 Police)
4. Optionally adds phone number and description
5. Clicks emergency button
6. System creates request instantly

**Backend Processing**:
```python
# 1. Generate unique request ID
request_id = f"REQ-{secrets.token_hex(6).upper()}"

# 2. Create PostGIS geometry
location = ST_SetSRID(ST_MakePoint(longitude, latitude), 4326)

# 3. Insert into database
db.create_emergency_request({
    'request_id': request_id,
    'location': location,
    'request_type': 'ambulance'
})

# 4. Broadcast to relevant services
await manager.broadcast_to_services(
    service_type='hospital',
    event='new_emergency_request',
    data=notification_data
)

# 5. Publish to MQTT
await mqtt_manager.publish_new_request(
    service_type='ambulance',
    request_data=notification_data
)
```

### 2. Service Provider Registration & Login

**Registration**:
- Service name, type, email, password
- Contact phone, address
- **Geographic coordinates** (latitude, longitude)
- Available units (ambulances, fire trucks, police cars)

**Login**:
- JWT token generation
- Token includes: service_id, email, service_type
- Token expires after 7 days
- Coordinates returned in login response for map display

**Password Security**:
```python
# Registration: Hash password with bcrypt
password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

# Login: Verify password
is_valid = bcrypt.checkpw(password.encode('utf-8'), stored_hash.encode('utf-8'))
```

### 3. FIFO Assignment Algorithm with Simultaneous Accept Window

**Problem**: What if 3 ambulances click "Accept" at the same time?

**Solution**: 2-second acceptance window + assign nearest

**Algorithm**:

```python
# 1. Service accepts request
async def respond_to_request(response: ServiceResponseAction):

    # 2. Acquire lock (FIFO: one service at a time)
    async with request_locks[response.request_id]:

        # 3. Record acceptance with timestamp and distance
        db.record_service_response({
            'request_id': response.request_id,
            'service_id': service['service_id'],
            'response_type': 'accepted',
            'distance_km': distance_km,
            'response_time': datetime.now()
        })

        # 4. Check for other acceptances in last 2 seconds
        recent_accepts = db.get_recent_accepts(response.request_id, seconds=2)

        # 5. If only this service accepted → assign immediately
        if len(recent_accepts) == 1:
            assign_to_service(service)
            return

        # 6. Multiple services accepted → calculate distances
        distances = {}
        for accept in recent_accepts:
            svc = db.get_service_by_id(accept['service_id'])
            distance, eta = await calculate_distance_and_eta(
                svc['latitude'], svc['longitude'],
                request['latitude'], request['longitude']
            )
            distances[svc['service_id']] = distance

        # 7. Find nearest service
        nearest_service_id = min(distances, key=distances.get)

        # 8. Assign to nearest, notify others as reserves
        assign_to_service(nearest_service)

        for sid in distances.keys():
            if sid != nearest_service_id:
                notify_reserve_service(sid)
```

**Timeline Example**:
```
10:00:00.000 - Request created
10:00:05.500 - Ambulance A accepts (distance: 2.3 km)
10:00:06.200 - Ambulance B accepts (distance: 1.8 km) ← within 2 sec window
10:00:07.300 - System assigns to Ambulance B (nearest)
10:00:07.301 - Ambulance A notified as reserve
```

### 4. Reserve/Standby System

**Purpose**: Keep backup services ready in case primary service fails

**Implementation**:
```python
# Mark services as reserves in database
db.mark_services_as_reserve(request_id, reserve_service_ids)

# Notify each reserve service
for sid in reserve_service_ids:
    reserve_notification = {
        'request_id': request_id,
        'status': 'reserve',
        'assigned_to_service': nearest_service['service_name'],
        'your_distance_km': distances[sid],
        'message': 'You are on standby',
        'reserve_position': position  # 1st backup, 2nd backup, etc.
    }

    await manager.notify_service(sid, 'request_reserve_standby', reserve_notification)
```

**Reserve Service Dashboard**:
- Shows separate "Reserve Requests" section
- Displays assigned service name
- Shows "You're 2nd in line" message
- Can be promoted to primary if assigned service cancels

### 5. Real-time Route Visualization

**Components**:

1. **Route Fetching** (OSRM API):
```javascript
const osrmUrl = `https://router.project-osrm.org/route/v1/driving/${fromLng},${fromLat};${toLng},${toLat}?overview=full&geometries=geojson`;

const response = await fetch(osrmUrl);
const data = await response.json();

// Extract route coordinates
const route = data.routes[0];
const coordinates = route.geometry.coordinates.map(coord => [coord[1], coord[0]]);
```

2. **Destination Accuracy Fix**:
```javascript
// OSRM may snap to nearest road, so ensure exact destination
const lastCoord = coordinates[coordinates.length - 1];
const distanceToDestination = calculateDistance(lastCoord, destination);

if (distanceToDestination > 0.01) { // > 10 meters
    coordinates.push([exactLat, exactLng]); // Force exact destination
}
```

3. **Route Display**:
```javascript
// Draw colored route line
const routeLine = L.polyline(coordinates, {
    color: '#e53935',  // Red for ambulance
    weight: 5,
    opacity: 0.7
}).addTo(map);

// Add directional arrows
L.polylineDecorator(routeLine, {
    patterns: [{
        offset: '10%',
        repeat: '15%',
        symbol: L.Symbol.arrowHead({
            pixelSize: 10,
            pathOptions: { color: '#e53935' }
        })
    }]
}).addTo(map);
```

4. **Car Animation**:
```javascript
// Create car marker
const carMarker = L.marker([startLat, startLng], {
    icon: L.divIcon({
        html: '<div style="font-size:30px">🚑</div>',
        iconSize: [30, 30]
    })
}).addTo(map);

// Animate along route
const stepDelay = animationDuration / coordinates.length;

setInterval(() => {
    const nextPos = coordinates[currentIndex];
    const angle = calculateBearing(currentPos, nextPos);

    carMarker.setLatLng(nextPos);
    carMarker.getElement().style.transform = `rotate(${angle}deg)`;

    currentIndex++;
}, stepDelay);
```

**Animation appears on**:
- ✅ Service provider dashboard (sees route from their location → user)
- ✅ User interface (sees route from service → their location)

---

## 🔒 Security

### 1. Password Security

- **Algorithm**: bcrypt with salt
- **Rounds**: 12 (2^12 = 4096 iterations)
- **Storage**: Only hashed passwords stored in database

### 2. JWT Authentication

**Token Structure**:
```json
{
  "service_id": "HOSP-ABC123",
  "email": "hospital@example.com",
  "service_type": "hospital",
  "exp": 1704067200  // Expiration timestamp
}
```

**Token Validation**:
```python
def verify_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
```

### 3. SQL Injection Prevention

**Using parameterized queries**:
```python
# ✅ SAFE
cursor.execute(
    "SELECT * FROM service_providers WHERE email = %s",
    (email,)
)

# ❌ VULNERABLE
cursor.execute(f"SELECT * FROM service_providers WHERE email = '{email}'")
```

### 4. CORS Configuration

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production: specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### 5. Input Validation

Using Pydantic models:
```python
class EmergencyRequestCreate(BaseModel):
    request_type: Literal['ambulance', 'fire', 'police']
    location: LocationData
    user_phone: Optional[str] = None
    user_note: Optional[str] = None

    @validator('user_phone')
    def validate_phone(cls, v):
        if v and not re.match(r'^\+?\d{8,15}$', v):
            raise ValueError('Invalid phone number')
        return v
```

---

## 🌍 Geospatial Features

### PostGIS Geometry Types

**POINT**: Represents a location
```sql
ST_MakePoint(longitude, latitude)
-- Example: ST_MakePoint(114.1694, 22.3193)
```

**Coordinate System**: SRID 4326 (WGS84)
- Used by GPS
- Latitude: -90 to +90
- Longitude: -180 to +180

### Distance Calculation

**Method 1: Haversine Formula** (straight-line)
```python
def haversine_distance(lat1, lng1, lat2, lng2):
    R = 6371  # Earth radius in km

    dlat = radians(lat2 - lat1)
    dlng = radians(lng2 - lng1)

    a = sin(dlat/2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlng/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1-a))

    return R * c
```

**Method 2: PostGIS ST_Distance** (accurate geographic distance)
```sql
ST_Distance(
    location1::geography,
    location2::geography
) / 1000.0  -- Convert meters to km
```

**Method 3: OSRM Routing** (real road distance)
```
GET https://router.project-osrm.org/route/v1/driving/114.1694,22.3193;114.2000,22.3500

Response:
{
  "routes": [{
    "distance": 4532.5,  // meters
    "duration": 542.3    // seconds
  }]
}
```

### Nearest Service Query

```sql
SELECT
    service_id, service_name,
    ST_Distance(
        location::geography,
        ST_SetSRID(ST_MakePoint(%s, %s), 4326)::geography
    ) / 1000.0 AS distance_km
FROM service_providers
WHERE service_type = %s AND is_online = TRUE
ORDER BY location <-> ST_SetSRID(ST_MakePoint(%s, %s), 4326)
LIMIT 5;
```

**Operators**:
- `<->`: KNN (K-Nearest Neighbor) operator for fast distance-based sorting
- `ST_Distance`: Accurate distance calculation
- `::geography`: Cast to geography type for meters instead of degrees

---

## 📊 Data Flow

### Complete Request Lifecycle

```
┌─────────────────────────────────────────────────────────────┐
│ 1. USER CREATES EMERGENCY REQUEST                          │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│ User Interface                                              │
│  - User sets location on map                                │
│  - Clicks emergency button (ambulance/fire/police)          │
│  - Optionally adds phone + description                      │
└──────────────┬──────────────────────────────────────────────┘
               │
               │ HTTP POST /api/requests/create
               │ { request_type, location, user_phone, user_note }
               ▼
┌─────────────────────────────────────────────────────────────┐
│ Backend - Create Request                                    │
│  1. Generate request_id: "REQ-ABC123DEF456"                 │
│  2. Create PostGIS geometry: ST_MakePoint(lng, lat)         │
│  3. Insert into emergency_requests table                    │
│  4. Log to MongoDB (request_logs collection)                │
└──────────────┬──────────────────────────────────────────────┘
               │
               ├─────────────────┬───────────────────┐
               │                 │                   │
               ▼                 ▼                   ▼
┌──────────────────┐  ┌──────────────────┐  ┌──────────────┐
│ WebSocket        │  │ MQTT Publish     │  │ Response     │
│ Broadcast        │  │                  │  │ to User      │
│                  │  │ Topic:           │  │              │
│ To: All services │  │ emergency/       │  │ { request_id │
│     of type      │  │ ambulance/       │  │   status }   │
│                  │  │ new_request      │  │              │
└────────┬─────────┘  └──────────────────┘  └──────────────┘
         │
         │ Event: 'new_emergency_request'
         │
         ▼
┌─────────────────────────────────────────────────────────────┐
│ 2. SERVICE PROVIDERS RECEIVE NOTIFICATION                   │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│ Service Provider Dashboards                                 │
│  - Notification popup appears                               │
│  - Audio alert plays                                        │
│  - Request details shown: location, type, distance          │
│  - Map shows user location marker                           │
│  - [Accept] [Reject] buttons enabled                        │
└──────────────┬──────────────────────────────────────────────┘
               │
               │ Multiple services may respond
               │
               ▼
┌─────────────────────────────────────────────────────────────┐
│ 3. SERVICES RESPOND (Accept/Reject)                         │
└─────────────────────────────────────────────────────────────┘
               │
               │ HTTP POST /api/requests/respond
               │ { request_id, response_type: "accepted" }
               │ Authorization: Bearer <jwt_token>
               ▼
┌─────────────────────────────────────────────────────────────┐
│ Backend - FIFO Assignment Algorithm                         │
│                                                              │
│ Step 1: Acquire request-specific lock (asyncio.Lock)        │
│         → Ensures FIFO: one service at a time               │
│                                                              │
│ Step 2: Check if request already assigned                   │
│         → If yes: notify "request_unavailable"              │
│                                                              │
│ Step 3: Calculate distance using OSRM                       │
│         → Real road distance + ETA                          │
│                                                              │
│ Step 4: Record acceptance in service_responses table        │
│         → { service_id, request_id, distance, timestamp }   │
│                                                              │
│ Step 5: Get all accepts in last 2 seconds                   │
│         → SELECT * WHERE response_time > NOW() - 2s         │
│                                                              │
│ Step 6: Determine assignment                                │
│         ┌─────────────────┬────────────────────┐            │
│         │ If 1 accept     │ If multiple accepts│            │
│         │ → Assign now    │ → Calc all dists   │            │
│         │                 │ → Assign nearest   │            │
│         └─────────────────┴────────────────────┘            │
│                                                              │
│ Step 7: Update emergency_requests table                     │
│         → status = 'accepted'                               │
│         → assigned_service_id = nearest_service             │
│                                                              │
│ Step 8: Mark other services as reserves                     │
│         → is_reserve = TRUE in service_responses            │
└──────────────┬──────────────────────────────────────────────┘
               │
               ├────────────────┬───────────────┐
               │                │               │
               ▼                ▼               ▼
┌──────────────────┐  ┌──────────────┐  ┌──────────────┐
│ Notify Assigned  │  │ Notify User  │  │ Notify       │
│ Service          │  │              │  │ Reserves     │
│                  │  │              │  │              │
│ Event:           │  │ Event:       │  │ Event:       │
│ request_         │  │ request_     │  │ request_     │
│ assigned_to_you  │  │ assigned     │  │ reserve_     │
│                  │  │              │  │ standby      │
│ Data:            │  │ Data:        │  │              │
│ { distance,      │  │ { service_   │  │ Data:        │
│   eta,           │  │   name,      │  │ { assigned_  │
│   location }     │  │   service_   │  │   to,        │
│                  │  │   location,  │  │   position,  │
│                  │  │   eta }      │  │   distance } │
└────────┬─────────┘  └──────┬───────┘  └──────────────┘
         │                   │
         │                   │
         ▼                   ▼
┌─────────────────────────────────────────────────────────────┐
│ 4. ROUTE VISUALIZATION STARTS                               │
└─────────────────────────────────────────────────────────────┘
                          │
         ┌────────────────┴────────────────┐
         │                                 │
         ▼                                 ▼
┌─────────────────────┐         ┌─────────────────────┐
│ Service Dashboard   │         │ User Interface      │
│                     │         │                     │
│ 1. Extract coords:  │         │ 1. Extract coords:  │
│    - From: service  │         │    - From: service  │
│    - To: user       │         │    - To: user       │
│                     │         │                     │
│ 2. Call OSRM API:   │         │ 2. Call OSRM API:   │
│    GET router.      │         │    Same route!      │
│    project-osrm.org │         │                     │
│                     │         │                     │
│ 3. Get route coords │         │ 3. Get route coords │
│    [250+ points]    │         │    [250+ points]    │
│                     │         │                     │
│ 4. Fix destination: │         │ 4. Fix destination: │
│    Ensure last point│         │    Ensure last point│
│    = exact user loc │         │    = exact user loc │
│                     │         │                     │
│ 5. Draw polyline    │         │ 5. Draw polyline    │
│    Color: red/      │         │    Color: red/      │
│    orange/blue      │         │    orange/blue      │
│                     │         │                     │
│ 6. Add arrows       │         │ 6. Add arrows       │
│    (Polyline        │         │    (Polyline        │
│     Decorator)      │         │     Decorator)      │
│                     │         │                     │
│ 7. Create car       │         │ 7. Create car       │
│    marker 🚑/🚒/🚓  │         │    marker 🚑/🚒/🚓  │
│                     │         │                     │
│ 8. Animate (45s)    │         │ 8. Animate (45s)    │
│    - Move marker    │         │    - Move marker    │
│    - Rotate icon    │         │    - Rotate icon    │
│    - Follow route   │         │    - Follow route   │
└─────────────────────┘         └─────────────────────┘
```

---

## 📁 Code Structure Details

### Backend File Breakdown

**app/config.py** (Configuration Management)
```python
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_DB = os.getenv("POSTGRES_DB", "emergency_response")
MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
MQTT_BROKER = os.getenv("MQTT_BROKER", "localhost")
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-here")
```

**app/models.py** (Pydantic Data Models)
```python
class LocationData(BaseModel):
    latitude: float
    longitude: float
    address: Optional[str] = None

class EmergencyRequestCreate(BaseModel):
    request_type: Literal['ambulance', 'fire', 'police']
    location: LocationData
    user_phone: Optional[str] = None
    user_note: Optional[str] = None

class ServiceResponseAction(BaseModel):
    request_id: str
    response_type: Literal['accepted', 'rejected']

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    service_id: str
    service_name: str
    service_type: str
    latitude: float
    longitude: float
```

### Frontend File Breakdown

**4_FRONTEND/user/index.html** (User Interface)
- Lines 1-342: HTML structure + CSS styling
- Lines 343-651: JavaScript (map, location, WebSocket)
- Lines 652-701: Emergency request creation
- Lines 702-810: WebSocket event handlers + route animation

**4_FRONTEND/service/dashboard.html** (Service Provider Dashboard)
- Lines 1-530: HTML structure + CSS styling
- Lines 531-1100: JavaScript (map, auth, request handling, route animation)

**route-animation.js** (Shared Route Visualization Module)
- Lines 1-62: OSRM route fetching with fallback
- Lines 88-146: Route display with arrows
- Lines 154-184: Animated car marker creation
- Lines 192-242: Car movement animation with rotation
- Lines 306-386: Main `showRouteAndAnimate()` function

---

## 🚀 Performance Optimizations

### Database Indexes

```sql
-- Spatial indexes for fast location queries
CREATE INDEX idx_service_location ON service_providers USING GIST(location);
CREATE INDEX idx_request_location ON emergency_requests USING GIST(location);

-- B-tree indexes for filtering
CREATE INDEX idx_service_type ON service_providers(service_type);
CREATE INDEX idx_request_status ON emergency_requests(status);
CREATE INDEX idx_responses_request ON service_responses(request_id, response_time);
```

### Async Operations

All I/O operations are asynchronous:
- Database queries: async with asyncpg (future upgrade)
- HTTP requests: async with httpx
- WebSocket: async Socket.IO
- MQTT: event-driven callbacks

### Caching Strategy (Future Enhancement)

```python
# Redis caching for frequently accessed data
cache.set(f"service:{service_id}", service_data, expire=300)  # 5 min TTL
```

---

## 📈 Monitoring & Logging

### MongoDB Logs

**Service Actions**:
```json
{
  "service_id": "HOSP-ABC123",
  "action": "login",
  "timestamp": "2024-12-31T10:30:00Z",
  "ip": "192.168.1.100"
}
```

**Request Events**:
```json
{
  "request_id": "REQ-ABC123",
  "event": "created",
  "timestamp": "2024-12-31T10:30:00Z",
  "data": { "type": "ambulance", "location": {...} }
}
```

### Application Logging

```python
import logging

logger = logging.getLogger(__name__)

logger.info(f"Service logged in: {service_id}")
logger.warning(f"Service {service_id} has NULL coordinates")
logger.error(f"Failed to connect to database: {error}")
```

---

## 🧪 Testing Scenarios

### Test Case 1: Single Service Accepts

1. Create emergency request (ambulance)
2. Single hospital accepts
3. ✅ Expected: Immediate assignment, route animation starts

### Test Case 2: Multiple Services Accept Simultaneously

1. Create emergency request (fire)
2. Three fire stations accept within 2 seconds
3. ✅ Expected: Nearest station assigned, others marked as reserve

### Test Case 3: Reserve Promotion

1. Primary service assigned
2. Primary service cancels
3. ✅ Expected: First reserve promoted to primary

### Test Case 4: Route Accuracy

1. Service accepts request
2. Route animation plays
3. ✅ Expected: Car ends at exact user location (within 10 meters)

---

## 🔮 Future Enhancements

1. **Live Tracking**: Real GPS tracking of ambulance/fire truck/police car
2. **Status Updates**: "En route", "Arrived", "Returning to base"
3. **Rating System**: Users rate service providers after completion
4. **Analytics Dashboard**: Response times, success rates, heat maps
5. **Mobile Apps**: Native iOS/Android apps
6. **Multi-language Support**: i18n for global deployment
7. **Voice Calls**: Direct communication between user and service
8. **Video Streaming**: Live video feed from service provider
9. **Payment Integration**: Billing for private ambulance services
10. **AI Dispatch**: Machine learning for optimal service assignment

---

**Version**: 1.0.0
**Last Updated**: December 2024
**License**: MIT
**Author**: Emergency Response System Development Team