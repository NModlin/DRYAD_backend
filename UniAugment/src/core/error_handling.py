"""
Enhanced Error Handling and Logging System for DRYAD.AI Backend
Provides comprehensive error handling, structured logging, and recovery mechanisms.
"""

import logging
import traceback
import sys
import os
import json
import time
from datetime import datetime
from typing import Dict, Any, Optional, Union
from enum import Enum
from functools import wraps
from contextlib import contextmanager

from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel


class ErrorSeverity(str, Enum):
    """Error severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ErrorCategory(str, Enum):
    """Error categories for better classification."""
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    VALIDATION = "validation"
    DATABASE = "database"
    EXTERNAL_SERVICE = "external_service"
    LLM_PROVIDER = "llm_provider"
    VECTOR_STORE = "vector_store"
    TASK_QUEUE = "task_queue"
    SYSTEM = "system"
    UNKNOWN = "unknown"


class StructuredError(BaseModel):
    """Structured error model for consistent error reporting."""
    error_id: str
    timestamp: str
    severity: ErrorSeverity
    category: ErrorCategory
    message: str
    details: Optional[Dict[str, Any]] = None
    context: Optional[Dict[str, Any]] = None
    traceback: Optional[str] = None
    user_message: Optional[str] = None
    recovery_suggestions: Optional[list] = None


class ErrorHandler:
    """Centralized error handling system."""
    
    def __init__(self):
        self.error_count = 0
        self.error_history = []
        self.max_history = 1000
        
    def generate_error_id(self) -> str:
        """Generate unique error ID."""
        self.error_count += 1
        timestamp = int(time.time() * 1000)
        return f"ERR-{timestamp}-{self.error_count:04d}"
    
    def create_structured_error(
        self,
        message: str,
        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
        category: ErrorCategory = ErrorCategory.UNKNOWN,
        details: Optional[Dict[str, Any]] = None,
        context: Optional[Dict[str, Any]] = None,
        include_traceback: bool = True,
        user_message: Optional[str] = None,
        recovery_suggestions: Optional[list] = None
    ) -> StructuredError:
        """Create a structured error with all relevant information."""
        
        error_id = self.generate_error_id()
        timestamp = datetime.utcnow().isoformat()
        
        # Get traceback if requested
        tb = None
        if include_traceback:
            tb = traceback.format_exc() if sys.exc_info()[0] else None
        
        # Default user message based on category
        if not user_message:
            user_message = self._get_default_user_message(category)
        
        # Default recovery suggestions
        if not recovery_suggestions:
            recovery_suggestions = self._get_default_recovery_suggestions(category)
        
        error = StructuredError(
            error_id=error_id,
            timestamp=timestamp,
            severity=severity,
            category=category,
            message=message,
            details=details,
            context=context,
            traceback=tb,
            user_message=user_message,
            recovery_suggestions=recovery_suggestions
        )
        
        # Add to history
        self.error_history.append(error)
        if len(self.error_history) > self.max_history:
            self.error_history.pop(0)
        
        return error
    
    def _get_default_user_message(self, category: ErrorCategory) -> str:
        """Get default user-friendly message based on error category."""
        messages = {
            ErrorCategory.AUTHENTICATION: "Authentication failed. Please check your credentials.",
            ErrorCategory.AUTHORIZATION: "You don't have permission to access this resource.",
            ErrorCategory.VALIDATION: "The provided data is invalid. Please check your input.",
            ErrorCategory.DATABASE: "A database error occurred. Please try again later.",
            ErrorCategory.EXTERNAL_SERVICE: "An external service is temporarily unavailable.",
            ErrorCategory.LLM_PROVIDER: "The AI service is temporarily unavailable.",
            ErrorCategory.VECTOR_STORE: "The search service is temporarily unavailable.",
            ErrorCategory.TASK_QUEUE: "Background task processing is temporarily unavailable.",
            ErrorCategory.SYSTEM: "A system error occurred. Please try again later.",
            ErrorCategory.UNKNOWN: "An unexpected error occurred. Please try again later."
        }
        return messages.get(category, "An error occurred. Please try again later.")
    
    def _get_default_recovery_suggestions(self, category: ErrorCategory) -> list:
        """Get default recovery suggestions based on error category."""
        suggestions = {
            ErrorCategory.AUTHENTICATION: [
                "Verify your API key or credentials",
                "Check if your session has expired",
                "Try logging in again"
            ],
            ErrorCategory.AUTHORIZATION: [
                "Contact an administrator for access",
                "Verify you have the required permissions",
                "Check if your account is active"
            ],
            ErrorCategory.VALIDATION: [
                "Check the API documentation for required fields",
                "Verify data types and formats",
                "Ensure all required parameters are provided"
            ],
            ErrorCategory.DATABASE: [
                "Try the request again in a few moments",
                "Check if the system is under maintenance",
                "Contact support if the issue persists"
            ],
            ErrorCategory.EXTERNAL_SERVICE: [
                "Try again in a few minutes",
                "Check service status pages",
                "Use alternative features if available"
            ],
            ErrorCategory.LLM_PROVIDER: [
                "Check your LLM provider configuration",
                "Verify API keys and quotas",
                "Try using a different model or provider"
            ],
            ErrorCategory.VECTOR_STORE: [
                "Check if Weaviate is running",
                "Verify connection settings",
                "Try using basic search instead"
            ],
            ErrorCategory.TASK_QUEUE: [
                "Check if Redis is running",
                "Try the operation synchronously",
                "Contact support if urgent"
            ],
            ErrorCategory.SYSTEM: [
                "Try the request again",
                "Check system status",
                "Contact support with error ID"
            ]
        }
        return suggestions.get(category, [
            "Try the request again",
            "Check system status",
            "Contact support if the issue persists"
        ])
    
    def log_error(self, error: StructuredError, logger: Optional[logging.Logger] = None):
        """Log structured error with appropriate level."""
        if not logger:
            logger = logging.getLogger(__name__)
        
        # Create log message
        log_data = {
            "error_id": error.error_id,
            "severity": error.severity,
            "category": error.category,
            "message": error.message,
            "details": error.details,
            "context": error.context
        }
        
        log_message = f"[{error.error_id}] {error.message}"
        
        # Log with appropriate level
        if error.severity == ErrorSeverity.CRITICAL:
            logger.critical(log_message, extra={"structured_error": log_data})
        elif error.severity == ErrorSeverity.HIGH:
            logger.error(log_message, extra={"structured_error": log_data})
        elif error.severity == ErrorSeverity.MEDIUM:
            logger.warning(log_message, extra={"structured_error": log_data})
        else:
            logger.info(log_message, extra={"structured_error": log_data})
        
        # Log traceback separately if available
        if error.traceback:
            logger.debug(f"[{error.error_id}] Traceback: {error.traceback}")
    
    def get_error_stats(self) -> Dict[str, Any]:
        """Get error statistics."""
        if not self.error_history:
            return {"total_errors": 0}
        
        # Count by severity
        severity_counts = {}
        for severity in ErrorSeverity:
            severity_counts[severity.value] = sum(
                1 for error in self.error_history if error.severity == severity
            )
        
        # Count by category
        category_counts = {}
        for category in ErrorCategory:
            category_counts[category.value] = sum(
                1 for error in self.error_history if error.category == category
            )
        
        # Recent errors (last hour)
        one_hour_ago = datetime.utcnow().timestamp() - 3600
        recent_errors = [
            error for error in self.error_history
            if datetime.fromisoformat(error.timestamp).timestamp() > one_hour_ago
        ]
        
        return {
            "total_errors": len(self.error_history),
            "recent_errors_1h": len(recent_errors),
            "severity_breakdown": severity_counts,
            "category_breakdown": category_counts,
            "error_rate_1h": len(recent_errors) / 60,  # errors per minute
        }


# Global error handler instance
error_handler = ErrorHandler()


def handle_exceptions(
    severity: ErrorSeverity = ErrorSeverity.MEDIUM,
    category: ErrorCategory = ErrorCategory.UNKNOWN,
    user_message: Optional[str] = None,
    recovery_suggestions: Optional[list] = None,
    reraise: bool = False
):
    """Decorator for automatic exception handling."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                # Create structured error
                error = error_handler.create_structured_error(
                    message=str(e),
                    severity=severity,
                    category=category,
                    details={"function": func.__name__, "args": str(args), "kwargs": str(kwargs)},
                    user_message=user_message,
                    recovery_suggestions=recovery_suggestions
                )
                
                # Log error
                error_handler.log_error(error)
                
                if reraise:
                    raise
                
                # Return error response for API endpoints
                if hasattr(args[0], 'method'):  # Likely a Request object
                    return JSONResponse(
                        status_code=500,
                        content={
                            "error_id": error.error_id,
                            "message": error.user_message,
                            "recovery_suggestions": error.recovery_suggestions
                        }
                    )
                
                return None
        return wrapper
    return decorator


