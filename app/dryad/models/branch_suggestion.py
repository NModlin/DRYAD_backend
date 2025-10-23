"""
Branch Suggestion Model

SQLAlchemy model for AI-powered branch suggestions.
"""

from sqlalchemy import Column, String, DateTime, Float, Integer, Boolean, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.database import Base
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone


class BranchSuggestion(Base):
    """
    Branch Suggestion Entity
    
    Represents an AI-generated suggestion for creating a new branch
    based on oracle wisdom (themes, questions, decisions, facts).
    """
    
    __tablename__ = "dryad_branch_suggestions"
    
    # Primary key
    id = Column(String, primary_key=True, index=True)
    
    # Foreign keys
    dialogue_id = Column(String, ForeignKey("dryad_dialogues.id", ondelete="CASCADE"), nullable=False, index=True)
    branch_id = Column(String, ForeignKey("dryad_branches.id", ondelete="CASCADE"), nullable=False, index=True)
    created_branch_id = Column(String, ForeignKey("dryad_branches.id", ondelete="SET NULL"), nullable=True, index=True)
    
    # Suggestion details
    suggestion_type = Column(String(50), nullable=False, index=True)  # theme, question, decision, fact, insight
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    source_text = Column(Text, nullable=False)
    
    # Scoring and priority
    priority_score = Column(Float, nullable=False, index=True)  # 0-100
    priority_level = Column(String(50), nullable=False, index=True)  # critical, high, medium, low
    relevance_score = Column(Float, nullable=False)  # 0-1
    confidence = Column(Float, nullable=False)  # 0-1
    estimated_depth = Column(Integer, nullable=False, default=1)
    
    # Keywords and metadata
    keywords = Column(JSON, nullable=True)  # List of extracted keywords
    extra_metadata = Column(JSON, nullable=True)  # Additional metadata
    
    # Status
    is_auto_created = Column(Boolean, nullable=False, default=False, index=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    dialogue = relationship("Dialogue", foreign_keys=[dialogue_id], back_populates="suggestions")
    parent_branch = relationship("Branch", foreign_keys=[branch_id], back_populates="suggestions")
    created_branch = relationship("Branch", foreign_keys=[created_branch_id], back_populates="source_suggestion")
    
    def __init__(
        self,
        id: str,
        dialogue_id: str,
        branch_id: str,
        suggestion_type: str,
        title: str,
        description: str,
        source_text: str,
        priority_score: float,
        priority_level: str,
        relevance_score: float,
        confidence: float,
        estimated_depth: int = 1,
        keywords: Optional[List[str]] = None,
        extra_metadata: Optional[Dict[str, Any]] = None,
        is_auto_created: bool = False,
        created_branch_id: Optional[str] = None,
        **kwargs
    ):
        self.id = id
        self.dialogue_id = dialogue_id
        self.branch_id = branch_id
        self.suggestion_type = suggestion_type
        self.title = title.strip()
        self.description = description
        self.source_text = source_text
        self.priority_score = priority_score
        self.priority_level = priority_level
        self.relevance_score = relevance_score
        self.confidence = confidence
        self.estimated_depth = estimated_depth
        self.keywords = keywords or []
        self.extra_metadata = extra_metadata or {}
        self.is_auto_created = is_auto_created
        self.created_branch_id = created_branch_id
        self.created_at = datetime.now(timezone.utc)
        self.updated_at = datetime.now(timezone.utc)
        
        # Apply any additional kwargs
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "id": self.id,
            "dialogue_id": self.dialogue_id,
            "branch_id": self.branch_id,
            "created_branch_id": self.created_branch_id,
            "suggestion_type": self.suggestion_type,
            "title": self.title,
            "description": self.description,
            "source_text": self.source_text,
            "priority_score": self.priority_score,
            "priority_level": self.priority_level,
            "relevance_score": self.relevance_score,
            "confidence": self.confidence,
            "estimated_depth": self.estimated_depth,
            "keywords": self.keywords,
            "metadata": self.extra_metadata,
            "is_auto_created": self.is_auto_created,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }

