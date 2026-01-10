"""
Memory Guild Database Models

SQLAlchemy models for Memory Keeper Guild data foundation.
Supports memory storage, embeddings, relationships, and access control.
"""

import uuid
from datetime import datetime
from sqlalchemy import (
    Column,
    String,
    Text,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Index,
    CheckConstraint,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy import JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database.database import Base


class MemoryRecord(Base):
    """
    Memory Record model representing stored agent memories.
    
    Supports multi-tenant isolation, deduplication via content_hash,
    and soft deletion for audit trails.
    """
    
    __tablename__ = "memory_records"
    
    # Primary key
    memory_id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
    )
    
    # Multi-tenant isolation
    agent_id = Column(String(255), nullable=False, index=True)
    tenant_id = Column(String(255), nullable=False, index=True)
    
    # Memory content
    source_type = Column(String(50), nullable=False, index=True)
    content_text = Column(Text, nullable=False)
    content_hash = Column(String(64), nullable=False, index=True)  # MD5 hash
    memory_metadata = Column("metadata", JSON, default={}, nullable=False)
    
    # Timestamps
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
    
    # Soft deletion
    is_deleted = Column(Boolean, default=False, nullable=False, index=True)
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    embeddings = relationship(
        "MemoryEmbedding",
        back_populates="memory",
        cascade="all, delete-orphan",
    )
    
    outgoing_relationships = relationship(
        "MemoryRelationship",
        foreign_keys="MemoryRelationship.source_memory_id",
        back_populates="source_memory",
        cascade="all, delete-orphan",
    )
    
    incoming_relationships = relationship(
        "MemoryRelationship",
        foreign_keys="MemoryRelationship.target_memory_id",
        back_populates="target_memory",
        cascade="all, delete-orphan",
    )
    
    # Constraints
    __table_args__ = (
        UniqueConstraint(
            "agent_id",
            "tenant_id",
            "content_hash",
            name="unique_content_hash",
        ),
        CheckConstraint(
            "source_type IN ('conversation', 'tool_output', 'document', 'observation', 'external', 'coordinator')",
            name="check_source_type",
        ),
        Index("idx_memory_agent", "agent_id"),
        Index("idx_memory_tenant", "tenant_id"),
        Index("idx_memory_source", "source_type"),
        Index("idx_memory_created", "created_at"),
        Index("idx_memory_hash", "content_hash"),
        Index("idx_memory_active", "is_deleted", postgresql_where=(Column("is_deleted") == False)),
    )
    
    def __repr__(self) -> str:
        return (
            f"<MemoryRecord("
            f"agent={self.agent_id}, "
            f"tenant={self.tenant_id}, "
            f"source={self.source_type}, "
            f"deleted={self.is_deleted}"
            f")>"
        )


