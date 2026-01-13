-- ============================================
-- Schema Update for Reserve/Standby Feature
-- Adds support for reserve services tracking
-- ============================================

-- Update service_responses table to support reserve and canceled types
ALTER TABLE service_responses
DROP CONSTRAINT IF EXISTS service_responses_response_type_check;

ALTER TABLE service_responses
ADD CONSTRAINT service_responses_response_type_check
CHECK (response_type IN ('accepted', 'rejected', 'canceled', 'reserve'));

-- Create index for reserve lookups
CREATE INDEX IF NOT EXISTS idx_service_responses_reserve
ON service_responses(request_id, response_type)
WHERE response_type = 'reserve';

-- Add comment
COMMENT ON COLUMN service_responses.response_type IS
'Response type: accepted (assigned), rejected (refused), canceled (another service took it), reserve (on standby)';

COMMENT ON TABLE service_responses IS
'Tracks all service provider responses to emergency requests including reserve/standby status';