# Testing Guide - Route Visualization & Service Location Features

## 🎯 What Was Fixed

### Issues Resolved:
1. ✅ **Service Location Marker** - Each service provider now sees their location on the map
2. ✅ **Route Visualization** - Blue/Red/Orange line appears between service provider and user when request is accepted
3. ✅ **Car Animation** - Animated vehicle (🚑/🚒/🚓) travels along the route path
4. ✅ **Police Station Support** - All service types (hospital, fire, police) properly supported

---

## 🚀 Quick Test Steps

### Step 1: Restart Backend (IMPORTANT!)

You need to restart the backend because we updated the login API to include service coordinates:

```bash
cd 3_BACKEND
python -m uvicorn app.main:sio_app --reload
```

**Expected output:**
```
🚀 Starting Emergency Response System...
📊 PostgreSQL: localhost:5432
📊 MongoDB: localhost:27017
📡 MQTT Broker: localhost:1883
✅ MQTT broker connected (or ⚠️ will retry if Mosquitto not running)
```

### Step 2: Login to Service Dashboard

**IMPORTANT: You must logout and login again** to get your service coordinates stored!

1. Open browser: `http://localhost:8000/service/login.html`
2. Login with any service provider account
3. **Check localStorage** (F12 → Console):
   ```javascript
   console.log('Service Lat:', localStorage.getItem('serviceLat'));
   console.log('Service Lng:', localStorage.getItem('serviceLng'));
   ```
   Both should show numbers (not null)!

### Step 3: Verify Service Location Marker

After logging in, you should see on the map:
- Your service location marked with a colored circle and emoji:
  - 🏥 Hospital (Red circle)
  - 🚒 Fire Station (Orange circle)
  - 🚓 Police Station (Blue circle)
- Map centered on your location
- Click the marker to see popup with your service details

### Step 4: Test Route Visualization

1. **Open TWO browser windows side by side:**
   - Window 1: Service Dashboard (`http://localhost:8000/service/dashboard.html`)
   - Window 2: User Interface (`http://localhost:8000/user/`)

2. **In User Window:**
   - Click somewhere on the map to set location
   - Select request type (Ambulance/Fire/Police)
   - Click "Request Emergency Service"

3. **In Service Window:**
   - Wait for request to appear in right panel
   - Click "✓ Accept"

4. **Expected Result:**
   You should see:
   - ✅ Route line appears (colored based on service type)
   - ✅ Arrows along the route showing direction
   - ✅ Animated vehicle icon at your location
   - ✅ Vehicle travels along the route to user location
   - ✅ Notification shows distance and ETA
   - ✅ Animation completes when vehicle reaches destination

---

## 🎨 Visual Reference

### What You Should See:

```
Service Dashboard Map:
┌─────────────────────────────────────┐
│                                     │
│    🏥 ← Your Location (Red circle)  │
│     │                               │
│     │ ← Animated ambulance 🚑       │
│     │ (travels along blue route)    │
│     ════════════→                   │
│    /                                │
│   /                                 │
│  ════════════→                      │
│               \                     │
│                🆘 ← User Location   │
│                                     │
└─────────────────────────────────────┘
```

### Browser Console Logs

**When route appears, you should see:**
```
🗺️ Showing route from [22.3193, 114.1694] to [22.2800, 114.1580]
📍 Fetching route from [22.3193, 114.1694] to [22.2800, 114.1580]
✅ Route fetched: 4.5 km, 12 min
✅ Route animation completed for REQ-ABC123
```

**If there are problems:**
```
❌ showRouteAndAnimate function not found. Is route-animation.js loaded?
⚠️ Service or request location not available for route visualization
```

---

## 🐛 Troubleshooting

### Problem 1: Service location marker not showing

**Symptoms:** Map loads but no service marker appears

**Solution:**
1. Check localStorage:
   ```javascript
   localStorage.getItem('serviceLat')
   localStorage.getItem('serviceLng')
   ```
2. If null → **Logout and login again**
3. Backend must be restarted with updated code

### Problem 2: Route not appearing after accepting request

**Symptoms:** Request accepted but no route line appears

**Debug Steps:**

1. **Check if route-animation.js is loaded:**
   ```javascript
   typeof showRouteAndAnimate // Should be 'function'
   ```

2. **Check service coordinates:**
   ```javascript
   localStorage.getItem('serviceLat')  // Should be a number
   localStorage.getItem('serviceLng')  // Should be a number
   ```

