"""
Observation Point Model

SQLAlchemy model for ObservationPoint entity.
Ported from TypeScript database/entities/ObservationPoint.ts
"""

from sqlalchemy import Column, String, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from dryad.infrastructure.database import Base
from typing import Dict, Any, Optional
from datetime import datetime, timezone


class ObservationPoint(Base):
    """
    Observation Point Entity
    
    Represents a decision point where branches can split into multiple possibilities.
    This is where the quantum-inspired branching occurs.
    """
    
    __tablename__ = "dryad_observation_points"
    
    # Primary key
    id = Column(String, primary_key=True, index=True)
    
    # Foreign key
    branch_id = Column(String, ForeignKey("dryad_branches.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Content
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    context = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    branch = relationship(
        "Branch",
        back_populates="observation_points",
        foreign_keys=[branch_id]  # Explicitly specify which foreign key to use
    )
    possibilities = relationship("Possibility", back_populates="observation_point", cascade="all, delete-orphan")
    
    def __init__(
        self,
        id: str,
        branch_id: str,
        name: str,
        description: Optional[str] = None,
        context: Optional[str] = None,
        **kwargs
    ):
        self.id = id
        self.branch_id = branch_id
        self.name = name.strip()
        self.description = description
        self.context = context
        self.created_at = datetime.now(timezone.utc)
        
        # Apply any additional kwargs
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
    
    def get_possibility_count(self) -> int:
        """Get the number of possibilities for this observation point."""
        return len(self.possibilities) if self.possibilities else 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert observation point to dictionary representation."""
        return {
            "id": self.id,
            "branch_id": self.branch_id,
            "name": self.name,
            "description": self.description,
            "context": self.context,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "possibility_count": self.get_possibility_count(),
            "possibilities": [p.to_dict() for p in self.possibilities] if self.possibilities else []
        }
    
    def __repr__(self) -> str:
        return f"<ObservationPoint(id='{self.id}', name='{self.name}', branch_id='{self.branch_id}')>"
