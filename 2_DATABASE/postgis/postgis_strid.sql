-- Fix PostGIS SRID 4326 Issue
-- Run this in pgAdmin Query Tool

-- Enable PostGIS extension if not already enabled
CREATE EXTENSION IF NOT EXISTS postgis;

-- Insert SRID 4326 (WGS 84) if it doesn't exist
INSERT INTO spatial_ref_sys (srid, auth_name, auth_srid, proj4text, srtext)
VALUES (
    4326,
    'EPSG',
    4326,
    '+proj=longlat +datum=WGS84 +no_defs',
    'GEOGCS["WGS 84",DATUM["WGS_1984",SPHEROID["WGS 84",6378137,298.257223563,AUTHORITY["EPSG","7030"]],AUTHORITY["EPSG","6326"]],PRIMEM["Greenwich",0,AUTHORITY["EPSG","8901"]],UNIT["degree",0.0174532925199433,AUTHORITY["EPSG","9122"]],AUTHORITY["EPSG","4326"]]'
)
ON CONFLICT (srid) DO NOTHING;

-- Verify it's there
SELECT srid, auth_name, auth_srid 
FROM spatial_ref_sys 
WHERE srid = 4326;

-- This should return one row with SRID 4326