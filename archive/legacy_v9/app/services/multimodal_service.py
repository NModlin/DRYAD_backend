"""
Multi-Modal Service Layer for Phase 7.

Provides business logic for managing multi-modal content including
storage, retrieval, and processing coordination.
"""

import os
import hashlib
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.database.database import AsyncSessionLocal
from app.database.models import MultiModalContent, Conversation
from app.api.v1.schemas.multimodal import MultiModalContentSummary

logger = logging.getLogger(__name__)


class MultiModalService:
    """
    Service for managing multi-modal content and processing.
    
    Handles storage, retrieval, and lifecycle management of audio, video,
    and image content with associated processing results.
    """
    
    def __init__(self):
        self.storage_base_path = Path("data/multimodal")
        self.storage_base_path.mkdir(parents=True, exist_ok=True)
    
    async def save_multimodal_content(
        self,
        conversation_id: str,
        media_type: str,
        filename: str,
        content_data: bytes,
        processing_result: Optional[Dict[str, Any]] = None
    ) -> MultiModalContent:
        """
        Save multi-modal content to database and optionally to file system.
        
        Args:
            conversation_id: ID of associated conversation
            media_type: Type of media (audio, video, image)
            filename: Original filename
            content_data: Raw content data
            processing_result: Processing results and metadata
            
        Returns:
            Created MultiModalContent instance
        """
        try:
            # Calculate content hash for deduplication
            content_hash = hashlib.sha256(content_data).hexdigest()
            
            # Determine storage path
            storage_path = None
            if len(content_data) > 0:
                # Create storage directory structure
                media_dir = self.storage_base_path / media_type
                media_dir.mkdir(exist_ok=True)
                
                # Use hash-based filename to avoid conflicts
                file_extension = Path(filename).suffix
                storage_filename = f"{content_hash}{file_extension}"
                storage_path = media_dir / storage_filename
                
                # Save file if it doesn't already exist
                if not storage_path.exists():
                    with open(storage_path, 'wb') as f:
                        f.write(content_data)
                    logger.info(f"Saved {media_type} content to {storage_path}")
                else:
                    logger.info(f"Content already exists at {storage_path}")
            
            # Save to database
            async with AsyncSessionLocal() as session:
                content = MultiModalContent(
                    conversation_id=conversation_id,
                    media_type=media_type,
                    filename=filename,
                    file_size=len(content_data),
                    content_hash=content_hash,
                    storage_path=str(storage_path) if storage_path else None,
                    processing_status="completed" if processing_result else "pending",
                    processing_result=processing_result
                )
                
                session.add(content)
                await session.commit()
                await session.refresh(content)
                
                logger.info(f"Saved multimodal content {content.id} for conversation {conversation_id}")
                return content
                
        except Exception as e:
            logger.error(f"Failed to save multimodal content: {e}")
            raise
    
    async def get_multimodal_content(self, content_id: str) -> Optional[MultiModalContent]:
        """
        Retrieve multi-modal content by ID.
        
        Args:
            content_id: ID of the content to retrieve
            
        Returns:
            MultiModalContent instance or None if not found
        """
        try:
            async with AsyncSessionLocal() as session:
                result = await session.execute(
                    select(MultiModalContent).where(MultiModalContent.id == content_id)
                )
                return result.scalar_one_or_none()
                
        except Exception as e:
            logger.error(f"Failed to get multimodal content {content_id}: {e}")
            return None
    
    async def get_conversation_multimodal_content(
        self,
        conversation_id: str,
        media_type: Optional[str] = None
    ) -> List[MultiModalContentSummary]:
        """
        Get all multi-modal content for a conversation.
        
        Args:
            conversation_id: ID of the conversation
            media_type: Optional filter by media type
            
        Returns:
            List of content summaries
        """
        try:
            async with AsyncSessionLocal() as session:
                query = select(MultiModalContent).where(
                    MultiModalContent.conversation_id == conversation_id
                )
                
                if media_type:
                    query = query.where(MultiModalContent.media_type == media_type)
                
                query = query.order_by(MultiModalContent.created_at.desc())
                
                result = await session.execute(query)
                content_items = result.scalars().all()
                
                # Convert to summary format
                summaries = []
                for item in content_items:
                    summaries.append(MultiModalContentSummary(
                        id=item.id,
                        conversation_id=item.conversation_id,
                        media_type=item.media_type,
                        filename=item.filename,
                        file_size=item.file_size,
                        processing_status=item.processing_status,
                        created_at=item.created_at.isoformat()
                    ))
                
                return summaries
                
        except Exception as e:
            logger.error(f"Failed to get conversation multimodal content: {e}")
            return []
    
    async def delete_multimodal_content(self, content_id: str) -> bool:
        """
        Delete multi-modal content by ID.
        
        Args:
            content_id: ID of the content to delete
            
        Returns:
            True if deleted successfully, False otherwise
        """
        try:
            async with AsyncSessionLocal() as session:
                # Get the content first
                result = await session.execute(
                    select(MultiModalContent).where(MultiModalContent.id == content_id)
                )
                content = result.scalar_one_or_none()
                
                if not content:
                    return False
                
                # Delete file from storage if it exists
                if content.storage_path and os.path.exists(content.storage_path):
                    try:
                        os.unlink(content.storage_path)
                        logger.info(f"Deleted file {content.storage_path}")
                    except Exception as e:
                        logger.warning(f"Failed to delete file {content.storage_path}: {e}")
                
                # Delete from database
                await session.delete(content)
                await session.commit()
                
                logger.info(f"Deleted multimodal content {content_id}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to delete multimodal content {content_id}: {e}")
            return False
    
    async def update_processing_status(
        self,
        content_id: str,
        status: str,
        processing_result: Optional[Dict[str, Any]] = None,
        error_message: Optional[str] = None
    ) -> bool:
        """
        Update processing status and results for content.
        
        Args:
            content_id: ID of the content
            status: New processing status
            processing_result: Updated processing results
            error_message: Error message if processing failed
            
        Returns:
            True if updated successfully, False otherwise
        """
        try:
            async with AsyncSessionLocal() as session:
                result = await session.execute(
                    select(MultiModalContent).where(MultiModalContent.id == content_id)
                )
                content = result.scalar_one_or_none()
                
                if not content:
                    return False
                
                # Update fields
                content.processing_status = status
                if processing_result is not None:
                    content.processing_result = processing_result
                if error_message is not None:
                    content.error_message = error_message
                
                await session.commit()
                
                logger.info(f"Updated processing status for content {content_id} to {status}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to update processing status for {content_id}: {e}")
            return False
    
    async def get_content_data(self, content_id: str) -> Optional[bytes]:
        """
        Retrieve raw content data for a content item.
        
        Args:
            content_id: ID of the content
            
        Returns:
            Raw content data or None if not found
        """
        try:
            content = await self.get_multimodal_content(content_id)
            
            if not content or not content.storage_path:
                return None
            
            if not os.path.exists(content.storage_path):
                logger.warning(f"Storage file not found: {content.storage_path}")
                return None
            
            with open(content.storage_path, 'rb') as f:
                return f.read()
                
        except Exception as e:
            logger.error(f"Failed to get content data for {content_id}: {e}")
            return None
    
    async def get_storage_statistics(self) -> Dict[str, Any]:
        """
        Get storage statistics for multi-modal content.
        
        Returns:
            Dictionary with storage statistics
        """
        try:
            async with AsyncSessionLocal() as session:
                # Get total count and size by media type
                result = await session.execute(
                    select(MultiModalContent)
                )
                all_content = result.scalars().all()
                
                stats = {
                    "total_items": len(all_content),
                    "total_size_bytes": sum(item.file_size for item in all_content),
                    "by_media_type": {},
                    "by_status": {},
                    "storage_path": str(self.storage_base_path)
                }
                
                # Group by media type
                for item in all_content:
                    media_type = item.media_type
                    if media_type not in stats["by_media_type"]:
                        stats["by_media_type"][media_type] = {"count": 0, "size_bytes": 0}
                    
                    stats["by_media_type"][media_type]["count"] += 1
                    stats["by_media_type"][media_type]["size_bytes"] += item.file_size
                
                # Group by status
                for item in all_content:
                    status = item.processing_status
                    if status not in stats["by_status"]:
                        stats["by_status"][status] = 0
                    stats["by_status"][status] += 1
                
                return stats
                
        except Exception as e:
            logger.error(f"Failed to get storage statistics: {e}")
            return {
                "error": str(e),
                "total_items": 0,
                "total_size_bytes": 0
            }
    
    async def cleanup_orphaned_files(self) -> Dict[str, Any]:
        """
        Clean up orphaned files that exist in storage but not in database.
        
        Returns:
            Cleanup results
        """
        try:
            # Get all content from database
            async with AsyncSessionLocal() as session:
                result = await session.execute(select(MultiModalContent))
                db_content = result.scalars().all()
                
                db_paths = {item.storage_path for item in db_content if item.storage_path}
            
            # Scan storage directory
            orphaned_files = []
            total_size = 0
            
            for media_type_dir in self.storage_base_path.iterdir():
                if media_type_dir.is_dir():
                    for file_path in media_type_dir.iterdir():
                        if file_path.is_file():
                            file_path_str = str(file_path)
                            if file_path_str not in db_paths:
                                file_size = file_path.stat().st_size
                                orphaned_files.append({
                                    "path": file_path_str,
                                    "size": file_size
                                })
                                total_size += file_size
            
            return {
                "orphaned_files_count": len(orphaned_files),
                "total_orphaned_size": total_size,
                "orphaned_files": orphaned_files
            }
            
        except Exception as e:
            logger.error(f"Failed to cleanup orphaned files: {e}")
            return {"error": str(e)}
