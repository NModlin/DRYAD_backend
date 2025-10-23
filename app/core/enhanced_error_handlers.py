"""
Enhanced Error Handlers for DRYAD.AI Backend
Replaces the basic error handlers with structured error handling.
"""

import logging
from typing import Union

from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import SQLAlchemyError

from app.core.error_handling import (
    error_handler, ErrorCategory, ErrorSeverity, 
    create_validation_error, create_service_error, create_system_error
)
from app.core.logging_config import get_logger

logger = get_logger(__name__)


async def enhanced_http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Enhanced HTTP exception handler with structured errors."""
    
    # Determine error category based on status code
    if exc.status_code == 401:
        category = ErrorCategory.AUTHENTICATION
        severity = ErrorSeverity.MEDIUM
    elif exc.status_code == 403:
        category = ErrorCategory.AUTHORIZATION
        severity = ErrorSeverity.MEDIUM
    elif exc.status_code == 422:
        category = ErrorCategory.VALIDATION
        severity = ErrorSeverity.LOW
    elif exc.status_code >= 500:
        category = ErrorCategory.SYSTEM
        severity = ErrorSeverity.HIGH
    else:
        category = ErrorCategory.UNKNOWN
        severity = ErrorSeverity.MEDIUM
    
    # Create structured error
    error = error_handler.create_structured_error(
        message=f"HTTP {exc.status_code}: {exc.detail}",
        severity=severity,
        category=category,
        context={
            "status_code": exc.status_code,
            "method": request.method,
            "path": request.url.path,
            "client_ip": request.client.host if request.client else "unknown"
        },
        include_traceback=False
    )
    
    # Log error
    error_handler.log_error(error, logger)
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error_id": error.error_id,
            "message": error.user_message,
            "recovery_suggestions": error.recovery_suggestions,
            "timestamp": error.timestamp
        }
    )


async def enhanced_validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Enhanced validation exception handler."""
    
    # Extract validation details
    validation_errors = []
    for error in exc.errors():
        validation_errors.append({
            "field": ".".join(str(x) for x in error["loc"]),
            "message": error["msg"],
            "type": error["type"]
        })
    
    # Create structured error
    error = create_validation_error(
        message=f"Validation failed for {len(validation_errors)} field(s)",
        details={
            "validation_errors": validation_errors,
            "method": request.method,
            "path": request.url.path
        }
    )
    
    # Log error
    error_handler.log_error(error, logger)
    
    return JSONResponse(
        status_code=422,
        content={
            "error_id": error.error_id,
            "message": "Invalid input data provided",
            "validation_errors": validation_errors,
            "recovery_suggestions": [
                "Check the API documentation for required fields",
                "Verify data types and formats",
                "Ensure all required parameters are provided"
            ],
            "timestamp": error.timestamp
        }
    )


async def enhanced_sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError) -> JSONResponse:
    """Enhanced SQLAlchemy exception handler."""
    
    # Create structured error
    error = error_handler.create_structured_error(
        message=f"Database error: {str(exc)}",
        severity=ErrorSeverity.HIGH,
        category=ErrorCategory.DATABASE,
        context={
            "method": request.method,
            "path": request.url.path,
            "exception_type": type(exc).__name__
        }
    )
    
    # Log error
    error_handler.log_error(error, logger)
    
    return JSONResponse(
        status_code=500,
        content={
            "error_id": error.error_id,
            "message": error.user_message,
            "recovery_suggestions": error.recovery_suggestions,
            "timestamp": error.timestamp
        }
    )


async def enhanced_general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Enhanced general exception handler for unexpected errors."""
    
    # Create structured error
    error = create_system_error(
        message=f"Unexpected error: {str(exc)}",
        details={
            "exception_type": type(exc).__name__,
            "method": request.method,
            "path": request.url.path,
            "client_ip": request.client.host if request.client else "unknown"
        }
    )
    
    # Log error
    error_handler.log_error(error, logger)
    
    return JSONResponse(
        status_code=500,
        content={
            "error_id": error.error_id,
            "message": error.user_message,
            "recovery_suggestions": error.recovery_suggestions,
            "timestamp": error.timestamp
        }
    )


async def circuit_breaker_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handler for circuit breaker exceptions."""
    
    # Extract service name from exception if available
    service_name = getattr(exc, 'service_name', 'unknown service')
    
    # Create structured error
    error = create_service_error(
        service=service_name,
        message=f"Service temporarily unavailable due to circuit breaker",
        details={
            "method": request.method,
            "path": request.url.path,
            "service": service_name
        }
    )
    
    # Log error
    error_handler.log_error(error, logger)
    
    return JSONResponse(
        status_code=503,
        content={
            "error_id": error.error_id,
            "message": f"The {service_name} is temporarily unavailable",
            "recovery_suggestions": [
                "Try again in a few minutes",
                "Check service status",
                "Use alternative features if available"
            ],
            "timestamp": error.timestamp
        }
    )


async def llm_provider_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handler for LLM provider exceptions."""
    
    # Create structured error
    error = error_handler.create_structured_error(
        message=f"LLM provider error: {str(exc)}",
        severity=ErrorSeverity.HIGH,
        category=ErrorCategory.LLM_PROVIDER,
        context={
            "method": request.method,
            "path": request.url.path,
            "exception_type": type(exc).__name__
        }
    )
    
    # Log error
    error_handler.log_error(error, logger)
    
    return JSONResponse(
        status_code=503,
        content={
            "error_id": error.error_id,
            "message": "AI service is temporarily unavailable",
            "recovery_suggestions": [
                "Check your LLM provider configuration",
                "Verify API keys and quotas",
                "Try using a different model or provider",
                "Contact support if the issue persists"
            ],
            "timestamp": error.timestamp
        }
    )


async def vector_store_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handler for vector store exceptions."""
    
    # Create structured error
    error = error_handler.create_structured_error(
        message=f"Vector store error: {str(exc)}",
        severity=ErrorSeverity.HIGH,
        category=ErrorCategory.VECTOR_STORE,
        context={
            "method": request.method,
            "path": request.url.path,
            "exception_type": type(exc).__name__
        }
    )
    
    # Log error
    error_handler.log_error(error, logger)
    
    return JSONResponse(
        status_code=503,
        content={
            "error_id": error.error_id,
            "message": "Search service is temporarily unavailable",
            "recovery_suggestions": [
                "Check if Weaviate is running",
                "Verify connection settings",
                "Try using basic search instead",
                "Contact support if the issue persists"
            ],
            "timestamp": error.timestamp
        }
    )


# Error statistics endpoint
async def get_error_statistics() -> dict:
    """Get error statistics for monitoring."""
    return error_handler.get_error_stats()


# Health check for error handling system
async def error_handling_health_check() -> dict:
    """Health check for error handling system."""
    try:
        stats = error_handler.get_error_stats()
        
        # Check error rates
        recent_errors = stats.get("recent_errors_1h", 0)
        error_rate = stats.get("error_rate_1h", 0)
        
        # Determine health status
        if error_rate > 10:  # More than 10 errors per minute
            status = "unhealthy"
            issues = ["High error rate detected"]
        elif error_rate > 5:  # More than 5 errors per minute
            status = "degraded"
            issues = ["Elevated error rate"]
        else:
            status = "healthy"
            issues = []
        
        return {
            "status": status,
            "error_rate_1h": error_rate,
            "recent_errors_1h": recent_errors,
            "total_errors": stats.get("total_errors", 0),
            "issues": issues,
            "timestamp": time.time()
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error handling health check failed: {str(e)}",
            "timestamp": time.time()
        }
