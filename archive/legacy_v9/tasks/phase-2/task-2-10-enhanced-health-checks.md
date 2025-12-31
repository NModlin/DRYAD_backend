# Task 2-10: Enhanced Health Checks (Liveness & Readiness)

**Phase:** 2 - Performance & Production Readiness  
**Week:** 6 - Monitoring & Observability  
**Priority:** CRITICAL  
**Estimated Hours:** 4 hours

---

## 📋 OVERVIEW

Implement comprehensive health check endpoints with liveness and readiness probes, dependency health checks, and detailed health status for proper Kubernetes/orchestration management.

---

## 🎯 OBJECTIVES

1. Implement liveness probe (`/health/live`)
2. Implement readiness probe (`/health/ready`)
3. Add dependency health checks (DB, Redis, etc.)
4. Add detailed health status endpoint
5. Test health check reliability
6. Configure Kubernetes probes

---

## 📊 CURRENT STATE

**Existing:**
- Basic health endpoint at `/api/v1/health/status`
- No liveness/readiness distinction
- No dependency checks

**Gaps:**
- No liveness probe
- No readiness probe
- No detailed health status
- Missing dependency health checks

---

## 🔧 IMPLEMENTATION

### 1. Health Check Models

Create `app/core/health_checks.py`:

```python
"""
Health Check System

Implements liveness and readiness probes with dependency checks.
"""
from __future__ import annotations

import logging
from datetime import datetime
from enum import Enum
from typing import Any
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class HealthStatus(str, Enum):
    """Health status values."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


class DependencyHealth(BaseModel):
    """Health status of a dependency."""
    name: str
    status: HealthStatus
    response_time_ms: float | None = None
    error: str | None = None
    details: dict[str, Any] | None = None


class LivenessResponse(BaseModel):
    """Liveness probe response."""
    status: HealthStatus
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ReadinessResponse(BaseModel):
    """Readiness probe response."""
    status: HealthStatus
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    dependencies: list[DependencyHealth]


class DetailedHealthResponse(BaseModel):
    """Detailed health status response."""
    status: HealthStatus
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    version: str
    uptime_seconds: float
    dependencies: list[DependencyHealth]
    system_info: dict[str, Any]


class HealthChecker:
    """Performs health checks on dependencies."""
    
    def __init__(self):
        self.start_time = datetime.utcnow()
    
    async def check_liveness(self) -> LivenessResponse:
        """
        Check if application is alive.
        
        Liveness probe should only check if the application process is running.
        It should NOT check dependencies.
        """
        return LivenessResponse(status=HealthStatus.HEALTHY)
    
    async def check_readiness(self) -> ReadinessResponse:
        """
        Check if application is ready to serve traffic.
        
        Readiness probe checks if all dependencies are available.
        """
        dependencies = []
        
        # Check database
        db_health = await self._check_database()
        dependencies.append(db_health)
        
        # Check Redis (if configured)
        redis_health = await self._check_redis()
        if redis_health:
            dependencies.append(redis_health)
        
        # Check Weaviate (if configured)
        weaviate_health = await self._check_weaviate()
        if weaviate_health:
            dependencies.append(weaviate_health)
        
        # Determine overall status
        if all(d.status == HealthStatus.HEALTHY for d in dependencies):
            status = HealthStatus.HEALTHY
        elif any(d.status == HealthStatus.UNHEALTHY for d in dependencies):
            status = HealthStatus.UNHEALTHY
        else:
            status = HealthStatus.DEGRADED
        
        return ReadinessResponse(
            status=status,
            dependencies=dependencies
        )
    
    async def check_detailed_health(self) -> DetailedHealthResponse:
        """Get detailed health status."""
        readiness = await self.check_readiness()
        
        uptime = (datetime.utcnow() - self.start_time).total_seconds()
        
        return DetailedHealthResponse(
            status=readiness.status,
            version="1.0.0",
            uptime_seconds=uptime,
            dependencies=readiness.dependencies,
            system_info=self._get_system_info()
        )
    
    async def _check_database(self) -> DependencyHealth:
        """Check database health."""
        import time
        from app.database.database import get_db
        
        start = time.time()
        try:
            async for db in get_db():
                # Simple query to check connection
                await db.execute("SELECT 1")
                response_time = (time.time() - start) * 1000
                
                return DependencyHealth(
                    name="database",
                    status=HealthStatus.HEALTHY,
                    response_time_ms=response_time
                )
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return DependencyHealth(
                name="database",
                status=HealthStatus.UNHEALTHY,
                error=str(e)
            )
    
    async def _check_redis(self) -> DependencyHealth | None:
        """Check Redis health."""
        import os
        
        redis_url = os.getenv("REDIS_URL")
        if not redis_url:
            return None
        
        import time
        try:
            import redis.asyncio as redis
            
            start = time.time()
            client = redis.from_url(redis_url)
            await client.ping()
            response_time = (time.time() - start) * 1000
            await client.close()
            
            return DependencyHealth(
                name="redis",
                status=HealthStatus.HEALTHY,
                response_time_ms=response_time
            )
        except Exception as e:
            logger.error(f"Redis health check failed: {e}")
            return DependencyHealth(
                name="redis",
                status=HealthStatus.UNHEALTHY,
                error=str(e)
            )
    
    async def _check_weaviate(self) -> DependencyHealth | None:
        """Check Weaviate health."""
        import os
        
        weaviate_url = os.getenv("WEAVIATE_URL")
        if not weaviate_url:
            return None
        
        import time
        try:
            import httpx
            
            start = time.time()
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{weaviate_url}/v1/.well-known/ready")
                response.raise_for_status()
            response_time = (time.time() - start) * 1000
            
            return DependencyHealth(
                name="weaviate",
                status=HealthStatus.HEALTHY,
                response_time_ms=response_time
            )
        except Exception as e:
            logger.error(f"Weaviate health check failed: {e}")
            return DependencyHealth(
                name="weaviate",
                status=HealthStatus.UNHEALTHY,
                error=str(e)
            )
    
    def _get_system_info(self) -> dict[str, Any]:
        """Get system information."""
        import psutil
        import platform
        
        return {
            "platform": platform.system(),
            "python_version": platform.python_version(),
            "cpu_percent": psutil.cpu_percent(),
            "memory_percent": psutil.virtual_memory().percent,
            "disk_percent": psutil.disk_usage("/").percent
        }


# Global health checker instance
health_checker = HealthChecker()
```

