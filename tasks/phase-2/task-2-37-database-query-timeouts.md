# Task 2-37: Database Query Timeouts

**Phase:** 2 - Performance & Production Readiness  
**Week:** 5 - Performance Optimization  
**Priority:** HIGH  
**Estimated Hours:** 2 hours

---

## 📋 OVERVIEW

Configure database query timeouts to prevent long-running queries from blocking resources and ensure responsive database operations.

---

## 🎯 OBJECTIVES

1. Configure statement timeout for PostgreSQL
2. Set busy timeout for SQLite
3. Implement query timeout monitoring
4. Add timeout error handling
5. Test timeout scenarios
6. Document timeout policies

---

## 📊 CURRENT STATE

**Existing:**
- No query timeouts configured
- Queries can run indefinitely
- No timeout monitoring

**Gaps:**
- Risk of long-running queries
- No timeout protection
- No query performance monitoring

---

## 🔧 IMPLEMENTATION

### 1. SQLite Query Timeout

Update `app/database/database.py`:

```python
"""
Database Configuration with Query Timeouts

SQLite and PostgreSQL timeout configuration.
"""
from __future__ import annotations

import logging
from sqlalchemy import event, create_engine
from sqlalchemy.ext.asyncio import create_async_engine
from app.core.config import settings

logger = logging.getLogger(__name__)


def configure_sqlite_timeout(dbapi_conn, connection_record):
    """
    Configure SQLite busy timeout.
    
    Args:
        dbapi_conn: Database API connection
        connection_record: Connection record
    """
    cursor = dbapi_conn.cursor()
    # Set busy timeout to 30 seconds (30000 milliseconds)
    cursor.execute("PRAGMA busy_timeout = 30000")
    cursor.close()
    logger.debug("SQLite busy timeout configured: 30s")


def configure_postgresql_timeout(dbapi_conn, connection_record):
    """
    Configure PostgreSQL statement timeout.
    
    Args:
        dbapi_conn: Database API connection
        connection_record: Connection record
    """
    cursor = dbapi_conn.cursor()
    # Set statement timeout to 30 seconds (30000 milliseconds)
    cursor.execute("SET statement_timeout = 30000")
    cursor.close()
    logger.debug("PostgreSQL statement timeout configured: 30s")


# Create engine with timeout configuration
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    pool_pre_ping=True,
    pool_recycle=3600,
)

# Register timeout configuration based on database type
if "sqlite" in settings.DATABASE_URL:
    event.listen(engine.sync_engine, "connect", configure_sqlite_timeout)
elif "postgresql" in settings.DATABASE_URL:
    event.listen(engine.sync_engine, "connect", configure_postgresql_timeout)
```

---

### 2. Query Timeout Decorator

Create `app/core/query_timeout.py`:

```python
"""
Query Timeout Utilities

Decorators and utilities for query timeout management.
"""
from __future__ import annotations

import asyncio
import logging
from typing import Callable, TypeVar
from functools import wraps
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

T = TypeVar("T")


def with_query_timeout(timeout: float = 30.0):
    """
    Decorator to enforce query timeout.
    
    Args:
        timeout: Timeout in seconds
    
    Example:
        @with_query_timeout(timeout=10.0)
        async def get_user(db: AsyncSession, user_id: str):
            ...
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await asyncio.wait_for(
                    func(*args, **kwargs),
                    timeout=timeout
                )
            except asyncio.TimeoutError:
                logger.error(
                    f"Query timeout in {func.__name__}",
                    extra={"function": func.__name__, "timeout": timeout}
                )
                raise QueryTimeoutError(
                    f"Query exceeded {timeout}s timeout"
                )
        return wrapper
    return decorator


class QueryTimeoutError(Exception):
    """Raised when query exceeds timeout."""
    pass
```

---

### 3. Query Monitoring

Create `app/core/query_monitor.py`:

