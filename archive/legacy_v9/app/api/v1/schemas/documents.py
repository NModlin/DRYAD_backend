# app/api/v1/schemas/documents.py
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Annotated
from datetime import datetime
from enum import Enum

class SearchType(str, Enum):
    """Available search types for semantic search."""
    CHUNKS = "chunks"
    DOCUMENTS = "documents"
    BOTH = "both"

class DocumentCreate(BaseModel):
    """Schema for creating a new document."""
    title: str = Field(..., min_length=1, max_length=500, description="Document title")
    content: str = Field(..., min_length=1, description="Document content")
    content_type: str = Field(default="text/plain", description="MIME type of the content")
    doc_metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")
    tags: Optional[List[str]] = Field(None, description="Tags for categorization")
    chunk_size: int = Field(default=1000, ge=100, le=5000, description="Size of text chunks")
    chunk_overlap: int = Field(default=200, ge=0, le=1000, description="Overlap between chunks")

class DocumentResponse(BaseModel):
    """Schema for document responses."""
    id: str = Field(..., description="Document ID")
    title: str = Field(..., description="Document title")
    content: str = Field(..., description="Document content")
    content_type: str = Field(..., description="MIME type")
    file_path: Optional[str] = Field(None, description="Original file path")
    file_size: Optional[int] = Field(None, description="File size in bytes")
    vector_id: Optional[str] = Field(None, description="Vector store ID")
    embedding_model: Optional[str] = Field(None, description="Embedding model used")
    doc_metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")
    tags: Optional[List[str]] = Field(None, description="Document tags")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    is_active: bool = Field(..., description="Whether document is active")

class DocumentListResponse(BaseModel):
    """Schema for document list responses."""
    documents: List[DocumentResponse] = Field(..., description="List of documents")
    total: int = Field(..., description="Total number of documents")
    limit: int = Field(..., description="Limit used for pagination")
    offset: int = Field(..., description="Offset used for pagination")

class SemanticSearchRequest(BaseModel):
    """Schema for semantic search requests."""
    query: str = Field(..., min_length=1, description="Search query")
    limit: int = Field(default=5, ge=1, le=50, description="Maximum number of results")
    score_threshold: float = Field(default=0.7, ge=0.0, le=1.0, description="Minimum similarity score")
    search_type: SearchType = Field(default=SearchType.CHUNKS, description="Type of search to perform")
    filter_conditions: Optional[Dict[str, Any]] = Field(None, description="Additional filter conditions")
    conversation_id: Optional[str] = Field(None, description="Conversation ID for context")

class SearchResult(BaseModel):
    """Schema for individual search results."""
    id: str = Field(..., description="Result ID")
    score: float = Field(..., description="Similarity score")
    content: str = Field(..., description="Content snippet")
    document_id: str = Field(..., description="Source document ID")
    document_title: str = Field(..., description="Source document title")
    document_type: str = Field(..., description="Document content type")
    chunk_index: Optional[int] = Field(None, description="Chunk index if applicable")
    metadata: Dict[str, Any] = Field(..., description="Additional metadata")

class AdvancedSearchRequest(BaseModel):
    """Schema for advanced search requests with faceted filtering."""
    query: str = Field(..., min_length=1, description="Search query")

    # Filtering options
    content_types: Optional[List[str]] = Field(None, description="Filter by content types")
    tags: Optional[List[str]] = Field(None, description="Filter by tags")
    date_from: Optional[datetime] = Field(None, description="Filter documents from this date")
    date_to: Optional[datetime] = Field(None, description="Filter documents to this date")
    file_size_min: Optional[int] = Field(None, ge=0, description="Minimum file size in bytes")
    file_size_max: Optional[int] = Field(None, ge=0, description="Maximum file size in bytes")
    metadata_filters: Optional[Dict[str, Any]] = Field(None, description="Filter by metadata fields")

    # Search options
    search_type: str = Field(default="hybrid", description="Search type: semantic, bm25, or hybrid")
    limit: int = Field(default=10, ge=1, le=100, description="Number of results to return")
    offset: int = Field(default=0, ge=0, description="Offset for pagination")
    score_threshold: float = Field(default=0.0, ge=0.0, le=1.0, description="Minimum relevance score")

    # Sorting options
    sort_by: str = Field(default="relevance", description="Sort by: relevance, date, title, file_size")
    sort_order: str = Field(default="desc", description="Sort order: asc or desc")

    # Faceting options
    include_facets: bool = Field(default=True, description="Include facet counts in response")
    facet_fields: Optional[List[str]] = Field(None, description="Specific facet fields to include")

