"""
Enhanced Exception Handling for DRYAD.AI API

Comprehensive custom exception classes and error response models for
improved developer experience and consistent error handling across all API endpoints.
"""

import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional, Union
from enum import Enum

from fastapi import HTTPException, status
from pydantic import BaseModel, Field, ConfigDict


class ErrorCode(str, Enum):
    """Standardized error codes for the DRYAD.AI API."""
    
    # General errors (1000-1999)
    INTERNAL_SERVER_ERROR = "GREMLINS_1000"
    INVALID_REQUEST = "GREMLINS_1001"
    RESOURCE_NOT_FOUND = "GREMLINS_1002"
    VALIDATION_ERROR = "GREMLINS_1003"
    RATE_LIMIT_EXCEEDED = "GREMLINS_1004"
    
    # Authentication/Authorization errors (2000-2999)
    AUTHENTICATION_REQUIRED = "GREMLINS_2000"
    INVALID_API_KEY = "GREMLINS_2001"
    INSUFFICIENT_PERMISSIONS = "GREMLINS_2002"
    TOKEN_EXPIRED = "GREMLINS_2003"
    
    # Agent processing errors (3000-3999)
    AGENT_PROCESSING_FAILED = "GREMLINS_3000"
    AGENT_TIMEOUT = "GREMLINS_3001"
    TOOL_EXECUTION_FAILED = "GREMLINS_3002"
    CONTEXT_TOO_LARGE = "GREMLINS_3003"
    
    # Multi-agent errors (4000-4999)
    MULTI_AGENT_ORCHESTRATION_FAILED = "GREMLINS_4000"
    AGENT_COMMUNICATION_ERROR = "GREMLINS_4001"
    WORKFLOW_EXECUTION_FAILED = "GREMLINS_4002"
    AGENT_UNAVAILABLE = "GREMLINS_4003"
    
    # Document processing errors (5000-5999)
    DOCUMENT_UPLOAD_FAILED = "GREMLINS_5000"
    DOCUMENT_PROCESSING_FAILED = "GREMLINS_5001"
    VECTOR_STORE_ERROR = "GREMLINS_5002"
    SEARCH_FAILED = "GREMLINS_5003"
    DOCUMENT_TOO_LARGE = "GREMLINS_5004"
    
    # Multi-modal processing errors (6000-6999)
    MULTIMODAL_PROCESSING_FAILED = "GREMLINS_6000"
    AUDIO_PROCESSING_FAILED = "GREMLINS_6001"
    VIDEO_PROCESSING_FAILED = "GREMLINS_6002"
    IMAGE_PROCESSING_FAILED = "GREMLINS_6003"
    UNSUPPORTED_MEDIA_FORMAT = "GREMLINS_6004"
    MEDIA_FILE_TOO_LARGE = "GREMLINS_6005"
    TRANSCRIPTION_FAILED = "GREMLINS_6006"
    
    # Orchestrator errors (7000-7999)
    TASK_EXECUTION_FAILED = "GREMLINS_7000"
    TASK_TIMEOUT = "GREMLINS_7001"
    WORKER_UNAVAILABLE = "GREMLINS_7002"
    TASK_QUEUE_FULL = "GREMLINS_7003"
    
    # External service errors (8000-8999)
    EXTERNAL_SERVICE_UNAVAILABLE = "GREMLINS_8000"
    OPENAI_API_ERROR = "GREMLINS_8001"
    QDRANT_CONNECTION_ERROR = "GREMLINS_8002"
    REDIS_CONNECTION_ERROR = "GREMLINS_8003"
    WEBSOCKET_CONNECTION_ERROR = "GREMLINS_8004"
    
    # Database errors (9000-9999)
    DATABASE_CONNECTION_ERROR = "GREMLINS_9000"
    DATABASE_QUERY_FAILED = "GREMLINS_9001"
    CONVERSATION_NOT_FOUND = "GREMLINS_9002"
    DATA_INTEGRITY_ERROR = "GREMLINS_9003"


class ErrorSeverity(str, Enum):
    """Error severity levels for categorizing errors."""
    
    LOW = "low"           # Minor issues, system continues normally
    MEDIUM = "medium"     # Some functionality affected, fallbacks available
    HIGH = "high"         # Major functionality affected, limited fallbacks
    CRITICAL = "critical" # System functionality severely impacted


class ServiceStatus(BaseModel):
    """Model for representing service availability status."""
    
    service_name: str = Field(..., description="Name of the service")
    status: str = Field(..., description="Service status (available, degraded, unavailable)")
    fallback_available: bool = Field(..., description="Whether fallback functionality is available")
    capabilities_affected: List[str] = Field(default_factory=list, description="List of affected capabilities")
    last_check: Optional[datetime] = Field(None, description="Last check timestamp")
    error_message: Optional[str] = Field(None, description="Error message if service is unavailable")
    circuit_breaker_state: Optional[str] = Field(None, description="Circuit breaker state")
    degradation_reason: Optional[str] = Field(None, description="Reason for degradation")
    
    model_config = ConfigDict()


