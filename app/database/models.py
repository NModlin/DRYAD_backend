# app/database/models.py
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean, JSON, LargeBinary, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.database import Base
import uuid


class User(Base):
    """Model for OAuth2 authenticated users."""
    __tablename__ = "users"

    id = Column(String, primary_key=True)  # Google sub or other OAuth provider ID
    email = Column(String(255), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    picture = Column(String(500), nullable=True)  # Profile picture URL
    email_verified = Column(Boolean, default=False)

    # Authorization
    roles = Column(JSON, default=lambda: ["user"])  # List of roles
    permissions = Column(JSON, default=lambda: ["read", "write"])  # List of permissions

    # OAuth2 provider info
    provider = Column(String(50), default="google")  # OAuth provider
    provider_id = Column(String(255), nullable=True)  # Provider-specific ID

    # Multi-client support
    client_app_id = Column(String(255), ForeignKey("client_applications.id"), nullable=True, index=True)
    tenant_id = Column(String(255), nullable=True, index=True)  # For grouping users within client apps
    organization_id = Column(String(255), ForeignKey("organizations.id"), nullable=True, index=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    last_login = Column(DateTime(timezone=True), nullable=True)

    # Status
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)

    # Relationships
    conversations = relationship("Conversation", back_populates="user", cascade="all, delete-orphan")
    documents = relationship("Document", back_populates="user", cascade="all, delete-orphan")
    client_application = relationship("ClientApplication", back_populates="users")
    organization = relationship("Organization", back_populates="users")

    def __repr__(self):
        return f"<User(id={self.id}, email={self.email}, name={self.name}, client_app={self.client_app_id})>"


class RefreshToken(Base):
    """Model for OAuth2 refresh tokens."""
    __tablename__ = "refresh_tokens"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    token_hash = Column(String(255), unique=True, nullable=False, index=True)  # SHA256 hash of token
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    # Token metadata
    expires_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_used_at = Column(DateTime(timezone=True), nullable=True)

    # Security and tracking
    is_revoked = Column(Boolean, default=False)
    revoked_at = Column(DateTime(timezone=True), nullable=True)
    device_info = Column(String(500), nullable=True)  # User agent or device identifier
    ip_address = Column(String(45), nullable=True)  # IPv4 or IPv6

    # Token rotation
    token_version = Column(Integer, default=1)  # For token rotation/invalidation
    parent_token_id = Column(String, ForeignKey("refresh_tokens.id"), nullable=True)  # For token rotation chain

    # Relationships
    user = relationship("User", backref="refresh_tokens")
    parent_token = relationship("RefreshToken", remote_side=[id], backref="child_tokens")

    def __repr__(self):
        return f"<RefreshToken(id={self.id}, user_id={self.user_id}, expires_at={self.expires_at})>"


class Conversation(Base):
    """Model for chat conversations."""
    __tablename__ = "conversations"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    title = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    is_active = Column(Boolean, default=True)

    # Relationships
    user = relationship("User", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")
    multimodal_content = relationship("MultiModalContent", back_populates="conversation", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Conversation(id={self.id}, title={self.title}, user_id={self.user_id})>"


class Message(Base):
    """Model for individual messages in conversations."""
    __tablename__ = "messages"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    conversation_id = Column(String, ForeignKey("conversations.id"), nullable=False)
    role = Column(String(50), nullable=False)  # 'user', 'assistant', 'system'
    content = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Additional metadata
    tool_calls = Column(Text, nullable=True)  # JSON string for tool calls
    extra_data = Column(Text, nullable=True)  # JSON string for additional metadata
    
    # Relationship to conversation
    conversation = relationship("Conversation", back_populates="messages")

    def __repr__(self):
        return f"<Message(id={self.id}, role={self.role}, conversation_id={self.conversation_id})>"


class Document(Base):
    """
    Model for storing documents and their metadata for vector search and RAG.
    """
    __tablename__ = "documents"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    title = Column(String(500), nullable=False)
    content = Column(Text, nullable=False)
    content_type = Column(String(100), default="text/plain")  # MIME type
    file_path = Column(String(1000), nullable=True)  # Original file path if uploaded
    file_size = Column(Integer, nullable=True)  # File size in bytes

    # Vector store integration
    vector_id = Column(String, nullable=True)  # ID in vector store (Qdrant)
    embedding_model = Column(String(200), nullable=True)  # Model used for embeddings

    # Metadata
    doc_metadata = Column(JSON, nullable=True)  # Additional metadata as JSON
    tags = Column(JSON, nullable=True)  # Tags for categorization

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Soft delete
    is_active = Column(Boolean, default=True)

    # Relationships
    user = relationship("User", back_populates="documents")
    chunks = relationship("DocumentChunk", back_populates="document", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Document(id={self.id}, title={self.title[:50]}, user_id={self.user_id})>"


class DocumentChunk(Base):
    """
    Model for storing document chunks for better vector search performance.
    """
    __tablename__ = "document_chunks"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    document_id = Column(String, ForeignKey("documents.id"), nullable=False)

    # Chunk content
    content = Column(Text, nullable=False)
    chunk_index = Column(Integer, nullable=False)  # Order within document
    chunk_size = Column(Integer, nullable=False)  # Size in characters

    # Vector store integration
    vector_id = Column(String, nullable=True)  # ID in vector store
    embedding_model = Column(String(200), nullable=True)

    # Chunk metadata
    start_position = Column(Integer, nullable=True)  # Start position in original document
    end_position = Column(Integer, nullable=True)  # End position in original document
    chunk_metadata = Column(JSON, nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    document = relationship("Document", back_populates="chunks")

    def __repr__(self):
        return f"<DocumentChunk(id={self.id}, document_id={self.document_id}, index={self.chunk_index})>"


class DocumentAnalytics(Base):
    """
    Model for tracking document analytics and usage metrics.
    """
    __tablename__ = "document_analytics"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    document_id = Column(String, ForeignKey("documents.id"), nullable=False)

    # Usage metrics
    view_count = Column(Integer, default=0)
    search_count = Column(Integer, default=0)  # How many times found in searches
    download_count = Column(Integer, default=0)
    share_count = Column(Integer, default=0)

    # Engagement metrics
    avg_time_spent = Column(Float, default=0.0)  # Average time spent viewing (seconds)
    bounce_rate = Column(Float, default=0.0)  # Percentage of quick exits

    # Search performance
    avg_search_rank = Column(Float, default=0.0)  # Average position in search results
    click_through_rate = Column(Float, default=0.0)  # CTR from search results

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationship
    document = relationship("Document", backref="analytics")

    def __repr__(self):
        return f"<DocumentAnalytics(document_id={self.document_id}, views={self.view_count})>"


class SearchAnalytics(Base):
    """
    Model for tracking search analytics and query patterns.
    """
    __tablename__ = "search_analytics"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))

    # Search details
    query = Column(String(1000), nullable=False)
    query_hash = Column(String(64), nullable=False, index=True)  # Hash for deduplication
    search_type = Column(String(50), default="semantic")  # semantic, bm25, hybrid, advanced

    # Results
    results_count = Column(Integer, default=0)
    results_returned = Column(Integer, default=0)

    # Performance
    execution_time_ms = Column(Float, default=0.0)

    # User interaction
    clicked_results = Column(JSON, nullable=True)  # List of clicked document IDs
    user_session = Column(String(100), nullable=True)  # Session identifier

    # Filters applied (for advanced search)
    filters_applied = Column(JSON, nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self):
        return f"<SearchAnalytics(query={self.query[:50]}, results={self.results_count})>"


class UserEngagement(Base):
    """
    Model for tracking user engagement patterns.
    """
    __tablename__ = "user_engagement"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))

    # User identification (anonymous)
    user_session = Column(String(100), nullable=False, index=True)
    user_agent = Column(String(500), nullable=True)

    # Engagement details
    action_type = Column(String(50), nullable=False)  # view, search, download, upload, analyze
    resource_type = Column(String(50), nullable=False)  # document, search, system
    resource_id = Column(String, nullable=True)  # Document ID, search ID, etc.

    # Context
    duration_seconds = Column(Float, nullable=True)  # Time spent on action
    context_data = Column(JSON, nullable=True)  # Additional context data

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self):
        return f"<UserEngagement(action={self.action_type}, resource={self.resource_type})>"


