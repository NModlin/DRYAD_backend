"""
Database models for Tool Registry System
Part of Prometheus Week 1 Implementation
"""

from sqlalchemy import Column, String, Text, Boolean, Integer, JSON, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

Base = declarative_base()

class ToolRegistry(Base):
    """Tool Registry table for managing AI agent tools"""
    
    __tablename__ = "tool_registry"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False, unique=True)
    description = Column(Text, nullable=True)
    version = Column(String(50), nullable=False, default="1.0.0")
    function_signature = Column(JSON, nullable=False)  # JSON schema for tool parameters
    permissions = Column(JSON, nullable=False, default=dict)  # Access control permissions
    requires_sandbox = Column(Boolean, default=False, nullable=False)
    sandbox_image = Column(String(255), nullable=True)  # Docker image for sandbox
    max_session_duration = Column(Integer, default=300)  # seconds
    stateful = Column(Boolean, default=False, nullable=False)
    active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    permissions_rel = relationship("ToolPermission", back_populates="tool", cascade="all, delete-orphan")
    sessions = relationship("ToolSession", back_populates="tool")
    
    def __repr__(self):
        return f"<ToolRegistry(id='{self.id}', name='{self.name}', version='{self.version}')>"


class ToolPermission(Base):
    """Tool permission system for access control"""
    
    __tablename__ = "tool_permissions"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tool_id = Column(String(36), ForeignKey("tool_registry.id"), nullable=False)
    agent_id = Column(String(36), nullable=True)  # Specific agent or null for all
    user_id = Column(String(36), nullable=True)  # Specific user or null for all
    permission_level = Column(String(50), nullable=False, default="read")  # read, write, execute
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    tool = relationship("ToolRegistry", back_populates="permissions_rel")
    
    def __repr__(self):
        return f"<ToolPermission(tool='{self.tool_id}', agent='{self.agent_id}', level='{self.permission_level}')>"


class ToolSession(Base):
    """Tool execution sessions for stateful tools"""
    
    __tablename__ = "tool_sessions"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tool_id = Column(String(36), ForeignKey("tool_registry.id"), nullable=False)
    agent_id = Column(String(36), nullable=False)
    session_state = Column(JSON, nullable=True)  # Current state of the session
    execution_id = Column(String(36), nullable=True)  # Link to specific execution
    sandbox_id = Column(String(255), nullable=True)  # Docker container ID
    sandbox_status = Column(String(50), nullable=True)  # running, stopped, error
    status = Column(String(50), nullable=False, default="active")  # active, completed, error
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    expires_at = Column(DateTime, nullable=True)  # Session expiration
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    tool = relationship("ToolRegistry", back_populates="sessions")
    executions = relationship("ToolExecution", back_populates="session")
    
    def __repr__(self):
        return f"<ToolSession(tool='{self.tool_id}', agent='{self.agent_id}', status='{self.status}')>"


class ToolExecution(Base):
    """Individual tool execution records"""
    
    __tablename__ = "tool_executions"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String(36), ForeignKey("tool_sessions.id"), nullable=False)
    input_data = Column(JSON, nullable=False)
    output_data = Column(JSON, nullable=True)
    error_message = Column(Text, nullable=True)
    execution_time_ms = Column(Integer, nullable=True)  # Execution duration in milliseconds
    resource_usage = Column(JSON, nullable=True)  # CPU, memory usage
    status = Column(String(50), nullable=False, default="pending")  # pending, running, completed, error
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime, nullable=True)
    
    # Relationships
    session = relationship("ToolSession", back_populates="executions")
    
    def __repr__(self):
        return f"<ToolExecution(session='{self.session_id}', status='{self.status}', time_ms='{self.execution_time_ms}')>"


# Memory Guild Tables for Week 1 Completion
class MemoryContext(Base):
    """Memory context storage for agent memory management"""
    
    __tablename__ = "memory_contexts"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    agent_id = Column(String(36), nullable=False)
    context_data = Column(JSON, nullable=False)
    parent_context_id = Column(String(36), ForeignKey("memory_contexts.id"), nullable=True)  # Context inheritance
    context_type = Column(String(50), nullable=False, default="general")  # general, task, session
    priority = Column(Integer, default=1, nullable=False)  # Context priority
    expires_at = Column(DateTime, nullable=True)  # Optional expiration
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Self-referential relationship for context inheritance
    parent_context = relationship("MemoryContext", remote_side=[id], backref="child_contexts")
    
    def __repr__(self):
        return f"<MemoryContext(agent='{self.agent_id}', type='{self.context_type}', priority='{self.priority}')>"


class ErrorLog(Base):
    """Error logging for Guardian self-healing system"""
    
    __tablename__ = "error_logs"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    error_type = Column(String(255), nullable=False)
    error_message = Column(Text, nullable=False)
    component = Column(String(255), nullable=False)  # Which component failed
    fix_applied = Column(Boolean, default=False, nullable=False)
    fix_details = Column(JSON, nullable=True)  # Details of applied fix
    severity = Column(String(50), nullable=False, default="medium")  # low, medium, high, critical
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    resolved_at = Column(DateTime, nullable=True)
    
    def __repr__(self):
        return f"<ErrorLog(type='{self.error_type}', component='{self.component}', fixed='{self.fix_applied}')>"