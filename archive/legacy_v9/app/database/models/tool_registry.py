"""
Database models for Tool Registry System
Part of Prometheus Week 3 Implementation - Consolidated and Enhanced

This module contains enhanced database models that align with:
- The new Universal Tool Integration Framework 
- Week 1 legacy models
- Enhanced functionality for the armory architecture
"""

from sqlalchemy import Column, String, Text, Boolean, Integer, JSON, DateTime, ForeignKey, Float, Enum as SQLEnum
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import enum
from app.database.database import Base

# Enums for tool integration
class ToolStatus(str, enum.Enum):
    """Tool status enumeration"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    MAINTENANCE = "maintenance"
    DEPRECATED = "deprecated"


class SecurityLevel(str, enum.Enum):
    """Tool security levels"""
    SAFE = "safe"
    LOW_RISK = "low_risk"
    MEDIUM_RISK = "medium_risk"
    HIGH_RISK = "high_risk"
    CRITICAL = "critical"


class ToolCategory(str, enum.Enum):
    """Tool categories for organization"""
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
    EDUCATIONAL = "educational"
    RESEARCH = "research"
    CONTENT_CREATION = "content_creation"
    ASSESSMENT = "assessment"
    LLM = "llm"
    WEB_SCRAPING = "web_scraping"
    DATA_PROCESSING = "data_processing"
    VISUALIZATION = "visualization"


class PermissionLevel(str, enum.Enum):
    """Permission levels for tool access"""
    READ = "read"
    WRITE = "write"
    EXECUTE = "execute"
    ADMIN = "admin"
    OWNER = "owner"


class SessionStatus(str, enum.Enum):
    """Session status enumeration"""
    ACTIVE = "active"
    COMPLETED = "completed"
    ERROR = "error"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"


class ExecutionStatus(str, enum.Enum):
    """Execution status enumeration"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"


