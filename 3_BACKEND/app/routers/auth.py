"""
Emergency Response System - Authentication Router
Handles service provider registration and login
"""

from fastapi import APIRouter, HTTPException, status
from datetime import timedelta
import secrets
import logging

from app.models import (
    ServiceRegisterRequest,
    ServiceLoginRequest,
    TokenResponse
)
from app.auth.password import hash_password, verify_password
from app.auth.jwt_handler import create_access_token
from app.database.postgis import db
from app.database.mongodb import mongodb
from app.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register_service(data: ServiceRegisterRequest):
    """
    Register a new service provider
    
    - **service_name**: Name of the service
    - **service_type**: Type (hospital, fire_station, police_station)
    - **email**: Email address for login
    - **password**: Password (min 8 characters)
    - **latitude**: Service location latitude
    - **longitude**: Service location longitude
    """
    try:
        # Check if email already exists
        existing_service = db.get_service_by_email(data.email)
        if existing_service:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # Generate unique service ID
        service_id_prefix = {
            'hospital': 'HOSP',
            'fire_station': 'FIRE',
            'police_station': 'POL'
        }
        prefix = service_id_prefix.get(data.service_type, 'SERV')
        service_id = f"{prefix}-{secrets.token_hex(4).upper()}"
        
        # Hash password
        password_hash = hash_password(data.password)
        
        # Create service provider
        service_data = {
            'service_id': service_id,
            'service_name': data.service_name,
            'service_type': data.service_type,
            'email': data.email,
            'password_hash': password_hash,
            'contact_phone': data.contact_phone,
            'address': data.address,
            'latitude': data.latitude,
            'longitude': data.longitude,
            'available_units': data.available_units
        }
        
        result = db.create_service_provider(service_data)
        
        # Log to MongoDB
        mongodb.log_service_action(
            service_id=service_id,
            action="registered",
            details={'service_name': data.service_name, 'service_type': data.service_type}
        )
        
        # Create JWT token
        token_data = {
            'service_id': service_id,
            'email': data.email,
            'service_type': data.service_type
        }
        access_token = create_access_token(token_data)
        
        logger.info(f"Service registered successfully: {service_id}")
        
        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            service_id=service_id,
            service_name=data.service_name,
            service_type=data.service_type
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error registering service: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to register service: {str(e)}"
        )


@router.post("/login", response_model=TokenResponse)
async def login_service(data: ServiceLoginRequest):
    """
    Service provider login
    
    - **email**: Registered email address
    - **password**: Account password
    """
    try:
        # Get service by email
        service = db.get_service_by_email(data.email)
        
        if not service:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        # Verify password
        if not verify_password(data.password, service['password_hash']):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        # Log login
        mongodb.log_service_login(
            service_id=service['service_id'],
            service_name=service['service_name']
        )
        
        # Create JWT token
        token_data = {
            'service_id': service['service_id'],
            'email': service['email'],
            'service_type': service['service_type']
        }
        access_token = create_access_token(token_data)
        
        logger.info(f"Service logged in: {service['service_id']}")
        
        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            service_id=service['service_id'],
            service_name=service['service_name'],
            service_type=service['service_type']
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error during login: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed"
        )


@router.get("/verify")
async def verify_token_endpoint(token: str):
    """
    Verify JWT token validity
    
    - **token**: JWT token to verify
    """
    from app.auth.jwt_handler import verify_token
    
    try:
        payload = verify_token(token)
        return {
            'valid': True,
            'service_id': payload.get('service_id'),
            'service_type': payload.get('service_type')
        }
    except HTTPException:
        return {'valid': False}
