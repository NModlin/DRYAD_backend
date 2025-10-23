"""
Agent Creation Studio Enhancement Models - Phase 2: Progression Paths

Database models for progression paths through skill trees.
Defines recommended skill sequences and learning paths.
"""

import uuid
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional

from sqlalchemy import Column, String, Integer, Boolean, DateTime, JSON, Text, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from pydantic import BaseModel, Field, field_validator

from app.database.database import Base
from app.models.specialization import SpecializationType


# ============================================================================
# SQLAlchemy Models
# ============================================================================

class ProgressionPath(Base):
    """
    Progression path for a skill tree.
    Defines a recommended sequence of skills to learn.
    """
    __tablename__ = "progression_paths"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    skill_tree_id = Column(String, ForeignKey("skill_trees.id"), nullable=False, index=True)

    # Basic info
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)

    # Path configuration
    skill_sequence = Column(JSON, nullable=False)  # Ordered array of skill_node IDs
    estimated_duration_weeks = Column(Integer, nullable=True)

    # Specialization
    specialization = Column(SQLEnum(SpecializationType), nullable=False, index=True)

    # Customization
    is_custom = Column(Boolean, nullable=False, default=False)
    creator_id = Column(String, nullable=True)
    is_public = Column(Boolean, nullable=False, default=False)

    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    skill_tree = relationship("SkillTree", back_populates="progression_paths")

    def __repr__(self):
        return f"<ProgressionPath id={self.id} name={self.name} specialization={self.specialization.value}>"


# ============================================================================
# Pydantic Schemas for API
# ============================================================================

class ProgressionPathCreate(BaseModel):
    """Schema for creating a progression path."""
    skill_tree_id: str
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    skill_sequence: List[str] = Field(..., min_items=1, description="Ordered list of skill node IDs")
    estimated_duration_weeks: Optional[int] = Field(None, ge=1)
    specialization: SpecializationType
    is_custom: bool = False
    creator_id: Optional[str] = None
    is_public: bool = False

    @field_validator('skill_sequence')
    @classmethod
    def validate_skill_sequence(cls, v):
        """Ensure skill sequence has no duplicates."""
        if len(v) != len(set(v)):
            raise ValueError("Skill sequence cannot contain duplicate skill nodes")
        return v


class ProgressionPathUpdate(BaseModel):
    """Schema for updating a progression path."""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    skill_sequence: Optional[List[str]] = Field(None, min_items=1)
    estimated_duration_weeks: Optional[int] = Field(None, ge=1)
    is_public: Optional[bool] = None


class ProgressionPathResponse(BaseModel):
    """Schema for progression path responses."""
    id: str
    skill_tree_id: str
    name: str
    description: Optional[str]
    skill_sequence: List[str]
    estimated_duration_weeks: Optional[int]
    specialization: SpecializationType
    is_custom: bool
    creator_id: Optional[str]
    is_public: bool
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


class ProgressionPathWithDetails(BaseModel):
    """Schema for progression path with skill details."""
    path: ProgressionPathResponse
    skills: List[Dict[str, Any]]  # Skill node details in sequence
    total_skills: int
    total_estimated_experience: int


class AgentProgressionPathAssignment(BaseModel):
    """Schema for assigning a progression path to an agent."""
    agent_id: str
    progression_path_id: str
    assigned_at: datetime
    current_step: int = 0
    completed_steps: int = 0
    progress_percentage: float = 0.0


class AssignProgressionPathRequest(BaseModel):
    """Schema for assigning a progression path to an agent."""
    progression_path_id: str


class AgentProgressionPathProgress(BaseModel):
    """Schema for tracking agent progress through a progression path."""
    agent_id: str
    progression_path_id: str
    path_name: str
    current_step: int
    total_steps: int
    completed_steps: int
    progress_percentage: float
    current_skill: Optional[Dict[str, Any]]
    next_skill: Optional[Dict[str, Any]]
    completed_skills: List[str]
    remaining_skills: List[str]
    estimated_weeks_remaining: Optional[int]


class ProgressionPathRecommendation(BaseModel):
    """Schema for progression path recommendations."""
    agent_id: str
    specialization: SpecializationType
    recommended_paths: List[ProgressionPathResponse]
    reason: str

