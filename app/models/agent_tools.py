"""
Agent Tools Models

Database models and schemas for the agent tool catalog and permission system.
"""

from datetime import datetime
from typing import Optional, Dict, Any, List
from enum import Enum
from sqlalchemy import Column, String, Integer, Boolean, DateTime, Text, JSON, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from pydantic import BaseModel, Field
import uuid

from app.database.database import Base


class ToolCategory(str, Enum):
    """Tool categories for organization."""
    DATABASE = "database"
    API = "api"
    FILE_SYSTEM = "file_system"
    POWERSHELL = "powershell"
    BASH = "bash"
    ANALYSIS = "analysis"
    COMMUNICATION = "communication"
    SEARCH = "search"
    CODE_EXECUTION = "code_execution"
    MONITORING = "monitoring"


class ToolSecurityLevel(str, Enum):
    """Security levels for tools."""
    SAFE = "safe"  # Read-only, no side effects
    LOW_RISK = "low_risk"  # Limited write operations
    MEDIUM_RISK = "medium_risk"  # Moderate write operations
    HIGH_RISK = "high_risk"  # Significant system changes
    CRITICAL = "critical"  # Requires human approval


class AgentToolCatalog(Base):
    """
    Tool Catalog - Available tools that agents can use.
    """
    __tablename__ = "agent_tool_catalog"
    __table_args__ = {'extend_existing': True}

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tool_id = Column(String(100), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    display_name = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    category = Column(SQLEnum(ToolCategory), nullable=False, index=True)
    security_level = Column(SQLEnum(ToolSecurityLevel), nullable=False, index=True)

    # Configuration
    configuration_schema = Column(JSON, nullable=True)  # JSON schema for tool config
    default_configuration = Column(JSON, nullable=True)
    required_permissions = Column(JSON, nullable=False, default=list)  # List of required permissions

    # Implementation details
    implementation_class = Column(String(500), nullable=True)  # Python class path
    implementation_function = Column(String(500), nullable=True)  # Function to call

    # Constraints
    max_execution_time = Column(Integer, default=30)  # Max seconds
    rate_limit = Column(Integer, default=10)  # Max calls per minute
    requires_human_approval = Column(Boolean, default=False)

    # Phase 5: Stateful execution
    stateful = Column(Boolean, default=False, nullable=False)
    requires_sandbox = Column(Boolean, default=False, nullable=False)
    sandbox_image = Column(String(255), nullable=True)  # Docker image name
    max_session_duration = Column(Integer, default=300)  # seconds

    # Status
    enabled = Column(Boolean, default=True)
    deprecated = Column(Boolean, default=False)
    deprecation_message = Column(Text, nullable=True)

    # Metadata
    version = Column(String(50), default="1.0.0")
    documentation_url = Column(String(500), nullable=True)
    examples = Column(JSON, nullable=True)  # Example usage

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    permissions = relationship("app.models.agent_tools.ToolPermission", back_populates="tool", cascade="all, delete-orphan")
    sessions = relationship("app.models.agent_tools.ToolSession", back_populates="tool", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<AgentToolCatalog {self.tool_id} - {self.name} ({self.security_level.value})>"


class ToolPermission(Base):
    """
    Tool Permissions - Maps tools to agent categories and security constraints.
    """
    __tablename__ = "agent_tool_permissions"
    __table_args__ = {'extend_existing': True}

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tool_id = Column(String(36), ForeignKey("agent_tool_catalog.id"), nullable=False, index=True)

    # Permission scope
    agent_category = Column(String(100), nullable=True, index=True)  # e.g., "automation", "support"
    agent_tier = Column(String(50), nullable=True)  # For system agents

    # Constraints
    allowed = Column(Boolean, default=True)
    max_calls_per_execution = Column(Integer, nullable=True)
    additional_constraints = Column(JSON, nullable=True)

    # Approval requirements
    requires_approval_override = Column(Boolean, default=False)
    approval_reason = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    tool = relationship("app.models.agent_tools.AgentToolCatalog", back_populates="permissions")

    def __repr__(self):
        return f"<ToolPermission {self.agent_category} - Tool: {self.tool_id}>"


class ToolUsageLog(Base):
    """
    Tool Usage Log - Tracks tool usage by agents.
    """
    __tablename__ = "tool_usage_logs"
    __table_args__ = {'extend_existing': True}

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    execution_id = Column(String(36), nullable=False, index=True)  # Links to agent_executions
    tool_id = Column(String(36), ForeignKey("agent_tool_catalog.id"), nullable=False, index=True)
    agent_id = Column(String(36), nullable=False, index=True)

    # Execution details
    input_parameters = Column(JSON, nullable=True)
    output_result = Column(JSON, nullable=True)
    execution_time = Column(Integer, nullable=True)  # Milliseconds
    success = Column(Boolean, default=True)
    error_message = Column(Text, nullable=True)

    # Security
    approved_by = Column(String(36), nullable=True)  # If human approval was required
    approval_timestamp = Column(DateTime, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<ToolUsageLog {self.tool_id} - Execution: {self.execution_id}>"


# ============================================================================
# Pydantic Schemas
# ============================================================================

class ToolCatalogBase(BaseModel):
    """Base schema for tool catalog."""
    tool_id: str = Field(..., pattern="^[a-z0-9_]+$")
    name: str
    display_name: str
    description: str
    category: ToolCategory
    security_level: ToolSecurityLevel
    configuration_schema: Optional[Dict[str, Any]] = None
    default_configuration: Optional[Dict[str, Any]] = None
    required_permissions: List[str] = []
    implementation_class: Optional[str] = None
    implementation_function: Optional[str] = None
    max_execution_time: int = 30
    rate_limit: int = 10
    requires_human_approval: bool = False
    enabled: bool = True
    version: str = "1.0.0"
    documentation_url: Optional[str] = None
    examples: Optional[List[Dict[str, Any]]] = None


class ToolCatalogCreate(ToolCatalogBase):
    """Schema for creating a tool in the catalog."""
    pass


class ToolCatalogResponse(ToolCatalogBase):
    """Schema for tool catalog response."""
    id: str
    deprecated: bool
    deprecation_message: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ToolPermissionCreate(BaseModel):
    """Schema for creating tool permission."""
    tool_id: str
    agent_category: Optional[str] = None
    agent_tier: Optional[str] = None
    allowed: bool = True
    max_calls_per_execution: Optional[int] = None
    additional_constraints: Optional[Dict[str, Any]] = None
    requires_approval_override: bool = False
    approval_reason: Optional[str] = None


class ToolPermissionResponse(BaseModel):
    """Schema for tool permission response."""
    id: str
    tool_id: str
    agent_category: Optional[str]
    agent_tier: Optional[str]
    allowed: bool
    max_calls_per_execution: Optional[int]
    requires_approval_override: bool

    class Config:
        from_attributes = True


class ToolUsageRequest(BaseModel):
    """Schema for tool usage request."""
    tool_id: str
    input_parameters: Dict[str, Any]
    execution_context: Optional[Dict[str, Any]] = None


class ToolUsageResponse(BaseModel):
    """Schema for tool usage response."""
    success: bool
    output_result: Optional[Dict[str, Any]] = None
    execution_time: int
    error_message: Optional[str] = None
    requires_approval: bool = False
    approval_id: Optional[str] = None


class AgentToolRequest(BaseModel):
    """Schema for agent tool request in agent sheet."""
    tool_id: str
    enabled: bool = True
    configuration: Dict[str, Any] = {}
    max_calls: Optional[int] = None


def get_default_tool_catalog() -> List[Dict[str, Any]]:
    """Get default tool catalog entries."""
    return [
        {
            "tool_id": "database_query",
            "name": "Database Query",
            "display_name": "Database Query Tool",
            "description": "Execute read-only database queries",
            "category": ToolCategory.DATABASE,
            "security_level": ToolSecurityLevel.SAFE,
            "configuration_schema": {
                "type": "object",
                "properties": {
                    "max_query_time": {"type": "integer", "default": 30},
                    "allowed_tables": {"type": "array", "items": {"type": "string"}}
                }
            },
            "default_configuration": {
                "max_query_time": 30,
                "allowed_tables": []
            },
            "required_permissions": ["database.read"],
            "max_execution_time": 30,
            "rate_limit": 10,
            "requires_human_approval": False,
            "enabled": True,
            "version": "1.0.0"
        },
        {
            "tool_id": "powershell_ad_query",
            "name": "PowerShell AD Query",
            "display_name": "Active Directory Query",
            "description": "Query Active Directory using PowerShell",
            "category": ToolCategory.POWERSHELL,
            "security_level": ToolSecurityLevel.LOW_RISK,
            "configuration_schema": {
                "type": "object",
                "properties": {
                    "allowed_commands": {"type": "array", "items": {"type": "string"}},
                    "timeout": {"type": "integer", "default": 60}
                }
            },
            "default_configuration": {
                "allowed_commands": ["Get-ADUser", "Get-ADGroup", "Get-ADComputer"],
                "timeout": 60
            },
            "required_permissions": ["ad.read"],
            "max_execution_time": 60,
            "rate_limit": 5,
            "requires_human_approval": False,
            "enabled": True,
            "version": "1.0.0"
        },
        {
            "tool_id": "powershell_ad_modify",
            "name": "PowerShell AD Modify",
            "display_name": "Active Directory Modification",
            "description": "Modify Active Directory objects using PowerShell",
            "category": ToolCategory.POWERSHELL,
            "security_level": ToolSecurityLevel.HIGH_RISK,
            "configuration_schema": {
                "type": "object",
                "properties": {
                    "allowed_commands": {"type": "array", "items": {"type": "string"}},
                    "timeout": {"type": "integer", "default": 120}
                }
            },
            "default_configuration": {
                "allowed_commands": ["Set-ADUser", "Set-ADGroup", "Add-ADGroupMember"],
                "timeout": 120
            },
            "required_permissions": ["ad.write", "ad.modify"],
            "max_execution_time": 120,
            "rate_limit": 2,
            "requires_human_approval": True,
            "enabled": True,
            "version": "1.0.0"
        }
    ]



# ============================================================================
# Phase 5: Tool Sessions
# ============================================================================

class ToolSession(Base):
    """
    Tool Session - Active stateful tool execution sessions.
    """
    __tablename__ = "tool_sessions"
    __table_args__ = {'extend_existing': True}

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String(255), unique=True, nullable=False, index=True)

    # References
    tool_id = Column(String(36), ForeignKey("agent_tool_catalog.id"), nullable=False, index=True)
    agent_id = Column(String(255), nullable=False, index=True)
    execution_id = Column(String(255), nullable=True, index=True)

    # Sandbox details
    sandbox_id = Column(String(255), nullable=True)  # Docker container ID
    sandbox_status = Column(String(50), nullable=True)  # running, stopped, error

    # Status
    status = Column(String(50), nullable=False, default="active")  # active, closed, expired

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    expires_at = Column(DateTime, nullable=True)
    closed_at = Column(DateTime, nullable=True)

    # Relationships
    tool = relationship("app.models.agent_tools.AgentToolCatalog", back_populates="sessions")

    def __repr__(self):
        return f"<ToolSession {self.session_id} - {self.status}>"


class ToolExecution(Base):
    """
    Tool Execution - Individual tool execution records for Level 1 Sandbox Environment.
    Tracks each execution within a sandbox session with detailed metrics.
    """
    __tablename__ = "tool_executions"
    __table_args__ = {'extend_existing': True}

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    execution_id = Column(String(255), unique=True, nullable=False, index=True)

    # References
    session_id = Column(String(255), ForeignKey("tool_sessions.session_id"), nullable=False, index=True)
    tool_id = Column(String(36), ForeignKey("agent_tool_catalog.id"), nullable=False, index=True)
    agent_id = Column(String(255), nullable=False, index=True)

    # Execution details
    command = Column(Text, nullable=False)
    working_directory = Column(String(500), nullable=True)
    environment_variables = Column(JSON, nullable=True)
    input_parameters = Column(JSON, nullable=True)

    # Results
    stdout = Column(Text, nullable=True)
    stderr = Column(Text, nullable=True)
    exit_code = Column(Integer, nullable=True)
    success = Column(Boolean, nullable=False, default=False)
    error_message = Column(Text, nullable=True)

    # Performance metrics
    execution_time_ms = Column(Integer, nullable=True)
    memory_usage_mb = Column(Integer, nullable=True)
    cpu_usage_percent = Column(Integer, nullable=True)

    # Security and resource tracking
    resource_limits_enforced = Column(Boolean, default=True)
    security_violations = Column(JSON, nullable=True)

    # Timestamps
    started_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    def __repr__(self):
        return f"<ToolExecution {self.execution_id} - {self.success}>"
