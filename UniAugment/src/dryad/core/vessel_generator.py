"""
Vessel Generator

Core vessel generation and management functionality.
Ported from TypeScript core/vessel/vessel-generator.ts
"""

import os
import json
import hashlib
import uuid
from typing import Dict, Any, Optional
from datetime import datetime, timezone
from pathlib import Path

from app.dryad.models.vessel import Vessel
from app.dryad.models.branch import Branch
from app.dryad.core.errors import DryadError, DryadErrorCode
from app.core.logging_config import get_logger

logger = get_logger(__name__)


class VesselContent:
    """Represents the content structure of a vessel."""
    
    def __init__(
        self,
        metadata: Optional[Dict[str, Any]] = None,
        summary: str = "",
        base_context: str = "",
        branch_context: str = "",
        inherited_context: str = "",
        dialogues: Optional[list] = None
    ):
        self.metadata = metadata or {}
        self.summary = summary
        self.base_context = base_context
        self.branch_context = branch_context
        self.inherited_context = inherited_context
        self.dialogues = dialogues or []
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "metadata": self.metadata,
            "summary": self.summary,
            "base_context": self.base_context,
            "branch_context": self.branch_context,
            "inherited_context": self.inherited_context,
            "dialogues": self.dialogues
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "VesselContent":
        """Create from dictionary representation."""
        return cls(
            metadata=data.get("metadata", {}),
            summary=data.get("summary", ""),
            base_context=data.get("base_context", ""),
            branch_context=data.get("branch_context", ""),
            inherited_context=data.get("inherited_context", ""),
            dialogues=data.get("dialogues", [])
        )


class VesselCreationOptions:
    """Options for vessel creation."""
    
    def __init__(
        self,
        parent_branch_id: Optional[str] = None,
        initial_content: Optional[Dict[str, Any]] = None,
        storage_base_path: Optional[str] = None
    ):
        self.parent_branch_id = parent_branch_id
        self.initial_content = initial_content or {}
        self.storage_base_path = storage_base_path or "./data/vessels"


class VesselGenerator:
    """Generates and manages vessel content and storage."""
    
    def __init__(self, storage_base_path: str = "./data/vessels"):
        self.storage_base_path = Path(storage_base_path)
        self.storage_base_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"VesselGenerator initialized with storage path: {self.storage_base_path}")
    
    async def create_vessel(
        self,
        branch_id: str,
        options: Optional[VesselCreationOptions] = None
    ) -> Vessel:
        """Create a new vessel for a branch."""
        try:
            options = options or VesselCreationOptions()
            vessel_id = str(uuid.uuid4())
            
            logger.debug(f"Creating vessel for branch {branch_id}")
            
            # Create initial content
            content = VesselContent(
                metadata={
                    "name": f"Vessel for Branch {branch_id[:8]}",
                    "status": "active",
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "branch_id": branch_id
                },
                summary="New vessel created",
                base_context=options.initial_content.get("base_context", ""),
                branch_context="",
                inherited_context="",
                dialogues=[]
            )
            
            # Generate storage path
            storage_path = self._generate_storage_path(vessel_id)
            
            # Save content to disk
            await self._save_content_to_disk(storage_path, content)
            
            # Calculate content hash
            content_hash = self._calculate_content_hash(content)
            
            # Create vessel entity
            vessel = Vessel(
                id=vessel_id,
                branch_id=branch_id,
                storage_path=str(storage_path),
                content_hash=content_hash,
                file_references={"content": str(storage_path)},
                is_compressed=False,
                status="active"
            )
            
            logger.info(f"Vessel created successfully: {vessel_id}")
            return vessel
            
        except Exception as e:
            logger.error(f"Failed to create vessel for branch {branch_id}: {e}")
            raise DryadError(
                DryadErrorCode.VESSEL_CREATE_FAILED,
                f"Failed to create vessel: {str(e)}",
                {"branch_id": branch_id}
            )
    
    async def get_vessel_content(self, vessel_id: str) -> VesselContent:
        """Get vessel content by vessel ID."""
        try:
            # This would typically load from database and then from disk
            # For now, we'll implement a basic version
            storage_path = self._generate_storage_path(vessel_id)
            
            if not storage_path.exists():
                raise DryadError(
                    DryadErrorCode.VESSEL_NOT_FOUND,
                    f"Vessel content not found: {vessel_id}",
                    {"vessel_id": vessel_id}
                )
            
            with open(storage_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            return VesselContent.from_dict(data)
            
        except Exception as e:
            logger.error(f"Failed to get vessel content {vessel_id}: {e}")
            raise DryadError(
                DryadErrorCode.VESSEL_LOAD_FAILED,
                f"Failed to load vessel content: {str(e)}",
                {"vessel_id": vessel_id}
            )
    
    def _generate_storage_path(self, vessel_id: str) -> Path:
        """Generate storage path for a vessel."""
        # Create subdirectories based on vessel ID for better organization
        subdir = vessel_id[:2]
        vessel_dir = self.storage_base_path / subdir
        vessel_dir.mkdir(parents=True, exist_ok=True)
        return vessel_dir / f"{vessel_id}.json"
    
    async def _save_content_to_disk(self, storage_path: Path, content: VesselContent) -> None:
        """Save vessel content to disk."""
        try:
            with open(storage_path, 'w', encoding='utf-8') as f:
                json.dump(content.to_dict(), f, indent=2, ensure_ascii=False)
        except Exception as e:
            raise DryadError(
                DryadErrorCode.VESSEL_SAVE_FAILED,
                f"Failed to save vessel content: {str(e)}",
                {"storage_path": str(storage_path)}
            )
    
    def _calculate_content_hash(self, content: VesselContent) -> str:
        """Calculate hash of vessel content."""
        content_str = json.dumps(content.to_dict(), sort_keys=True)
        return hashlib.sha256(content_str.encode('utf-8')).hexdigest()
