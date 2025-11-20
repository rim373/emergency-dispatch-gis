-- Emergency Response System - Seed Test Data
-- Run this: sudo -u postgres psql -d emergency_response -f 7_seed_data.sql

-- ==========================================
-- Insert Sample Service Providers (Los Angeles area)
-- ==========================================

-- Password for all test accounts: "password123"
-- Hashed with bcrypt: $2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5NU7RqAKHqAiu

-- HOSPITALS
INSERT INTO service_providers (service_id, service_name, service_type, email, password_hash, contact_phone, address, latitude, longitude, location, available_units, is_online) VALUES
('HOSP-001', 'Cedars-Sinai Medical Center', 'hospital', 'admin@csmc.edu', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5NU7RqAKHqAiu', '+1-310-423-5000', '8700 Beverly Blvd, Los Angeles, CA 90048', 34.0754, -118.3765, ST_SetSRID(ST_MakePoint(-118.3765, 34.0754), 4326), 5, true),
('HOSP-002', 'UCLA Medical Center', 'hospital', 'admin@uclahealth.org', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5NU7RqAKHqAiu', '+1-310-825-9111', '757 Westwood Plaza, Los Angeles, CA 90095', 34.0648, -118.4452, ST_SetSRID(ST_MakePoint(-118.4452, 34.0648), 4326), 4, true),
('HOSP-003', 'USC Medical Center', 'hospital', 'admin@uscmed.org', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5NU7RqAKHqAiu', '+1-323-442-8500', '1500 San Pablo St, Los Angeles, CA 90033', 34.0581, -118.2113, ST_SetSRID(ST_MakePoint(-118.2113, 34.0581), 4326), 6, true),
('HOSP-004', 'Providence Saint Johns Health Center', 'hospital', 'admin@providence.org', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5NU7RqAKHqAiu', '+1-310-829-5511', '2121 Santa Monica Blvd, Santa Monica, CA 90404', 34.0335, -118.4788, ST_SetSRID(ST_MakePoint(-118.4788, 34.0335), 4326), 3, true),
('HOSP-005', 'Good Samaritan Hospital', 'hospital', 'admin@goodsam.org', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5NU7RqAKHqAiu', '+1-213-977-2121', '1225 Wilshire Blvd, Los Angeles, CA 90017', 34.0522, -118.2655, ST_SetSRID(ST_MakePoint(-118.2655, 34.0522), 4326), 4, true);

-- FIRE STATIONS
INSERT INTO service_providers (service_id, service_name, service_type, email, password_hash, contact_phone, address, latitude, longitude, location, available_units, is_online) VALUES
('FIRE-001', 'LAFD Fire Station 1', 'fire_station', 'station1@lafd.org', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5NU7RqAKHqAiu', '+1-213-485-6185', '1355 N Cahuenga Blvd, Los Angeles, CA 90028', 34.0963, -118.3287, ST_SetSRID(ST_MakePoint(-118.3287, 34.0963), 4326), 3, true),
('FIRE-002', 'LAFD Fire Station 9', 'fire_station', 'station9@lafd.org', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5NU7RqAKHqAiu', '+1-213-485-6109', '2300 E 1st St, Los Angeles, CA 90033', 34.0384, -118.2236, ST_SetSRID(ST_MakePoint(-118.2236, 34.0384), 4326), 2, true),
('FIRE-003', 'LAFD Fire Station 27', 'fire_station', 'station27@lafd.org', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5NU7RqAKHqAiu', '+1-213-485-6127', '2727 S Hoover St, Los Angeles, CA 90007', 34.0265, -118.2859, ST_SetSRID(ST_MakePoint(-118.2859, 34.0265), 4326), 2, true),
('FIRE-004', 'Santa Monica Fire Station 1', 'fire_station', 'station1@smfd.org', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5NU7RqAKHqAiu', '+1-310-458-8427', '1337 7th St, Santa Monica, CA 90401', 34.0156, -118.4912, ST_SetSRID(ST_MakePoint(-118.4912, 34.0156), 4326), 2, true);

-- POLICE STATIONS
INSERT INTO service_providers (service_id, service_name, service_type, email, password_hash, contact_phone, address, latitude, longitude, location, available_units, is_online) VALUES
('POL-001', 'LAPD Central Division', 'police_station', 'central@lapd.org', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5NU7RqAKHqAiu', '+1-213-972-1298', '251 E 6th St, Los Angeles, CA 90014', 34.0452, -118.2468, ST_SetSRID(ST_MakePoint(-118.2468, 34.0452), 4326), 10, true),
('POL-002', 'LAPD Hollywood Division', 'police_station', 'hollywood@lapd.org', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5NU7RqAKHqAiu', '+1-213-972-2971', '1358 N Wilcox Ave, Los Angeles, CA 90028', 34.0958, -118.3387, ST_SetSRID(ST_MakePoint(-118.3387, 34.0958), 4326), 8, true),
('POL-003', 'LAPD Rampart Division', 'police_station', 'rampart@lapd.org', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5NU7RqAKHqAiu', '+1-213-972-8401', '1401 W 6th St, Los Angeles, CA 90017', 34.0547, -118.2644, ST_SetSRID(ST_MakePoint(-118.2644, 34.0547), 4326), 9, true),
('POL-004', 'Santa Monica Police Department', 'police_station', 'admin@smpd.org', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5NU7RqAKHqAiu', '+1-310-458-8491', '333 Olympic Dr, Santa Monica, CA 90401', 34.0104, -118.4803, ST_SetSRID(ST_MakePoint(-118.4803, 34.0104), 4326), 7, true);

-- ==========================================
-- Insert Sample Emergency Requests
-- ==========================================
INSERT INTO emergency_requests (request_id, request_type, user_phone, user_note, latitude, longitude, location, address, status) VALUES
('REQ-001', 'ambulance', '+1-555-0101', 'Severe chest pain, difficulty breathing', 34.0522, -118.2437, ST_SetSRID(ST_MakePoint(-118.2437, 34.0522), 4326), 'Downtown Los Angeles, CA', 'pending'),
('REQ-002', 'fire', '+1-555-0102', 'Small kitchen fire', 34.0689, -118.4452, ST_SetSRID(ST_MakePoint(-118.4452, 34.0689), 4326), 'Westwood, Los Angeles, CA', 'pending'),
('REQ-003', 'police', '+1-555-0103', 'Suspicious activity reported', 34.0417, -118.2468, ST_SetSRID(ST_MakePoint(-118.2468, 34.0417), 4326), 'Downtown Los Angeles, CA', 'pending');

-- ==========================================
-- Verify Data
-- ==========================================
SELECT 'Service Providers:' as info, COUNT(*) as count FROM service_providers
UNION ALL
SELECT 'Hospitals:', COUNT(*) FROM service_providers WHERE service_type = 'hospital'
UNION ALL
SELECT 'Fire Stations:', COUNT(*) FROM service_providers WHERE service_type = 'fire_station'
UNION ALL
SELECT 'Police Stations:', COUNT(*) FROM service_providers WHERE service_type = 'police_station'
UNION ALL
SELECT 'Emergency Requests:', COUNT(*) FROM emergency_requests;

\echo ''
\echo '✅ Seed data inserted successfully!'
\echo ''
\echo '📊 Test Data Summary:'
\echo '  - 5 Hospitals'
\echo '  - 4 Fire Stations'
\echo '  - 4 Police Stations'
\echo '  - 3 Sample Emergency Requests'
\echo ''
\echo '🔐 Login credentials for testing:'
\echo '  Email: admin@csmc.edu (or any other email above)'
\echo '  Password: password123'
\echo ''
\echo 'Next: Run test_postgis.sql to verify everything works'