@contextmanager
def error_context(
    operation: str,
    severity: ErrorSeverity = ErrorSeverity.MEDIUM,
    category: ErrorCategory = ErrorCategory.UNKNOWN,
    **context_data
):
    """Context manager for error handling with additional context."""
    try:
        yield
    except Exception as e:
        error = error_handler.create_structured_error(
            message=f"Error in {operation}: {str(e)}",
            severity=severity,
            category=category,
            context={"operation": operation, **context_data}
        )
        error_handler.log_error(error)
        raise


def create_http_exception(
    error: StructuredError,
    status_code: int = 500
) -> HTTPException:
    """Create HTTPException from structured error."""
    return HTTPException(
        status_code=status_code,
        detail={
            "error_id": error.error_id,
            "message": error.user_message,
            "recovery_suggestions": error.recovery_suggestions,
            "timestamp": error.timestamp
        }
    )


# Convenience functions for common error types
def create_validation_error(message: str, details: Optional[Dict] = None) -> StructuredError:
    """Create validation error."""
    return error_handler.create_structured_error(
        message=message,
        severity=ErrorSeverity.LOW,
        category=ErrorCategory.VALIDATION,
        details=details
    )


def create_service_error(service: str, message: str, details: Optional[Dict] = None) -> StructuredError:
    """Create external service error."""
    return error_handler.create_structured_error(
        message=f"{service} error: {message}",
        severity=ErrorSeverity.HIGH,
        category=ErrorCategory.EXTERNAL_SERVICE,
        details={"service": service, **(details or {})}
    )


def create_system_error(message: str, details: Optional[Dict] = None) -> StructuredError:
    """Create system error."""
    return error_handler.create_structured_error(
        message=message,
        severity=ErrorSeverity.CRITICAL,
        category=ErrorCategory.SYSTEM,
        details=details
    )
