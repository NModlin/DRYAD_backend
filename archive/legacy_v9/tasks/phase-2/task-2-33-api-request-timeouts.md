# Task 2-33: API Request Timeouts

**Phase:** 2 - Performance & Production Readiness  
**Week:** 5 - Performance Optimization  
**Priority:** HIGH  
**Estimated Hours:** 2 hours

---

## 📋 OVERVIEW

Implement request timeout middleware to prevent long-running requests from consuming resources and ensure responsive API behavior.

---

## 🎯 OBJECTIVES

1. Implement request timeout middleware
2. Configure per-endpoint timeouts
3. Add timeout error handling
4. Implement timeout monitoring
5. Test timeout scenarios
6. Document timeout policies

---

## 📊 CURRENT STATE

**Existing:**
- No request timeouts
- Requests can run indefinitely
- No timeout configuration

**Gaps:**
- No timeout protection
- Resource exhaustion risk
- Poor user experience for slow requests

---

## 🔧 IMPLEMENTATION

### 1. Timeout Middleware

Create `app/middleware/timeout.py`:

```python
"""
Request Timeout Middleware

Enforces request timeouts to prevent resource exhaustion.
"""
from __future__ import annotations

import asyncio
import logging
from typing import Callable
from fastapi import Request, Response, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


class TimeoutMiddleware(BaseHTTPMiddleware):
    """Middleware for request timeout enforcement."""
    
    # Default timeout in seconds
    DEFAULT_TIMEOUT = 30
    
    # Per-endpoint timeout overrides
    ENDPOINT_TIMEOUTS = {
        "/api/v1/chat/completions": 120,  # 2 minutes for LLM
        "/api/v1/documents/process": 300,  # 5 minutes for processing
        "/api/v1/search/vector": 60,       # 1 minute for search
        "/api/v1/health/status": 5,        # 5 seconds for health
    }
    
    async def dispatch(
        self,
        request: Request,
        call_next: Callable
    ) -> Response:
        """Process request with timeout."""
        
        # Get timeout for this endpoint
        timeout = self._get_timeout(request.url.path)
        
        try:
            # Execute request with timeout
            response = await asyncio.wait_for(
                call_next(request),
                timeout=timeout
            )
            return response
            
        except asyncio.TimeoutError:
            logger.warning(
                f"Request timeout: {request.method} {request.url.path}",
                extra={
                    "method": request.method,
                    "path": request.url.path,
                    "timeout": timeout,
                    "request_id": getattr(request.state, "request_id", None)
                }
            )
            
            raise HTTPException(
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                detail={
                    "error": "Request Timeout",
                    "message": f"Request exceeded {timeout}s timeout",
                    "timeout": timeout
                }
            )
    
    def _get_timeout(self, path: str) -> float:
        """
        Get timeout for endpoint.
        
        Args:
            path: Request path
        
        Returns:
            Timeout in seconds
        """
        # Check for exact match
        if path in self.ENDPOINT_TIMEOUTS:
            return self.ENDPOINT_TIMEOUTS[path]
        
        # Check for prefix match
        for endpoint_path, timeout in self.ENDPOINT_TIMEOUTS.items():
            if path.startswith(endpoint_path):
                return timeout
        
        # Return default
        return self.DEFAULT_TIMEOUT
```

---

### 2. Timeout Configuration

Create `app/core/timeout_config.py`:

```python
"""
Timeout Configuration

Centralized timeout settings.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict


@dataclass
class TimeoutConfig:
    """Timeout configuration settings."""
    
    # Default request timeout
    default_timeout: float = 30.0
    
    # Per-endpoint timeouts
    endpoint_timeouts: Dict[str, float] = None
    
    # Database query timeout
    db_query_timeout: float = 30.0
    
    # External API timeout
    external_api_timeout: float = 10.0
    
    # LLM completion timeout
    llm_timeout: float = 120.0
    
    # File upload timeout
    upload_timeout: float = 300.0
    
    def __post_init__(self):
        """Initialize endpoint timeouts."""
        if self.endpoint_timeouts is None:
            self.endpoint_timeouts = {
                "/api/v1/chat/completions": self.llm_timeout,
                "/api/v1/documents/upload": self.upload_timeout,
                "/api/v1/documents/process": self.upload_timeout,
                "/api/v1/search/vector": 60.0,
                "/api/v1/health/status": 5.0,
                "/api/v1/health/ready": 10.0,
            }


# Global timeout configuration
timeout_config = TimeoutConfig()
```

---

### 3. Database Query Timeout

Update `app/database/database.py`:

