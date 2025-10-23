"""
Structured Logging Configuration for DRYAD.AI Backend
Provides comprehensive logging with structured output, multiple handlers, and performance monitoring.
"""

import logging
import logging.handlers
import json
import os
import sys
import time
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from pathlib import Path


class StructuredFormatter(logging.Formatter):
    """Custom formatter for structured JSON logging."""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as structured JSON."""

        # Base log data
        log_data = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
            "process_id": os.getpid(),
            "thread_id": record.thread,
        }
        
        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = {
                "type": record.exc_info[0].__name__ if record.exc_info[0] else None,
                "message": str(record.exc_info[1]) if record.exc_info[1] else None,
                "traceback": self.formatException(record.exc_info) if record.exc_info else None
            }
        
        # Add structured error data if present
        if hasattr(record, 'structured_error'):
            log_data["structured_error"] = record.structured_error
        
        # Add extra fields
        for key, value in record.__dict__.items():
            if key not in ['name', 'msg', 'args', 'levelname', 'levelno', 'pathname', 
                          'filename', 'module', 'lineno', 'funcName', 'created', 'msecs',
                          'relativeCreated', 'thread', 'threadName', 'processName', 'process',
                          'getMessage', 'exc_info', 'exc_text', 'stack_info', 'structured_error']:
                log_data[key] = value
        
        return json.dumps(log_data, default=str, ensure_ascii=False)


class PerformanceFilter(logging.Filter):
    """Filter to add performance metrics to log records."""
    
    def __init__(self):
        super().__init__()
        self.start_time = time.time()
        self.request_count = 0
    
    def filter(self, record: logging.LogRecord) -> bool:
        """Add performance metrics to log record."""
        self.request_count += 1
        record.uptime = time.time() - self.start_time
        record.request_count = self.request_count
        return True


class LoggingConfig:
    """Centralized logging configuration."""
    
    def __init__(self):
        # Default to WARNING level for console (only show warnings and errors)
        self.log_level = os.getenv("LOG_LEVEL", "WARNING").upper()
        self.log_format = os.getenv("LOG_FORMAT", "structured")  # structured or simple
        self.log_dir = Path(os.getenv("LOG_DIR", "logs"))
        self.max_file_size = int(os.getenv("LOG_MAX_FILE_SIZE", "10485760"))  # 10MB
        self.backup_count = int(os.getenv("LOG_BACKUP_COUNT", "5"))
        self.enable_console = os.getenv("LOG_ENABLE_CONSOLE", "true").lower() == "true"
        self.enable_file = os.getenv("LOG_ENABLE_FILE", "true").lower() == "true"
        
        # Create log directory
        self.log_dir.mkdir(exist_ok=True)
    
    def setup_logging(self):
        """Set up comprehensive logging configuration."""
        
        # Get root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(getattr(logging, self.log_level))
        
        # Clear existing handlers
        root_logger.handlers.clear()
        
        # Performance filter
        perf_filter = PerformanceFilter()
        
        # Console handler with UTF-8 encoding for Windows compatibility
        if self.enable_console:
            # Reconfigure stdout to use UTF-8 encoding on Windows
            if sys.platform == 'win32':
                import io
                sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(getattr(logging, self.log_level))
            console_handler.addFilter(perf_filter)
            
            if self.log_format == "structured":
                console_handler.setFormatter(StructuredFormatter())
            else:
                console_handler.setFormatter(logging.Formatter(
                    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
                ))
            
            root_logger.addHandler(console_handler)
        
        # File handlers
        if self.enable_file:
            # Main application log
            app_handler = logging.handlers.RotatingFileHandler(
                self.log_dir / "gremlins_app.log",
                maxBytes=self.max_file_size,
                backupCount=self.backup_count
            )
            app_handler.setLevel(getattr(logging, self.log_level))
            app_handler.addFilter(perf_filter)
            app_handler.setFormatter(StructuredFormatter())
            root_logger.addHandler(app_handler)
            
            # Error log (errors and above only)
            error_handler = logging.handlers.RotatingFileHandler(
                self.log_dir / "gremlins_errors.log",
                maxBytes=self.max_file_size,
                backupCount=self.backup_count
            )
            error_handler.setLevel(logging.ERROR)
            error_handler.addFilter(perf_filter)
            error_handler.setFormatter(StructuredFormatter())
            root_logger.addHandler(error_handler)
            
            # Access log for API requests
            access_logger = logging.getLogger("access")
            access_handler = logging.handlers.RotatingFileHandler(
                self.log_dir / "gremlins_access.log",
                maxBytes=self.max_file_size,
                backupCount=self.backup_count
            )
            access_handler.setLevel(logging.INFO)
            access_handler.setFormatter(StructuredFormatter())
            access_logger.addHandler(access_handler)
            access_logger.setLevel(logging.INFO)
            access_logger.propagate = False
        
        # Set specific logger levels
        self._configure_specific_loggers()
        
        # Log startup message
        logger = logging.getLogger(__name__)
        logger.info("Logging system initialized", extra={
            "log_level": self.log_level,
            "log_format": self.log_format,
            "console_enabled": self.enable_console,
            "file_enabled": self.enable_file,
            "log_directory": str(self.log_dir)
        })
    
    def _configure_specific_loggers(self):
        """Configure specific loggers with appropriate levels."""

        # Silence all noise - only show warnings and errors
        logging.getLogger("uvicorn").setLevel(logging.ERROR)
        logging.getLogger("uvicorn.access").setLevel(logging.ERROR)
        logging.getLogger("uvicorn.error").setLevel(logging.WARNING)
        logging.getLogger("fastapi").setLevel(logging.WARNING)
        logging.getLogger("sqlalchemy").setLevel(logging.WARNING)
        logging.getLogger("alembic").setLevel(logging.WARNING)
        logging.getLogger("httpx").setLevel(logging.WARNING)
        logging.getLogger("httpcore").setLevel(logging.WARNING)

        # Silence metrics and performance logging completely
        logging.getLogger("metrics").setLevel(logging.ERROR)
        logging.getLogger("app.core.performance_optimizer").setLevel(logging.ERROR)
        logging.getLogger("app.core.monitoring").setLevel(logging.ERROR)

        # Set our modules to WARNING level (only show warnings and errors)
        logging.getLogger("app.core").setLevel(logging.WARNING)
        logging.getLogger("app.api").setLevel(logging.WARNING)
        logging.getLogger("app.services").setLevel(logging.WARNING)
        logging.getLogger("app.main").setLevel(logging.WARNING)


class RequestLogger:
    """Middleware for logging HTTP requests."""
    
    def __init__(self):
        self.logger = logging.getLogger("access")
    
    async def log_request(self, request, response, process_time: float):
        """Log HTTP request with structured data."""
        
        # Extract client info
        client_ip = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("user-agent", "unknown")
        
        # Extract user info if available
        user_id = getattr(request.state, 'user_id', None)
        
        log_data = {
            "method": request.method,
            "url": str(request.url),
            "path": request.url.path,
            "query_params": dict(request.query_params),
            "status_code": response.status_code,
            "process_time_ms": round(process_time * 1000, 2),
            "client_ip": client_ip,
            "user_agent": user_agent,
            "user_id": user_id,
            "request_size": request.headers.get("content-length", 0),
            "response_size": response.headers.get("content-length", 0) if hasattr(response, 'headers') else 0
        }
        
        # Log with appropriate level based on status code
        if response.status_code >= 500:
            self.logger.error("HTTP Request", extra=log_data)
        elif response.status_code >= 400:
            self.logger.warning("HTTP Request", extra=log_data)
        else:
            self.logger.info("HTTP Request", extra=log_data)


class MetricsLogger:
    """Logger for application metrics."""
    
    def __init__(self):
        self.logger = logging.getLogger("metrics")
        self.metrics = {}
    
    def increment_counter(self, name: str, value: int = 1, tags: Optional[Dict[str, str]] = None):
        """Increment a counter metric."""
        self.logger.info("Counter metric", extra={
            "metric_type": "counter",
            "metric_name": name,
            "value": value,
            "tags": tags or {}
        })
    
    def record_gauge(self, name: str, value: float, tags: Optional[Dict[str, str]] = None):
        """Record a gauge metric."""
        self.logger.info("Gauge metric", extra={
            "metric_type": "gauge",
            "metric_name": name,
            "value": value,
            "tags": tags or {}
        })
    
    def record_histogram(self, name: str, value: float, tags: Optional[Dict[str, str]] = None):
        """Record a histogram metric."""
        self.logger.info("Histogram metric", extra={
            "metric_type": "histogram",
            "metric_name": name,
            "value": value,
            "tags": tags or {}
        })
    
    def record_timing(self, name: str, duration_ms: float, tags: Optional[Dict[str, str]] = None):
        """Record a timing metric."""
        self.logger.info("Timing metric", extra={
            "metric_type": "timing",
            "metric_name": name,
            "duration_ms": duration_ms,
            "tags": tags or {}
        })


# Global instances
logging_config = LoggingConfig()
request_logger = RequestLogger()
metrics_logger = MetricsLogger()


def setup_logging():
    """Initialize logging system."""
    logging_config.setup_logging()


def get_logger(name: str) -> logging.Logger:
    """Get logger with consistent configuration."""
    return logging.getLogger(name)


# Context manager for timing operations
class LogTimer:
    """Context manager for timing operations with logging."""
    
    def __init__(self, operation: str, logger: Optional[logging.Logger] = None):
        self.operation = operation
        self.logger = logger or logging.getLogger(__name__)
        self.start_time = None
    
    def __enter__(self):
        self.start_time = time.time()
        self.logger.debug(f"Starting {self.operation}")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = time.time() - self.start_time
        duration_ms = duration * 1000
        
        if exc_type:
            self.logger.error(f"{self.operation} failed after {duration_ms:.2f}ms", extra={
                "operation": self.operation,
                "duration_ms": duration_ms,
                "exception_type": exc_type.__name__,
                "exception_message": str(exc_val)
            })
        else:
            self.logger.info(f"{self.operation} completed in {duration_ms:.2f}ms", extra={
                "operation": self.operation,
                "duration_ms": duration_ms
            })
        
        # Record timing metric
        metrics_logger.record_timing(f"{self.operation.lower().replace(' ', '_')}_duration", duration_ms)


# Decorator for automatic timing
def log_timing(operation: str = None):
    """Decorator for automatic operation timing."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            op_name = operation or f"{func.__module__}.{func.__name__}"
            with LogTimer(op_name):
                return func(*args, **kwargs)
        return wrapper
    return decorator
