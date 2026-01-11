"""
Agent Creation Studio Enhancement Models - Phase 1

Database models for visual and behavioral customization of agents.
These models extend the base Agent model with enhanced customization features.
"""

import uuid
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from enum import Enum

from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, JSON, Text, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from pydantic import BaseModel, Field

from dryad.database.database import Base


# ============================================================================
# Enums for Visual and Behavioral Customization
# ============================================================================

class AvatarStyle(str, Enum):
    """Avatar style options."""
    ABSTRACT = "abstract"
    HUMANOID = "humanoid"
    ANIMAL = "animal"
    CUSTOM = "custom"


class VisualTheme(str, Enum):
    """Visual theme options."""
    PROFESSIONAL = "professional"
    PLAYFUL = "playful"
    MYSTERIOUS = "mysterious"
    MINIMALIST = "minimalist"
    CYBERPUNK = "cyberpunk"


class LearningStyle(str, Enum):
    """Agent learning style preferences."""
    VISUAL = "visual"
    AUDITORY = "auditory"
    KINESTHETIC = "kinesthetic"
    READING = "reading"


class CollaborationStyle(str, Enum):
    """Agent collaboration style."""
    LEADER = "leader"
    FOLLOWER = "follower"
    EQUAL = "equal"
    INDEPENDENT = "independent"


class CommunicationTone(str, Enum):
    """Agent communication tone."""
    FORMAL = "formal"
    CASUAL = "casual"
    TECHNICAL = "technical"
    FRIENDLY = "friendly"


# ============================================================================
# SQLAlchemy Models
# ============================================================================

class VisualProfile(Base):
    """
    Visual customization profile for agents.
    Stores avatar, color, theme, and visual effect preferences.
    """
    __tablename__ = "visual_profiles"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    agent_id = Column(String, ForeignKey("agents.id"), nullable=False, unique=True, index=True)

    # Avatar customization
    avatar_style = Column(SQLEnum(AvatarStyle), nullable=False, default=AvatarStyle.ABSTRACT)
    avatar_url = Column(String(500), nullable=True)  # Custom avatar URL
    
    # Color scheme
    primary_color = Column(String(7), nullable=False, default="#0066CC")  # Hex color
    secondary_color = Column(String(7), nullable=False, default="#00CC66")
    accent_color = Column(String(7), nullable=False, default="#FF6600")
    
    # Theme and effects
    visual_theme = Column(SQLEnum(VisualTheme), nullable=False, default=VisualTheme.PROFESSIONAL)
    animation_style = Column(String(50), nullable=True)  # e.g., "smooth", "bouncy", "rigid"
    particle_effects = Column(Boolean, default=False)
    glow_intensity = Column(Float, default=0.5)  # 0.0-1.0
    
    # Badges
    achievement_badges = Column(JSON, default=lambda: [])  # List of badge IDs
    specialization_badge = Column(String(100), nullable=True)
    university_badge = Column(String(100), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<VisualProfile agent_id={self.agent_id} theme={self.visual_theme}>"


class BehavioralProfile(Base):
    """
    Behavioral customization profile for agents.
    Stores learning style, risk tolerance, collaboration preferences, and communication style.
    """
    __tablename__ = "behavioral_profiles"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    agent_id = Column(String, ForeignKey("agents.id"), nullable=False, unique=True, index=True)

    # Learning preferences
    learning_style = Column(SQLEnum(LearningStyle), nullable=False, default=LearningStyle.VISUAL)
    learning_pace = Column(Float, nullable=False, default=1.0)  # 0.5-2.0 multiplier
    learning_retention = Column(Float, nullable=False, default=0.8)  # 0.0-1.0
    
    # Risk and decision making
    risk_tolerance = Column(Float, nullable=False, default=0.5)  # 0.0-1.0 (conservative to aggressive)
    failure_recovery = Column(Float, nullable=False, default=0.7)  # How quickly agent recovers from failures
    decision_speed = Column(Float, nullable=False, default=0.5)  # 0.0-1.0 (deliberate to quick)
    decision_confidence = Column(Float, nullable=False, default=0.6)  # 0.0-1.0
    second_guessing = Column(Float, nullable=False, default=0.3)  # 0.0-1.0 (tendency to reconsider)
    
    # Collaboration preferences
    collaboration_style = Column(SQLEnum(CollaborationStyle), nullable=False, default=CollaborationStyle.EQUAL)
    communication_frequency = Column(Float, nullable=False, default=0.6)  # 0.0-1.0 (quiet to chatty)
    feedback_receptiveness = Column(Float, nullable=False, default=0.8)  # 0.0-1.0
    
    # Communication style
    communication_tone = Column(SQLEnum(CommunicationTone), nullable=False, default=CommunicationTone.TECHNICAL)
    explanation_depth = Column(String(50), nullable=False, default="moderate")  # brief, moderate, detailed
    question_asking = Column(Float, nullable=False, default=0.6)  # 0.0-1.0 (tendency to ask questions)
    
    # Specialization focus
    specialization_focus = Column(String(100), nullable=True)
    cross_specialization_interest = Column(Float, nullable=False, default=0.3)  # 0.0-1.0
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<BehavioralProfile agent_id={self.agent_id} style={self.collaboration_style}>"


# ============================================================================
# Pydantic Schemas for API
# ============================================================================

class VisualProfileSchema(BaseModel):
    """Schema for visual profile API requests/responses."""
    avatar_style: AvatarStyle = AvatarStyle.ABSTRACT
    avatar_url: Optional[str] = None
    primary_color: str = "#0066CC"
    secondary_color: str = "#00CC66"
    accent_color: str = "#FF6600"
    visual_theme: VisualTheme = VisualTheme.PROFESSIONAL
    animation_style: Optional[str] = None
    particle_effects: bool = False
    glow_intensity: float = 0.5
    achievement_badges: List[str] = Field(default_factory=list)
    specialization_badge: Optional[str] = None
    university_badge: Optional[str] = None

    class Config:
        from_attributes = True


class BehavioralProfileSchema(BaseModel):
    """Schema for behavioral profile API requests/responses."""
    learning_style: LearningStyle = LearningStyle.VISUAL
    learning_pace: float = 1.0
    learning_retention: float = 0.8
    risk_tolerance: float = 0.5
    failure_recovery: float = 0.7
    decision_speed: float = 0.5
    decision_confidence: float = 0.6
    second_guessing: float = 0.3
    collaboration_style: CollaborationStyle = CollaborationStyle.EQUAL
    communication_frequency: float = 0.6
    feedback_receptiveness: float = 0.8
    communication_tone: CommunicationTone = CommunicationTone.TECHNICAL
    explanation_depth: str = "moderate"
    question_asking: float = 0.6
    specialization_focus: Optional[str] = None
    cross_specialization_interest: float = 0.3

    class Config:
        from_attributes = True


class EnhancedAgentProfileSchema(BaseModel):
    """Combined schema for enhanced agent profile."""
    agent_id: str
    visual_profile: VisualProfileSchema
    behavioral_profile: BehavioralProfileSchema
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