```python
"""Add query timeout support."""
from sqlalchemy import event
from app.core.timeout_config import timeout_config


def set_query_timeout(dbapi_conn, connection_record):
    """Set query timeout for connection."""
    cursor = dbapi_conn.cursor()
    # For SQLite
    cursor.execute(f"PRAGMA busy_timeout = {int(timeout_config.db_query_timeout * 1000)}")
    # For PostgreSQL, use statement_timeout
    # cursor.execute(f"SET statement_timeout = {int(timeout_config.db_query_timeout * 1000)}")
    cursor.close()


# Register event listener
event.listen(engine.sync_engine, "connect", set_query_timeout)
```

---

### 4. External API Timeout

Create `app/core/http_client.py`:

```python
"""
HTTP Client with Timeout

Configured HTTP client for external APIs.
"""
from __future__ import annotations

import httpx
from app.core.timeout_config import timeout_config


class HTTPClient:
    """HTTP client with timeout configuration."""
    
    def __init__(self):
        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(
                connect=5.0,
                read=timeout_config.external_api_timeout,
                write=5.0,
                pool=5.0
            ),
            limits=httpx.Limits(
                max_keepalive_connections=20,
                max_connections=100
            )
        )
    
    async def get(self, url: str, **kwargs):
        """GET request with timeout."""
        return await self.client.get(url, **kwargs)
    
    async def post(self, url: str, **kwargs):
        """POST request with timeout."""
        return await self.client.post(url, **kwargs)
    
    async def close(self):
        """Close client."""
        await self.client.aclose()


# Global HTTP client
http_client = HTTPClient()
```

---

### 5. Timeout Monitoring

Create `app/core/timeout_monitor.py`:

```python
"""
Timeout Monitoring

Track and report timeout metrics.
"""
from __future__ import annotations

import logging
from collections import defaultdict
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class TimeoutMonitor:
    """Monitor request timeouts."""
    
    def __init__(self):
        self.timeout_counts: dict[str, int] = defaultdict(int)
        self.last_reset = datetime.now()
    
    def record_timeout(self, endpoint: str, timeout: float):
        """
        Record timeout event.
        
        Args:
            endpoint: Endpoint path
            timeout: Timeout duration
        """
        self.timeout_counts[endpoint] += 1
        
        logger.warning(
            f"Timeout recorded for {endpoint}",
            extra={
                "endpoint": endpoint,
                "timeout": timeout,
                "total_timeouts": self.timeout_counts[endpoint]
            }
        )
    
    def get_timeout_stats(self) -> dict[str, int]:
        """
        Get timeout statistics.
        
        Returns:
            Timeout counts by endpoint
        """
        return dict(self.timeout_counts)
    
    def reset_stats(self):
        """Reset timeout statistics."""
        self.timeout_counts.clear()
        self.last_reset = datetime.now()


# Global timeout monitor
timeout_monitor = TimeoutMonitor()
```

---

### 6. Timeout Metrics Endpoint

Create `app/api/v1/endpoints/metrics.py`:

```python
"""
Metrics Endpoints

Expose timeout metrics.
"""
from __future__ import annotations

from fastapi import APIRouter
from app.core.timeout_monitor import timeout_monitor

router = APIRouter()


@router.get("/metrics/timeouts")
async def get_timeout_metrics():
    """Get timeout statistics."""
    return {
        "timeout_counts": timeout_monitor.get_timeout_stats(),
        "last_reset": timeout_monitor.last_reset.isoformat()
    }
```

---

## ✅ ACCEPTANCE CRITERIA

- [ ] Timeout middleware implemented
- [ ] Per-endpoint timeouts configured
- [ ] Database query timeouts set
- [ ] External API timeouts configured
- [ ] Timeout monitoring working
- [ ] Timeout errors handled gracefully
- [ ] Documentation complete

---

## 🧪 TESTING

```python
# tests/test_timeouts.py
"""Tests for request timeouts."""
import pytest
import asyncio
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_request_timeout():
    """Test request timeout enforcement."""
    # Create slow endpoint for testing
    @app.get("/test/slow")
    async def slow_endpoint():
        await asyncio.sleep(60)  # Sleep longer than timeout
        return {"status": "ok"}
    
    response = client.get("/test/slow")
    assert response.status_code == 504
    assert "timeout" in response.json()["detail"].lower()


def test_fast_request_no_timeout():
    """Test fast request completes normally."""
    response = client.get("/api/v1/health/status")
    assert response.status_code == 200
```

---

## 📝 NOTES

- Set timeouts based on expected response times
- Monitor timeout rates in production
- Adjust timeouts based on actual usage
- Use longer timeouts for LLM operations
- Implement retry logic for timeout errors


