# Task 5-02: Archivist (Short-Term Memory) Implementation

**Phase:** 5 - Cognitive Architecture & Self-Improvement  
**Week:** 21  
**Estimated Hours:** 12 hours  
**Priority:** HIGH  
**Dependencies:** Task 5-01 (Memory Coordinator)

---

## 🎯 OBJECTIVE

Implement Archivist agent for managing short-term memory using Redis. Handles recent context, active workflows, and temporary data with TTL-based expiration.

---

## 📋 REQUIREMENTS

### Functional Requirements
- Store/retrieve short-term memory in Redis
- TTL-based automatic expiration
- Key-value and hash operations
- Memory prioritization
- Automatic archival triggers

### Technical Requirements
- Redis integration with async client
- TTL management
- Memory usage monitoring
- Integration with Memory Coordinator

### Performance Requirements
- Store operation: <10ms
- Retrieve operation: <5ms
- Memory capacity: 10GB

---

## 🔧 IMPLEMENTATION

**File:** `app/agents/archivist.py`

```python
"""
Archivist - Short-Term Memory Specialist
Manages recent context and temporary data in Redis.
"""

from __future__ import annotations

import json
from datetime import timedelta
from typing import Any

import redis.asyncio as redis
from pydantic import BaseModel
from structlog import get_logger

logger = get_logger(__name__)


class ArchivistAgent:
    """
    Archivist Agent - Short-Term Memory (Redis)
    
    Manages recent context with automatic expiration.
    """
    
    DEFAULT_TTL = timedelta(hours=24)
    
    def __init__(self, redis_url: str = "redis://localhost:6379") -> None:
        self.redis_client = redis.from_url(redis_url)
        self.logger = logger.bind(agent="archivist")
    
    async def store(
        self,
        key: str,
        value: dict[str, Any],
        ttl: timedelta | None = None,
    ) -> bool:
        """Store value in short-term memory."""
        ttl = ttl or self.DEFAULT_TTL
        
        try:
            await self.redis_client.setex(
                key,
                int(ttl.total_seconds()),
                json.dumps(value),
            )
            
            self.logger.info("memory_stored", key=key, ttl_seconds=ttl.total_seconds())
            return True
            
        except Exception as e:
            self.logger.error("store_failed", key=key, error=str(e))
            return False
    
    async def retrieve(self, key: str) -> dict[str, Any] | None:
        """Retrieve value from short-term memory."""
        try:
            value = await self.redis_client.get(key)
            
            if value is None:
                return None
            
            return json.loads(value)
            
        except Exception as e:
            self.logger.error("retrieve_failed", key=key, error=str(e))
            return None
    
    async def delete(self, key: str) -> bool:
        """Delete value from short-term memory."""
        try:
            await self.redis_client.delete(key)
            self.logger.info("memory_deleted", key=key)
            return True
            
        except Exception as e:
            self.logger.error("delete_failed", key=key, error=str(e))
            return False
```

---

## ✅ DEFINITION OF DONE

- [ ] Archivist agent implemented
- [ ] Redis integration working
- [ ] TTL management functional
- [ ] Tests passing (>85% coverage)

---

## 📊 SUCCESS METRICS

- Store operation: <10ms
- Retrieve operation: <5ms
- Test coverage: >85%

---

**Estimated Completion:** 12 hours  
**Status:** NOT STARTED

