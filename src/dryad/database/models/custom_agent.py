"""
Custom Agent Models for DRYAD Agent Creation Studio

This module defines database models for custom agent creation, submission,
and management through the Agent Creation Studio.
"""

from datetime import datetime
from typing import Optional, Dict, Any, List
from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, Text, JSON, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid

from dryad.database.database import Base


class AgentSubmission(Base):
    """Model for agent sheet submissions from clients."""
    
    __tablename__ = "agent_submissions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    client_id = Column(String(255), nullable=False, index=True)
    agent_sheet = Column(JSON, nullable=False)
    status = Column(String(50), nullable=False, default="pending", index=True)  # pending, approved, rejected, draft
    submitted_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    reviewed_at = Column(DateTime, nullable=True)
    reviewed_by = Column(UUID(as_uuid=True), nullable=True)
    rejection_reason = Column(Text, nullable=True)
    validation_results = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    custom_agent = relationship("CustomAgent", back_populates="submission", uselist=False)
    
    def __repr__(self):
        return f"<AgentSubmission {self.id} - {self.agent_sheet.get('agent_definition', {}).get('name', 'Unknown')} ({self.status})>"


class CustomAgent(Base):
    """Model for approved and active custom agents."""
    
    __tablename__ = "custom_agents"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    submission_id = Column(UUID(as_uuid=True), ForeignKey("agent_submissions.id"), nullable=False)
    name = Column(String(255), unique=True, nullable=False, index=True)
    display_name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String(100), nullable=True, index=True)
    client_id = Column(String(255), nullable=False, index=True)
    agent_configuration = Column(JSON, nullable=False)
    status = Column(String(50), nullable=False, default="active", index=True)  # active, inactive, deprecated
    usage_count = Column(Integer, default=0)
    total_tokens_used = Column(Integer, default=0)
    avg_execution_time = Column(Float, default=0.0)
    success_rate = Column(Float, default=1.0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_used_at = Column(DateTime, nullable=True)
    
    # Relationships
    submission = relationship("AgentSubmission", back_populates="custom_agent")
    executions = relationship("AgentExecution", back_populates="agent", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<CustomAgent {self.name} - {self.display_name} ({self.status})>"
    
    def update_metrics(self, execution_time: float, tokens_used: int, success: bool):
        """Update agent performance metrics."""
        self.usage_count += 1
        self.total_tokens_used += tokens_used
        
        # Update average execution time
        if self.avg_execution_time == 0:
            self.avg_execution_time = execution_time
        else:
            self.avg_execution_time = (self.avg_execution_time * (self.usage_count - 1) + execution_time) / self.usage_count
        
        # Update success rate
        if success:
            self.success_rate = ((self.success_rate * (self.usage_count - 1)) + 1.0) / self.usage_count
        else:
            self.success_rate = (self.success_rate * (self.usage_count - 1)) / self.usage_count
        
        self.last_used_at = datetime.utcnow()


class AgentExecution(Base):
    """Model for tracking custom agent executions."""
    
    __tablename__ = "agent_executions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    agent_id = Column(UUID(as_uuid=True), ForeignKey("custom_agents.id"), nullable=False, index=True)
    client_id = Column(String(255), nullable=False, index=True)
    query = Column(Text, nullable=False)
    response = Column(Text, nullable=True)
    context = Column(Text, nullable=True)
    execution_time = Column(Float, nullable=True)
    tokens_used = Column(Integer, nullable=True)
    success = Column(Boolean, default=True)
    error_message = Column(Text, nullable=True)
    execution_metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    # DRYAD integration fields
    branch_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    dialogue_id = Column(UUID(as_uuid=True), nullable=True)
    
    # Relationships
    agent = relationship("CustomAgent", back_populates="executions")
    
    def __repr__(self):
        return f"<AgentExecution {self.id} - Agent: {self.agent_id} ({self.success})>"


class AgentTemplate(Base):
    """Model for pre-built agent templates that clients can use."""
    
    __tablename__ = "agent_templates"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), unique=True, nullable=False, index=True)
    display_name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String(100), nullable=True, index=True)
    template_sheet = Column(JSON, nullable=False)
    is_public = Column(Boolean, default=True)
    created_by = Column(UUID(as_uuid=True), nullable=True)
    usage_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<AgentTemplate {self.name} - {self.display_name}>"


class AgentCapability(Base):
    """Model for tracking agent capabilities and skills."""
    
    __tablename__ = "agent_capabilities"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), unique=True, nullable=False, index=True)
    display_name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String(100), nullable=True, index=True)
    required_tools = Column(JSON, nullable=True)
    required_llm_features = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<AgentCapability {self.name} - {self.display_name}>"


