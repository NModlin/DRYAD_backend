"""
Vessel Schemas

Pydantic schemas for Vessel API requests and responses.
Ported from TypeScript service interfaces.
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import Dict, Any, Optional, List
from datetime import datetime


class VesselCreate(BaseModel):
    """Schema for creating a new vessel."""
    
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True
    )
    
    branch_id: str = Field(..., description="Branch ID")
    parent_branch_id: Optional[str] = Field(None, description="Parent branch ID for context inheritance")
    initial_context: Optional[str] = Field(None, description="Initial context for the vessel")


class VesselResponse(BaseModel):
    """Schema for vessel response."""
    
    model_config = ConfigDict(
        from_attributes=True
    )
    
    id: str = Field(..., description="Vessel ID")
    branch_id: str = Field(..., description="Branch ID")
    storage_path: str = Field(..., description="Storage path")
    content_hash: str = Field(..., description="Content hash")
    file_references: Dict[str, str] = Field(..., description="File references")
    is_compressed: bool = Field(..., description="Whether vessel is compressed")
    compressed_path: Optional[str] = Field(None, description="Compressed file path")
    status: str = Field(..., description="Vessel status")
    generated_at: Optional[datetime] = Field(None, description="Generation timestamp")
    last_updated: Optional[datetime] = Field(None, description="Last update timestamp")
    last_accessed: Optional[datetime] = Field(None, description="Last access timestamp")


class VesselContentMetadata(BaseModel):
    """Schema for vessel content metadata."""
    
    name: str = Field(..., description="Vessel name")
    status: str = Field(..., description="Vessel status")
    branch_id: str = Field(..., description="Branch ID")
    grove_id: str = Field(..., description="Grove ID")


class VesselContentResponse(BaseModel):
    """Schema for vessel content response."""
    
    metadata: VesselContentMetadata = Field(..., description="Vessel metadata")
    summary: str = Field(..., description="Content summary")
    base_context: str = Field(..., description="Base context")
    branch_context: str = Field(..., description="Branch-specific context")
    inherited_context: str = Field(..., description="Inherited context from parent branches")
    dialogues: List[Dict[str, Any]] = Field(default_factory=list, description="Dialogue history")


class VesselContentUpdate(BaseModel):
    """Schema for updating vessel content."""
    
    model_config = ConfigDict(
        str_strip_whitespace=True
    )
    
    summary: Optional[str] = Field(None, description="Content summary")
    base_context: Optional[str] = Field(None, description="Base context")
    branch_context: Optional[str] = Field(None, description="Branch-specific context")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class VesselSearchOptions(BaseModel):
    """Schema for vessel search options."""
    
    grove_id: Optional[str] = Field(None, description="Limit search to specific grove")
    branch_ids: Optional[List[str]] = Field(None, description="Limit search to specific branches")
    include_archived: Optional[bool] = Field(False, description="Include archived vessels")
    limit: Optional[int] = Field(10, ge=1, le=100, description="Maximum number of results")


class VesselSearchResult(BaseModel):
    """Schema for vessel search result."""
    
    vessel_id: str = Field(..., description="Vessel ID")
    branch_id: str = Field(..., description="Branch ID")
    grove_id: str = Field(..., description="Grove ID")
    score: float = Field(..., description="Search relevance score")
    snippet: str = Field(..., description="Content snippet")
    context: str = Field(..., description="Search context")


class VesselSearchResponse(BaseModel):
    """Schema for vessel search response."""
    
    results: List[VesselSearchResult] = Field(..., description="Search results")
    total: int = Field(..., description="Total number of results")
    query: str = Field(..., description="Original search query")
    execution_time: float = Field(..., description="Search execution time in seconds")