class DocumentVersion(Base):
    """
    Model for document version control and change history.
    """
    __tablename__ = "document_versions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    document_id = Column(String, ForeignKey("documents.id"), nullable=False)
    version_number = Column(Integer, nullable=False)

    # Version content
    title = Column(String(500), nullable=False)
    content = Column(Text, nullable=False)
    content_type = Column(String(100), nullable=False)
    file_size = Column(Integer, nullable=True)

    # Version metadata
    doc_metadata = Column(JSON, nullable=True)
    tags = Column(JSON, nullable=True)

    # Change information
    change_summary = Column(String(1000), nullable=True)  # Brief description of changes
    change_type = Column(String(50), default="update")  # create, update, restore, rollback
    changed_fields = Column(JSON, nullable=True)  # List of fields that changed

    # Version control
    is_current = Column(Boolean, default=False)  # Is this the current version?
    parent_version_id = Column(String, ForeignKey("document_versions.id"), nullable=True)

    # User information (if available)
    created_by = Column(String(100), nullable=True)  # User identifier
    created_by_session = Column(String(100), nullable=True)  # Session identifier

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    document = relationship("Document", backref="versions")
    parent_version = relationship("DocumentVersion", remote_side=[id], backref="child_versions")

    def __repr__(self):
        return f"<DocumentVersion(document_id={self.document_id}, version={self.version_number})>"


