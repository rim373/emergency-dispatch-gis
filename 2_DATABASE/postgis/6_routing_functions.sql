-- Emergency Response System - Routing and Spatial Functions
-- Run this: sudo -u postgres psql -d emergency_response -f 6_routing_functions.sql

-- ==========================================
-- FUNCTION 1: Calculate straight-line distance between two points
-- ==========================================
CREATE OR REPLACE FUNCTION calculate_distance(
    lat1 DECIMAL,
    lon1 DECIMAL,
    lat2 DECIMAL,
    lon2 DECIMAL
)
RETURNS DECIMAL AS $$
DECLARE
    distance_km DECIMAL;
BEGIN
    -- Calculate distance in kilometers using PostGIS geography type
    SELECT ST_Distance(
        ST_MakePoint(lon1, lat1)::geography,
        ST_MakePoint(lon2, lat2)::geography
    ) / 1000.0 INTO distance_km;
    
    RETURN ROUND(distance_km, 2);
END;
$$ LANGUAGE plpgsql;

-- ==========================================
-- FUNCTION 2: Find nearest service providers
-- ==========================================
CREATE OR REPLACE FUNCTION find_nearest_services(
    user_lat DECIMAL,
    user_lon DECIMAL,
    service_type_filter VARCHAR,
    max_distance_km DECIMAL DEFAULT 50.0,
    limit_count INTEGER DEFAULT 5
)
RETURNS TABLE (
    service_id VARCHAR,
    service_name VARCHAR,
    service_type VARCHAR,
    contact_phone VARCHAR,
    address TEXT,
    latitude DECIMAL,
    longitude DECIMAL,
    distance_km DECIMAL,
    is_online BOOLEAN,
    available_units INTEGER
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        sp.service_id,
        sp.service_name,
        sp.service_type,
        sp.contact_phone,
        sp.address,
        sp.latitude,
        sp.longitude,
        ROUND(
            (ST_Distance(
                sp.location::geography,
                ST_MakePoint(user_lon, user_lat)::geography
            ) / 1000.0)::NUMERIC, 
            2
        ) as distance_km,
        sp.is_online,
        sp.available_units
    FROM service_providers sp
    WHERE sp.service_type = service_type_filter
        AND sp.is_online = true
        AND sp.available_units > 0
        AND ST_DWithin(
            sp.location::geography,
            ST_MakePoint(user_lon, user_lat)::geography,
            max_distance_km * 1000  -- convert km to meters
        )
    ORDER BY sp.location <-> ST_MakePoint(user_lon, user_lat)::geometry
    LIMIT limit_count;
END;
$$ LANGUAGE plpgsql;

-- ==========================================
-- FUNCTION 3: Calculate route using pgRouting (Dijkstra)
-- Note: This requires road network data to be loaded
-- ==========================================
CREATE OR REPLACE FUNCTION calculate_route(
    start_lat DECIMAL,
    start_lon DECIMAL,
    end_lat DECIMAL,
    end_lon DECIMAL
)
RETURNS TABLE (
    seq INTEGER,
    path_seq INTEGER,
    node BIGINT,
    edge BIGINT,
    cost DOUBLE PRECISION,
    agg_cost DOUBLE PRECISION,
    geom GEOMETRY
) AS $$
DECLARE
    start_vertex INTEGER;
    end_vertex INTEGER;
    route_exists BOOLEAN;
BEGIN
    -- Check if road network exists
    SELECT EXISTS (SELECT 1 FROM road_network LIMIT 1) INTO route_exists;
    
    IF NOT route_exists THEN
        RAISE NOTICE 'Road network not loaded. Cannot calculate route.';
        RETURN;
    END IF;

    -- Find nearest vertex to start point
    SELECT id INTO start_vertex
    FROM road_network_vertices
    ORDER BY the_geom <-> ST_SetSRID(ST_MakePoint(start_lon, start_lat), 4326)
    LIMIT 1;

    -- Find nearest vertex to end point
    SELECT id INTO end_vertex
    FROM road_network_vertices
    ORDER BY the_geom <-> ST_SetSRID(ST_MakePoint(end_lon, end_lat), 4326)
    LIMIT 1;

    -- Calculate route using Dijkstra algorithm
    RETURN QUERY
    SELECT 
        r.seq,
        r.path_seq,
        r.node,
        r.edge,
        r.cost,
        r.agg_cost,
        rn.geometry as geom
    FROM pgr_dijkstra(
        'SELECT id, source_vertex as source, target_vertex as target, cost, reverse_cost FROM road_network',
        start_vertex,
        end_vertex,
        directed := true
    ) r
    LEFT JOIN road_network rn ON r.edge = rn.id;
END;
$$ LANGUAGE plpgsql;

-- ==========================================
-- FUNCTION 4: Get service provider by ID
-- ==========================================
CREATE OR REPLACE FUNCTION get_service_by_id(
    search_service_id VARCHAR
)
RETURNS TABLE (
    id INTEGER,
    service_id VARCHAR,
    service_name VARCHAR,
    service_type VARCHAR,
    email VARCHAR,
    contact_phone VARCHAR,
    address TEXT,
    latitude DECIMAL,
    longitude DECIMAL,
    available_units INTEGER,
    is_online BOOLEAN
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        sp.id,
        sp.service_id,
        sp.service_name,
        sp.service_type,
        sp.email,
        sp.contact_phone,
        sp.address,
        sp.latitude,
        sp.longitude,
        sp.available_units,
        sp.is_online
    FROM service_providers sp
    WHERE sp.service_id = search_service_id;
END;
$$ LANGUAGE plpgsql;

-- ==========================================
-- FUNCTION 5: Get all active emergency requests
-- ==========================================
CREATE OR REPLACE FUNCTION get_active_requests(
    filter_service_type VARCHAR DEFAULT NULL
)
RETURNS TABLE (
    request_id VARCHAR,
    request_type VARCHAR,
    user_phone VARCHAR,
    user_note TEXT,
    latitude DECIMAL,
    longitude DECIMAL,
    address TEXT,
    status VARCHAR,
    created_at TIMESTAMP,
    assigned_service_name VARCHAR
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        er.request_id,
        er.request_type,
        er.user_phone,
        er.user_note,
        er.latitude,
        er.longitude,
        er.address,
        er.status,
        er.created_at,
        sp.service_name as assigned_service_name
    FROM emergency_requests er
    LEFT JOIN service_providers sp ON er.assigned_service_id = sp.id
    WHERE er.status IN ('pending', 'accepted', 'in_progress')
        AND (filter_service_type IS NULL OR 
             (er.request_type = 'ambulance' AND filter_service_type = 'hospital') OR
             (er.request_type = 'fire' AND filter_service_type = 'fire_station') OR
             (er.request_type = 'police' AND filter_service_type = 'police_station'))
    ORDER BY er.created_at DESC;
END;
$$ LANGUAGE plpgsql;

-- ==========================================
-- Test Functions
-- ==========================================
\echo '✅ All routing functions created successfully!'
\echo ''
\echo '📝 Available functions:'
\echo '  - calculate_distance(lat1, lon1, lat2, lon2)'
\echo '  - find_nearest_services(lat, lon, type, max_dist, limit)'
\echo '  - calculate_route(start_lat, start_lon, end_lat, end_lon)'
\echo '  - get_service_by_id(service_id)'
\echo '  - get_active_requests(service_type)'
\echo ''
\echo 'Test example:'
\echo '  SELECT * FROM calculate_distance(34.0522, -118.2437, 34.0754, -118.3765);'
\echo ''
\echo 'Next: Run 7_seed_data.sql to add test data'