class SearchFacet(BaseModel):
    """Schema for search facets."""
    field: str = Field(..., description="Facet field name")
    values: Dict[str, int] = Field(..., description="Facet values and their counts")

class AdvancedSearchResponse(BaseModel):
    """Schema for advanced search responses."""
    query: str = Field(..., description="Original search query")
    results: List[SearchResult] = Field(..., description="Search results")
    total_results: int = Field(..., description="Total number of matching documents")
    limit: int = Field(..., description="Results limit used")
    offset: int = Field(..., description="Results offset used")
    search_time_ms: float = Field(..., description="Search execution time in milliseconds")

    # Faceting information
    facets: Optional[List[SearchFacet]] = Field(None, description="Search facets")

    # Search metadata
    search_metadata: Dict[str, Any] = Field(..., description="Search execution metadata")
    filters_applied: Dict[str, Any] = Field(..., description="Applied filters summary")

class SemanticSearchResponse(BaseModel):
    """Schema for semantic search responses."""
    query: str = Field(..., description="Original search query")
    results: List[SearchResult] = Field(..., description="Search results")
    total_found: int = Field(..., description="Total number of results found")
    search_query_id: Optional[str] = Field(None, description="ID of the search query record")
    execution_time_ms: Optional[float] = Field(None, description="Search execution time")

class RAGRequest(BaseModel):
    """Schema for RAG (Retrieval-Augmented Generation) requests."""
    query: str = Field(..., min_length=1, description="User query")
    conversation_id: Optional[str] = Field(None, description="Conversation ID for context")
    search_limit: Optional[int] = Field(5, ge=1, le=20, description="Number of documents to retrieve")
    score_threshold: Optional[float] = Field(0.7, ge=0.0, le=1.0, description="Minimum similarity score")
    filter_conditions: Optional[Dict[str, Any]] = Field(None, description="Search filter conditions")
    use_multi_agent: bool = Field(False, description="Whether to use multi-agent system")
    search_type: SearchType = Field(default=SearchType.CHUNKS, description="Type of search to perform")
    save_conversation: bool = Field(True, description="Whether to save to conversation history")

class RAGResponse(BaseModel):
    """Schema for RAG responses."""
    query: str = Field(..., description="Original user query")
    response: str = Field(..., description="Generated response")
    retrieved_documents: List[SearchResult] = Field(..., description="Documents used for context")
    context_used: bool = Field(..., description="Whether retrieved context was used")
    search_metadata: Dict[str, Any] = Field(..., description="Search operation metadata")
    agent_metadata: Dict[str, Any] = Field(..., description="Agent processing metadata")
    conversation_id: Optional[str] = Field(None, description="Conversation ID if saved")
    timestamp: str = Field(..., description="Response timestamp")

class DocumentUploadResponse(BaseModel):
    """Schema for document upload responses."""
    document_id: str = Field(..., description="ID of the created document")
    title: str = Field(..., description="Document title")
    file_size: int = Field(..., description="File size in bytes")
    chunks_created: int = Field(..., description="Number of chunks created")
    vector_ids: List[str] = Field(..., description="Vector store IDs")
    processing_time_ms: float = Field(..., description="Processing time")

class SystemStatusResponse(BaseModel):
    """Schema for RAG system status responses."""
    status: str = Field(..., description="System status")
    total_documents: int = Field(..., description="Total number of documents")
    vector_store: Dict[str, Any] = Field(..., description="Vector store information")
    search_analytics: Dict[str, Any] = Field(..., description="Search analytics")
    configuration: Dict[str, Any] = Field(..., description="System configuration")

