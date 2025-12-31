# Task 1-27: Environment Configuration Validation

**Phase:** 1 - Foundation & Beta Readiness  
**Week:** 7 - Production Infrastructure  
**Priority:** CRITICAL  
**Estimated Hours:** 4 hours

---

## 📋 OVERVIEW

Implement comprehensive environment variable validation, secrets management, and configuration verification to prevent deployment failures and security vulnerabilities.

---

## 🎯 OBJECTIVES

1. Document all required environment variables
2. Create environment validation script
3. Implement secrets rotation strategy
4. Add environment-specific configuration files
5. Create configuration validation tests
6. Implement secure secrets management

---

## 📊 CURRENT STATE

**Existing:**
- `.env` file support via python-dotenv
- Basic config in `app/core/config.py`
- SecureSecretsManager class

**Gaps:**
- No comprehensive environment variable documentation
- No validation on startup
- No secrets rotation strategy
- No environment-specific validation

---

## 🔧 IMPLEMENTATION

### 1. Environment Variables Documentation

Create `docs/deployment/ENVIRONMENT_VARIABLES.md`:

```markdown
# Environment Variables Reference

## Required Variables (All Environments)

### Database
- `DATABASE_URL` - Database connection string
  - Development: `sqlite:///./data/DRYAD.AI.db`
  - Production: `postgresql://user:pass@host:5432/dryad`

### Security
- `JWT_SECRET_KEY` - JWT signing key (min 48 chars)
  - Generate: `python -c 'import secrets; print(secrets.token_urlsafe(48))'`
- `JWT_ALGORITHM` - JWT algorithm (default: HS256)
- `JWT_EXPIRATION_HOURS` - Token expiration (default: 1)

### Application
- `ENVIRONMENT` - Environment name (development/staging/production)
- `LOG_LEVEL` - Logging level (DEBUG/INFO/WARNING/ERROR)
- `API_HOST` - API host (default: 0.0.0.0)
- `API_PORT` - API port (default: 8000)

## Optional Variables

### OAuth2
- `GOOGLE_CLIENT_ID` - Google OAuth client ID
- `GOOGLE_CLIENT_SECRET` - Google OAuth client secret

### External Services
- `OPENAI_API_KEY` - OpenAI API key
- `ANTHROPIC_API_KEY` - Anthropic API key
- `WEAVIATE_URL` - Weaviate vector database URL
- `WEAVIATE_API_KEY` - Weaviate API key

### Caching & Queue
- `REDIS_URL` - Redis connection string
- `CELERY_BROKER_URL` - Celery broker URL
- `CELERY_RESULT_BACKEND` - Celery result backend

### Monitoring
- `SENTRY_DSN` - Sentry error tracking DSN
- `PROMETHEUS_PORT` - Prometheus metrics port

## Environment-Specific Requirements

### Development
- Minimal required: DATABASE_URL, JWT_SECRET_KEY, ENVIRONMENT

### Staging
- All required variables
- Optional: External service keys for testing

### Production
- All required variables
- All security variables must be strong
- External service keys required
- Monitoring variables required
```

---

### 2. Configuration Validation Script

Create `scripts/config/validate_environment.py`:

```python
"""
Environment Configuration Validation

Validates all environment variables before application startup.
"""
from __future__ import annotations

import os
import sys
import logging
from typing import Any
from pathlib import Path
from pydantic import BaseModel, Field, field_validator, ValidationError

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EnvironmentConfig(BaseModel):
    """Environment configuration with validation."""
    
    # Required
    database_url: str = Field(..., min_length=10)
    jwt_secret_key: str = Field(..., min_length=48)
    environment: str = Field(..., pattern="^(development|staging|production)$")
    
    # Optional with defaults
    jwt_algorithm: str = Field(default="HS256")
    jwt_expiration_hours: int = Field(default=1, ge=1, le=24)
    log_level: str = Field(default="INFO", pattern="^(DEBUG|INFO|WARNING|ERROR|CRITICAL)$")
    api_host: str = Field(default="0.0.0.0")
    api_port: int = Field(default=8000, ge=1024, le=65535)
    
    # OAuth2 (optional)
    google_client_id: str | None = None
    google_client_secret: str | None = None
    
    # External Services (optional)
    openai_api_key: str | None = None
    anthropic_api_key: str | None = None
    weaviate_url: str | None = None
    weaviate_api_key: str | None = None
    
    # Caching & Queue (optional)
    redis_url: str | None = None
    celery_broker_url: str | None = None
    celery_result_backend: str | None = None
    
    # Monitoring (optional)
    sentry_dsn: str | None = None
    prometheus_port: int | None = Field(default=None, ge=1024, le=65535)
    
    @field_validator("jwt_secret_key")
    @classmethod
    def validate_jwt_secret(cls, v: str) -> str:
        """Validate JWT secret strength."""
        # Check for insecure defaults
        insecure_defaults = {
            "your-secret-key-change-in-production",
            "your-super-secret-jwt-key-change-in-production",
            "test-jwt-secret-key-for-testing-only",
            "development-jwt-secret",
            "jwt-secret-key",
            "secret",
            "password",
        }
        
        if v.lower() in insecure_defaults:
            raise ValueError("JWT secret matches known insecure default")
        
        # Check entropy
        unique_chars = len(set(v))
        if unique_chars < len(v) * 0.3:
            raise ValueError("JWT secret has low entropy")
        
        return v
    
    @field_validator("database_url")
    @classmethod
    def validate_database_url(cls, v: str) -> str:
        """Validate database URL format."""
        if not (v.startswith("sqlite:///") or v.startswith("postgresql://")):
            raise ValueError("Database URL must be SQLite or PostgreSQL")
        return v


