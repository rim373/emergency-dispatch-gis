"""
Emergency Response System - Pydantic Models
Data validation and serialization schemas
"""

from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional, List
from datetime import datetime
from decimal import Decimal


# ==========================================
# Location Models
# ==========================================
class LocationModel(BaseModel):
    """Location with latitude and longitude"""
    latitude: float = Field(..., ge=-90, le=90, description="Latitude coordinate")
    longitude: float = Field(..., ge=-180, le=180, description="Longitude coordinate")
    address: Optional[str] = Field(None, description="Human-readable address")


# ==========================================
# Authentication Models
# ==========================================
class ServiceRegisterRequest(BaseModel):
    """Service provider registration request"""
    service_name: str = Field(..., min_length=3, max_length=255)
    service_type: str = Field(..., pattern="^(hospital|fire_station|police_station)$")
    email: EmailStr
    password: str = Field(..., min_length=8)
    contact_phone: Optional[str] = None
    address: Optional[str] = None
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    available_units: int = Field(default=1, ge=1)


class ServiceLoginRequest(BaseModel):
    """Service provider login request"""
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    """JWT token response"""
    access_token: str
    token_type: str = "bearer"
    service_id: str
    service_name: str
    service_type: str
    latitude: float
    longitude: float

    class Config:
        json_encoders = {
            Decimal: lambda v: float(v) if v is not None else None
        }


# ==========================================
# Emergency Request Models
# ==========================================
class EmergencyRequestCreate(BaseModel):
    """Create new emergency request"""
    request_type: str = Field(..., pattern="^(ambulance|fire|police)$")
    location: LocationModel
    user_phone: Optional[str] = Field(None, max_length=50)
    user_note: Optional[str] = Field(None, max_length=1000)


class EmergencyRequestResponse(BaseModel):
    """Emergency request response"""
    request_id: str
    request_type: str
    location: LocationModel
    user_phone: Optional[str]
    user_note: Optional[str]
    status: str
    assigned_service_name: Optional[str] = None
    assigned_service_phone: Optional[str] = None
    estimated_arrival_time: Optional[int] = None
    distance_km: Optional[float] = None
    created_at: datetime


class EmergencyRequestUpdate(BaseModel):
    """Update emergency request status"""
    status: str = Field(..., pattern="^(pending|accepted|rejected|in_progress|completed|cancelled)$")
    notes: Optional[str] = None


# ==========================================
# Service Provider Models
# ==========================================
class ServiceProviderResponse(BaseModel):
    """Service provider information"""
    service_id: str
    service_name: str
    service_type: str
    contact_phone: Optional[str]
    address: Optional[str]
    latitude: float
    longitude: float
    available_units: int
    is_online: bool
    distance_km: Optional[float] = None


class ServiceResponseAction(BaseModel):
    """Service response to emergency request"""
    request_id: str
    response_type: str = Field(..., pattern="^(accepted|rejected)$")
    estimated_time_minutes: Optional[int] = Field(None, ge=1, le=120)
    notes: Optional[str] = None


# ==========================================
# WebSocket Models
# ==========================================
class WebSocketMessage(BaseModel):
    """WebSocket message structure"""
    event: str
    data: dict


class ServiceRegistration(BaseModel):
    """Service provider WebSocket registration"""
    service_id: str
    service_type: str


class UserRegistration(BaseModel):
    """User WebSocket registration"""
    user_id: str
    request_id: Optional[str] = None


# ==========================================
# Routing Models
# ==========================================
class RouteRequest(BaseModel):
    """Request to calculate route"""
    start_location: LocationModel
    end_location: LocationModel


class RouteResponse(BaseModel):
    """Route calculation response"""
    distance_km: float
    estimated_time_minutes: int
    route_geometry: Optional[List[List[float]]] = None  # [[lon, lat], ...]


# ==========================================
# Statistics Models
# ==========================================
class SystemStatsResponse(BaseModel):
    """System statistics"""
    total_services: int
    online_services: int
    pending_requests: int
    accepted_requests: int
    completed_requests: int
    services_by_type: dict


class ServiceStatsResponse(BaseModel):
    """Service provider statistics"""
    total_requests_received: int
    total_requests_accepted: int
    total_requests_completed: int
    average_response_time_minutes: Optional[float]


# ==========================================
# Helper Models
# ==========================================
class HealthCheckResponse(BaseModel):
    """API health check response"""
    status: str
    timestamp: datetime
    database_connected: bool
    mongodb_connected: bool


class ErrorResponse(BaseModel):
    """Error response"""
    error: str
    detail: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)
