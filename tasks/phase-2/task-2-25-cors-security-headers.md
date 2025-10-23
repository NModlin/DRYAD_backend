# Task 2-25: CORS & Security Headers Configuration

**Phase:** 2 - Performance & Production Readiness  
**Week:** 7 - Production Infrastructure  
**Priority:** HIGH  
**Estimated Hours:** 2 hours

---

## 📋 OVERVIEW

Configure CORS (Cross-Origin Resource Sharing) and security headers for production deployment to prevent security vulnerabilities and enable proper cross-origin requests.

---

## 🎯 OBJECTIVES

1. Configure CORS middleware for production
2. Add security headers (CSP, HSTS, X-Frame-Options, etc.)
3. Implement environment-specific CORS policies
4. Add CORS preflight caching
5. Test CORS configuration
6. Document CORS policies

---

## 📊 CURRENT STATE

**Existing:**
- Basic CORS middleware in `app/main.py`
- Allows all origins in development

**Gaps:**
- No production CORS configuration
- No security headers
- No CORS preflight caching
- No environment-specific policies

---

## 🔧 IMPLEMENTATION

### 1. CORS Configuration

Create `app/core/cors_config.py`:

```python
"""
CORS Configuration

Environment-specific CORS policies.
"""
from __future__ import annotations

import os
from typing import List


class CORSConfig:
    """CORS configuration based on environment."""
    
    def __init__(self):
        self.environment = os.getenv("ENVIRONMENT", "development")
    
    def get_allowed_origins(self) -> List[str]:
        """Get allowed origins based on environment."""
        if self.environment == "production":
            # Production: Only allow specific domains
            return [
                "https://dryad.ai",
                "https://www.dryad.ai",
                "https://app.dryad.ai",
                # Add your production domains
            ]
        elif self.environment == "staging":
            # Staging: Allow staging domains
            return [
                "https://staging.dryad.ai",
                "https://dev.dryad.ai",
            ]
        else:
            # Development: Allow localhost
            return [
                "http://localhost:3000",
                "http://localhost:8000",
                "http://127.0.0.1:3000",
                "http://127.0.0.1:8000",
            ]
    
    def get_allowed_methods(self) -> List[str]:
        """Get allowed HTTP methods."""
        return ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"]
    
    def get_allowed_headers(self) -> List[str]:
        """Get allowed headers."""
        return [
            "Accept",
            "Accept-Language",
            "Content-Type",
            "Authorization",
            "X-Request-ID",
            "X-API-Key",
        ]
    
    def get_exposed_headers(self) -> List[str]:
        """Get headers exposed to browser."""
        return [
            "X-Request-ID",
            "X-API-Version",
            "X-RateLimit-Limit",
            "X-RateLimit-Remaining",
            "X-RateLimit-Reset",
        ]
    
    def allow_credentials(self) -> bool:
        """Whether to allow credentials."""
        return True
    
    def get_max_age(self) -> int:
        """Get preflight cache duration in seconds."""
        if self.environment == "production":
            return 3600  # 1 hour
        return 600  # 10 minutes


cors_config = CORSConfig()
```

---

### 2. Security Headers Middleware

Create `app/middleware/security_headers.py`:

```python
"""
Security Headers Middleware

Adds security headers to all responses.
"""
from __future__ import annotations

import os
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Middleware for adding security headers."""
    
    def __init__(self, app, environment: str = None):
        super().__init__(app)
        self.environment = environment or os.getenv("ENVIRONMENT", "development")
    
    async def dispatch(
        self,
        request: Request,
        call_next: Callable
    ) -> Response:
        """Add security headers to response."""
        response = await call_next(request)
        
        # Content Security Policy
        if self.environment == "production":
            response.headers["Content-Security-Policy"] = (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
                "style-src 'self' 'unsafe-inline'; "
                "img-src 'self' data: https:; "
                "font-src 'self' data:; "
                "connect-src 'self' https://api.dryad.ai; "
                "frame-ancestors 'none';"
            )
        
        # HTTP Strict Transport Security (HSTS)
        if self.environment == "production":
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains; preload"
            )
        
        # X-Frame-Options
        response.headers["X-Frame-Options"] = "DENY"
        
        # X-Content-Type-Options
        response.headers["X-Content-Type-Options"] = "nosniff"
        
        # X-XSS-Protection
        response.headers["X-XSS-Protection"] = "1; mode=block"
        
        # Referrer-Policy
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        # Permissions-Policy
        response.headers["Permissions-Policy"] = (
            "geolocation=(), microphone=(), camera=()"
        )
        
        return response
```

---

### 3. Update Main Application

Update `app/main.py`:

```python
"""Main application with CORS and security headers."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.cors_config import cors_config
from app.middleware.security_headers import SecurityHeadersMiddleware

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_config.get_allowed_origins(),
    allow_credentials=cors_config.allow_credentials(),
    allow_methods=cors_config.get_allowed_methods(),
    allow_headers=cors_config.get_allowed_headers(),
    expose_headers=cors_config.get_exposed_headers(),
    max_age=cors_config.get_max_age(),
)

# Add security headers middleware
app.add_middleware(SecurityHeadersMiddleware)
```

---

## ✅ ACCEPTANCE CRITERIA

- [ ] CORS configured for all environments
- [ ] Security headers added
- [ ] Preflight caching configured
- [ ] Environment-specific policies working
- [ ] CORS tests passing
- [ ] Documentation complete

---

## 🧪 TESTING

```python
# tests/test_cors_security.py
"""Tests for CORS and security headers."""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_cors_headers_present():
    """Test CORS headers are present."""
    response = client.options(
        "/api/v1/health/status",
        headers={"Origin": "http://localhost:3000"}
    )
    assert "access-control-allow-origin" in response.headers


def test_security_headers_present():
    """Test security headers are present."""
    response = client.get("/api/v1/health/status")
    assert "x-frame-options" in response.headers
    assert "x-content-type-options" in response.headers
    assert response.headers["x-frame-options"] == "DENY"


def test_preflight_cache():
    """Test preflight cache header."""
    response = client.options(
        "/api/v1/health/status",
        headers={"Origin": "http://localhost:3000"}
    )
    assert "access-control-max-age" in response.headers
```

---

## 📝 NOTES

- Use strict CORS in production
- Enable HSTS in production
- Test with actual frontend
- Document allowed origins


