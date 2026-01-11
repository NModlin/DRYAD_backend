"""
Vessel Model

SQLAlchemy model for Vessel entity.
Ported from TypeScript database/entities/Vessel.ts
"""

from sqlalchemy import Column, String, DateTime, Boolean, JSON, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from dryad.infrastructure.database import Base
from typing import Dict, Any, Optional
from datetime import datetime, timezone


class Vessel(Base):
    """
    Vessel Entity
    
    Represents an isolated context container for a specific branch.
    Each vessel stores the context, content, and state for its branch.
    """
    
    __tablename__ = "dryad_vessels"
    
    # Primary key
    id = Column(String, primary_key=True, index=True)
    
    # Foreign key
    branch_id = Column(String, ForeignKey("dryad_branches.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    
    # File and storage references
    file_references = Column(JSON, nullable=False, default=dict)
    content_hash = Column(String, nullable=False)
    storage_path = Column(String, nullable=False)
    
    # Compression
    is_compressed = Column(Boolean, default=False, nullable=False)
    compressed_path = Column(String, nullable=True)
    
    # Status
    status = Column(String, default="active", nullable=False)

    # Timestamps (database has both old and new columns)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), nullable=True)
    generated_at = Column(DateTime(timezone=True), nullable=True)
    last_updated = Column(DateTime(timezone=True), nullable=True)
    last_accessed = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    branch = relationship("Branch", back_populates="vessel")
    
    def __init__(
        self,
        id: str,
        branch_id: str,
        storage_path: str,
        content_hash: str = "",
        file_references: Optional[Dict[str, str]] = None,
        is_compressed: bool = False,
        compressed_path: Optional[str] = None,
        status: str = "active",
        **kwargs
    ):
        self.id = id
        self.branch_id = branch_id
        self.storage_path = storage_path
        self.content_hash = content_hash
        self.file_references = file_references or {}
        self.is_compressed = is_compressed
        self.compressed_path = compressed_path
        self.status = status
        # Set both old and new timestamp columns for compatibility
        now = datetime.now(timezone.utc)
        self.created_at = now
        self.updated_at = now
        self.generated_at = now
        self.last_updated = now
        self.last_accessed = now
        
        # Apply any additional kwargs
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
    
    def update_last_accessed(self) -> None:
        """Update the last accessed timestamp."""
        self.last_accessed = datetime.now(timezone.utc)

    def update_last_updated(self) -> None:
        """Update the last updated timestamp."""
        self.last_updated = datetime.now(timezone.utc)
    
    def add_file_reference(self, key: str, path: str) -> None:
        """Add a file reference to the vessel."""
        if self.file_references is None:
            self.file_references = {}
        self.file_references[key] = path
        self.update_last_updated()
    
    def remove_file_reference(self, key: str) -> bool:
        """Remove a file reference from the vessel."""
        if self.file_references and key in self.file_references:
            del self.file_references[key]
            self.update_last_updated()
            return True
        return False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert vessel to dictionary representation."""
        return {
            "id": self.id,
            "branch_id": self.branch_id,
            "storage_path": self.storage_path,
            "content_hash": self.content_hash,
            "file_references": self.file_references,
            "is_compressed": self.is_compressed,
            "compressed_path": self.compressed_path,
            "status": self.status,
            "generated_at": self.generated_at.isoformat() if self.generated_at else None,
            "last_updated": self.last_updated.isoformat() if self.last_updated else None,
            "last_accessed": self.last_accessed.isoformat() if self.last_accessed else None
        }
    
    def __repr__(self) -> str:
        return f"<Vessel(id='{self.id}', branch_id='{self.branch_id}', status='{self.status}')>"
