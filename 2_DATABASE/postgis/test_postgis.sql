-- Emergency Response System - Test PostGIS Setup
-- Run this: sudo -u postgres psql -d emergency_response -f test_postgis.sql

\echo '=========================================='
\echo 'Emergency Response System - Database Tests'
\echo '=========================================='
\echo ''

-- Test 1: Check Extensions
\echo '📦 TEST 1: Check Extensions'
SELECT extname, extversion FROM pg_extension WHERE extname IN ('postgis', 'pgrouting');
\echo ''

-- Test 2: List all tables
\echo '📋 TEST 2: List Tables'
SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' ORDER BY table_name;
\echo ''

-- Test 3: Count records
\echo '📊 TEST 3: Count Records'
SELECT 'service_providers' as table_name, COUNT(*) as records FROM service_providers
UNION ALL SELECT 'emergency_requests', COUNT(*) FROM emergency_requests
UNION ALL SELECT 'service_responses', COUNT(*) FROM service_responses
UNION ALL SELECT 'road_network', COUNT(*) FROM road_network;
\echo ''

-- Test 4: Test distance calculation function
\echo '🧮 TEST 4: Calculate Distance'
\echo 'Distance from Downtown LA to Santa Monica:'
SELECT calculate_distance(34.0522, -118.2437, 34.0195, -118.4912) as distance_km;
\echo ''

-- Test 5: Find nearest hospitals
\echo '🏥 TEST 5: Find Nearest Hospitals'
\echo 'Finding nearest hospitals to Downtown LA (34.0522, -118.2437):'
SELECT service_name, distance_km, contact_phone 
FROM find_nearest_services(34.0522, -118.2437, 'hospital', 50, 5);
\echo ''

-- Test 6: Find nearest fire stations
\echo '🚒 TEST 6: Find Nearest Fire Stations'
\echo 'Finding nearest fire stations to Downtown LA:'
SELECT service_name, distance_km, contact_phone 
FROM find_nearest_services(34.0522, -118.2437, 'fire_station', 50, 5);
\echo ''

-- Test 7: Find nearest police stations
\echo '🚓 TEST 7: Find Nearest Police Stations'
\echo 'Finding nearest police stations to Downtown LA:'
SELECT service_name, distance_km, contact_phone 
FROM find_nearest_services(34.0522, -118.2437, 'police_station', 50, 5);
\echo ''

-- Test 8: Get active requests
\echo '🚨 TEST 8: Active Emergency Requests'
SELECT request_id, request_type, status, user_note, created_at 
FROM emergency_requests 
WHERE status = 'pending'
ORDER BY created_at DESC;
\echo ''

-- Test 9: Test spatial indexes
\echo '🗺️  TEST 9: Spatial Indexes'
SELECT 
    schemaname,
    tablename,
    indexname,
    indexdef
FROM pg_indexes
WHERE tablename IN ('service_providers', 'emergency_requests', 'road_network')
    AND indexdef LIKE '%GIST%'
ORDER BY tablename;
\echo ''

-- Test 10: Service types distribution
\echo '📈 TEST 10: Service Types Distribution'
SELECT service_type, COUNT(*) as count, SUM(available_units) as total_units
FROM service_providers
GROUP BY service_type
ORDER BY count DESC;
\echo ''

\echo '=========================================='
\echo '✅ All tests completed!'
\echo '=========================================='
\echo ''
\echo '🎯 Quick Reference:'
\echo '  - Database: emergency_response'
\echo '  - User: emergency_app'
\echo '  - Password: emergency_pass_2024'
\echo ''
\echo '📝 Common Queries:'
\echo '  View all services:'
\echo '    SELECT service_id, service_name, service_type FROM service_providers;'
\echo ''
\echo '  View all requests:'
\echo '    SELECT request_id, request_type, status FROM emergency_requests;'
\echo ''
\echo '  Find nearest hospital:'
\echo '    SELECT * FROM find_nearest_services(34.0522, -118.2437, ''hospital'', 50, 1);'
\echo ''