---

### 2. Health Check Endpoints

Update `app/api/v1/endpoints/health.py`:

```python
"""Health check endpoints."""
from fastapi import APIRouter, status
from app.core.health_checks import (
    health_checker,
    LivenessResponse,
    ReadinessResponse,
    DetailedHealthResponse,
    HealthStatus
)

router = APIRouter()


@router.get("/live", response_model=LivenessResponse, tags=["Health"])
async def liveness_probe():
    """
    Liveness probe endpoint.
    
    Returns 200 if application is alive.
    Kubernetes uses this to restart unhealthy pods.
    """
    return await health_checker.check_liveness()


@router.get("/ready", response_model=ReadinessResponse, tags=["Health"])
async def readiness_probe():
    """
    Readiness probe endpoint.
    
    Returns 200 if application is ready to serve traffic.
    Kubernetes uses this to route traffic to healthy pods.
    """
    readiness = await health_checker.check_readiness()
    
    # Return 503 if not ready
    if readiness.status == HealthStatus.UNHEALTHY:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content=readiness.model_dump()
        )
    
    return readiness


@router.get("/status", response_model=DetailedHealthResponse, tags=["Health"])
async def detailed_health():
    """
    Detailed health status endpoint.
    
    Returns comprehensive health information including dependencies.
    """
    return await health_checker.check_detailed_health()
```

---

## ✅ ACCEPTANCE CRITERIA

- [ ] Liveness probe implemented
- [ ] Readiness probe implemented
- [ ] Database health check working
- [ ] Redis health check working (if configured)
- [ ] Weaviate health check working (if configured)
- [ ] Kubernetes probes configured
- [ ] Health checks tested

---

## 🧪 TESTING

```python
# tests/test_health_checks.py
"""Tests for health check endpoints."""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_liveness_probe():
    """Test liveness probe returns 200."""
    response = client.get("/api/v1/health/live")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


def test_readiness_probe():
    """Test readiness probe checks dependencies."""
    response = client.get("/api/v1/health/ready")
    assert response.status_code in [200, 503]
    data = response.json()
    assert "dependencies" in data


def test_detailed_health():
    """Test detailed health endpoint."""
    response = client.get("/api/v1/health/status")
    assert response.status_code == 200
    data = response.json()
    assert "version" in data
    assert "uptime_seconds" in data
    assert "dependencies" in data
```

---

## 📝 NOTES

- Liveness should be simple and fast
- Readiness should check all dependencies
- Return 503 when not ready
- Configure appropriate timeouts


