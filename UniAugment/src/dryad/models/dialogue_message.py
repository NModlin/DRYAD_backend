"""
Dialogue Message Model

SQLAlchemy model for DialogueMessage entity.
Ported from TypeScript database/entities/DialogueMessage.ts
"""

from sqlalchemy import Column, String, DateTime, Text, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.database import Base
from enum import Enum
from typing import Dict, Any, Optional
from datetime import datetime


class MessageRole(str, Enum):
    """Message role enumeration."""
    HUMAN = "human"
    ORACLE = "oracle"
    SYSTEM = "system"


class DialogueMessage(Base):
    """
    Dialogue Message Entity
    
    Represents a single message in a dialogue between human and oracle.
    """
    
    __tablename__ = "dryad_dialogue_messages"
    
    # Primary key
    id = Column(String, primary_key=True, index=True)
    
    # Foreign key
    dialogue_id = Column(String, ForeignKey("dryad_dialogues.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Message content
    role = Column(SQLEnum(MessageRole), nullable=False)
    content = Column(Text, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    dialogue = relationship("Dialogue", back_populates="messages")
    
    def __init__(
        self,
        id: str,
        dialogue_id: str,
        role: MessageRole,
        content: str,
        **kwargs
    ):
        self.id = id
        self.dialogue_id = dialogue_id
        self.role = role
        self.content = content
        self.created_at = datetime.utcnow()
        
        # Apply any additional kwargs
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
    
    def is_human_message(self) -> bool:
        """Check if this is a human message."""
        return self.role == MessageRole.HUMAN
    
    def is_oracle_message(self) -> bool:
        """Check if this is an oracle message."""
        return self.role == MessageRole.ORACLE
    
    def is_system_message(self) -> bool:
        """Check if this is a system message."""
        return self.role == MessageRole.SYSTEM
    
    def get_content_preview(self, max_length: int = 100) -> str:
        """Get a preview of the message content."""
        if len(self.content) <= max_length:
            return self.content
        return self.content[:max_length] + "..."
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary representation."""
        return {
            "id": self.id,
            "dialogue_id": self.dialogue_id,
            "role": self.role.value,
            "content": self.content,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "content_preview": self.get_content_preview()
        }
    
    def __repr__(self) -> str:
        preview = self.get_content_preview(50)
        return f"<DialogueMessage(id='{self.id}', role='{self.role.value}', content='{preview}')>"
