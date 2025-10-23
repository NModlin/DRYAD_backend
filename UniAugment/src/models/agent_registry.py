"""
Agent Registry Models for GAD Multi-Agent System

Database models and schemas for the 20-agent swarm system registry.
This is separate from the custom agent system (app/models/custom_agent.py).
"""

import uuid
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Union
from enum import Enum
import uuid as uuid_lib

from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, JSON, Text, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID, JSONB
from pydantic import BaseModel, Field, field_validator

from app.database.database import Base


class AgentTier(str, Enum):
    """Agent hierarchy tiers."""
    ORCHESTRATOR = "orchestrator"
    SPECIALIST = "specialist"
    EXECUTION = "execution"


class AgentStatus(str, Enum):
    """Agent operational status."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    MAINTENANCE = "maintenance"
    ERROR = "error"


class OrchestrationPattern(str, Enum):
    """Orchestration patterns for agent collaboration."""
    HIERARCHICAL = "hierarchical"  # Traditional top-down (default)
    PEER_TO_PEER = "peer_to_peer"  # Direct specialist collaboration
    HYBRID = "hybrid"  # Mix of both patterns
    AUTONOMOUS = "autonomous"  # Agent works independently


class SystemAgent(Base):
    """
    System Agent Registry - Built-in agents for the 20-agent swarm.
    
    This table tracks the built-in system agents (Master Orchestrator, Project Manager,
    Codebase Analyst, etc.) as opposed to user-submitted custom agents.
    """
    __tablename__ = "system_agents"
    
    # Primary identification
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    agent_id = Column(String(100), unique=True, nullable=False, index=True)  # e.g., "master_orchestrator"
    name = Column(String(255), nullable=False)  # e.g., "Master Orchestrator"
    display_name = Column(String(255), nullable=False)  # Human-readable name
    
    # Classification
    tier = Column(SQLEnum(AgentTier), nullable=False, index=True)
    category = Column(String(100), nullable=False, index=True)  # e.g., "orchestration", "development", "qa"

    # Orchestration
    orchestration_pattern = Column(SQLEnum(OrchestrationPattern), nullable=False, default=OrchestrationPattern.HIERARCHICAL, index=True)
    can_collaborate_directly = Column(Boolean, default=False)  # Can work peer-to-peer with other specialists
    preferred_collaborators = Column(JSONB, nullable=True, default=list)  # List of agent_ids for peer collaboration

    # Capabilities
    capabilities = Column(JSONB, nullable=False, default=list)  # List of capability strings
    description = Column(Text, nullable=True)
    role = Column(Text, nullable=True)  # Agent's role description
    goal = Column(Text, nullable=True)  # Agent's primary goal
    backstory = Column(Text, nullable=True)  # Agent's backstory for LLM context
    
    # Configuration
    configuration = Column(JSONB, nullable=False, default=dict)  # Agent-specific config
    llm_config = Column(JSONB, nullable=True)  # LLM preferences (temperature, max_tokens, etc.)
    tools = Column(JSONB, nullable=False, default=list)  # Available tools
    
    # Status and health
    status = Column(SQLEnum(AgentStatus), nullable=False, default=AgentStatus.ACTIVE, index=True)
    health_check_url = Column(String(500), nullable=True)  # Optional health check endpoint
    last_health_check = Column(DateTime(timezone=True), nullable=True)
    health_status = Column(String(50), nullable=True)  # "healthy", "degraded", "unhealthy"
    
    # Metrics
    total_tasks = Column(Integer, default=0)
    successful_tasks = Column(Integer, default=0)
    failed_tasks = Column(Integer, default=0)
    avg_execution_time = Column(Float, default=0.0)  # Average execution time in seconds
    total_tokens_used = Column(Integer, default=0)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    last_used_at = Column(DateTime(timezone=True), nullable=True)

    # Additional data
    extra_data = Column(JSONB, nullable=True)  # Additional metadata (renamed from 'metadata' to avoid SQLAlchemy conflict)
    
    def __repr__(self):
        return f"<SystemAgent {self.agent_id} - {self.name} ({self.tier.value})>"
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate."""
        if self.total_tasks == 0:
            return 1.0
        return self.successful_tasks / self.total_tasks
    
    def update_metrics(self, success: bool, execution_time: float, tokens_used: int = 0):
        """Update agent metrics after task execution."""
        self.total_tasks += 1
        if success:
            self.successful_tasks += 1
        else:
            self.failed_tasks += 1
        
        # Update average execution time
        if self.total_tasks == 1:
            self.avg_execution_time = execution_time
        else:
            self.avg_execution_time = (
                (self.avg_execution_time * (self.total_tasks - 1) + execution_time) / self.total_tasks
            )
        
        self.total_tokens_used += tokens_used
        self.last_used_at = datetime.now(timezone.utc)


