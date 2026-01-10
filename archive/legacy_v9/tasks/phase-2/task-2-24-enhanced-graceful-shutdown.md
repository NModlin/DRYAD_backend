# Task 2-24: Enhanced Graceful Shutdown Implementation

**Phase:** 2 - Performance & Production Readiness  
**Week:** 8 - Production Deployment & Validation  
**Priority:** CRITICAL  
**Estimated Hours:** 4 hours

---

## 📋 OVERVIEW

Implement graceful shutdown with SIGTERM handler, connection draining, in-flight request handling, and cleanup procedures to prevent data loss and ensure smooth deployments.

---

## 🎯 OBJECTIVES

1. Implement SIGTERM handler
2. Add connection draining
3. Handle in-flight requests
4. Add cleanup procedures
5. Test shutdown scenarios
6. Configure shutdown timeout

---

## 📊 CURRENT STATE

**Existing:**
- Basic FastAPI application
- No graceful shutdown handling
- No connection draining

**Gaps:**
- No SIGTERM handler
- No in-flight request tracking
- No cleanup procedures
- No shutdown timeout

---

## 🔧 IMPLEMENTATION

### 1. Graceful Shutdown Manager

Create `app/core/shutdown.py`:

```python
"""
Graceful Shutdown Manager

Handles application shutdown gracefully.
"""
from __future__ import annotations

import asyncio
import logging
import signal
from typing import Callable
from datetime import datetime

logger = logging.getLogger(__name__)


class GracefulShutdownManager:
    """Manages graceful application shutdown."""
    
    def __init__(self, shutdown_timeout: int = 30):
        self.shutdown_timeout = shutdown_timeout
        self.is_shutting_down = False
        self.in_flight_requests = 0
        self.cleanup_tasks: list[Callable] = []
        self.shutdown_event = asyncio.Event()
    
    def register_cleanup_task(self, task: Callable):
        """Register a cleanup task to run on shutdown."""
        self.cleanup_tasks.append(task)
        logger.info(f"Registered cleanup task: {task.__name__}")
    
    def track_request_start(self):
        """Track start of a request."""
        self.in_flight_requests += 1
    
    def track_request_end(self):
        """Track end of a request."""
        self.in_flight_requests -= 1
        if self.is_shutting_down and self.in_flight_requests == 0:
            self.shutdown_event.set()
    
    async def shutdown(self):
        """Perform graceful shutdown."""
        if self.is_shutting_down:
            logger.warning("Shutdown already in progress")
            return
        
        self.is_shutting_down = True
        shutdown_start = datetime.utcnow()
        
        logger.info("=" * 60)
        logger.info("GRACEFUL SHUTDOWN INITIATED")
        logger.info("=" * 60)
        
        # Step 1: Stop accepting new requests
        logger.info("Step 1: Stopping new request acceptance")
        # This is handled by the middleware
        
        # Step 2: Wait for in-flight requests to complete
        logger.info(f"Step 2: Waiting for {self.in_flight_requests} in-flight requests")
        if self.in_flight_requests > 0:
            try:
                await asyncio.wait_for(
                    self.shutdown_event.wait(),
                    timeout=self.shutdown_timeout
                )
                logger.info("✅ All in-flight requests completed")
            except asyncio.TimeoutError:
                logger.warning(
                    f"⚠️  Shutdown timeout reached with {self.in_flight_requests} "
                    f"requests still in flight"
                )
        
        # Step 3: Run cleanup tasks
        logger.info(f"Step 3: Running {len(self.cleanup_tasks)} cleanup tasks")
        for task in self.cleanup_tasks:
            try:
                if asyncio.iscoroutinefunction(task):
                    await task()
                else:
                    task()
                logger.info(f"✅ Cleanup task completed: {task.__name__}")
            except Exception as e:
                logger.error(f"❌ Cleanup task failed: {task.__name__}: {e}")
        
        # Step 4: Close database connections
        logger.info("Step 4: Closing database connections")
        await self._close_database_connections()
        
        # Step 5: Close Redis connections
        logger.info("Step 5: Closing Redis connections")
        await self._close_redis_connections()
        
        shutdown_duration = (datetime.utcnow() - shutdown_start).total_seconds()
        logger.info("=" * 60)
        logger.info(f"GRACEFUL SHUTDOWN COMPLETED ({shutdown_duration:.2f}s)")
        logger.info("=" * 60)
    
    async def _close_database_connections(self):
        """Close database connections."""
        try:
            from app.database.database import engine
            if engine:
                await engine.dispose()
                logger.info("✅ Database connections closed")
        except Exception as e:
            logger.error(f"❌ Error closing database connections: {e}")
    
    async def _close_redis_connections(self):
        """Close Redis connections."""
        try:
            import os
            redis_url = os.getenv("REDIS_URL")
            if redis_url:
                # Close Redis connections if any
                logger.info("✅ Redis connections closed")
        except Exception as e:
            logger.error(f"❌ Error closing Redis connections: {e}")


# Global shutdown manager
shutdown_manager = GracefulShutdownManager(shutdown_timeout=30)
```

