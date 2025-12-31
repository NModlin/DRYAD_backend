# Task 2-32: Database Connection Retry Logic

**Phase:** 2 - Performance & Production Readiness  
**Week:** 5 - Performance Optimization  
**Priority:** HIGH  
**Estimated Hours:** 2 hours

---

## 📋 OVERVIEW

Implement robust database connection retry logic with exponential backoff to handle transient connection failures during deployments, network issues, or database restarts.

---

## 🎯 OBJECTIVES

1. Implement connection retry with exponential backoff
2. Add connection health checks
3. Configure retry parameters
4. Add connection failure logging
5. Test retry scenarios
6. Document retry behavior

---

## 📊 CURRENT STATE

**Existing:**
- Basic database connection
- No retry logic
- Fails immediately on connection error

**Gaps:**
- No retry mechanism
- No exponential backoff
- No connection health checks
- Poor resilience to transient failures

---

## 🔧 IMPLEMENTATION

### 1. Database Connection with Retry

Update `app/database/database.py`:

```python
"""
Database Connection with Retry Logic

Robust database connection handling.
"""
from __future__ import annotations

import asyncio
import logging
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    create_async_engine,
    async_sessionmaker
)
from sqlalchemy.exc import OperationalError, DBAPIError
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log
)
from app.core.config import settings

logger = logging.getLogger(__name__)


class DatabaseConnectionManager:
    """Manages database connections with retry logic."""
    
    def __init__(self):
        self.engine = None
        self.session_factory = None
        self._initialized = False
    
    @retry(
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=1, min=2, max=30),
        retry=retry_if_exception_type((OperationalError, DBAPIError)),
        before_sleep=before_sleep_log(logger, logging.WARNING)
    )
    async def initialize(self):
        """
        Initialize database connection with retry.
        
        Retries up to 5 times with exponential backoff:
        - Attempt 1: immediate
        - Attempt 2: wait 2 seconds
        - Attempt 3: wait 4 seconds
        - Attempt 4: wait 8 seconds
        - Attempt 5: wait 16 seconds
        """
        if self._initialized:
            return
        
        logger.info("Initializing database connection...")
        
        try:
            # Create async engine
            self.engine = create_async_engine(
                settings.DATABASE_URL,
                echo=settings.DEBUG,
                pool_size=10,
                max_overflow=20,
                pool_pre_ping=True,  # Verify connections before using
                pool_recycle=3600,   # Recycle connections after 1 hour
                connect_args={
                    "timeout": 30,
                    "check_same_thread": False
                }
            )
            
            # Test connection
            async with self.engine.begin() as conn:
                await conn.execute("SELECT 1")
            
            # Create session factory
            self.session_factory = async_sessionmaker(
                self.engine,
                class_=AsyncSession,
                expire_on_commit=False
            )
            
            self._initialized = True
            logger.info("✅ Database connection initialized successfully")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize database: {e}")
            raise
    
    async def close(self):
        """Close database connection."""
        if self.engine:
            await self.engine.dispose()
            self._initialized = False
            logger.info("Database connection closed")
    
    async def health_check(self) -> bool:
        """
        Check database connection health.
        
        Returns:
            True if healthy, False otherwise
        """
        if not self._initialized:
            return False
        
        try:
            async with self.engine.begin() as conn:
                await conn.execute("SELECT 1")
            return True
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False


# Global connection manager
db_manager = DatabaseConnectionManager()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Get database session with automatic retry.
    
    Yields:
        Database session
    """
    if not db_manager._initialized:
        await db_manager.initialize()
    
    async with db_manager.session_factory() as session:
        try:
            yield session
        except Exception as e:
            await session.rollback()
            logger.error(f"Database session error: {e}")
            raise
        finally:
            await session.close()


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=10),
    retry=retry_if_exception_type((OperationalError, DBAPIError)),
    before_sleep=before_sleep_log(logger, logging.WARNING)
)
async def execute_with_retry(session: AsyncSession, query):
    """
    Execute query with retry logic.
    
    Args:
        session: Database session
        query: SQLAlchemy query
    
    Returns:
        Query result
    """
    try:
        result = await session.execute(query)
        return result
    except (OperationalError, DBAPIError) as e:
        logger.warning(f"Query failed, retrying: {e}")
        raise
```

