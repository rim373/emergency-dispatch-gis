"""
Emergency Response System - Distance Calculator Service
Calculates distances and estimates travel times with OSRM fallback
"""

from typing import Tuple
import aiohttp
import math
from app.database.postgis import db
import logging

logger = logging.getLogger(__name__)


def calculate_straight_line_distance(
    lat1: float, 
    lon1: float, 
    lat2: float, 
    lon2: float
) -> float:
    """
    Calculate straight-line distance between two points using Haversine formula
    Fallback method when PostGIS or routing services fail
    
    Args:
        lat1: Latitude of first point
        lon1: Longitude of first point
        lat2: Latitude of second point
        lon2: Longitude of second point
    
    Returns:
        Distance in kilometers
    """
    # Try PostGIS first
    try:
        return db.calculate_distance(lat1, lon1, lat2, lon2)
    except Exception as e:
        logger.warning(f"PostGIS distance calculation failed, using Haversine: {e}")
        
        # Fallback to Haversine formula
        R = 6371.0  # Earth radius in kilometers
        
        lat1_rad = math.radians(lat1)
        lon1_rad = math.radians(lon1)
        lat2_rad = math.radians(lat2)
        lon2_rad = math.radians(lon2)
        
        dlat = lat2_rad - lat1_rad
        dlon = lon2_rad - lon1_rad
        
        a = math.sin(dlat / 2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        
        return R * c


async def calculate_route_osrm(
    start_lat: float,
    start_lon: float,
    end_lat: float,
    end_lon: float
) -> dict:
    """
    Calculate route using OSRM (Open Source Routing Machine) - FREE
    
    Returns:
        {
            'distance_km': float,
            'time_minutes': int,
            'route_found': bool
        }
    """
    try:
        url = f"http://router.project-osrm.org/route/v1/driving/{start_lon},{start_lat};{end_lon},{end_lat}"
        
        params = {
            'overview': 'false',
            'steps': 'false'
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, timeout=10) as response:
                if response.status != 200:
                    return None
                
                data = await response.json()
                
                if data.get('code') == 'Ok' and 'routes' in data:
                    route = data['routes'][0]
                    
                    # Distance in meters, convert to km
                    distance_km = route['distance'] / 1000.0
                    
                    # Duration in seconds, convert to minutes
                    time_minutes = int(route['duration'] / 60)
                    
                    logger.info(f"OSRM routing: {distance_km:.2f} km, {time_minutes} min")
                    
                    return {
                        'distance_km': distance_km,
                        'time_minutes': time_minutes,
                        'route_found': True
                    }
                else:
                    logger.warning("OSRM routing failed")
                    return None
    
    except Exception as e:
        logger.error(f"Error calling OSRM: {e}")
        return None


def estimate_travel_time(distance_km: float, average_speed_kmh: float = 60.0) -> int:
    """
    Estimate travel time based on distance
    
    Args:
        distance_km: Distance in kilometers
        average_speed_kmh: Average speed in km/h (default: 60 km/h for emergency vehicles)
    
    Returns:
        Estimated time in minutes
    """
    if distance_km <= 0:
        return 0
    
    time_hours = distance_km / average_speed_kmh
    time_minutes = int(time_hours * 60)
    
    # Add buffer time for city traffic (20% increase)
    time_minutes = int(time_minutes * 1.2)
    
    # Minimum 5 minutes, maximum 120 minutes
    return max(5, min(120, time_minutes))


async def calculate_distance_and_eta(
    start_lat: float,
    start_lon: float,
    end_lat: float,
    end_lon: float
) -> Tuple[float, int]:
    """
    Calculate both distance and estimated time
    Uses OSRM routing if available, falls back to straight-line distance
    
    Returns:
        Tuple of (distance_km, eta_minutes)
    """
    # Try OSRM routing first (real routes)
    route_info = await calculate_route_osrm(start_lat, start_lon, end_lat, end_lon)
    
    if route_info and route_info['route_found']:
        logger.info(f"Using OSRM route: {route_info['distance_km']:.2f} km")
        return route_info['distance_km'], route_info['time_minutes']
    
    # Fallback to straight-line distance
    logger.info("Using straight-line distance (OSRM unavailable)")
    distance = calculate_straight_line_distance(start_lat, start_lon, end_lat, end_lon)
    eta = estimate_travel_time(distance)
    
    return distance, eta