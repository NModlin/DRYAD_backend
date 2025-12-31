"""
Export Service for Dryad

Handles exporting Dryad knowledge structures to various formats (JSON, YAML, Markdown).
"""

import json
import yaml
import gzip
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.dryad.models import (
    Grove, Branch, Vessel, Dialogue, DialogueMessage,
    ObservationPoint, Possibility, BranchSuggestion
)

logger = logging.getLogger(__name__)
from app.dryad.schemas.export_schemas import (
    ExportRequest, ExportResponse, ExportMetadata, ExportOptions,
    ExportFormat, ExportScope, ExportFilters,
    ExportedGrove, ExportedBranch, ExportedVessel, ExportedDialogue,
    ExportedDialogueMessage, ExportedObservationPoint, ExportedPossibility,
    ExportedBranchSuggestion
)
from app.dryad.core.errors import NotFoundError, DryadError, DryadErrorCode


class ExportService:
    """Service for exporting Dryad knowledge structures."""

    def __init__(self, db: AsyncSession):
        """
        Initialize export service.

        Args:
            db: Database session
        """
        self.db = db
    
    async def export_grove(self, request: ExportRequest, user_id: str) -> ExportResponse:
        """
        Export a grove to specified format.
        
        Args:
            request: Export request
            user_id: User ID
            
        Returns:
            Export response with data or file path
        """
        start_time = datetime.utcnow()
        warnings = []
        
        try:
            logger.info(f"Exporting grove {request.grove_id} for user {user_id}")

            # Get grove
            stmt = select(Grove).where(Grove.id == request.grove_id)
            result = await self.db.execute(stmt)
            grove = result.scalar_one_or_none()
            if not grove:
                raise NotFoundError("Grove", request.grove_id)
            
            # Export grove data
            exported_grove = await self._export_grove_data(
                grove, request.options, warnings
            )
            
            # Count exported items
            total_branches = self._count_branches(exported_grove)
            total_vessels = self._count_vessels(exported_grove)
            total_dialogues = self._count_dialogues(exported_grove)
            total_suggestions = self._count_suggestions(exported_grove)
            
            # Create metadata
            metadata = ExportMetadata(
                export_version="1.0.0",
                exported_at=datetime.utcnow(),
                grove_id=grove.id,
                grove_name=grove.name,
                total_branches=total_branches,
                total_vessels=total_vessels,
                total_dialogues=total_dialogues,
                total_suggestions=total_suggestions,
                export_options=request.options
            )
            
            # Format data
            formatted_data = await self._format_export_data(
                exported_grove, metadata, request.options.format
            )
            
            # Calculate export time
            export_time_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            # Return response
            return ExportResponse(
                success=True,
                metadata=metadata,
                data=formatted_data if not request.options.compress else None,
                file_path=None,  # TODO: Implement file export
                file_size_bytes=None,
                export_time_ms=export_time_ms,
                warnings=warnings
            )
            
        except Exception as e:
            logger.error(f"Failed to export grove {request.grove_id}: {e}")
            raise
    
    async def _export_grove_data(
        self,
        grove: Grove,
        options: ExportOptions,
        warnings: List[str]
    ) -> ExportedGrove:
        """
        Export grove data with all related entities.
        
        Args:
            grove: Grove to export
            options: Export options
            warnings: List to append warnings to
            
        Returns:
            Exported grove data
        """
        # Get root branches (branches with no parent)
        stmt = select(Branch).where(
            and_(
                Branch.grove_id == grove.id,
                Branch.parent_id.is_(None)
            )
        )

        # Apply filters
        if options.filters:
            stmt = self._apply_filters(stmt, options.filters)

        result = await self.db.execute(stmt)
        root_branches = result.scalars().all()
        
        # Export branches recursively
        exported_branches = []
        for branch in root_branches:
            exported_branch = await self._export_branch(
                branch, options, warnings, depth=0
            )
            if exported_branch:
                exported_branches.append(exported_branch)
        
        # Create exported grove
        return ExportedGrove(
            id=grove.id,
            name=grove.name,
            description=grove.description,
            created_at=grove.created_at,
            updated_at=grove.updated_at,
            last_accessed_at=grove.last_accessed_at,
            is_favorite=grove.is_favorite,
            template_metadata=grove.template_metadata,
            branches=exported_branches
        )
    
    async def _export_branch(
        self,
        branch: Branch,
        options: ExportOptions,
        warnings: List[str],
        depth: int
    ) -> Optional[ExportedBranch]:
        """
        Export a branch with all related entities.
        
        Args:
            branch: Branch to export
            options: Export options
            warnings: List to append warnings to
            depth: Current depth in tree
            
        Returns:
            Exported branch data or None if filtered out
        """
        # Check max depth filter
        if options.filters and options.filters.max_depth is not None:
            if depth > options.filters.max_depth:
                return None
        
        # Check archived filter
        if not options.filters or not options.filters.include_archived:
            if branch.status == "archived":
                return None
        
        # Export vessel
        vessel = None
        if options.scope == ExportScope.FULL and options.include_vessel_content:
            vessel = await self._export_vessel(branch, options, warnings)
        
        # Export dialogues
        dialogues = []
        if options.scope == ExportScope.FULL and options.include_dialogue_messages:
            dialogues = await self._export_dialogues(branch, options, warnings)
        
        # Export observation points
        observation_points = []
        if options.scope == ExportScope.FULL and options.include_observation_points:
            observation_points = await self._export_observation_points(branch, warnings)
        
        # Export child branches recursively
        children = []
        if options.scope != ExportScope.METADATA_ONLY:
            stmt = select(Branch).where(Branch.parent_id == branch.id)
            result = await self.db.execute(stmt)
            child_branches = result.scalars().all()

            for child in child_branches:
                exported_child = await self._export_branch(
                    child, options, warnings, depth + 1
                )
                if exported_child:
                    children.append(exported_child)
        
        # Create exported branch
        return ExportedBranch(
            id=branch.id,
            grove_id=branch.grove_id,
            parent_id=branch.parent_id,
            observation_point_id=branch.observation_point_id,
            name=branch.name,
            description=branch.description,
            status=branch.status.value if hasattr(branch.status, 'value') else branch.status,
            priority=branch.priority.value if hasattr(branch.priority, 'value') else branch.priority,
            path_depth=branch.path_depth,
            created_at=branch.created_at,
            updated_at=branch.updated_at,
            vessel=vessel,
            dialogues=dialogues,
            observation_points=observation_points,
            children=children
        )
    
    async def _export_vessel(
        self,
        branch: Branch,
        options: ExportOptions,
        warnings: List[str]
    ) -> Optional[ExportedVessel]:
        """Export vessel for a branch."""
        stmt = select(Vessel).where(Vessel.branch_id == branch.id)
        result = await self.db.execute(stmt)
        vessel = result.scalar_one_or_none()
        if not vessel:
            return None
        
        # TODO: Load vessel content from disk if needed
        content = None
        
        return ExportedVessel(
            id=vessel.id,
            branch_id=vessel.branch_id,
            file_references=vessel.file_references,
            content_hash=vessel.content_hash,
            storage_path=vessel.storage_path,
            is_compressed=vessel.is_compressed,
            compressed_path=vessel.compressed_path,
            status=vessel.status,
            created_at=vessel.created_at,
            content=content
        )
    
    async def _export_dialogues(
        self,
        branch: Branch,
        options: ExportOptions,
        warnings: List[str]
    ) -> List[ExportedDialogue]:
        """Export dialogues for a branch."""
        stmt = select(Dialogue).where(Dialogue.branch_id == branch.id)
        result = await self.db.execute(stmt)
        dialogues = result.scalars().all()

        exported_dialogues = []
        for dialogue in dialogues:
            # Export messages
            messages = []
            if options.include_dialogue_messages:
                msg_stmt = select(DialogueMessage).where(
                    DialogueMessage.dialogue_id == dialogue.id
                )
                msg_result = await self.db.execute(msg_stmt)
                db_messages = msg_result.scalars().all()
                
                messages = [
                    ExportedDialogueMessage(
                        id=msg.id,
                        dialogue_id=msg.dialogue_id,
                        role=msg.role.value if hasattr(msg.role, 'value') else msg.role,
                        content=msg.content,
                        created_at=msg.created_at
                    )
                    for msg in db_messages
                ]
            
            # Export suggestions
            suggestions = []
            if options.include_suggestions:
                db_suggestions = self.db.query(BranchSuggestion).filter(
                    BranchSuggestion.dialogue_id == dialogue.id
                ).all()
                
                suggestions = [
                    ExportedBranchSuggestion(
                        id=sug.id,
                        dialogue_id=sug.dialogue_id,
                        branch_id=sug.branch_id,
                        created_branch_id=sug.created_branch_id,
                        suggestion_type=sug.suggestion_type,
                        title=sug.title,
                        description=sug.description,
                        source_text=sug.source_text,
                        priority_score=sug.priority_score,
                        priority_level=sug.priority_level,
                        relevance_score=sug.relevance_score,
                        confidence=sug.confidence,
                        estimated_depth=sug.estimated_depth,
                        keywords=sug.keywords,
                        metadata=sug.extra_metadata,
                        is_auto_created=sug.is_auto_created,
                        created_at=sug.created_at
                    )
                    for sug in db_suggestions
                ]
            
            exported_dialogues.append(
                ExportedDialogue(
                    id=dialogue.id,
                    branch_id=dialogue.branch_id,
                    oracle_used=dialogue.oracle_used,
                    insights=dialogue.insights,
                    storage_path=dialogue.storage_path,
                    created_at=dialogue.created_at,
                    messages=messages,
                    suggestions=suggestions
                )
            )
        
        return exported_dialogues

    async def _export_observation_points(
        self,
        branch: Branch,
        warnings: List[str]
    ) -> List[ExportedObservationPoint]:
        """Export observation points for a branch."""
        stmt = select(ObservationPoint).where(
            ObservationPoint.branch_id == branch.id
        )
        result = await self.db.execute(stmt)
        observation_points = result.scalars().all()

        exported_points = []
        for point in observation_points:
            # Export possibilities
            poss_stmt = select(Possibility).where(
                Possibility.observation_point_id == point.id
            )
            poss_result = await self.db.execute(poss_stmt)
            possibilities = poss_result.scalars().all()

            exported_possibilities = [
                ExportedPossibility(
                    id=poss.id,
                    observation_point_id=poss.observation_point_id,
                    description=poss.description,
                    probability=poss.probability,
                    is_manifested=poss.is_manifested,
                    created_at=poss.created_at
                )
                for poss in possibilities
            ]

            exported_points.append(
                ExportedObservationPoint(
                    id=point.id,
                    branch_id=point.branch_id,
                    name=point.name,
                    description=point.description,
                    context=point.context,
                    created_at=point.created_at,
                    possibilities=exported_possibilities
                )
            )

        return exported_points

    def _apply_filters(self, stmt, filters: ExportFilters):
        """Apply export filters to statement."""
        if filters.branch_ids:
            stmt = stmt.where(Branch.id.in_(filters.branch_ids))

        if filters.min_priority:
            stmt = stmt.where(Branch.priority >= filters.min_priority)

        if filters.created_after:
            stmt = stmt.where(Branch.created_at >= filters.created_after)

        if filters.created_before:
            stmt = stmt.where(Branch.created_at <= filters.created_before)

        return stmt

    async def _format_export_data(
        self,
        grove: ExportedGrove,
        metadata: ExportMetadata,
        format: ExportFormat
    ) -> Dict[str, Any]:
        """
        Format exported data according to specified format.

        Args:
            grove: Exported grove data
            metadata: Export metadata
            format: Export format

        Returns:
            Formatted data
        """
        # Create export package
        export_data = {
            "metadata": metadata.model_dump(mode="json"),
            "grove": grove.model_dump(mode="json")
        }

        if format == ExportFormat.JSON:
            return export_data
        elif format == ExportFormat.YAML:
            return export_data  # Will be converted to YAML string later
        elif format == ExportFormat.MARKDOWN:
            return self._convert_to_markdown(grove, metadata)
        else:
            raise DryadError(
                DryadErrorCode.INVALID_INPUT,
                f"Unsupported export format: {format}",
                {"format": format}
            )

    def _convert_to_markdown(
        self,
        grove: ExportedGrove,
        metadata: ExportMetadata
    ) -> Dict[str, Any]:
        """Convert exported grove to Markdown format."""
        lines = []

        # Header
        lines.append(f"# {grove.name}")
        lines.append("")
        if grove.description:
            lines.append(grove.description)
            lines.append("")

        # Metadata
        lines.append("## Export Metadata")
        lines.append("")
        lines.append(f"- **Exported:** {metadata.exported_at.isoformat()}")
        lines.append(f"- **Version:** {metadata.export_version}")
        lines.append(f"- **Total Branches:** {metadata.total_branches}")
        lines.append(f"- **Total Vessels:** {metadata.total_vessels}")
        lines.append(f"- **Total Dialogues:** {metadata.total_dialogues}")
        lines.append("")

        # Branches
        lines.append("## Knowledge Tree")
        lines.append("")
        for branch in grove.branches:
            self._add_branch_to_markdown(branch, lines, depth=0)

        markdown_content = "\n".join(lines)
        return {"markdown": markdown_content}

    def _add_branch_to_markdown(
        self,
        branch: ExportedBranch,
        lines: List[str],
        depth: int
    ):
        """Add branch to markdown lines recursively."""
        indent = "  " * depth

        # Branch header
        lines.append(f"{indent}- **{branch.name}** ({branch.status})")
        if branch.description:
            lines.append(f"{indent}  {branch.description}")

        # Dialogues
        if branch.dialogues:
            lines.append(f"{indent}  - Dialogues: {len(branch.dialogues)}")

        # Observation points
        if branch.observation_points:
            lines.append(f"{indent}  - Observation Points: {len(branch.observation_points)}")

        # Children
        for child in branch.children:
            self._add_branch_to_markdown(child, lines, depth + 1)

    def _count_branches(self, grove: ExportedGrove) -> int:
        """Count total branches in exported grove."""
        count = len(grove.branches)
        for branch in grove.branches:
            count += self._count_branches_recursive(branch)
        return count

    def _count_branches_recursive(self, branch: ExportedBranch) -> int:
        """Count branches recursively."""
        count = len(branch.children)
        for child in branch.children:
            count += self._count_branches_recursive(child)
        return count

    def _count_vessels(self, grove: ExportedGrove) -> int:
        """Count total vessels in exported grove."""
        count = 0
        for branch in grove.branches:
            count += self._count_vessels_recursive(branch)
        return count

    def _count_vessels_recursive(self, branch: ExportedBranch) -> int:
        """Count vessels recursively."""
        count = 1 if branch.vessel else 0
        for child in branch.children:
            count += self._count_vessels_recursive(child)
        return count

    def _count_dialogues(self, grove: ExportedGrove) -> int:
        """Count total dialogues in exported grove."""
        count = 0
        for branch in grove.branches:
            count += self._count_dialogues_recursive(branch)
        return count

    def _count_dialogues_recursive(self, branch: ExportedBranch) -> int:
        """Count dialogues recursively."""
        count = len(branch.dialogues)
        for child in branch.children:
            count += self._count_dialogues_recursive(child)
        return count

    def _count_suggestions(self, grove: ExportedGrove) -> int:
        """Count total suggestions in exported grove."""
        count = 0
        for branch in grove.branches:
            count += self._count_suggestions_recursive(branch)
        return count

    def _count_suggestions_recursive(self, branch: ExportedBranch) -> int:
        """Count suggestions recursively."""
        count = sum(len(dialogue.suggestions) for dialogue in branch.dialogues)
        for child in branch.children:
            count += self._count_suggestions_recursive(child)
        return count