---

### 2. Application Startup with Retry

Update `app/main.py`:

```python
"""
FastAPI Application with Database Retry

Handles database connection on startup.
"""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.database.database import db_manager

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan with database initialization.
    
    Retries database connection on startup.
    """
    # Startup
    logger.info("🚀 Starting application...")
    
    try:
        # Initialize database with retry
        await db_manager.initialize()
        logger.info("✅ Database initialized")
    except Exception as e:
        logger.error(f"❌ Failed to initialize database: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("🛑 Shutting down application...")
    await db_manager.close()
    logger.info("✅ Shutdown complete")


app = FastAPI(lifespan=lifespan)
```

---

### 3. Connection Health Check Endpoint

Create `app/api/v1/endpoints/health.py`:

```python
"""
Health Check Endpoints

Includes database connection health.
"""
from __future__ import annotations

from fastapi import APIRouter, status
from pydantic import BaseModel
from app.database.database import db_manager

router = APIRouter()


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    database: str


@router.get("/health/ready", response_model=HealthResponse)
async def readiness_check():
    """
    Readiness check - includes database health.
    
    Returns 200 if ready, 503 if not ready.
    """
    db_healthy = await db_manager.health_check()
    
    if db_healthy:
        return HealthResponse(
            status="ready",
            database="connected"
        )
    else:
        return HealthResponse(
            status="not_ready",
            database="disconnected"
        ), status.HTTP_503_SERVICE_UNAVAILABLE


@router.get("/health/live")
async def liveness_check():
    """
    Liveness check - application is alive.
    
    Does not check dependencies.
    """
    return {"status": "alive"}
```

---

### 4. Retry Configuration

Create `app/core/retry_config.py`:

```python
"""
Retry Configuration

Centralized retry settings.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class RetryConfig:
    """Retry configuration settings."""
    
    # Database connection retry
    db_max_attempts: int = 5
    db_min_wait: int = 2
    db_max_wait: int = 30
    db_multiplier: int = 1
    
    # Query retry
    query_max_attempts: int = 3
    query_min_wait: int = 1
    query_max_wait: int = 10
    
    # Health check retry
    health_max_attempts: int = 3
    health_wait: int = 5


# Global retry configuration
retry_config = RetryConfig()
```

---

## ✅ ACCEPTANCE CRITERIA

- [ ] Connection retry implemented
- [ ] Exponential backoff configured
- [ ] Health checks working
- [ ] Retry logging implemented
- [ ] Startup retry tested
- [ ] Transient failure handling verified
- [ ] Documentation complete

---

## 🧪 TESTING

```python
# tests/test_database_retry.py
"""Tests for database retry logic."""
import pytest
from unittest.mock import patch, AsyncMock
from sqlalchemy.exc import OperationalError
from app.database.database import db_manager


@pytest.mark.asyncio
async def test_connection_retry_success():
    """Test successful connection after retry."""
    with patch.object(db_manager, 'engine') as mock_engine:
        # Fail twice, then succeed
        mock_engine.begin.side_effect = [
            OperationalError("Connection failed", None, None),
            OperationalError("Connection failed", None, None),
            AsyncMock()
        ]
        
        await db_manager.initialize()
        assert db_manager._initialized


@pytest.mark.asyncio
async def test_connection_retry_failure():
    """Test connection failure after max retries."""
    with patch.object(db_manager, 'engine') as mock_engine:
        # Always fail
        mock_engine.begin.side_effect = OperationalError(
            "Connection failed", None, None
        )
        
        with pytest.raises(OperationalError):
            await db_manager.initialize()


@pytest.mark.asyncio
async def test_health_check():
    """Test database health check."""
    await db_manager.initialize()
    healthy = await db_manager.health_check()
    assert healthy is True
```

---

## 📝 NOTES

- Use exponential backoff to avoid overwhelming database
- Log retry attempts for debugging
- Set reasonable max attempts (3-5)
- Test with actual database failures
- Monitor retry metrics in production


