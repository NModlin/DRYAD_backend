"""
Logging Configuration for DRYAD.AI Backend
Structured logging with JSON format for production
"""

import logging
import logging.handlers
import sys
from pathlib import Path
from typing import Any, Dict
import json
from datetime import datetime


class JSONFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging"""

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON"""
        log_data: Dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # Add extra fields
        if hasattr(record, "user_id"):
            log_data["user_id"] = record.user_id
        if hasattr(record, "request_id"):
            log_data["request_id"] = record.request_id
        if hasattr(record, "ip_address"):
            log_data["ip_address"] = record.ip_address
        if hasattr(record, "endpoint"):
            log_data["endpoint"] = record.endpoint
        if hasattr(record, "method"):
            log_data["method"] = record.method
        if hasattr(record, "status_code"):
            log_data["status_code"] = record.status_code
        if hasattr(record, "duration"):
            log_data["duration_ms"] = record.duration

        return json.dumps(log_data)


class ColoredFormatter(logging.Formatter):
    """Colored formatter for console output"""

    COLORS = {
        "DEBUG": "\033[36m",  # Cyan
        "INFO": "\033[32m",  # Green
        "WARNING": "\033[33m",  # Yellow
        "ERROR": "\033[31m",  # Red
        "CRITICAL": "\033[35m",  # Magenta
    }
    RESET = "\033[0m"

    def format(self, record: logging.LogRecord) -> str:
        """Format log record with colors"""
        color = self.COLORS.get(record.levelname, self.RESET)
        record.levelname = f"{color}{record.levelname}{self.RESET}"
        return super().format(record)


def setup_logging(
    log_level: str = "INFO",
    log_file: str = "logs/DRYAD.AI.log",
    log_format: str = "json",
    max_bytes: int = 10485760,  # 10MB
    backup_count: int = 5,
) -> None:
    """
    Set up logging configuration
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Path to log file
        log_format: Format (json or text)
        max_bytes: Maximum log file size before rotation
        backup_count: Number of backup files to keep
    """
    # Create logs directory
    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))

    # Remove existing handlers
    root_logger.handlers.clear()

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)

    if log_format == "json":
        console_handler.setFormatter(JSONFormatter())
    else:
        console_formatter = ColoredFormatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        console_handler.setFormatter(console_formatter)

    root_logger.addHandler(console_handler)

    # File handler with rotation
    file_handler = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding="utf-8",
    )
    file_handler.setLevel(logging.DEBUG)

    if log_format == "json":
        file_handler.setFormatter(JSONFormatter())
    else:
        file_formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        file_handler.setFormatter(file_formatter)

    root_logger.addHandler(file_handler)

    # Error file handler (separate file for errors)
    error_file = log_path.parent / "errors.log"
    error_handler = logging.handlers.RotatingFileHandler(
        error_file,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding="utf-8",
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(JSONFormatter() if log_format == "json" else file_formatter)
    root_logger.addHandler(error_handler)

    # Set levels for third-party loggers
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("fastapi").setLevel(logging.INFO)
    logging.getLogger("sqlalchemy").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)

    logging.info(f"Logging configured: level={log_level}, format={log_format}, file={log_file}")


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance
    
    Args:
        name: Logger name (usually __name__)
    
    Returns:
        Logger instance
    """
    return logging.getLogger(name)


class RequestLogger:
    """Middleware for logging HTTP requests"""

    def __init__(self, logger: logging.Logger):
        self.logger = logger

    def log_request(
        self,
        method: str,
        path: str,
        status_code: int,
        duration_ms: float,
        user_id: str = None,
        ip_address: str = None,
        request_id: str = None,
    ) -> None:
        """Log HTTP request"""
        extra = {
            "method": method,
            "endpoint": path,
            "status_code": status_code,
            "duration": duration_ms,
        }

        if user_id:
            extra["user_id"] = user_id
        if ip_address:
            extra["ip_address"] = ip_address
        if request_id:
            extra["request_id"] = request_id

        level = logging.INFO
        if status_code >= 500:
            level = logging.ERROR
        elif status_code >= 400:
            level = logging.WARNING

        self.logger.log(
            level,
            f"{method} {path} {status_code} {duration_ms:.2f}ms",
            extra=extra,
        )


class SelfHealingLogger:
    """Logger for self-healing system"""

    def __init__(self, logger: logging.Logger):
        self.logger = logger

    def log_task_created(self, task_id: str, error_type: str, file_path: str) -> None:
        """Log task creation"""
        self.logger.info(
            f"Self-healing task created: {task_id}",
            extra={
                "task_id": task_id,
                "error_type": error_type,
                "file_path": file_path,
                "event": "task_created",
            },
        )

    def log_task_approved(self, task_id: str, approver: str) -> None:
        """Log task approval"""
        self.logger.info(
            f"Self-healing task approved: {task_id}",
            extra={
                "task_id": task_id,
                "approver": approver,
                "event": "task_approved",
            },
        )

    def log_task_completed(self, task_id: str, duration_seconds: float) -> None:
        """Log task completion"""
        self.logger.info(
            f"Self-healing task completed: {task_id}",
            extra={
                "task_id": task_id,
                "duration": duration_seconds * 1000,  # Convert to ms
                "event": "task_completed",
            },
        )

    def log_task_failed(self, task_id: str, error: str) -> None:
        """Log task failure"""
        self.logger.error(
            f"Self-healing task failed: {task_id}",
            extra={
                "task_id": task_id,
                "error": error,
                "event": "task_failed",
            },
        )


# Example usage
if __name__ == "__main__":
    # Set up logging
    setup_logging(log_level="DEBUG", log_format="json")

    # Get logger
    logger = get_logger(__name__)

    # Test logging
    logger.debug("This is a debug message")
    logger.info("This is an info message")
    logger.warning("This is a warning message")
    logger.error("This is an error message")
    logger.critical("This is a critical message")

    # Test with extra fields
    logger.info(
        "User logged in",
        extra={
            "user_id": "user123",
            "ip_address": "192.168.1.1",
            "request_id": "req-abc-123",
        },
    )

    # Test exception logging
    try:
        raise ValueError("Test exception")
    except Exception as e:
        logger.exception("An error occurred")

