# 🚨 Emergency Response System

A complete real-time emergency response dispatch system that connects citizens in need with emergency services using geospatial technology and WebSocket communication.

## 📋 Overview

This system allows:
- **Users** to request emergency help (ambulance, fire, police) with NO login required
- **Service Providers** (hospitals, fire stations, police) to receive and respond to requests in real-time
- **Automatic assignment** of the nearest available service provider
- **Real-time updates** via WebSocket connections
- **Geospatial routing** using PostGIS and pgRouting

## 🏗️ Architecture

### Technology Stack

- **Backend**: Python FastAPI with WebSocket (Socket.IO)
- **Databases**: 
  - PostgreSQL + PostGIS + pgRouting (spatial data & routing)
  - MongoDB (logs & analytics)
- **Frontend**: HTML/CSS/JavaScript + Leaflet.js
- **Geospatial**: ArcGIS Pro (data preparation) + Living Atlas data

### System Components

```
emergency-response-system/
├── 1_ARCGIS_PRO/          # ArcGIS Pro project & scripts
├── 2_DATABASE/            # Database setup scripts
│   ├── postgis/           # PostgreSQL/PostGIS setup
│   └── mongodb/           # MongoDB setup
├── 3_BACKEND/             # FastAPI backend application
│   └── app/               # Application code
├── 4_FRONTEND/            # Web interfaces
│   ├── user/              # User interface (NO login)
│   └── service/           # Service provider dashboard
├── 5_DOCS/                # Documentation
└── 6_SCRIPTS/             # Utility scripts
```

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- PostgreSQL 12+ with PostGIS and pgRouting
- MongoDB 4.4+
- Modern web browser

### Installation Steps

#### 1. Database Setup

```bash
cd 2_DATABASE/postgis

# Install PostgreSQL/PostGIS/pgRouting
sudo bash 1_install.sh

# Create database
sudo -u postgres psql -f 2_setup_database.sql

# Enable pgRouting
sudo -u postgres psql -d emergency_response -f 3_enable_pgrouting.sql

# Create tables
sudo -u postgres psql -d emergency_response -f 4_create_tables.sql

# Create functions
sudo -u postgres psql -d emergency_response -f 6_routing_functions.sql

# Load test data
sudo -u postgres psql -d emergency_response -f 7_seed_data.sql

# Test setup
sudo -u postgres psql -d emergency_response -f test_postgis.sql
```

#### 2. MongoDB Setup

```bash
cd 2_DATABASE/mongodb
mongosh < init_collections.js
```

#### 3. Backend Setup

```bash
cd 3_BACKEND

# Copy environment file
cp .env.example .env

# Edit .env with your database credentials
nano .env

# Start backend
bash start.sh
```

The backend will be available at:
- API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- WebSocket: ws://localhost:8000/socket.io

#### 4. Frontend Setup

Open the frontend files in a web browser:

**User Interface** (NO login required):
```bash
cd 4_FRONTEND/user
python3 -m http.server 3000
# Open: http://localhost:3000
```

**Service Provider Dashboard**:
```bash
# Login credentials (from seed data):
# Email: admin@csmc.edu
# Password: password123

# Access: http://localhost:3000/service/login.html
```

## 📖 Usage Guide

### For Users (Citizens)

1. Open the user interface
2. Click "Get My Location" to detect your position
3. Select emergency type:
   - 🚑 Medical Emergency (Ambulance)
   - 🚒 Fire Emergency
   - 🚓 Police Emergency
4. Optionally add phone number and notes
5. Submit request
6. Wait for service assignment (real-time updates)

### For Service Providers

1. Register your service at `/service/register.html` or use test accounts
2. Login at `/service/login.html`
3. View dashboard with real-time request notifications
4. Click "Accept" or "Reject" for incoming requests
5. If multiple services accept, the nearest one is automatically assigned

## 🔧 Configuration

### Database Connection (.env)

```env
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=emergency_response
POSTGRES_USER=emergency_app
POSTGRES_PASSWORD=emergency_pass_2024

MONGODB_HOST=localhost
MONGODB_PORT=27017
MONGODB_DB=emergency_response_logs
```

### Frontend Configuration (4_FRONTEND/user/js/config.js)

```javascript
const CONFIG = {
    API_URL: 'http://localhost:8000',
    WEBSOCKET_URL: 'http://localhost:8000',
    MAP_CENTER: [34.0522, -118.2437], // Your city coordinates
    MAP_ZOOM: 12
};
```

## 📊 API Endpoints

### Authentication
- `POST /api/auth/register` - Register new service provider
- `POST /api/auth/login` - Service provider login

### Emergency Requests
- `POST /api/requests/create` - Create emergency request (NO auth)
- `GET /api/requests/{request_id}` - Get request status
- `POST /api/requests/respond` - Service responds to request (auth required)
- `GET /api/requests/pending/all` - Get all pending requests

### Services
- `GET /api/services/nearest` - Find nearest services
- `GET /api/services/{service_id}` - Get service details
- `GET /api/services/type/{service_type}` - Get services by type

### System
- `GET /health` - Health check
- `GET /api/stats` - System statistics

Full API documentation: http://localhost:8000/docs

## 🔌 WebSocket Events

### Client → Server

**User Registration:**
```javascript
socket.emit('register_user', {
    user_id: 'USER-REQ-123',
    request_id: 'REQ-123'
});
```

**Service Registration:**
```javascript
socket.emit('register_service', {
    service_id: 'HOSP-001',
    service_type: 'hospital'
});
```

