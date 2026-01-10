# Task 2-34: CORS Preflight Caching

**Phase:** 2 - Performance & Production Readiness  
**Week:** 5 - Performance Optimization  
**Priority:** MEDIUM  
**Estimated Hours:** 1 hour

---

## 📋 OVERVIEW

Optimize CORS preflight request handling by implementing proper caching headers to reduce unnecessary OPTIONS requests and improve API performance.

---

## 🎯 OBJECTIVES

1. Configure CORS preflight caching
2. Set appropriate max-age headers
3. Test preflight caching behavior
4. Monitor preflight request reduction
5. Document CORS caching policy

---

## 📊 CURRENT STATE

**Existing:**
- Basic CORS middleware configured
- No preflight caching

**Gaps:**
- Every cross-origin request triggers preflight
- Unnecessary OPTIONS requests
- Performance overhead

---

## 🔧 IMPLEMENTATION

### 1. Enhanced CORS Configuration

Update `app/core/cors_config.py`:

```python
"""
CORS Configuration with Preflight Caching

Optimized CORS settings for production.
"""
from __future__ import annotations

import os


class CORSConfig:
    """CORS configuration with caching."""
    
    def __init__(self):
        self.environment = os.getenv("ENVIRONMENT", "development")
    
    def get_max_age(self) -> int:
        """
        Get preflight cache duration in seconds.
        
        Returns:
            Cache duration
        """
        if self.environment == "production":
            # Cache for 24 hours in production
            return 86400
        elif self.environment == "staging":
            # Cache for 1 hour in staging
            return 3600
        else:
            # Cache for 10 minutes in development
            return 600
    
    def get_allowed_origins(self) -> list[str]:
        """Get allowed origins."""
        if self.environment == "production":
            return [
                "https://dryad.ai",
                "https://www.dryad.ai",
                "https://app.dryad.ai",
            ]
        return ["http://localhost:3000", "http://localhost:8000"]
    
    def get_allowed_methods(self) -> list[str]:
        """Get allowed HTTP methods."""
        return ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"]
    
    def get_allowed_headers(self) -> list[str]:
        """Get allowed headers."""
        return [
            "Accept",
            "Accept-Language",
            "Content-Type",
            "Authorization",
            "X-Request-ID",
            "X-API-Key",
        ]
    
    def get_exposed_headers(self) -> list[str]:
        """Get headers exposed to browser."""
        return [
            "X-Request-ID",
            "X-API-Version",
            "X-RateLimit-Limit",
            "X-RateLimit-Remaining",
            "X-RateLimit-Reset",
        ]


cors_config = CORSConfig()
```

---

### 2. Update Main Application

Update `app/main.py`:

```python
"""
FastAPI Application with Optimized CORS

Includes preflight caching.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.cors_config import cors_config

app = FastAPI()

# Add CORS middleware with caching
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_config.get_allowed_origins(),
    allow_credentials=True,
    allow_methods=cors_config.get_allowed_methods(),
    allow_headers=cors_config.get_allowed_headers(),
    expose_headers=cors_config.get_exposed_headers(),
    max_age=cors_config.get_max_age(),  # Preflight cache duration
)
```

---

### 3. Nginx CORS Configuration (Alternative)

Create `docker/nginx/cors.conf`:

```nginx
# CORS Configuration with Preflight Caching

# Map to determine if origin is allowed
map $http_origin $cors_origin {
    default "";
    "https://dryad.ai" $http_origin;
    "https://www.dryad.ai" $http_origin;
    "https://app.dryad.ai" $http_origin;
}

# Add CORS headers
add_header 'Access-Control-Allow-Origin' $cors_origin always;
add_header 'Access-Control-Allow-Credentials' 'true' always;
add_header 'Access-Control-Allow-Methods' 'GET, POST, PUT, PATCH, DELETE, OPTIONS' always;
add_header 'Access-Control-Allow-Headers' 'Accept,Accept-Language,Content-Type,Authorization,X-Request-ID,X-API-Key' always;
add_header 'Access-Control-Expose-Headers' 'X-Request-ID,X-API-Version,X-RateLimit-Limit,X-RateLimit-Remaining,X-RateLimit-Reset' always;

# Preflight cache - 24 hours
add_header 'Access-Control-Max-Age' 86400 always;

# Handle OPTIONS requests
if ($request_method = 'OPTIONS') {
    add_header 'Access-Control-Allow-Origin' $cors_origin;
    add_header 'Access-Control-Allow-Credentials' 'true';
    add_header 'Access-Control-Allow-Methods' 'GET, POST, PUT, PATCH, DELETE, OPTIONS';
    add_header 'Access-Control-Allow-Headers' 'Accept,Accept-Language,Content-Type,Authorization,X-Request-ID,X-API-Key';
    add_header 'Access-Control-Max-Age' 86400;
    add_header 'Content-Type' 'text/plain; charset=utf-8';
    add_header 'Content-Length' 0;
    return 204;
}
```

