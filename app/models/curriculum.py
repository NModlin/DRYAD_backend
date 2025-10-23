"""
Curriculum models for the Agentic Research University System.

This module defines curriculum paths, levels, and agent progression tracking.
"""

import uuid
from datetime import datetime
from typing import Optional, Dict, Any, List
from enum import Enum

from sqlalchemy import Column, String, Text, Integer, Float, Boolean, DateTime, JSON, ForeignKey, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from pydantic import BaseModel, Field, validator

from app.database.models import Base


# Enums
class DifficultyLevel(str, Enum):
    """Curriculum difficulty level"""
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"
    MASTER = "master"


class CurriculumStatus(str, Enum):
    """Curriculum path status"""
    DRAFT = "draft"
    ACTIVE = "active"
    ARCHIVED = "archived"
    DEPRECATED = "deprecated"


class AgentProgressStatus(str, Enum):
    """Agent progress status on a curriculum"""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"


# SQLAlchemy Models
class CurriculumPath(Base):
    """
    Structured learning path for agents.
    
    Defines a sequence of learning objectives, challenges, and evaluations
    that agents must complete to progress.
    """
    __tablename__ = "curriculum_paths"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    university_id = Column(String, ForeignKey("universities.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Basic info
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    
    # Path configuration
    difficulty_level = Column(String(50), nullable=False, default=DifficultyLevel.BEGINNER.value, index=True)
    estimated_duration_hours = Column(Integer, nullable=False, default=40)
    prerequisites = Column(JSON, nullable=False, default=list)  # Array of required path IDs or competency scores
    
    # Specialization alignment
    specialization = Column(String(100), nullable=True, index=True)
    skill_tree_id = Column(String, ForeignKey("skill_trees.id"), nullable=True)
    
    # Metadata
    version = Column(String(20), nullable=False, default="1.0.0")
    tags = Column(JSON, nullable=False, default=list)
    is_public = Column(Boolean, nullable=False, default=False)
    
    # Status
    status = Column(String(50), nullable=False, default=CurriculumStatus.ACTIVE.value, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Statistics
    total_enrollments = Column(Integer, nullable=False, default=0)
    total_completions = Column(Integer, nullable=False, default=0)
    average_completion_time_hours = Column(Float, nullable=True)
    average_score = Column(Float, nullable=True)
    
    # Relationships
    # university = relationship("University", back_populates="curriculum_paths")
    levels = relationship("CurriculumLevel", back_populates="curriculum_path", cascade="all, delete-orphan", order_by="CurriculumLevel.level_number")
    # agent_progress = relationship("AgentCurriculumProgress", back_populates="curriculum_path", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<CurriculumPath(id={self.id}, name={self.name}, difficulty={self.difficulty_level})>"


class CurriculumLevel(Base):
    """
    Individual level within a curriculum path.
    
    Each level contains specific objectives, challenges, and evaluation criteria.
    """
    __tablename__ = "curriculum_levels"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    curriculum_path_id = Column(String, ForeignKey("curriculum_paths.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Level info
    level_number = Column(Integer, nullable=False)  # 1, 2, 3, etc.
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    
    # Learning objectives
    objectives = Column(JSON, nullable=False, default=list)  # Array of learning objectives
    
    # Challenges and tasks
    challenges = Column(JSON, nullable=False, default=list)  # Array of challenge definitions
    required_challenges = Column(Integer, nullable=False, default=1)  # Minimum challenges to complete
    
    # Evaluation criteria
    evaluation_criteria = Column(JSON, nullable=False, default=dict)  # {"accuracy": 0.8, "speed": 0.6}
    required_score = Column(Float, nullable=False, default=0.7)  # Minimum score to pass (0.0-1.0)
    
    # Resources
    learning_resources = Column(JSON, nullable=False, default=list)  # Links, documents, etc.
    
    # Estimated time
    estimated_hours = Column(Integer, nullable=False, default=5)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    curriculum_path = relationship("CurriculumPath", back_populates="levels")

    def __repr__(self):
        return f"<CurriculumLevel(id={self.id}, level={self.level_number}, name={self.name})>"


class AgentCurriculumProgress(Base):
    """
    Tracks an agent's progress through a curriculum path.
    """
    __tablename__ = "agent_curriculum_progress"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    agent_id = Column(String, nullable=False, index=True)
    curriculum_path_id = Column(String, ForeignKey("curriculum_paths.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Progress tracking
    current_level_number = Column(Integer, nullable=False, default=1)
    completed_levels = Column(JSON, nullable=False, default=list)  # Array of completed level numbers
    
    # Status
    status = Column(String(50), nullable=False, default=AgentProgressStatus.NOT_STARTED.value, index=True)
    
    # Scores and performance
    overall_score = Column(Float, nullable=True)  # 0.0-1.0
    level_scores = Column(JSON, nullable=False, default=dict)  # {level_number: score}
    
    # Time tracking
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    total_time_hours = Column(Float, nullable=True)
    last_activity_at = Column(DateTime(timezone=True), nullable=True)
    
    # Attempts
    total_attempts = Column(Integer, nullable=False, default=0)
    failed_attempts = Column(Integer, nullable=False, default=0)
    
    # Metadata
    notes = Column(Text, nullable=True)
    custom_metadata = Column(JSON, nullable=False, default=dict)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    # curriculum_path = relationship("CurriculumPath", back_populates="agent_progress")

    def __repr__(self):
        return f"<AgentCurriculumProgress(agent_id={self.agent_id}, curriculum={self.curriculum_path_id}, status={self.status})>"


# Indexes
Index("idx_curriculum_university_status", CurriculumPath.university_id, CurriculumPath.status)
Index("idx_curriculum_specialization", CurriculumPath.specialization, CurriculumPath.difficulty_level)
Index("idx_curriculum_level_path", CurriculumLevel.curriculum_path_id, CurriculumLevel.level_number)
Index("idx_agent_progress_agent_status", AgentCurriculumProgress.agent_id, AgentCurriculumProgress.status)
Index("idx_agent_progress_unique", AgentCurriculumProgress.agent_id, AgentCurriculumProgress.curriculum_path_id, unique=True)


# Pydantic Schemas
class CurriculumPathCreate(BaseModel):
    """Schema for creating a curriculum path"""
    university_id: str
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    difficulty_level: DifficultyLevel = DifficultyLevel.BEGINNER
    estimated_duration_hours: int = Field(default=40, ge=1, le=1000)
    prerequisites: List[str] = Field(default_factory=list)
    specialization: Optional[str] = None
    skill_tree_id: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    is_public: bool = False


class CurriculumPathUpdate(BaseModel):
    """Schema for updating a curriculum path"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    difficulty_level: Optional[DifficultyLevel] = None
    estimated_duration_hours: Optional[int] = Field(None, ge=1, le=1000)
    prerequisites: Optional[List[str]] = None
    specialization: Optional[str] = None
    tags: Optional[List[str]] = None
    is_public: Optional[bool] = None
    status: Optional[CurriculumStatus] = None


class CurriculumPathResponse(BaseModel):
    """Schema for curriculum path response"""
    id: str
    university_id: str
    name: str
    description: Optional[str]
    difficulty_level: str
    estimated_duration_hours: int
    prerequisites: List[str]
    specialization: Optional[str]
    skill_tree_id: Optional[str]
    version: str
    tags: List[str]
    is_public: bool
    status: str
    created_at: datetime
    updated_at: Optional[datetime]
    total_enrollments: int
    total_completions: int
    average_completion_time_hours: Optional[float]
    average_score: Optional[float]

    class Config:
        from_attributes = True


class CurriculumLevelCreate(BaseModel):
    """Schema for creating a curriculum level"""
    curriculum_path_id: str
    level_number: int = Field(..., ge=1)
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    objectives: List[str] = Field(default_factory=list)
    challenges: List[Dict[str, Any]] = Field(default_factory=list)
    required_challenges: int = Field(default=1, ge=1)
    evaluation_criteria: Dict[str, float] = Field(default_factory=dict)
    required_score: float = Field(default=0.7, ge=0.0, le=1.0)
    learning_resources: List[Dict[str, Any]] = Field(default_factory=list)
    estimated_hours: int = Field(default=5, ge=1, le=100)


class CurriculumLevelResponse(BaseModel):
    """Schema for curriculum level response"""
    id: str
    curriculum_path_id: str
    level_number: int
    name: str
    description: Optional[str]
    objectives: List[str]
    challenges: List[Dict[str, Any]]
    required_challenges: int
    evaluation_criteria: Dict[str, float]
    required_score: float
    learning_resources: List[Dict[str, Any]]
    estimated_hours: int
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


class AgentProgressCreate(BaseModel):
    """Schema for enrolling an agent in a curriculum"""
    agent_id: str
    curriculum_path_id: str


class AgentProgressUpdate(BaseModel):
    """Schema for updating agent progress"""
    current_level_number: Optional[int] = Field(None, ge=1)
    status: Optional[AgentProgressStatus] = None
    notes: Optional[str] = None


class AgentProgressResponse(BaseModel):
    """Schema for agent progress response"""
    id: str
    agent_id: str
    curriculum_path_id: str
    current_level_number: int
    completed_levels: List[int]
    status: str
    overall_score: Optional[float]
    level_scores: Dict[str, float]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    total_time_hours: Optional[float]
    last_activity_at: Optional[datetime]
    total_attempts: int
    failed_attempts: int
    notes: Optional[str]
    custom_metadata: Dict[str, Any]
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True

