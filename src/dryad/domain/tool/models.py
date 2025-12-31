from datetime import datetime
import uuid
from typing import Optional, Any

from sqlalchemy import String, Boolean, DateTime, Integer, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from dryad.infrastructure.database import Base

class Tool(Base):
    """
    Tool Registry model defining available AI tools.
    """
    __tablename__ = "tools"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    version: Mapped[str] = mapped_column(String(50), default="1.0.0")
    
    # Classification
    category: Mapped[str] = mapped_column(String(100), default="general")
    security_level: Mapped[str] = mapped_column(String(50), default="standard") # safe, standard, critical
    
    # Execution Config
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    requires_sandbox: Mapped[bool] = mapped_column(Boolean, default=False)
    sandbox_image: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # Schemas (JSON)
    input_schema: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    output_schema: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON, nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
