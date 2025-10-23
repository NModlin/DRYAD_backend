"""
Import Service for Dryad

Handles importing Dryad knowledge structures from various formats (JSON, YAML, Markdown).
"""

import json
import yaml
import uuid
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.dryad.models import (
    Grove, Branch, Vessel, Dialogue, DialogueMessage,
    ObservationPoint, Possibility, BranchSuggestion,
    BranchStatus, BranchPriority, MessageRole
)

logger = logging.getLogger(__name__)
from app.dryad.schemas.export_schemas import (
    ImportRequest, ImportResponse, ImportValidationResult, ImportStats,
    ImportOptions, ImportStrategy, ExportFormat,
    ExportedGrove, ExportedBranch, ExportedVessel, ExportedDialogue,
    ExportedDialogueMessage, ExportedObservationPoint, ExportedPossibility,
    ExportedBranchSuggestion
)
from app.dryad.core.errors import NotFoundError, DryadError, DryadErrorCode


class ImportService:
    """Service for importing Dryad knowledge structures."""

    SUPPORTED_VERSIONS = ["1.0.0"]

    def __init__(self, db: AsyncSession):
        """
        Initialize import service.

        Args:
            db: Database session
        """
        self.db = db
        self.stats = ImportStats()
        self.errors = []
        self.warnings = []
    
    async def import_grove(self, request: ImportRequest, user_id: str) -> ImportResponse:
        """
        Import a grove from specified format.
        
        Args:
            request: Import request
            user_id: User ID
            
        Returns:
            Import response with statistics
        """
        start_time = datetime.utcnow()
        self.stats = ImportStats()
        self.errors = []
        self.warnings = []
        
        try:
            logger.info(f"Importing grove for user {user_id}")
            
            # Load import data
            import_data = await self._load_import_data(request)
            
            # Validate import data
            validation = await self._validate_import_data(import_data, request.options)
            
            if request.options.validate_only:
                import_time_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
                return ImportResponse(
                    success=validation.is_valid,
                    validation=validation,
                    stats=self.stats,
                    grove_id=None,
                    import_time_ms=import_time_ms,
                    errors=validation.errors,
                    warnings=validation.warnings
                )
            
            if not validation.is_valid and not request.options.skip_validation:
                raise DryadError(
                    DryadErrorCode.INVALID_INPUT,
                    "Import validation failed",
                    {"errors": validation.errors}
                )
            
            # Parse exported grove
            exported_grove = self._parse_exported_grove(import_data["grove"])
            
            # Import grove
            grove_id = await self._import_grove_data(
                exported_grove, request.options, user_id
            )
            
            # Calculate import time
            import_time_ms = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000
            
            # Return response
            return ImportResponse(
                success=True,
                validation=validation,
                stats=self.stats,
                grove_id=grove_id,
                import_time_ms=import_time_ms,
                errors=self.errors,
                warnings=self.warnings
            )
            
        except Exception as e:
            logger.error(f"Failed to import grove: {e}")
            self.errors.append(str(e))
            import_time_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
            return ImportResponse(
                success=False,
                validation=None,
                stats=self.stats,
                grove_id=None,
                import_time_ms=import_time_ms,
                errors=self.errors,
                warnings=self.warnings
            )
    
    async def _load_import_data(self, request: ImportRequest) -> Dict[str, Any]:
        """Load import data from request."""
        if request.data:
            return request.data
        elif request.file_path:
            # TODO: Load from file
            raise DryadError(
                DryadErrorCode.NOT_IMPLEMENTED,
                "File import not yet implemented",
                {}
            )
        else:
            raise DryadError(
                DryadErrorCode.INVALID_INPUT,
                "Either data or file_path must be provided",
                {}
            )
    
    async def _validate_import_data(
        self,
        data: Dict[str, Any],
        options: ImportOptions
    ) -> ImportValidationResult:
        """Validate import data."""
        errors = []
        warnings = []
        
        # Check required fields
        if "metadata" not in data:
            errors.append("Missing 'metadata' field")
        if "grove" not in data:
            errors.append("Missing 'grove' field")
        
        if errors:
            return ImportValidationResult(
                is_valid=False,
                errors=errors,
                warnings=warnings,
                compatible_version=False,
                total_items=0
            )
        
        # Check version compatibility
        metadata = data["metadata"]
        export_version = metadata.get("export_version", "unknown")
        compatible_version = export_version in self.SUPPORTED_VERSIONS
        
        if not compatible_version:
            warnings.append(
                f"Export version {export_version} may not be fully compatible. "
                f"Supported versions: {', '.join(self.SUPPORTED_VERSIONS)}"
            )
        
        # Count total items
        grove_data = data["grove"]
        total_items = 1  # Grove itself
        total_items += self._count_items_recursive(grove_data.get("branches", []))
        
        # Validate strategy-specific requirements
        if options.strategy == ImportStrategy.MERGE_EXISTING:
            if not options.target_grove_id:
                errors.append("target_grove_id required for MERGE_EXISTING strategy")
        
        is_valid = len(errors) == 0
        
        return ImportValidationResult(
            is_valid=is_valid,
            errors=errors,
            warnings=warnings,
            compatible_version=compatible_version,
            total_items=total_items
        )
    
    def _count_items_recursive(self, branches: List[Dict]) -> int:
        """Count items recursively."""
        count = len(branches)
        for branch in branches:
            count += self._count_items_recursive(branch.get("children", []))
        return count
    
    def _parse_exported_grove(self, grove_data: Dict[str, Any]) -> ExportedGrove:
        """Parse exported grove data into Pydantic model."""
        return ExportedGrove(**grove_data)
    
    async def _import_grove_data(
        self,
        exported_grove: ExportedGrove,
        options: ImportOptions,
        user_id: str
    ) -> str:
        """
        Import grove data into database.
        
        Args:
            exported_grove: Exported grove data
            options: Import options
            user_id: User ID
            
        Returns:
            Grove ID (new or existing)
        """
        if options.strategy == ImportStrategy.CREATE_NEW:
            return await self._create_new_grove(exported_grove, options, user_id)
        elif options.strategy == ImportStrategy.MERGE_EXISTING:
            return await self._merge_into_existing_grove(exported_grove, options, user_id)
        elif options.strategy == ImportStrategy.SKIP_DUPLICATES:
            return await self._import_with_skip_duplicates(exported_grove, options, user_id)
        elif options.strategy == ImportStrategy.OVERWRITE:
            return await self._import_with_overwrite(exported_grove, options, user_id)
        else:
            raise DryadError(
                DryadErrorCode.INVALID_INPUT,
                f"Unsupported import strategy: {options.strategy}",
                {"strategy": options.strategy}
            )
    
    async def _create_new_grove(
        self,
        exported_grove: ExportedGrove,
        options: ImportOptions,
        user_id: str
    ) -> str:
        """Create new grove with new IDs."""
        # Create new grove
        grove_id = str(uuid.uuid4()) if not options.preserve_ids else exported_grove.id
        
        grove = Grove(
            id=grove_id,
            name=exported_grove.name,
            description=exported_grove.description,
            is_favorite=exported_grove.is_favorite,
            template_metadata=exported_grove.template_metadata
        )
        
        if options.preserve_timestamps and exported_grove.created_at:
            grove.created_at = exported_grove.created_at
            grove.updated_at = exported_grove.updated_at
            grove.last_accessed_at = exported_grove.last_accessed_at
        
        self.db.add(grove)
        self.stats.groves_created += 1

        # Import branches
        id_mapping = {}  # Map old IDs to new IDs
        for exported_branch in exported_grove.branches:
            await self._import_branch(
                exported_branch, grove_id, None, options, id_mapping
            )

        await self.db.commit()
        logger.info(f"Created new grove {grove_id}")

        return grove_id
    
    async def _import_branch(
        self,
        exported_branch: ExportedBranch,
        grove_id: str,
        parent_id: Optional[str],
        options: ImportOptions,
        id_mapping: Dict[str, str]
    ):
        """Import a branch recursively."""
        # Generate new ID or preserve old one
        old_branch_id = exported_branch.id
        branch_id = str(uuid.uuid4()) if not options.preserve_ids else old_branch_id
        id_mapping[old_branch_id] = branch_id
        
        # Create branch
        branch = Branch(
            id=branch_id,
            grove_id=grove_id,
            parent_id=parent_id,
            name=exported_branch.name,
            description=exported_branch.description,
            status=BranchStatus(exported_branch.status) if isinstance(exported_branch.status, str) else exported_branch.status,
            priority=BranchPriority(exported_branch.priority) if isinstance(exported_branch.priority, str) else exported_branch.priority,
            path_depth=exported_branch.path_depth
        )
        
        if options.preserve_timestamps and exported_branch.created_at:
            branch.created_at = exported_branch.created_at
            branch.updated_at = exported_branch.updated_at
        
        self.db.add(branch)
        self.stats.branches_created += 1
        
        # Import vessel
        if exported_branch.vessel and options.import_vessel_content:
            await self._import_vessel(exported_branch.vessel, branch_id, options)
        
        # Import dialogues
        if exported_branch.dialogues and options.import_dialogue_messages:
            for exported_dialogue in exported_branch.dialogues:
                await self._import_dialogue(exported_dialogue, branch_id, options, id_mapping)
        
        # Import observation points
        if exported_branch.observation_points and options.import_observation_points:
            for exported_point in exported_branch.observation_points:
                await self._import_observation_point(exported_point, branch_id, options)
        
        # Import children recursively
        for child in exported_branch.children:
            await self._import_branch(child, grove_id, branch_id, options, id_mapping)

    async def _import_vessel(
        self,
        exported_vessel: ExportedVessel,
        branch_id: str,
        options: ImportOptions
    ):
        """Import vessel for a branch."""
        vessel_id = str(uuid.uuid4()) if not options.preserve_ids else exported_vessel.id

        vessel = Vessel(
            id=vessel_id,
            branch_id=branch_id,
            file_references=exported_vessel.file_references,
            content_hash=exported_vessel.content_hash,
            storage_path=exported_vessel.storage_path,
            is_compressed=exported_vessel.is_compressed,
            compressed_path=exported_vessel.compressed_path,
            status=exported_vessel.status
        )

        if options.preserve_timestamps and exported_vessel.created_at:
            vessel.created_at = exported_vessel.created_at

        self.db.add(vessel)
        self.stats.vessels_created += 1

        # TODO: Import vessel content files

    async def _import_dialogue(
        self,
        exported_dialogue: ExportedDialogue,
        branch_id: str,
        options: ImportOptions,
        id_mapping: Dict[str, str]
    ):
        """Import dialogue for a branch."""
        old_dialogue_id = exported_dialogue.id
        dialogue_id = str(uuid.uuid4()) if not options.preserve_ids else old_dialogue_id
        id_mapping[old_dialogue_id] = dialogue_id

        dialogue = Dialogue(
            id=dialogue_id,
            branch_id=branch_id,
            oracle_used=exported_dialogue.oracle_used,
            insights=exported_dialogue.insights,
            storage_path=exported_dialogue.storage_path
        )

        if options.preserve_timestamps and exported_dialogue.created_at:
            dialogue.created_at = exported_dialogue.created_at

        self.db.add(dialogue)
        self.stats.dialogues_created += 1

        # Import messages
        for exported_message in exported_dialogue.messages:
            await self._import_dialogue_message(exported_message, dialogue_id, options)

        # Import suggestions
        if options.import_suggestions:
            for exported_suggestion in exported_dialogue.suggestions:
                await self._import_suggestion(exported_suggestion, dialogue_id, branch_id, options, id_mapping)

    async def _import_dialogue_message(
        self,
        exported_message: ExportedDialogueMessage,
        dialogue_id: str,
        options: ImportOptions
    ):
        """Import dialogue message."""
        message_id = str(uuid.uuid4()) if not options.preserve_ids else exported_message.id

        message = DialogueMessage(
            id=message_id,
            dialogue_id=dialogue_id,
            role=MessageRole(exported_message.role) if isinstance(exported_message.role, str) else exported_message.role,
            content=exported_message.content
        )

        if options.preserve_timestamps and exported_message.created_at:
            message.created_at = exported_message.created_at

        self.db.add(message)

    async def _import_suggestion(
        self,
        exported_suggestion: ExportedBranchSuggestion,
        dialogue_id: str,
        branch_id: str,
        options: ImportOptions,
        id_mapping: Dict[str, str]
    ):
        """Import branch suggestion."""
        suggestion_id = str(uuid.uuid4()) if not options.preserve_ids else exported_suggestion.id

        # Map created_branch_id if it exists
        created_branch_id = None
        if exported_suggestion.created_branch_id:
            created_branch_id = id_mapping.get(exported_suggestion.created_branch_id)

        suggestion = BranchSuggestion(
            id=suggestion_id,
            dialogue_id=dialogue_id,
            branch_id=branch_id,
            created_branch_id=created_branch_id,
            suggestion_type=exported_suggestion.suggestion_type,
            title=exported_suggestion.title,
            description=exported_suggestion.description,
            source_text=exported_suggestion.source_text,
            priority_score=exported_suggestion.priority_score,
            priority_level=exported_suggestion.priority_level,
            relevance_score=exported_suggestion.relevance_score,
            confidence=exported_suggestion.confidence,
            estimated_depth=exported_suggestion.estimated_depth,
            keywords=exported_suggestion.keywords,
            extra_metadata=exported_suggestion.metadata,
            is_auto_created=exported_suggestion.is_auto_created
        )

        if options.preserve_timestamps and exported_suggestion.created_at:
            suggestion.created_at = exported_suggestion.created_at

        self.db.add(suggestion)
        self.stats.suggestions_created += 1

    async def _import_observation_point(
        self,
        exported_point: ExportedObservationPoint,
        branch_id: str,
        options: ImportOptions
    ):
        """Import observation point."""
        point_id = str(uuid.uuid4()) if not options.preserve_ids else exported_point.id

        point = ObservationPoint(
            id=point_id,
            branch_id=branch_id,
            name=exported_point.name,
            description=exported_point.description,
            context=exported_point.context
        )

        if options.preserve_timestamps and exported_point.created_at:
            point.created_at = exported_point.created_at

        self.db.add(point)
        self.stats.observation_points_created += 1

        # Import possibilities
        for exported_possibility in exported_point.possibilities:
            await self._import_possibility(exported_possibility, point_id, options)

    async def _import_possibility(
        self,
        exported_possibility: ExportedPossibility,
        observation_point_id: str,
        options: ImportOptions
    ):
        """Import possibility."""
        possibility_id = str(uuid.uuid4()) if not options.preserve_ids else exported_possibility.id

        possibility = Possibility(
            id=possibility_id,
            observation_point_id=observation_point_id,
            description=exported_possibility.description,
            probability=exported_possibility.probability,
            is_manifested=exported_possibility.is_manifested
        )

        if options.preserve_timestamps and exported_possibility.created_at:
            possibility.created_at = exported_possibility.created_at

        self.db.add(possibility)

    async def _merge_into_existing_grove(
        self,
        exported_grove: ExportedGrove,
        options: ImportOptions,
        user_id: str
    ) -> str:
        """Merge into existing grove."""
        if not options.target_grove_id:
            raise DryadError(
                DryadErrorCode.INVALID_INPUT,
                "target_grove_id required for MERGE_EXISTING strategy",
                {}
            )

        # Get existing grove
        stmt = select(Grove).where(Grove.id == options.target_grove_id)
        result = await self.db.execute(stmt)
        grove = result.scalar_one_or_none()
        if not grove:
            raise NotFoundError("Grove", options.target_grove_id)

        # Update grove metadata
        grove.updated_at = datetime.now(timezone.utc)
        self.stats.groves_updated += 1

        # Import branches
        id_mapping = {}
        for exported_branch in exported_grove.branches:
            await self._import_branch(
                exported_branch, grove.id, None, options, id_mapping
            )

        await self.db.commit()
        logger.info(f"Merged into existing grove {grove.id}")

        return grove.id

    async def _import_with_skip_duplicates(
        self,
        exported_grove: ExportedGrove,
        options: ImportOptions,
        user_id: str
    ) -> str:
        """Import with skip duplicates strategy."""
        # For now, same as CREATE_NEW
        # TODO: Implement duplicate detection
        self.warnings.append("Skip duplicates strategy not fully implemented, creating new grove")
        return await self._create_new_grove(exported_grove, options, user_id)

    async def _import_with_overwrite(
        self,
        exported_grove: ExportedGrove,
        options: ImportOptions,
        user_id: str
    ) -> str:
        """Import with overwrite strategy."""
        # For now, same as CREATE_NEW
        # TODO: Implement overwrite logic
        self.warnings.append("Overwrite strategy not fully implemented, creating new grove")
        return await self._create_new_grove(exported_grove, options, user_id)