### Server → Client

**New Request (to services):**
```javascript
socket.on('new_emergency_request', (data) => {
    // data contains request details
});
```

**Assignment (to user):**
```javascript
socket.on('request_assigned', (data) => {
    // data contains service details and ETA
});
```

**Assignment Confirmation (to service):**
```javascript
socket.on('request_assigned_to_you', (data) => {
    // You got the request!
});
```

## 🧪 Testing

### Test Database
```bash
cd 2_DATABASE/postgis
sudo -u postgres psql -d emergency_response -f test_postgis.sql
```

### Test Backend API
```bash
# Health check
curl http://localhost:8000/health

# Get services
curl http://localhost:8000/api/services

# Create request
curl -X POST http://localhost:8000/api/requests/create \
  -H "Content-Type: application/json" \
  -d '{
    "request_type": "ambulance",
    "location": {"latitude": 34.0522, "longitude": -118.2437},
    "user_note": "Test emergency"
  }'
```

### Test Accounts (from seed data)

**Hospitals:**
- Email: admin@csmc.edu | Password: password123
- Email: admin@uclahealth.org | Password: password123

**Fire Stations:**
- Email: station1@lafd.org | Password: password123

**Police:**
- Email: central@lapd.org | Password: password123

## 🗺️ Data Preparation (ArcGIS Pro)

### Using ArcGIS Living Atlas

1. Open ArcGIS Pro project: `1_ARCGIS_PRO/EmergencyResponse.aprx`
2. Connect to ArcGIS Online (organizational account)
3. Add Living Atlas layers:
   - World Hospitals
   - Fire Stations
   - Police Stations
   - Road Networks
4. Filter by your area of interest
5. Export to PostGIS or GeoJSON
6. Import into database using provided scripts

### Alternative: Use Provided Test Data

The system includes test data for Los Angeles area with:
- 5 Hospitals
- 4 Fire Stations  
- 4 Police Stations

## 📈 System Features

### Core Features
- ✅ Real-time emergency request broadcasting
- ✅ Automatic nearest service selection
- ✅ WebSocket notifications
- ✅ Geospatial distance calculations
- ✅ Service provider authentication
- ✅ NO login required for users
- ✅ Interactive maps (Leaflet.js)
- ✅ Request status tracking

### Advanced Features (Optional)
- 🔄 Route visualization using pgRouting
- 📊 Analytics and logging (MongoDB)
- 🗺️ Service area polygons (isochrones)
- 📧 Email/SMS notifications
- 📱 Mobile responsive design

## 🔐 Security

- Passwords hashed with bcrypt
- JWT tokens for service authentication
- CORS protection
- Input validation with Pydantic
- SQL injection prevention (parameterized queries)
- WebSocket authentication

## 🐛 Troubleshooting

### Database Connection Failed
```bash
# Check PostgreSQL is running
sudo systemctl status postgresql

# Check connection settings in .env
cat 3_BACKEND/.env
```

### WebSocket Not Connecting
- Ensure backend is running on port 8000
- Check CORS settings in config
- Verify firewall allows port 8000

### No Services Found
```bash
# Load seed data
cd 2_DATABASE/postgis
sudo -u postgres psql -d emergency_response -f 7_seed_data.sql
```

## 📝 Development

### Adding New Service Types

1. Update database enum in `4_create_tables.sql`
2. Add mapping in `3_BACKEND/app/routers/requests.py`
3. Update frontend emergency types
4. Add icon and styling

### Customizing Location

1. Update `MAP_CENTER` in `config.js`
2. Load service data for your area
3. Import OSM road network for routing

## 📚 Documentation

See `5_DOCS/` folder for detailed guides:
- `1_SETUP_GUIDE.md` - Complete setup instructions
- `2_ARCGIS_PRO_WORKFLOW.md` - Data preparation guide
- `3_POSTGIS_SETUP.md` - Database configuration
- `4_BACKEND_GUIDE.md` - Backend development
- `5_FRONTEND_GUIDE.md` - Frontend development
- `6_TESTING_GUIDE.md` - Testing procedures
- `7_API_REFERENCE.md` - Complete API documentation

## 🤝 Contributing

This is a complete, production-ready system. Feel free to:
- Report bugs
- Suggest features
- Submit pull requests
- Improve documentation

## 📄 License

This project is open source and available for educational and commercial use.

## 🆘 Support

For issues or questions:
1. Check documentation in `5_DOCS/`
2. Review test scripts in `6_SCRIPTS/`
3. Check API docs at `/docs`
4. Review logs in MongoDB

## 🎯 Production Deployment

### Requirements
- Ubuntu 20.04+ or similar Linux server
- 2+ CPU cores
- 4GB+ RAM
- PostgreSQL/PostGIS/pgRouting
- MongoDB
- Nginx (reverse proxy)
- SSL certificate

### Steps
1. Setup databases on production server
2. Configure `.env` with production settings
3. Use `uvicorn` with gunicorn for backend
4. Setup Nginx reverse proxy
5. Enable HTTPS with Let's Encrypt
6. Configure firewall
7. Setup monitoring and logging

## 🌟 Features Roadmap

- [ ] Mobile app (React Native)
- [ ] Admin dashboard
- [ ] Historical analytics
- [ ] Service ratings
- [ ] Multi-language support
- [ ] SMS notifications
- [ ] Voice call integration
- [ ] Advanced routing algorithms

---

**Built with ❤️ for emergency response systems**

Version: 1.0.0  
Last Updated: November 2024
