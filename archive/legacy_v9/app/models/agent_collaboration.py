"""
Agent Collaboration Models

Models for tracking agent collaboration patterns and workflows.
"""

from datetime import datetime
from typing import Optional, Dict, Any, List
from enum import Enum
from sqlalchemy import Column, String, Integer, Boolean, DateTime, Text, JSON, ForeignKey, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from pydantic import BaseModel, Field
import uuid

from app.database.database import Base


class CollaborationStatus(str, Enum):
    """Status of collaboration workflow."""
    INITIATED = "initiated"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class CollaborationWorkflow(Base):
    """
    Collaboration Workflow - Tracks multi-agent collaboration sessions.
    """
    __tablename__ = "collaboration_workflows"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workflow_id = Column(String(100), unique=True, nullable=False, index=True)
    
    # Workflow details
    task_description = Column(Text, nullable=False)
    orchestration_pattern = Column(String(50), nullable=False)  # hierarchical, peer_to_peer, hybrid
    initiator_agent_id = Column(String(100), nullable=False, index=True)
    
    # Participating agents
    participating_agents = Column(JSONB, nullable=False, default=list)  # List of agent_ids
    collaboration_graph = Column(JSONB, nullable=True)  # Graph of agent interactions
    
    # Status
    status = Column(SQLEnum(CollaborationStatus), nullable=False, default=CollaborationStatus.INITIATED)

    # Workflow type (Phase 5 enhancement)
    workflow_type = Column(String(50), default="standard", nullable=False)  # standard, task_force
    terminal_state = Column(String(50), nullable=True)  # solution_found, failed, timeout

    # Results
    final_output = Column(JSONB, nullable=True)
    success = Column(Boolean, nullable=True)
    error_message = Column(Text, nullable=True)
    
    # Metrics
    total_steps = Column(Integer, default=0)
    total_execution_time = Column(Integer, nullable=True)  # Seconds
    total_tokens_used = Column(Integer, default=0)
    
    # Timestamps
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    
    # Relationships
    steps = relationship("CollaborationStep", back_populates="workflow", cascade="all, delete-orphan")
    task_force_messages = relationship("TaskForceMessage", back_populates="workflow", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<CollaborationWorkflow {self.workflow_id} - {self.orchestration_pattern} ({self.status.value})>"


class CollaborationStep(Base):
    """
    Collaboration Step - Individual steps in a collaboration workflow.
    """
    __tablename__ = "collaboration_steps"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workflow_id = Column(UUID(as_uuid=True), ForeignKey("collaboration_workflows.id"), nullable=False, index=True)
    step_number = Column(Integer, nullable=False)
    
    # Step details
    agent_id = Column(String(100), nullable=False, index=True)
    action = Column(String(255), nullable=False)
    input_data = Column(JSONB, nullable=True)
    output_data = Column(JSONB, nullable=True)
    
    # Collaboration
    requested_by_agent = Column(String(100), nullable=True)  # For peer-to-peer
    delegated_to_agents = Column(JSONB, nullable=True, default=list)  # For hierarchical
    
    # Execution
    execution_time = Column(Integer, nullable=True)  # Milliseconds
    tokens_used = Column(Integer, default=0)
    success = Column(Boolean, default=True)
    error_message = Column(Text, nullable=True)
    
    # Timestamps
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    
    # Relationships
    workflow = relationship("CollaborationWorkflow", back_populates="steps")
    
    def __repr__(self):
        return f"<CollaborationStep {self.step_number} - Agent: {self.agent_id}>"


class CollaborationPattern(Base):
    """
    Collaboration Pattern - Predefined patterns for agent collaboration.
    """
    __tablename__ = "collaboration_patterns"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    pattern_id = Column(String(100), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    
    # Pattern definition
    pattern_type = Column(String(50), nullable=False)  # hierarchical, peer_to_peer, hybrid
    required_agents = Column(JSONB, nullable=False, default=list)  # List of required agent roles
    optional_agents = Column(JSONB, nullable=True, default=list)
    
    # Workflow definition
    workflow_steps = Column(JSONB, nullable=False)  # Ordered list of steps
    decision_points = Column(JSONB, nullable=True)  # Conditional branching
    
    # Constraints
    max_steps = Column(Integer, default=20)
    max_execution_time = Column(Integer, default=300)  # Seconds
    
    # Usage
    enabled = Column(Boolean, default=True)
    usage_count = Column(Integer, default=0)
    success_count = Column(Integer, default=0)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<CollaborationPattern {self.pattern_id} - {self.pattern_type}>"


# ============================================================================
# Pydantic Schemas
# ============================================================================

class CollaborationWorkflowCreate(BaseModel):
    """Schema for creating a collaboration workflow."""
    task_description: str
    orchestration_pattern: str = "hierarchical"
    initiator_agent_id: str
    participating_agents: List[str] = []


class CollaborationWorkflowResponse(BaseModel):
    """Schema for collaboration workflow response."""
    id: str
    workflow_id: str
    task_description: str
    orchestration_pattern: str
    initiator_agent_id: str
    participating_agents: List[str]
    status: str
    total_steps: int
    success: Optional[bool]
    started_at: datetime
    completed_at: Optional[datetime]

    class Config:
        from_attributes = True


# ============================================================================
# Phase 5: Task Force Messages
# ============================================================================

class TaskForceMessage(Base):
    """
    Task Force Message - Messages exchanged within a task force collaboration.
    """
    __tablename__ = "task_force_messages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workflow_id = Column(UUID(as_uuid=True), ForeignKey("collaboration_workflows.id"), nullable=False, index=True)

    # Message details
    agent_id = Column(String(255), nullable=False, index=True)
    message = Column(Text, nullable=False)
    message_type = Column(String(50), nullable=False)  # response, question, proposal, agreement

    # Metadata
    message_metadata = Column(JSONB, nullable=True)

    # Timestamp
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    workflow = relationship("CollaborationWorkflow", back_populates="task_force_messages")

    def __repr__(self):
        return f"<TaskForceMessage {self.agent_id} - {self.message_type}>"


class CollaborationStepCreate(BaseModel):
    """Schema for creating a collaboration step."""
    workflow_id: str
    agent_id: str
    action: str
    input_data: Optional[Dict[str, Any]] = None
    requested_by_agent: Optional[str] = None


class CollaborationStepResponse(BaseModel):
    """Schema for collaboration step response."""
    id: str
    step_number: int
    agent_id: str
    action: str
    output_data: Optional[Dict[str, Any]]
    success: bool
    execution_time: Optional[int]
    started_at: datetime
    completed_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class CollaborationPatternCreate(BaseModel):
    """Schema for creating a collaboration pattern."""
    pattern_id: str = Field(..., pattern="^[a-z0-9_]+$")
    name: str
    description: str
    pattern_type: str
    required_agents: List[str]
    optional_agents: List[str] = []
    workflow_steps: List[Dict[str, Any]]
    decision_points: Optional[Dict[str, Any]] = None
    max_steps: int = 20
    max_execution_time: int = 300


class CollaborationPatternResponse(BaseModel):
    """Schema for collaboration pattern response."""
    id: str
    pattern_id: str
    name: str
    description: str
    pattern_type: str
    required_agents: List[str]
    workflow_steps: List[Dict[str, Any]]
    enabled: bool
    usage_count: int
    success_count: int
    
    class Config:
        from_attributes = True


def get_default_collaboration_patterns() -> List[Dict[str, Any]]:
    """Get default collaboration patterns."""
    return [
        {
            "pattern_id": "code_review_collaboration",
            "name": "Code Review Collaboration",
            "description": "Code Editor and Test Engineer collaborate on code changes",
            "pattern_type": "peer_to_peer",
            "required_agents": ["code_editor", "test_engineer"],
            "optional_agents": ["security_analyst"],
            "workflow_steps": [
                {"step": 1, "agent": "code_editor", "action": "analyze_code_changes"},
                {"step": 2, "agent": "test_engineer", "action": "generate_tests", "parallel": True},
                {"step": 3, "agent": "code_editor", "action": "apply_feedback"},
                {"step": 4, "agent": "test_engineer", "action": "run_tests"}
            ],
            "max_steps": 10,
            "max_execution_time": 180
        },
        {
            "pattern_id": "hierarchical_task_decomposition",
            "name": "Hierarchical Task Decomposition",
            "description": "Master Orchestrator delegates to specialists",
            "pattern_type": "hierarchical",
            "required_agents": ["master_orchestrator"],
            "optional_agents": ["project_manager", "codebase_analyst", "code_editor"],
            "workflow_steps": [
                {"step": 1, "agent": "master_orchestrator", "action": "analyze_task"},
                {"step": 2, "agent": "master_orchestrator", "action": "decompose_task"},
                {"step": 3, "agent": "master_orchestrator", "action": "delegate_subtasks"},
                {"step": 4, "agent": "specialists", "action": "execute_subtasks", "parallel": True},
                {"step": 5, "agent": "master_orchestrator", "action": "synthesize_results"}
            ],
            "max_steps": 20,
            "max_execution_time": 300
        }
    ]
    
    
    class WorkflowStatus(BaseModel):
        """Schema for workflow status."""
        workflow_id: str
        status: CollaborationStatus
        current_step: Optional[int] = None
        total_steps: Optional[int] = None
        progress_percentage: Optional[float] = None
        estimated_completion: Optional[datetime] = None
        active_agents: Optional[List[str]] = None
        last_activity: Optional[datetime] = None

