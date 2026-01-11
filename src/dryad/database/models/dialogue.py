"""
Dialogue Model

SQLAlchemy model for Dialogue entity.
Ported from TypeScript database/entities/Dialogue.ts
"""

from sqlalchemy import Column, String, DateTime, JSON, Text, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from dryad.infrastructure.database import Base
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone


class Dialogue(Base):
    """
    Dialogue Entity
    
    Represents a conversation with an LLM oracle in a specific branch.
    Contains the messages and extracted insights from the consultation.
    """
    
    __tablename__ = "dryad_dialogues"
    
    # Primary key
    id = Column(String, primary_key=True, index=True)
    
    # Foreign key
    branch_id = Column(String, ForeignKey("dryad_branches.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Oracle information
    oracle_used = Column(String, nullable=False)
    
    # Insights extracted from the dialogue
    insights = Column(JSON, nullable=True)
    
    # Storage path for dialogue content
    storage_path = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    branch = relationship("Branch", back_populates="dialogues")
    messages = relationship("DialogueMessage", back_populates="dialogue", cascade="all, delete-orphan", order_by="DialogueMessage.created_at")
    suggestions = relationship("BranchSuggestion", back_populates="dialogue", cascade="all, delete-orphan", foreign_keys="BranchSuggestion.dialogue_id")
    
    def __init__(
        self,
        id: str,
        branch_id: str,
        oracle_used: str,
        insights: Optional[Dict[str, List[str]]] = None,
        storage_path: Optional[str] = None,
        **kwargs
    ):
        self.id = id
        self.branch_id = branch_id
        self.oracle_used = oracle_used
        self.insights = insights or {
            "themes": [],
            "facts": [],
            "decisions": [],
            "questions": []
        }
        self.storage_path = storage_path
        self.created_at = datetime.now(timezone.utc)
        
        # Apply any additional kwargs
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
    
    def add_insight(self, category: str, insight: str) -> None:
        """Add an insight to the dialogue."""
        if self.insights is None:
            self.insights = {"themes": [], "facts": [], "decisions": [], "questions": []}
        
        if category in self.insights:
            if insight not in self.insights[category]:
                self.insights[category].append(insight)
    
    def get_message_count(self) -> int:
        """Get the number of messages in this dialogue."""
        return len(self.messages) if self.messages else 0
    
    def get_latest_message(self) -> Optional["DialogueMessage"]:
        """Get the latest message in the dialogue."""
        if self.messages:
            return max(self.messages, key=lambda m: m.created_at)
        return None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert dialogue to dictionary representation."""
        return {
            "id": self.id,
            "branch_id": self.branch_id,
            "oracle_used": self.oracle_used,
            "insights": self.insights,
            "storage_path": self.storage_path,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "message_count": self.get_message_count(),
            "messages": [msg.to_dict() for msg in self.messages] if self.messages else []
        }
    
    def __repr__(self) -> str:
        return f"<Dialogue(id='{self.id}', branch_id='{self.branch_id}', oracle='{self.oracle_used}')>"
