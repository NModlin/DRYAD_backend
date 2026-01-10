"""
Structured Logger Implementation

High-performance async logger with database persistence and Python logging integration.
"""

import logging
from datetime import datetime
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from .models import SystemLog
from .schemas import LogLevel


class StructuredLogger:
    """
    Structured logger with database persistence.
    
    Provides high-performance async logging with rich metadata,
    distributed tracing support, and Python logging integration.
    
    Example:
        logger = StructuredLogger(component="tool_registry")
        
        await logger.info(
            event_type="tool_registered",
            message="Tool registered successfully",
            metadata={"tool_id": "uuid", "tool_name": "executor"},
            trace_id="trace_123",
            agent_id="agent_456"
        )
    """
    
    def __init__(
        self,
        component: str,
        db_session: AsyncSession | None = None,
    ):
        """
        Initialize structured logger.
        
        Args:
            component: Component name for all logs from this logger
            db_session: Optional database session for persistence
        """
        self.component = component
        self.db_session = db_session
        self._python_logger = logging.getLogger(f"dryad.{component}")
    
    async def log(
        self,
        level: LogLevel | str,
        event_type: str,
        message: str,
        metadata: dict[str, Any] | None = None,
        trace_id: str | None = None,
        span_id: str | None = None,
        agent_id: str | None = None,
        task_id: str | None = None,
    ) -> SystemLog | None:
        """
        Write a structured log entry.
        
        Args:
            level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            event_type: Event type identifier
            message: Human-readable log message
            metadata: Additional structured metadata
            trace_id: Distributed trace ID
            span_id: Distributed span ID
            agent_id: Agent correlation ID
            task_id: Task correlation ID
            
        Returns:
            SystemLog instance if persisted, None otherwise
        """
        # Convert string level to enum
        if isinstance(level, str):
            level = LogLevel(level.upper())
        
        # Create log entry
        log_entry = SystemLog(
            level=level.value,
            component=self.component,
            event_type=event_type,
            message=message,
            log_metadata=metadata or {},
            trace_id=trace_id,
            span_id=span_id,
            agent_id=agent_id,
            task_id=task_id,
        )
        
        # Persist to database if session available
        if self.db_session:
            self.db_session.add(log_entry)
            await self.db_session.commit()
            await self.db_session.refresh(log_entry)
        
        # Also log to Python logger
        python_level = getattr(logging, level.value)
        self._python_logger.log(
            python_level,
            message,
            extra={
                "event_type": event_type,
                "metadata": metadata,
                "trace_id": trace_id,
                "span_id": span_id,
                "agent_id": agent_id,
                "task_id": task_id,
            },
        )
        
        return log_entry
    
    async def debug(
        self,
        event_type: str,
        message: str,
        **kwargs: Any,
    ) -> SystemLog | None:
        """Log DEBUG level message."""
        return await self.log(LogLevel.DEBUG, event_type, message, **kwargs)
    
    async def info(
        self,
        event_type: str,
        message: str,
        **kwargs: Any,
    ) -> SystemLog | None:
        """Log INFO level message."""
        return await self.log(LogLevel.INFO, event_type, message, **kwargs)
    
    async def warning(
        self,
        event_type: str,
        message: str,
        **kwargs: Any,
    ) -> SystemLog | None:
        """Log WARNING level message."""
        return await self.log(LogLevel.WARNING, event_type, message, **kwargs)
    
    async def error(
        self,
        event_type: str,
        message: str,
        **kwargs: Any,
    ) -> SystemLog | None:
        """Log ERROR level message."""
        return await self.log(LogLevel.ERROR, event_type, message, **kwargs)
    
    async def critical(
        self,
        event_type: str,
        message: str,
        **kwargs: Any,
    ) -> SystemLog | None:
        """Log CRITICAL level message."""
        return await self.log(LogLevel.CRITICAL, event_type, message, **kwargs)

    # Synchronous wrapper methods for non-async contexts
    def log_info(self, event_type: str, metadata: dict[str, Any] | None = None) -> None:
        """Synchronous INFO level logging (no database persistence)."""
        message = metadata.get("message", event_type) if metadata else event_type
        self._python_logger.info(message, extra={"event_type": event_type, "metadata": metadata})

    def log_debug(self, event_type: str, metadata: dict[str, Any] | None = None) -> None:
        """Synchronous DEBUG level logging (no database persistence)."""
        message = metadata.get("message", event_type) if metadata else event_type
        self._python_logger.debug(message, extra={"event_type": event_type, "metadata": metadata})

    def log_warning(self, event_type: str, metadata: dict[str, Any] | None = None) -> None:
        """Synchronous WARNING level logging (no database persistence)."""
        message = metadata.get("message", event_type) if metadata else event_type
        self._python_logger.warning(message, extra={"event_type": event_type, "metadata": metadata})

    def log_error(self, event_type: str, metadata: dict[str, Any] | None = None) -> None:
        """Synchronous ERROR level logging (no database persistence)."""
        message = metadata.get("message", event_type) if metadata else event_type
        self._python_logger.error(message, extra={"event_type": event_type, "metadata": metadata})

    def log_critical(self, event_type: str, metadata: dict[str, Any] | None = None) -> None:
        """Synchronous CRITICAL level logging (no database persistence)."""
        message = metadata.get("message", event_type) if metadata else event_type
        self._python_logger.critical(message, extra={"event_type": event_type, "metadata": metadata})


class DatabaseLogHandler(logging.Handler):
    """
    Python logging handler that writes to database.
    
    Allows standard Python logging to be captured in structured logs.
    
    Example:
        import logging
        from app.services.logging.logger import DatabaseLogHandler
        
        handler = DatabaseLogHandler(component="my_component", db_session=session)
        logging.getLogger().addHandler(handler)
        
        logging.info("This will be stored in database")
    """
    
    def __init__(
        self,
        component: str,
        db_session: AsyncSession,
        level: int = logging.INFO,
    ):
        """
        Initialize database log handler.
        
        Args:
            component: Component name for logs
            db_session: Database session for persistence
            level: Minimum log level to capture
        """
        super().__init__(level)
        self.component = component
        self.db_session = db_session
    
    def emit(self, record: logging.LogRecord) -> None:
        """
        Emit a log record to database.
        
        Args:
            record: Python logging record
        """
        try:
            # Map Python log level to our LogLevel enum
            level_map = {
                logging.DEBUG: LogLevel.DEBUG,
                logging.INFO: LogLevel.INFO,
                logging.WARNING: LogLevel.WARNING,
                logging.ERROR: LogLevel.ERROR,
                logging.CRITICAL: LogLevel.CRITICAL,
            }
            level = level_map.get(record.levelno, LogLevel.INFO)
            
            # Extract metadata from record
            metadata = {
                "filename": record.filename,
                "lineno": record.lineno,
                "funcName": record.funcName,
                "pathname": record.pathname,
            }
            
            # Add any extra fields
            if hasattr(record, "metadata"):
                metadata.update(record.metadata)
            
            # Create log entry
            log_entry = SystemLog(
                level=level.value,
                component=self.component,
                event_type=getattr(record, "event_type", "python_log"),
                message=self.format(record),
                log_metadata=metadata,
                trace_id=getattr(record, "trace_id", None),
                span_id=getattr(record, "span_id", None),
                agent_id=getattr(record, "agent_id", None),
                task_id=getattr(record, "task_id", None),
            )
            
            # Note: This is synchronous - for production, consider async queue
            self.db_session.add(log_entry)
            
        except Exception:
            self.handleError(record)