class DocumentChangeLog(Base):
    """
    Model for detailed document change logging.
    """
    __tablename__ = "document_change_logs"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    document_id = Column(String, ForeignKey("documents.id"), nullable=False)
    version_id = Column(String, ForeignKey("document_versions.id"), nullable=False)

    # Change details
    field_name = Column(String(100), nullable=False)  # Field that changed
    old_value = Column(Text, nullable=True)  # Previous value (truncated if too long)
    new_value = Column(Text, nullable=True)  # New value (truncated if too long)
    change_type = Column(String(20), nullable=False)  # added, modified, deleted

    # Change metadata
    value_type = Column(String(50), nullable=True)  # string, json, number, boolean
    is_truncated = Column(Boolean, default=False)  # Was the value truncated?

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    document = relationship("Document")
    version = relationship("DocumentVersion", backref="change_logs")

    def __repr__(self):
        return f"<DocumentChangeLog(document_id={self.document_id}, field={self.field_name})>"


class SearchQuery(Base):
    """
    Model for tracking search queries and their results for analytics.
    """
    __tablename__ = "search_queries"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    query_text = Column(Text, nullable=False)
    query_type = Column(String(50), default="semantic")  # semantic, keyword, hybrid

    # Search parameters
    limit_requested = Column(Integer, default=5)
    score_threshold = Column(Float, nullable=True)
    filter_conditions = Column(JSON, nullable=True)

    # Results
    results_count = Column(Integer, default=0)
    results_metadata = Column(JSON, nullable=True)  # Summary of results

    # Performance metrics
    execution_time_ms = Column(Float, nullable=True)
    embedding_time_ms = Column(Float, nullable=True)
    search_time_ms = Column(Float, nullable=True)

    # Context
    conversation_id = Column(String, ForeignKey("conversations.id"), nullable=True)
    user_context = Column(JSON, nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    conversation = relationship("Conversation")

    def __repr__(self):
        return f"<SearchQuery(id={self.id}, query={self.query_text[:50]})>"


class AgentInteraction(Base):
    """
    Model for tracking agent interactions and multi-agent workflows.
    """
    __tablename__ = "agent_interactions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))

    # Agent information
    agent_name = Column(String(100), nullable=False)  # researcher, analyst, writer, coordinator
    agent_role = Column(String(200), nullable=True)

    # Interaction details
    interaction_type = Column(String(50), nullable=False)  # workflow, query, task
    input_data = Column(Text, nullable=True)
    output_data = Column(Text, nullable=True)

    # Workflow context
    workflow_id = Column(String, nullable=True)  # Links related agent interactions
    workflow_type = Column(String(100), nullable=True)  # simple_research, complex_analysis, etc.
    step_number = Column(Integer, nullable=True)  # Order in workflow

    # Performance metrics
    execution_time_ms = Column(Float, nullable=True)
    tokens_used = Column(Integer, nullable=True)

    # Context and metadata
    conversation_id = Column(String, ForeignKey("conversations.id"), nullable=True)
    task_metadata = Column(JSON, nullable=True)

    # Status tracking
    status = Column(String(50), default="completed")  # pending, running, completed, failed
    error_message = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    conversation = relationship("Conversation")

    def __repr__(self):
        return f"<AgentInteraction(id={self.id}, agent={self.agent_name}, type={self.interaction_type})>"


class MultiModalContent(Base):
    """
    Model for storing multi-modal content and processing results.
    Supports audio, video, and image content with processing metadata.
    """
    __tablename__ = "multimodal_content"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))

    # Content information
    media_type = Column(String(50), nullable=False)  # audio, video, image
    filename = Column(String(500), nullable=False)
    file_size = Column(Integer, nullable=False)
    content_hash = Column(String(64), nullable=True)  # SHA-256 hash for deduplication
    storage_path = Column(String(1000), nullable=True)  # Path to stored file

    # Processing information
    processing_status = Column(String(50), default="pending")  # pending, processing, completed, failed
    processing_result = Column(JSON, nullable=True)  # Processing results and metadata
    error_message = Column(Text, nullable=True)

    # Context
    conversation_id = Column(String, ForeignKey("conversations.id"), nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    conversation = relationship("Conversation", back_populates="multimodal_content")

    def __repr__(self):
        return f"<MultiModalContent(id={self.id}, type={self.media_type}, filename={self.filename})>"


class Organization(Base):
    """Model for client organizations."""
    __tablename__ = "organizations"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)

    # Organization settings
    settings = Column(JSON, default=lambda: {})
    isolation_level = Column(String(50), default="strict")  # strict, shared, collaborative

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Status
    is_active = Column(Boolean, default=True)

    # Relationships
    users = relationship("User", back_populates="organization")
    client_applications = relationship("ClientApplication", back_populates="organization")

    def __repr__(self):
        return f"<Organization(id={self.id}, name={self.name})>"