class ErrorSeverity(str, enum.Enum):
    """Error severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class MemoryContextType(str, enum.Enum):
    """Memory context types"""
    GENERAL = "general"
    TASK = "task"
    SESSION = "session"
    WORKFLOW = "workflow"
    LEARNING = "learning"


class ToolRegistry(Base):
    """Enhanced Tool Registry table for managing AI agent tools"""
    
    __tablename__ = "tool_registry"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False, unique=True)
    description = Column(Text, nullable=True)
    version = Column(String(50), nullable=False, default="1.0.0")
    
    # Enhanced tool metadata
    category = Column(SQLEnum(ToolCategory), nullable=False, default=ToolCategory.CONTENT_CREATION)
    security_level = Column(SQLEnum(SecurityLevel), nullable=False, default=SecurityLevel.MEDIUM_RISK)
    status = Column(SQLEnum(ToolStatus), nullable=False, default=ToolStatus.ACTIVE)
    
    # Tool execution configuration
    schema_json = Column(JSON, nullable=True)  # OpenAPI schema for tool
    function_signature = Column(JSON, nullable=False)  # JSON schema for tool parameters
    permissions = Column(JSON, nullable=False, default=dict)  # Access control permissions
    requires_sandbox = Column(Boolean, default=False, nullable=False)
    sandbox_image = Column(String(255), nullable=True)  # Docker image for sandbox
    
    # Session and execution limits
    max_session_duration = Column(Integer, default=300)  # seconds
    stateful = Column(Boolean, default=False, nullable=False)
    active = Column(Boolean, default=True, nullable=False)
    
    # Tool metadata
    tool_metadata = Column(JSON, nullable=True)  # Additional tool metadata
    dependencies = Column(JSON, nullable=True)  # Tool dependencies
    capabilities = Column(JSON, nullable=True)  # Tool capabilities
    tags = Column(JSON, nullable=True)  # Tool tags for search
    
    # Audit fields
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    created_by = Column(String(255), nullable=True)  # Who created the tool
    last_used_at = Column(DateTime, nullable=True)  # Last time tool was executed
    
    # Relationships
    permissions_rel = relationship("ToolPermission", back_populates="tool", cascade="all, delete-orphan")
    sessions = relationship("ToolSession", back_populates="tool")
    executions = relationship("ToolExecution", back_populates="tool")
    
    def __repr__(self):
        return f"<ToolRegistry(id='{self.id}', name='{self.name}', version='{self.version}', category='{self.category}')>"


class ToolPermission(Base):
    """Enhanced Tool permission system for access control"""
    
    __tablename__ = "tool_permissions"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tool_id = Column(String(36), ForeignKey("tool_registry.id"), nullable=False)
    principal_id = Column(String(255), nullable=True)  # Agent, user, or role ID
    principal_type = Column(String(50), nullable=False, default="user")  # agent, user, role, group
    permission_level = Column(SQLEnum(PermissionLevel), nullable=False, default=PermissionLevel.READ)
    
    # Permission configuration
    conditions = Column(JSON, nullable=True)  # Conditions for permission
    expires_at = Column(DateTime, nullable=True)  # Optional expiration
    
    # Audit fields
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    created_by = Column(String(255), nullable=True)
    
    # Relationships
    tool = relationship("ToolRegistry", back_populates="permissions_rel")
    
    def __repr__(self):
        return f"<ToolPermission(tool='{self.tool_id}', principal='{self.principal_id}', level='{self.permission_level}')>"


class ToolSession(Base):
    """Enhanced Tool execution sessions for stateful tools"""
    
    __tablename__ = "tool_sessions"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tool_id = Column(String(36), ForeignKey("tool_registry.id"), nullable=False)
    agent_id = Column(String(36), nullable=False)
    user_id = Column(String(36), nullable=True)  # Optional user context
    
    # Session state
    session_state = Column(JSON, nullable=True)  # Current state of the session
    session_data = Column(JSON, nullable=True)  # Additional session data
    execution_id = Column(String(36), nullable=True)  # Link to specific execution
    
    # Sandbox information
    sandbox_id = Column(String(255), nullable=True)  # Docker container ID
    sandbox_status = Column(String(50), nullable=True)  # running, stopped, error
    sandbox_config = Column(JSON, nullable=True)  # Sandbox configuration
    
    # Session lifecycle
    status = Column(SQLEnum(SessionStatus), nullable=False, default=SessionStatus.ACTIVE)
    priority = Column(Integer, default=1)  # Session priority
    max_duration = Column(Integer, default=300)  # Maximum session duration in seconds
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    expires_at = Column(DateTime, nullable=True)  # Session expiration
    completed_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    tool = relationship("ToolRegistry", back_populates="sessions")
    executions = relationship("ToolExecution", back_populates="session")
    
    def __repr__(self):
        return f"<ToolSession(tool='{self.tool_id}', agent='{self.agent_id}', status='{self.status}')>"


class ToolExecution(Base):
    """Enhanced Individual tool execution records"""
    
    __tablename__ = "tool_executions"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String(36), ForeignKey("tool_sessions.id"), nullable=True)  # Optional session context
    tool_id = Column(String(36), ForeignKey("tool_registry.id"), nullable=False)
    
    # Execution context
    agent_id = Column(String(36), nullable=False)
    user_id = Column(String(36), nullable=True)  # Optional user context
    execution_context = Column(JSON, nullable=True)  # Execution context data
    
    # Input and output data
    input_data = Column(JSON, nullable=False)
    output_data = Column(JSON, nullable=True)
    error_message = Column(Text, nullable=True)
    error_details = Column(JSON, nullable=True)  # Additional error details
    
    # Execution metrics
    execution_time_ms = Column(Integer, nullable=True)  # Execution duration in milliseconds
    resource_usage = Column(JSON, nullable=True)  # CPU, memory, disk usage
    performance_metrics = Column(JSON, nullable=True)  # Additional performance data
    
    # Status and lifecycle
    status = Column(SQLEnum(ExecutionStatus), nullable=False, default=ExecutionStatus.PENDING)
    progress = Column(Float, default=0.0)  # Execution progress (0.0 to 1.0)
    requires_approval = Column(Boolean, default=False)  # Whether execution requires approval
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    
    # Relationships
    session = relationship("ToolSession", back_populates="executions")
    tool = relationship("ToolRegistry", back_populates="executions")
    
    def __repr__(self):
        return f"<ToolExecution(session='{self.session_id}', tool='{self.tool_id}', status='{self.status}')>"


# Memory Guild Tables for Week 1 Completion (Enhanced)
class MemoryContext(Base):
    """Enhanced Memory context storage for agent memory management"""
    
    __tablename__ = "memory_contexts"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    agent_id = Column(String(36), nullable=False)
    context_data = Column(JSON, nullable=False)
    parent_context_id = Column(String(36), ForeignKey("memory_contexts.id"), nullable=True)  # Context inheritance
    context_type = Column(SQLEnum(MemoryContextType), nullable=False, default=MemoryContextType.GENERAL)
    
    # Context management
    priority = Column(Integer, default=1, nullable=False)  # Context priority
    tags = Column(JSON, nullable=True)  # Context tags
    context_metadata = Column(JSON, nullable=True)  # Additional context metadata
    
    # Lifecycle
    expires_at = Column(DateTime, nullable=True)  # Optional expiration
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    last_accessed_at = Column(DateTime, nullable=True)
    
    # Self-referential relationship for context inheritance
    parent_context = relationship("MemoryContext", remote_side=[id], backref="child_contexts")
    
    def __repr__(self):
        return f"<MemoryContext(agent='{self.agent_id}', type='{self.context_type}', priority='{self.priority}')>"


class ErrorLog(Base):
    """Enhanced Error logging for Guardian self-healing system"""
    
    __tablename__ = "error_logs"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    error_type = Column(String(255), nullable=False)
    error_message = Column(Text, nullable=False)
    error_code = Column(String(50), nullable=True)  # Specific error code
    stack_trace = Column(Text, nullable=True)  # Stack trace information
    
    # Component and context information
    component = Column(String(255), nullable=False)  # Which component failed
    service_name = Column(String(255), nullable=True)  # Service where error occurred
    operation = Column(String(255), nullable=True)  # Operation that failed
    request_id = Column(String(36), nullable=True)  # Related request ID
    
    # Fix and resolution
    fix_applied = Column(Boolean, default=False, nullable=False)
    fix_details = Column(JSON, nullable=True)  # Details of applied fix
    resolution_notes = Column(Text, nullable=True)  # Notes about resolution
    
    # Severity and categorization
    severity = Column(SQLEnum(ErrorSeverity), nullable=False, default=ErrorSeverity.MEDIUM)
    category = Column(String(100), nullable=True)  # Error category
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    resolved_at = Column(DateTime, nullable=True)
    
    def __repr__(self):
        return f"<ErrorLog(type='{self.error_type}', component='{self.component}', severity='{self.severity}', fixed='{self.fix_applied}')>"


# Additional models for enhanced functionality
class ToolExecutionLog(Base):
    """Detailed execution logs for debugging and monitoring"""
    
    __tablename__ = "tool_execution_logs"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    execution_id = Column(String(36), ForeignKey("tool_executions.id"), nullable=False)
    log_level = Column(String(20), nullable=False)  # DEBUG, INFO, WARNING, ERROR
    message = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    source = Column(String(100), nullable=True)  # Log source (e.g., "tool_execution", "sandbox")
    log_metadata = Column(JSON, nullable=True)  # Additional log metadata
    
    # Relationships
    execution = relationship("ToolExecution")
    
    def __repr__(self):
        return f"<ToolExecutionLog(execution='{self.execution_id}', level='{self.log_level}', message='{self.message[:50]}...')>"


class SystemMetric(Base):
    """System performance and usage metrics"""
    
    __tablename__ = "system_metrics"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    metric_name = Column(String(100), nullable=False)
    metric_value = Column(Float, nullable=False)
    metric_type = Column(String(50), nullable=False)  # gauge, counter, histogram
    unit = Column(String(20), nullable=True)  # ms, bytes, count, etc.
    
    # Context
    component = Column(String(100), nullable=True)  # Component name
    tags = Column(JSON, nullable=True)  # Metric tags
    
    # Timestamps
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    period_start = Column(DateTime, nullable=True)
    period_end = Column(DateTime, nullable=True)
    
    def __repr__(self):
        return f"<SystemMetric(name='{self.metric_name}', value='{self.metric_value}', type='{self.metric_type}')>"


# Export all models for easy importing
__all__ = [
    "ToolRegistry", "ToolPermission", "ToolSession", "ToolExecution",
    "MemoryContext", "ErrorLog", "ToolExecutionLog", "SystemMetric",
    "ToolStatus", "SecurityLevel", "ToolCategory", "PermissionLevel",
    "SessionStatus", "ExecutionStatus", "ErrorSeverity", "MemoryContextType"
]