"""
Global Error Handlers for DRYAD.AI API

Centralized error handling middleware and exception handlers to ensure
consistent error responses across all API endpoints.
"""

import logging
import traceback
from typing import Dict, Any, List

from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError
from sqlalchemy.exc import SQLAlchemyError

from app.core.exceptions import (
    ErrorCode, ErrorSeverity, ErrorResponse, DRYADAIException,
    ValidationException, DatabaseException, ValidationErrorDetail
)

logger = logging.getLogger(__name__)


async def gremlins_exception_handler(request: Request, exc: DRYADAIException) -> JSONResponse:
    """
    Handler for custom DRYAD.AI exceptions.
    
    Returns structured error responses with comprehensive error information.
    """
    logger.error(
        f"DRYAD.AI Exception: {exc.error_response.error_code} - {exc.error_response.error_message}",
        extra={
            "request_id": exc.error_response.request_id,
            "error_code": exc.error_response.error_code,
            "severity": exc.error_response.severity,
            "category": exc.error_response.category,
            "processing_step": exc.error_response.processing_step
        }
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content=exc.error_response.model_dump(),
        headers={"X-Request-ID": exc.error_response.request_id}
    )


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """
    Handler for standard FastAPI HTTPExceptions.
    
    Converts standard HTTPExceptions to structured DRYAD.AI error format.
    """
    # Map HTTP status codes to DRYAD.AI error codes
    status_code_map = {
        400: ErrorCode.INVALID_REQUEST,
        401: ErrorCode.AUTHENTICATION_REQUIRED,
        403: ErrorCode.INSUFFICIENT_PERMISSIONS,
        404: ErrorCode.RESOURCE_NOT_FOUND,
        429: ErrorCode.RATE_LIMIT_EXCEEDED,
        500: ErrorCode.INTERNAL_SERVER_ERROR,
        503: ErrorCode.EXTERNAL_SERVICE_UNAVAILABLE
    }
    
    error_code = status_code_map.get(exc.status_code, ErrorCode.INTERNAL_SERVER_ERROR)
    
    # Determine severity based on status code
    if exc.status_code < 500:
        severity = ErrorSeverity.LOW if exc.status_code == 429 else ErrorSeverity.MEDIUM
    else:
        severity = ErrorSeverity.HIGH
    
    error_response = ErrorResponse(
        error_code=error_code,
        error_message=str(exc.detail),
        severity=severity,
        category="http_error",
        suggested_action=_get_suggested_action_for_status(exc.status_code)
    )

    # Add detail field for backward compatibility with tests
    response_dict = error_response.model_dump()
    response_dict["detail"] = str(exc.detail)
    
    logger.warning(
        f"HTTP Exception: {exc.status_code} - {exc.detail}",
        extra={
            "request_id": error_response.request_id,
            "status_code": exc.status_code,
            "error_code": error_code
        }
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content=response_dict,
        headers={"X-Request-ID": error_response.request_id}
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """
    Handler for Pydantic validation errors.
    
    Provides detailed field-level validation error information.
    """
    validation_errors = []
    
    for error in exc.errors():
        field_path = " -> ".join(str(loc) for loc in error["loc"])
        
        # Handle bytes data that can't be JSON serialized
        invalid_value = error.get("input")
        if isinstance(invalid_value, bytes):
            invalid_value = f"<bytes: {invalid_value.decode('utf-8', errors='replace')[:100]}...>"

        validation_errors.append(ValidationErrorDetail(
            field=field_path,
            message=error["msg"],
            invalid_value=invalid_value,
            expected_type=error.get("type")
        ))
    
    error_message = f"Validation failed for {len(validation_errors)} field(s)"
    
    validation_exc = ValidationException(
        error_message=error_message,
        validation_errors=validation_errors,
        error_details="Please check the validation errors and correct the invalid fields"
    )
    
    logger.warning(
        f"Validation Error: {error_message}",
        extra={
            "request_id": validation_exc.error_response.request_id,
            "validation_errors": [ve.model_dump() for ve in validation_errors]
        }
    )
    
    # Add detail field for backward compatibility with tests
    response_dict = validation_exc.error_response.model_dump()
    response_dict["detail"] = error_message

    return JSONResponse(
        status_code=validation_exc.status_code,
        content=response_dict,
        headers={"X-Request-ID": validation_exc.error_response.request_id}
    )


async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError) -> JSONResponse:
    """
    Handler for SQLAlchemy database errors.

    Converts database errors to structured error responses.
    """
    error_message = "Database operation failed"
    error_details = str(exc)

    # Don't expose sensitive database details in production
    if "production" in str(request.url).lower():
        error_details = "A database error occurred. Please contact support."

    db_exc = DatabaseException(
        error_message=error_message,
        error_details=error_details
    )

    logger.error(
        f"Database Error: {error_message} - {type(exc).__name__}: {str(exc)}",
        extra={
            "request_id": db_exc.error_response.request_id,
            "exception_type": type(exc).__name__,
            "error_details": str(exc),
            "traceback": traceback.format_exc()
        }
    )
    
    return JSONResponse(
        status_code=db_exc.status_code,
        content=db_exc.error_response.model_dump(),
        headers={"X-Request-ID": db_exc.error_response.request_id}
    )


