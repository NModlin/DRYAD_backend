"""
Structured Logging Database Models

SQLAlchemy models for system-wide structured logging.
"""

from sqlalchemy import (
    Column,
    BigInteger,
    Integer,
    String,
    Text,
    DateTime,
    CheckConstraint,
    Index,
    JSON,
)
from sqlalchemy.sql import func

from app.database.database import Base


class SystemLog(Base):
    """
    System Log model for centralized structured logging.

    Supports distributed tracing, component tracking, and rich metadata
    for observability and Professor agent analysis.

    Performance requirement: >1000 writes/sec
    """

    __tablename__ = "system_logs"

    # Primary key (Integer for SQLite, BIGSERIAL for PostgreSQL)
    log_id = Column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )
    
    # Timestamp
    timestamp = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )
    
    # Log metadata
    level = Column(String(20), nullable=False, index=True)
    component = Column(String(100), nullable=False, index=True)
    event_type = Column(String(100), nullable=False, index=True)
    message = Column(Text, nullable=False)
    log_metadata = Column("metadata", JSON, default={}, nullable=False)
    
    # Distributed tracing
    trace_id = Column(String(255), nullable=True, index=True)
    span_id = Column(String(255), nullable=True)
    
    # Correlation IDs
    agent_id = Column(String(255), nullable=True, index=True)
    task_id = Column(String(255), nullable=True, index=True)
    
    # Constraints
    __table_args__ = (
        CheckConstraint(
            "level IN ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL')",
            name="check_log_level",
        ),
        Index("idx_logs_timestamp", "timestamp"),
        Index("idx_logs_level", "level"),
        Index("idx_logs_component", "component"),
        Index("idx_logs_event_type", "event_type"),
        Index("idx_logs_trace", "trace_id"),
        Index("idx_logs_agent", "agent_id"),
        Index("idx_logs_task", "task_id"),
    )
    
    def __repr__(self) -> str:
        return (
            f"<SystemLog("
            f"level={self.level}, "
            f"component={self.component}, "
            f"event={self.event_type}"
            f")>"
        )

