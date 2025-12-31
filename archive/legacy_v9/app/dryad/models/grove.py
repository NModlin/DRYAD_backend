"""
Grove Model

SQLAlchemy model for Grove entity.
Ported from TypeScript database/entities/Grove.ts
"""

from sqlalchemy import Column, String, DateTime, Boolean, JSON, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.database import Base
from typing import Dict, Any, Optional
from datetime import datetime, timezone


class Grove(Base):
    """
    Grove Entity
    
    Represents a project managed by Dryad, containing a full tree of branches.
    A grove is the top-level container for knowledge exploration.
    """
    
    __tablename__ = "dryad_groves"
    
    # Primary key
    id = Column(String, primary_key=True, index=True)
    
    # Basic information
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), nullable=True)
    last_accessed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Flags
    is_favorite = Column(Boolean, default=False, nullable=False)
    
    # Metadata
    template_metadata = Column(JSON, nullable=True)
    
    # Relationships
    branches = relationship(
        "Branch",
        back_populates="grove",
        cascade="all, delete-orphan",
        lazy="select"
    )
    
    def __init__(
        self,
        id: str,
        name: str,
        description: Optional[str] = None,
        template_metadata: Optional[Dict[str, Any]] = None,
        is_favorite: bool = False,
        **kwargs
    ):
        self.id = id
        self.name = name.strip()
        self.description = description or ""
        self.template_metadata = template_metadata or {}
        self.is_favorite = is_favorite
        self.created_at = datetime.now(timezone.utc)
        self.updated_at = datetime.now(timezone.utc)
        self.last_accessed_at = datetime.now(timezone.utc)
        
        # Apply any additional kwargs
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
    
    def update_last_accessed(self) -> None:
        """Update the last accessed timestamp."""
        self.last_accessed_at = datetime.now(timezone.utc)

    def update_timestamp(self) -> None:
        """Update the updated_at timestamp."""
        self.updated_at = datetime.now(timezone.utc)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert grove to dictionary representation."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "last_accessed_at": self.last_accessed_at.isoformat() if self.last_accessed_at else None,
            "is_favorite": self.is_favorite,
            "template_metadata": self.template_metadata,
            "branch_count": len(self.branches) if self.branches else 0
        }
    
    def __repr__(self) -> str:
        return f"<Grove(id='{self.id}', name='{self.name}')>"