class ClientApplication(Base):
    """Model for client applications that connect to DRYAD.AI."""
    __tablename__ = "client_applications"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)

    # Organization relationship
    organization_id = Column(String, ForeignKey("organizations.id"), nullable=True, index=True)

    # API authentication
    api_key_hash = Column(String(255), unique=True, nullable=False, index=True)  # SHA256 hash
    api_key_prefix = Column(String(20), nullable=False)  # First few chars for identification

    # Client configuration
    permissions = Column(JSON, default=lambda: ["read", "write"])
    isolation_level = Column(String(50), default="strict")  # strict, shared, collaborative
    settings = Column(JSON, default=lambda: {})

    # MCP configuration
    mcp_enabled = Column(Boolean, default=True)
    mcp_version = Column(String(20), default="2025-06-18")

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    last_used = Column(DateTime(timezone=True), nullable=True)

    # Status
    is_active = Column(Boolean, default=True)

    # Relationships
    users = relationship("User", back_populates="client_application")
    organization = relationship("Organization", back_populates="client_applications")

    def __repr__(self):
        return f"<ClientApplication(id={self.id}, name={self.name}, org={self.organization_id})>"


class SharedKnowledge(Base):
    """Model for cross-client shared knowledge and learning."""
    __tablename__ = "shared_knowledge"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))

    # Content identification
    content_hash = Column(String(255), unique=True, nullable=False, index=True)  # SHA256 of original content
    content_type = Column(String(50), nullable=False)  # query, response, document, insight

    # Anonymized content
    anonymized_content = Column(Text, nullable=False)
    embedding_vector = Column(JSON, nullable=True)  # Vector representation

    # Privacy and sharing
    privacy_level = Column(String(50), default="public")  # public, restricted, private
    contributing_clients = Column(JSON, default=lambda: [])  # List of client app IDs
    excluded_clients = Column(JSON, default=lambda: [])  # Clients that opted out

    # Metadata
    tags = Column(JSON, default=lambda: [])
    category = Column(String(100), nullable=True)
    confidence_score = Column(Float, default=0.0)  # Quality/relevance score

    # Usage tracking
    access_count = Column(Integer, default=0)
    last_accessed = Column(DateTime(timezone=True), nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<SharedKnowledge(id={self.id}, type={self.content_type}, privacy={self.privacy_level})>"
