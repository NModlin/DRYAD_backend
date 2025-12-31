"""
Vessel Persistence Service

Handles vessel content persistence to disk and database.
Ported from TypeScript core/vessel/vessel-persistence-service.ts
"""

import os
import json
import shutil
import gzip
from typing import Dict, Any, Optional
from pathlib import Path
from datetime import datetime, timezone

from app.dryad.models.vessel import Vessel
from app.dryad.core.vessel_generator import VesselContent
from app.dryad.core.errors import DryadError, DryadErrorCode
from app.core.logging_config import get_logger

logger = get_logger(__name__)


class VesselPersistenceService:
    """Handles vessel content persistence operations."""
    
    def __init__(self, storage_base_path: str = "./data/vessels"):
        self.storage_base_path = Path(storage_base_path)
        self.storage_base_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"VesselPersistenceService initialized with storage path: {self.storage_base_path}")
    
    async def load_vessel_content(self, vessel: Vessel) -> VesselContent:
        """
        Load vessel content from disk.
        
        Args:
            vessel: The vessel to load content for
            
        Returns:
            Loaded vessel content
        """
        try:
            logger.debug(f"Loading vessel content for {vessel.id}")
            
            storage_path = Path(vessel.storage_path)
            
            if not storage_path.exists():
                logger.warning(f"Vessel content file not found: {storage_path}")
                # Return default content if file doesn't exist
                return self._create_default_content(vessel)
            
            # Handle compressed files
            if vessel.is_compressed and vessel.compressed_path:
                return await self._load_compressed_content(vessel.compressed_path)
            
            # Load regular content
            with open(storage_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            content = VesselContent.from_dict(data)
            
            # Update last accessed timestamp
            vessel.update_last_accessed()
            
            logger.debug(f"Vessel content loaded successfully for {vessel.id}")
            return content
            
        except Exception as e:
            logger.error(f"Failed to load vessel content for {vessel.id}: {e}")
            raise DryadError(
                DryadErrorCode.VESSEL_LOAD_FAILED,
                f"Failed to load vessel content: {str(e)}",
                {"vessel_id": vessel.id, "storage_path": vessel.storage_path}
            )
    
    async def save_vessel_content(self, vessel: Vessel, content: VesselContent) -> None:
        """
        Save vessel content to disk.
        
        Args:
            vessel: The vessel to save content for
            content: The content to save
        """
        try:
            logger.debug(f"Saving vessel content for {vessel.id}")
            
            storage_path = Path(vessel.storage_path)
            storage_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Add timestamp to content metadata
            if not content.metadata:
                content.metadata = {}
            content.metadata["last_saved"] = datetime.now(timezone.utc).isoformat()
            
            # Save content to disk
            with open(storage_path, 'w', encoding='utf-8') as f:
                json.dump(content.to_dict(), f, indent=2, ensure_ascii=False)
            
            # Update vessel metadata
            vessel.update_last_updated()
            vessel.content_hash = self._calculate_content_hash(content)
            
            logger.debug(f"Vessel content saved successfully for {vessel.id}")
            
        except Exception as e:
            logger.error(f"Failed to save vessel content for {vessel.id}: {e}")
            raise DryadError(
                DryadErrorCode.VESSEL_SAVE_FAILED,
                f"Failed to save vessel content: {str(e)}",
                {"vessel_id": vessel.id, "storage_path": vessel.storage_path}
            )
    
    async def compress_vessel(self, vessel: Vessel) -> None:
        """
        Compress vessel content to save disk space.
        
        Args:
            vessel: The vessel to compress
        """
        try:
            logger.debug(f"Compressing vessel {vessel.id}")
            
            if vessel.is_compressed:
                logger.warning(f"Vessel {vessel.id} is already compressed")
                return
            
            storage_path = Path(vessel.storage_path)
            if not storage_path.exists():
                raise DryadError(
                    DryadErrorCode.VESSEL_NOT_FOUND,
                    f"Vessel content file not found: {storage_path}",
                    {"vessel_id": vessel.id}
                )
            
            # Create compressed file path
            compressed_path = storage_path.with_suffix('.json.gz')
            
            # Compress the file
            with open(storage_path, 'rb') as f_in:
                with gzip.open(compressed_path, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            
            # Update vessel metadata
            vessel.is_compressed = True
            vessel.compressed_path = str(compressed_path)
            vessel.update_last_updated()
            
            # Remove original file
            storage_path.unlink()
            
            logger.info(f"Vessel {vessel.id} compressed successfully")
            
        except Exception as e:
            logger.error(f"Failed to compress vessel {vessel.id}: {e}")
            raise DryadError(
                DryadErrorCode.VESSEL_UPDATE_FAILED,
                f"Failed to compress vessel: {str(e)}",
                {"vessel_id": vessel.id}
            )
    
    async def decompress_vessel(self, vessel: Vessel) -> None:
        """
        Decompress vessel content.
        
        Args:
            vessel: The vessel to decompress
        """
        try:
            logger.debug(f"Decompressing vessel {vessel.id}")
            
            if not vessel.is_compressed or not vessel.compressed_path:
                logger.warning(f"Vessel {vessel.id} is not compressed")
                return
            
            compressed_path = Path(vessel.compressed_path)
            if not compressed_path.exists():
                raise DryadError(
                    DryadErrorCode.VESSEL_NOT_FOUND,
                    f"Compressed vessel file not found: {compressed_path}",
                    {"vessel_id": vessel.id}
                )
            
            storage_path = Path(vessel.storage_path)
            
            # Decompress the file
            with gzip.open(compressed_path, 'rb') as f_in:
                with open(storage_path, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            
            # Update vessel metadata
            vessel.is_compressed = False
            vessel.compressed_path = None
            vessel.update_last_updated()
            
            # Remove compressed file
            compressed_path.unlink()
            
            logger.info(f"Vessel {vessel.id} decompressed successfully")
            
        except Exception as e:
            logger.error(f"Failed to decompress vessel {vessel.id}: {e}")
            raise DryadError(
                DryadErrorCode.VESSEL_UPDATE_FAILED,
                f"Failed to decompress vessel: {str(e)}",
                {"vessel_id": vessel.id}
            )
    
    async def _load_compressed_content(self, compressed_path: str) -> VesselContent:
        """Load content from compressed file."""
        with gzip.open(compressed_path, 'rt', encoding='utf-8') as f:
            data = json.load(f)
        return VesselContent.from_dict(data)
    
    def _create_default_content(self, vessel: Vessel) -> VesselContent:
        """Create default content for a vessel."""
        return VesselContent(
            metadata={
                "name": f"Vessel {vessel.id[:8]}",
                "status": vessel.status,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "branch_id": vessel.branch_id
            },
            summary="Default vessel content",
            base_context="",
            branch_context="",
            inherited_context="",
            dialogues=[]
        )
    
    def _calculate_content_hash(self, content: VesselContent) -> str:
        """Calculate hash of vessel content."""
        import hashlib
        content_str = json.dumps(content.to_dict(), sort_keys=True)
        return hashlib.sha256(content_str.encode('utf-8')).hexdigest()
