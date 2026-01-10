"""
Execution Guardrails Models

Models for runtime monitoring and safety guardrails during agent execution.
"""

from datetime import datetime
from typing import Optional, Dict, Any, List
from enum import Enum
from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, Text, JSON, ForeignKey, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from pydantic import BaseModel, Field
import uuid

from app.database.database import Base


class GuardrailType(str, Enum):
    """Types of guardrails."""
    RELEVANCE_CHECK = "relevance_check"
    CONTENT_FILTER = "content_filter"
    TOKEN_LIMIT = "token_limit"
    EXECUTION_TIME = "execution_time"
    RATE_LIMIT = "rate_limit"
    OUTPUT_VALIDATION = "output_validation"
    SAFETY_CHECK = "safety_check"


class GuardrailSeverity(str, Enum):
    """Severity levels for guardrail violations."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class GuardrailAction(str, Enum):
    """Actions taken when guardrail is triggered."""
    LOG_ONLY = "log_only"
    WARN_USER = "warn_user"
    TRUNCATE_OUTPUT = "truncate_output"
    STOP_EXECUTION = "stop_execution"
    REQUEST_APPROVAL = "request_approval"


class ExecutionGuardrail(Base):
    """
    Execution Guardrail - Tracks guardrail violations during agent execution.
    """
    __tablename__ = "execution_guardrails"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    execution_id = Column(UUID(as_uuid=True), nullable=False, index=True)  # Links to agent_executions
    agent_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    
    # Guardrail details
    guardrail_type = Column(SQLEnum(GuardrailType), nullable=False, index=True)
    severity = Column(SQLEnum(GuardrailSeverity), nullable=False, index=True)
    action_taken = Column(SQLEnum(GuardrailAction), nullable=False)
    
    # Violation details
    violation_description = Column(Text, nullable=False)
    violation_data = Column(JSONB, nullable=True)  # Additional context
    threshold_value = Column(Float, nullable=True)  # Expected threshold
    actual_value = Column(Float, nullable=True)  # Actual value that triggered
    
    # Context
    input_text = Column(Text, nullable=True)
    output_text = Column(Text, nullable=True)
    execution_context = Column(JSONB, nullable=True)
    
    # Resolution
    resolved = Column(Boolean, default=False)
    resolution_action = Column(String(255), nullable=True)
    resolved_by = Column(UUID(as_uuid=True), nullable=True)
    resolved_at = Column(DateTime, nullable=True)
    
    # Timestamps
    triggered_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    def __repr__(self):
        return f"<ExecutionGuardrail {self.guardrail_type.value} - {self.severity.value}>"


class GuardrailConfiguration(Base):
    """
    Guardrail Configuration - Defines guardrail rules and thresholds.
    """
    __tablename__ = "guardrail_configurations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    config_id = Column(String(100), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    
    # Configuration
    guardrail_type = Column(SQLEnum(GuardrailType), nullable=False, index=True)
    enabled = Column(Boolean, default=True)
    
    # Thresholds
    threshold_config = Column(JSONB, nullable=False)  # Type-specific thresholds
    severity = Column(SQLEnum(GuardrailSeverity), nullable=False)
    action = Column(SQLEnum(GuardrailAction), nullable=False)
    
    # Scope
    applies_to_agents = Column(JSONB, nullable=True)  # List of agent categories or IDs
    applies_to_categories = Column(JSONB, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<GuardrailConfiguration {self.config_id} - {self.guardrail_type.value}>"


class GuardrailMetrics(Base):
    """
    Guardrail Metrics - Aggregated metrics for guardrail performance.
    """
    __tablename__ = "guardrail_metrics"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    date = Column(DateTime, nullable=False, index=True)
    
    # Metrics by type
    guardrail_type = Column(SQLEnum(GuardrailType), nullable=False, index=True)
    total_checks = Column(Integer, default=0)
    total_violations = Column(Integer, default=0)
    
    # By severity
    info_count = Column(Integer, default=0)
    warning_count = Column(Integer, default=0)
    error_count = Column(Integer, default=0)
    critical_count = Column(Integer, default=0)
    
    # By action
    logged_count = Column(Integer, default=0)
    warned_count = Column(Integer, default=0)
    stopped_count = Column(Integer, default=0)
    approval_requested_count = Column(Integer, default=0)
    
    # Performance
    avg_check_time_ms = Column(Float, default=0.0)
    
    def __repr__(self):
        return f"<GuardrailMetrics {self.guardrail_type.value} - {self.date.date()}>"


# ============================================================================
# Pydantic Schemas
# ============================================================================

class GuardrailViolation(BaseModel):
    """Schema for guardrail violation."""
    guardrail_type: GuardrailType
    severity: GuardrailSeverity
    action_taken: GuardrailAction
    violation_description: str
    violation_data: Optional[Dict[str, Any]] = None
    threshold_value: Optional[float] = None
    actual_value: Optional[float] = None


class GuardrailCheckResult(BaseModel):
    """Schema for guardrail check result."""
    passed: bool
    violations: List[GuardrailViolation] = []
    should_stop_execution: bool = False
    modified_output: Optional[str] = None


class GuardrailConfigCreate(BaseModel):
    """Schema for creating guardrail configuration."""
    config_id: str = Field(..., pattern="^[a-z0-9_]+$")
    name: str
    description: str
    guardrail_type: GuardrailType
    enabled: bool = True
    threshold_config: Dict[str, Any]
    severity: GuardrailSeverity
    action: GuardrailAction
    applies_to_agents: Optional[List[str]] = None
    applies_to_categories: Optional[List[str]] = None


class GuardrailConfigResponse(BaseModel):
    """Schema for guardrail configuration response."""
    id: str
    config_id: str
    name: str
    description: str
    guardrail_type: GuardrailType
    enabled: bool
    threshold_config: Dict[str, Any]
    severity: GuardrailSeverity
    action: GuardrailAction
    
    class Config:
        from_attributes = True


def get_default_guardrail_configs() -> List[Dict[str, Any]]:
    """Get default guardrail configurations."""
    return [
        {
            "config_id": "relevance_classifier",
            "name": "Relevance Classifier",
            "description": "Detects when agent responses drift off-topic",
            "guardrail_type": GuardrailType.RELEVANCE_CHECK,
            "enabled": True,
            "threshold_config": {
                "min_relevance_score": 0.6,
                "check_method": "semantic_similarity"
            },
            "severity": GuardrailSeverity.WARNING,
            "action": GuardrailAction.WARN_USER
        },
        {
            "config_id": "content_safety_filter",
            "name": "Content Safety Filter",
            "description": "Filters inappropriate or harmful content",
            "guardrail_type": GuardrailType.CONTENT_FILTER,
            "enabled": True,
            "threshold_config": {
                "blocked_patterns": ["harmful", "inappropriate"],
                "check_pii": True,
                "check_profanity": True
            },
            "severity": GuardrailSeverity.ERROR,
            "action": GuardrailAction.TRUNCATE_OUTPUT
        },
        {
            "config_id": "token_usage_monitor",
            "name": "Token Usage Monitor",
            "description": "Prevents runaway token generation",
            "guardrail_type": GuardrailType.TOKEN_LIMIT,
            "enabled": True,
            "threshold_config": {
                "max_tokens": 8192,
                "warning_threshold": 6000
            },
            "severity": GuardrailSeverity.ERROR,
            "action": GuardrailAction.STOP_EXECUTION
        },
        {
            "config_id": "execution_time_circuit_breaker",
            "name": "Execution Time Circuit Breaker",
            "description": "Stops execution if it exceeds time limit",
            "guardrail_type": GuardrailType.EXECUTION_TIME,
            "enabled": True,
            "threshold_config": {
                "max_execution_seconds": 300,
                "warning_threshold_seconds": 240
            },
            "severity": GuardrailSeverity.CRITICAL,
            "action": GuardrailAction.STOP_EXECUTION
        },
        {
            "config_id": "rate_limit_enforcer",
            "name": "Rate Limit Enforcer",
            "description": "Enforces rate limits on agent executions",
            "guardrail_type": GuardrailType.RATE_LIMIT,
            "enabled": True,
            "threshold_config": {
                "max_requests_per_minute": 60,
                "max_requests_per_hour": 1000
            },
            "severity": GuardrailSeverity.WARNING,
            "action": GuardrailAction.WARN_USER
        }
    ]
    
    
    class GuardrailViolationResponse(BaseModel):
        """Schema for guardrail violation response."""
        id: str
        execution_id: str
        agent_id: str
        guardrail_type: GuardrailType
        severity: GuardrailSeverity
        action_taken: GuardrailAction
        violation_description: str
        triggered_at: datetime
        resolved: bool
        resolved_at: Optional[datetime] = None
        
        class Config:
            from_attributes = True

