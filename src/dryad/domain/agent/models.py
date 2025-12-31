from datetime import datetime
import uuid
from typing import Optional, Any

from sqlalchemy import String, Boolean, DateTime, Integer, Text, JSON, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from dryad.infrastructure.database import Base

class Agent(Base):
    """
    Agent model defining AI agent configurations.
    """
    __tablename__ = "agents"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    
    # Configuration
    model_provider: Mapped[str] = mapped_column(String(50), default="openai") # openai, anthropic, ollama
    model_name: Mapped[str] = mapped_column(String(100), default="gpt-4o")
    temperature: Mapped[float] = mapped_column(default=0.7)
    
    # Prompting
    system_prompt: Mapped[str] = mapped_column(Text, nullable=False)
    
    # Tools (References via ID list for now, simpler than M2M table for initial phase)
    # Storing as JSON list of Tool IDs ["tool-uuid-1", "tool-uuid-2"]
    tool_ids: Mapped[list[str]] = mapped_column(JSON, default=list)
    
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_by: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"))
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
