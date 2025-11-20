-- Emergency Response System - Import OSM Road Data
-- This script provides instructions for importing OpenStreetMap data

-- ==========================================
-- OPTION 1: Using osm2pgrouting (Recommended)
-- ==========================================
-- Download OSM data for your area from https://download.geofabrik.de/
-- For example, Tunisia: https://download.geofabrik.de/africa/tunisia-latest.osm.pbf
-- Or USA (California): https://download.geofabrik.de/north-america/us/california-latest.osm.pbf

-- Command to import (run in terminal):
-- osm2pgrouting \
--   --file /path/to/california-latest.osm.pbf \
--   --dbname emergency_response \
--   --username emergency_app \
--   --password emergency_pass_2024 \
--   --host localhost \
--   --port 5432 \
--   --clean

-- This will create tables:
-- - ways (roads)
-- - ways_vertices_pgr (vertices for routing)

-- ==========================================
-- OPTION 2: Using osm2pgsql (Alternative)
-- ==========================================
-- Install: sudo apt install osm2pgsql
-- Import: osm2pgsql -d emergency_response -U emergency_app california-latest.osm.pbf

-- ==========================================
-- OPTION 3: Manual small dataset for testing
-- ==========================================
-- If you want to test without OSM data, create a simple road network:

-- Insert test roads in Los Angeles area
INSERT INTO road_network (name, highway, length_meters, source_vertex, target_vertex, cost, reverse_cost, geometry)
VALUES
    ('Main St', 'primary', 1000, 1, 2, 1.0, 1.0, 
     ST_GeomFromText('LINESTRING(-118.2437 34.0522, -118.2337 34.0522)', 4326)),
    ('Broadway', 'primary', 1500, 2, 3, 1.5, 1.5,
     ST_GeomFromText('LINESTRING(-118.2337 34.0522, -118.2337 34.0672)', 4326)),
    ('5th Ave', 'secondary', 800, 3, 4, 0.8, 0.8,
     ST_GeomFromText('LINESTRING(-118.2337 34.0672, -118.2437 34.0672)', 4326)),
    ('Hill St', 'secondary', 1000, 4, 1, 1.0, 1.0,
     ST_GeomFromText('LINESTRING(-118.2437 34.0672, -118.2437 34.0522)', 4326));

-- Insert corresponding vertices
INSERT INTO road_network_vertices (osm_id, lon, lat, the_geom)
VALUES
    (1, -118.2437, 34.0522, ST_GeomFromText('POINT(-118.2437 34.0522)', 4326)),
    (2, -118.2337, 34.0522, ST_GeomFromText('POINT(-118.2337 34.0522)', 4326)),
    (3, -118.2337, 34.0672, ST_GeomFromText('POINT(-118.2337 34.0672)', 4326)),
    (4, -118.2437, 34.0672, ST_GeomFromText('POINT(-118.2437 34.0672)', 4326));

-- ==========================================
-- Verify data
-- ==========================================
SELECT COUNT(*) as total_roads FROM road_network;
SELECT COUNT(*) as total_vertices FROM road_network_vertices;

\echo '✅ Road network setup instructions provided!'
\echo ''
\echo '📝 To import real OSM data:'
\echo '1. Download OSM data: https://download.geofabrik.de/'
\echo '2. Install osm2pgrouting: sudo apt install osm2pgrouting'
\echo '3. Run: osm2pgrouting --file data.osm.pbf --dbname emergency_response --username emergency_app --clean'
\echo ''
\echo 'Next: Run 6_routing_functions.sql to create routing functions'
