"""
Agent Creation Studio Enhancement Models - Phase 2: Specialization

Database models for agent specialization profiles.
Defines primary/secondary specializations, levels, and configuration.
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


# ============================================================================
# Enums for Specialization Types
# ============================================================================

class SpecializationType(str, Enum):
    """Available specialization types for agents."""
    MEMETICS = "memetics"
    WARFARE_STUDIES = "warfare_studies"
    BIOENGINEERED_INTELLIGENCE = "bioengineered_intelligence"
    DATA_SCIENCE = "data_science"
    PHILOSOPHY = "philosophy"
    ENGINEERING = "engineering"
    CREATIVE_ARTS = "creative_arts"
    CUSTOM = "custom"


# ============================================================================
# SQLAlchemy Models
# ============================================================================

class SpecializationProfile(Base):
    """
    Specialization profile for agents.
    Defines primary/secondary specializations, levels, and specialization-specific configuration.
    """
    __tablename__ = "specialization_profiles"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    agent_id = Column(String, ForeignKey("agents.id"), nullable=False, unique=True, index=True)

    # Primary specialization
    primary_specialization = Column(SQLEnum(SpecializationType), nullable=False, default=SpecializationType.DATA_SCIENCE)
    specialization_level = Column(Integer, nullable=False, default=1)  # 1-10 (novice to expert)

    # Secondary specializations (JSON array of SpecializationType values)
    secondary_specializations = Column(JSON, nullable=False, default=list)  # ["data_science", "philosophy"]

    # Specialization-specific configuration
    specialization_tools = Column(JSON, nullable=False, default=list)  # Tool IDs relevant to specialization
    specialization_curriculum = Column(String, nullable=True)  # Curriculum ID
    specialization_constraints = Column(JSON, nullable=False, default=dict)  # Custom constraints

    # Cross-specialization learning
    cross_specialization_enabled = Column(Boolean, nullable=False, default=True)
    cross_specialization_penalty = Column(Float, nullable=False, default=0.2)  # 0.0-1.0 performance penalty

    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships (will be defined when Agent model is updated)
    # agent = relationship("Agent", back_populates="specialization_profile")

    def __repr__(self):
        return f"<SpecializationProfile agent_id={self.agent_id} primary={self.primary_specialization.value} level={self.specialization_level}>"


# ============================================================================
# Pydantic Schemas for API
# ============================================================================

class SpecializationProfileCreate(BaseModel):
    """Schema for creating a specialization profile."""
    primary_specialization: SpecializationType = Field(default=SpecializationType.DATA_SCIENCE)
    specialization_level: int = Field(default=1, ge=1, le=10)
    secondary_specializations: List[SpecializationType] = Field(default_factory=list)
    specialization_tools: List[str] = Field(default_factory=list)
    specialization_curriculum: Optional[str] = None
    specialization_constraints: Dict[str, Any] = Field(default_factory=dict)
    cross_specialization_enabled: bool = True
    cross_specialization_penalty: float = Field(default=0.2, ge=0.0, le=1.0)

    @field_validator('secondary_specializations')
    @classmethod
    def validate_secondary_specializations(cls, v, info):
        """Ensure secondary specializations don't include primary."""
        if 'primary_specialization' in info.data and info.data['primary_specialization'] in v:
            raise ValueError("Secondary specializations cannot include the primary specialization")
        return v


class SpecializationProfileUpdate(BaseModel):
    """Schema for updating a specialization profile."""
    primary_specialization: Optional[SpecializationType] = None
    specialization_level: Optional[int] = Field(None, ge=1, le=10)
    secondary_specializations: Optional[List[SpecializationType]] = None
    specialization_tools: Optional[List[str]] = None
    specialization_curriculum: Optional[str] = None
    specialization_constraints: Optional[Dict[str, Any]] = None
    cross_specialization_enabled: Optional[bool] = None
    cross_specialization_penalty: Optional[float] = Field(None, ge=0.0, le=1.0)


class SpecializationProfileResponse(BaseModel):
    """Schema for specialization profile responses."""
    id: str
    agent_id: str
    primary_specialization: SpecializationType
    specialization_level: int
    secondary_specializations: List[SpecializationType]
    specialization_tools: List[str]
    specialization_curriculum: Optional[str]
    specialization_constraints: Dict[str, Any]
    cross_specialization_enabled: bool
    cross_specialization_penalty: float
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


