"""
Grove Schemas

Pydantic schemas for Grove API requests and responses.
Ported from TypeScript service interfaces.
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import Dict, Any, Optional, List
from datetime import datetime
from enum import Enum


class SortOrder(str, Enum):
    """Sort order enumeration."""
    ASC = "ASC"
    DESC = "DESC"


class GroveSortBy(str, Enum):
    """Grove sort field enumeration."""
    NAME = "name"
    CREATED_AT = "created_at"
    LAST_ACCESSED_AT = "last_accessed_at"


class GroveCreate(BaseModel):
    """Schema for creating a new grove."""
    
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        use_enum_values=True
    )
    
    name: str = Field(..., min_length=1, max_length=255, description="Grove name")
    description: Optional[str] = Field(None, description="Grove description")
    template_metadata: Optional[Dict[str, Any]] = Field(None, description="Template metadata")
    is_favorite: Optional[bool] = Field(False, description="Whether grove is marked as favorite")


class GroveUpdate(BaseModel):
    """Schema for updating an existing grove."""
    
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        use_enum_values=True
    )
    
    name: Optional[str] = Field(None, min_length=1, max_length=255, description="Grove name")
    description: Optional[str] = Field(None, description="Grove description")
    template_metadata: Optional[Dict[str, Any]] = Field(None, description="Template metadata")
    is_favorite: Optional[bool] = Field(None, description="Whether grove is marked as favorite")


class GroveResponse(BaseModel):
    """Schema for grove response."""
    
    model_config = ConfigDict(
        from_attributes=True,
        use_enum_values=True
    )
    
    id: str = Field(..., description="Grove ID")
    name: str = Field(..., description="Grove name")
    description: Optional[str] = Field(None, description="Grove description")
    created_at: Optional[datetime] = Field(None, description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")
    last_accessed_at: Optional[datetime] = Field(None, description="Last access timestamp")
    is_favorite: bool = Field(..., description="Whether grove is marked as favorite")
    template_metadata: Optional[Dict[str, Any]] = Field(None, description="Template metadata")
    branch_count: Optional[int] = Field(None, description="Number of branches in grove")


class GroveListOptions(BaseModel):
    """Schema for grove list options."""
    
    model_config = ConfigDict(
        use_enum_values=True
    )
    
    include_archived: Optional[bool] = Field(False, description="Include archived groves")
    favorites_only: Optional[bool] = Field(False, description="Show only favorite groves")
    sort_by: Optional[GroveSortBy] = Field(GroveSortBy.LAST_ACCESSED_AT, description="Sort field")
    sort_order: Optional[SortOrder] = Field(SortOrder.DESC, description="Sort order")
    limit: Optional[int] = Field(None, ge=1, le=1000, description="Maximum number of results")
    offset: Optional[int] = Field(None, ge=0, description="Number of results to skip")


class GroveStats(BaseModel):
    """Schema for grove statistics."""
    
    model_config = ConfigDict(
        from_attributes=True
    )
    
    total_branches: int = Field(..., description="Total number of branches")
    active_branches: int = Field(..., description="Number of active branches")
    archived_branches: int = Field(..., description="Number of archived branches")
    total_observations: int = Field(..., description="Total number of observation points")


class GroveListResponse(BaseModel):
    """Schema for grove list response."""
    
    groves: List[GroveResponse] = Field(..., description="List of groves")
    total: int = Field(..., description="Total number of groves")
    limit: Optional[int] = Field(None, description="Applied limit")
    offset: Optional[int] = Field(None, description="Applied offset")