class AgentReview(Base):
    """Model for admin reviews of agent submissions."""
    
    __tablename__ = "agent_reviews"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    submission_id = Column(UUID(as_uuid=True), ForeignKey("agent_submissions.id"), nullable=False, index=True)
    reviewer_id = Column(UUID(as_uuid=True), nullable=False)
    review_status = Column(String(50), nullable=False)  # approved, rejected, needs_revision
    review_notes = Column(Text, nullable=True)
    test_results = Column(JSON, nullable=True)
    security_check = Column(Boolean, default=False)
    performance_check = Column(Boolean, default=False)
    compatibility_check = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<AgentReview {self.id} - Submission: {self.submission_id} ({self.review_status})>"


# Pydantic schemas for API validation
from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any


class AgentSheetMetadata(BaseModel):
    """Metadata for agent sheet submission."""
    submitted_by: str
    submission_date: Optional[datetime] = None
    client_name: str
    purpose: str


class AgentDefinition(BaseModel):
    """Agent definition section of agent sheet."""
    name: str = Field(..., pattern="^[a-zA-Z0-9_]+$", min_length=3, max_length=100)
    display_name: str = Field(..., min_length=3, max_length=255)
    description: str
    version: str = "1.0.0"
    category: str
    tags: List[str] = []


class AgentCapabilities(BaseModel):
    """Agent capabilities section."""
    role: str
    goal: str
    backstory: str
    expertise_areas: List[str] = []
    skills: List[str] = []


class AgentBehavior(BaseModel):
    """Agent behavior configuration."""
    temperature: float = Field(..., ge=0.0, le=1.0)
    max_tokens: int = Field(..., ge=100, le=8192)
    response_style: str = "balanced"
    tone: str = "professional"
    verbosity: str = "balanced"
    code_generation: bool = False
    citation_required: bool = False


class LLMPreferences(BaseModel):
    """LLM provider preferences."""
    preferred_provider: str
    fallback_providers: List[str] = []
    model_requirements: Dict[str, Any] = {}


class AgentTool(BaseModel):
    """Agent tool configuration."""
    name: str
    description: str
    enabled: bool = True
    configuration: Dict[str, Any] = {}


class AgentIntegration(BaseModel):
    """Agent integration settings."""
    dryad_compatible: bool = True
    oracle_integration: bool = True
    multi_agent_compatible: bool = False
    standalone: bool = True


class AgentConstraints(BaseModel):
    """Agent constraints and limitations."""
    max_execution_time: int = 60
    rate_limit: int = 20
    allowed_operations: List[str] = []
    forbidden_operations: List[str] = []


class AgentValidation(BaseModel):
    """Agent validation configuration."""
    test_queries: List[str] = []
    expected_capabilities: List[str] = []


class AgentSheet(BaseModel):
    """Complete agent sheet schema."""
    agent_sheet_version: str = "1.0"
    metadata: AgentSheetMetadata
    agent_definition: AgentDefinition
    capabilities: AgentCapabilities
    behavior: AgentBehavior
    llm_preferences: LLMPreferences
    tools: List[AgentTool] = []
    integration: AgentIntegration
    constraints: AgentConstraints
    validation: AgentValidation
    
    @validator('agent_sheet_version')
    def validate_version(cls, v):
        if v not in ["1.0"]:
            raise ValueError(f"Unsupported agent sheet version: {v}")
        return v


class AgentSubmissionCreate(BaseModel):
    """Schema for creating agent submission."""
    agent_sheet: AgentSheet


class AgentSubmissionResponse(BaseModel):
    """Schema for agent submission response."""
    submission_id: str
    status: str
    message: str
    estimated_review_time: str = "24-48 hours"
    
    class Config:
        from_attributes = True


class CustomAgentResponse(BaseModel):
    """Schema for custom agent response."""
    agent_id: str
    name: str
    display_name: str
    description: Optional[str]
    category: Optional[str]
    capabilities: List[str]
    status: str
    usage_count: int
    success_rate: float
    
    class Config:
        from_attributes = True


class AgentExecutionRequest(BaseModel):
    """Schema for agent execution request."""
    agent_name: str
    query: str
    context: Optional[str] = None
    branch_id: Optional[str] = None
    include_context: bool = False


class AgentExecutionResponse(BaseModel):
    """Schema for agent execution response."""
    execution_id: str
    agent_name: str
    response: str
    execution_time: float
    tokens_used: int
    success: bool
    
    class Config:
        from_attributes = True

