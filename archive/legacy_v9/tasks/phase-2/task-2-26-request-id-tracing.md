# Task 2-26: Request ID & Distributed Tracing

**Phase:** 2 - Performance & Production Readiness  
**Week:** 6 - Monitoring & Observability  
**Priority:** HIGH  
**Estimated Hours:** 4 hours

---

## 📋 OVERVIEW

Implement request ID generation and propagation for distributed tracing, enabling end-to-end request tracking across services and improving debugging capabilities.

---

## 🎯 OBJECTIVES

1. Generate unique request IDs
2. Propagate request IDs through middleware
3. Include request IDs in logs
4. Add request IDs to error responses
5. Implement distributed tracing headers
6. Test request ID propagation

---

## 📊 CURRENT STATE

**Existing:**
- Basic logging
- No request ID tracking

**Gaps:**
- No request ID generation
- No request ID in logs
- No request ID in error responses
- No distributed tracing

---

## 🔧 IMPLEMENTATION

### 1. Request ID Middleware

Create `app/middleware/request_id.py`:

```python
"""
Request ID Middleware

Generates and propagates request IDs for tracing.
"""
from __future__ import annotations

import uuid
import logging
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Middleware for request ID generation and propagation."""
    
    REQUEST_ID_HEADER = "X-Request-ID"
    TRACE_ID_HEADER = "X-Trace-ID"
    SPAN_ID_HEADER = "X-Span-ID"
    
    async def dispatch(
        self,
        request: Request,
        call_next: Callable
    ) -> Response:
        """Generate and propagate request ID."""
        
        # Get or generate request ID
        request_id = request.headers.get(self.REQUEST_ID_HEADER)
        if not request_id:
            request_id = self._generate_request_id()
        
        # Get or generate trace ID (for distributed tracing)
        trace_id = request.headers.get(self.TRACE_ID_HEADER)
        if not trace_id:
            trace_id = self._generate_trace_id()
        
        # Generate span ID for this service
        span_id = self._generate_span_id()
        
        # Store in request state
        request.state.request_id = request_id
        request.state.trace_id = trace_id
        request.state.span_id = span_id
        
        # Add to logging context
        with self._logging_context(request_id, trace_id, span_id):
            # Process request
            response = await call_next(request)
            
            # Add headers to response
            response.headers[self.REQUEST_ID_HEADER] = request_id
            response.headers[self.TRACE_ID_HEADER] = trace_id
            response.headers[self.SPAN_ID_HEADER] = span_id
            
            # Log request completion
            logger.info(
                f"{request.method} {request.url.path} - {response.status_code}",
                extra={
                    "request_id": request_id,
                    "trace_id": trace_id,
                    "span_id": span_id,
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": response.status_code,
                }
            )
            
            return response
    
    def _generate_request_id(self) -> str:
        """Generate unique request ID."""
        return f"req_{uuid.uuid4().hex[:16]}"
    
    def _generate_trace_id(self) -> str:
        """Generate unique trace ID."""
        return f"trace_{uuid.uuid4().hex}"
    
    def _generate_span_id(self) -> str:
        """Generate unique span ID."""
        return f"span_{uuid.uuid4().hex[:8]}"
    
    def _logging_context(self, request_id: str, trace_id: str, span_id: str):
        """Create logging context with request IDs."""
        import contextvars
        
        # Create context vars for request IDs
        request_id_var = contextvars.ContextVar("request_id", default=None)
        trace_id_var = contextvars.ContextVar("trace_id", default=None)
        span_id_var = contextvars.ContextVar("span_id", default=None)
        
        # Set values
        request_id_token = request_id_var.set(request_id)
        trace_id_token = trace_id_var.set(trace_id)
        span_id_token = span_id_var.set(span_id)
        
        try:
            yield
        finally:
            # Reset context
            request_id_var.reset(request_id_token)
            trace_id_var.reset(trace_id_token)
            span_id_var.reset(span_id_token)
```

---

### 2. Structured Logging with Request IDs

Update `app/core/logging_config.py`:

```python
"""
Logging Configuration with Request ID Support
"""
from __future__ import annotations

import logging
import sys
from typing import Any
import structlog


def configure_logging():
    """Configure structured logging with request ID support."""
    
    # Configure structlog
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer()
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )
    
    # Configure standard logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=logging.INFO,
    )


class RequestIDFilter(logging.Filter):
    """Add request ID to log records."""
    
    def filter(self, record: logging.LogRecord) -> bool:
        """Add request ID to record if available."""
        import contextvars
        
        request_id_var = contextvars.ContextVar("request_id", default=None)
        trace_id_var = contextvars.ContextVar("trace_id", default=None)
        
        record.request_id = request_id_var.get()
        record.trace_id = trace_id_var.get()
        
        return True
```

---

### 3. Update Error Responses

Update `app/core/error_responses.py` to include request ID:

```python
"""Error responses with request ID."""
from fastapi import Request


def create_error_response_from_request(
    request: Request,
    error: str,
    message: str,
    code: ErrorCode,
    category: ErrorCategory,
    status_code: int,
    details: list[ErrorDetail] | None = None
) -> ErrorResponse:
    """Create error response with request ID from request."""
    request_id = getattr(request.state, "request_id", None)
    
    return create_error_response(
        error=error,
        message=message,
        code=code,
        category=category,
        status_code=status_code,
        request_id=request_id,
        details=details
    )
```

---

## ✅ ACCEPTANCE CRITERIA

- [ ] Request ID middleware implemented
- [ ] Request IDs in all logs
- [ ] Request IDs in error responses
- [ ] Request IDs in response headers
- [ ] Distributed tracing headers supported
- [ ] Request ID propagation tested

---

## 🧪 TESTING

```python
# tests/test_request_id.py
"""Tests for request ID middleware."""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_request_id_generated():
    """Test request ID is generated."""
    response = client.get("/api/v1/health/status")
    assert "X-Request-ID" in response.headers
    assert response.headers["X-Request-ID"].startswith("req_")


def test_request_id_propagated():
    """Test request ID is propagated from header."""
    custom_id = "req_custom123"
    response = client.get(
        "/api/v1/health/status",
        headers={"X-Request-ID": custom_id}
    )
    assert response.headers["X-Request-ID"] == custom_id


def test_trace_id_in_headers():
    """Test trace ID is in response headers."""
    response = client.get("/api/v1/health/status")
    assert "X-Trace-ID" in response.headers
    assert "X-Span-ID" in response.headers


def test_request_id_in_error_response():
    """Test request ID is included in error responses."""
    response = client.get("/api/v1/nonexistent")
    data = response.json()
    assert "request_id" in data
```

---

## 📝 NOTES

- Include request ID in all logs
- Propagate request ID to external services
- Use request ID for debugging
- Monitor request ID coverage


