"""
Emergency Response System - Main FastAPI Application
Entry point for the backend API
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import socketio
import logging
from datetime import datetime

from app.config import settings
from app.routers import auth, requests, services, user_auth
from app.websocket.manager import manager
from app.database.postgis import db
from app.database.mongodb import mongodb

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    logger.info("🚀 Starting Emergency Response System...")
    logger.info(f"📊 PostgreSQL: {settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}")
    logger.info(f"📊 MongoDB: {settings.MONGODB_HOST}:{settings.MONGODB_PORT}")
    
    # Log system startup
    mongodb.log_system_event(
        level="info",
        message="System starting up",
        component="main"
    )
    
    yield
    
    # Shutdown
    logger.info("🛑 Shutting down Emergency Response System...")
    db.close()
    mongodb.close()
    
    mongodb.log_system_event(
        level="info",
        message="System shutting down",
        component="main"
    )


# Create FastAPI app
app = FastAPI(
    title="Emergency Response System API",
    description="Real-time emergency response dispatch system",
    version="1.0.0",
    lifespan=lifespan
)

# Create Socket.IO ASGI app
sio_app = socketio.ASGIApp(
    socketio_server=manager.sio,
    other_asgi_app=app,
    socketio_path="/socket.io"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    
    mongodb.log_system_event(
        level="error",
        message=f"Unhandled exception: {str(exc)}",
        component="main",
        details={"path": str(request.url)}
    )
    
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "detail": str(exc) if settings.DEBUG else "An error occurred",
            "timestamp": datetime.now().isoformat()
        }
    )


# Include routers
app.include_router(auth.router)
app.include_router(requests.router)
app.include_router(services.router)
app.include_router(user_auth.router)


# Health check endpoint
@app.get("/health")
async def health_check():
    """Check API health and database connectivity"""
    postgres_connected = False
    mongodb_connected = False
    
    try:
        with db.get_cursor() as cursor:
            cursor.execute("SELECT 1")
            postgres_connected = True
    except Exception as e:
        logger.error(f"PostgreSQL health check failed: {e}")
    
    try:
        mongodb_connected = mongodb.is_connected()
    except Exception as e:
        logger.error(f"MongoDB health check failed: {e}")
    
    status = "healthy" if (postgres_connected and mongodb_connected) else "degraded"
    
    return {
        "status": status,
        "timestamp": datetime.now().isoformat(),
        "database_connected": postgres_connected,
        "mongodb_connected": mongodb_connected,
        "version": "1.0.0"
    }


# Root endpoint
@app.get("/")
async def root():
    """API root endpoint"""
    return {
        "message": "Emergency Response System API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }


# Statistics endpoint
@app.get("/api/stats")
async def get_system_stats():
    """Get system statistics"""
    with db.get_cursor() as cursor:
        # Count services
        cursor.execute("SELECT COUNT(*) as count FROM service_providers")
        total_services = cursor.fetchone()['count']
        
        cursor.execute("SELECT COUNT(*) as count FROM service_providers WHERE is_online = true")
        online_services = cursor.fetchone()['count']
        
        # Count requests by status
        cursor.execute("SELECT COUNT(*) as count FROM emergency_requests WHERE status = 'pending'")
        pending_requests = cursor.fetchone()['count']
        
        cursor.execute("SELECT COUNT(*) as count FROM emergency_requests WHERE status = 'accepted'")
        accepted_requests = cursor.fetchone()['count']
        
        cursor.execute("SELECT COUNT(*) as count FROM emergency_requests WHERE status = 'completed'")
        completed_requests = cursor.fetchone()['count']
        
        # Services by type
        cursor.execute("""
            SELECT service_type, COUNT(*) as count
            FROM service_providers
            GROUP BY service_type
        """)
        services_by_type = {row['service_type']: row['count'] for row in cursor.fetchall()}
    
    return {
        "total_services": total_services,
        "online_services": online_services,
        "pending_requests": pending_requests,
        "accepted_requests": accepted_requests,
        "completed_requests": completed_requests,
        "services_by_type": services_by_type,
        "connected_services": manager.get_connected_services_count(),
        "connected_users": manager.get_connected_users_count(),
        "timestamp": datetime.now().isoformat()
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:sio_app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )
