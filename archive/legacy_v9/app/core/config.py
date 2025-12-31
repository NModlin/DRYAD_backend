# app/core/config.py
"""
Configuration management for DRYAD.AI Backend.
Provides secure configuration with mandatory secrets validation for production.
"""

import os
import secrets
import logging
import re
from typing import Dict, Any
from pathlib import Path

# Initialize logger before using it
logger = logging.getLogger(__name__)

# Load .env file if it exists
try:
    from dotenv import load_dotenv
    env_path = Path(__file__).parent.parent.parent / ".env"
    if env_path.exists():
        load_dotenv(env_path)
        logger.info(f"Loaded environment variables from {env_path}")
except ImportError:
    logger.warning("python-dotenv not installed, .env file will not be loaded")


class SecureSecretsManager:
    """Manages secure secrets with validation and entropy checking."""

    # Known insecure default values that must be rejected
    INSECURE_DEFAULTS = {
        "your-secret-key-change-in-production",
        "your-super-secret-jwt-key-change-in-production",
        "test-jwt-secret-key-for-testing-only",
        "development-jwt-secret",
        "jwt-secret-key",
        "dev-secret-key-change-in-production",
        "secret",
        "password",
        "123456",
        "admin",
        "admin123",
        "changeme",
        "default",
        "your-openai-api-key-here",
        "your-google-client-secret",
        "your_openai_api_key_here",
        "your_anthropic_api_key_here",
        "redis-secure-password-change-in-production",
        "weaviate-secure-key-change-in-production"
    }

    @staticmethod
    def validate_secret_strength(secret: str, min_length: int = 32) -> Dict[str, Any]:
        """Validate secret strength and entropy."""
        if not secret:
            return {"valid": False, "reason": "Secret is empty"}

        if len(secret) < min_length:
            return {"valid": False, "reason": f"Secret too short (minimum {min_length} characters)"}

        if secret.lower() in SecureSecretsManager.INSECURE_DEFAULTS:
            return {"valid": False, "reason": "Secret matches known insecure default value"}

        # Check for common patterns that indicate weak secrets
        weak_patterns = [
            r'^[a-z]+$',  # Only lowercase letters
            r'^[A-Z]+$',  # Only uppercase letters
            r'^[0-9]+$',  # Only numbers
            r'^(.)\1{10,}$',  # Repeated characters
            r'(password|secret|key|admin|test|dev)',  # Common words
        ]

        for pattern in weak_patterns:
            if re.search(pattern, secret, re.IGNORECASE):
                return {"valid": False, "reason": f"Secret contains weak pattern: {pattern}"}

        # Calculate entropy (simplified)
        unique_chars = len(set(secret))
        entropy_score = unique_chars / len(secret)

        if entropy_score < 0.3:  # Less than 30% unique characters
            return {"valid": False, "reason": "Secret has low entropy (too many repeated characters)"}

        return {"valid": True, "entropy_score": entropy_score}

    @staticmethod
    def generate_secure_secret(length: int = 48) -> str:
        """Generate a cryptographically secure secret."""
        return secrets.token_urlsafe(length)

    @staticmethod
    def is_production_environment(environment: str) -> bool:
        """Check if environment is production or staging."""
        return environment.lower() in {"production", "prod", "staging", "stage"}


class Config:
    """
    Secure configuration class with mandatory secrets validation.
    Fails fast in production if required secrets are missing or insecure.
    """

    def __init__(self):
        """Initialize configuration with security-first approach."""
        self.secrets_manager = SecureSecretsManager()
        self._load_defaults()
        self._validate_critical_settings()
    
    def _load_defaults(self):
        """Load configuration with sensible defaults."""
        
        # =============================================================================
        # DEPLOYMENT CONFIGURATION
        # =============================================================================
        self.INSTALL_TIER = os.getenv("INSTALL_TIER", "minimal")
        self.ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
        self.LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
        
        # =============================================================================
        # SECURITY CONFIGURATION - MANDATORY SECRETS VALIDATION
        # =============================================================================
        self._configure_jwt_security()
        self._configure_oauth_security()
        self._configure_api_keys()

        self.JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
        self.JWT_EXPIRATION_HOURS = int(os.getenv("JWT_EXPIRATION_HOURS", "1"))  # Reduced from 24 to 1 hour
        self.REFRESH_TOKEN_EXPIRATION_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRATION_DAYS", "7"))  # Reduced from 30 to 7 days
        
        # =============================================================================
        # DATABASE CONFIGURATION
        # =============================================================================
        # Ensure data directory exists
        data_dir = Path("./data")
        data_dir.mkdir(exist_ok=True)
        
        self.DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./data/DRYAD.AI.db")
        
        # =============================================================================
        # LLM CONFIGURATION - OPTIMIZED FOR SELF-CONTAINED AI
        # =============================================================================
        self.LLM_PROVIDER = os.getenv("LLM_PROVIDER", "llamacpp")  # Self-contained AI default
        self.LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.1"))
        self.LLM_MAX_TOKENS = int(os.getenv("LLM_MAX_TOKENS", "2048"))
        self.LLM_TIMEOUT = int(os.getenv("LLM_TIMEOUT", "30"))
        
        # Local LlamaCpp Configuration
        self.LLAMACPP_MODEL = os.getenv("LLAMACPP_MODEL", "tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf")
        models_dir = Path("./models")
        models_dir.mkdir(exist_ok=True)
        self.LLAMACPP_MODEL_PATH = os.getenv("LLAMACPP_MODEL_PATH", str(models_dir))
        
        # External LLM Configuration (optional)
        self.OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
        self.OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
        self.OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        self.OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2:3b")
        
        # =============================================================================
        # VECTOR DATABASE CONFIGURATION
        # =============================================================================
        self.WEAVIATE_URL = os.getenv("WEAVIATE_URL", "http://localhost:8080")
        self.WEAVIATE_API_KEY = os.getenv("WEAVIATE_API_KEY", "")
        self.WEAVIATE_TIMEOUT_SECONDS = int(os.getenv("WEAVIATE_TIMEOUT_SECONDS", "10"))
        self.WEAVIATE_MAX_RETRIES = int(os.getenv("WEAVIATE_MAX_RETRIES", "3"))
        self.WEAVIATE_CLASS_NAME = os.getenv("WEAVIATE_CLASS_NAME", "GremlinsDocument")
        self.EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
        
        # =============================================================================
        # TASK QUEUE CONFIGURATION
        # =============================================================================
        self.CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
        self.CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/0")
        self.REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
        
        # =============================================================================
        # FEATURE FLAGS
        # =============================================================================
        # Conservative defaults - only enable features that work without external services
        self.ENABLE_VECTOR_SEARCH = self._str_to_bool(os.getenv("ENABLE_VECTOR_SEARCH", "false"))
        self.ENABLE_MULTI_AGENT = self._str_to_bool(os.getenv("ENABLE_MULTI_AGENT", "true"))  # Works with fallback
        self.ENABLE_MULTIMODAL = self._str_to_bool(os.getenv("ENABLE_MULTIMODAL", "false"))
        self.ENABLE_TASK_QUEUE = self._str_to_bool(os.getenv("ENABLE_TASK_QUEUE", "false"))
        self.ENABLE_GRAPHQL = self._str_to_bool(os.getenv("ENABLE_GRAPHQL", "true"))  # Works with fallback

        # =============================================================================
        # MODEL CONTEXT PROTOCOL (MCP) CONFIGURATION
        # =============================================================================
        self.MCP_ENABLED = self._str_to_bool(os.getenv("MCP_ENABLED", "true"))  # MCP works with self-contained AI
        self.MCP_VERSION = os.getenv("MCP_VERSION", "2025-06-18")
        self.MCP_MAX_CLIENTS = int(os.getenv("MCP_MAX_CLIENTS", "100"))
        self.MCP_TIMEOUT_SECONDS = int(os.getenv("MCP_TIMEOUT_SECONDS", "30"))
        self.MCP_ALLOW_ANONYMOUS = self._str_to_bool(os.getenv("MCP_ALLOW_ANONYMOUS", "false"))
        self.MCP_LOG_LEVEL = os.getenv("MCP_LOG_LEVEL", "INFO")
        
        # =============================================================================
        # EXTERNAL SERVICE URLS
        # =============================================================================
        self.FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")
        self.API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
        
        # =============================================================================
        # OAUTH CONFIGURATION
        # =============================================================================
        self.GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
        self.GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
        
        # =============================================================================
        # BASIC MODE CONFIGURATION
        # =============================================================================
        self.BASIC_MODE = self._str_to_bool(os.getenv("BASIC_MODE", "false"))
    
    def _str_to_bool(self, value: str) -> bool:
        """Convert string to boolean."""
        return value.lower() in ("true", "1", "yes", "on")
    
    def _configure_jwt_security(self):
        """Configure JWT security with mandatory validation."""
        jwt_secret = os.getenv("JWT_SECRET_KEY")

        # Fail fast if JWT secret is missing in production/staging
        if not jwt_secret:
            if self.secrets_manager.is_production_environment(self.ENVIRONMENT):
                raise ValueError(
                    f"JWT_SECRET_KEY is REQUIRED in {self.ENVIRONMENT} environment. "
                    "Generate a secure key with: python -c 'import secrets; print(secrets.token_urlsafe(48))'"
                )
            else:
                # Development only - generate temporary key with warning
                jwt_secret = self.secrets_manager.generate_secure_secret()
                logger.warning(
                    "🚨 JWT_SECRET_KEY not provided in development. Generated temporary key. "
                    "This key will change on restart, invalidating existing tokens. "
                    "Set JWT_SECRET_KEY in your .env file for persistent tokens."
                )

        # Validate secret strength
        validation_result = self.secrets_manager.validate_secret_strength(jwt_secret)
        if not validation_result["valid"]:
            if self.secrets_manager.is_production_environment(self.ENVIRONMENT):
                raise ValueError(
                    f"JWT_SECRET_KEY validation failed in {self.ENVIRONMENT} environment: "
                    f"{validation_result['reason']}. Generate a secure key with: "
                    "python -c 'import secrets; print(secrets.token_urlsafe(48))'"
                )
            else:
                # Development - replace with secure key and warn
                jwt_secret = self.secrets_manager.generate_secure_secret()
                logger.warning(
                    f"🚨 Insecure JWT secret detected: {validation_result['reason']}. "
                    "Replaced with secure generated key for development."
                )
                # Re-validate the new secure secret to get accurate entropy
                validation_result = self.secrets_manager.validate_secret_strength(jwt_secret)

        self.JWT_SECRET_KEY = jwt_secret
        # Handle case where entropy_score might not be present
        entropy_score = validation_result.get('entropy_score')
        if isinstance(entropy_score, (int, float)):
            logger.info(f"✅ JWT security configured (entropy: {entropy_score:.2f})")
        else:
            logger.info("✅ JWT security configured")

    def _configure_oauth_security(self):
        """Configure OAuth security settings."""
        self.GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
        self.GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")

        # Validate OAuth secrets if provided
        if self.GOOGLE_CLIENT_SECRET:
            validation_result = self.secrets_manager.validate_secret_strength(
                self.GOOGLE_CLIENT_SECRET, min_length=24
            )
            if not validation_result["valid"]:
                if self.secrets_manager.is_production_environment(self.ENVIRONMENT):
                    raise ValueError(
                        f"GOOGLE_CLIENT_SECRET validation failed: {validation_result['reason']}"
                    )
                else:
                    logger.warning(f"⚠️ Google OAuth secret validation failed: {validation_result['reason']}")

    def _configure_api_keys(self):
        """Configure and validate API keys."""
        # OpenAI API Key
        openai_key = os.getenv("OPENAI_API_KEY")
        if openai_key and openai_key in self.secrets_manager.INSECURE_DEFAULTS:
            if self.secrets_manager.is_production_environment(self.ENVIRONMENT):
                raise ValueError("OPENAI_API_KEY contains insecure default value")
            else:
                logger.warning("⚠️ OpenAI API key contains insecure default value")

        # Weaviate API Key
        weaviate_key = os.getenv("WEAVIATE_API_KEY")
        if weaviate_key and weaviate_key in self.secrets_manager.INSECURE_DEFAULTS:
            if self.secrets_manager.is_production_environment(self.ENVIRONMENT):
                raise ValueError("WEAVIATE_API_KEY contains insecure default value")
            else:
                logger.warning("⚠️ Weaviate API key contains insecure default value")

    def _validate_critical_settings(self):
        """Validate critical configuration settings."""
        # Log configuration status
        logger.info(f"Configuration loaded - Install tier: {self.INSTALL_TIER}, Environment: {self.ENVIRONMENT}")

        if self.BASIC_MODE:
            logger.info("🔧 BASIC MODE enabled - external services optional")

        # Security validation summary
        if self.secrets_manager.is_production_environment(self.ENVIRONMENT):
            logger.info("🔒 Production security validation passed - all secrets validated")
        else:
            logger.info("🔧 Development mode - some security validations relaxed")
        
        # Log feature status
        enabled_features = []
        if self.ENABLE_VECTOR_SEARCH:
            enabled_features.append("vector_search")
        if self.ENABLE_MULTI_AGENT:
            enabled_features.append("multi_agent")
        if self.ENABLE_MULTIMODAL:
            enabled_features.append("multimodal")
        if self.ENABLE_TASK_QUEUE:
            enabled_features.append("task_queue")
        if self.ENABLE_GRAPHQL:
            enabled_features.append("graphql")
        if self.MCP_ENABLED:
            enabled_features.append("mcp_server")
        
        logger.info(f"Enabled features: {', '.join(enabled_features) if enabled_features else 'none'}")
    
    def get_feature_status(self) -> Dict[str, Any]:
        """Get current feature status for API responses."""
        return {
            "install_tier": self.INSTALL_TIER,
            "environment": self.ENVIRONMENT,
            "basic_mode": self.BASIC_MODE,
            "features": {
                "vector_search": self.ENABLE_VECTOR_SEARCH,
                "multi_agent": self.ENABLE_MULTI_AGENT,
                "multimodal": self.ENABLE_MULTIMODAL,
                "task_queue": self.ENABLE_TASK_QUEUE,
                "graphql": self.ENABLE_GRAPHQL,
                "mcp_server": self.MCP_ENABLED,
            },
            "mcp_config": {
                "enabled": self.MCP_ENABLED,
                "version": self.MCP_VERSION,
                "max_clients": self.MCP_MAX_CLIENTS,
                "timeout_seconds": self.MCP_TIMEOUT_SECONDS,
                "allow_anonymous": self.MCP_ALLOW_ANONYMOUS,
                "log_level": self.MCP_LOG_LEVEL
            },
            "llm_provider": self.LLM_PROVIDER,
            "database_type": "sqlite" if "sqlite" in self.DATABASE_URL else "postgresql"
        }


# Global configuration instance
config = Config()

# Export commonly used settings for backward compatibility
JWT_SECRET_KEY = config.JWT_SECRET_KEY
JWT_ALGORITHM = config.JWT_ALGORITHM
JWT_EXPIRATION_HOURS = config.JWT_EXPIRATION_HOURS
DATABASE_URL = config.DATABASE_URL
BASIC_MODE = config.BASIC_MODE
