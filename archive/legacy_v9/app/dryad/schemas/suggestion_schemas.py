"""
Branch Suggestion Schemas

Pydantic schemas for AI-powered branch suggestion system.
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


class SuggestionType(str, Enum):
    """Type of branch suggestion."""
    THEME = "theme"
    QUESTION = "question"
    DECISION = "decision"
    FACT = "fact"
    INSIGHT = "insight"


class SuggestionPriority(str, Enum):
    """Priority level for suggestions."""
    CRITICAL = "critical"  # 90-100 score
    HIGH = "high"          # 70-89 score
    MEDIUM = "medium"      # 40-69 score
    LOW = "low"            # 0-39 score


class BranchSuggestion(BaseModel):
    """Schema for a single branch suggestion."""
    
    model_config = ConfigDict(
        from_attributes=True
    )
    
    id: str = Field(..., description="Suggestion ID")
    dialogue_id: str = Field(..., description="Source dialogue ID")
    branch_id: str = Field(..., description="Parent branch ID")
    suggestion_type: SuggestionType = Field(..., description="Type of suggestion")
    title: str = Field(..., description="Suggested branch title")
    description: str = Field(..., description="Suggested branch description")
    priority_score: float = Field(..., ge=0.0, le=100.0, description="Priority score (0-100)")
    priority_level: SuggestionPriority = Field(..., description="Priority level")
    keywords: List[str] = Field(default_factory=list, description="Extracted keywords")
    estimated_depth: int = Field(..., ge=0, description="Estimated exploration depth")
    relevance_score: float = Field(..., ge=0.0, le=1.0, description="Relevance to parent branch")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence in suggestion")
    source_text: str = Field(..., description="Original text from oracle response")
    is_auto_created: bool = Field(default=False, description="Whether branch was auto-created")
    created_branch_id: Optional[str] = Field(None, description="ID of created branch if auto-created")
    created_at: Optional[datetime] = Field(None, description="Creation timestamp")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class GenerateSuggestionsRequest(BaseModel):
    """Request to generate branch suggestions from oracle response."""
    
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True
    )
    
    dialogue_id: str = Field(..., description="Dialogue ID to analyze")
    auto_create_threshold: Optional[float] = Field(
        80.0, 
        ge=0.0, 
        le=100.0,
        description="Priority score threshold for auto-creating branches"
    )
    max_suggestions: Optional[int] = Field(
        10,
        ge=1,
        le=50,
        description="Maximum number of suggestions to generate"
    )
    include_low_priority: Optional[bool] = Field(
        False,
        description="Include low priority suggestions"
    )


class GenerateSuggestionsResponse(BaseModel):
    """Response containing generated branch suggestions."""
    
    dialogue_id: str = Field(..., description="Source dialogue ID")
    branch_id: str = Field(..., description="Parent branch ID")
    total_suggestions: int = Field(..., description="Total suggestions generated")
    auto_created_count: int = Field(..., description="Number of auto-created branches")
    suggestions: List[BranchSuggestion] = Field(..., description="List of suggestions")
    processing_time_ms: float = Field(..., description="Processing time in milliseconds")


class SuggestionFilters(BaseModel):
    """Filters for querying suggestions."""
    
    model_config = ConfigDict(
        str_strip_whitespace=True
    )
    
    branch_id: Optional[str] = Field(None, description="Filter by branch ID")
    dialogue_id: Optional[str] = Field(None, description="Filter by dialogue ID")
    suggestion_types: Optional[List[SuggestionType]] = Field(None, description="Filter by suggestion types")
    priority_levels: Optional[List[SuggestionPriority]] = Field(None, description="Filter by priority levels")
    min_priority_score: Optional[float] = Field(None, ge=0.0, le=100.0, description="Minimum priority score")
    max_priority_score: Optional[float] = Field(None, ge=0.0, le=100.0, description="Maximum priority score")
    is_auto_created: Optional[bool] = Field(None, description="Filter by auto-created status")
    created_branch_exists: Optional[bool] = Field(None, description="Filter by whether branch was created")
    keywords: Optional[List[str]] = Field(None, description="Filter by keywords")


class ListSuggestionsRequest(BaseModel):
    """Request to list branch suggestions."""
    
    model_config = ConfigDict(
        str_strip_whitespace=True
    )
    
    filters: Optional[SuggestionFilters] = Field(None, description="Filters to apply")
    limit: int = Field(20, ge=1, le=100, description="Maximum results to return")
    offset: int = Field(0, ge=0, description="Offset for pagination")
    sort_by: Optional[str] = Field("priority_score", description="Field to sort by")
    sort_desc: bool = Field(True, description="Sort in descending order")


class ListSuggestionsResponse(BaseModel):
    """Response containing list of suggestions."""
    
    total: int = Field(..., description="Total suggestions matching filters")
    limit: int = Field(..., description="Limit applied")
    offset: int = Field(..., description="Offset applied")
    suggestions: List[BranchSuggestion] = Field(..., description="List of suggestions")


class CreateBranchFromSuggestionRequest(BaseModel):
    """Request to create a branch from a suggestion."""
    
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True
    )
    
    suggestion_id: str = Field(..., description="Suggestion ID")
    custom_name: Optional[str] = Field(None, description="Custom branch name (overrides suggestion)")
    custom_description: Optional[str] = Field(None, description="Custom description (overrides suggestion)")


class CreateBranchFromSuggestionResponse(BaseModel):
    """Response after creating branch from suggestion."""
    
    suggestion_id: str = Field(..., description="Source suggestion ID")
    branch_id: str = Field(..., description="Created branch ID")
    branch_name: str = Field(..., description="Branch name")
    success: bool = Field(..., description="Whether creation was successful")
    message: str = Field(..., description="Success or error message")


class SuggestionAnalytics(BaseModel):
    """Analytics for branch suggestions."""
    
    total_suggestions: int = Field(..., description="Total suggestions generated")
    auto_created_count: int = Field(..., description="Branches auto-created")
    manually_created_count: int = Field(..., description="Branches manually created from suggestions")
    by_type: Dict[str, int] = Field(..., description="Count by suggestion type")
    by_priority: Dict[str, int] = Field(..., description="Count by priority level")
    average_priority_score: float = Field(..., description="Average priority score")
    average_confidence: float = Field(..., description="Average confidence score")
    top_keywords: List[Dict[str, Any]] = Field(..., description="Most common keywords")


class SuggestionAnalyticsRequest(BaseModel):
    """Request for suggestion analytics."""
    
    model_config = ConfigDict(
        str_strip_whitespace=True
    )
    
    branch_id: Optional[str] = Field(None, description="Filter by branch ID")
    grove_id: Optional[str] = Field(None, description="Filter by grove ID")
    start_date: Optional[datetime] = Field(None, description="Start date for analytics")
    end_date: Optional[datetime] = Field(None, description="End date for analytics")


class SuggestionAnalyticsResponse(BaseModel):
    """Response containing suggestion analytics."""
    
    analytics: SuggestionAnalytics = Field(..., description="Analytics data")
    period_start: Optional[datetime] = Field(None, description="Analytics period start")
    period_end: Optional[datetime] = Field(None, description="Analytics period end")
    generated_at: datetime = Field(..., description="Analytics generation timestamp")


class UpdateSuggestionRequest(BaseModel):
    """Request to update a suggestion."""
    
    model_config = ConfigDict(
        str_strip_whitespace=True
    )
    
    title: Optional[str] = Field(None, description="Updated title")
    description: Optional[str] = Field(None, description="Updated description")
    priority_score: Optional[float] = Field(None, ge=0.0, le=100.0, description="Updated priority score")
    keywords: Optional[List[str]] = Field(None, description="Updated keywords")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Updated metadata")


class DeleteSuggestionRequest(BaseModel):
    """Request to delete a suggestion."""
    
    suggestion_id: str = Field(..., description="Suggestion ID to delete")
    reason: Optional[str] = Field(None, description="Reason for deletion")


class DeleteSuggestionResponse(BaseModel):
    """Response after deleting a suggestion."""
    
    suggestion_id: str = Field(..., description="Deleted suggestion ID")
    success: bool = Field(..., description="Whether deletion was successful")
    message: str = Field(..., description="Success or error message")

