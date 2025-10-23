"""
RADAR Integration Schemas

Pydantic models for RADAR ↔ Dryad.AI integration.
Matches the expected request/response formats from RADAR's integration guide.
"""

from datetime import datetime
from typing import Dict, List, Optional, Any, Literal
from pydantic import BaseModel, Field


# ============================================================================
# Chat Schemas
# ============================================================================

class RADARContext(BaseModel):
    """Context data provided by RADAR."""
    userId: Optional[str] = Field(None, description="RADAR user ID")
    username: Optional[str] = Field(None, description="RADAR username")
    department: Optional[str] = Field(None, description="User department")
    # Additional context fields
    user: Optional[Dict[str, Any]] = Field(None, description="Full user object")
    session: Optional[Dict[str, Any]] = Field(None, description="Session information")
    environment: Optional[Dict[str, Any]] = Field(None, description="Environment data (AD domain, connections)")
    recentActions: Optional[List[Dict[str, Any]]] = Field(None, description="Recent user actions")


class ChatMessageRequest(BaseModel):
    """Request schema for RADAR chat messages."""
    conversationId: Optional[str] = Field(None, description="Existing conversation ID or null for new")
    message: str = Field(..., description="User message content")
    context: Optional[RADARContext] = Field(None, description="RADAR context data")


class ChatMessageResponse(BaseModel):
    """Response schema for RADAR chat messages."""
    success: bool = Field(True, description="Whether the request was successful")
    conversationId: str = Field(..., description="Conversation ID")
    messageId: str = Field(..., description="Message ID")
    response: str = Field(..., description="AI-generated response")
    suggestions: Optional[List[str]] = Field(None, description="Suggested follow-up actions")
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Response metadata (model, tokensUsed, responseTime)"
    )


class ConversationListItem(BaseModel):
    """Single conversation in list response."""
    id: str = Field(..., description="Conversation ID")
    title: Optional[str] = Field(None, description="Conversation title")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    message_count: int = Field(0, description="Number of messages")
    is_active: bool = Field(True, description="Whether conversation is active")


class ConversationListResponse(BaseModel):
    """Response schema for conversation list."""
    success: bool = Field(True, description="Whether the request was successful")
    conversations: List[ConversationListItem] = Field(default_factory=list)
    total: int = Field(0, description="Total number of conversations")
    limit: int = Field(50, description="Results per page")
    offset: int = Field(0, description="Offset for pagination")


class MessageItem(BaseModel):
    """Single message in conversation."""
    id: str = Field(..., description="Message ID")
    role: str = Field(..., description="Message role (user/assistant/system)")
    content: str = Field(..., description="Message content")
    created_at: datetime = Field(..., description="Creation timestamp")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional message metadata")


class ConversationMessagesResponse(BaseModel):
    """Response schema for conversation messages."""
    success: bool = Field(True, description="Whether the request was successful")
    conversationId: str = Field(..., description="Conversation ID")
    messages: List[MessageItem] = Field(default_factory=list)
    total: int = Field(0, description="Total number of messages")


# ============================================================================
# Knowledge Base Schemas
# ============================================================================

class KnowledgeSearchFilters(BaseModel):
    """Filters for knowledge base search."""
    category: Optional[str] = Field(None, description="Filter by category")
    tags: Optional[List[str]] = Field(None, description="Filter by tags")
    source: Optional[str] = Field(None, description="Filter by source (confluence, jira, etc.)")


class KnowledgeSearchRequest(BaseModel):
    """Request schema for knowledge base search."""
    query: str = Field(..., description="Search query")
    filters: Optional[KnowledgeSearchFilters] = Field(None, description="Search filters")
    limit: int = Field(5, ge=1, le=20, description="Maximum number of results")


class KnowledgeSearchResult(BaseModel):
    """Single knowledge base search result."""
    id: str = Field(..., description="Document ID")
    title: str = Field(..., description="Document title")
    content: str = Field(..., description="Document content excerpt")
    relevanceScore: float = Field(..., description="Relevance score (0-1)")
    source: str = Field(..., description="Source system (confluence, jira, etc.)")
    url: Optional[str] = Field(None, description="URL to original document")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class KnowledgeSearchResponse(BaseModel):
    """Response schema for knowledge base search."""
    success: bool = Field(True, description="Whether the request was successful")
    results: List[KnowledgeSearchResult] = Field(default_factory=list)
    totalResults: int = Field(0, description="Total number of results found")
    queryTime: int = Field(0, description="Query execution time in milliseconds")


# ============================================================================
# Feedback Schemas
# ============================================================================

class FeedbackRequest(BaseModel):
    """Request schema for user feedback."""
    messageId: str = Field(..., description="Message ID being rated")
    rating: Literal["positive", "negative"] = Field(..., description="Feedback rating")
    comment: Optional[str] = Field(None, description="Optional feedback comment")


class FeedbackResponse(BaseModel):
    """Response schema for feedback submission."""
    success: bool = Field(True, description="Whether feedback was recorded")
    feedbackId: str = Field(..., description="Feedback record ID")
    message: str = Field("Feedback recorded successfully", description="Response message")


# ============================================================================
# Error Schemas
# ============================================================================

class RADARErrorResponse(BaseModel):
    """Standard error response for RADAR integration."""
    success: bool = Field(False, description="Always false for errors")
    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Human-readable error message")
    code: str = Field(..., description="Error code")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")


# ============================================================================
# Health Check Schemas
# ============================================================================

class RADARHealthResponse(BaseModel):
    """Health check response for RADAR integration."""
    status: str = Field("healthy", description="Overall health status")
    database: str = Field("connected", description="Database connection status")
    redis: Optional[str] = Field(None, description="Redis connection status (if applicable)")
    dryad: str = Field("connected", description="Dryad.AI backend status")
    llm: Optional[str] = Field(None, description="LLM availability status")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Health check timestamp")

