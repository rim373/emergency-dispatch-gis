-- Fix coordinates for Kwong Wah Hospital
-- Real coordinates: 22.3193, 114.1694 (Mong Kok, Hong Kong)

UPDATE service_providers
SET
    latitude = 22.3193,
    longitude = 114.1694,
    location = ST_SetSRID(ST_MakePoint(114.1694, 22.3193), 4326)
WHERE service_name LIKE '%Kwong Wah%' OR email LIKE '%kwong%';

-- Verify the update
SELECT service_id, service_name, email, latitude, longitude
FROM service_providers
WHERE service_name LIKE '%Kwong Wah%' OR email LIKE '%kwong%';