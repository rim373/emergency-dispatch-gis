"""
Emergency Response System - MongoDB Connection
Handles logging and non-spatial data storage
"""

from pymongo import MongoClient
from pymongo.database import Database
from pymongo.collection import Collection
from typing import Dict, List, Optional
from datetime import datetime
import logging

from app.config import settings

logger = logging.getLogger(__name__)


class MongoDB:
    """MongoDB connection manager for logging"""
    
    def __init__(self):
        """Initialize MongoDB connection"""
        self.client: Optional[MongoClient] = None
        self.db: Optional[Database] = None
        self._connect()
    
    def _connect(self):
        """Connect to MongoDB"""
        try:
            self.client = MongoClient(
                settings.mongodb_url,
                serverSelectionTimeoutMS=5000
            )
            # Test connection
            self.client.server_info()
            
            self.db = self.client[settings.MONGODB_DB]
            logger.info("MongoDB connected successfully")
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise
    
    # ==========================================
    # Request Logging
    # ==========================================
    
    def log_request_created(self, request_data: Dict):
        """Log new emergency request creation"""
        log_entry = {
            "request_id": request_data.get("request_id"),
            "request_type": request_data.get("request_type"),
            "action": "created",
            "location": {
                "latitude": request_data.get("latitude"),
                "longitude": request_data.get("longitude")
            },
            "timestamp": datetime.now(),
            "status": "pending"
        }
        self.db.request_logs.insert_one(log_entry)
    
    def log_request_status_change(
        self, 
        request_id: str, 
        old_status: str, 
        new_status: str,
        changed_by: Optional[str] = None
    ):
        """Log request status change"""
        log_entry = {
            "request_id": request_id,
            "action": "status_change",
            "old_status": old_status,
            "new_status": new_status,
            "changed_by": changed_by,
            "timestamp": datetime.now()
        }
        self.db.request_logs.insert_one(log_entry)
    
    # ==========================================
    # Service Logging
    # ==========================================
    
    def log_service_action(
        self, 
        service_id: str, 
        action: str, 
        details: Optional[Dict] = None
    ):
        """Log service provider action"""
        log_entry = {
            "service_id": service_id,
            "action": action,
            "details": details or {},
            "timestamp": datetime.now()
        }
        self.db.service_logs.insert_one(log_entry)
    
    def log_service_login(self, service_id: str, service_name: str):
        """Log service provider login"""
        self.log_service_action(
            service_id=service_id,
            action="login",
            details={"service_name": service_name}
        )
    
    def log_service_response(
        self, 
        service_id: str, 
        request_id: str, 
        response_type: str
    ):
        """Log service response to request"""
        self.log_service_action(
            service_id=service_id,
            action="response",
            details={
                "request_id": request_id,
                "response_type": response_type
            }
        )
    
    # ==========================================
    # WebSocket Event Logging
    # ==========================================
    
    def log_websocket_event(
        self, 
        event_type: str, 
        user_type: str,
        user_id: str,
        details: Optional[Dict] = None
    ):
        """Log WebSocket event"""
        log_entry = {
            "event_type": event_type,
            "user_type": user_type,
            "user_id": user_id,
            "details": details or {},
            "timestamp": datetime.now()
        }
        self.db.websocket_events.insert_one(log_entry)
    
    # ==========================================
    # System Logging
    # ==========================================
    
    def log_system_event(
        self, 
        level: str, 
        message: str, 
        component: str,
        details: Optional[Dict] = None
    ):
        """Log system event"""
        log_entry = {
            "level": level,
            "message": message,
            "component": component,
            "details": details or {},
            "timestamp": datetime.now()
        }
        self.db.system_logs.insert_one(log_entry)
    
    # ==========================================
    # Query Methods
    # ==========================================
    
    def get_request_logs(
        self, 
        request_id: str, 
        limit: int = 100
    ) -> List[Dict]:
        """Get logs for specific request"""
        return list(
            self.db.request_logs
            .find({"request_id": request_id})
            .sort("timestamp", -1)
            .limit(limit)
        )
    
    def get_service_logs(
        self, 
        service_id: str, 
        limit: int = 100
    ) -> List[Dict]:
        """Get logs for specific service"""
        return list(
            self.db.service_logs
            .find({"service_id": service_id})
            .sort("timestamp", -1)
            .limit(limit)
        )
    
    def get_recent_system_logs(
        self, 
        level: Optional[str] = None, 
        limit: int = 100
    ) -> List[Dict]:
        """Get recent system logs"""
        query = {"level": level} if level else {}
        return list(
            self.db.system_logs
            .find(query)
            .sort("timestamp", -1)
            .limit(limit)
        )
    
    def is_connected(self) -> bool:
        """Check if MongoDB is connected"""
        try:
            self.client.admin.command('ping')
            return True
        except Exception:
            return False
    
    def close(self):
        """Close MongoDB connection"""
        if self.client:
            self.client.close()
            logger.info("MongoDB connection closed")


# Create global MongoDB instance
mongodb = MongoDB()
