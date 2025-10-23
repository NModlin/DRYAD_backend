# Task 2-44: API Rate Limiting Per-Endpoint

**Phase:** 2 - Performance & Production Readiness  
**Week:** 5 - Performance Optimization  
**Priority:** HIGH  
**Estimated Hours:** 4 hours

---

## 📋 OVERVIEW

Implement granular per-endpoint rate limiting with Redis backend to prevent abuse, ensure fair usage, and protect API resources.

---

## 🎯 OBJECTIVES

1. Implement Redis-based rate limiting
2. Configure per-endpoint limits
3. Add rate limit headers
4. Implement user-based limits
5. Create rate limit monitoring
6. Test rate limiting scenarios

---

## 📊 CURRENT STATE

**Existing:**
- Basic rate limiting middleware
- Global rate limits only

**Gaps:**
- No per-endpoint limits
- No Redis backend
- No user-specific limits
- No rate limit monitoring

---

## 🔧 IMPLEMENTATION

### 1. Redis Rate Limiter

Create `app/core/rate_limiter.py`:

```python
"""
Redis-Based Rate Limiter

Per-endpoint rate limiting with Redis backend.
"""
from __future__ import annotations

import time
import logging
from typing import Optional
from redis import asyncio as aioredis
from fastapi import Request, HTTPException, status

logger = logging.getLogger(__name__)


class RateLimiter:
    """Redis-based rate limiter."""
    
    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis = aioredis.from_url(redis_url, decode_responses=True)
    
    async def check_rate_limit(
        self,
        key: str,
        limit: int,
        window: int
    ) -> tuple[bool, dict]:
        """
        Check if request is within rate limit.
        
        Args:
            key: Rate limit key (e.g., "user:123:endpoint:/api/chat")
            limit: Maximum requests allowed
            window: Time window in seconds
        
        Returns:
            Tuple of (allowed, info)
        """
        now = int(time.time())
        window_start = now - window
        
        # Use sorted set to track requests
        pipe = self.redis.pipeline()
        
        # Remove old requests
        pipe.zremrangebyscore(key, 0, window_start)
        
        # Count requests in window
        pipe.zcard(key)
        
        # Add current request
        pipe.zadd(key, {str(now): now})
        
        # Set expiry
        pipe.expire(key, window)
        
        results = await pipe.execute()
        request_count = results[1]
        
        # Check if limit exceeded
        allowed = request_count < limit
        
        # Calculate reset time
        reset_time = now + window
        
        info = {
            "limit": limit,
            "remaining": max(0, limit - request_count - 1),
            "reset": reset_time,
            "retry_after": window if not allowed else 0
        }
        
        return allowed, info
    
    async def get_rate_limit_key(
        self,
        request: Request,
        endpoint: str
    ) -> str:
        """
        Generate rate limit key.
        
        Args:
            request: FastAPI request
            endpoint: Endpoint path
        
        Returns:
            Rate limit key
        """
        # Get user ID from request state (set by auth middleware)
        user_id = getattr(request.state, "user_id", None)
        
        if user_id:
            return f"rate_limit:user:{user_id}:endpoint:{endpoint}"
        else:
            # Use IP address for anonymous users
            client_ip = request.client.host
            return f"rate_limit:ip:{client_ip}:endpoint:{endpoint}"


# Global rate limiter instance
rate_limiter = RateLimiter()
```

---

### 2. Rate Limit Decorator

Create `app/core/rate_limit_decorator.py`:

```python
"""
Rate Limit Decorator

Decorator for applying rate limits to endpoints.
"""
from __future__ import annotations

from functools import wraps
from fastapi import Request, HTTPException, status, Response
from app.core.rate_limiter import rate_limiter


def rate_limit(limit: int = 100, window: int = 60):
    """
    Rate limit decorator.
    
    Args:
        limit: Maximum requests allowed
        window: Time window in seconds
    
    Example:
        @router.get("/api/chat")
        @rate_limit(limit=10, window=60)
        async def chat_endpoint():
            ...
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract request from args
            request = None
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                    break
            
            if not request:
                # No request found, skip rate limiting
                return await func(*args, **kwargs)
            
            # Get rate limit key
            endpoint = request.url.path
            key = await rate_limiter.get_rate_limit_key(request, endpoint)
            
            # Check rate limit
            allowed, info = await rate_limiter.check_rate_limit(
                key, limit, window
            )
            
            # Add rate limit headers to response
            response = await func(*args, **kwargs)
            if isinstance(response, Response):
                response.headers["X-RateLimit-Limit"] = str(info["limit"])
                response.headers["X-RateLimit-Remaining"] = str(info["remaining"])
                response.headers["X-RateLimit-Reset"] = str(info["reset"])
            
            if not allowed:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail={
                        "error": "Rate limit exceeded",
                        "limit": info["limit"],
                        "window": window,
                        "retry_after": info["retry_after"]
                    },
                    headers={
                        "Retry-After": str(info["retry_after"]),
                        "X-RateLimit-Limit": str(info["limit"]),
                        "X-RateLimit-Remaining": "0",
                        "X-RateLimit-Reset": str(info["reset"])
                    }
                )
            
            return response
        
        return wrapper
    return decorator
```

---

### 3. Per-Endpoint Configuration

Create `app/core/rate_limit_config.py`:

```python
"""
Rate Limit Configuration

Per-endpoint rate limit settings.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class EndpointRateLimit:
    """Rate limit configuration for endpoint."""
    limit: int
    window: int  # seconds


class RateLimitConfig:
    """Rate limit configuration."""
    
    # Default limits
    DEFAULT_LIMIT = 100
    DEFAULT_WINDOW = 60
    
    # Per-endpoint limits
    ENDPOINT_LIMITS = {
        # Chat endpoints (expensive)
        "/api/v1/chat/completions": EndpointRateLimit(10, 60),
        "/api/v1/chat/stream": EndpointRateLimit(10, 60),
        
        # Search endpoints
        "/api/v1/search/vector": EndpointRateLimit(30, 60),
        "/api/v1/search/text": EndpointRateLimit(50, 60),
        
        # Document endpoints
        "/api/v1/documents/upload": EndpointRateLimit(10, 60),
        "/api/v1/documents/process": EndpointRateLimit(5, 60),
        
        # User endpoints
        "/api/v1/users/register": EndpointRateLimit(5, 3600),
        "/api/v1/users/login": EndpointRateLimit(10, 300),
        
        # General API endpoints
        "/api/v1/conversations": EndpointRateLimit(100, 60),
        "/api/v1/messages": EndpointRateLimit(100, 60),
    }
    
    @classmethod
    def get_limit(cls, endpoint: str) -> EndpointRateLimit:
        """
        Get rate limit for endpoint.
        
        Args:
            endpoint: Endpoint path
        
        Returns:
            Rate limit configuration
        """
        return cls.ENDPOINT_LIMITS.get(
            endpoint,
            EndpointRateLimit(cls.DEFAULT_LIMIT, cls.DEFAULT_WINDOW)
        )


rate_limit_config = RateLimitConfig()
```

---

### 4. Apply Rate Limits to Endpoints

Update `app/api/v1/endpoints/chat.py`:

```python
"""
Chat Endpoints with Rate Limiting
"""
from fastapi import APIRouter, Request
from app.core.rate_limit_decorator import rate_limit

router = APIRouter()


@router.post("/chat/completions")
@rate_limit(limit=10, window=60)
async def chat_completion(request: Request, ...):
    """Chat completion endpoint with rate limiting."""
    # Implementation
    pass


@router.post("/chat/stream")
@rate_limit(limit=10, window=60)
async def chat_stream(request: Request, ...):
    """Streaming chat endpoint with rate limiting."""
    # Implementation
    pass
```

---

### 5. Rate Limit Monitoring

Create `app/api/v1/endpoints/rate_limits.py`:

```python
"""
Rate Limit Monitoring Endpoints
"""
from fastapi import APIRouter, Request
from app.core.rate_limiter import rate_limiter

router = APIRouter()


@router.get("/rate-limits/status")
async def get_rate_limit_status(request: Request):
    """Get current rate limit status for user."""
    user_id = getattr(request.state, "user_id", None)
    
    if not user_id:
        return {"error": "Not authenticated"}
    
    # Check limits for common endpoints
    endpoints = [
        "/api/v1/chat/completions",
        "/api/v1/search/vector",
        "/api/v1/documents/upload"
    ]
    
    status = {}
    for endpoint in endpoints:
        key = f"rate_limit:user:{user_id}:endpoint:{endpoint}"
        
        # Get current count
        count = await rate_limiter.redis.zcard(key)
        
        from app.core.rate_limit_config import rate_limit_config
        limit_config = rate_limit_config.get_limit(endpoint)
        
        status[endpoint] = {
            "limit": limit_config.limit,
            "used": count,
            "remaining": max(0, limit_config.limit - count),
            "window": limit_config.window
        }
    
    return status
```

---

## ✅ ACCEPTANCE CRITERIA

- [ ] Redis rate limiter implemented
- [ ] Per-endpoint limits configured
- [ ] Rate limit decorator working
- [ ] Rate limit headers added
- [ ] User-based limits working
- [ ] Monitoring endpoints working
- [ ] Rate limit testing complete

---

## 🧪 TESTING

```python
# tests/test_rate_limiting.py
"""Tests for rate limiting."""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_rate_limit_enforced():
    """Test rate limit is enforced."""
    # Make requests up to limit
    for i in range(10):
        response = client.post("/api/v1/chat/completions", json={...})
        assert response.status_code == 200
    
    # Next request should be rate limited
    response = client.post("/api/v1/chat/completions", json={...})
    assert response.status_code == 429
    assert "Retry-After" in response.headers


def test_rate_limit_headers():
    """Test rate limit headers are present."""
    response = client.get("/api/v1/conversations")
    assert "X-RateLimit-Limit" in response.headers
    assert "X-RateLimit-Remaining" in response.headers
    assert "X-RateLimit-Reset" in response.headers
```

---

## 📝 NOTES

- Use Redis for distributed rate limiting
- Set appropriate limits per endpoint
- Monitor rate limit violations
- Provide clear error messages
- Consider premium tier with higher limits


