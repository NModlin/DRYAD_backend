"""
Dryad Search Schemas

Pydantic schemas for advanced search functionality.
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum


class SearchType(str, Enum):
    """Type of search to perform."""
    SEMANTIC = "semantic"  # Vector similarity search
    KEYWORD = "keyword"    # Text-based keyword search
    HYBRID = "hybrid"      # Combination of semantic and keyword


class SearchScope(str, Enum):
    """Scope of search."""
    VESSELS = "vessels"      # Search vessel content
    DIALOGUES = "dialogues"  # Search dialogue history
    BRANCHES = "branches"    # Search branch descriptions
    ALL = "all"              # Search everything


class SortBy(str, Enum):
    """Sort options for search results."""
    RELEVANCE = "relevance"  # Sort by relevance score
    DATE_DESC = "date_desc"  # Newest first
    DATE_ASC = "date_asc"    # Oldest first
    TITLE = "title"          # Alphabetical by title


class SearchFilters(BaseModel):
    """Filters for search results."""
    
    grove_ids: Optional[List[str]] = Field(None, description="Filter by grove IDs")
    branch_ids: Optional[List[str]] = Field(None, description="Filter by branch IDs")
    tags: Optional[List[str]] = Field(None, description="Filter by tags")
    date_from: Optional[datetime] = Field(None, description="Filter by date from")
    date_to: Optional[datetime] = Field(None, description="Filter by date to")
    include_archived: bool = Field(False, description="Include archived items")
    min_score: Optional[float] = Field(None, ge=0.0, le=1.0, description="Minimum relevance score")


class AdvancedSearchRequest(BaseModel):
    """Request schema for advanced search."""
    
    query: str = Field(..., min_length=1, max_length=1000, description="Search query")
    search_type: SearchType = Field(SearchType.HYBRID, description="Type of search")
    scope: SearchScope = Field(SearchScope.ALL, description="Search scope")
    filters: Optional[SearchFilters] = Field(None, description="Search filters")
    sort_by: SortBy = Field(SortBy.RELEVANCE, description="Sort order")
    limit: int = Field(10, ge=1, le=100, description="Maximum results")
    offset: int = Field(0, ge=0, description="Results offset for pagination")
    include_snippets: bool = Field(True, description="Include content snippets")
    include_metadata: bool = Field(True, description="Include full metadata")


class SearchResultItem(BaseModel):
    """Individual search result."""
    
    id: str = Field(..., description="Item ID")
    type: str = Field(..., description="Item type (vessel, dialogue, branch)")
    title: str = Field(..., description="Item title")
    snippet: Optional[str] = Field(None, description="Content snippet")
    score: float = Field(..., ge=0.0, le=1.0, description="Relevance score")
    grove_id: str = Field(..., description="Grove ID")
    grove_name: str = Field(..., description="Grove name")
    branch_id: Optional[str] = Field(None, description="Branch ID")
    branch_name: Optional[str] = Field(None, description="Branch name")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")
    highlights: Optional[List[str]] = Field(None, description="Highlighted matches")


class SearchFacet(BaseModel):
    """Facet for filtering search results."""
    
    name: str = Field(..., description="Facet name")
    values: List[Dict[str, Any]] = Field(..., description="Facet values with counts")


class AdvancedSearchResponse(BaseModel):
    """Response schema for advanced search."""
    
    results: List[SearchResultItem] = Field(..., description="Search results")
    total: int = Field(..., description="Total number of results")
    query: str = Field(..., description="Original search query")
    search_type: SearchType = Field(..., description="Type of search performed")
    scope: SearchScope = Field(..., description="Search scope")
    execution_time: float = Field(..., description="Search execution time in seconds")
    facets: Optional[List[SearchFacet]] = Field(None, description="Available facets")
    suggestions: Optional[List[str]] = Field(None, description="Query suggestions")
    has_more: bool = Field(..., description="Whether more results are available")


class SearchSuggestionRequest(BaseModel):
    """Request schema for search suggestions."""
    
    query: str = Field(..., min_length=1, max_length=100, description="Partial query")
    scope: SearchScope = Field(SearchScope.ALL, description="Search scope")
    limit: int = Field(5, ge=1, le=20, description="Maximum suggestions")


class SearchSuggestionResponse(BaseModel):
    """Response schema for search suggestions."""
    
    suggestions: List[str] = Field(..., description="Query suggestions")
    query: str = Field(..., description="Original query")


class SavedSearch(BaseModel):
    """Schema for saved search."""
    
    id: str = Field(..., description="Saved search ID")
    name: str = Field(..., min_length=1, max_length=200, description="Search name")
    query: str = Field(..., description="Search query")
    search_type: SearchType = Field(..., description="Type of search")
    scope: SearchScope = Field(..., description="Search scope")
    filters: Optional[SearchFilters] = Field(None, description="Search filters")
    created_at: datetime = Field(..., description="Creation timestamp")
    last_used: Optional[datetime] = Field(None, description="Last used timestamp")
    use_count: int = Field(0, ge=0, description="Number of times used")


class SaveSearchRequest(BaseModel):
    """Request schema for saving a search."""
    
    name: str = Field(..., min_length=1, max_length=200, description="Search name")
    query: str = Field(..., description="Search query")
    search_type: SearchType = Field(SearchType.HYBRID, description="Type of search")
    scope: SearchScope = Field(SearchScope.ALL, description="Search scope")
    filters: Optional[SearchFilters] = Field(None, description="Search filters")


class SaveSearchResponse(BaseModel):
    """Response schema for saving a search."""
    
    saved_search: SavedSearch = Field(..., description="Saved search")
    message: str = Field(..., description="Success message")


class SearchHistoryItem(BaseModel):
    """Schema for search history item."""
    
    id: str = Field(..., description="History item ID")
    query: str = Field(..., description="Search query")
    search_type: SearchType = Field(..., description="Type of search")
    scope: SearchScope = Field(..., description="Search scope")
    results_count: int = Field(..., ge=0, description="Number of results")
    timestamp: datetime = Field(..., description="Search timestamp")


class SearchHistoryResponse(BaseModel):
    """Response schema for search history."""
    
    history: List[SearchHistoryItem] = Field(..., description="Search history")
    total: int = Field(..., description="Total history items")


class SearchAnalytics(BaseModel):
    """Schema for search analytics."""
    
    total_searches: int = Field(..., ge=0, description="Total number of searches")
    unique_queries: int = Field(..., ge=0, description="Number of unique queries")
    avg_results_per_search: float = Field(..., ge=0.0, description="Average results per search")
    most_common_queries: List[Dict[str, Any]] = Field(..., description="Most common queries")
    search_type_distribution: Dict[str, int] = Field(..., description="Distribution by search type")
    scope_distribution: Dict[str, int] = Field(..., description="Distribution by scope")
    avg_execution_time: float = Field(..., ge=0.0, description="Average execution time")


class SearchAnalyticsResponse(BaseModel):
    """Response schema for search analytics."""
    
    analytics: SearchAnalytics = Field(..., description="Search analytics")
    period_start: datetime = Field(..., description="Analytics period start")
    period_end: datetime = Field(..., description="Analytics period end")

