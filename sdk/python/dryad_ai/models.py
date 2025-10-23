"""
DRYAD.AI Data Models

Pydantic models for all DRYAD.AI API data structures.
"""

from datetime import datetime
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field


class Message(BaseModel):
    """Represents a message in a conversation."""
    
    id: str
    role: str
    content: str
    created_at: datetime
    tool_calls: Optional[str] = None
    extra_data: Optional[Dict[str, Any]] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Message":
        """Create a Message from a dictionary."""
        return cls(**data)


class Conversation(BaseModel):
    """Represents a conversation with messages."""
    
    id: str
    title: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    is_active: bool = True
    messages: List[Message] = Field(default_factory=list)
    message_count: Optional[int] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Conversation":
        """Create a Conversation from a dictionary."""
        messages = [Message.from_dict(msg) for msg in data.get("messages", [])]
        conversation_data = data.copy()
        conversation_data["messages"] = messages
        return cls(**conversation_data)


class Document(BaseModel):
    """Represents a document in the system."""
    
    id: str
    title: str
    content: Optional[str] = None
    content_type: str
    file_path: Optional[str] = None
    file_size: Optional[int] = None
    vector_id: Optional[str] = None
    embedding_model: Optional[str] = None
    doc_metadata: Optional[Dict[str, Any]] = None
    tags: Optional[List[str]] = None
    created_at: datetime
    updated_at: datetime
    is_active: bool = True
    chunks_created: Optional[int] = None
    vector_indexed: Optional[bool] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Document":
        """Create a Document from a dictionary."""
        return cls(**data)


class DocumentChunk(BaseModel):
    """Represents a chunk of a document."""
    
    id: str
    document_id: str
    content: str
    chunk_index: int
    chunk_size: int
    vector_id: Optional[str] = None
    embedding_model: Optional[str] = None
    start_position: Optional[int] = None
    end_position: Optional[int] = None
    chunk_metadata: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DocumentChunk":
        """Create a DocumentChunk from a dictionary."""
        return cls(**data)


class Agent(BaseModel):
    """Represents an AI agent and its capabilities."""
    
    name: str
    role: str
    goal: Optional[str] = None
    backstory: Optional[str] = None
    capabilities: Optional[str] = None
    tools: Optional[str] = None
    available: bool = True
    mock: bool = False
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Agent":
        """Create an Agent from a dictionary."""
        # Handle different data formats from API
        if "name" not in data:
            # If data is just the agent info without name
            return cls(name="unknown", **data)
        return cls(**data)


class Task(BaseModel):
    """Represents an orchestrator task."""
    
    task_id: str
    task_type: str
    status: str
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    execution_time: Optional[float] = None
    priority: int = 1
    timeout: Optional[int] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Task":
        """Create a Task from a dictionary."""
        return cls(**data)


class ComponentStatus(BaseModel):
    """Represents the status of a system component."""
    
    name: str
    available: bool
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ComponentStatus":
        """Create a ComponentStatus from a dictionary."""
        return cls(**data)


class SystemHealth(BaseModel):
    """Represents system health status."""
    
    status: str
    version: str
    components: List[ComponentStatus] = Field(default_factory=list)
    uptime: float = 0.0
    active_tasks: int = 0
    performance_metrics: Optional[Dict[str, Any]] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SystemHealth":
        """Create a SystemHealth from a dictionary."""
        components = [ComponentStatus.from_dict(comp) for comp in data.get("components", [])]
        health_data = data.copy()
        health_data["components"] = components
        return cls(**health_data)


class SearchResult(BaseModel):
    """Represents a document search result."""
    
    document_id: str
    title: str
    content: str
    score: float
    chunk_index: Optional[int] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SearchResult":
        """Create a SearchResult from a dictionary."""
        return cls(**data)


class WorkflowResult(BaseModel):
    """Represents the result of a multi-agent workflow."""
    
    workflow_type: str
    result: str
    agents_used: List[str]
    execution_time: float
    conversation_id: Optional[str] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "WorkflowResult":
        """Create a WorkflowResult from a dictionary."""
        return cls(**data)


class APICapabilities(BaseModel):
    """Represents API capabilities and features."""
    
    rest_api: bool = True
    graphql_api: bool = True
    websocket_api: bool = True
    real_time_subscriptions: bool = True
    supported_features: List[str] = Field(default_factory=list)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "APICapabilities":
        """Create APICapabilities from a dictionary."""
        return cls(**data)


class ConnectionInfo(BaseModel):
    """Represents WebSocket connection information."""
    
    total_connections: int
    connections_by_type: Dict[str, int] = Field(default_factory=dict)
    uptime: float = 0.0
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ConnectionInfo":
        """Create ConnectionInfo from a dictionary."""
        return cls(**data)


class WebSocketMessage(BaseModel):
    """Represents a WebSocket message."""
    
    type: str
    data: Optional[Dict[str, Any]] = None
    timestamp: Optional[datetime] = None
    subscription_id: Optional[str] = None
    error_code: Optional[str] = None
    message: Optional[str] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "WebSocketMessage":
        """Create a WebSocketMessage from a dictionary."""
        return cls(**data)


# Response wrapper models
class PaginatedResponse(BaseModel):
    """Generic paginated response wrapper."""
    
    items: List[Any]
    total: int
    limit: int
    offset: int
    has_more: bool = False
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any], item_class: type) -> "PaginatedResponse":
        """Create a PaginatedResponse from a dictionary."""
        items = [item_class.from_dict(item) for item in data.get("items", [])]
        response_data = data.copy()
        response_data["items"] = items
        response_data["has_more"] = (data.get("offset", 0) + len(items)) < data.get("total", 0)
        return cls(**response_data)


class APIResponse(BaseModel):
    """Generic API response wrapper."""
    
    success: bool = True
    data: Optional[Any] = None
    error: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)
    execution_time: Optional[float] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "APIResponse":
        """Create an APIResponse from a dictionary."""
        return cls(**data)