class EnvironmentValidator:
    """Validates environment configuration."""
    
    def __init__(self):
        self.errors: list[str] = []
        self.warnings: list[str] = []
    
    def load_from_env(self) -> dict[str, Any]:
        """Load configuration from environment variables."""
        return {
            # Required
            "database_url": os.getenv("DATABASE_URL"),
            "jwt_secret_key": os.getenv("JWT_SECRET_KEY"),
            "environment": os.getenv("ENVIRONMENT", "development"),
            
            # Optional
            "jwt_algorithm": os.getenv("JWT_ALGORITHM", "HS256"),
            "jwt_expiration_hours": int(os.getenv("JWT_EXPIRATION_HOURS", "1")),
            "log_level": os.getenv("LOG_LEVEL", "INFO"),
            "api_host": os.getenv("API_HOST", "0.0.0.0"),
            "api_port": int(os.getenv("API_PORT", "8000")),
            
            # OAuth2
            "google_client_id": os.getenv("GOOGLE_CLIENT_ID"),
            "google_client_secret": os.getenv("GOOGLE_CLIENT_SECRET"),
            
            # External Services
            "openai_api_key": os.getenv("OPENAI_API_KEY"),
            "anthropic_api_key": os.getenv("ANTHROPIC_API_KEY"),
            "weaviate_url": os.getenv("WEAVIATE_URL"),
            "weaviate_api_key": os.getenv("WEAVIATE_API_KEY"),
            
            # Caching & Queue
            "redis_url": os.getenv("REDIS_URL"),
            "celery_broker_url": os.getenv("CELERY_BROKER_URL"),
            "celery_result_backend": os.getenv("CELERY_RESULT_BACKEND"),
            
            # Monitoring
            "sentry_dsn": os.getenv("SENTRY_DSN"),
            "prometheus_port": int(os.getenv("PROMETHEUS_PORT", "0")) or None,
        }
    
    def validate(self) -> bool:
        """Validate environment configuration."""
        try:
            config_dict = self.load_from_env()
            config = EnvironmentConfig(**config_dict)
            
            # Environment-specific validation
            if config.environment == "production":
                self._validate_production(config)
            
            logger.info("✅ Environment configuration is valid")
            return True
            
        except ValidationError as e:
            logger.error("❌ Environment configuration validation failed:")
            for error in e.errors():
                field = ".".join(str(x) for x in error["loc"])
                message = error["msg"]
                logger.error(f"  - {field}: {message}")
                self.errors.append(f"{field}: {message}")
            return False
    
    def _validate_production(self, config: EnvironmentConfig) -> None:
        """Additional validation for production environment."""
        # Check for required production variables
        if not config.sentry_dsn:
            self.warnings.append("SENTRY_DSN not set - error tracking disabled")
        
        if not config.redis_url:
            self.warnings.append("REDIS_URL not set - caching disabled")
        
        if config.database_url.startswith("sqlite:///"):
            self.errors.append("SQLite not recommended for production")
        
        # Log warnings
        for warning in self.warnings:
            logger.warning(f"⚠️  {warning}")


def main():
    """Run environment validation."""
    validator = EnvironmentValidator()
    
    if not validator.validate():
        logger.error("❌ Environment validation failed")
        sys.exit(1)
    
    if validator.warnings:
        logger.warning(f"⚠️  {len(validator.warnings)} warnings found")
    
    logger.info("🎉 Environment validation passed!")


if __name__ == "__main__":
    main()
```

---

## ✅ ACCEPTANCE CRITERIA

- [ ] All environment variables documented
- [ ] Validation script created and tested
- [ ] Environment-specific validation implemented
- [ ] Secrets strength validation working
- [ ] CI/CD integration for validation
- [ ] Documentation complete

---

## 🧪 TESTING

```python
# tests/test_environment_validation.py
"""Tests for environment validation."""
import pytest
from scripts.config.validate_environment import EnvironmentValidator, EnvironmentConfig


def test_valid_configuration(monkeypatch):
    """Test valid configuration."""
    monkeypatch.setenv("DATABASE_URL", "sqlite:///./test.db")
    monkeypatch.setenv("JWT_SECRET_KEY", "a" * 48)
    monkeypatch.setenv("ENVIRONMENT", "development")
    
    validator = EnvironmentValidator()
    assert validator.validate()


def test_weak_jwt_secret(monkeypatch):
    """Test weak JWT secret detection."""
    monkeypatch.setenv("DATABASE_URL", "sqlite:///./test.db")
    monkeypatch.setenv("JWT_SECRET_KEY", "weak-secret")
    monkeypatch.setenv("ENVIRONMENT", "development")
    
    validator = EnvironmentValidator()
    assert not validator.validate()
```

---

## 📝 NOTES

- Run validation on application startup
- Fail fast if configuration invalid
- Log all validation errors clearly
- Document all environment variables


