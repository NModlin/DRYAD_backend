"""
Tool Registry Database Models

SQLAlchemy models for tool registry tables.
"""

import uuid
from datetime import datetime
from sqlalchemy import (
    Column,
    String,
    Text,
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    CheckConstraint,
    UniqueConstraint,
    JSON,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database.database import Base


class Tool(Base):
    """
    Tool model representing a registered tool in the system.

    Tools are versioned and contain OpenAPI 3.0 schema definitions.
    Each tool can have an associated Docker image for execution.
    """

    __tablename__ = "tools"
    __table_args__ = {'extend_existing': True}

    # Primary key
    tool_id = Column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        index=True,
    )

    # Tool identification
    name = Column(String(255), nullable=False, index=True)
    version = Column(String(50), nullable=False, index=True)

    # Tool metadata
    description = Column(Text, nullable=True)
    schema_json = Column(JSON, nullable=False)  # OpenAPI 3.0 specification
    docker_image_uri = Column(String(500), nullable=True)

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

    # Status
    is_active = Column(Boolean, default=True, nullable=False, index=True)

    # Relationships
    permissions = relationship(
        "ToolPermission",
        back_populates="tool",
        cascade="all, delete-orphan",
    )

    # Constraints
    __table_args__ = (
        UniqueConstraint("name", "version", name="unique_tool_version"),
        Index("idx_tools_name", "name"),
        Index("idx_tools_version", "version"),
        Index("idx_tools_active", "is_active"),
        Index("idx_tools_created", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<Tool(name='{self.name}', version='{self.version}', active={self.is_active})>"


class ToolPermission(Base):
    """
    Tool Permission model for access control.

    Links agents or roles to tools, controlling who can execute which tools.
    Supports both agent-level and role-level permissions.
    """

    __tablename__ = "tool_permissions"
    __table_args__ = {'extend_existing': True}

    # Primary key
    permission_id = Column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        index=True,
    )

    # Principal (agent or role)
    principal_id = Column(String(255), nullable=False, index=True)
    principal_type = Column(String(20), nullable=False)  # 'agent' or 'role'

    # Tool reference
    tool_id = Column(
        String(36),
        ForeignKey("tools.tool_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Permission details
    allow_stateful_execution = Column(Boolean, default=False, nullable=False)

    # Audit fields
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    created_by = Column(String(255), nullable=True)

    # Relationships
    tool = relationship("app.services.tool_registry.models.Tool", back_populates="permissions")

    # Constraints
    __table_args__ = (
        UniqueConstraint(
            "principal_id",
            "principal_type",
            "tool_id",
            name="unique_principal_tool",
        ),
        CheckConstraint(
            "principal_type IN ('agent', 'role')",
            name="check_principal_type",
        ),
        Index("idx_tool_permissions_principal", "principal_id", "principal_type"),
        Index("idx_tool_permissions_tool", "tool_id"),
    )

    def __repr__(self) -> str:
        return (
            f"<ToolPermission("
            f"principal={self.principal_type}:{self.principal_id}, "
            f"tool_id={self.tool_id}, "
            f"stateful={self.allow_stateful_execution}"
            f")>"
        )

