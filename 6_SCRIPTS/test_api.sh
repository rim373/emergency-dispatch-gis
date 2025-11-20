#!/bin/bash
# Test Emergency Response System API

API_URL="http://localhost:8000"

echo "🧪 Testing Emergency Response System API"
echo "========================================"
echo ""

# Test 1: Health Check
echo "1️⃣ Health Check:"
curl -s "${API_URL}/health" | python3 -m json.tool
echo ""

# Test 2: Get System Stats
echo "2️⃣ System Statistics:"
curl -s "${API_URL}/api/stats" | python3 -m json.tool
echo ""

# Test 3: Get All Services
echo "3️⃣ Get All Services:"
curl -s "${API_URL}/api/services?limit=3" | python3 -m json.tool
echo ""

# Test 4: Create Emergency Request
echo "4️⃣ Create Emergency Request:"
curl -s -X POST "${API_URL}/api/requests/create" \
  -H "Content-Type: application/json" \
  -d '{
    "request_type": "ambulance",
    "location": {
      "latitude": 34.0522,
      "longitude": -118.2437,
      "address": "Downtown Los Angeles"
    },
    "user_phone": "+1-555-TEST",
    "user_note": "API Test Request"
  }' | python3 -m json.tool
echo ""

echo "✅ All API tests completed!"
