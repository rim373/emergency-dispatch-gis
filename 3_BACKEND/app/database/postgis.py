"""
Emergency Response System - PostgreSQL/PostGIS Database Connection
Handles all spatial database operations
"""

import psycopg2
from psycopg2.extras import RealDictCursor
from psycopg2.pool import SimpleConnectionPool
from contextlib import contextmanager
from typing import List, Dict, Optional, Tuple
from datetime import datetime
import logging

from app.config import settings

logger = logging.getLogger(__name__)


class PostGISDatabase:
    """PostgreSQL/PostGIS database connection manager"""
    
    def __init__(self):
        """Initialize connection pool"""
        self.pool = None
        self._initialize_pool()
    
    def _initialize_pool(self):
        """Create connection pool"""
        try:
            self.pool = SimpleConnectionPool(
                minconn=1,
                maxconn=10,
                host=settings.POSTGRES_HOST,
                port=settings.POSTGRES_PORT,
                database=settings.POSTGRES_DB,
                user=settings.POSTGRES_USER,
                password=settings.POSTGRES_PASSWORD
            )
            logger.info("PostgreSQL connection pool created successfully")
        except Exception as e:
            logger.error(f"Failed to create connection pool: {e}")
            raise
    
    @contextmanager
    def get_connection(self):
        """Context manager for database connections"""
        conn = self.pool.getconn()
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"Database error: {e}")
            raise
        finally:
            self.pool.putconn(conn)
    
    @contextmanager
    def get_cursor(self, cursor_factory=RealDictCursor):
        """Context manager for database cursor"""
        with self.get_connection() as conn:
            cursor = conn.cursor(cursor_factory=cursor_factory)
            try:
                yield cursor
            finally:
                cursor.close()
    
    # ==========================================
    # Service Provider Operations
    # ==========================================
    
    def create_service_provider(self, data: Dict) -> Dict:
        """Create new service provider"""
        with self.get_cursor() as cursor:
            cursor.execute("""
                INSERT INTO service_providers (
                    service_id, service_name, service_type, email, password_hash,
                    contact_phone, address, latitude, longitude, location, available_units
                )
                VALUES (
                    %(service_id)s, %(service_name)s, %(service_type)s, %(email)s, 
                    %(password_hash)s, %(contact_phone)s, %(address)s, %(latitude)s, 
                    %(longitude)s, ST_SetSRID(ST_MakePoint(%(longitude)s, %(latitude)s), 4326),
                    %(available_units)s
                )
                RETURNING id, service_id, service_name, service_type, email, 
                          contact_phone, latitude, longitude, available_units, created_at
            """, data)
            return cursor.fetchone()
    
    def get_service_by_email(self, email: str) -> Optional[Dict]:
        """Get service provider by email"""
        with self.get_cursor() as cursor:
            cursor.execute("""
                SELECT id, service_id, service_name, service_type, email, password_hash,
                       contact_phone, address, latitude, longitude, available_units, is_online
                FROM service_providers
                WHERE email = %s
            """, (email,))
            return cursor.fetchone()
    
    def get_service_by_id(self, service_id: str) -> Optional[Dict]:
        """Get service provider by service_id"""
        with self.get_cursor() as cursor:
            cursor.execute("""
                SELECT id, service_id, service_name, service_type, email,
                       contact_phone, address, latitude, longitude, available_units, is_online
                FROM service_providers
                WHERE service_id = %s
            """, (service_id,))
            return cursor.fetchone()
    
    def update_service_online_status(self, service_id: str, is_online: bool):
        """Update service online status"""
        with self.get_cursor() as cursor:
            cursor.execute("""
                UPDATE service_providers
                SET is_online = %s, updated_at = CURRENT_TIMESTAMP
                WHERE service_id = %s
            """, (is_online, service_id))
    
    def find_nearest_services(
        self, 
        latitude: float, 
        longitude: float, 
        service_type: str,
        max_distance_km: float = 50.0,
        limit: int = 5
    ) -> List[Dict]:
        """Find nearest service providers using PostGIS function"""
        with self.get_cursor() as cursor:
            cursor.execute("""
                SELECT * FROM find_nearest_services(%s, %s, %s, %s, %s)
            """, (latitude, longitude, service_type, max_distance_km, limit))
            return cursor.fetchall()
    
    # ==========================================
    # Emergency Request Operations
    # ==========================================
    
    def create_emergency_request(self, data: Dict) -> Dict:
        """Create new emergency request"""
        with self.get_cursor() as cursor:
            cursor.execute("""
                INSERT INTO emergency_requests (
                    request_id, request_type, user_phone, user_note,
                    latitude, longitude, location, address, status
                )
                VALUES (
                    %(request_id)s, %(request_type)s, %(user_phone)s, %(user_note)s,
                    %(latitude)s, %(longitude)s, 
                    ST_SetSRID(ST_MakePoint(%(longitude)s, %(latitude)s), 4326),
                    %(address)s, 'pending'
                )
                RETURNING id, request_id, request_type, user_phone, user_note,
                          latitude, longitude, address, status, created_at
            """, data)
            return cursor.fetchone()
    
    def get_request_by_id(self, request_id: str) -> Optional[Dict]:
        """Get emergency request by ID"""
        with self.get_cursor() as cursor:
            cursor.execute("""
                SELECT 
                    er.id, er.request_id, er.request_type, er.user_phone, er.user_note,
                    er.latitude, er.longitude, er.address, er.status,
                    er.estimated_arrival_time, er.distance_km, er.created_at, er.updated_at,
                    sp.service_name as assigned_service_name,
                    sp.contact_phone as assigned_service_phone,
                    sp.service_id as assigned_service_id
                FROM emergency_requests er
                LEFT JOIN service_providers sp ON er.assigned_service_id = sp.id
                WHERE er.request_id = %s
            """, (request_id,))
            return cursor.fetchone()
    
    def get_pending_requests(self, service_type: Optional[str] = None) -> List[Dict]:
        """Get all pending emergency requests"""
        with self.get_cursor() as cursor:
            if service_type:
                # Map service type to request type
                type_map = {
                    'hospital': 'ambulance',
                    'fire_station': 'fire',
                    'police_station': 'police'
                }
                request_type = type_map.get(service_type)
                
                cursor.execute("""
                    SELECT 
                        request_id, request_type, user_phone, user_note,
                        latitude, longitude, address, status, created_at
                    FROM emergency_requests
                    WHERE status = 'pending' AND request_type = %s
                    ORDER BY created_at DESC
                """, (request_type,))
            else:
                cursor.execute("""
                    SELECT 
                        request_id, request_type, user_phone, user_note,
                        latitude, longitude, address, status, created_at
                    FROM emergency_requests
                    WHERE status = 'pending'
                    ORDER BY created_at DESC
                """)
            return cursor.fetchall()
    
    def update_request_status(
        self, 
        request_id: str, 
        status: str,
        assigned_service_id: Optional[str] = None,  # Changed to accept service_id (string)
        estimated_arrival_time: Optional[int] = None,
        distance_km: Optional[float] = None
    ):
        """Update emergency request status"""
        with self.get_cursor() as cursor:
            # If assigned_service_id is provided, look up the integer ID
            service_internal_id = None
            if assigned_service_id:
                cursor.execute("""
                    SELECT id FROM service_providers WHERE service_id = %s
                """, (assigned_service_id,))
                result = cursor.fetchone()
                if result:
                    service_internal_id = result['id']
            
            cursor.execute("""
                UPDATE emergency_requests
                SET status = %s,
                    assigned_service_id = COALESCE(%s, assigned_service_id),
                    estimated_arrival_time = COALESCE(%s, estimated_arrival_time),
                    distance_km = COALESCE(%s, distance_km),
                    updated_at = CURRENT_TIMESTAMP
                WHERE request_id = %s
                RETURNING id, request_id, status, assigned_service_id
            """, (status, service_internal_id, estimated_arrival_time, distance_km, request_id))
            return cursor.fetchone()
    
    # ==========================================
    # Service Response Operations
    # ==========================================
    
    def record_service_response(self, data: Dict):
        """Record service provider response to request"""
        with self.get_cursor() as cursor:
            # Set defaults for optional fields
            data.setdefault('distance_km', None)
            data.setdefault('estimated_time_minutes', None)
            data.setdefault('notes', None)
            
            cursor.execute("""
                INSERT INTO service_responses (
                    request_id, service_id, response_type, distance_km,
                    estimated_time_minutes, notes
                )
                VALUES (
                    (SELECT id FROM emergency_requests WHERE request_id = %(request_id)s),
                    (SELECT id FROM service_providers WHERE service_id = %(service_id)s),
                    %(response_type)s, %(distance_km)s, %(estimated_time_minutes)s, %(notes)s
                )
                ON CONFLICT (request_id, service_id) DO UPDATE
                SET response_type = EXCLUDED.response_type,
                    estimated_time_minutes = EXCLUDED.estimated_time_minutes,
                    responded_at = CURRENT_TIMESTAMP
            """, data)
    
    def get_accepting_services(self, request_id: str) -> List[Dict]:
        """Get all services that accepted a request"""
        with self.get_cursor() as cursor:
            cursor.execute("""
                SELECT 
                    sp.service_id, sp.service_name, sp.latitude, sp.longitude,
                    sr.distance_km, sr.estimated_time_minutes
                FROM service_responses sr
                JOIN service_providers sp ON sr.service_id = sp.id
                WHERE sr.request_id = (SELECT id FROM emergency_requests WHERE request_id = %s)
                    AND sr.response_type = 'accepted'
                ORDER BY sr.distance_km ASC
            """, (request_id,))
            return cursor.fetchall()
    
    # ==========================================
    # Distance and Routing
    # ==========================================
    
    def calculate_distance(
        self, 
        lat1: float, lon1: float, 
        lat2: float, lon2: float
    ) -> float:
        """Calculate distance between two points"""
        with self.get_cursor() as cursor:
            cursor.execute("""
                SELECT calculate_distance(%s, %s, %s, %s) as distance_km
            """, (lat1, lon1, lat2, lon2))
            result = cursor.fetchone()
            return float(result['distance_km']) if result else 0.0
    
    def close(self):
        """Close all connections in pool"""
        if self.pool:
            self.pool.closeall()
            logger.info("PostgreSQL connection pool closed")
    
    # ==========================================
    # FIFO Logic Functions
    # ==========================================
    
    def count_refusals(self, request_id: str) -> int:
        """Count how many services refused a request"""
        with self.get_cursor() as cursor:
            cursor.execute("""
                SELECT COUNT(*) as count
                FROM service_responses
                WHERE request_id = (SELECT id FROM emergency_requests WHERE request_id = %s)
                    AND response_type = 'rejected'
            """, (request_id,))
            result = cursor.fetchone()
            return result['count'] if result else 0
    
    def count_available_services(self, request_type: str) -> int:
        """Count available services for a request type"""
        # Map request type to service type
        type_map = {
            'ambulance': 'hospital',
            'fire': 'fire_station',
            'police': 'police_station'
        }
        service_type = type_map.get(request_type, request_type)
        
        with self.get_cursor() as cursor:
            cursor.execute("""
                SELECT COUNT(*) as count
                FROM service_providers
                WHERE service_type = %s 
                    AND is_online = true 
                    AND available_units > 0
            """, (service_type,))
            result = cursor.fetchone()
            return result['count'] if result else 0
    
    def get_recent_accepts(self, request_id: str, seconds: int = 2) -> list:
        """Get all accepts for a request in the last N seconds"""
        with self.get_cursor() as cursor:
            cursor.execute("""
                SELECT sr.service_id, sr.responded_at, sr.distance_km, sr.estimated_time_minutes,
                       sp.service_id as svc_id
                FROM service_responses sr
                JOIN service_providers sp ON sr.service_id = sp.id
                WHERE sr.request_id = (SELECT id FROM emergency_requests WHERE request_id = %s)
                    AND sr.response_type = 'accepted'
                    AND sr.responded_at >= NOW() - make_interval(secs => %s)
                ORDER BY sr.responded_at ASC
            """, (request_id, seconds))
            
            results = cursor.fetchall()
            # Fix the service_id field to use the correct one
            for r in results:
                r['service_id'] = r['svc_id']
            return results
    
    def mark_response_canceled(self, request_id: str, service_id: str):
        """Mark a service response as canceled"""
        with self.get_cursor() as cursor:
            cursor.execute("""
                UPDATE service_responses
                SET response_type = 'canceled',
                    responded_at = CURRENT_TIMESTAMP
                WHERE request_id = (SELECT id FROM emergency_requests WHERE request_id = %s)
                    AND service_id = (SELECT id FROM service_providers WHERE service_id = %s)
            """, (request_id, service_id))

    def mark_response_as_reserve(self, request_id: str, service_id: str):
        """Mark a service response as reserve/standby"""
        with self.get_cursor() as cursor:
            cursor.execute("""
                UPDATE service_responses
                SET response_type = 'reserve',
                    notes = 'On standby - another service was closer',
                    responded_at = CURRENT_TIMESTAMP
                WHERE request_id = (SELECT id FROM emergency_requests WHERE request_id = %s)
                    AND service_id = (SELECT id FROM service_providers WHERE service_id = %s)
            """, (request_id, service_id))

    def mark_services_as_reserve(self, request_id: str, service_ids: list):
        """Mark multiple services as reserve/standby for a request"""
        if not service_ids:
            return

        with self.get_cursor() as cursor:
            # Update each service response to reserve status
            for service_id in service_ids:
                cursor.execute("""
                    UPDATE service_responses
                    SET response_type = 'reserve',
                        notes = 'On standby - another service was closer',
                        responded_at = CURRENT_TIMESTAMP
                    WHERE request_id = (SELECT id FROM emergency_requests WHERE request_id = %s)
                        AND service_id = (SELECT id FROM service_providers WHERE service_id = %s)
                """, (request_id, service_id))

    def get_reserve_services(self, request_id: str):
        """Get all services on reserve for a request"""
        with self.get_cursor() as cursor:
            cursor.execute("""
                SELECT
                    sp.service_id,
                    sp.service_name,
                    sp.contact_phone,
                    sr.distance_km,
                    sr.estimated_time_minutes
                FROM service_responses sr
                JOIN service_providers sp ON sr.service_id = sp.id
                WHERE sr.request_id = (SELECT id FROM emergency_requests WHERE request_id = %s)
                    AND sr.response_type = 'reserve'
                ORDER BY sr.distance_km ASC
            """, (request_id,))
            return cursor.fetchall()


