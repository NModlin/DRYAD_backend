"""
University models for the Agentic Research University System (Level 6).

This module defines the core university infrastructure including:
- University instances with multi-tenant isolation
- University configuration and settings
- University agents (students)
- University statistics and metrics
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
class UniversityStatus(str, Enum):
    """University status"""
    ACTIVE = "active"
    PAUSED = "paused"
    ARCHIVED = "archived"
    MAINTENANCE = "maintenance"


class IsolationLevel(str, Enum):
    """Multi-tenant isolation level"""
    STRICT = "strict"  # Complete isolation
    SHARED = "shared"  # Shared resources
    HYBRID = "hybrid"  # Mix of both


# SQLAlchemy Models
class University(Base):
    """
    University instance with multi-tenant isolation.
    
    Each university is an isolated training environment for AI agents
    with its own curriculum, competitions, and configuration.
    """
    __tablename__ = "universities"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Basic info
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    
    # Ownership and multi-tenancy
    owner_user_id = Column(String, nullable=False, index=True)
    client_app_id = Column(String, nullable=True)
    tenant_id = Column(String, nullable=True, index=True)
    organization_id = Column(String, nullable=True)
    
    # Configuration
    settings = Column(JSON, nullable=False, default=dict)  # Custom settings
    isolation_level = Column(String(50), nullable=False, default=IsolationLevel.STRICT.value)
    max_agents = Column(Integer, nullable=False, default=100)
    max_concurrent_competitions = Column(Integer, nullable=False, default=10)
    storage_quota_mb = Column(Integer, nullable=False, default=1024)
    
    # Specialization focus
    primary_specialization = Column(String(100), nullable=True)  # Main focus area
    secondary_specializations = Column(JSON, nullable=False, default=list)  # Additional areas
    
    # Status and lifecycle
    status = Column(String(50), nullable=False, default=UniversityStatus.ACTIVE.value, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_activity_at = Column(DateTime(timezone=True), nullable=True)
    
    # Statistics (denormalized for performance)
    total_agents = Column(Integer, nullable=False, default=0)
    active_agents = Column(Integer, nullable=False, default=0)
    total_competitions = Column(Integer, nullable=False, default=0)
    total_training_data_points = Column(Integer, nullable=False, default=0)
    
    # Metadata
    tags = Column(JSON, nullable=False, default=list)
    custom_metadata = Column(JSON, nullable=False, default=dict)
    
    # Relationships (to be added when other models are created)
    # agents = relationship("UniversityAgent", back_populates="university", cascade="all, delete-orphan")
    # curriculum_paths = relationship("CurriculumPath", back_populates="university", cascade="all, delete-orphan")
    # competitions = relationship("Competition", back_populates="university", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<University(id={self.id}, name={self.name}, status={self.status})>"


# Indexes
Index("idx_university_owner_status", University.owner_user_id, University.status)
Index("idx_university_tenant_status", University.tenant_id, University.status)


# Pydantic Schemas
class UniversityConfigSchema(BaseModel):
    """University configuration settings"""
    curriculum_template: Optional[str] = "default"
    competition_frequency: str = "weekly"  # daily, weekly, monthly
    auto_enroll_agents: bool = True
    enable_inter_university_competitions: bool = False
    training_data_sharing: bool = True
    memory_retention_days: int = 90
    custom_settings: Dict[str, Any] = Field(default_factory=dict)


class UniversityCreate(BaseModel):
    """Schema for creating a university"""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    owner_user_id: str
    client_app_id: Optional[str] = None
    tenant_id: Optional[str] = None
    organization_id: Optional[str] = None
    
    # Configuration
    settings: UniversityConfigSchema = Field(default_factory=UniversityConfigSchema)
    isolation_level: IsolationLevel = IsolationLevel.STRICT
    max_agents: int = Field(default=100, ge=1, le=10000)
    max_concurrent_competitions: int = Field(default=10, ge=1, le=100)
    storage_quota_mb: int = Field(default=1024, ge=100, le=100000)
    
    # Specialization
    primary_specialization: Optional[str] = None
    secondary_specializations: List[str] = Field(default_factory=list)
    
    # Metadata
    tags: List[str] = Field(default_factory=list)
    custom_metadata: Dict[str, Any] = Field(default_factory=dict)

    @validator('secondary_specializations')
    def validate_secondary_specializations(cls, v):
        if len(v) > 5:
            raise ValueError("Maximum 5 secondary specializations allowed")
        return v


class UniversityUpdate(BaseModel):
    """Schema for updating a university"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    
    # Configuration
    settings: Optional[UniversityConfigSchema] = None
    max_agents: Optional[int] = Field(None, ge=1, le=10000)
    max_concurrent_competitions: Optional[int] = Field(None, ge=1, le=100)
    storage_quota_mb: Optional[int] = Field(None, ge=100, le=100000)
    
    # Specialization
    primary_specialization: Optional[str] = None
    secondary_specializations: Optional[List[str]] = None
    
    # Status
    status: Optional[UniversityStatus] = None
    
    # Metadata
    tags: Optional[List[str]] = None
    custom_metadata: Optional[Dict[str, Any]] = None

    @validator('secondary_specializations')
    def validate_secondary_specializations(cls, v):
        if v is not None and len(v) > 5:
            raise ValueError("Maximum 5 secondary specializations allowed")
        return v


class UniversityResponse(BaseModel):
    """Schema for university response"""
    id: str
    name: str
    description: Optional[str]
    owner_user_id: str
    client_app_id: Optional[str]
    tenant_id: Optional[str]
    organization_id: Optional[str]
    
    # Configuration
    settings: Dict[str, Any]
    isolation_level: str
    max_agents: int
    max_concurrent_competitions: int
    storage_quota_mb: int
    
    # Specialization
    primary_specialization: Optional[str]
    secondary_specializations: List[str]
    
    # Status
    status: str
    created_at: datetime
    updated_at: Optional[datetime]
    last_activity_at: Optional[datetime]
    
    # Statistics
    total_agents: int
    active_agents: int
    total_competitions: int
    total_training_data_points: int
    
    # Metadata
    tags: List[str]
    custom_metadata: Dict[str, Any]

    class Config:
        from_attributes = True


class UniversityStatistics(BaseModel):
    """Detailed university statistics"""
    university_id: str
    university_name: str
    
    # Agent statistics
    total_agents: int
    active_agents: int
    graduated_agents: int
    average_agent_level: float
    
    # Competition statistics
    total_competitions: int
    completed_competitions: int
    ongoing_competitions: int
    average_competition_score: float
    
    # Training data statistics
    total_training_data_points: int
    data_quality_score: float
    
    # Activity statistics
    daily_active_agents: int
    weekly_active_agents: int
    monthly_active_agents: int
    
    # Resource usage
    storage_used_mb: int
    storage_quota_mb: int
    storage_usage_percent: float
    
    # Timestamps
    last_competition_at: Optional[datetime]
    last_graduation_at: Optional[datetime]
    last_activity_at: Optional[datetime]


class UniversityListResponse(BaseModel):
    """Schema for listing universities"""
    universities: List[UniversityResponse]
    total: int
    skip: int
    limit: int
    has_more: bool