class SpecializationTypeInfo(BaseModel):
    """Information about a specialization type."""
    type: SpecializationType
    name: str
    description: str
    focus_areas: List[str]
    recommended_tools: List[str]
    recommended_curriculum: Optional[str]


# ============================================================================
# Specialization Type Metadata
# ============================================================================

SPECIALIZATION_METADATA: Dict[SpecializationType, Dict[str, Any]] = {
    SpecializationType.MEMETICS: {
        "name": "Memetics",
        "description": "Cultural evolution, idea propagation, and meme analysis",
        "focus_areas": ["Cultural evolution", "Idea propagation", "Meme analysis", "Viral dynamics", "Social influence"],
        "recommended_tools": ["social_network_analysis", "trend_detection", "cultural_modeling"],
        "recommended_curriculum": "memetics_101"
    },
    SpecializationType.WARFARE_STUDIES: {
        "name": "Warfare Studies",
        "description": "Strategic analysis, conflict resolution, and game theory",
        "focus_areas": ["Military strategy", "Game theory", "Conflict resolution", "Strategic planning", "Tactical analysis"],
        "recommended_tools": ["strategy_simulator", "game_theory_calculator", "conflict_modeling"],
        "recommended_curriculum": "warfare_strategy_101"
    },
    SpecializationType.BIOENGINEERED_INTELLIGENCE: {
        "name": "Bioengineered Intelligence",
        "description": "Biological systems, neural networks, and hybrid intelligence",
        "focus_areas": ["Neuroscience", "Biological computing", "Hybrid systems", "Neural networks", "Genetic algorithms"],
        "recommended_tools": ["neural_network_simulator", "biological_modeling", "genetic_algorithm_toolkit"],
        "recommended_curriculum": "bioengineered_intelligence_101"
    },
    SpecializationType.DATA_SCIENCE: {
        "name": "Data Science",
        "description": "Analytics, pattern recognition, and predictive modeling",
        "focus_areas": ["Statistics", "Machine learning", "Data engineering", "Pattern recognition", "Predictive modeling"],
        "recommended_tools": ["statistical_analysis", "ml_frameworks", "data_visualization"],
        "recommended_curriculum": "data_science_101"
    },
    SpecializationType.PHILOSOPHY: {
        "name": "Philosophy",
        "description": "Ethics, reasoning, and knowledge systems",
        "focus_areas": ["Ethics", "Epistemology", "Logic", "Metaphysics", "Philosophy of mind"],
        "recommended_tools": ["logic_analyzer", "ethical_framework", "knowledge_graph"],
        "recommended_curriculum": "philosophy_101"
    },
    SpecializationType.ENGINEERING: {
        "name": "Engineering",
        "description": "Systems design, optimization, and problem-solving",
        "focus_areas": ["Systems engineering", "Optimization", "Design thinking", "Problem-solving", "Innovation"],
        "recommended_tools": ["cad_system", "optimization_algorithms", "simulation_tools"],
        "recommended_curriculum": "engineering_101"
    },
    SpecializationType.CREATIVE_ARTS: {
        "name": "Creative Arts",
        "description": "Generative art, music, and narrative creation",
        "focus_areas": ["Creative theory", "Generative systems", "Artistic expression", "Music composition", "Narrative design"],
        "recommended_tools": ["generative_models", "art_tools", "music_composition"],
        "recommended_curriculum": "creative_arts_101"
    },
    SpecializationType.CUSTOM: {
        "name": "Custom",
        "description": "User-defined specialization",
        "focus_areas": ["User-defined"],
        "recommended_tools": [],
        "recommended_curriculum": None
    }
}


def get_specialization_info(spec_type: SpecializationType) -> SpecializationTypeInfo:
    """Get metadata for a specialization type."""
    metadata = SPECIALIZATION_METADATA.get(spec_type, {})
    return SpecializationTypeInfo(
        type=spec_type,
        name=metadata.get("name", spec_type.value),
        description=metadata.get("description", ""),
        focus_areas=metadata.get("focus_areas", []),
        recommended_tools=metadata.get("recommended_tools", []),
        recommended_curriculum=metadata.get("recommended_curriculum")
    )


def get_all_specialization_types() -> List[SpecializationTypeInfo]:
    """Get metadata for all specialization types."""
    return [get_specialization_info(spec_type) for spec_type in SpecializationType]