```python
"""
Query Performance Monitoring

Track slow queries and timeouts.
"""
from __future__ import annotations

import time
import logging
from collections import defaultdict
from datetime import datetime
from sqlalchemy import event
from sqlalchemy.engine import Engine

logger = logging.getLogger(__name__)


class QueryMonitor:
    """Monitor database query performance."""
    
    def __init__(self, slow_query_threshold: float = 1.0):
        self.slow_query_threshold = slow_query_threshold
        self.slow_queries: list[dict] = []
        self.query_counts: dict[str, int] = defaultdict(int)
        self.total_time: dict[str, float] = defaultdict(float)
    
    def record_query(
        self,
        query: str,
        duration: float,
        params: dict | None = None
    ):
        """
        Record query execution.
        
        Args:
            query: SQL query
            duration: Execution time in seconds
            params: Query parameters
        """
        # Normalize query for counting
        query_normalized = self._normalize_query(query)
        
        self.query_counts[query_normalized] += 1
        self.total_time[query_normalized] += duration
        
        # Record slow queries
        if duration > self.slow_query_threshold:
            self.slow_queries.append({
                "query": query,
                "duration": duration,
                "params": params,
                "timestamp": datetime.now().isoformat()
            })
            
            logger.warning(
                f"Slow query detected: {duration:.2f}s",
                extra={
                    "query": query[:100],
                    "duration": duration,
                    "threshold": self.slow_query_threshold
                }
            )
    
    def _normalize_query(self, query: str) -> str:
        """Normalize query for grouping."""
        # Remove extra whitespace
        query = " ".join(query.split())
        # Truncate for grouping
        return query[:100]
    
    def get_slow_queries(self, limit: int = 10) -> list[dict]:
        """
        Get slowest queries.
        
        Args:
            limit: Number of queries to return
        
        Returns:
            List of slow queries
        """
        return sorted(
            self.slow_queries,
            key=lambda x: x["duration"],
            reverse=True
        )[:limit]
    
    def get_stats(self) -> dict:
        """Get query statistics."""
        return {
            "total_queries": sum(self.query_counts.values()),
            "slow_queries": len(self.slow_queries),
            "most_frequent": sorted(
                self.query_counts.items(),
                key=lambda x: x[1],
                reverse=True
            )[:10],
            "slowest_average": sorted(
                [
                    (query, self.total_time[query] / self.query_counts[query])
                    for query in self.query_counts
                ],
                key=lambda x: x[1],
                reverse=True
            )[:10]
        }


# Global query monitor
query_monitor = QueryMonitor()


# SQLAlchemy event listeners
@event.listens_for(Engine, "before_cursor_execute")
def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    """Record query start time."""
    conn.info.setdefault("query_start_time", []).append(time.time())


@event.listens_for(Engine, "after_cursor_execute")
def after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    """Record query completion and duration."""
    total_time = time.time() - conn.info["query_start_time"].pop()
    query_monitor.record_query(statement, total_time, parameters)
```

---

### 4. Query Timeout Configuration

Create `app/core/query_config.py`:

```python
"""
Query Timeout Configuration

Centralized query timeout settings.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class QueryConfig:
    """Query timeout configuration."""
    
    # Default query timeout (seconds)
    default_timeout: float = 30.0
    
    # Slow query threshold (seconds)
    slow_query_threshold: float = 1.0
    
    # Long-running query timeout (seconds)
    long_query_timeout: float = 300.0
    
    # Read query timeout (seconds)
    read_timeout: float = 30.0
    
    # Write query timeout (seconds)
    write_timeout: float = 60.0
    
    # Bulk operation timeout (seconds)
    bulk_timeout: float = 300.0


# Global query configuration
query_config = QueryConfig()
```

---

### 5. Query Timeout Endpoint

Create `app/api/v1/endpoints/query_stats.py`:

```python
"""
Query Statistics Endpoints

Monitor query performance.
"""
from __future__ import annotations

from fastapi import APIRouter
from app.core.query_monitor import query_monitor

router = APIRouter()


@router.get("/query/stats")
async def get_query_stats():
    """Get query performance statistics."""
    return query_monitor.get_stats()


@router.get("/query/slow")
async def get_slow_queries(limit: int = 10):
    """Get slowest queries."""
    return {
        "slow_queries": query_monitor.get_slow_queries(limit)
    }
```

---

## ✅ ACCEPTANCE CRITERIA

- [ ] Query timeouts configured
- [ ] SQLite busy timeout set
- [ ] PostgreSQL statement timeout set
- [ ] Query monitoring implemented
- [ ] Slow query detection working
- [ ] Timeout errors handled
- [ ] Documentation complete

---

## 🧪 TESTING

```python
# tests/test_query_timeout.py
"""Tests for query timeouts."""
import pytest
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.query_timeout import with_query_timeout, QueryTimeoutError


@pytest.mark.asyncio
async def test_query_timeout():
    """Test query timeout enforcement."""
    
    @with_query_timeout(timeout=1.0)
    async def slow_query(db: AsyncSession):
        await asyncio.sleep(2)  # Simulate slow query
        return "result"
    
    with pytest.raises(QueryTimeoutError):
        await slow_query(None)


@pytest.mark.asyncio
async def test_fast_query_no_timeout():
    """Test fast query completes normally."""
    
    @with_query_timeout(timeout=5.0)
    async def fast_query(db: AsyncSession):
        await asyncio.sleep(0.1)
        return "result"
    
    result = await fast_query(None)
    assert result == "result"
```

---

## 📝 NOTES

- Set appropriate timeouts for different query types
- Monitor slow queries regularly
- Optimize queries that frequently timeout
- Use longer timeouts for bulk operations
- Log timeout events for analysis