3. **Check browser console** for error messages

4. **Check route-animation.js file exists:**
   ```
   4_FRONTEND/service/js/route-animation.js
   ```

5. **Hard refresh the page:** Ctrl+F5 (Windows) or Cmd+Shift+R (Mac)

### Problem 3: OSRM errors (route falls back to straight line)

**Symptoms:** Route appears as straight line, no road following

**Explanation:** This is normal! OSRM public server may be slow or blocked

**What happens:**
- System tries OSRM first
- If fails → falls back to straight-line distance
- Still shows route and animation, just not following roads

**To use real routing:**
- Use your own OSRM server (see ROUTE_VISUALIZATION.md)
- Or wait for public OSRM to be available

### Problem 4: Car animation doesn't move

**Symptoms:** Route appears, car marker appears, but doesn't animate

**Debug:**
```javascript
// In browser console
console.log(animationInterval);  // Should be a number
console.log(routeCoordinates.length);  // Should be > 1
```

**Solutions:**
- Hard refresh page (Ctrl+F5)
- Check if Leaflet Polyline Decorator loaded:
  ```javascript
  typeof L.polylineDecorator  // Should be 'function'
  ```

### Problem 5: Wrong service type marker color

**Symptoms:** Police station shows red instead of blue

**Check:**
```javascript
localStorage.getItem('serviceType')
```

**Should be one of:**
- `hospital` or `ambulance` → Red 🏥/🚑
- `fire_station` or `fire` → Orange 🚒
- `police_station` or `police` → Blue 🚓

---

## 🧪 Testing Checklist

Use this checklist to verify everything works:

### Basic Functionality
- [ ] Backend starts without errors
- [ ] Login as service provider works
- [ ] Service coordinates stored in localStorage
- [ ] Map centers on service location
- [ ] Service location marker appears on map
- [ ] Service marker has correct color and emoji

### Route Visualization
- [ ] User can create emergency request
- [ ] Service receives request notification
- [ ] Accept button works
- [ ] Route line appears on map after accepting
- [ ] Route has correct color for service type
- [ ] Directional arrows appear on route
- [ ] Map fits route (shows both endpoints)

### Car Animation
- [ ] Vehicle marker appears at service location
- [ ] Vehicle has correct emoji (🚑/🚒/🚓)
- [ ] Vehicle starts moving along route
- [ ] Vehicle rotates to face direction of travel
- [ ] Vehicle reaches destination
- [ ] Animation completes successfully

### Notifications
- [ ] "🗺️ Calculating route..." appears
- [ ] Distance and ETA shown (e.g., "📏 4.5 km • ⏱️ 12 min")
- [ ] "🏁 Service arrived at destination!" appears when done

### Multiple Service Types
- [ ] Test with Hospital/Ambulance (Red route)
- [ ] Test with Fire Station (Orange route)
- [ ] Test with Police Station (Blue route)

---

## 📞 Common Questions

**Q: Do I need to restart the backend every time?**
A: No, only when you first update the code. After that, you can test multiple times.

**Q: Why do I need to logout and login again?**
A: The login API was updated to return coordinates. Old login sessions don't have this data.

**Q: Can I test with multiple services at once?**
A: Yes! Open multiple service dashboards in different browser windows. The nearest one will be assigned.

**Q: What if OSRM doesn't work?**
A: The system automatically falls back to straight-line routes. Animation still works!

**Q: How do I clear old route visualization?**
A: The route automatically clears when you accept a new request.

---

## 🎬 Full Test Scenario

### Complete End-to-End Test:

1. **Start backend** (with updated code)
2. **Open 3 browser windows:**
   - Window 1: Hospital service
   - Window 2: Fire service
   - Window 3: User interface

3. **Login to both services** (logout first if needed)
4. **Verify markers** appear on both service maps
5. **Create ambulance request** from user window
6. **Accept in hospital window** - should show route
7. **Create fire request** from user window
8. **Accept in fire window** - should show orange route
9. **Watch both animations** complete

---

## 📝 Notes

- Route animation duration: 15 seconds (configurable in code)
- OSRM timeout: 10 seconds before fallback
- Service marker z-index: 1000 (always on top)
- Route line width: 5 pixels
- Car marker size: 30x30 pixels

---

**If you encounter any issues not covered here, check the browser console for error messages and refer to ROUTE_VISUALIZATION.md for detailed configuration options.**