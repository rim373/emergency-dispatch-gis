"""
Emergency Response System - Emergency Requests Router
Handles emergency request creation, updates, and retrieval
"""

from fastapi import APIRouter, HTTPException, status, Depends, Header
from typing import List, Optional
import secrets
import logging
from datetime import datetime

from app.models import (
    EmergencyRequestCreate,
    EmergencyRequestResponse,
    ServiceResponseAction
)
from app.database.postgis import db
from app.database.mongodb import mongodb
from app.websocket.manager import manager
from app.services.distance_calculator import calculate_distance_and_eta
from app.auth.jwt_handler import verify_token

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/requests", tags=["Emergency Requests"])


# ==========================================
# Helper Functions
# ==========================================

def get_service_from_token(authorization: Optional[str] = Header(None)) -> dict:
    """Extract service info from JWT token"""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid authorization header"
        )
    
    token = authorization.split(" ")[1]
    payload = verify_token(token)
    
    service = db.get_service_by_id(payload['service_id'])
    if not service:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Service not found"
        )
    
    return service


# ==========================================
# Endpoints
# ==========================================

@router.post("/create", response_model=EmergencyRequestResponse, status_code=status.HTTP_201_CREATED)
async def create_emergency_request(data: EmergencyRequestCreate):
    """
    Create a new emergency request (NO LOGIN REQUIRED)
    
    - **request_type**: ambulance, fire, or police
    - **location**: User's current location
    - **user_phone**: Optional contact phone
    - **user_note**: Optional description of emergency
    """
    try:
        # Generate unique request ID
        request_id = f"REQ-{secrets.token_hex(6).upper()}"
        
        # Prepare request data
        request_data = {
            'request_id': request_id,
            'request_type': data.request_type,
            'user_phone': data.user_phone,
            'user_note': data.user_note,
            'latitude': data.location.latitude,
            'longitude': data.location.longitude,
            'address': data.location.address
        }
        
        # Create request in database
        result = db.create_emergency_request(request_data)
        
        # Log to MongoDB
        mongodb.log_request_created(request_data)
        
        # Determine which service type to notify
        service_type_mapping = {
            'ambulance': 'hospital',
            'fire': 'fire_station',
            'police': 'police_station'
        }
        target_service_type = service_type_mapping[data.request_type]
        
        # Prepare WebSocket notification
        notification_data = {
            'request_id': request_id,
            'request_type': data.request_type,
            'location': {
                'latitude': data.location.latitude,
                'longitude': data.location.longitude,
                'address': data.location.address
            },
            'user_phone': data.user_phone,
            'user_note': data.user_note,
            'created_at': result['created_at'].isoformat(),
            'status': 'pending'
        }
        
        # Broadcast to relevant services
        await manager.broadcast_to_services(
            service_type=target_service_type,
            event='new_emergency_request',
            data=notification_data
        )
        
        logger.info(f"Emergency request created: {request_id} (type: {data.request_type})")
        
        return EmergencyRequestResponse(
            request_id=request_id,
            request_type=data.request_type,
            location=data.location,
            user_phone=data.user_phone,
            user_note=data.user_note,
            status='pending',
            created_at=result['created_at']
        )
    
    except Exception as e:
        logger.error(f"Error creating emergency request: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create emergency request: {str(e)}"
        )


@router.get("/{request_id}", response_model=EmergencyRequestResponse)
async def get_request_status(request_id: str):
    """
    Get status of an emergency request
    
    - **request_id**: The request ID to check
    """
    request = db.get_request_by_id(request_id)
    
    if not request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Request not found"
        )
    
    return EmergencyRequestResponse(
        request_id=request['request_id'],
        request_type=request['request_type'],
        location={
            'latitude': float(request['latitude']),
            'longitude': float(request['longitude']),
            'address': request['address']
        },
        user_phone=request['user_phone'],
        user_note=request['user_note'],
        status=request['status'],
        assigned_service_name=request.get('assigned_service_name'),
        assigned_service_phone=request.get('assigned_service_phone'),
        estimated_arrival_time=request.get('estimated_arrival_time'),
        distance_km=float(request['distance_km']) if request.get('distance_km') else None,
        created_at=request['created_at']
    )


