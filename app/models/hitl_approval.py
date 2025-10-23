"""
Human-in-the-Loop (HITL) Approval Models

Models for managing human approval workflows for high-risk agent operations.
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


class ApprovalStatus(str, Enum):
    """Status of approval request."""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


class RiskLevel(str, Enum):
    """Risk level of the action."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ActionType(str, Enum):
    """Types of actions that may require approval."""
    DATA_DELETION = "data_deletion"
    DATA_MODIFICATION = "data_modification"
    EXTERNAL_API_CALL = "external_api_call"
    SYSTEM_MODIFICATION = "system_modification"
    USER_ACCOUNT_CHANGE = "user_account_change"
    FINANCIAL_TRANSACTION = "financial_transaction"
    SECURITY_POLICY_CHANGE = "security_policy_change"
    TOOL_EXECUTION = "tool_execution"
    CUSTOM = "custom"


class PendingApproval(Base):
    """
    Pending Approval - Tracks approval requests for high-risk operations.
    """
    __tablename__ = "pending_approvals"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    approval_id = Column(String(100), unique=True, nullable=False, index=True)
    
    # Execution context
    execution_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    agent_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    agent_name = Column(String(255), nullable=False)
    
    # Action details
    action_type = Column(SQLEnum(ActionType), nullable=False, index=True)
    action_description = Column(Text, nullable=False)
    action_details = Column(JSONB, nullable=False)  # Full action parameters
    
    # Risk assessment
    risk_level = Column(SQLEnum(RiskLevel), nullable=False, index=True)
    risk_factors = Column(JSONB, nullable=True)  # List of risk factors
    impact_assessment = Column(Text, nullable=True)
    
    # Request details
    requested_by = Column(UUID(as_uuid=True), nullable=True)  # User who initiated
    requested_at = Column(DateTime, default=datetime.utcnow, index=True)
    expires_at = Column(DateTime, nullable=True)  # Auto-reject after this time
    
    # Status
    status = Column(SQLEnum(ApprovalStatus), nullable=False, default=ApprovalStatus.PENDING, index=True)

    # Phase 5: Interactive consultation
    consultation_active = Column(Boolean, default=False, nullable=False)
    consultation_started_at = Column(DateTime, nullable=True)
    consultation_ended_at = Column(DateTime, nullable=True)

    # Review details
    reviewed_by = Column(UUID(as_uuid=True), nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    approval_decision = Column(String(50), nullable=True)  # approved/rejected
    rejection_reason = Column(Text, nullable=True)
    reviewer_notes = Column(Text, nullable=True)
    
    # Execution result (if approved)
    executed = Column(Boolean, default=False)
    execution_result = Column(JSONB, nullable=True)
    execution_error = Column(Text, nullable=True)
    executed_at = Column(DateTime, nullable=True)
    
    # Metadata
    priority = Column(Integer, default=5)  # 1-10, higher = more urgent
    notification_sent = Column(Boolean, default=False)
    notification_channels = Column(JSONB, nullable=True)  # email, webhook, etc.
    
    # Relationships
    consultation_messages = relationship("ConsultationMessage", back_populates="approval", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<PendingApproval {self.approval_id} - {self.action_type.value} ({self.status.value})>"


class ApprovalPolicy(Base):
    """
    Approval Policy - Defines which actions require approval and who can approve.
    """
    __tablename__ = "approval_policies"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    policy_id = Column(String(100), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    
    # Policy scope
    action_types = Column(JSONB, nullable=False)  # List of ActionType values
    agent_categories = Column(JSONB, nullable=True)  # Applies to these categories
    agent_ids = Column(JSONB, nullable=True)  # Applies to specific agents
    
    # Approval requirements
    requires_approval = Column(Boolean, default=True)
    min_risk_level = Column(SQLEnum(RiskLevel), nullable=False)  # Minimum risk to trigger
    
    # Approvers
    approver_roles = Column(JSONB, nullable=False)  # List of roles that can approve
    approver_users = Column(JSONB, nullable=True)  # Specific user IDs
    require_multiple_approvers = Column(Boolean, default=False)
    min_approvers = Column(Integer, default=1)
    
    # Timeouts
    approval_timeout_minutes = Column(Integer, default=60)  # Auto-reject after timeout
    
    # Notifications
    notify_on_request = Column(Boolean, default=True)
    notification_channels = Column(JSONB, nullable=True)
    
    # Status
    enabled = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<ApprovalPolicy {self.policy_id} - {self.name}>"


class ApprovalAuditLog(Base):
    """
    Approval Audit Log - Tracks all approval-related events.
    """
    __tablename__ = "approval_audit_logs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    approval_id = Column(UUID(as_uuid=True), ForeignKey("pending_approvals.id"), nullable=False, index=True)
    
    # Event details
    event_type = Column(String(100), nullable=False)  # requested, approved, rejected, executed, etc.
    event_description = Column(Text, nullable=False)
    event_data = Column(JSONB, nullable=True)
    
    # Actor
    actor_id = Column(UUID(as_uuid=True), nullable=True)
    actor_role = Column(String(100), nullable=True)
    
    # Timestamp
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    def __repr__(self):
        return f"<ApprovalAuditLog {self.event_type} - {self.created_at}>"


# ============================================================================
# Phase 5: Consultation Messages
# ============================================================================

class ConsultationMessage(Base):
    """
    Consultation Message - Messages exchanged during HITL consultation.
    """
    __tablename__ = "consultation_messages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    approval_id = Column(UUID(as_uuid=True), ForeignKey("pending_approvals.id"), nullable=False, index=True)

    # Message details
    sender_id = Column(String(255), nullable=False, index=True)
    sender_type = Column(String(50), nullable=False)  # human, agent
    message = Column(Text, nullable=False)

    # Metadata
    metadata = Column(JSONB, nullable=True)

    # Timestamp
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    approval = relationship("PendingApproval", back_populates="consultation_messages")

    def __repr__(self):
        return f"<ConsultationMessage {self.sender_type} - {self.sender_id}>"


# ============================================================================
# Pydantic Schemas
# ============================================================================

class ApprovalRequestCreate(BaseModel):
    """Schema for creating an approval request."""
    execution_id: str
    agent_id: str
    agent_name: str
    action_type: ActionType
    action_description: str
    action_details: Dict[str, Any]
    risk_level: RiskLevel
    risk_factors: Optional[List[str]] = None
    impact_assessment: Optional[str] = None
    requested_by: Optional[str] = None
    priority: int = 5


class ApprovalRequestResponse(BaseModel):
    """Schema for approval request response."""
    id: str
    approval_id: str
    execution_id: str
    agent_name: str
    action_type: ActionType
    action_description: str
    risk_level: RiskLevel
    status: ApprovalStatus
    requested_at: datetime
    expires_at: Optional[datetime]
    priority: int
    
    class Config:
        from_attributes = True


class ApprovalDecision(BaseModel):
    """Schema for approval decision."""
    approval_id: str
    decision: str  # "approve" or "reject"
    reviewer_notes: Optional[str] = None
    rejection_reason: Optional[str] = None


class ApprovalDecisionResponse(BaseModel):
    """Schema for approval decision response."""
    approval_id: str
    status: ApprovalStatus
    reviewed_by: str
    reviewed_at: datetime
    decision: str
    
    class Config:
        from_attributes = True


class ApprovalPolicyCreate(BaseModel):
    """Schema for creating approval policy."""
    policy_id: str = Field(..., pattern="^[a-z0-9_]+$")
    name: str
    description: str
    action_types: List[ActionType]
    agent_categories: Optional[List[str]] = None
    agent_ids: Optional[List[str]] = None
    requires_approval: bool = True
    min_risk_level: RiskLevel
    approver_roles: List[str]
    approver_users: Optional[List[str]] = None
    require_multiple_approvers: bool = False
    min_approvers: int = 1
    approval_timeout_minutes: int = 60
    notify_on_request: bool = True
    notification_channels: Optional[List[str]] = None


class ApprovalPolicyResponse(BaseModel):
    """Schema for approval policy response."""
    id: str
    policy_id: str
    name: str
    description: str
    action_types: List[ActionType]
    min_risk_level: RiskLevel
    approver_roles: List[str]
    enabled: bool
    
    class Config:
        from_attributes = True


def get_default_approval_policies() -> List[Dict[str, Any]]:
    """Get default approval policies."""
    return [
        {
            "policy_id": "high_risk_data_operations",
            "name": "High Risk Data Operations",
            "description": "Requires approval for data deletion and modification",
            "action_types": [ActionType.DATA_DELETION, ActionType.DATA_MODIFICATION],
            "min_risk_level": RiskLevel.HIGH,
            "approver_roles": ["admin", "data_steward"],
            "approval_timeout_minutes": 30,
            "notify_on_request": True,
            "notification_channels": ["email", "webhook"]
        },
        {
            "policy_id": "system_modifications",
            "name": "System Modifications",
            "description": "Requires approval for system configuration changes",
            "action_types": [ActionType.SYSTEM_MODIFICATION, ActionType.SECURITY_POLICY_CHANGE],
            "min_risk_level": RiskLevel.MEDIUM,
            "approver_roles": ["admin", "system_admin"],
            "require_multiple_approvers": True,
            "min_approvers": 2,
            "approval_timeout_minutes": 60,
            "notify_on_request": True
        },
        {
            "policy_id": "user_account_changes",
            "name": "User Account Changes",
            "description": "Requires approval for user account modifications",
            "action_types": [ActionType.USER_ACCOUNT_CHANGE],
            "min_risk_level": RiskLevel.MEDIUM,
            "approver_roles": ["admin", "hr_admin"],
            "approval_timeout_minutes": 120,
            "notify_on_request": True
        }
    ]

