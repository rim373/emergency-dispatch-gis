-- Emergency Response System - Enable pgRouting
-- Run this: sudo -u postgres psql -d emergency_response -f 3_enable_pgrouting.sql

-- Enable pgRouting extension
CREATE EXTENSION IF NOT EXISTS pgrouting;

-- Verify pgRouting installation
SELECT pgr_version();

\echo '✅ pgRouting enabled successfully!'
\echo 'Next: Run 4_create_tables.sql to create application tables'