class AgentCapabilityMatch(Base):
    """
    Agent Capability Matching - Maps capabilities to agents.
    
    This table helps with agent selection based on required capabilities.
    """
    __tablename__ = "agent_capability_matches"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    capability = Column(String(255), nullable=False, index=True)
    agent_id = Column(String(100), nullable=False, index=True)  # References SystemAgent.agent_id
    proficiency = Column(Float, default=1.0)  # 0.0 to 1.0, how good the agent is at this capability
    
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    
    def __repr__(self):
        return f"<AgentCapabilityMatch {self.capability} -> {self.agent_id} ({self.proficiency})>"


# ============================================================================
# Pydantic Schemas
# ============================================================================

class SystemAgentBase(BaseModel):
    """Base schema for system agents."""
    agent_id: str
    name: str
    display_name: str
    tier: AgentTier
    category: str
    capabilities: List[str] = []
    description: Optional[str] = None
    role: Optional[str] = None
    goal: Optional[str] = None
    backstory: Optional[str] = None
    configuration: Dict[str, Any] = {}
    llm_config: Optional[Dict[str, Any]] = None
    tools: List[str] = []
    status: AgentStatus = AgentStatus.ACTIVE


class SystemAgentCreate(SystemAgentBase):
    """Schema for creating a system agent."""
    pass


class SystemAgentUpdate(BaseModel):
    """Schema for updating a system agent."""
    name: Optional[str] = None
    display_name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[AgentStatus] = None
    configuration: Optional[Dict[str, Any]] = None
    llm_config: Optional[Dict[str, Any]] = None
    tools: Optional[List[str]] = None
    capabilities: Optional[List[str]] = None


class SystemAgentResponse(BaseModel):
    """Schema for system agent response."""
    id: str
    agent_id: str
    name: str
    display_name: str
    tier: AgentTier
    category: str
    capabilities: List[str]
    description: Optional[str]
    status: AgentStatus
    total_tasks: int
    successful_tasks: int
    failed_tasks: int
    success_rate: float
    avg_execution_time: float
    total_tokens_used: int
    health_status: Optional[str]
    last_health_check: Optional[datetime]
    last_used_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    @field_validator('id', mode='before')
    @classmethod
    def convert_uuid_to_str(cls, v):
        """Convert UUID to string."""
        if isinstance(v, uuid_lib.UUID):
            return str(v)
        return v

    class Config:
        from_attributes = True


class AgentSelectionRequest(BaseModel):
    """Schema for agent selection request."""
    required_capabilities: List[str]
    task_description: Optional[str] = None
    tier_preference: Optional[AgentTier] = None
    exclude_agents: List[str] = []


class AgentSelectionResponse(BaseModel):
    """Schema for agent selection response."""
    agent_id: str
    name: str
    tier: AgentTier
    match_score: float
    matched_capabilities: List[str]
    missing_capabilities: List[str]


class AgentHealthCheckRequest(BaseModel):
    """Schema for agent health check request."""
    agent_id: str


class AgentHealthCheckResponse(BaseModel):
    """Schema for agent health check response."""
    agent_id: str
    status: str  # "healthy", "degraded", "unhealthy"
    response_time: float
    last_check: datetime
    details: Optional[Dict[str, Any]] = None


class AgentMetricsUpdate(BaseModel):
    """Schema for updating agent metrics."""
    agent_id: str
    success: bool
    execution_time: float
    tokens_used: int = 0

