"""
Structured Logging Pydantic Schemas

Request/response models for structured logging API.
"""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, ConfigDict


class LogLevel(str, Enum):
    """Log level enumeration."""
    
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class LogEntryCreate(BaseModel):
    """Schema for creating a log entry."""
    
    level: LogLevel
    component: str = Field(..., max_length=100)
    event_type: str = Field(..., max_length=100)
    message: str
    metadata: dict[str, Any] = Field(default_factory=dict)
    trace_id: str | None = Field(None, max_length=255)
    span_id: str | None = Field(None, max_length=255)
    agent_id: str | None = Field(None, max_length=255)
    task_id: str | None = Field(None, max_length=255)
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "level": "INFO",
                "component": "sandbox",
                "event_type": "tool_execution_started",
                "message": "Starting tool execution",
                "metadata": {
                    "tool_id": "uuid",
                    "tool_name": "code_executor",
                    "input_size_bytes": 1024,
                },
                "trace_id": "trace_abc123",
                "span_id": "span_def456",
                "agent_id": "agent_123",
                "task_id": "task_789",
            }
        }
    )


class LogEntry(BaseModel):
    """Schema for log entry response."""
    
    log_id: int
    timestamp: datetime
    level: LogLevel
    component: str
    event_type: str
    message: str
    metadata: dict[str, Any]
    trace_id: str | None
    span_id: str | None
    agent_id: str | None
    task_id: str | None
    
    model_config = ConfigDict(from_attributes=True)


class LogQueryParams(BaseModel):
    """Schema for log query parameters."""
    
    start_time: datetime | None = None
    end_time: datetime | None = None
    level: LogLevel | None = None
    component: str | None = None
    event_type: str | None = None
    agent_id: str | None = None
    task_id: str | None = None
    trace_id: str | None = None
    limit: int = Field(default=100, ge=1, le=1000)
    offset: int = Field(default=0, ge=0)
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "start_time": "2025-01-10T09:00:00Z",
                "end_time": "2025-01-10T10:00:00Z",
                "level": "ERROR",
                "component": "sandbox",
                "limit": 50,
                "offset": 0,
            }
        }
    )


class LogListResponse(BaseModel):
    """Schema for paginated log list response."""
    
    logs: list[LogEntry]
    total: int
    limit: int
    offset: int
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "logs": [],
                "total": 150,
                "limit": 100,
                "offset": 0,
            }
        }
    )

