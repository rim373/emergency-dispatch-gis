-- Emergency Response System - Create All Tables
-- Run this: sudo -u postgres psql -d emergency_response -f 4_create_tables.sql

-- ==========================================
-- TABLE 1: Service Providers (Hospitals, Fire Stations, Police)
-- ==========================================
CREATE TABLE IF NOT EXISTS service_providers (
    id SERIAL PRIMARY KEY,
    service_id VARCHAR(50) UNIQUE NOT NULL,
    service_name VARCHAR(255) NOT NULL,
    service_type VARCHAR(50) NOT NULL CHECK (service_type IN ('hospital', 'fire_station', 'police_station')),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    contact_phone VARCHAR(50),
    address TEXT,
    latitude DECIMAL(10, 8) NOT NULL,
    longitude DECIMAL(11, 8) NOT NULL,
    location GEOMETRY(Point, 4326) NOT NULL,
    available_units INTEGER DEFAULT 1,
    is_online BOOLEAN DEFAULT true,
    service_area_radius_km DECIMAL(5, 2) DEFAULT 50.0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create spatial index on location
CREATE INDEX idx_service_providers_location ON service_providers USING GIST(location);
CREATE INDEX idx_service_providers_type ON service_providers(service_type);
CREATE INDEX idx_service_providers_online ON service_providers(is_online);

-- ==========================================
-- TABLE 2: Emergency Requests
-- ==========================================
CREATE TABLE IF NOT EXISTS emergency_requests (
    id SERIAL PRIMARY KEY,
    request_id VARCHAR(50) UNIQUE NOT NULL,
    request_type VARCHAR(50) NOT NULL CHECK (request_type IN ('ambulance', 'fire', 'police')),
    user_phone VARCHAR(50),
    user_note TEXT,
    latitude DECIMAL(10, 8) NOT NULL,
    longitude DECIMAL(11, 8) NOT NULL,
    location GEOMETRY(Point, 4326) NOT NULL,
    address TEXT,
    status VARCHAR(50) DEFAULT 'pending' CHECK (status IN ('pending', 'accepted', 'rejected', 'in_progress', 'completed', 'cancelled')),
    assigned_service_id INTEGER REFERENCES service_providers(id),
    estimated_arrival_time INTEGER, -- in minutes
    distance_km DECIMAL(8, 2), -- distance from assigned service
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    accepted_at TIMESTAMP,
    completed_at TIMESTAMP
);

-- Create spatial index on location
CREATE INDEX idx_emergency_requests_location ON emergency_requests USING GIST(location);
CREATE INDEX idx_emergency_requests_status ON emergency_requests(status);
CREATE INDEX idx_emergency_requests_type ON emergency_requests(request_type);
CREATE INDEX idx_emergency_requests_assigned ON emergency_requests(assigned_service_id);

-- ==========================================
-- TABLE 3: Service Responses (tracks which services responded)
-- ==========================================
CREATE TABLE IF NOT EXISTS service_responses (
    id SERIAL PRIMARY KEY,
    request_id INTEGER NOT NULL REFERENCES emergency_requests(id) ON DELETE CASCADE,
    service_id INTEGER NOT NULL REFERENCES service_providers(id) ON DELETE CASCADE,
    response_type VARCHAR(20) NOT NULL CHECK (response_type IN ('accepted', 'rejected')),
    distance_km DECIMAL(8, 2),
    estimated_time_minutes INTEGER,
    responded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    notes TEXT,
    UNIQUE(request_id, service_id)
);

ALTER TABLE emergency_requests 
ADD COLUMN IF NOT EXISTS accepted_at TIMESTAMP;

CREATE INDEX IF NOT EXISTS idx_emergency_requests_accepted_at 
ON emergency_requests(accepted_at);

CREATE INDEX idx_service_responses_request ON service_responses(request_id);
CREATE INDEX idx_service_responses_service ON service_responses(service_id);

-- ==========================================
-- TABLE 4: Road Network (for routing)
-- This will be populated from OSM data
-- ==========================================
CREATE TABLE IF NOT EXISTS road_network (
    id SERIAL PRIMARY KEY,
    osm_id BIGINT,
    name VARCHAR(255),
    highway VARCHAR(50),
    oneway VARCHAR(3),
    maxspeed INTEGER,
    length_meters DECIMAL(10, 2),
    source_vertex INTEGER,
    target_vertex INTEGER,
    cost DECIMAL(10, 4),
    reverse_cost DECIMAL(10, 4),
    geometry GEOMETRY(LineString, 4326) NOT NULL
);

-- Create spatial index
CREATE INDEX idx_road_network_geometry ON road_network USING GIST(geometry);
CREATE INDEX idx_road_network_source ON road_network(source_vertex);
CREATE INDEX idx_road_network_target ON road_network(target_vertex);

-- ==========================================
-- TABLE 5: Road Network Vertices (for pgRouting)
-- ==========================================
CREATE TABLE IF NOT EXISTS road_network_vertices (
    id SERIAL PRIMARY KEY,
    osm_id BIGINT,
    lon DECIMAL(11, 8),
    lat DECIMAL(10, 8),
    the_geom GEOMETRY(Point, 4326)
);

-- Create spatial index
CREATE INDEX idx_road_vertices_geom ON road_network_vertices USING GIST(the_geom);

-- ==========================================
-- TABLE 6: Request History Log
-- ==========================================
CREATE TABLE IF NOT EXISTS request_history (
    id SERIAL PRIMARY KEY,
    request_id INTEGER REFERENCES emergency_requests(id) ON DELETE CASCADE,
    status VARCHAR(50),
    notes TEXT,
    changed_by VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_request_history_request ON request_history(request_id);

-- ==========================================
-- TRIGGER: Update timestamp on row update
-- ==========================================
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_service_providers_updated_at BEFORE UPDATE ON service_providers
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_emergency_requests_updated_at BEFORE UPDATE ON emergency_requests
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ==========================================
-- Summary
-- ==========================================
\echo '✅ All tables created successfully!'
\echo ''
\echo '📊 Tables created:'
\echo '  - service_providers (with spatial index)'
\echo '  - emergency_requests (with spatial index)'
\echo '  - service_responses'
\echo '  - road_network (for routing)'
\echo '  - road_network_vertices (for pgRouting)'
\echo '  - request_history'
\echo ''
\echo 'Next: Run 5_import_osm_data.sql or 6_routing_functions.sql'