class MemoryEmbedding(Base):
    """
    Memory Embedding model for vector representations.
    
    Links memory records to their vector embeddings in external
    vector databases (Weaviate, Pinecone, Milvus).
    """
    
    __tablename__ = "memory_embeddings"
    
    # Primary key
    embedding_id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
    )
    
    # Foreign key to memory record
    memory_id = Column(
        UUID(as_uuid=True),
        ForeignKey("memory_records.memory_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    # Vector database reference
    vector_id = Column(String(255), nullable=False, index=True)
    embedding_model = Column(String(100), nullable=False)
    
    # Timestamp
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    
    # Relationships
    memory = relationship("MemoryRecord", back_populates="embeddings")
    
    # Constraints
    __table_args__ = (
        UniqueConstraint(
            "memory_id",
            "embedding_model",
            name="unique_memory_embedding",
        ),
        Index("idx_embeddings_memory", "memory_id"),
        Index("idx_embeddings_vector", "vector_id"),
    )
    
    def __repr__(self) -> str:
        return (
            f"<MemoryEmbedding("
            f"memory_id={self.memory_id}, "
            f"model={self.embedding_model}"
            f")>"
        )


class MemoryRelationship(Base):
    """
    Memory Relationship model for knowledge graph connections.
    
    Represents typed relationships between memories with confidence scores.
    Enables multi-hop reasoning and knowledge graph traversal.
    """
    
    __tablename__ = "memory_relationships"
    
    # Primary key
    relationship_id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
    )
    
    # Foreign keys to memory records
    source_memory_id = Column(
        UUID(as_uuid=True),
        ForeignKey("memory_records.memory_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    target_memory_id = Column(
        UUID(as_uuid=True),
        ForeignKey("memory_records.memory_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    # Relationship metadata
    relationship_type = Column(String(50), nullable=False, index=True)
    confidence_score = Column(Float, nullable=True)
    
    # Timestamp
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    
    # Relationships
    source_memory = relationship(
        "MemoryRecord",
        foreign_keys=[source_memory_id],
        back_populates="outgoing_relationships",
    )
    
    target_memory = relationship(
        "MemoryRecord",
        foreign_keys=[target_memory_id],
        back_populates="incoming_relationships",
    )
    
    # Constraints
    __table_args__ = (
        UniqueConstraint(
            "source_memory_id",
            "target_memory_id",
            "relationship_type",
            name="unique_relationship",
        ),
        CheckConstraint(
            "relationship_type IN ('references', 'contradicts', 'supports', 'follows', 'related')",
            name="check_relationship_type",
        ),
        CheckConstraint(
            "confidence_score >= 0 AND confidence_score <= 1",
            name="check_confidence_score",
        ),
        CheckConstraint(
            "source_memory_id != target_memory_id",
            name="no_self_reference",
        ),
        Index("idx_relationships_source", "source_memory_id"),
        Index("idx_relationships_target", "target_memory_id"),
        Index("idx_relationships_type", "relationship_type"),
    )
    
    def __repr__(self) -> str:
        return (
            f"<MemoryRelationship("
            f"type={self.relationship_type}, "
            f"confidence={self.confidence_score}"
            f")>"
        )


class DataSource(Base):
    """
    Data Source model for tracking approved information sources.

    Maintains an allowlist of data sources for memory ingestion
    with metadata and sync tracking.
    """

    __tablename__ = "data_sources"

    # Primary key
    source_id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
    )

    # Source identification
    source_name = Column(String(255), nullable=False, unique=True)
    source_type = Column(String(50), nullable=False, index=True)
    source_uri = Column(Text, nullable=True)

    # Status
    is_active = Column(Boolean, default=True, nullable=False, index=True)

    # Timestamps
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    last_ingestion_at = Column(DateTime(timezone=True), nullable=True)

    # Metadata
    source_metadata = Column("metadata", JSON, default={}, nullable=False)

    # Constraints
    __table_args__ = (
        CheckConstraint(
            "source_type IN ('api', 'database', 'file_system', 'webhook', 'manual')",
            name="check_source_type",
        ),
        Index("idx_sources_active", "is_active"),
        Index("idx_sources_type", "source_type"),
    )

    def __repr__(self) -> str:
        return (
            f"<DataSource("
            f"name={self.source_name}, "
            f"type={self.source_type}, "
            f"active={self.is_active}"
            f")>"
        )


class MemoryAccessPolicy(Base):
    """
    Memory Access Policy model for fine-grained access control.

    Stores OPA (Open Policy Agent) Rego rules for memory access control.
    Enables dynamic, policy-based authorization.
    """

    __tablename__ = "memory_access_policies"

    # Primary key
    policy_id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
    )

    # Policy identification
    policy_name = Column(String(255), nullable=False, unique=True)
    policy_rules = Column(JSON, nullable=False)  # OPA Rego rules

    # Status
    is_active = Column(Boolean, default=True, nullable=False, index=True)

    # Timestamps
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Constraints
    __table_args__ = (
        Index("idx_policies_active", "is_active"),
    )

    def __repr__(self) -> str:
        return (
            f"<MemoryAccessPolicy("
            f"name={self.policy_name}, "
            f"active={self.is_active}"
            f")>"
        )

