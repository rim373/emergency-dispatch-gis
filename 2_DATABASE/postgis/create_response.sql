-- Create table to track service responses to requests
-- Run this in pgAdmin Query Tool

CREATE TABLE IF NOT EXISTS request_responses (
    id SERIAL PRIMARY KEY,
    request_id VARCHAR(50) NOT NULL,
    service_id VARCHAR(50) NOT NULL,
    action VARCHAR(20) NOT NULL,  -- accept, refuse, canceled
    distance_km NUMERIC(10, 2),
    eta_minutes INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (request_id) REFERENCES emergency_requests(request_id) ON DELETE CASCADE,
    FOREIGN KEY (service_id) REFERENCES service_providers(service_id) ON DELETE CASCADE,
    
    UNIQUE(request_id, service_id)  -- One response per service per request
);

-- Add index for faster queries
CREATE INDEX IF NOT EXISTS idx_request_responses_request_id ON request_responses(request_id);
CREATE INDEX IF NOT EXISTS idx_request_responses_created_at ON request_responses(created_at);

-- Verify table was created
SELECT * FROM request_responses LIMIT 1;