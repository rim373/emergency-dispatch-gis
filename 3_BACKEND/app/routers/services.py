"""
Emergency Response System - Services Router
Handles service provider information and queries
"""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
import logging

from app.models import ServiceProviderResponse
from app.database.postgis import db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/services", tags=["Services"])


@router.get("/nearest", response_model=List[ServiceProviderResponse])
async def find_nearest_services(
    latitude: float = Query(..., ge=-90, le=90),
    longitude: float = Query(..., ge=-180, le=180),
    service_type: str = Query(..., regex="^(hospital|fire_station|police_station)$"),
    max_distance_km: float = Query(50.0, gt=0, le=200),
    limit: int = Query(5, ge=1, le=20)
):
    """
    Find nearest service providers
    
    - **latitude**: User's latitude
    - **longitude**: User's longitude
    - **service_type**: Type of service needed
    - **max_distance_km**: Maximum search radius (default: 50km)
    - **limit**: Maximum number of results (default: 5)
    """
    try:
        services = db.find_nearest_services(
            latitude=latitude,
            longitude=longitude,
            service_type=service_type,
            max_distance_km=max_distance_km,
            limit=limit
        )
        
        return [
            ServiceProviderResponse(
                service_id=s['service_id'],
                service_name=s['service_name'],
                service_type=s['service_type'],
                contact_phone=s['contact_phone'],
                address=s['address'],
                latitude=float(s['latitude']),
                longitude=float(s['longitude']),
                available_units=s['available_units'],
                is_online=s['is_online'],
                distance_km=float(s['distance_km'])
            )
            for s in services
        ]
    
    except Exception as e:
        logger.error(f"Error finding nearest services: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to find services: {str(e)}"
        )


@router.get("/{service_id}", response_model=ServiceProviderResponse)
async def get_service_details(service_id: str):
    """
    Get details of a specific service provider
    
    - **service_id**: The service ID
    """
    service = db.get_service_by_id(service_id)
    
    if not service:
        raise HTTPException(
            status_code=404,
            detail="Service not found"
        )
    
    return ServiceProviderResponse(
        service_id=service['service_id'],
        service_name=service['service_name'],
        service_type=service['service_type'],
        contact_phone=service['contact_phone'],
        address=service['address'],
        latitude=float(service['latitude']),
        longitude=float(service['longitude']),
        available_units=service['available_units'],
        is_online=service['is_online']
    )


@router.get("/type/{service_type}")
async def get_services_by_type(
    service_type: str,
    online_only: bool = Query(True)
):
    """
    Get all services of a specific type
    
    - **service_type**: hospital, fire_station, or police_station
    - **online_only**: Only return online services (default: true)
    """
    with db.get_cursor() as cursor:
        if online_only:
            cursor.execute("""
                SELECT service_id, service_name, service_type, contact_phone,
                       address, latitude, longitude, available_units, is_online
                FROM service_providers
                WHERE service_type = %s AND is_online = true
                ORDER BY service_name
            """, (service_type,))
        else:
            cursor.execute("""
                SELECT service_id, service_name, service_type, contact_phone,
                       address, latitude, longitude, available_units, is_online
                FROM service_providers
                WHERE service_type = %s
                ORDER BY service_name
            """, (service_type,))
        
        services = cursor.fetchall()
    
    return {
        'service_type': service_type,
        'services': services,
        'count': len(services)
    }


@router.get("/", response_model=List[ServiceProviderResponse])
async def get_all_services(
    online_only: bool = Query(False),
    limit: int = Query(50, ge=1, le=200)
):
    """
    Get all service providers
    
    - **online_only**: Only return online services
    - **limit**: Maximum number of results
    """
    with db.get_cursor() as cursor:
        if online_only:
            cursor.execute("""
                SELECT service_id, service_name, service_type, contact_phone,
                       address, latitude, longitude, available_units, is_online
                FROM service_providers
                WHERE is_online = true
                ORDER BY service_type, service_name
                LIMIT %s
            """, (limit,))
        else:
            cursor.execute("""
                SELECT service_id, service_name, service_type, contact_phone,
                       address, latitude, longitude, available_units, is_online
                FROM service_providers
                ORDER BY service_type, service_name
                LIMIT %s
            """, (limit,))
        
        services = cursor.fetchall()
    
    return [
        ServiceProviderResponse(
            service_id=s['service_id'],
            service_name=s['service_name'],
            service_type=s['service_type'],
            contact_phone=s['contact_phone'],
            address=s['address'],
            latitude=float(s['latitude']),
            longitude=float(s['longitude']),
            available_units=s['available_units'],
            is_online=s['is_online']
        )
        for s in services
    ]
