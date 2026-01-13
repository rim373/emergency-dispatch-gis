"""
Emergency Response System - Configuration
Loads environment variables and provides application settings
"""

from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # Database settings
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "emergency_response"
    POSTGRES_USER: str = "emergency_app"
    POSTGRES_PASSWORD: str = "emergency_pass_2024"
    
    # MongoDB settings
    MONGODB_HOST: str = "localhost"
    MONGODB_PORT: int = 27017
    MONGODB_DB: str = "emergency_response_logs"
    
    # JWT settings
    JWT_SECRET_KEY: str = "your-super-secret-jwt-key-change-this-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 hours
    
    # Server settings
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = True
    
    # CORS settings
    CORS_ORIGINS: str = "*"
    
    # WebSocket settings
    WEBSOCKET_PING_INTERVAL: int = 25
    WEBSOCKET_PING_TIMEOUT: int = 60

    # MQTT settings
    MQTT_BROKER_HOST: str = "localhost"
    MQTT_BROKER_PORT: int = 1883
    MQTT_WEBSOCKET_PORT: int = 9001
    MQTT_KEEPALIVE: int = 60

    @property
    def postgres_dsn(self) -> str:
        """Get PostgreSQL connection string"""
        return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
    
    @property
    def mongodb_url(self) -> str:
        """Get MongoDB connection string"""
        return f"mongodb://{self.MONGODB_HOST}:{self.MONGODB_PORT}"
    
    @property
    def cors_origins_list(self) -> List[str]:
        """Get CORS origins as list"""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Create global settings instance
settings = Settings()

# Alias for backward compatibility
Config = settings