# Create global database instance
db = PostGISDatabase()


# ============================================================================
# NEW FUNCTIONS FOR FIFO LOGIC - Added Nov 2024
# ============================================================================

def get_request_responses(request_id: str):
    """Get all responses for a request"""
    with db.get_cursor() as cursor:
        cursor.execute("""
            SELECT * FROM request_responses 
            WHERE request_id = %s
            ORDER BY created_at ASC
        """, (request_id,))
        
        return cursor.fetchall()


def store_request_response(request_id, service_id, action, distance_km=None, eta_minutes=None):
    """Store service response to request"""
    with db.get_cursor() as cursor:
        cursor.execute("""
            INSERT INTO request_responses 
            (request_id, service_id, action, distance_km, eta_minutes)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (request_id, service_id) 
            DO UPDATE SET action = EXCLUDED.action, updated_at = CURRENT_TIMESTAMP
        """, (request_id, service_id, action, distance_km, eta_minutes))


def update_response_status(request_id, service_id, new_action):
    """Update response action"""
    with db.get_cursor() as cursor:
        cursor.execute("""
            UPDATE request_responses 
            SET action = %s, updated_at = CURRENT_TIMESTAMP
            WHERE request_id = %s AND service_id = %s
        """, (new_action, request_id, service_id))


def validate_request(request_id: str, service_id: str, estimated_arrival_time: int, distance_km: float):
    """Mark request as validated (accepted by a service)"""
    with db.get_cursor() as cursor:
        cursor.execute("""
            UPDATE emergency_requests
            SET status = 'validated',
                assigned_service_id = (SELECT id FROM service_providers WHERE service_id = %s),
                estimated_arrival_time = %s,
                distance_km = %s,
                updated_at = CURRENT_TIMESTAMP
            WHERE request_id = %s
        """, (service_id, estimated_arrival_time, distance_km, request_id))