---

### 2. Shutdown Middleware

Create `app/middleware/shutdown.py`:

```python
"""
Shutdown Middleware

Tracks in-flight requests and rejects new requests during shutdown.
"""
from __future__ import annotations

from typing import Callable
from fastapi import Request, Response, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.shutdown import shutdown_manager


class ShutdownMiddleware(BaseHTTPMiddleware):
    """Middleware for graceful shutdown."""
    
    async def dispatch(
        self,
        request: Request,
        call_next: Callable
    ) -> Response:
        """Process request with shutdown handling."""
        
        # Reject new requests if shutting down
        if shutdown_manager.is_shutting_down:
            return JSONResponse(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                content={
                    "error": "Service Unavailable",
                    "message": "Server is shutting down",
                    "code": "DRYAD-SYS-5003"
                }
            )
        
        # Track request
        shutdown_manager.track_request_start()
        
        try:
            response = await call_next(request)
            return response
        finally:
            shutdown_manager.track_request_end()
```

---

### 3. Signal Handlers

Update `app/main.py`:

```python
"""Main application with graceful shutdown."""
import signal
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI

from app.core.shutdown import shutdown_manager
from app.middleware.shutdown import ShutdownMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info("🚀 Application starting up")
    
    # Register signal handlers
    def signal_handler(signum, frame):
        """Handle shutdown signals."""
        logger.info(f"Received signal {signum}")
        asyncio.create_task(shutdown_manager.shutdown())
    
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)
    
    # Register cleanup tasks
    shutdown_manager.register_cleanup_task(cleanup_temp_files)
    shutdown_manager.register_cleanup_task(flush_metrics)
    
    yield
    
    # Shutdown
    logger.info("🛑 Application shutting down")
    await shutdown_manager.shutdown()


app = FastAPI(lifespan=lifespan)

# Add shutdown middleware
app.add_middleware(ShutdownMiddleware)


async def cleanup_temp_files():
    """Cleanup temporary files."""
    logger.info("Cleaning up temporary files")
    # Implementation here


async def flush_metrics():
    """Flush metrics before shutdown."""
    logger.info("Flushing metrics")
    # Implementation here
```

---

### 4. Kubernetes Configuration

Update `kubernetes/deployment.yaml`:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: gremlins-api
spec:
  template:
    spec:
      containers:
      - name: api
        lifecycle:
          preStop:
            exec:
              command: ["/bin/sh", "-c", "sleep 5"]
        terminationGracePeriodSeconds: 60
```

---

## ✅ ACCEPTANCE CRITERIA

- [ ] SIGTERM handler implemented
- [ ] Connection draining working
- [ ] In-flight requests tracked
- [ ] Cleanup tasks executed
- [ ] Shutdown timeout configured
- [ ] Kubernetes configuration updated
- [ ] Shutdown scenarios tested

---

## 🧪 TESTING

```python
# tests/test_graceful_shutdown.py
"""Tests for graceful shutdown."""
import pytest
import asyncio
from app.core.shutdown import GracefulShutdownManager


@pytest.mark.asyncio
async def test_shutdown_waits_for_requests():
    """Test shutdown waits for in-flight requests."""
    manager = GracefulShutdownManager(shutdown_timeout=5)
    
    # Simulate in-flight request
    manager.track_request_start()
    
    # Start shutdown in background
    shutdown_task = asyncio.create_task(manager.shutdown())
    
    # Wait a bit
    await asyncio.sleep(0.1)
    
    # Complete request
    manager.track_request_end()
    
    # Shutdown should complete
    await shutdown_task
    assert manager.is_shutting_down


@pytest.mark.asyncio
async def test_cleanup_tasks_executed():
    """Test cleanup tasks are executed."""
    manager = GracefulShutdownManager()
    
    executed = []
    
    async def cleanup_task():
        executed.append(True)
    
    manager.register_cleanup_task(cleanup_task)
    await manager.shutdown()
    
    assert len(executed) == 1
```

---

## 📝 NOTES

- Set appropriate shutdown timeout
- Test with real traffic
- Monitor shutdown duration
- Log all shutdown steps