async def service_unavailable_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Handler for service unavailable exceptions (circuit breaker, external services).

    Provides helpful error messages when services are degraded or unavailable.
    """
    from app.core.circuit_breaker import CircuitBreakerOpenException
    from app.core.feature_flags import feature_flags

    # Check if this is a circuit breaker exception
    if isinstance(exc, CircuitBreakerOpenException):
        # Get current system capabilities
        capabilities = feature_flags.get_system_capabilities()

        error_response = ErrorResponse(
            error_code=ErrorCode.SERVICE_UNAVAILABLE,
            error_message=f"Service temporarily unavailable: {exc.service_name}",
            error_details=f"The {exc.service_name} service is currently experiencing issues. "
                         f"Circuit breaker is open to prevent cascading failures.",
            severity=ErrorSeverity.HIGH,
            category="service_degradation",
            suggested_action=_get_service_degradation_suggestion(exc.service_name, capabilities),
            documentation_url="https://docs.DRYAD.AI.com/troubleshooting/service-degradation"
        )

        # Add degradation info
        error_response.error_details += f"\n\nAvailable features: {', '.join(capabilities['enabled'])}"
        if capabilities['degraded']:
            error_response.error_details += f"\nDegraded features: {', '.join(capabilities['degraded'])}"

        logger.warning(
            f"Service unavailable: {exc.service_name} - Circuit breaker open",
            extra={
                "request_id": error_response.request_id,
                "service": exc.service_name,
                "last_failure": exc.last_failure,
                "available_features": capabilities['enabled'],
                "degraded_features": capabilities['degraded']
            }
        )

        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content=error_response.model_dump(),
            headers={"X-Request-ID": error_response.request_id}
        )

    # Handle other service unavailable cases
    return await general_exception_handler(request, exc)


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Handler for unexpected exceptions.

    Catches all unhandled exceptions and returns structured error responses.
    """
    # Enhanced error categorization
    error_category, suggested_action = _categorize_exception(exc)

    error_response = ErrorResponse(
        error_code=ErrorCode.INTERNAL_SERVER_ERROR,
        error_message="An unexpected error occurred",
        error_details=f"The server encountered an unexpected condition: {type(exc).__name__}",
        severity=ErrorSeverity.CRITICAL,
        category=error_category,
        suggested_action=suggested_action,
        documentation_url="https://docs.DRYAD.AI.com/troubleshooting"
    )

    logger.error(
        f"Unhandled Exception: {type(exc).__name__} - {str(exc)}",
        extra={
            "request_id": error_response.request_id,
            "exception_type": type(exc).__name__,
            "traceback": traceback.format_exc(),
            "category": error_category
        }
    )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=error_response.model_dump(),
        headers={"X-Request-ID": error_response.request_id}
    )


def _get_service_degradation_suggestion(service_name: str, capabilities: Dict) -> str:
    """Get helpful suggestions when a service is degraded."""
    suggestions = []

    if service_name == "weaviate":
        suggestions.append("Vector search is temporarily unavailable")
        if "basic_chat" in capabilities.get("enabled", []):
            suggestions.append("You can still use basic chat functionality")
        suggestions.append("Try again in a few minutes or contact support")

    elif service_name == "redis":
        suggestions.append("Background task processing is temporarily unavailable")
        suggestions.append("Some operations may take longer than usual")
        if capabilities.get("basic_mode", False):
            suggestions.append("System is running in basic mode with limited features")

    elif service_name == "llm_provider":
        suggestions.append("AI language model is temporarily unavailable")
        suggestions.append("Please try again in a few minutes")
        if capabilities.get("degraded"):
            suggestions.append("Some features may still be available in degraded mode")

    else:
        suggestions.append(f"The {service_name} service is temporarily unavailable")
        suggestions.append("Please try again later")

    return ". ".join(suggestions)


def _categorize_exception(exc: Exception) -> tuple[str, str]:
    """Categorize exception and provide appropriate suggestion."""
    exc_type = type(exc).__name__
    exc_str = str(exc).lower()

    # Database-related errors
    if any(keyword in exc_str for keyword in ["database", "connection", "sql", "sqlite", "postgresql"]):
        return "database_error", "Check database connectivity and configuration"

    # Network/connectivity errors
    if any(keyword in exc_str for keyword in ["connection", "timeout", "network", "unreachable"]):
        return "connectivity_error", "Check network connectivity and service availability"

    # Authentication/authorization errors
    if any(keyword in exc_str for keyword in ["auth", "token", "permission", "unauthorized"]):
        return "auth_error", "Check authentication credentials and permissions"

    # Validation errors
    if any(keyword in exc_str for keyword in ["validation", "invalid", "format", "parse"]):
        return "validation_error", "Check request format and required parameters"

    # Resource errors
    if any(keyword in exc_str for keyword in ["memory", "disk", "resource", "limit"]):
        return "resource_error", "System resources may be exhausted - try again later"

    # Configuration errors
    if any(keyword in exc_str for keyword in ["config", "environment", "missing", "not found"]):
        return "configuration_error", "Check system configuration and environment variables"

    # Default
    return "internal_error", "Please try again later or contact support if the issue persists"


def _get_suggested_action_for_status(status_code: int) -> str:
    """Get suggested action based on HTTP status code."""
    suggestions = {
        400: "Check your request parameters and ensure they are valid",
        401: "Provide valid authentication credentials",
        403: "Ensure you have the necessary permissions for this operation",
        404: "Check that the requested resource exists and the URL is correct",
        429: "Reduce request frequency and retry after the specified time",
        500: "Try again later or contact support if the issue persists",
        503: "The service is temporarily unavailable, please try again later"
    }
    
    return suggestions.get(status_code, "Please try again or contact support")


def create_service_degradation_response(
    service_name: str,
    capabilities_affected: List[str],
    fallback_available: bool = True,
    error_message: str = None
) -> ErrorResponse:
    """
    Create a standardized response for service degradation scenarios.
    
    Used when external services are unavailable but fallback functionality exists.
    """
    if not error_message:
        error_message = f"{service_name} service is currently unavailable"
    
    from app.core.exceptions import ServiceStatus
    
    affected_services = [ServiceStatus(
        service_name=service_name,
        status="degraded" if fallback_available else "unavailable",
        fallback_available=fallback_available,
        capabilities_affected=capabilities_affected
    )]
    
    return ErrorResponse(
        error_code=ErrorCode.EXTERNAL_SERVICE_UNAVAILABLE,
        error_message=error_message,
        error_details=f"Fallback functionality is {'available' if fallback_available else 'not available'}",
        severity=ErrorSeverity.MEDIUM if fallback_available else ErrorSeverity.HIGH,
        category="service_degradation",
        suggested_action="The system will continue with reduced functionality" if fallback_available else "Please try again later",
        affected_services=affected_services,
        fallback_available=fallback_available
    )


def create_multimodal_processing_error(
    media_type: str,
    processing_step: str,
    error_details: str,
    processing_progress: float = None,
    fallback_available: bool = False
) -> ErrorResponse:
    """
    Create a standardized error response for multi-modal processing failures.
    
    Provides detailed context about which processing step failed and available fallbacks.
    """
    error_message = f"{media_type.title()} processing failed during {processing_step}"
    
    suggested_actions = {
        "audio": "Try converting to WAV or MP3 format with 16kHz sample rate",
        "video": "Ensure video is in MP4, AVI, or MOV format with standard codecs",
        "image": "Use JPEG, PNG, or GIF format with reasonable file size"
    }
    
    return ErrorResponse(
        error_code=getattr(ErrorCode, f"{media_type.upper()}_PROCESSING_FAILED"),
        error_message=error_message,
        error_details=error_details,
        severity=ErrorSeverity.MEDIUM if fallback_available else ErrorSeverity.HIGH,
        category="multimodal_processing",
        suggested_action=suggested_actions.get(media_type, "Check file format and try again"),
        documentation_url=f"https://docs.DRYAD.AI.com/multimodal/{media_type}-processing",
        fallback_available=fallback_available,
        processing_step=processing_step,
        processing_progress=processing_progress
    )


def create_validation_error_response(
    field_errors: Dict[str, str],
    error_message: str = "Validation failed"
) -> ErrorResponse:
    """
    Create a standardized validation error response.
    
    Converts field-level validation errors into structured format.
    """
    validation_errors = [
        ValidationErrorDetail(
            field=field,
            message=message,
            invalid_value=None,
            expected_type=None
        )
        for field, message in field_errors.items()
    ]
    
    return ErrorResponse(
        error_code=ErrorCode.VALIDATION_ERROR,
        error_message=error_message,
        error_details=f"Validation failed for {len(validation_errors)} field(s)",
        severity=ErrorSeverity.LOW,
        category="validation",
        suggested_action="Review the validation errors and correct the invalid fields",
        documentation_url="https://docs.DRYAD.AI.com/api/validation",
        validation_errors=validation_errors
    )
