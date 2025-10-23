"""
Production Configuration for DRYAD.AI Backend
Optimized settings for production deployment
"""

import os
from typing import List, Optional
from pydantic import BaseSettings, validator, ConfigDict


class ProductionSettings(BaseSettings):
    """Production-specific settings with validation"""

    # ========================================================================
    # ENVIRONMENT
    # ========================================================================
    ENVIRONMENT: str = "production"
    DEBUG: bool = False
    LOG_LEVEL: str = "info"

    # ========================================================================
    # APPLICATION
    # ========================================================================
    APP_NAME: str = "DRYAD.AI"
    APP_VERSION: str = "1.0.0"
    API_V1_PREFIX: str = "/api/v1"

    # ========================================================================
    # SERVER
    # ========================================================================
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    WORKERS: int = 4
    RELOAD: bool = False

    # ========================================================================
    # DATABASE
    # ========================================================================
    DATABASE_URL: str
    DB_POOL_SIZE: int = 20
    DB_MAX_OVERFLOW: int = 30
    DB_POOL_TIMEOUT: int = 30
    DB_POOL_RECYCLE: int = 3600

    @validator("DATABASE_URL")
    def validate_database_url(cls, v):
        """Ensure database URL is set"""
        if not v:
            raise ValueError("DATABASE_URL must be set in production")
        return v

    # ========================================================================
    # SECURITY
    # ========================================================================
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    @validator("JWT_SECRET_KEY")
    def validate_jwt_secret(cls, v):
        """Ensure JWT secret is strong"""
        if len(v) < 32:
            raise ValueError("JWT_SECRET_KEY must be at least 32 characters")
        if v == "CHANGE_THIS_TO_A_SECURE_RANDOM_STRING_AT_LEAST_32_CHARACTERS":
            raise ValueError("JWT_SECRET_KEY must be changed from default")
        return v

    # CORS
    CORS_ORIGINS: List[str] = []
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: List[str] = ["GET", "POST", "PUT", "DELETE", "PATCH"]
    CORS_ALLOW_HEADERS: List[str] = ["*"]

    # Rate Limiting
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_PER_MINUTE: int = 60
    RATE_LIMIT_PER_HOUR: int = 1000

    # ========================================================================
    # AI/LLM CONFIGURATION
    # ========================================================================
    USE_LOCAL_LLM: bool = True
    LLM_PROVIDER: str = "llamacpp"
    LLM_MODEL_PATH: str = "models/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf"
    LLM_CONTEXT_LENGTH: int = 2048
    LLM_TEMPERATURE: float = 0.7
    LLM_MAX_TOKENS: int = 512
    LLM_N_THREADS: int = 8
    LLM_N_GPU_LAYERS: int = 0

    # OpenAI (optional)
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_MODEL: str = "gpt-4"
    OPENAI_MAX_TOKENS: int = 2048

    # ========================================================================
    # MULTI-AGENT SYSTEM
    # ========================================================================
    ENABLE_MULTI_AGENT: bool = True
    AGENT_TIMEOUT: int = 300
    AGENT_MAX_RETRIES: int = 3

    # ========================================================================
    # SELF-HEALING SYSTEM
    # ========================================================================
    ENABLE_SELF_HEALING: bool = True
    GUARDIAN_ENABLED: bool = True
    GUARDIAN_CHECK_INTERVAL: int = 10
    WORKER_CHECK_INTERVAL: int = 10
    WORKER_MAX_CONCURRENT_TASKS: int = 3
    SELF_HEALING_AUTO_APPROVE: bool = False

    # ========================================================================
    # PERFORMANCE
    # ========================================================================
    ENABLE_PERFORMANCE_OPTIMIZATION: bool = True
    CACHE_ENABLED: bool = True
    CACHE_TTL: int = 3600
    CACHE_MAX_SIZE: int = 1000

    # ========================================================================
    # EXTERNAL SERVICES
    # ========================================================================
    # Redis
    REDIS_URL: Optional[str] = None
    REDIS_ENABLED: bool = False

    # Weaviate
    WEAVIATE_URL: Optional[str] = None
    WEAVIATE_ENABLED: bool = False

    # ========================================================================
    # INTEGRATIONS
    # ========================================================================
    # Microsoft Teams
    TEAMS_WEBHOOK_URL: Optional[str] = None
    TEAMS_ENABLED: bool = False

    # DRYAD Teams Channel (for deployment/integration updates)
    DRYAD_TEAMS_WEBHOOK_URL: Optional[str] = None

    # Slack
    SLACK_WEBHOOK_URL: Optional[str] = None
    SLACK_ENABLED: bool = False

    # Email
    SMTP_HOST: Optional[str] = None
    SMTP_PORT: int = 587
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    SMTP_FROM: Optional[str] = None
    EMAIL_ENABLED: bool = False

    # ========================================================================
    # MONITORING & LOGGING
    # ========================================================================
    LOG_FORMAT: str = "json"
    LOG_FILE: str = "logs/DRYAD.AI.log"
    LOG_MAX_BYTES: int = 10485760  # 10MB
    LOG_BACKUP_COUNT: int = 5

    METRICS_ENABLED: bool = True
    PROMETHEUS_PORT: int = 9090

    # Sentry
    SENTRY_DSN: Optional[str] = None
    SENTRY_ENABLED: bool = False
    SENTRY_ENVIRONMENT: str = "production"
    SENTRY_TRACES_SAMPLE_RATE: float = 0.1

    # ========================================================================
    # STORAGE
    # ========================================================================
    UPLOAD_DIR: str = "data/uploads"
    MAX_UPLOAD_SIZE: int = 104857600  # 100MB
    ALLOWED_EXTENSIONS: List[str] = ["pdf", "txt", "doc", "docx", "png", "jpg", "jpeg"]

    BACKUP_DIR: str = "backups"
    BACKUP_RETENTION_DAYS: int = 30
    AUTO_BACKUP_ENABLED: bool = True
    BACKUP_SCHEDULE: str = "0 2 * * *"  # 2 AM daily

    # ========================================================================
    # FEATURE FLAGS
    # ========================================================================
    FEATURE_GRAPHQL: bool = True
    FEATURE_WEBSOCKET: bool = True
    FEATURE_MCP_SERVER: bool = True
    FEATURE_MULTIMODAL: bool = True
    FEATURE_RAG: bool = True

    # ========================================================================
    # SECURITY HEADERS
    # ========================================================================
    HSTS_MAX_AGE: int = 31536000  # 1 year
    HSTS_INCLUDE_SUBDOMAINS: bool = True
    CSP_DEFAULT_SRC: str = "self"
    CSP_SCRIPT_SRC: str = "self unsafe-inline unsafe-eval"
    CSP_STYLE_SRC: str = "self unsafe-inline"

    # ========================================================================
    # SSL/TLS
    # ========================================================================
    SSL_CERT_PATH: str = "/etc/nginx/ssl/cert.pem"
    SSL_KEY_PATH: str = "/etc/nginx/ssl/key.pem"
    SSL_ENABLED: bool = True

    # ========================================================================
    # DEPLOYMENT
    # ========================================================================
    DEPLOYMENT_ENV: str = "production"
    DEPLOYMENT_VERSION: str = "1.0.0"
    DEPLOYMENT_DATE: str = "2025-10-02"

    # ========================================================================
    # HEALTH CHECKS
    # ========================================================================
    HEALTH_CHECK_INTERVAL: int = 30
    HEALTH_CHECK_TIMEOUT: int = 10
    HEALTH_CHECK_RETRIES: int = 3

    model_config = ConfigDict(
        env_file=".env.production",
        env_file_encoding="utf-8",
        case_sensitive=True
    )

    def get_security_headers(self) -> dict:
        """Get security headers for HTTP responses"""
        return {
            "Strict-Transport-Security": f"max-age={self.HSTS_MAX_AGE}; includeSubDomains" if self.HSTS_INCLUDE_SUBDOMAINS else f"max-age={self.HSTS_MAX_AGE}",
            "X-Frame-Options": "SAMEORIGIN",
            "X-Content-Type-Options": "nosniff",
            "X-XSS-Protection": "1; mode=block",
            "Referrer-Policy": "strict-origin-when-cross-origin",
            "Content-Security-Policy": f"default-src '{self.CSP_DEFAULT_SRC}'; script-src '{self.CSP_SCRIPT_SRC}'; style-src '{self.CSP_STYLE_SRC}'",
        }

    def is_production(self) -> bool:
        """Check if running in production"""
        return self.ENVIRONMENT == "production"

    def validate_production_requirements(self) -> List[str]:
        """Validate all production requirements are met"""
        errors = []

        # Check critical settings
        if self.DEBUG:
            errors.append("DEBUG must be False in production")

        if not self.SSL_ENABLED:
            errors.append("SSL must be enabled in production")

        if not self.RATE_LIMIT_ENABLED:
            errors.append("Rate limiting must be enabled in production")

        if self.SELF_HEALING_AUTO_APPROVE:
            errors.append("Auto-approve should be disabled in production")

        if not self.CORS_ORIGINS:
            errors.append("CORS origins must be configured in production")

        if not self.TEAMS_WEBHOOK_URL and self.TEAMS_ENABLED:
            errors.append("Teams webhook URL required when Teams is enabled")

        return errors


# Create production settings instance
production_settings = ProductionSettings()

# Validate production requirements
validation_errors = production_settings.validate_production_requirements()
if validation_errors:
    print("⚠️  Production Configuration Warnings:")
    for error in validation_errors:
        print(f"  - {error}")

