"""
Emergency Response System - WebSocket Manager
Manages real-time WebSocket connections for users and services
"""

import socketio
from typing import Dict, List, Optional, Set
import logging
from datetime import datetime

from app.database.mongodb import mongodb

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages WebSocket connections and message broadcasting"""
    
    def __init__(self):
        """Initialize connection manager"""
        self.sio = socketio.AsyncServer(
            async_mode='asgi',
            cors_allowed_origins='*',
            logger=False,
            engineio_logger=False
        )
        
        # Store active connections
        self.user_connections: Dict[str, str] = {}  # user_id -> sid
        self.service_connections: Dict[str, str] = {}  # service_id -> sid
        self.service_types: Dict[str, str] = {}  # service_id -> service_type
        
        # Reverse mapping for cleanup
        self.sid_to_user: Dict[str, str] = {}  # sid -> user_id
        self.sid_to_service: Dict[str, str] = {}  # sid -> service_id
        
        self._register_handlers()
    
    def _register_handlers(self):
        """Register Socket.IO event handlers"""
        
        @self.sio.event
        async def connect(sid, environ):
            """Handle client connection"""
            logger.info(f"Client connected: {sid}")
            mongodb.log_websocket_event(
                event_type="connect",
                user_type="unknown",
                user_id=sid
            )
        
        @self.sio.event
        async def disconnect(sid):
            """Handle client disconnection"""
            logger.info(f"Client disconnected: {sid}")
            
            # Clean up user connection
            if sid in self.sid_to_user:
                user_id = self.sid_to_user[sid]
                del self.user_connections[user_id]
                del self.sid_to_user[sid]
                logger.info(f"User {user_id} disconnected")
            
            # Clean up service connection
            if sid in self.sid_to_service:
                service_id = self.sid_to_service[sid]
                if service_id in self.service_connections:
                    del self.service_connections[service_id]
                if service_id in self.service_types:
                    del self.service_types[service_id]
                del self.sid_to_service[sid]
                logger.info(f"Service {service_id} disconnected")
                
                mongodb.log_websocket_event(
                    event_type="disconnect",
                    user_type="service",
                    user_id=service_id
                )
        
        @self.sio.event
        async def register_user(sid, data):
            """Register user connection"""
            user_id = data.get('user_id')
            if user_id:
                self.user_connections[user_id] = sid
                self.sid_to_user[sid] = user_id
                logger.info(f"User registered: {user_id}")
                
                mongodb.log_websocket_event(
                    event_type="register",
                    user_type="user",
                    user_id=user_id,
                    details=data
                )
                
                await self.sio.emit('registration_success', {
                    'user_id': user_id,
                    'timestamp': datetime.now().isoformat()
                }, room=sid)
        
        @self.sio.event
        async def register_service(sid, data):
            """Register service provider connection"""
            service_id = data.get('service_id')
            service_type = data.get('service_type')
            
            if service_id and service_type:
                self.service_connections[service_id] = sid
                self.sid_to_service[sid] = service_id
                self.service_types[service_id] = service_type
                logger.info(f"Service registered: {service_id} ({service_type})")
                
                mongodb.log_websocket_event(
                    event_type="register",
                    user_type="service",
                    user_id=service_id,
                    details=data
                )
                
                await self.sio.emit('registration_success', {
                    'service_id': service_id,
                    'service_type': service_type,
                    'timestamp': datetime.now().isoformat()
                }, room=sid)
        
        @self.sio.event
        async def ping(sid, data):
            """Handle ping from client"""
            await self.sio.emit('pong', {'timestamp': datetime.now().isoformat()}, room=sid)
    
    async def notify_user(self, user_id: str, event: str, data: dict):
        """
        Send notification to specific user
        
        Args:
            user_id: User ID
            event: Event name
            data: Data to send
        """
        if user_id in self.user_connections:
            sid = self.user_connections[user_id]
            await self.sio.emit(event, data, room=sid)
            logger.info(f"Sent {event} to user {user_id}")
        else:
            logger.warning(f"User {user_id} not connected")
    
    async def notify_service(self, service_id: str, event: str, data: dict):
        """
        Send notification to specific service
        
        Args:
            service_id: Service ID
            event: Event name
            data: Data to send
        """
        if service_id in self.service_connections:
            sid = self.service_connections[service_id]
            await self.sio.emit(event, data, room=sid)
            logger.info(f"Sent {event} to service {service_id}")
        else:
            logger.warning(f"Service {service_id} not connected")
    
    async def broadcast_to_services(
        self, 
        service_type: str, 
        event: str, 
        data: dict,
        exclude_service_id: Optional[str] = None
    ):
        """
        Broadcast message to all services of a specific type
        
        Args:
            service_type: Type of service (hospital, fire_station, police_station)
            event: Event name
            data: Data to send
            exclude_service_id: Optional service ID to exclude from broadcast
        """
        count = 0
        for service_id, sid in self.service_connections.items():
            # Check if service matches type and is not excluded
            if (self.service_types.get(service_id) == service_type and 
                service_id != exclude_service_id):
                await self.sio.emit(event, data, room=sid)
                count += 1
        
        logger.info(f"Broadcasted {event} to {count} services of type {service_type}")
        
        mongodb.log_websocket_event(
            event_type="broadcast",
            user_type="service",
            user_id=service_type,
            details={
                'event': event,
                'count': count,
                'excluded': exclude_service_id
            }
        )
    
    async def broadcast_to_all_services(self, event: str, data: dict):
        """
        Broadcast message to all connected services
        
        Args:
            event: Event name
            data: Data to send
        """
        count = 0
        for sid in self.service_connections.values():
            await self.sio.emit(event, data, room=sid)
            count += 1
        
        logger.info(f"Broadcasted {event} to {count} services")
    
    async def broadcast_to_all_users(self, event: str, data: dict):
        """
        Broadcast message to all connected users
        
        Args:
            event: Event name
            data: Data to send
        """
        count = 0
        for sid in self.user_connections.values():
            await self.sio.emit(event, data, room=sid)
            count += 1
        
        logger.info(f"Broadcasted {event} to {count} users")
    
    def get_connected_services_count(self, service_type: Optional[str] = None) -> int:
        """Get count of connected services"""
        if service_type:
            return sum(1 for sid, stype in self.service_types.items() 
                      if stype == service_type)
        return len(self.service_connections)
    
    def get_connected_users_count(self) -> int:
        """Get count of connected users"""
        return len(self.user_connections)
    
    def is_service_online(self, service_id: str) -> bool:
        """Check if service is connected"""
        return service_id in self.service_connections
    
    def is_user_online(self, user_id: str) -> bool:
        """Check if user is connected"""
        return user_id in self.user_connections


# Create global connection manager instance
manager = ConnectionManager()
