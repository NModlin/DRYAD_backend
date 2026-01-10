"""
Configuration settings for Uni0 application
"""

import os
from typing import Optional
try:
    from pydantic_settings import BaseSettings
except ImportError:
    # Fallback for older pydantic versions
    from pydantic import BaseSettings


class Settings(BaseSettings):
    """Application settings"""

    # Application
    APP_NAME: str = "Uni0 University System"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    # API
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Uni0"

    # Security - MUST be set via environment variable in production
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-here-change-in-production")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Database
    DATABASE_URL: str = "sqlite:///./uni0.db"
    DATABASE_POOL_SIZE: int = 5
    DATABASE_MAX_OVERFLOW: int = 10
    
    # CORS
    BACKEND_CORS_ORIGINS: list = ["http://localhost:3000", "http://localhost:8000"]
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # University System
    MAX_AGENTS_PER_UNIVERSITY: int = 100
    DEFAULT_UNIVERSITY_SETTINGS: dict = {
        "auto_approve_agents": True,
        "max_concurrent_competitions": 5,
        "skill_tree_enabled": True,
        "competition_system_enabled": True
    }
    
    # WebSocket
    WEBSOCKET_HEARTBEAT_INTERVAL: int = 30  # seconds
    WEBSOCKET_MAX_CONNECTIONS: int = 1000
    
    # File Storage
    UPLOAD_DIR: str = "./uploads"
    MAX_UPLOAD_SIZE: int = 100 * 1024 * 1024  # 100MB
    
    # External Services (placeholders for future integration)
    OPENAI_API_KEY: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None
    GEMINI_API_KEY: Optional[str] = None
    
    # Redis
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    
    class Config:
        env_file = ".env"
        case_sensitive = True

    def __init__(self, **data):
        super().__init__(**data)
        # Validate SECRET_KEY in production
        env = os.getenv("ENVIRONMENT", "development").lower()
        if env == "production":
            if self.SECRET_KEY == "your-secret-key-here-change-in-production":
                raise ValueError(
                    "CRITICAL: SECRET_KEY must be set via environment variable in production. "
                    "Generate a new key with: openssl rand -base64 32"
                )
            if len(self.SECRET_KEY) < 32:
                raise ValueError("SECRET_KEY must be at least 32 characters long in production")


# Create settings instance
settings = Settings()


def get_settings() -> Settings:
    """Get application settings"""
    return settings


# Environment-specific configurations
class DevelopmentSettings(Settings):
    """Development environment settings"""
    DEBUG: bool = True
    LOG_LEVEL: str = "DEBUG"
    DATABASE_URL: str = "sqlite:///./uni0_dev.db"


class ProductionSettings(Settings):
    """Production environment settings"""
    DEBUG: bool = False
    LOG_LEVEL: str = "WARNING"
    # Production database URL should be set via environment variable
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./uni0_prod.db")


class TestSettings(Settings):
    """Test environment settings"""
    DEBUG: bool = True
    LOG_LEVEL: str = "DEBUG"
    DATABASE_URL: str = "sqlite:///./uni0_test.db"


# Environment detection
def get_environment_settings() -> Settings:
    """Get settings based on current environment"""
    env = os.getenv("ENVIRONMENT", "development").lower()
    
    if env == "production":
        return ProductionSettings()
    elif env == "test":
        return TestSettings()
    else:
        return DevelopmentSettings()


# Default settings instance (can be overridden by environment)
current_settings = get_environment_settings()