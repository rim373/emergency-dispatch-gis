-- Emergency Response System - Database Setup
-- Run this as postgres user: sudo -u postgres psql -f 2_setup_database.sql

-- Drop database if exists (BE CAREFUL!)
DROP DATABASE IF EXISTS emergency_response;

-- Create database
CREATE DATABASE emergency_response;

-- Connect to database
\c emergency_response;

-- Create PostGIS extension
CREATE EXTENSION IF NOT EXISTS postgis;

-- Create pgRouting extension (will be done in next script)
-- CREATE EXTENSION IF NOT EXISTS pgrouting;

-- Verify extensions
SELECT PostGIS_version();

-- Create application user
CREATE USER emergency_app WITH PASSWORD 'emergency_pass_2024';

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE emergency_response TO emergency_app;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO emergency_app;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO emergency_app;

-- Set default privileges for future tables
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO emergency_app;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO emergency_app;

\echo '✅ Database setup complete!'
\echo 'Database: emergency_response'
\echo 'User: emergency_app'
\echo 'Next: Run 3_enable_pgrouting.sql'