def cancel_request(request_id: str):
    """Mark request as canceled"""
    with db.get_cursor() as cursor:
        cursor.execute("""
            UPDATE emergency_requests
            SET status = 'canceled',
                updated_at = CURRENT_TIMESTAMP
            WHERE request_id = %s
        """, (request_id,))


def get_available_services(service_type: str):
    """Get all available services of a specific type"""
    with db.get_cursor() as cursor:
        cursor.execute("""
            SELECT service_id, service_name, service_type, 
                   latitude, longitude, contact_phone, available_units
            FROM service_providers
            WHERE service_type = %s 
                AND is_online = true 
                AND available_units > 0
            ORDER BY service_name
        """, (service_type,))
        
        return cursor.fetchall()


def count_refusals(request_id: str) -> int:
    """Count how many services refused a request"""
    with db.get_cursor() as cursor:
        cursor.execute("""
            SELECT COUNT(*) as count
            FROM service_responses
            WHERE request_id = (SELECT id FROM emergency_requests WHERE request_id = %s)
                AND response_type = 'rejected'
        """, (request_id,))
        result = cursor.fetchone()
        return result['count'] if result else 0


def count_available_services(request_type: str) -> int:
    """Count available services for a request type"""
    # Map request type to service type
    type_map = {
        'ambulance': 'hospital',
        'fire': 'fire_station',
        'police': 'police_station'
    }
    service_type = type_map.get(request_type, request_type)
    
    with db.get_cursor() as cursor:
        cursor.execute("""
            SELECT COUNT(*) as count
            FROM service_providers
            WHERE service_type = %s 
                AND is_online = true 
                AND available_units > 0
        """, (service_type,))
        result = cursor.fetchone()
        return result['count'] if result else 0