class QuerySuggestionsRequest(BaseModel):
    """Schema for query suggestion requests."""
    query: str = Field(..., min_length=1, description="Base query for suggestions")
    limit: int = Field(default=5, ge=1, le=10, description="Number of suggestions to return")

class QuerySuggestionsResponse(BaseModel):
    """Schema for query suggestion responses."""
    original_query: str = Field(..., description="Original query")
    suggestions: List[str] = Field(..., description="Suggested related queries")
    total_suggestions: int = Field(..., description="Total number of suggestions generated")

class DocumentChunkResponse(BaseModel):
    """Schema for document chunk responses."""
    id: str = Field(..., description="Chunk ID")
    document_id: str = Field(..., description="Parent document ID")
    content: str = Field(..., description="Chunk content")
    chunk_index: int = Field(..., description="Chunk index in document")
    chunk_size: int = Field(..., description="Chunk size in characters")
    vector_id: Optional[str] = Field(None, description="Vector store ID")
    start_position: Optional[int] = Field(None, description="Start position in document")
    end_position: Optional[int] = Field(None, description="End position in document")
    chunk_metadata: Optional[Dict[str, Any]] = Field(None, description="Chunk metadata")
    created_at: datetime = Field(..., description="Creation timestamp")

class SearchAnalyticsResponse(BaseModel):
    """Schema for search analytics responses."""
    total_searches: int = Field(..., description="Total number of searches")
    avg_execution_time_ms: float = Field(..., description="Average execution time")
    avg_results_per_search: float = Field(..., description="Average results per search")
    popular_queries: List[List] = Field(..., description="Most popular queries")
    vector_store_info: Dict[str, Any] = Field(..., description="Vector store information")

# Error schemas
class DocumentError(BaseModel):
    """Schema for document-related errors."""
    error_type: str = Field(..., description="Type of error")
    message: str = Field(..., description="Error message")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")

class ValidationError(BaseModel):
    """Schema for validation errors."""
    field: str = Field(..., description="Field that failed validation")
    message: str = Field(..., description="Validation error message")
    value: Any = Field(..., description="Invalid value")

class ContentAnalysisRequest(BaseModel):
    """Schema for content analysis requests."""
    document_id: str = Field(..., description="Document ID to analyze")
    include_summary: bool = Field(default=True, description="Include AI-generated summary")
    include_tags: bool = Field(default=True, description="Include automatic tags")
    include_entities: bool = Field(default=True, description="Include entity extraction")
    force_reanalysis: bool = Field(default=False, description="Force re-analysis even if already analyzed")

class EntityInfo(BaseModel):
    """Schema for extracted entities."""
    persons: List[str] = Field(default_factory=list, description="Extracted person names")
    organizations: List[str] = Field(default_factory=list, description="Extracted organization names")
    locations: List[str] = Field(default_factory=list, description="Extracted location names")
    technologies: List[str] = Field(default_factory=list, description="Extracted technology terms")
    concepts: List[str] = Field(default_factory=list, description="Extracted concept terms")

class ContentAnalysisResponse(BaseModel):
    """Schema for content analysis responses."""
    document_id: str = Field(..., description="Analyzed document ID")
    title: str = Field(..., description="Document title")
    content_length: int = Field(..., description="Content length in characters")
    analysis_timestamp: Optional[str] = Field(None, description="Analysis timestamp")

    # Analysis results
    tags: List[str] = Field(default_factory=list, description="Automatically generated tags")
    summary: str = Field(..., description="AI-generated summary")
    entities: EntityInfo = Field(..., description="Extracted entities")
    topics: List[str] = Field(default_factory=list, description="Extracted topics")
    sentiment: str = Field(..., description="Sentiment analysis result")
    readability_score: float = Field(..., description="Readability score (0-1)")
    key_phrases: List[str] = Field(default_factory=list, description="Key phrases extracted")

    # Processing metadata
    processing_time_ms: float = Field(..., description="Analysis processing time")
    llm_used: bool = Field(..., description="Whether LLM was used for analysis")

