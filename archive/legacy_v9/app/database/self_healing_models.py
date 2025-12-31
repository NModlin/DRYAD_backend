"""
Database models for Self-Healing System
"""

from sqlalchemy import Column, String, Integer, Text, DateTime, Enum as SQLEnum, JSON
from sqlalchemy.sql import func
import enum
import uuid

from app.database.database import Base


class TaskStatus(str, enum.Enum):
    """Status of self-healing task."""
    PENDING_REVIEW = "pending_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"


class ErrorSeverity(str, enum.Enum):
    """Severity level of detected error."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class SelfHealingTask(Base):
    """
    Self-healing task tracking.
    
    Represents a detected error and the plan to fix it,
    following the GAD (Governed Agentic Development) framework.
    """
    __tablename__ = "self_healing_tasks"
    
    # Primary identification
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Error details
    error_type = Column(String(100), nullable=False, index=True)
    error_message = Column(Text, nullable=False)
    file_path = Column(String(500), nullable=False, index=True)
    line_number = Column(Integer, nullable=False)
    stack_trace = Column(Text, nullable=True)
    severity = Column(SQLEnum(ErrorSeverity), nullable=False, index=True)
    error_hash = Column(String(32), nullable=False, index=True)  # For deduplication
    
    # Task details
    goal = Column(Text, nullable=False)
    plan = Column(JSON, nullable=True)  # Structured fix plan from Architect Agent
    
    # Status tracking
    status = Column(
        SQLEnum(TaskStatus), 
        nullable=False, 
        default=TaskStatus.PENDING_REVIEW,
        index=True
    )
    
    # Review information (GAD human-in-the-loop)
    reviewer = Column(String(255), nullable=True)
    review_comments = Column(Text, nullable=True)
    reviewed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Execution tracking
    execution_log = Column(JSON, nullable=True)  # Logs from Code Agent execution
    test_results = Column(JSON, nullable=True)  # Test validation results
    rollback_info = Column(JSON, nullable=True)  # Rollback details if needed
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Metadata
    metadata_json = Column(JSON, nullable=True)  # Additional metadata
    
    def __repr__(self):
        return f"<SelfHealingTask {self.id}: {self.error_type} - {self.status}>"
    
    def to_dict(self):
        """Convert to dictionary."""
        return {
            "id": self.id,
            "error_type": self.error_type,
            "error_message": self.error_message,
            "file_path": self.file_path,
            "line_number": self.line_number,
            "severity": self.severity.value if self.severity else None,
            "goal": self.goal,
            "plan": self.plan,
            "status": self.status.value if self.status else None,
            "reviewer": self.reviewer,
            "review_comments": self.review_comments,
            "reviewed_at": self.reviewed_at.isoformat() if self.reviewed_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "execution_log": self.execution_log,
            "test_results": self.test_results
        }

