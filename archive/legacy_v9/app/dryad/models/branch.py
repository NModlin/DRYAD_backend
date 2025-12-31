"""
Branch Model

SQLAlchemy model for Branch entity.
Ported from TypeScript database/entities/Branch.ts
"""

from sqlalchemy import Column, String, DateTime, Integer, Text, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.database import Base
from enum import Enum
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone


class BranchStatus(str, Enum):
    """Branch status enumeration."""
    ACTIVE = "active"
    ARCHIVED = "archived"
    PRUNED = "pruned"


class BranchPriority(str, Enum):
    """Branch priority enumeration."""
    HIGHEST = "highest"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    LOWEST = "lowest"


class Branch(Base):
    """
    Branch Entity
    
    Represents a distinct exploration path in the quantum tree.
    Each branch maintains its own context and can spawn child branches.
    """
    
    __tablename__ = "dryad_branches"
    
    # Primary key
    id = Column(String, primary_key=True, index=True)
    
    # Foreign keys
    grove_id = Column(String, ForeignKey("dryad_groves.id", ondelete="CASCADE"), nullable=False, index=True)
    parent_id = Column(String, ForeignKey("dryad_branches.id", ondelete="SET NULL"), nullable=True, index=True)
    observation_point_id = Column(String, ForeignKey("dryad_observation_points.id"), nullable=True)
    
    # Basic information
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    
    # Hierarchy
    path_depth = Column(Integer, default=0, nullable=False)
    
    # Status and priority
    status = Column(SQLEnum(BranchStatus), default=BranchStatus.ACTIVE, nullable=False)
    priority = Column(SQLEnum(BranchPriority), default=BranchPriority.MEDIUM, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), nullable=False)

    # Relationships
    grove = relationship("Grove", back_populates="branches")
    parent_branch = relationship("Branch", remote_side=[id], back_populates="child_branches")
    child_branches = relationship("Branch", back_populates="parent_branch", cascade="all, delete-orphan")
    vessel = relationship("Vessel", back_populates="branch", uselist=False, cascade="all, delete-orphan")
    dialogues = relationship("Dialogue", back_populates="branch", cascade="all, delete-orphan")
    # Observation points that belong to this branch (one-to-many)
    observation_points = relationship(
        "ObservationPoint",
        back_populates="branch",
        foreign_keys="ObservationPoint.branch_id",
        cascade="all, delete-orphan"
    )
    # The observation point this branch is associated with (many-to-one, optional)
    observation_point = relationship(
        "ObservationPoint",
        foreign_keys=[observation_point_id],
        uselist=False
    )
    # Branch suggestions for this branch (one-to-many)
    suggestions = relationship(
        "BranchSuggestion",
        back_populates="parent_branch",
        foreign_keys="BranchSuggestion.branch_id",
        cascade="all, delete-orphan"
    )
    # Source suggestion if this branch was created from a suggestion (many-to-one, optional)
    source_suggestion = relationship(
        "BranchSuggestion",
        back_populates="created_branch",
        foreign_keys="BranchSuggestion.created_branch_id",
        uselist=False
    )
    
    def __init__(
        self,
        id: str,
        grove_id: str,
        name: str,
        parent_id: Optional[str] = None,
        description: Optional[str] = None,
        path_depth: int = 0,
        status: BranchStatus = BranchStatus.ACTIVE,
        priority: BranchPriority = BranchPriority.MEDIUM,
        observation_point_id: Optional[str] = None,
        **kwargs
    ):
        self.id = id
        self.grove_id = grove_id
        self.parent_id = parent_id
        self.name = name.strip()
        self.description = description or ""
        self.path_depth = path_depth
        self.status = status
        self.priority = priority
        self.observation_point_id = observation_point_id
        self.created_at = datetime.now(timezone.utc)
        self.updated_at = datetime.now(timezone.utc)

        # Apply any additional kwargs
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
    
    @property
    def is_root(self) -> bool:
        """Check if this is a root branch."""
        return self.parent_id is None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert branch to dictionary representation."""
        return {
            "id": self.id,
            "grove_id": self.grove_id,
            "parent_id": self.parent_id,
            "name": self.name,
            "description": self.description,
            "path_depth": self.path_depth,
            "status": self.status.value,
            "priority": self.priority.value,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "observation_point_id": self.observation_point_id,
            "child_count": self.get_child_count(),
            "is_root": self.is_root()
        }
    
    def __repr__(self) -> str:
        return f"<Branch(id='{self.id}', name='{self.name}', grove_id='{self.grove_id}')>"
