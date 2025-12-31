"""
Structured logging configuration for Uni0 application
Uses structlog for JSON logging with request ID tracking
"""

import structlog
import logging
import uuid
from typing import Optional
from contextvars import ContextVar
from pythonjsonlogger import jsonlogger

# Context variable for request ID
request_id_var: ContextVar[Optional[str]] = ContextVar('request_id', default=None)


def get_request_id() -> Optional[str]:
    """Get current request ID from context"""
    return request_id_var.get()


def set_request_id(request_id: str) -> None:
    """Set request ID in context"""
    request_id_var.set(request_id)


def generate_request_id() -> str:
    """Generate a new request ID"""
    return str(uuid.uuid4())


def add_request_id(logger, method_name, event_dict):
    """Add request ID to log event"""
    request_id = get_request_id()
    if request_id:
        event_dict['request_id'] = request_id
    return event_dict


def configure_logging(log_level: str = "INFO", json_logs: bool = True):
    """Configure structured logging with structlog"""
    
    # Configure standard logging
    logging.basicConfig(
        level=getattr(logging, log_level),
        format='%(message)s'
    )
    
    # Configure structlog
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            add_request_id,  # Add request ID to all logs
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer() if json_logs else structlog.dev.ConsoleRenderer(),
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str = __name__):
    """Get a structured logger"""
    return structlog.get_logger(name)


class RequestIDMiddleware:
    """Middleware to add request ID to all requests"""
    
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            # Generate or extract request ID
            request_id = scope.get("headers", {})
            request_id_header = None
            
            # Look for X-Request-ID header
            for header_name, header_value in scope.get("headers", []):
                if header_name.lower() == b"x-request-id":
                    request_id_header = header_value.decode()
                    break
            
            # Use existing request ID or generate new one
            request_id = request_id_header or generate_request_id()
            set_request_id(request_id)
            
            # Add request ID to response headers
            async def send_with_request_id(message):
                if message["type"] == "http.response.start":
                    headers = list(message.get("headers", []))
                    headers.append((b"x-request-id", request_id.encode()))
                    message["headers"] = headers
                await send(message)
            
            await self.app(scope, receive, send_with_request_id)
        else:
            await self.app(scope, receive, send)


def log_request(logger, method: str, path: str, status_code: int, duration: float):
    """Log HTTP request"""
    logger.info(
        "http_request",
        method=method,
        path=path,
        status_code=status_code,
        duration_ms=duration * 1000
    )


def log_error(logger, error_type: str, message: str, **kwargs):
    """Log error with context"""
    logger.error(
        "error",
        error_type=error_type,
        message=message,
        **kwargs
    )


def log_auth_event(logger, event: str, university_id: str, success: bool, **kwargs):
    """Log authentication event"""
    logger.info(
        "auth_event",
        event=event,
        university_id=university_id,
        success=success,
        **kwargs
    )


def log_database_operation(logger, operation: str, table: str, duration: float, **kwargs):
    """Log database operation"""
    logger.info(
        "db_operation",
        operation=operation,
        table=table,
        duration_ms=duration * 1000,
        **kwargs
    )