@router.post("/respond")
async def respond_to_request(
    response: ServiceResponseAction,
    authorization: str = Header(None)
):
    """
    Service provider responds to an emergency request (LOGIN REQUIRED)
    
    - **request_id**: The request to respond to
    - **response_type**: accepted or rejected
    - **estimated_time_minutes**: ETA if accepting
    - **notes**: Optional notes
    """
    # Authenticate service
    service = get_service_from_token(authorization)
    
    # Get request
    request = db.get_request_by_id(response.request_id)
    if not request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Request not found"
        )
    
    # Check if request is still pending
    if request['status'] != 'pending':
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Request is already {request['status']}"
        )
    
    # Calculate distance
    distance_km, eta_minutes = calculate_distance_and_eta(
        service['latitude'],
        service['longitude'],
        float(request['latitude']),
        float(request['longitude'])
    )
    
    # Use provided ETA if given, otherwise use calculated
    if response.estimated_time_minutes:
        eta_minutes = response.estimated_time_minutes
    
    # Record response
    response_data = {
        'request_id': response.request_id,
        'service_id': service['service_id'],
        'response_type': response.response_type,
        'distance_km': distance_km,
        'estimated_time_minutes': eta_minutes,
        'notes': response.notes
    }
    db.record_service_response(response_data)
    
    # Log to MongoDB
    mongodb.log_service_response(
        service_id=service['service_id'],
        request_id=response.request_id,
        response_type=response.response_type
    )
    
    if response.response_type == 'accepted':
        # Get all accepting services
        accepting_services = db.get_accepting_services(response.request_id)
        
        if len(accepting_services) == 1:
            # Only this service accepted - assign immediately
            db.update_request_status(
                request_id=response.request_id,
                status='accepted',
                assigned_service_id=service['id'],
                estimated_arrival_time=eta_minutes,
                distance_km=distance_km
            )
            
            # Notify this service
            await manager.notify_service(
                service_id=service['service_id'],
                event='request_assigned_to_you',
                data={
                    'request_id': response.request_id,
                    'message': 'Request assigned to you',
                    'distance_km': distance_km,
                    'estimated_arrival_time': eta_minutes
                }
            )
            
            # Notify user
            await manager.notify_user(
                user_id=f"USER-{response.request_id}",
                event='request_assigned',
                data={
                    'request_id': response.request_id,
                    'service_name': service['service_name'],
                    'service_phone': service['contact_phone'],
                    'estimated_arrival_time': eta_minutes,
                    'distance_km': distance_km
                }
            )
            
            logger.info(f"Request {response.request_id} assigned to {service['service_id']}")
        
        else:
            # Multiple services accepted - find nearest
            nearest_service = min(accepting_services, key=lambda s: s['distance_km'])
            
            # Assign to nearest
            nearest_service_full = db.get_service_by_id(nearest_service['service_id'])
            db.update_request_status(
                request_id=response.request_id,
                status='accepted',
                assigned_service_id=nearest_service_full['id'],
                estimated_arrival_time=nearest_service['estimated_time_minutes'],
                distance_km=nearest_service['distance_km']
            )
            
            # Notify assigned service
            await manager.notify_service(
                service_id=nearest_service['service_id'],
                event='request_assigned_to_you',
                data={
                    'request_id': response.request_id,
                    'message': 'You are the nearest service - request assigned to you',
                    'distance_km': nearest_service['distance_km'],
                    'estimated_arrival_time': nearest_service['estimated_time_minutes']
                }
            )
            
            # Notify other services
            for svc in accepting_services:
                if svc['service_id'] != nearest_service['service_id']:
                    await manager.notify_service(
                        service_id=svc['service_id'],
                        event='request_assigned_to_other',
                        data={
                            'request_id': response.request_id,
                            'message': 'Request assigned to closer service',
                            'assigned_to': nearest_service['service_name']
                        }
                    )
            
            # Notify user
            await manager.notify_user(
                user_id=f"USER-{response.request_id}",
                event='request_assigned',
                data={
                    'request_id': response.request_id,
                    'service_name': nearest_service['service_name'],
                    'estimated_arrival_time': nearest_service['estimated_time_minutes'],
                    'distance_km': nearest_service['distance_km']
                }
            )
            
            logger.info(f"Request {response.request_id} assigned to nearest: {nearest_service['service_id']}")
    
    return {
        'success': True,
        'request_id': response.request_id,
        'response_type': response.response_type,
        'distance_km': distance_km,
        'estimated_arrival_time': eta_minutes
    }


@router.get("/pending/all")
async def get_all_pending_requests():
    """Get all pending emergency requests"""
    requests = db.get_pending_requests()
    return {'requests': requests, 'count': len(requests)}


@router.get("/pending/by-type/{service_type}")
async def get_pending_requests_by_type(service_type: str):
    """
    Get pending requests for specific service type
    
    - **service_type**: hospital, fire_station, or police_station
    """
    requests = db.get_pending_requests(service_type=service_type)
    return {'requests': requests, 'count': len(requests)}