class BatchAnalysisRequest(BaseModel):
    """Schema for batch content analysis requests."""
    document_ids: Annotated[List[str], Field(min_length=1, max_length=50, description="Document IDs to analyze")]
    include_summary: bool = Field(default=True, description="Include AI-generated summaries")
    include_tags: bool = Field(default=True, description="Include automatic tags")
    include_entities: bool = Field(default=True, description="Include entity extraction")
    force_reanalysis: bool = Field(default=False, description="Force re-analysis for all documents")

class BatchAnalysisResponse(BaseModel):
    """Schema for batch content analysis responses."""
    total_documents: int = Field(..., description="Total documents requested for analysis")
    successful_analyses: int = Field(..., description="Number of successful analyses")
    failed_analyses: int = Field(..., description="Number of failed analyses")
    processing_time_ms: float = Field(..., description="Total processing time")

    results: List[ContentAnalysisResponse] = Field(..., description="Analysis results")
    failures: List[Dict[str, str]] = Field(default_factory=list, description="Failed analysis details")

class DocumentAnalyticsResponse(BaseModel):
    """Schema for document analytics responses."""
    document_id: str = Field(..., description="Document ID")
    title: str = Field(..., description="Document title")
    content_type: str = Field(..., description="Document content type")

    # Usage metrics
    view_count: int = Field(..., description="Number of views")
    search_count: int = Field(..., description="Number of times found in searches")
    download_count: int = Field(..., description="Number of downloads")
    share_count: int = Field(..., description="Number of shares")

    # Engagement metrics
    avg_time_spent: float = Field(..., description="Average time spent viewing (seconds)")
    bounce_rate: float = Field(..., description="Bounce rate percentage")
    avg_search_rank: float = Field(..., description="Average search result rank")
    click_through_rate: float = Field(..., description="Click-through rate from searches")

    # Timestamps
    created_at: Optional[str] = Field(None, description="Document creation timestamp")
    last_updated: Optional[str] = Field(None, description="Analytics last update timestamp")

class PopularQuery(BaseModel):
    """Schema for popular search queries."""
    query: str = Field(..., description="Search query")
    search_count: int = Field(..., description="Number of times searched")
    avg_execution_time_ms: float = Field(..., description="Average execution time")
    avg_results_count: float = Field(..., description="Average number of results")

class DailySearchVolume(BaseModel):
    """Schema for daily search volume data."""
    date: Optional[str] = Field(None, description="Date")
    search_count: int = Field(..., description="Number of searches on this date")

class SearchAnalyticsResponse(BaseModel):
    """Schema for search analytics responses."""
    popular_queries: List[PopularQuery] = Field(..., description="Most popular search queries")
    search_type_distribution: Dict[str, int] = Field(..., description="Distribution of search types")
    daily_search_volume: List[DailySearchVolume] = Field(..., description="Daily search volume")
    period_days: int = Field(..., description="Analysis period in days")

class UserEngagementResponse(BaseModel):
    """Schema for user engagement responses."""
    action_distribution: Dict[str, int] = Field(..., description="Distribution of user actions")
    unique_sessions: int = Field(..., description="Number of unique user sessions")
    avg_session_duration_seconds: float = Field(..., description="Average session duration")
    period_days: int = Field(..., description="Analysis period in days")

class AnalyticsDashboardResponse(BaseModel):
    """Schema for analytics dashboard responses."""
    document_analytics: List[DocumentAnalyticsResponse] = Field(..., description="Document analytics")
    search_analytics: SearchAnalyticsResponse = Field(..., description="Search analytics")
    user_engagement: UserEngagementResponse = Field(..., description="User engagement metrics")

    # Summary metrics
    total_documents: int = Field(..., description="Total number of documents")
    total_views: int = Field(..., description="Total document views")
    total_searches: int = Field(..., description="Total searches performed")
    total_sessions: int = Field(..., description="Total user sessions")

    # Performance metrics
    avg_search_time_ms: float = Field(..., description="Average search execution time")
    most_popular_document: Optional[str] = Field(None, description="Most popular document title")
    most_popular_query: Optional[str] = Field(None, description="Most popular search query")

    generated_at: str = Field(..., description="Dashboard generation timestamp")

