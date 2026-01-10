"""
Performance Optimization Utilities for DRYAD.AI Backend
Provides database query optimization, connection pooling, and performance monitoring.
"""

import asyncio
import time
from contextlib import asynccontextmanager
from typing import Dict, Any, List, Optional, Callable
from functools import wraps
from dataclasses import dataclass
from collections import defaultdict, deque

from sqlalchemy import text, event
from sqlalchemy.engine import Engine
from sqlalchemy.pool import QueuePool

from app.core.logging_config import get_logger, metrics_logger
from app.core.caching import cached

logger = get_logger(__name__)


@dataclass
class QueryMetrics:
    """Query performance metrics."""
    query_hash: str
    query_text: str
    execution_count: int
    total_time: float
    avg_time: float
    min_time: float
    max_time: float
    last_executed: float


class QueryProfiler:
    """Database query profiler for performance monitoring."""
    
    def __init__(self, max_queries: int = 1000):
        self.max_queries = max_queries
        self.query_metrics: Dict[str, QueryMetrics] = {}
        self.slow_query_threshold = 1.0  # seconds
        self.slow_queries: deque = deque(maxlen=100)
        self.total_queries = 0
        self.total_time = 0.0
    
    def record_query(self, query_text: str, execution_time: float):
        """Record query execution metrics."""
        import hashlib
        
        # Generate query hash
        query_hash = hashlib.md5(query_text.encode()).hexdigest()[:16]
        
        # Update metrics
        if query_hash in self.query_metrics:
            metrics = self.query_metrics[query_hash]
            metrics.execution_count += 1
            metrics.total_time += execution_time
            metrics.avg_time = metrics.total_time / metrics.execution_count
            metrics.min_time = min(metrics.min_time, execution_time)
            metrics.max_time = max(metrics.max_time, execution_time)
            metrics.last_executed = time.time()
        else:
            # Evict oldest if at capacity
            if len(self.query_metrics) >= self.max_queries:
                oldest_hash = min(self.query_metrics.keys(), 
                                key=lambda k: self.query_metrics[k].last_executed)
                del self.query_metrics[oldest_hash]
            
            # Add new metrics
            self.query_metrics[query_hash] = QueryMetrics(
                query_hash=query_hash,
                query_text=query_text[:500],  # Truncate long queries
                execution_count=1,
                total_time=execution_time,
                avg_time=execution_time,
                min_time=execution_time,
                max_time=execution_time,
                last_executed=time.time()
            )
        
        # Track slow queries
        if execution_time > self.slow_query_threshold:
            self.slow_queries.append({
                "query_hash": query_hash,
                "query_text": query_text[:200],
                "execution_time": execution_time,
                "timestamp": time.time()
            })
        
        # Update totals
        self.total_queries += 1
        self.total_time += execution_time
        
        # Log metrics
        metrics_logger.record_timing("database_query_duration", execution_time * 1000)
        if execution_time > self.slow_query_threshold:
            logger.warning(f"Slow query detected: {execution_time:.3f}s - {query_text[:100]}...")
    
    def get_top_queries(self, limit: int = 10, sort_by: str = "avg_time") -> List[Dict[str, Any]]:
        """Get top queries by specified metric."""
        sorted_queries = sorted(
            self.query_metrics.values(),
            key=lambda q: getattr(q, sort_by),
            reverse=True
        )
        
        return [
            {
                "query_hash": q.query_hash,
                "query_text": q.query_text,
                "execution_count": q.execution_count,
                "avg_time_ms": round(q.avg_time * 1000, 2),
                "total_time_ms": round(q.total_time * 1000, 2),
                "min_time_ms": round(q.min_time * 1000, 2),
                "max_time_ms": round(q.max_time * 1000, 2)
            }
            for q in sorted_queries[:limit]
        ]
    
    def get_stats(self) -> Dict[str, Any]:
        """Get overall query statistics."""
        avg_query_time = (self.total_time / self.total_queries) if self.total_queries > 0 else 0
        
        return {
            "total_queries": self.total_queries,
            "total_time_seconds": round(self.total_time, 3),
            "avg_query_time_ms": round(avg_query_time * 1000, 2),
            "unique_queries": len(self.query_metrics),
            "slow_queries_count": len(self.slow_queries),
            "slow_query_threshold_ms": self.slow_query_threshold * 1000
        }


