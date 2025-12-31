from datetime import datetime
import uuid
from typing import Optional, List

from sqlalchemy import String, Boolean, DateTime, Integer, Text, JSON, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from dryad.infrastructure.database import Base

class Grove(Base):
    """
    Grove Entity: Represents a Project.
    """
    __tablename__ = "groves"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    is_favorite: Mapped[bool] = mapped_column(Boolean, default=False)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    branches: Mapped[List["Branch"]] = relationship("Branch", back_populates="grove", cascade="all, delete-orphan")


class Branch(Base):
    """
    Branch Entity: Represents a node in the exploration tree.
    """
    __tablename__ = "branches"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(50), default="active") # active, archived, pruned
    
    # Hierarchy
    grove_id: Mapped[str] = mapped_column(String(36), ForeignKey("groves.id", ondelete="CASCADE"), nullable=False)
    parent_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("branches.id", ondelete="SET NULL"), nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    grove: Mapped["Grove"] = relationship("Grove", back_populates="branches")
    parent: Mapped[Optional["Branch"]] = relationship("Branch", remote_side=[id], back_populates="children")
    children: Mapped[List["Branch"]] = relationship("Branch", back_populates="parent", cascade="all, delete-orphan")
    vessel: Mapped[Optional["Vessel"]] = relationship("Vessel", back_populates="branch", uselist=False, cascade="all, delete-orphan")


class Vessel(Base):
    """
    Vessel Entity: Abstract container for storage/context linked to a Branch.
    """
    __tablename__ = "vessels"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # 1:1 Link to Branch
    branch_id: Mapped[str] = mapped_column(String(36), ForeignKey("branches.id", ondelete="CASCADE"), unique=True, nullable=False)
    
    # Content Metadata
    storage_path: Mapped[str] = mapped_column(String(500), nullable=True) # Logical path e.g. /groves/{id}/branches/{id}/
    file_manifest: Mapped[dict] = mapped_column(JSON, default=dict) # {"file.txt": "s3_key_or_path"}
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    branch: Mapped["Branch"] = relationship("Branch", back_populates="vessel")
