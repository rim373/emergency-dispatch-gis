# Reserve/Standby Notification System

## Overview

The emergency response system now features an **intelligent reserve notification system** that keeps backup services on standby when multiple services accept the same request.

## How It Works

### Scenario

1. **User creates emergency request** (e.g., needs ambulance)
2. **System broadcasts** to all hospitals via WebSocket + MQTT
3. **Multiple hospitals accept** within 2-second window (e.g., Hospital A, B, and C)
4. **System calculates real distances** using OSRM road routing
5. **Nearest hospital assigned** (e.g., Hospital A - 2.5km away)
6. **Other hospitals become reserves** (Hospital B - 3.1km, Hospital C - 4.2km)

### Distance Calculation

The system uses **real road routing** (OSRM) for accurate distances:
- ✅ Accounts for actual road networks
- ✅ Provides realistic ETAs
- ✅ More accurate than straight-line distance
- ✅ Fallback to Haversine formula if OSRM unavailable

## Reserve Status Flow

```
[Multiple Services Accept]
         ↓
[Calculate Real Distances]
         ↓
[Assign to Nearest Service] ← Primary Service
         ↓
[Mark Others as Reserve] ← Backup Services
         ↓
[Active Standby Mode]
```

### Reserve Services Receive:
- ✅ Notification they're on reserve
- ✅ Which service was assigned (name + distance)
- ✅ Their own distance from incident
- ✅ Their reserve position (#1, #2, etc.)
- ✅ Continue monitoring until request completes

## Benefits

### For System Operators
- **Redundancy**: Backup services ready if primary fails
- **Better Coverage**: Multiple services aware of incident
- **Data Analytics**: Track response patterns and distances

### For Service Providers
- **Transparency**: Know why they weren't selected
- **Preparedness**: Can prepare in case primary service cancels
- **Situational Awareness**: Better understanding of demand

### For Users
- **Reliability**: Automatic failover if primary service cancels
- **Faster Response**: Reserve services already notified
- **Quality Assurance**: Nearest service always selected

## API Response Examples

### Service Assigned (Nearest)

**Request:**
```http
POST /api/requests/respond
Authorization: Bearer <token>
Content-Type: application/json

{
  "request_id": "REQ-ABC123",
  "response_type": "accepted"
}
```

**Response:**
```json
{
  "success": true,
  "response_type": "accepted",
  "assigned_to": "HOSP-001",
  "distance_km": 2.5,
  "eta_minutes": 8,
  "message": "You have been assigned to this request"
}
```

### Service on Reserve (Backup)

**Request:**
```http
POST /api/requests/respond
Authorization: Bearer <token>
Content-Type: application/json

{
  "request_id": "REQ-ABC123",
  "response_type": "accepted"
}
```

**Response:**
```json
{
  "success": true,
  "response_type": "reserve",
  "assigned_to": "HOSP-001",
  "your_distance_km": 3.1,
  "assigned_distance_km": 2.5,
  "message": "Request assigned to City General Hospital - You are on reserve",
  "reserve_position": 1
}
```

## WebSocket Events

### For Assigned Service

**Event:** `request_assigned_to_you`

```json
{
  "request_id": "REQ-ABC123",
  "distance_km": 2.5,
  "estimated_arrival_time": 8,
  "message": "You have been assigned to this emergency request"
}
```

### For Reserve Services

**Event:** `request_reserve_standby`

```json
{
  "request_id": "REQ-ABC123",
  "status": "reserve",
  "assigned_to_service": "City General Hospital",
  "your_distance_km": 3.1,
  "assigned_distance_km": 2.5,
  "message": "Request handled by City General Hospital - You're on reserve/standby",
  "reserve_position": 1,
  "total_reserves": 2
}
```

## MQTT Topics

### Assignment Notification

**Topic:** `emergency/requests/assigned/{request_id}`

**Payload:**
```json
{
  "assigned_service_id": "HOSP-001",
  "assigned_service_name": "City General Hospital",
  "request_id": "REQ-ABC123",
  "distance_km": 2.5,
  "estimated_arrival_time": 8
}
```

### Reserve Notification

**Topic:** `emergency/requests/reserve/{request_id}`

**Payload:**
```json
{
  "reserve_service_ids": ["HOSP-002", "HOSP-003"],
  "assigned_service_id": "HOSP-001",
  "assigned_service_name": "City General Hospital",
  "distances": {
    "HOSP-002": 3.1,
    "HOSP-003": 4.2
  },
  "message": "Request assigned to City General Hospital - You are on reserve"
}
```

### Individual Service Status

**Topic:** `emergency/services/status/{service_id}`

**Payload:**
```json
{
  "event": "request_reserve",
  "request_id": "REQ-ABC123",
  "assigned_to": "City General Hospital",
  "your_distance_km": 3.1,
  "message": "Request handled by City General Hospital - You're on reserve"
}
```

## Database Schema

### service_responses Table

```sql
CREATE TABLE service_responses (
    id SERIAL PRIMARY KEY,
    request_id INTEGER REFERENCES emergency_requests(id),
    service_id INTEGER REFERENCES service_providers(id),
    response_type VARCHAR(20) CHECK (response_type IN (
        'accepted',  -- Service accepted and assigned
        'rejected',  -- Service refused
        'canceled',  -- Another service took it
        'reserve'    -- On standby/backup
    )),
    distance_km DECIMAL(8, 2),
    estimated_time_minutes INTEGER,
    responded_at TIMESTAMP,
    notes TEXT,
    UNIQUE(request_id, service_id)
);
```

### Query Reserve Services

```sql
-- Get all reserve services for a request
SELECT
    sp.service_id,
    sp.service_name,
    sp.contact_phone,
    sr.distance_km,
    sr.estimated_time_minutes
FROM service_responses sr
JOIN service_providers sp ON sr.service_id = sp.id
WHERE sr.request_id = (SELECT id FROM emergency_requests WHERE request_id = 'REQ-ABC123')
    AND sr.response_type = 'reserve'
ORDER BY sr.distance_km ASC;
```

## Frontend Implementation

### Service Dashboard Updates

The service dashboard now displays two sections:

#### 1. Active Requests (Pending Accept/Reject)
```javascript
socket.on('new_emergency_request', (data) => {
    requests[data.request_id] = data;
    renderRequests();
});
```

#### 2. Reserve Requests (On Standby)
```javascript
socket.on('request_reserve_standby', (data) => {
    reserveRequests[data.request_id] = {
        ...data,
        timestamp: new Date().toISOString()
    };
    renderReserveRequests();
});
```

### Visual Indicators

- **Active Requests**: Green border, Accept/Reject buttons
- **Reserve Requests**: Orange border, "⏸️ RESERVE" badge, Dismiss button

### Notification System

```javascript
// Success (Assigned)
showNotification('✅ Request assigned to you!', 'success');

// Warning (Reserve)
showNotification('⏸️ Request assigned to another service - You\'re on reserve', 'warning');

// Info (Unavailable)
showNotification('Request already handled', 'info');
```

## Configuration

### 2-Second Window

The system uses a 2-second acceptance window. Adjust in database query:

```python
# In postgis.py
def get_recent_accepts(self, request_id: str, seconds: int = 2):
```

To change to 5 seconds:
```python
recent = db.get_recent_accepts(response.request_id, seconds=5)
```

### Distance Calculation Method

Edit `3_BACKEND/app/services/distance_calculator.py`:

```python
async def calculate_distance_and_eta(start_lat, start_lon, end_lat, end_lon):
    # Try OSRM first (real routing)
    route_info = await calculate_route_osrm(...)

    # Fallback to straight-line if OSRM fails
    if not route_info or not route_info['route_found']:
        distance = calculate_straight_line_distance(...)
```

## Testing Scenarios

### Test 1: Single Acceptance
1. Create emergency request
2. Single hospital accepts
3. **Expected:** Hospital immediately assigned (no reserves)

### Test 2: Multiple Acceptances
1. Create emergency request
2. Three hospitals accept within 2 seconds
3. **Expected:**
   - Nearest hospital assigned
   - Other two marked as reserve
   - All receive appropriate notifications

### Test 3: Staggered Acceptances
1. Create emergency request
2. Hospital A accepts immediately
3. Hospital B accepts after 3 seconds
4. **Expected:**
   - Hospital A assigned immediately (first accept)
   - Hospital B gets "already assigned" message

## Analytics and Reporting

### Query Response Patterns

```sql
-- Count response types
SELECT
    response_type,
    COUNT(*) as count
FROM service_responses
GROUP BY response_type;

-- Average distances for assigned vs reserve
SELECT
    response_type,
    AVG(distance_km) as avg_distance,
    MIN(distance_km) as min_distance,
    MAX(distance_km) as max_distance
FROM service_responses
WHERE response_type IN ('accepted', 'reserve')
GROUP BY response_type;

-- Services most often on reserve
SELECT
    sp.service_name,
    COUNT(*) as reserve_count
FROM service_responses sr
JOIN service_providers sp ON sr.service_id = sp.id
WHERE sr.response_type = 'reserve'
GROUP BY sp.service_name
ORDER BY reserve_count DESC;
```

## Best Practices

### For Service Providers

1. **Monitor Reserve Notifications**: Stay aware of nearby incidents
2. **Keep Reserve Window Open**: Don't dismiss immediately - primary might cancel
3. **Update Availability**: Set status offline if truly unavailable

### For System Administrators

1. **Adjust Time Window**: Based on response patterns in your area
2. **Monitor Reserve Rates**: High reserve rates might indicate over-capacity
3. **Track Distance Accuracy**: Verify OSRM routing vs actual response times

### For Development

1. **Log All Distances**: Keep logs of calculated distances for validation
2. **Test with Real Coordinates**: Use actual addresses in your deployment area
3. **Monitor OSRM Availability**: Implement alerts if OSRM service is down

## Troubleshooting

### Reserve Notifications Not Showing

1. **Check frontend console** for WebSocket events
2. **Verify `reserveList` div** exists in HTML
3. **Check `renderReserveRequests()` function** is defined

### Distance Calculation Issues

1. **Verify OSRM service** is accessible
2. **Check fallback logic** activates for straight-line distance
3. **Review logs** for distance calculation errors

### Database Constraints

If you get constraint errors:
```sql
-- Run schema update
\i 2_DATABASE/postgis/5_update_schema_for_reserve.sql
```

## Future Enhancements

Potential improvements:
- [ ] Auto-promote reserve to primary if primary cancels
- [ ] Time-based reserve expiration
- [ ] Reserve priority based on historical response times
- [ ] SMS/email notifications for reserve status
- [ ] Reserve service metrics dashboard