# Global query profiler
query_profiler = QueryProfiler()


def setup_database_monitoring(engine: Engine):
    """Set up database monitoring and optimization."""
    
    @event.listens_for(engine, "before_cursor_execute")
    def receive_before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
        """Record query start time."""
        context._query_start_time = time.time()
    
    @event.listens_for(engine, "after_cursor_execute")
    def receive_after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
        """Record query completion and metrics."""
        if hasattr(context, '_query_start_time'):
            execution_time = time.time() - context._query_start_time
            query_profiler.record_query(statement, execution_time)


class ConnectionPoolManager:
    """Advanced connection pool management."""
    
    def __init__(self):
        self.pool_stats = defaultdict(lambda: {
            "connections_created": 0,
            "connections_closed": 0,
            "connections_active": 0,
            "connections_checked_out": 0,
            "pool_size": 0,
            "checked_out_connections": 0
        })
    
    def configure_pool(self, engine: Engine, **pool_kwargs):
        """Configure connection pool with optimized settings."""
        
        # Default optimized pool settings
        default_settings = {
            "poolclass": QueuePool,
            "pool_size": 20,
            "max_overflow": 30,
            "pool_pre_ping": True,
            "pool_recycle": 3600,  # 1 hour
            "pool_timeout": 30
        }
        
        # Merge with provided settings
        settings = {**default_settings, **pool_kwargs}
        
        # Apply settings to engine
        for key, value in settings.items():
            if hasattr(engine.pool, key.replace('pool_', '')):
                setattr(engine.pool, key.replace('pool_', ''), value)
        
        # Set up pool monitoring
        self._setup_pool_monitoring(engine)
        
        logger.info(f"Database connection pool configured: {settings}")
    
    def _setup_pool_monitoring(self, engine: Engine):
        """Set up connection pool monitoring."""
        
        @event.listens_for(engine, "connect")
        def receive_connect(dbapi_connection, connection_record):
            """Track connection creation."""
            pool_id = id(engine.pool)
            self.pool_stats[pool_id]["connections_created"] += 1
            logger.debug("Database connection created")
        
        @event.listens_for(engine, "close")
        def receive_close(dbapi_connection, connection_record):
            """Track connection closure."""
            pool_id = id(engine.pool)
            self.pool_stats[pool_id]["connections_closed"] += 1
            logger.debug("Database connection closed")
    
    def get_pool_stats(self, engine: Engine) -> Dict[str, Any]:
        """Get connection pool statistics."""
        pool = engine.pool
        pool_id = id(pool)
        
        stats = self.pool_stats[pool_id].copy()
        
        # Add current pool state
        stats.update({
            "pool_size": pool.size(),
            "checked_out_connections": pool.checkedout(),
            "overflow_connections": pool.overflow(),
            "checked_in_connections": pool.checkedin()
        })
        
        return stats


# Global connection pool manager
pool_manager = ConnectionPoolManager()


