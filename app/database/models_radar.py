"""
RADAR Integration Database Models

SQLAlchemy models for RADAR-specific data (feedback, sync status, etc.)
"""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime, Boolean, Float, JSON, ForeignKey, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.database import Base


class RADARFeedback(Base):
    """Model for storing user feedback from RADAR."""
    __tablename__ = "radar_feedback"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    message_id = Column(String, ForeignKey("messages.id"), nullable=False, index=True)
    conversation_id = Column(String, ForeignKey("conversations.id"), nullable=True, index=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=True, index=True)
    
    # Feedback data
    rating = Column(String(20), nullable=False)  # 'positive' or 'negative'
    comment = Column(Text, nullable=True)
    
    # RADAR context
    radar_user_id = Column(String, nullable=True)
    radar_username = Column(String, nullable=True)
    radar_context = Column(JSON, nullable=True)  # Full RADAR context at time of feedback
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    message = relationship("Message", foreign_keys=[message_id])
    conversation = relationship("Conversation", foreign_keys=[conversation_id])
    user = relationship("User", foreign_keys=[user_id])
    
    # Indexes for efficient queries
    __table_args__ = (
        Index('idx_radar_feedback_rating', 'rating'),
        Index('idx_radar_feedback_created', 'created_at'),
        Index('idx_radar_feedback_user', 'radar_user_id'),
    )

    def __repr__(self):
        return f"<RADARFeedback(id={self.id}, message_id={self.message_id}, rating={self.rating})>"


class RADARSyncStatus(Base):
    """Model for tracking sync status between RADAR and Dryad.AI."""
    __tablename__ = "radar_sync_status"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Entity information
    entity_type = Column(String(50), nullable=False, index=True)  # 'user', 'conversation', 'document'
    entity_id = Column(String, nullable=False, index=True)
    
    # Sync status
    sync_status = Column(String(20), nullable=False, default='pending')  # 'pending', 'synced', 'failed'
    last_sync_at = Column(DateTime(timezone=True), nullable=True)
    sync_attempts = Column(Float, default=0)
    
    # Error tracking
    last_error = Column(Text, nullable=True)
    error_count = Column(Float, default=0)
    
    # Metadata
    radar_metadata = Column(JSON, nullable=True)
    dryad_metadata = Column(JSON, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Indexes for efficient queries
    __table_args__ = (
        Index('idx_radar_sync_entity', 'entity_type', 'entity_id'),
        Index('idx_radar_sync_status', 'sync_status'),
        Index('idx_radar_sync_updated', 'updated_at'),
    )

    def __repr__(self):
        return f"<RADARSyncStatus(entity_type={self.entity_type}, entity_id={self.entity_id}, status={self.sync_status})>"


class RADARContextLog(Base):
    """Model for logging RADAR context data for analytics and debugging."""
    __tablename__ = "radar_context_logs"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    conversation_id = Column(String, ForeignKey("conversations.id"), nullable=True, index=True)
    message_id = Column(String, ForeignKey("messages.id"), nullable=True, index=True)
    
    # RADAR context data
    radar_user_id = Column(String, nullable=True, index=True)
    radar_username = Column(String, nullable=True)
    department = Column(String, nullable=True)
    
    # Full context snapshot
    user_context = Column(JSON, nullable=True)
    session_context = Column(JSON, nullable=True)
    environment_context = Column(JSON, nullable=True)
    recent_actions = Column(JSON, nullable=True)
    
    # Request metadata
    request_path = Column(String, nullable=True)
    request_method = Column(String, nullable=True)
    response_time_ms = Column(Float, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    conversation = relationship("Conversation", foreign_keys=[conversation_id])
    message = relationship("Message", foreign_keys=[message_id])
    
    # Indexes for analytics
    __table_args__ = (
        Index('idx_radar_context_user', 'radar_user_id'),
        Index('idx_radar_context_created', 'created_at'),
        Index('idx_radar_context_dept', 'department'),
    )

    def __repr__(self):
        return f"<RADARContextLog(id={self.id}, radar_user={self.radar_username})>"

