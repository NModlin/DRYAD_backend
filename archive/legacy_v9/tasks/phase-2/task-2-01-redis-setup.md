# Task 2-01: Redis Setup and Integration

**Phase:** 2 - Performance & Production Readiness  
**Week:** 5  
**Estimated Hours:** 4 hours  
**Priority:** HIGH  
**Dependencies:** None

---

## 🎯 OBJECTIVE

Set up Redis for caching, session management, and rate limiting to improve application performance.

---

## 📋 REQUIREMENTS

### Functional Requirements
- Redis installation and configuration
- Connection pooling
- Cache implementation
- Session storage
- Rate limit storage

### Technical Requirements
- redis-py async client
- Connection pool management
- Serialization/deserialization
- TTL configuration

### Performance Requirements
- Cache hit rate: >80%
- Redis response time: <5ms
- Connection pool: 10-50 connections

---

## 🔧 IMPLEMENTATION

**File:** `app/core/redis_client.py`

```python
"""
Redis Client Configuration
"""

from __future__ import annotations

import json
from typing import Any

import redis.asyncio as redis
from structlog import get_logger

logger = get_logger(__name__)


class RedisClient:
    """Async Redis client with connection pooling."""
    
    def __init__(self, url: str = "redis://localhost:6379"):
        self.pool = redis.ConnectionPool.from_url(
            url,
            max_connections=50,
            decode_responses=True,
        )
        self.client = redis.Redis(connection_pool=self.pool)
    
    async def get(self, key: str) -> Any | None:
        """Get value from cache."""
        value = await self.client.get(key)
        if value:
            return json.loads(value)
        return None
    
    async def set(
        self,
        key: str,
        value: Any,
        ttl: int = 3600,
    ) -> bool:
        """Set value in cache with TTL."""
        serialized = json.dumps(value)
        return await self.client.setex(key, ttl, serialized)
    
    async def delete(self, key: str) -> bool:
        """Delete key from cache."""
        return await self.client.delete(key) > 0
    
    async def close(self) -> None:
        """Close Redis connection."""
        await self.client.close()
        await self.pool.disconnect()


# Global Redis client
redis_client = RedisClient()
```

**File:** `app/services/cache_service.py`

```python
"""Cache Service"""

from __future__ import annotations

from typing import Any, Callable
from functools import wraps

from app.core.redis_client import redis_client


def cached(ttl: int = 3600, key_prefix: str = ""):
    """Cache decorator for async functions."""
    
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = f"{key_prefix}:{func.__name__}:{args}:{kwargs}"
            
            # Try cache
            cached_value = await redis_client.get(cache_key)
            if cached_value is not None:
                return cached_value
            
            # Execute function
            result = await func(*args, **kwargs)
            
            # Store in cache
            await redis_client.set(cache_key, result, ttl)
            
            return result
        
        return wrapper
    
    return decorator
```

---

## ✅ DEFINITION OF DONE

- [ ] Redis installed and configured
- [ ] Connection pooling working
- [ ] Cache service implemented
- [ ] Tests passing
- [ ] Documentation complete

---

## 📊 SUCCESS METRICS

- Cache hit rate: >80%
- Redis latency: <5ms
- Connection pool stable

---

**Estimated Completion:** 4 hours  
**Status:** NOT STARTED

