"""
Tool Registry Pydantic Schemas

Request and response schemas for tool registry API endpoints.
"""

from datetime import datetime
from typing import Any
from uuid import UUID
from pydantic import BaseModel, Field, field_validator


class ToolCreate(BaseModel):
    """Schema for creating a new tool."""
    
    name: str = Field(..., min_length=1, max_length=255, description="Tool name")
    version: str = Field(..., min_length=1, max_length=50, description="Semantic version")
    description: str | None = Field(None, description="Tool description")
    configuration_schema: dict[str, Any] = Field(..., description="OpenAPI 3.0-compliant JSON schema")
    docker_image_uri: str | None = Field(
        None,
        max_length=500,
        description="Docker image URI for tool execution",
    )
    
    @field_validator("configuration_schema")
    @classmethod
    def validate_openapi_schema(cls, v: dict[str, Any]) -> dict[str, Any]:
        """Validate that configuration_schema contains required OpenAPI 3.0 fields."""
        if not isinstance(v, dict):
            raise ValueError("configuration_schema must be a dictionary")
        
        # Check for required OpenAPI 3.0 fields
        if "openapi" not in v:
            raise ValueError("configuration_schema must contain 'openapi' field")
        
        if "info" not in v:
            raise ValueError("configuration_schema must contain 'info' field")
        
        if "paths" not in v:
            raise ValueError("configuration_schema must contain 'paths' field")
        
        return v
    
    model_config = {"from_attributes": True}


class ToolUpdate(BaseModel):
    """Schema for updating tool metadata (immutable fields excluded)."""
    
    description: str | None = None
    is_active: bool | None = None
    docker_image_uri: str | None = Field(None, max_length=500)
    
    model_config = {"from_attributes": True}


class ToolResponse(BaseModel):
    """Schema for tool response."""
    
    tool_id: UUID
    name: str
    version: str
    description: str | None
    configuration_schema: dict[str, Any]
    docker_image_uri: str | None
    created_at: datetime
    updated_at: datetime
    is_active: bool
    
    model_config = {"from_attributes": True}


class ToolListResponse(BaseModel):
    """Schema for paginated tool list response."""
    
    tools: list[ToolResponse]
    total: int
    limit: int
    offset: int
    
    model_config = {"from_attributes": True}


class ToolPermissionCreate(BaseModel):
    """Schema for creating a tool permission."""
    
    principal_id: str = Field(..., min_length=1, max_length=255)
    principal_type: str = Field(..., pattern="^(agent|role)$")
    allow_stateful_execution: bool = Field(default=False)
    created_by: str | None = Field(None, max_length=255)
    
    model_config = {"from_attributes": True}


class ToolPermissionResponse(BaseModel):
    """Schema for tool permission response."""
    
    permission_id: UUID
    principal_id: str
    principal_type: str
    tool_id: UUID
    allow_stateful_execution: bool
    created_at: datetime
    created_by: str | None
    
    model_config = {"from_attributes": True}


class ToolPermissionListResponse(BaseModel):
    """Schema for tool permission list response."""
    
    permissions: list[ToolPermissionResponse]
    total: int
    
    model_config = {"from_attributes": True}

