"""
Possibility Model

SQLAlchemy model for Possibility entity.
Ported from TypeScript database/entities/Possibility.ts
"""

from sqlalchemy import Column, String, DateTime, Text, Float, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.database import Base
from typing import Dict, Any, Optional
from datetime import datetime, timezone


class Possibility(Base):
    """
    Possibility Entity
    
    Represents a potential branching path from an observation point.
    Each possibility has a probability weight and can be "observed" to create a new branch.
    """
    
    __tablename__ = "dryad_possibilities"
    
    # Primary key
    id = Column(String, primary_key=True, index=True)
    
    # Foreign key
    observation_point_id = Column(String, ForeignKey("dryad_observation_points.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Content
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    
    # Quantum properties
    probability_weight = Column(Float, default=1.0, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    observation_point = relationship("ObservationPoint", back_populates="possibilities")
    
    def __init__(
        self,
        id: str,
        observation_point_id: str,
        name: str,
        description: Optional[str] = None,
        probability_weight: float = 1.0,
        **kwargs
    ):
        self.id = id
        self.observation_point_id = observation_point_id
        self.name = name.strip()
        self.description = description
        self.probability_weight = max(0.0, probability_weight)  # Ensure non-negative
        self.created_at = datetime.now(timezone.utc)
        
        # Apply any additional kwargs
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
    
    def normalize_probability(self, total_weight: float) -> float:
        """Calculate normalized probability given total weight of all possibilities."""
        if total_weight <= 0:
            return 0.0
        return self.probability_weight / total_weight
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert possibility to dictionary representation."""
        return {
            "id": self.id,
            "observation_point_id": self.observation_point_id,
            "name": self.name,
            "description": self.description,
            "probability_weight": self.probability_weight,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }
    
    def __repr__(self) -> str:
        return f"<Possibility(id='{self.id}', name='{self.name}', weight={self.probability_weight})>"
