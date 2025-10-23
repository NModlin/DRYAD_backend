"""
Agent Creation Studio Enhancement Models - Phase 2: Skill Trees

Database models for skill trees and skill nodes.
Defines skill tree structure, nodes, prerequisites, and bonuses.
"""

import uuid
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from enum import Enum

from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, JSON, Text, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from pydantic import BaseModel, Field, field_validator

from app.database.database import Base
from app.models.specialization import SpecializationType


# ============================================================================
# SQLAlchemy Models
# ============================================================================

class SkillTree(Base):
    """
    Skill tree for a specialization.
    Contains multiple skill nodes organized in a tree structure.
    """
    __tablename__ = "skill_trees"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)

    # Specialization
    specialization = Column(SQLEnum(SpecializationType), nullable=False, index=True)

    # Customization
    is_custom = Column(Boolean, nullable=False, default=False)
    creator_id = Column(String, nullable=True, index=True)  # User who created custom tree
    is_public = Column(Boolean, nullable=False, default=False)  # Can others use this tree?

    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    skill_nodes = relationship("SkillNode", back_populates="skill_tree", cascade="all, delete-orphan")
    progression_paths = relationship("ProgressionPath", back_populates="skill_tree", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<SkillTree id={self.id} name={self.name} specialization={self.specialization.value}>"


class SkillNode(Base):
    """
    Individual skill node within a skill tree.
    Represents a specific skill that can be learned and leveled up.
    """
    __tablename__ = "skill_nodes"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    skill_tree_id = Column(String, ForeignKey("skill_trees.id"), nullable=False, index=True)

    # Basic info
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)

    # Progression
    max_level = Column(Integer, nullable=False, default=5)
    experience_per_level = Column(Integer, nullable=False, default=100)

    # Dependencies (JSON array of skill_node IDs)
    prerequisites = Column(JSON, nullable=False, default=list)  # ["skill_node_1", "skill_node_2"]

    # Bonuses (JSON dictionaries)
    capability_bonuses = Column(JSON, nullable=False, default=dict)  # {"reasoning": 0.1, "creativity": 0.05}
    personality_shifts = Column(JSON, nullable=False, default=dict)  # {"analytical": 0.05}

    # Unlocks (JSON arrays)
    unlocks_tools = Column(JSON, nullable=False, default=list)  # ["tool_id_1", "tool_id_2"]
    unlocks_competitions = Column(JSON, nullable=False, default=list)  # ["competition_id_1"]

    # Position in tree (for visualization)
    tree_position_x = Column(Integer, nullable=True)
    tree_position_y = Column(Integer, nullable=True)

    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    skill_tree = relationship("SkillTree", back_populates="skill_nodes")
    agent_progress = relationship("AgentSkillProgress", back_populates="skill_node", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<SkillNode id={self.id} name={self.name} tree_id={self.skill_tree_id}>"


# ============================================================================
# Pydantic Schemas for API
# ============================================================================

class SkillTreeCreate(BaseModel):
    """Schema for creating a skill tree."""
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    specialization: SpecializationType
    is_custom: bool = False
    creator_id: Optional[str] = None
    is_public: bool = False


class SkillTreeUpdate(BaseModel):
    """Schema for updating a skill tree."""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    is_public: Optional[bool] = None


class SkillTreeResponse(BaseModel):
    """Schema for skill tree responses."""
    id: str
    name: str
    description: Optional[str]
    specialization: SpecializationType
    is_custom: bool
    creator_id: Optional[str]
    is_public: bool
    created_at: datetime
    updated_at: Optional[datetime]
    skill_nodes: List["SkillNodeResponse"] = []

    class Config:
        from_attributes = True


class SkillNodeCreate(BaseModel):
    """Schema for creating a skill node."""
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    max_level: int = Field(default=5, ge=1, le=10)
    experience_per_level: int = Field(default=100, ge=1)
    prerequisites: List[str] = Field(default_factory=list)
    capability_bonuses: Dict[str, float] = Field(default_factory=dict)
    personality_shifts: Dict[str, float] = Field(default_factory=dict)
    unlocks_tools: List[str] = Field(default_factory=list)
    unlocks_competitions: List[str] = Field(default_factory=list)
    tree_position_x: Optional[int] = None
    tree_position_y: Optional[int] = None

    @field_validator('capability_bonuses', 'personality_shifts')
    @classmethod
    def validate_bonuses(cls, v):
        """Ensure bonus values are reasonable."""
        for key, value in v.items():
            if not -1.0 <= value <= 1.0:
                raise ValueError(f"Bonus value for {key} must be between -1.0 and 1.0")
        return v


class SkillNodeUpdate(BaseModel):
    """Schema for updating a skill node."""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    max_level: Optional[int] = Field(None, ge=1, le=10)
    experience_per_level: Optional[int] = Field(None, ge=1)
    prerequisites: Optional[List[str]] = None
    capability_bonuses: Optional[Dict[str, float]] = None
    personality_shifts: Optional[Dict[str, float]] = None
    unlocks_tools: Optional[List[str]] = None
    unlocks_competitions: Optional[List[str]] = None
    tree_position_x: Optional[int] = None
    tree_position_y: Optional[int] = None


class SkillNodeResponse(BaseModel):
    """Schema for skill node responses."""
    id: str
    skill_tree_id: str
    name: str
    description: Optional[str]
    max_level: int
    experience_per_level: int
    prerequisites: List[str]
    capability_bonuses: Dict[str, float]
    personality_shifts: Dict[str, float]
    unlocks_tools: List[str]
    unlocks_competitions: List[str]
    tree_position_x: Optional[int]
    tree_position_y: Optional[int]
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


class SkillTreeVisualization(BaseModel):
    """Schema for skill tree visualization data."""
    tree_id: str
    tree_name: str
    specialization: SpecializationType
    nodes: List[Dict[str, Any]]  # Node data with positions
    edges: List[Dict[str, str]]  # Prerequisite relationships


# Update forward references
SkillTreeResponse.model_rebuild()