---

### 4. CORS Monitoring

Create `app/core/cors_monitor.py`:

```python
"""
CORS Request Monitoring

Track CORS preflight requests.
"""
from __future__ import annotations

import logging
from collections import defaultdict

logger = logging.getLogger(__name__)


class CORSMonitor:
    """Monitor CORS preflight requests."""
    
    def __init__(self):
        self.preflight_counts: dict[str, int] = defaultdict(int)
        self.origin_counts: dict[str, int] = defaultdict(int)
    
    def record_preflight(self, origin: str, path: str):
        """
        Record preflight request.
        
        Args:
            origin: Request origin
            path: Request path
        """
        self.preflight_counts[path] += 1
        self.origin_counts[origin] += 1
    
    def get_stats(self) -> dict:
        """Get CORS statistics."""
        return {
            "preflight_by_path": dict(self.preflight_counts),
            "requests_by_origin": dict(self.origin_counts),
            "total_preflights": sum(self.preflight_counts.values())
        }


cors_monitor = CORSMonitor()
```

---

### 5. Documentation

Create `docs/api/CORS_POLICY.md`:

```markdown
# CORS Policy

## Preflight Caching

### Cache Duration
- **Production:** 24 hours (86400 seconds)
- **Staging:** 1 hour (3600 seconds)
- **Development:** 10 minutes (600 seconds)

### How It Works

1. **First Request:** Browser sends OPTIONS preflight request
2. **Server Response:** Includes `Access-Control-Max-Age: 86400`
3. **Subsequent Requests:** Browser uses cached preflight for 24 hours
4. **Result:** Reduced OPTIONS requests, improved performance

### Benefits

- **Reduced Latency:** Fewer OPTIONS requests
- **Lower Server Load:** Less processing overhead
- **Better UX:** Faster API responses

### Monitoring

Check preflight request counts:
```bash
curl http://localhost:8000/api/v1/metrics/cors
```

### Testing

Test preflight caching:
```bash
# First request - triggers preflight
curl -X OPTIONS http://localhost:8000/api/v1/users \
  -H "Origin: https://dryad.ai" \
  -H "Access-Control-Request-Method: POST" \
  -v

# Check for Access-Control-Max-Age header
```
```

---

## ✅ ACCEPTANCE CRITERIA

- [ ] CORS max-age configured
- [ ] Preflight caching working
- [ ] Cache duration appropriate for environment
- [ ] CORS monitoring implemented
- [ ] Documentation complete
- [ ] Preflight reduction verified

---

## 🧪 TESTING

```python
# tests/test_cors_caching.py
"""Tests for CORS preflight caching."""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_preflight_cache_header():
    """Test preflight response includes max-age."""
    response = client.options(
        "/api/v1/users",
        headers={
            "Origin": "https://dryad.ai",
            "Access-Control-Request-Method": "POST"
        }
    )
    
    assert "access-control-max-age" in response.headers
    max_age = int(response.headers["access-control-max-age"])
    assert max_age > 0


def test_cors_headers_present():
    """Test CORS headers in preflight response."""
    response = client.options(
        "/api/v1/users",
        headers={
            "Origin": "https://dryad.ai",
            "Access-Control-Request-Method": "POST"
        }
    )
    
    assert "access-control-allow-origin" in response.headers
    assert "access-control-allow-methods" in response.headers
    assert "access-control-allow-headers" in response.headers
```

---

## 📝 NOTES

- Use 24-hour cache in production
- Monitor preflight request reduction
- Adjust cache duration based on deployment frequency
- Clear browser cache when testing
- Document cache policy for frontend team


