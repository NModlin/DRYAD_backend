# app/services/document_versioning_service.py
import logging
import json
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, and_
from datetime import datetime

from app.database.models import Document, DocumentVersion, DocumentChangeLog

logger = logging.getLogger(__name__)

class DocumentVersioningService:
    """Service for document version control and change tracking."""
    
    @staticmethod
    async def create_version(
        db: AsyncSession,
        document: Document,
        change_summary: Optional[str] = None,
        change_type: str = "update",
        created_by: Optional[str] = None,
        created_by_session: Optional[str] = None
    ) -> DocumentVersion:
        """Create a new version of a document."""
        try:
            # Get the next version number
            latest_version = await db.execute(
                select(func.max(DocumentVersion.version_number))
                .where(DocumentVersion.document_id == document.id)
            )
            max_version = latest_version.scalar() or 0
            new_version_number = max_version + 1
            
            # Mark all existing versions as not current
            await db.execute(
                DocumentVersion.__table__.update()
                .where(DocumentVersion.document_id == document.id)
                .values(is_current=False)
            )
            
            # Create new version
            new_version = DocumentVersion(
                document_id=document.id,
                version_number=new_version_number,
                title=document.title,
                content=document.content,
                content_type=document.content_type,
                file_size=document.file_size,
                doc_metadata=document.doc_metadata,
                tags=document.tags,
                change_summary=change_summary or f"Version {new_version_number}",
                change_type=change_type,
                is_current=True,
                created_by=created_by,
                created_by_session=created_by_session
            )
            
            db.add(new_version)
            await db.commit()
            await db.refresh(new_version)
            
            logger.info(f"Created version {new_version_number} for document {document.id}")
            return new_version
            
        except Exception as e:
            logger.error(f"Failed to create document version: {e}")
            await db.rollback()
            raise
    
    @staticmethod
    async def update_document_with_versioning(
        db: AsyncSession,
        document_id: str,
        updates: Dict[str, Any],
        change_summary: Optional[str] = None,
        created_by: Optional[str] = None,
        created_by_session: Optional[str] = None
    ) -> Tuple[Document, DocumentVersion]:
        """Update a document and create a new version with change tracking."""
        try:
            # Get current document
            document = await db.get(Document, document_id)
            if not document:
                raise ValueError(f"Document {document_id} not found")
            
            # Track changes
            changes = await DocumentVersioningService._track_changes(document, updates)
            
            # Apply updates to document
            for field, value in updates.items():
                if hasattr(document, field):
                    setattr(document, field, value)
            
            # Create new version
            new_version = await DocumentVersioningService.create_version(
                db=db,
                document=document,
                change_summary=change_summary,
                change_type="update",
                created_by=created_by,
                created_by_session=created_by_session
            )
            
            # Log detailed changes
            await DocumentVersioningService._log_changes(
                db=db,
                document_id=document_id,
                version_id=new_version.id,
                changes=changes
            )
            
            # Update version with changed fields
            new_version.changed_fields = list(changes.keys())
            await db.commit()
            
            logger.info(f"Updated document {document_id} with versioning")
            return document, new_version
            
        except Exception as e:
            logger.error(f"Failed to update document with versioning: {e}")
            await db.rollback()
            raise
    
    @staticmethod
    async def get_document_versions(
        db: AsyncSession,
        document_id: str,
        limit: int = 50
    ) -> List[DocumentVersion]:
        """Get all versions of a document."""
        try:
            result = await db.execute(
                select(DocumentVersion)
                .where(DocumentVersion.document_id == document_id)
                .order_by(desc(DocumentVersion.version_number))
                .limit(limit)
            )
            
            return result.scalars().all()
            
        except Exception as e:
            logger.error(f"Failed to get document versions: {e}")
            return []
    
    @staticmethod
    async def get_version_by_number(
        db: AsyncSession,
        document_id: str,
        version_number: int
    ) -> Optional[DocumentVersion]:
        """Get a specific version of a document."""
        try:
            result = await db.execute(
                select(DocumentVersion)
                .where(
                    and_(
                        DocumentVersion.document_id == document_id,
                        DocumentVersion.version_number == version_number
                    )
                )
            )
            
            return result.scalar_one_or_none()
            
        except Exception as e:
            logger.error(f"Failed to get document version: {e}")
            return None
    
    @staticmethod
    async def rollback_to_version(
        db: AsyncSession,
        document_id: str,
        target_version_number: int,
        created_by: Optional[str] = None,
        created_by_session: Optional[str] = None
    ) -> Tuple[Document, DocumentVersion]:
        """Rollback a document to a specific version."""
        try:
            # Get current document
            document = await db.get(Document, document_id)
            if not document:
                raise ValueError(f"Document {document_id} not found")
            
            # Get target version
            target_version = await DocumentVersioningService.get_version_by_number(
                db=db,
                document_id=document_id,
                version_number=target_version_number
            )
            
            if not target_version:
                raise ValueError(f"Version {target_version_number} not found")
            
            # Apply target version data to document
            document.title = target_version.title
            document.content = target_version.content
            document.content_type = target_version.content_type
            document.file_size = target_version.file_size
            document.doc_metadata = target_version.doc_metadata
            document.tags = target_version.tags
            
            # Create rollback version
            rollback_version = await DocumentVersioningService.create_version(
                db=db,
                document=document,
                change_summary=f"Rollback to version {target_version_number}",
                change_type="rollback",
                created_by=created_by,
                created_by_session=created_by_session
            )
            
            # Set parent version reference
            rollback_version.parent_version_id = target_version.id
            await db.commit()
            
            logger.info(f"Rolled back document {document_id} to version {target_version_number}")
            return document, rollback_version
            
        except Exception as e:
            logger.error(f"Failed to rollback document: {e}")
            await db.rollback()
            raise
    
    @staticmethod
    async def compare_versions(
        db: AsyncSession,
        document_id: str,
        version1_number: int,
        version2_number: int
    ) -> Dict[str, Any]:
        """Compare two versions of a document."""
        try:
            version1 = await DocumentVersioningService.get_version_by_number(
                db=db, document_id=document_id, version_number=version1_number
            )
            version2 = await DocumentVersioningService.get_version_by_number(
                db=db, document_id=document_id, version_number=version2_number
            )
            
            if not version1 or not version2:
                raise ValueError("One or both versions not found")
            
            # Compare fields
            comparison = {
                "document_id": document_id,
                "version1": {
                    "number": version1.version_number,
                    "created_at": version1.created_at.isoformat() if version1.created_at else None,
                    "change_summary": version1.change_summary
                },
                "version2": {
                    "number": version2.version_number,
                    "created_at": version2.created_at.isoformat() if version2.created_at else None,
                    "change_summary": version2.change_summary
                },
                "differences": {}
            }
            
            # Compare each field
            fields_to_compare = ["title", "content", "content_type", "file_size", "doc_metadata", "tags"]
            
            for field in fields_to_compare:
                val1 = getattr(version1, field)
                val2 = getattr(version2, field)
                
                if val1 != val2:
                    comparison["differences"][field] = {
                        f"version_{version1_number}": val1,
                        f"version_{version2_number}": val2,
                        "changed": True
                    }
                else:
                    comparison["differences"][field] = {
                        "value": val1,
                        "changed": False
                    }
            
            return comparison
            
        except Exception as e:
            logger.error(f"Failed to compare versions: {e}")
            raise
    
    @staticmethod
    async def get_change_history(
        db: AsyncSession,
        document_id: str,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get detailed change history for a document."""
        try:
            result = await db.execute(
                select(DocumentChangeLog)
                .where(DocumentChangeLog.document_id == document_id)
                .order_by(desc(DocumentChangeLog.created_at))
                .limit(limit)
            )
            
            change_logs = result.scalars().all()
            
            history = []
            for log in change_logs:
                history.append({
                    "id": log.id,
                    "version_id": log.version_id,
                    "field_name": log.field_name,
                    "old_value": log.old_value,
                    "new_value": log.new_value,
                    "change_type": log.change_type,
                    "value_type": log.value_type,
                    "is_truncated": log.is_truncated,
                    "created_at": log.created_at.isoformat() if log.created_at else None
                })
            
            return history
            
        except Exception as e:
            logger.error(f"Failed to get change history: {e}")
            return []
    
    @staticmethod
    async def _track_changes(document: Document, updates: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
        """Track changes between current document and updates."""
        changes = {}
        
        for field, new_value in updates.items():
            if hasattr(document, field):
                old_value = getattr(document, field)
                if old_value != new_value:
                    changes[field] = {
                        "old_value": old_value,
                        "new_value": new_value,
                        "change_type": "modified"
                    }
        
        return changes
    
    @staticmethod
    async def _log_changes(
        db: AsyncSession,
        document_id: str,
        version_id: str,
        changes: Dict[str, Dict[str, Any]]
    ):
        """Log detailed changes to the change log table."""
        try:
            for field_name, change_data in changes.items():
                old_value = change_data["old_value"]
                new_value = change_data["new_value"]
                
                # Truncate long values
                old_value_str = str(old_value) if old_value is not None else None
                new_value_str = str(new_value) if new_value is not None else None
                
                is_truncated = False
                if old_value_str and len(old_value_str) > 1000:
                    old_value_str = old_value_str[:1000] + "..."
                    is_truncated = True
                
                if new_value_str and len(new_value_str) > 1000:
                    new_value_str = new_value_str[:1000] + "..."
                    is_truncated = True
                
                # Determine value type
                value_type = "string"
                if isinstance(new_value, dict) or isinstance(new_value, list):
                    value_type = "json"
                elif isinstance(new_value, (int, float)):
                    value_type = "number"
                elif isinstance(new_value, bool):
                    value_type = "boolean"
                
                change_log = DocumentChangeLog(
                    document_id=document_id,
                    version_id=version_id,
                    field_name=field_name,
                    old_value=old_value_str,
                    new_value=new_value_str,
                    change_type=change_data["change_type"],
                    value_type=value_type,
                    is_truncated=is_truncated
                )
                
                db.add(change_log)
            
            await db.commit()
            
        except Exception as e:
            logger.error(f"Failed to log changes: {e}")
            await db.rollback()
