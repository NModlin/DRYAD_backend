"""
API Example Models for Enhanced Documentation
Provides example request/response models for better API documentation.
"""

from typing import Dict, Any, List, Optional, Union
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from enum import Enum


class ExampleStatus(str, Enum):
    """Example status values."""
    SUCCESS = "success"
    ERROR = "error"
    PROCESSING = "processing"
    PENDING = "pending"


class ChatRequest(BaseModel):
    """Example chat request model."""
    message: str = Field(
        ...,
        description="The message to send to the AI agent"
    )
    context: Optional[Dict[str, Any]] = Field(
        None,
        description="Additional context for the conversation"
    )
    options: Optional[Dict[str, Any]] = Field(
        None,
        description="Configuration options for the AI response"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "message": "Hello, can you help me analyze this document?",
                "context": {
                    "user_id": "user123",
                    "session_id": "session456"
                },
                "options": {
                    "model": "gpt-3.5-turbo",
                    "temperature": 0.7,
                    "max_tokens": 1000
                }
            }
        }
    )


class ChatResponse(BaseModel):
    """Example chat response model."""
    response: str = Field(
        ...,
        description="The AI agent's response"
    )
    agent_id: str = Field(
        ...,
        description="Unique identifier for the responding agent"
    )
    session_id: str = Field(
        ...,
        description="Session identifier for conversation continuity"
    )
    timestamp: datetime = Field(
        ...,
        description="Response timestamp"
    )
    metadata: Dict[str, Any] = Field(
        ...,
        description="Additional response metadata"
    )


class DocumentUploadResponse(BaseModel):
    """Example document upload response."""
    document_id: str = Field(
        ...,
        description="Unique identifier for the uploaded document"
    )
    filename: str = Field(
        ...,
        description="Original filename"
    )
    size_bytes: int = Field(
        ...,
        description="File size in bytes"
    )
    content_type: str = Field(
        ...,
        description="MIME type of the uploaded file"
    )
    status: str = Field(
        ...,
        description="Processing status"
    )
    metadata: Dict[str, Any] = Field(
        ...,
        description="Document metadata"
    )


class TaskRequest(BaseModel):
    """Example task creation request."""
    task_type: str = Field(
        ...,
        description="Type of task to create"
    )
    description: str = Field(
        ...,
        description="Detailed description of the task"
    )
    parameters: Dict[str, Any] = Field(
        ...,
        description="Task-specific parameters"
    )
    priority: str = Field(
        "normal",
        description="Task priority level"
    )


class TaskResponse(BaseModel):
    """Example task response."""
    task_id: str = Field(
        ...,
        description="Unique task identifier"
    )
    status: str = Field(
        ...,
        description="Current task status"
    )
    progress: float = Field(
        ...,
        description="Task completion percentage (0-100)"
    )
    result: Optional[Dict[str, Any]] = Field(
        None,
        description="Task results (available when completed)"
    )
    created_at: datetime = Field(
        ...,
        description="Task creation timestamp"
    )
    updated_at: datetime = Field(
        ...,
        description="Last update timestamp"
    )


class HealthResponse(BaseModel):
    """Example health check response."""
    status: str = Field(
        ...,
        description="Overall system health status"
    )
    version: str = Field(
        ...,
        description="API version"
    )
    mode: str = Field(
        ...,
        description="Current deployment mode"
    )
    capabilities: Dict[str, str] = Field(
        ...,
        description="Available system capabilities"
    )
    services: Dict[str, Dict[str, Any]] = Field(
        ...,
        description="Individual service health status"
    )


class ErrorResponse(BaseModel):
    """Example error response."""
    error_id: str = Field(
        ...,
        description="Unique error identifier for tracking"
    )
    message: str = Field(
        ...,
        description="User-friendly error message"
    )
    recovery_suggestions: List[str] = Field(
        ...,
        description="Suggested actions to resolve the error"
    )
    timestamp: datetime = Field(
        ...,
        description="Error occurrence timestamp"
    )


class MultiModalRequest(BaseModel):
    """Example multi-modal processing request."""
    content: List[Dict[str, Any]] = Field(
        ...,
        description="List of content items to process"
    )
    processing_options: Dict[str, Any] = Field(
        ...,
        description="Processing configuration options"
    )


class WebSocketMessage(BaseModel):
    """Example WebSocket message."""
    type: str = Field(
        ...,
        description="Message type"
    )
    data: Dict[str, Any] = Field(
        ...,
        description="Message payload"
    )
    timestamp: datetime = Field(
        ...,
        description="Message timestamp"
    )


class PerformanceMetrics(BaseModel):
    """Example performance metrics response."""
    query_stats: Dict[str, Any] = Field(
        ...,
        description="Database query performance statistics"
    )
    cache_stats: Dict[str, Any] = Field(
        ...,
        description="Cache performance statistics"
    )
    system_metrics: Dict[str, Any] = Field(
        ...,
        description="System resource metrics"
    )


# Example data for testing and documentation
EXAMPLE_RESPONSES = {
    "chat_success": {
        "response": "Hello! I'd be happy to help you analyze a document. Please upload the document using the /api/v1/documents/upload endpoint, and I'll provide detailed analysis.",
        "agent_id": "agent_001",
        "session_id": "session456",
        "timestamp": "2024-01-15T10:30:00Z",
        "metadata": {
            "model_used": "gpt-3.5-turbo",
            "tokens_used": 45,
            "response_time_ms": 1250,
            "confidence": 0.95
        }
    },
    "health_healthy": {
        "status": "healthy",
        "version": "9.0.0",
        "mode": "basic",
        "capabilities": {
            "llm_provider": "openai",
            "vector_store": "available",
            "task_queue": "available",
            "websockets": "available"
        },
        "services": {
            "database": {"status": "healthy", "response_time_ms": 12},
            "llm": {"status": "healthy", "provider": "openai"},
            "vector_store": {"status": "healthy", "type": "weaviate"}
        }
    },
    "error_service_unavailable": {
        "error_id": "ERR-1642234567890-0001",
        "message": "The AI service is temporarily unavailable",
        "recovery_suggestions": [
            "Check your LLM provider configuration",
            "Verify API keys and quotas",
            "Try using a different model or provider"
        ],
        "timestamp": "2024-01-15T10:30:00Z"
    }
}