def get_recent_accepts(request_id: str, seconds: int = 2) -> list:
    """Get all accepts for a request in the last N seconds"""
    with db.get_cursor() as cursor:
        cursor.execute("""
            SELECT sr.service_id, sr.responded_at, sr.distance_km, sr.estimated_time_minutes,
                   sp.service_id as svc_id
            FROM service_responses sr
            JOIN service_providers sp ON sr.service_id = sp.id
            WHERE sr.request_id = (SELECT id FROM emergency_requests WHERE request_id = %s)
                AND sr.response_type = 'accepted'
                AND sr.responded_at >= NOW() - INTERVAL '%s seconds'
            ORDER BY sr.responded_at ASC
        """, (request_id, seconds))
        
        results = cursor.fetchall()
        # Fix the service_id field to use the correct one
        for r in results:
            r['service_id'] = r['svc_id']
        return results


def mark_response_canceled(request_id: str, service_id: str):
    """Mark a service response as canceled"""
    with db.get_cursor() as cursor:
        cursor.execute("""
            UPDATE service_responses
            SET response_type = 'canceled',
                responded_at = CURRENT_TIMESTAMP
            WHERE request_id = (SELECT id FROM emergency_requests WHERE request_id = %s)
                AND service_id = (SELECT id FROM service_providers WHERE service_id = %s)
        """, (request_id, service_id))