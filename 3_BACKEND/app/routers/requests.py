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
from app.mqtt.mqtt_manager import mqtt_manager
from app.services.distance_calculator import calculate_distance_and_eta
from app.auth.jwt_handler import verify_token
import asyncio


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/requests", tags=["Emergency Requests"])
# Global locks to prevent multiple responders from accepting the same request
request_locks = {}
request_locks_lock = asyncio.Lock()



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
        
        # Broadcast to relevant services via WebSocket (for web clients)
        await manager.broadcast_to_services(
            service_type=target_service_type,
            event='new_emergency_request',
            data=notification_data
        )

        # Publish to MQTT (for service providers using MQTT)
        await mqtt_manager.publish_new_request(
            service_type=data.request_type,  # ambulance, fire, police
            request_data=notification_data
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
    Service provider responds to an emergency request
    FIFO logic + 2-second simultaneous accept window + nearest-service winner
    """

    # ------------------------------------------------------
    # 1. Authenticate service (from your existing function)
    # ------------------------------------------------------
    service = get_service_from_token(authorization)

    # ------------------------------------------------------
    # 2. Create lock for this request
    # ------------------------------------------------------
    async with request_locks_lock:
        if response.request_id not in request_locks:
            request_locks[response.request_id] = asyncio.Lock()

    # ------------------------------------------------------
    # 3. FIFO: process ONE service at a time per request
    # ------------------------------------------------------
    async with request_locks[response.request_id]:

        # --------------------------------------------------
        # Fetch request
        # --------------------------------------------------
        req = db.get_request_by_id(response.request_id)
        if not req:
            raise HTTPException(
                status_code=404,
                detail="Request not found"
            )

        # If already assigned or canceled → notify service
        if req["status"] in ["accepted", "canceled"]:
            await manager.notify_service(
                service_id=service["service_id"],
                event="request_unavailable",
                data={
                    "request_id": response.request_id,
                    "reason": f"Request already {req['status']}",
                    "assigned_to": req.get("assigned_service_id")
                }
            )
            return {
                "success": False,
                "message": f"Request already {req['status']}",
                "status": req["status"]
            }

        # --------------------------------------------------
        # Handle REFUSE
        # --------------------------------------------------
        if response.response_type == "rejected":
            db.record_service_response({
                "request_id": response.request_id,
                "service_id": service["service_id"],
                "response_type": "rejected"
            })

            # Check if all refused
            if db.count_refusals(response.request_id) == db.count_available_services(req["request_type"]):
                db.update_request_status(response.request_id, "canceled")

                # Notify user
                await manager.notify_user(
                    user_id=f"USER-{response.request_id}",
                    event="request_canceled",
                    data={"reason": "All services refused your request"}
                )

            return {
                "success": True,
                "response_type": "rejected"
            }

        # --------------------------------------------------
        # ACCEPT LOGIC
        # --------------------------------------------------

        # Calculate distance
        distance_km, eta_minutes = await calculate_distance_and_eta(
            service["latitude"],
            service["longitude"],
            float(req["latitude"]),
            float(req["longitude"])
        )

        # Save this accept
        db.record_service_response({
            "request_id": response.request_id,
            "service_id": service["service_id"],
            "response_type": "accepted",
            "distance_km": distance_km,
            "estimated_time_minutes": eta_minutes
        })

        # Fetch accepts in last 2 seconds
        recent = db.get_recent_accepts(response.request_id, seconds=2)

        # ----------------------------------------------------------
        # Case 1: only this service accepted → assign immediately
        # ----------------------------------------------------------
        if len(recent) == 1:
            db.update_request_status(
                request_id=response.request_id,
                status="accepted",
                assigned_service_id=service["service_id"],
                estimated_arrival_time=eta_minutes,
                distance_km=distance_km
            )

            await manager.notify_service(
                service_id=service["service_id"],
                event="request_assigned_to_you",
                data={
                    "request_id": response.request_id,
                    "distance_km": distance_km,
                    "estimated_arrival_time": eta_minutes
                }
            )

            await manager.notify_user(
                user_id=f"USER-{response.request_id}",
                event="request_assigned",
                data={
                    "request_id": response.request_id,
                    "service_name": service["service_name"],
                    "service_phone": service["contact_phone"],
                    "service_type": service["service_type"],
                    "estimated_arrival_time": eta_minutes,
                    "distance_km": distance_km,
                    "service_location": {
                        "latitude": float(service["latitude"]),
                        "longitude": float(service["longitude"])
                    }
                }
            )

            return {
                "success": True,
                "response_type": "accepted",
                "assigned_to": service["service_id"],
                "eta_minutes": eta_minutes
            }

        # ----------------------------------------------------------
        # Case 2: multiple accepts in window → choose nearest
        # ----------------------------------------------------------
        logger.info(f"Multiple services ({len(recent)}) accepted request {response.request_id} - calculating distances")

        # Calculate distances for ALL responding services using real road routing
        distances = {}
        service_details = {}
        eta_times = {}

        for r in recent:
            svc = db.get_service_by_id(r["service_id"])
            service_details[r["service_id"]] = svc

            # Use real road routing (OSRM) for accurate distance
            d, eta = await calculate_distance_and_eta(
                svc["latitude"], svc["longitude"],
                float(req["latitude"]), float(req["longitude"])
            )
            distances[r["service_id"]] = d
            eta_times[r["service_id"]] = eta

            logger.info(f"  - {svc['service_name']}: {d:.2f}km, ETA: {eta}min")

        # Find nearest service
        nearest_service_id = min(distances, key=distances.get)
        nearest_service = service_details[nearest_service_id]
        nearest_dist = distances[nearest_service_id]
        nearest_eta = eta_times[nearest_service_id]

        logger.info(f"Nearest service: {nearest_service['service_name']} ({nearest_dist:.2f}km)")

        # ----------------------------------------------------------
        # Update request status with nearest service
        # ----------------------------------------------------------
        db.update_request_status(
            request_id=response.request_id,
            status="accepted",
            assigned_service_id=nearest_service_id,
            estimated_arrival_time=nearest_eta,
            distance_km=nearest_dist
        )

        # Mark reserve services in database
        reserve_service_ids = [sid for sid in distances.keys() if sid != nearest_service_id]
        if reserve_service_ids:
            db.mark_services_as_reserve(response.request_id, reserve_service_ids)

        # ----------------------------------------------------------
        # Notify assigned service (WebSocket + MQTT)
        # ----------------------------------------------------------
        assigned_data = {
            "request_id": response.request_id,
            "distance_km": nearest_dist,
            "estimated_arrival_time": nearest_eta,
            "message": "You have been assigned to this emergency request"
        }

        await manager.notify_service(
            service_id=nearest_service_id,
            event="request_assigned_to_you",
            data=assigned_data
        )

        await mqtt_manager.publish_request_assigned(
            request_id=response.request_id,
            assignment_data={
                "assigned_service_id": nearest_service_id,
                "assigned_service_name": nearest_service["service_name"],
                **assigned_data
            }
        )

        # ----------------------------------------------------------
        # Notify user (WebSocket only)
        # ----------------------------------------------------------
        await manager.notify_user(
            user_id=f"USER-{response.request_id}",
            event="request_assigned",
            data={
                "request_id": response.request_id,
                "service_name": nearest_service["service_name"],
                "service_phone": nearest_service["contact_phone"],
                "service_type": nearest_service["service_type"],
                "estimated_arrival_time": nearest_eta,
                "distance_km": nearest_dist,
                "service_location": {
                    "latitude": float(nearest_service["latitude"]),
                    "longitude": float(nearest_service["longitude"])
                }
            }
        )

        # ----------------------------------------------------------
        # Notify RESERVE services (WebSocket + MQTT)
        # Active standby - they stay notified until request completes
        # ----------------------------------------------------------
        for sid in reserve_service_ids:
            reserve_service = service_details[sid]
            reserve_dist = distances[sid]

            # Mark as canceled in response table but keep as reserve
            db.mark_response_as_reserve(response.request_id, sid)

            # Send reserve notification via WebSocket
            reserve_notification = {
                "request_id": response.request_id,
                "status": "reserve",
                "assigned_to_service": nearest_service["service_name"],
                "your_distance_km": reserve_dist,
                "assigned_distance_km": nearest_dist,
                "message": f"Request handled by {nearest_service['service_name']} - You're on reserve/standby",
                "reserve_position": list(reserve_service_ids).index(sid) + 1,
                "total_reserves": len(reserve_service_ids)
            }

            await manager.notify_service(
                service_id=sid,
                event="request_reserve_standby",
                data=reserve_notification
            )

            logger.info(f"Reserve: {reserve_service['service_name']} (#{reserve_notification['reserve_position']}, {reserve_dist:.2f}km)")

        # Send reserve notification via MQTT for all reserves
        if reserve_service_ids:
            await mqtt_manager.publish_reserve_notification(
                request_id=response.request_id,
                reserve_data={
                    "reserve_service_ids": reserve_service_ids,
                    "assigned_service_id": nearest_service_id,
                    "assigned_service_name": nearest_service["service_name"],
                    "distances": {sid: distances[sid] for sid in reserve_service_ids},
                    "message": f"Request assigned to {nearest_service['service_name']} - You are on reserve"
                }
            )

        # ----------------------------------------------------------
        # Return response based on whether current service was selected
        # ----------------------------------------------------------
        if service["service_id"] == nearest_service_id:
            return {
                "success": True,
                "response_type": "accepted",
                "assigned_to": nearest_service_id,
                "distance_km": nearest_dist,
                "eta_minutes": nearest_eta,
                "message": "You have been assigned to this request"
            }
        else:
            return {
                "success": True,
                "response_type": "reserve",
                "assigned_to": nearest_service_id,
                "your_distance_km": distances[service["service_id"]],
                "assigned_distance_km": nearest_dist,
                "message": f"Request assigned to {nearest_service['service_name']} - You are on reserve",
                "reserve_position": reserve_service_ids.index(service["service_id"]) + 1
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

