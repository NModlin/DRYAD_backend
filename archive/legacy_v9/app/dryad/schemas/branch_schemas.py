"""
Branch Schemas

Pydantic schemas for Branch API requests and responses.
Ported from TypeScript service interfaces.
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime
from app.dryad.models.branch import BranchStatus, BranchPriority


class BranchCreate(BaseModel):
    """Schema for creating a new branch."""
    
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        use_enum_values=True
    )
    
    grove_id: str = Field(..., description="Grove ID")
    parent_id: Optional[str] = Field(None, description="Parent branch ID")
    name: str = Field(..., min_length=1, max_length=255, description="Branch name")
    description: Optional[str] = Field(None, description="Branch description")
    priority: Optional[BranchPriority] = Field(BranchPriority.MEDIUM, description="Branch priority")
    observation_point_id: Optional[str] = Field(None, description="Observation point ID that created this branch")


class BranchUpdate(BaseModel):
    """Schema for updating an existing branch."""
    
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        use_enum_values=True
    )
    
    name: Optional[str] = Field(None, min_length=1, max_length=255, description="Branch name")
    description: Optional[str] = Field(None, description="Branch description")
    status: Optional[BranchStatus] = Field(None, description="Branch status")
    priority: Optional[BranchPriority] = Field(None, description="Branch priority")


class BranchResponse(BaseModel):
    """Schema for branch response."""
    
    model_config = ConfigDict(
        from_attributes=True,
        use_enum_values=True
    )
    
    id: str = Field(..., description="Branch ID")
    grove_id: str = Field(..., description="Grove ID")
    parent_id: Optional[str] = Field(None, description="Parent branch ID")
    name: str = Field(..., description="Branch name")
    description: Optional[str] = Field(None, description="Branch description")
    path_depth: int = Field(..., description="Depth in the branch tree")
    status: BranchStatus = Field(..., description="Branch status")
    priority: BranchPriority = Field(..., description="Branch priority")
    created_at: Optional[datetime] = Field(None, description="Creation timestamp")
    observation_point_id: Optional[str] = Field(None, description="Observation point ID")
    child_count: Optional[int] = Field(None, description="Number of child branches")
    is_root: Optional[bool] = Field(None, description="Whether this is a root branch")


class BranchTreeNode(BaseModel):
    """Schema for branch tree node."""
    
    model_config = ConfigDict(
        from_attributes=True,
        use_enum_values=True
    )
    
    branch: BranchResponse = Field(..., description="Branch data")
    children: List["BranchTreeNode"] = Field(default_factory=list, description="Child nodes")
    depth: int = Field(..., description="Depth in the tree")


class BranchPath(BaseModel):
    """Schema for branch path response."""
    
    path: List[BranchResponse] = Field(..., description="Path from root to branch")
    total_depth: int = Field(..., description="Total depth of the path")


class BranchListResponse(BaseModel):
    """Schema for branch list response."""
    
    branches: List[BranchResponse] = Field(..., description="List of branches")
    total: int = Field(..., description="Total number of branches")


# Enable forward references for recursive model
BranchTreeNode.model_rebuild()