class BatchProcessor:
    """Batch processing utilities for database operations."""
    
    def __init__(self, batch_size: int = 100):
        self.batch_size = batch_size
    
    async def batch_insert(self, session, model_class, data: List[Dict[str, Any]]) -> int:
        """Perform batch insert operations."""
        if not data:
            return 0
        
        total_inserted = 0
        
        with LogTimer(f"Batch insert {len(data)} {model_class.__name__} records"):
            # Process in batches
            for i in range(0, len(data), self.batch_size):
                batch = data[i:i + self.batch_size]
                
                try:
                    # Create model instances
                    instances = [model_class(**item) for item in batch]
                    
                    # Bulk insert
                    session.add_all(instances)
                    await session.commit()
                    
                    total_inserted += len(batch)
                    logger.debug(f"Inserted batch of {len(batch)} records")
                    
                except Exception as e:
                    await session.rollback()
                    logger.error(f"Batch insert failed: {e}")
                    raise
        
        logger.info(f"Batch insert completed: {total_inserted} records")
        return total_inserted
    
    async def batch_update(self, session, model_class, updates: List[Dict[str, Any]], key_field: str = "id") -> int:
        """Perform batch update operations."""
        if not updates:
            return 0
        
        total_updated = 0
        
        with LogTimer(f"Batch update {len(updates)} {model_class.__name__} records"):
            # Process in batches
            for i in range(0, len(updates), self.batch_size):
                batch = updates[i:i + self.batch_size]
                
                try:
                    # Bulk update using raw SQL for better performance
                    for update_data in batch:
                        key_value = update_data.pop(key_field)
                        
                        if update_data:  # Only update if there are fields to update
                            stmt = text(f"""
                                UPDATE {model_class.__tablename__} 
                                SET {', '.join(f"{k} = :{k}" for k in update_data.keys())}
                                WHERE {key_field} = :key_value
                            """)
                            
                            await session.execute(stmt, {**update_data, "key_value": key_value})
                    
                    await session.commit()
                    total_updated += len(batch)
                    logger.debug(f"Updated batch of {len(batch)} records")
                    
                except Exception as e:
                    await session.rollback()
                    logger.error(f"Batch update failed: {e}")
                    raise
        
        logger.info(f"Batch update completed: {total_updated} records")
        return total_updated


# Global batch processor
batch_processor = BatchProcessor()


def optimize_query(func: Callable) -> Callable:
    """Decorator for query optimization hints."""
    @wraps(func)
    async def async_wrapper(*args, **kwargs):
        with LogTimer(f"Optimized query: {func.__name__}"):
            return await func(*args, **kwargs)
    
    @wraps(func)
    def sync_wrapper(*args, **kwargs):
        with LogTimer(f"Optimized query: {func.__name__}"):
            return func(*args, **kwargs)
    
    if asyncio.iscoroutinefunction(func):
        return async_wrapper
    else:
        return sync_wrapper


@asynccontextmanager
async def database_transaction(session, isolation_level: Optional[str] = None):
    """Context manager for database transactions with performance monitoring."""
    start_time = time.time()
    
    try:
        if isolation_level:
            await session.execute(text(f"SET TRANSACTION ISOLATION LEVEL {isolation_level}"))
        
        yield session
        await session.commit()
        
        duration = time.time() - start_time
        metrics_logger.record_timing("database_transaction_duration", duration * 1000)
        logger.debug(f"Transaction completed in {duration:.3f}s")
        
    except Exception as e:
        await session.rollback()
        duration = time.time() - start_time
        logger.error(f"Transaction failed after {duration:.3f}s: {e}")
        raise


def get_performance_stats() -> Dict[str, Any]:
    """Get comprehensive performance statistics."""
    return {
        "query_profiler": query_profiler.get_stats(),
        "top_queries_by_time": query_profiler.get_top_queries(sort_by="avg_time"),
        "top_queries_by_count": query_profiler.get_top_queries(sort_by="execution_count"),
        "slow_queries": list(query_profiler.slow_queries)[-10:],  # Last 10 slow queries
        "timestamp": time.time()
    }


# Performance monitoring decorator
def monitor_performance(operation_name: str = None):
    """Decorator for monitoring operation performance."""
    def decorator(func: Callable) -> Callable:
        op_name = operation_name or f"{func.__module__}.{func.__name__}"
        
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                duration = time.time() - start_time
                metrics_logger.record_timing(f"{op_name}_duration", duration * 1000)
                return result
            except Exception as e:
                duration = time.time() - start_time
                metrics_logger.record_timing(f"{op_name}_error_duration", duration * 1000)
                raise
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                metrics_logger.record_timing(f"{op_name}_duration", duration * 1000)
                return result
            except Exception as e:
                duration = time.time() - start_time
                metrics_logger.record_timing(f"{op_name}_error_duration", duration * 1000)
                raise
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator
