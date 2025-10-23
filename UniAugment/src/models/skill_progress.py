"""
Agent Creation Studio Enhancement Models - Phase 2: Skill Progress

Database models for tracking agent progress through skill trees.
Tracks individual agent progress, experience, and unlocked skills.
"""

import uuid
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional

from sqlalchemy import Column, String, Integer, Boolean, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from pydantic import BaseModel, Field

from app.database.database import Base


# ============================================================================
# SQLAlchemy Models
# ============================================================================

class AgentSkillProgress(Base):
    """
    Tracks an agent's progress through a specific skill node.
    Each agent has one progress record per skill node they're working on.
    """
    __tablename__ = "agent_skill_progress"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    agent_id = Column(String, ForeignKey("agents.id"), nullable=False, index=True)
    skill_node_id = Column(String, ForeignKey("skill_nodes.id"), nullable=False, index=True)

    # Progress
    current_level = Column(Integer, nullable=False, default=0)
    current_experience = Column(Integer, nullable=False, default=0)

    # Status
    is_unlocked = Column(Boolean, nullable=False, default=False)
    unlocked_at = Column(DateTime(timezone=True), nullable=True)

    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships (will be defined when Agent model is updated)
    # agent = relationship("Agent", back_populates="skill_progress")
    skill_node = relationship("SkillNode", back_populates="agent_progress")

    # Unique constraint: one progress record per agent per skill
    __table_args__ = (
        UniqueConstraint('agent_id', 'skill_node_id', name='uq_agent_skill'),
    )

    def __repr__(self):
        return f"<AgentSkillProgress agent_id={self.agent_id} skill_node_id={self.skill_node_id} level={self.current_level}>"


# ============================================================================
# Pydantic Schemas for API
# ============================================================================

class AgentSkillProgressCreate(BaseModel):
    """Schema for creating skill progress (usually done automatically)."""
    skill_node_id: str
    current_level: int = Field(default=0, ge=0)
    current_experience: int = Field(default=0, ge=0)
    is_unlocked: bool = False


class AgentSkillProgressUpdate(BaseModel):
    """Schema for updating skill progress."""
    current_level: Optional[int] = Field(None, ge=0)
    current_experience: Optional[int] = Field(None, ge=0)
    is_unlocked: Optional[bool] = None


class AgentSkillProgressResponse(BaseModel):
    """Schema for skill progress responses."""
    id: str
    agent_id: str
    skill_node_id: str
    current_level: int
    current_experience: int
    is_unlocked: bool
    unlocked_at: Optional[datetime]
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


class SkillProgressWithDetails(BaseModel):
    """Schema for skill progress with skill node details."""
    progress: AgentSkillProgressResponse
    skill_name: str
    skill_description: Optional[str]
    max_level: int
    experience_per_level: int
    experience_to_next_level: int
    progress_percentage: float
    capability_bonuses: Dict[str, float]
    personality_shifts: Dict[str, float]
    unlocks_tools: List[str]
    unlocks_competitions: List[str]


class GainExperienceRequest(BaseModel):
    """Schema for gaining experience in a skill."""
    experience_amount: int = Field(..., ge=1, description="Amount of experience to gain")
    reason: Optional[str] = Field(None, description="Reason for gaining experience")


class GainExperienceResponse(BaseModel):
    """Schema for experience gain response."""
    skill_node_id: str
    previous_level: int
    new_level: int
    previous_experience: int
    new_experience: int
    leveled_up: bool
    levels_gained: int
    bonuses_applied: Dict[str, float]
    tools_unlocked: List[str]
    competitions_unlocked: List[str]


class UnlockSkillRequest(BaseModel):
    """Schema for unlocking a skill."""
    force: bool = Field(default=False, description="Force unlock even if prerequisites not met")


class UnlockSkillResponse(BaseModel):
    """Schema for skill unlock response."""
    skill_node_id: str
    unlocked: bool
    prerequisites_met: bool
    missing_prerequisites: List[str]
    message: str


class AgentSkillSummary(BaseModel):
    """Summary of an agent's skill progress."""
    agent_id: str
    total_skills: int
    unlocked_skills: int
    total_levels: int
    total_experience: int
    skills_by_tree: Dict[str, int]
    top_skills: List[SkillProgressWithDetails]


class AvailableSkillsResponse(BaseModel):
    """Schema for available skills (prerequisites met but not unlocked)."""
    agent_id: str
    available_skills: List[Dict[str, Any]]
    count: int

