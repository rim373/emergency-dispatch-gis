"""
Emergency Response System - Routing Service
Handles route calculation using pgRouting
"""

from typing import List, Dict, Optional, Tuple
from app.database.postgis import db
import logging

logger = logging.getLogger(__name__)


def calculate_route(
    start_lat: float,
    start_lon: float,
    end_lat: float,
    end_lon: float
) -> Optional[Dict]:
    """
    Calculate route between two points using pgRouting
    
    Args:
        start_lat: Starting latitude
        start_lon: Starting longitude
        end_lat: Ending latitude
        end_lon: Ending longitude
    
    Returns:
        Dictionary with route information or None if routing fails
    """
    try:
        with db.get_cursor() as cursor:
            # Check if road network exists
            cursor.execute("SELECT COUNT(*) as count FROM road_network")
            result = cursor.fetchone()
            
            if not result or result['count'] == 0:
                logger.warning("Road network not loaded, returning straight-line distance")
                return None
            
            # Find nearest vertices
            cursor.execute("""
                SELECT id, 
                       ST_Distance(
                           the_geom::geography,
                           ST_SetSRID(ST_MakePoint(%s, %s), 4326)::geography
                       ) as distance
                FROM road_network_vertices
                ORDER BY distance
                LIMIT 1
            """, (start_lon, start_lat))
            start_vertex = cursor.fetchone()
            
            cursor.execute("""
                SELECT id,
                       ST_Distance(
                           the_geom::geography,
                           ST_SetSRID(ST_MakePoint(%s, %s), 4326)::geography
                       ) as distance
                FROM road_network_vertices
                ORDER BY distance
                LIMIT 1
            """, (end_lon, end_lat))
            end_vertex = cursor.fetchone()
            
            if not start_vertex or not end_vertex:
                logger.error("Could not find nearest vertices")
                return None
            
            # Calculate route using Dijkstra
            cursor.execute("""
                SELECT 
                    seq,
                    node,
                    edge,
                    cost,
                    agg_cost,
                    ST_AsGeoJSON(rn.geometry) as geometry
                FROM pgr_dijkstra(
                    'SELECT id, source_vertex as source, target_vertex as target, 
                            cost, reverse_cost FROM road_network',
                    %s,
                    %s,
                    directed := true
                ) r
                LEFT JOIN road_network rn ON r.edge = rn.id
                WHERE rn.geometry IS NOT NULL
                ORDER BY seq
            """, (start_vertex['id'], end_vertex['id']))
            
            route_segments = cursor.fetchall()
            
            if not route_segments:
                logger.warning("No route found between vertices")
                return None
            
            # Calculate total distance and time
            total_distance_km = sum(seg['cost'] for seg in route_segments if seg['cost'])
            estimated_time_minutes = int((total_distance_km / 60.0) * 60)  # Assuming 60 km/h
            
            # Extract geometry coordinates
            route_geometry = []
            for segment in route_segments:
                if segment['geometry']:
                    import json
                    geom = json.loads(segment['geometry'])
                    if geom['type'] == 'LineString':
                        route_geometry.extend(geom['coordinates'])
            
            return {
                'distance_km': round(total_distance_km, 2),
                'estimated_time_minutes': max(5, estimated_time_minutes),
                'route_geometry': route_geometry,
                'segments': len(route_segments)
            }
    
    except Exception as e:
        logger.error(f"Error calculating route: {e}")
        return None


def get_route_coordinates(
    start_lat: float,
    start_lon: float,
    end_lat: float,
    end_lon: float
) -> List[List[float]]:
    """
    Get route coordinates as list of [lon, lat] pairs
    
    Returns:
        List of [longitude, latitude] coordinates
    """
    route = calculate_route(start_lat, start_lon, end_lat, end_lon)
    if route and 'route_geometry' in route:
        return route['route_geometry']
    return []
