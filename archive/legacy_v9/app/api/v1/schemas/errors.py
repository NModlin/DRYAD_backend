"""
Enhanced Error Response Schemas for API Documentation

Provides comprehensive error response models for OpenAPI documentation
and consistent error handling across all API endpoints.
"""

from typing import Dict, Any, List, Optional, Union
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime

from app.core.exceptions import ErrorCode, ErrorSeverity


class ValidationErrorDetailSchema(BaseModel):
    """Schema for detailed validation error information."""
    
    field: str = Field(..., description="Field that failed validation")
    message: str = Field(..., description="Validation error message")
    invalid_value: Optional[Any] = Field(None, description="The invalid value that was provided")
    expected_type: Optional[str] = Field(None, description="Expected data type or format")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "field": "file",
                "message": "File must be an audio file",
                "invalid_value": "text/plain",
                "expected_type": "audio/*"
            }
        }
    )


class ServiceStatusSchema(BaseModel):
    """Schema for service availability status."""
    
    service_name: str = Field(..., description="Name of the service")
    status: str = Field(..., description="Service status")
    fallback_available: bool = Field(..., description="Whether fallback functionality is available")
    capabilities_affected: List[str] = Field(
        default_factory=list,
        description="List of affected capabilities"
    )
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "service_name": "openai_api",
                "status": "unavailable",
                "fallback_available": True,
                "capabilities_affected": ["multi_agent_reasoning", "gpt_analysis"]
            }
        }
    )


class ErrorResponseSchema(BaseModel):
    """Comprehensive error response schema for all API endpoints."""
    
    success: bool = Field(False, description="Always false for error responses")
    error_code: str = Field(..., description="Standardized error code")
    error_message: str = Field(..., description="Human-readable error message")
    error_details: Optional[str] = Field(
        None,
        description="Additional error details and context"
    )

    # Request tracking
    request_id: str = Field(
        default_factory=lambda: f"req_{__import__('uuid').uuid4()}",
        description="Unique request identifier for tracking"
    )
    timestamp: str = Field(
        default_factory=lambda: __import__('datetime').datetime.now().isoformat(),
        description="Error occurrence timestamp"
    )
    
    # Error categorization
    severity: str = Field(..., description="Error severity level")
    category: str = Field(..., description="Error category")

    # Remediation guidance
    suggested_action: Optional[str] = Field(
        None,
        description="Suggested action to resolve the error"
    )
    documentation_url: Optional[str] = Field(
        None,
        description="Link to relevant documentation"
    )
    
    # Service status information
    affected_services: List[ServiceStatusSchema] = Field(
        default_factory=list, 
        description="Services affected by this error"
    )
    fallback_available: bool = Field(False, description="Whether fallback functionality is available")
    
    # Validation-specific details
    validation_errors: List[ValidationErrorDetailSchema] = Field(
        default_factory=list, 
        description="Detailed validation errors"
    )
    
    # Processing-specific details
    processing_step: Optional[str] = Field(
        None,
        description="Processing step where error occurred"
    )
    processing_progress: Optional[float] = Field(
        None,
        description="Processing progress when error occurred (0.0-1.0)"
    )
    
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
                "validation_errors": [],
                "processing_step": "audio_transcription",
                "processing_progress": 0.3
            }
        }
    )


# Common error response examples for different scenarios

class ValidationErrorExample(ErrorResponseSchema):
    """Example validation error response."""
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "success": False,
                "error_code": "GREMLINS_1003",
                "error_message": "Validation failed for 2 field(s)",
                "error_details": "Please check the validation errors and correct the invalid fields",
                "request_id": "req_validation_123",
                "timestamp": "2024-01-01T12:00:00.000Z",
                "severity": "low",
                "category": "validation",
                "suggested_action": "Review the validation errors and correct the invalid fields",
                "documentation_url": "https://docs.DRYAD.AI.com/api/validation",
                "affected_services": [],
                "fallback_available": False,
                "validation_errors": [
                    {
                        "field": "file",
                        "message": "File must be an audio file",
                        "invalid_value": "text/plain",
                        "expected_type": "audio/*"
                    },
                    {
                        "field": "transcribe",
                        "message": "Must be a boolean value",
                        "invalid_value": "yes",
                        "expected_type": "boolean"
                    }
                ],
                "processing_step": None,
                "processing_progress": None
            }
        }
    )


