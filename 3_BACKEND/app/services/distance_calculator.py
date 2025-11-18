"""
Emergency Response System - Distance Calculator Service
Calculates distances and estimates travel times
"""

from typing import Tuple
from app.database.postgis import db


def calculate_straight_line_distance(
    lat1: float, 
    lon1: float, 
    lat2: float, 
    lon2: float
) -> float:
    """
    Calculate straight-line distance between two points using PostGIS
    
    Args:
        lat1: Latitude of first point
        lon1: Longitude of first point
        lat2: Latitude of second point
        lon2: Longitude of second point
    
    Returns:
        Distance in kilometers
    """
    return db.calculate_distance(lat1, lon1, lat2, lon2)


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


def calculate_distance_and_eta(
    start_lat: float,
    start_lon: float,
    end_lat: float,
    end_lon: float
) -> Tuple[float, int]:
    """
    Calculate both distance and estimated time
    
    Returns:
        Tuple of (distance_km, eta_minutes)
    """
    distance = calculate_straight_line_distance(start_lat, start_lon, end_lat, end_lon)
    eta = estimate_travel_time(distance)
    return distance, eta