class DocumentVersionResponse(BaseModel):
    """Schema for document version responses."""
    id: str = Field(..., description="Version ID")
    document_id: str = Field(..., description="Document ID")
    version_number: int = Field(..., description="Version number")

    # Version content
    title: str = Field(..., description="Document title at this version")
    content: str = Field(..., description="Document content at this version")
    content_type: str = Field(..., description="Document content type")
    file_size: Optional[int] = Field(None, description="File size in bytes")

    # Version metadata
    doc_metadata: Optional[Dict[str, Any]] = Field(None, description="Document metadata")
    tags: Optional[List[str]] = Field(None, description="Document tags")

    # Change information
    change_summary: Optional[str] = Field(None, description="Summary of changes")
    change_type: str = Field(..., description="Type of change")
    changed_fields: Optional[List[str]] = Field(None, description="Fields that changed")

    # Version control
    is_current: bool = Field(..., description="Is this the current version")
    parent_version_id: Optional[str] = Field(None, description="Parent version ID")

    # User information
    created_by: Optional[str] = Field(None, description="User who created this version")
    created_by_session: Optional[str] = Field(None, description="Session that created this version")

    # Timestamps
    created_at: Optional[str] = Field(None, description="Version creation timestamp")

class DocumentUpdateRequest(BaseModel):
    """Schema for document update requests with versioning."""
    title: Optional[str] = Field(None, description="New document title")
    content: Optional[str] = Field(None, description="New document content")
    content_type: Optional[str] = Field(None, description="New content type")
    doc_metadata: Optional[Dict[str, Any]] = Field(None, description="New metadata")
    tags: Optional[List[str]] = Field(None, description="New tags")

    # Versioning information
    change_summary: Optional[str] = Field(None, description="Summary of changes being made")
    created_by: Optional[str] = Field(None, description="User making the changes")
    created_by_session: Optional[str] = Field(None, description="Session making the changes")

class DocumentRollbackRequest(BaseModel):
    """Schema for document rollback requests."""
    target_version_number: int = Field(..., ge=1, description="Version number to rollback to")
    created_by: Optional[str] = Field(None, description="User performing rollback")
    created_by_session: Optional[str] = Field(None, description="Session performing rollback")

class VersionComparisonRequest(BaseModel):
    """Schema for version comparison requests."""
    version1_number: int = Field(..., ge=1, description="First version number")
    version2_number: int = Field(..., ge=1, description="Second version number")

class VersionDifference(BaseModel):
    """Schema for version differences."""
    field: str = Field(..., description="Field name")
    version1_value: Any = Field(..., description="Value in version 1")
    version2_value: Any = Field(..., description="Value in version 2")
    changed: bool = Field(..., description="Whether the field changed")

class VersionComparisonResponse(BaseModel):
    """Schema for version comparison responses."""
    document_id: str = Field(..., description="Document ID")
    version1: Dict[str, Any] = Field(..., description="Version 1 information")
    version2: Dict[str, Any] = Field(..., description="Version 2 information")
    differences: Dict[str, Any] = Field(..., description="Field differences")

class ChangeLogEntry(BaseModel):
    """Schema for change log entries."""
    id: str = Field(..., description="Change log entry ID")
    version_id: str = Field(..., description="Version ID")
    field_name: str = Field(..., description="Field that changed")
    old_value: Optional[str] = Field(None, description="Previous value")
    new_value: Optional[str] = Field(None, description="New value")
    change_type: str = Field(..., description="Type of change")
    value_type: Optional[str] = Field(None, description="Data type of the value")
    is_truncated: bool = Field(..., description="Whether values were truncated")
    created_at: Optional[str] = Field(None, description="Change timestamp")

class DocumentHistoryResponse(BaseModel):
    """Schema for document history responses."""
    document_id: str = Field(..., description="Document ID")
    versions: List[DocumentVersionResponse] = Field(..., description="Document versions")
    change_logs: List[ChangeLogEntry] = Field(..., description="Detailed change logs")
    total_versions: int = Field(..., description="Total number of versions")
    current_version: int = Field(..., description="Current version number")