class ServiceUnavailableErrorExample(ErrorResponseSchema):
    """Example service unavailable error response."""
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "success": False,
                "error_code": "GREMLINS_8001",
                "error_message": "OpenAI API service is currently unavailable",
                "error_details": "Connection timeout while attempting to reach OpenAI API",
                "request_id": "req_service_456",
                "timestamp": "2024-01-01T12:00:00.000Z",
                "severity": "medium",
                "category": "external_service",
                "suggested_action": "The system will continue with reduced functionality using fallback agents",
                "documentation_url": "https://docs.DRYAD.AI.com/services/external-dependencies",
                "affected_services": [
                    {
                        "service_name": "openai_api",
                        "status": "unavailable",
                        "fallback_available": True,
                        "capabilities_affected": ["gpt_analysis", "advanced_reasoning"]
                    }
                ],
                "fallback_available": True,
                "validation_errors": [],
                "processing_step": "external_api_call",
                "processing_progress": None
            }
        }
    )


class MultiModalProcessingErrorExample(ErrorResponseSchema):
    """Example multi-modal processing error response."""
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "success": False,
                "error_code": "GREMLINS_6002",
                "error_message": "Video processing failed during frame extraction",
                "error_details": "OpenCV failed to read video file: codec not supported",
                "request_id": "req_video_789",
                "timestamp": "2024-01-01T12:00:00.000Z",
                "severity": "medium",
                "category": "multimodal_processing",
                "suggested_action": "Ensure video is in MP4, AVI, or MOV format with standard codecs",
                "documentation_url": "https://docs.DRYAD.AI.com/multimodal/video-processing",
                "affected_services": [
                    {
                        "service_name": "video_processor",
                        "status": "degraded",
                        "fallback_available": True,
                        "capabilities_affected": ["frame_extraction", "video_analysis"]
                    }
                ],
                "fallback_available": True,
                "validation_errors": [],
                "processing_step": "frame_extraction",
                "processing_progress": 0.15
            }
        }
    )


class AgentProcessingErrorExample(ErrorResponseSchema):
    """Example agent processing error response."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "success": False,
                "error_code": "GREMLINS_3000",
                "error_message": "Agent processing failed",
                "error_details": "Tool execution timeout during web search operation",
                "request_id": "req_agent_101",
                "timestamp": "2024-01-01T12:00:00.000Z",
                "severity": "high",
                "category": "agent_processing",
                "suggested_action": "Retry the request or contact support if the issue persists",
                "documentation_url": "https://docs.DRYAD.AI.com/agents/troubleshooting",
                "affected_services": [],
                "fallback_available": False,
                "validation_errors": [],
                "processing_step": "tool_execution",
                "processing_progress": 0.7
            }
        }
    )


class RateLimitErrorExample(ErrorResponseSchema):
    """Example rate limit error response."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "success": False,
                "error_code": "GREMLINS_1004",
                "error_message": "Rate limit exceeded",
                "error_details": "Too many requests from this client. Limit: 100 requests per minute",
                "request_id": "req_rate_202",
                "timestamp": "2024-01-01T12:00:00.000Z",
                "severity": "low",
                "category": "rate_limiting",
                "suggested_action": "Reduce request frequency and retry after 60 seconds",
                "documentation_url": "https://docs.DRYAD.AI.com/api/rate-limits",
                "affected_services": [],
                "fallback_available": False,
                "validation_errors": [],
                "processing_step": None,
                "processing_progress": None
            }
        }
    )


# Response models for different HTTP status codes
ERROR_RESPONSES = {
    400: {"model": ValidationErrorExample, "description": "Validation Error"},
    422: {"model": ValidationErrorExample, "description": "Unprocessable Entity"},
    429: {"model": RateLimitErrorExample, "description": "Rate Limit Exceeded"},
    500: {"model": AgentProcessingErrorExample, "description": "Internal Server Error"},
    503: {"model": ServiceUnavailableErrorExample, "description": "Service Unavailable"}
}