class ValidationErrorDetail(BaseModel):
    """Detailed validation error information."""
    
    field: str = Field(..., description="Field that failed validation")
    message: str = Field(..., description="Validation error message")
    invalid_value: Any = Field(None, description="The invalid value that was provided")
    expected_type: Optional[str] = Field(None, description="Expected data type or format")


class ErrorResponse(BaseModel):
    """Standardized error response model for all API endpoints."""
    
    success: bool = Field(False, description="Always false for error responses")
    error_code: ErrorCode = Field(..., description="Standardized error code")
    error_message: str = Field(..., description="Human-readable error message")
    error_details: Optional[str] = Field(None, description="Additional error details and context")
    
    # Request tracking
    request_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique request identifier")
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat(), description="Error occurrence timestamp")
    
    # Error categorization
    severity: ErrorSeverity = Field(ErrorSeverity.MEDIUM, description="Error severity level")
    category: str = Field(..., description="Error category (validation, processing, external_service, etc.)")
    
    # Remediation guidance
    suggested_action: Optional[str] = Field(None, description="Suggested action to resolve the error")
    documentation_url: Optional[str] = Field(None, description="Link to relevant documentation")
    
    # Service status information
    affected_services: List[ServiceStatus] = Field(default_factory=list, description="Services affected by this error")
    fallback_available: bool = Field(False, description="Whether fallback functionality is available")
    
    # Validation-specific details
    validation_errors: List[ValidationErrorDetail] = Field(default_factory=list, description="Detailed validation errors")
    
    # Processing-specific details
    processing_step: Optional[str] = Field(None, description="Processing step where error occurred")
    processing_progress: Optional[float] = Field(None, description="Processing progress when error occurred (0.0-1.0)")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "success": False,
                "error_code": "GREMLINS_6001",
                "error_message": "Audio processing failed during transcription",
                "error_details": "Whisper model failed to process audio file: unsupported sample rate",
                "request_id": "req_123e4567-e89b-12d3-a456-426614174000",
                "timestamp": "2024-01-01T12:00:00.000Z",
                "severity": "medium",
                "category": "multimodal_processing",
                "suggested_action": "Convert audio to supported format (WAV, MP3) with sample rate 16kHz or 44.1kHz",
                "documentation_url": "https://docs.DRYAD.AI.com/multimodal/audio-processing",
                "affected_services": [
                    {
                        "service_name": "audio_transcription",
                        "status": "degraded",
                        "fallback_available": True,
                        "capabilities_affected": ["speech_to_text"]
                    }
                ],
                "fallback_available": True,
                "processing_step": "audio_transcription",
                "processing_progress": 0.3
            }
        }
    )


class DRYADAIException(HTTPException):
    """Base exception class for DRYAD.AI API with enhanced error information."""
    
    def __init__(
        self,
        status_code: int,
        error_code: ErrorCode,
        error_message: str,
        error_details: Optional[str] = None,
        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
        category: str = "general",
        suggested_action: Optional[str] = None,
        documentation_url: Optional[str] = None,
        affected_services: Optional[List[ServiceStatus]] = None,
        fallback_available: bool = False,
        validation_errors: Optional[List[ValidationErrorDetail]] = None,
        processing_step: Optional[str] = None,
        processing_progress: Optional[float] = None,
        **kwargs
    ):
        self.error_response = ErrorResponse(
            error_code=error_code,
            error_message=error_message,
            error_details=error_details,
            severity=severity,
            category=category,
            suggested_action=suggested_action,
            documentation_url=documentation_url,
            affected_services=affected_services or [],
            fallback_available=fallback_available,
            validation_errors=validation_errors or [],
            processing_step=processing_step,
            processing_progress=processing_progress
        )
        
        super().__init__(
            status_code=status_code,
            detail=self.error_response.model_dump(),
            **kwargs
        )


# Specific exception classes for different error types

class ValidationException(DRYADAIException):
    """Exception for validation errors."""
    
    def __init__(
        self,
        error_message: str,
        validation_errors: List[ValidationErrorDetail],
        error_details: Optional[str] = None,
        **kwargs
    ):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            error_code=ErrorCode.VALIDATION_ERROR,
            error_message=error_message,
            error_details=error_details,
            severity=ErrorSeverity.LOW,
            category="validation",
            suggested_action="Review the validation errors and correct the invalid fields",
            documentation_url="https://docs.DRYAD.AI.com/api/validation",
            validation_errors=validation_errors,
            **kwargs
        )


class AgentProcessingException(DRYADAIException):
    """Exception for agent processing errors."""
    
    def __init__(
        self,
        error_message: str,
        error_details: Optional[str] = None,
        processing_step: Optional[str] = None,
        **kwargs
    ):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            error_code=ErrorCode.AGENT_PROCESSING_FAILED,
            error_message=error_message,
            error_details=error_details,
            severity=ErrorSeverity.HIGH,
            category="agent_processing",
            suggested_action="Retry the request or contact support if the issue persists",
            documentation_url="https://docs.DRYAD.AI.com/agents/troubleshooting",
            processing_step=processing_step,
            **kwargs
        )


class MultiModalProcessingException(DRYADAIException):
    """Exception for multi-modal processing errors."""
    
    def __init__(
        self,
        error_message: str,
        media_type: str,
        error_details: Optional[str] = None,
        processing_step: Optional[str] = None,
        processing_progress: Optional[float] = None,
        fallback_available: bool = False,
        **kwargs
    ):
        error_code_map = {
            "audio": ErrorCode.AUDIO_PROCESSING_FAILED,
            "video": ErrorCode.VIDEO_PROCESSING_FAILED,
            "image": ErrorCode.IMAGE_PROCESSING_FAILED
        }
        
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            error_code=error_code_map.get(media_type, ErrorCode.MULTIMODAL_PROCESSING_FAILED),
            error_message=error_message,
            error_details=error_details,
            severity=ErrorSeverity.MEDIUM if fallback_available else ErrorSeverity.HIGH,
            category="multimodal_processing",
            suggested_action=f"Check {media_type} file format and try again, or use alternative processing options",
            documentation_url=f"https://docs.DRYAD.AI.com/multimodal/{media_type}-processing",
            fallback_available=fallback_available,
            processing_step=processing_step,
            processing_progress=processing_progress,
            **kwargs
        )


class ExternalServiceException(DRYADAIException):
    """Exception for external service errors."""
    
    def __init__(
        self,
        service_name: str,
        error_message: str,
        error_details: Optional[str] = None,
        affected_capabilities: Optional[List[str]] = None,
        fallback_available: bool = False,
        **kwargs
    ):
        service_error_codes = {
            "openai": ErrorCode.OPENAI_API_ERROR,
            "qdrant": ErrorCode.QDRANT_CONNECTION_ERROR,
            "redis": ErrorCode.REDIS_CONNECTION_ERROR,
            "websocket": ErrorCode.WEBSOCKET_CONNECTION_ERROR
        }
        
        affected_services = [ServiceStatus(
            service_name=service_name,
            status="unavailable",
            fallback_available=fallback_available,
            capabilities_affected=affected_capabilities or []
        )]
        
        super().__init__(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            error_code=service_error_codes.get(service_name, ErrorCode.EXTERNAL_SERVICE_UNAVAILABLE),
            error_message=error_message,
            error_details=error_details,
            severity=ErrorSeverity.MEDIUM if fallback_available else ErrorSeverity.HIGH,
            category="external_service",
            suggested_action="The service will retry automatically, or you can try again later",
            documentation_url="https://docs.DRYAD.AI.com/services/external-dependencies",
            affected_services=affected_services,
            fallback_available=fallback_available,
            **kwargs
        )


class DatabaseException(DRYADAIException):
    """Exception for database-related errors."""
    
    def __init__(
        self,
        error_message: str,
        error_details: Optional[str] = None,
        **kwargs
    ):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            error_code=ErrorCode.DATABASE_CONNECTION_ERROR,
            error_message=error_message,
            error_details=error_details,
            severity=ErrorSeverity.CRITICAL,
            category="database",
            suggested_action="Contact support immediately - this indicates a system issue",
            documentation_url="https://docs.DRYAD.AI.com/troubleshooting/database",
            **kwargs
        )


class RateLimitException(DRYADAIException):
    """Exception for rate limiting errors."""
    
    def __init__(
        self,
        error_message: str = "Rate limit exceeded",
        retry_after: Optional[int] = None,
        **kwargs
    ):
        suggested_action = "Reduce request frequency"
        if retry_after:
            suggested_action += f" and retry after {retry_after} seconds"
        
        super().__init__(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            error_code=ErrorCode.RATE_LIMIT_EXCEEDED,
            error_message=error_message,
            severity=ErrorSeverity.LOW,
            category="rate_limiting",
            suggested_action=suggested_action,
            documentation_url="https://docs.DRYAD.AI.com/api/rate-limits",
            **kwargs
        )


# Legacy Compatibility Aliases
DryadError = DRYADAIException
DryadErrorCode = ErrorCode
NotFoundError = lambda *args, **kwargs: DRYADAIException(status_code=404, error_code=ErrorCode.RESOURCE_NOT_FOUND, *args, **kwargs)

def wrap_error(error: Exception, message: str = None) -> DRYADAIException:
    return DRYADAIException(
        status_code=500,
        error_code=ErrorCode.INTERNAL_SERVER_ERROR,
        error_message=message or str(error),
        error_details=str(error)
    )
