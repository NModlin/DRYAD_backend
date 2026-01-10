"""
Prometheus metrics middleware for Uni0 application
Tracks request metrics, database operations, and system performance
"""

from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
import time
import logging

logger = logging.getLogger(__name__)

# Request metrics
request_count = Counter(
    'uni0_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status_code']
)

request_duration = Histogram(
    'uni0_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint'],
    buckets=(0.01, 0.025, 0.05, 0.075, 0.1, 0.25, 0.5, 0.75, 1.0, 2.5, 5.0, 7.5, 10.0)
)

active_requests = Gauge(
    'uni0_active_requests',
    'Number of active HTTP requests',
    ['method', 'endpoint']
)

# Authentication metrics
auth_attempts = Counter(
    'uni0_auth_attempts_total',
    'Total authentication attempts',
    ['status']  # success, failure
)

auth_duration = Histogram(
    'uni0_auth_duration_seconds',
    'Authentication operation duration in seconds',
    buckets=(0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5)
)

# Database metrics
db_queries = Counter(
    'uni0_db_queries_total',
    'Total database queries',
    ['operation', 'table']  # operation: select, insert, update, delete
)

db_query_duration = Histogram(
    'uni0_db_query_duration_seconds',
    'Database query duration in seconds',
    ['operation'],
    buckets=(0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0)
)

# Business logic metrics
universities_total = Gauge(
    'uni0_universities_total',
    'Total number of universities'
)

agents_total = Gauge(
    'uni0_agents_total',
    'Total number of agents'
)

agents_active = Gauge(
    'uni0_agents_active',
    'Number of active agents'
)

competitions_total = Gauge(
    'uni0_competitions_total',
    'Total number of competitions'
)

competitions_active = Gauge(
    'uni0_competitions_active',
    'Number of active competitions'
)

# Error metrics
errors_total = Counter(
    'uni0_errors_total',
    'Total errors',
    ['error_type', 'endpoint']
)

# Rate limit metrics
rate_limit_exceeded = Counter(
    'uni0_rate_limit_exceeded_total',
    'Total rate limit exceeded events',
    ['endpoint']
)


class PrometheusMiddleware(BaseHTTPMiddleware):
    """Middleware to track Prometheus metrics"""
    
    async def dispatch(self, request: Request, call_next):
        # Skip metrics endpoint to avoid recursion
        if request.url.path == "/metrics":
            return await call_next(request)
        
        # Extract endpoint path (remove IDs to group similar requests)
        endpoint = self._normalize_endpoint(request.url.path)
        method = request.method
        
        # Track active requests
        active_requests.labels(method=method, endpoint=endpoint).inc()
        
        # Track request duration
        start_time = time.time()
        
        try:
            response = await call_next(request)
            status_code = response.status_code
        except Exception as exc:
            status_code = 500
            errors_total.labels(error_type=type(exc).__name__, endpoint=endpoint).inc()
            raise
        finally:
            # Record metrics
            duration = time.time() - start_time
            request_duration.labels(method=method, endpoint=endpoint).observe(duration)
            request_count.labels(method=method, endpoint=endpoint, status_code=status_code).inc()
            active_requests.labels(method=method, endpoint=endpoint).dec()
        
        return response
    
    @staticmethod
    def _normalize_endpoint(path: str) -> str:
        """Normalize endpoint path by removing IDs"""
        # Remove UUID and numeric IDs from path
        import re
        # Replace UUIDs and numeric IDs with placeholders
        normalized = re.sub(r'/[a-f0-9\-]{36}', '/{id}', path)  # UUID
        normalized = re.sub(r'/\d+', '/{id}', normalized)  # Numeric ID
        return normalized


def record_auth_attempt(success: bool):
    """Record authentication attempt"""
    status = "success" if success else "failure"
    auth_attempts.labels(status=status).inc()


def record_auth_duration(duration: float):
    """Record authentication duration"""
    auth_duration.observe(duration)


def record_db_query(operation: str, table: str, duration: float):
    """Record database query"""
    db_queries.labels(operation=operation, table=table).inc()
    db_query_duration.labels(operation=operation).observe(duration)


def update_business_metrics(db_session):
    """Update business logic metrics from app.university_system.database"""
    try:
        from app.university_system.database.models_university import (
            University, UniversityAgent, Competition
        )
        
        # Update university metrics
        total_unis = db_session.query(University).count()
        universities_total.set(total_unis)
        
        # Update agent metrics
        total_agents = db_session.query(UniversityAgent).count()
        active_agents_count = db_session.query(UniversityAgent).filter(
            UniversityAgent.status == "active"
        ).count()
        
        agents_total.set(total_agents)
        agents_active.set(active_agents_count)
        
        # Update competition metrics
        total_comps = db_session.query(Competition).count()
        active_comps = db_session.query(Competition).filter(
            Competition.status == "active"
        ).count()
        
        competitions_total.set(total_comps)
        competitions_active.set(active_comps)
        
    except Exception as exc:
        logger.error(f"Error updating business metrics: {str(exc)}")

