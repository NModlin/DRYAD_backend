"""
Vessel Service

Platform-agnostic service for vessel management.
Ported from TypeScript services/vessel-service.ts
"""

import uuid
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.dryad.models.vessel import Vessel
from app.dryad.models.branch import Branch
from app.dryad.schemas.vessel_schemas import (
    VesselCreate, VesselResponse, VesselContentResponse, VesselContentUpdate,
    VesselSearchOptions, VesselSearchResult
)
from app.dryad.core.vessel_generator import VesselGenerator, VesselCreationOptions
from app.dryad.core.vessel_persistence import VesselPersistenceService
from app.dryad.core.vessel_inheritance import VesselInheritanceManager
from app.dryad.core.errors import DryadError, DryadErrorCode, NotFoundError, wrap_error
from app.core.logging_config import get_logger

logger = get_logger(__name__)


class VesselService:
    """Platform-agnostic Vessel Service for vessel management operations."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        
        # Initialize vessel subsystems
        self.vessel_generator = VesselGenerator()
        self.persistence_service = VesselPersistenceService()
        self.inheritance_manager = VesselInheritanceManager()
        
        logger.info("VesselService initialized")
    
    async def create_vessel(self, vessel_data: VesselCreate) -> VesselResponse:
        """
        Create a new vessel for a branch.
        
        Args:
            vessel_data: Vessel creation data
            
        Returns:
            Created vessel response
        """
        try:
            logger.debug(f"Creating vessel for branch {vessel_data.branch_id}")
            
            # Validate branch exists
            branch_stmt = select(Branch).where(Branch.id == vessel_data.branch_id)
            branch_result = await self.db.execute(branch_stmt)
            branch = branch_result.scalar_one_or_none()
            
            if not branch:
                raise NotFoundError("Branch", vessel_data.branch_id)
            
            # Prepare creation options
            options = VesselCreationOptions(
                parent_branch_id=vessel_data.parent_branch_id,
                initial_content={"base_context": vessel_data.initial_context} if vessel_data.initial_context else None
            )
            
            # Create vessel using generator
            vessel = await self.vessel_generator.create_vessel(vessel_data.branch_id, options)
            
            # Save to database
            self.db.add(vessel)
            await self.db.commit()
            await self.db.refresh(vessel)
            
            logger.info(f"Vessel created successfully: {vessel.id}")
            return VesselResponse.model_validate(vessel)
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to create vessel: {e}")
            raise wrap_error(
                e, DryadErrorCode.VESSEL_CREATE_FAILED,
                "Failed to create vessel",
                {"branch_id": vessel_data.branch_id}
            )
    
    async def get_vessel_by_id(self, vessel_id: str) -> Optional[VesselResponse]:
        """
        Get a vessel by ID.
        
        Args:
            vessel_id: Vessel ID
            
        Returns:
            Vessel response or None if not found
        """
        try:
            logger.debug(f"Getting vessel by ID: {vessel_id}")
            
            stmt = select(Vessel).options(selectinload(Vessel.branch)).where(Vessel.id == vessel_id)
            result = await self.db.execute(stmt)
            vessel = result.scalar_one_or_none()
            
            if not vessel:
                logger.warning(f"Vessel not found: {vessel_id}")
                return None
            
            vessel.update_last_accessed()
            await self.db.commit()
            
            logger.debug(f"Vessel retrieved successfully: {vessel_id}")
            return VesselResponse.model_validate(vessel)
            
        except Exception as e:
            logger.error(f"Failed to retrieve vessel {vessel_id}: {e}")
            raise wrap_error(
                e, DryadErrorCode.VESSEL_NOT_FOUND,
                f"Failed to get vessel: {vessel_id}",
                {"vessel_id": vessel_id}
            )
    
    async def get_vessel_by_branch_id(self, branch_id: str) -> Optional[VesselResponse]:
        """
        Get vessel by branch ID.
        
        Args:
            branch_id: Branch ID
            
        Returns:
            Vessel response or None if not found
        """
        try:
            logger.debug(f"Getting vessel by branch ID: {branch_id}")
            
            stmt = select(Vessel).options(selectinload(Vessel.branch)).where(Vessel.branch_id == branch_id)
            result = await self.db.execute(stmt)
            vessel = result.scalar_one_or_none()
            
            if not vessel:
                logger.warning(f"No vessel found for branch: {branch_id}")
                return None
            
            vessel.update_last_accessed()
            await self.db.commit()
            
            logger.debug(f"Vessel retrieved by branch ID: {vessel.id}")
            return VesselResponse.model_validate(vessel)
            
        except Exception as e:
            logger.error(f"Failed to retrieve vessel by branch {branch_id}: {e}")
            raise wrap_error(
                e, DryadErrorCode.VESSEL_NOT_FOUND,
                f"Failed to get vessel for branch: {branch_id}",
                {"branch_id": branch_id}
            )
    
    async def get_vessel_content(self, vessel_id: str) -> VesselContentResponse:
        """
        Get vessel content.
        
        Args:
            vessel_id: Vessel ID
            
        Returns:
            Vessel content response
        """
        try:
            logger.debug(f"Getting vessel content: {vessel_id}")
            
            # Get vessel from database
            stmt = select(Vessel).options(selectinload(Vessel.branch)).where(Vessel.id == vessel_id)
            result = await self.db.execute(stmt)
            vessel = result.scalar_one_or_none()
            
            if not vessel:
                raise NotFoundError("Vessel", vessel_id)
            
            # Load content from disk
            content = await self.persistence_service.load_vessel_content(vessel)
            
            # Get inherited context
            inherited_context = await self.inheritance_manager.resolve_full_inherited_context(vessel, self.db)
            
            # Build response
            response = VesselContentResponse(
                metadata={
                    "name": content.metadata.get("name", f"Vessel {vessel_id[:8]}"),
                    "status": content.metadata.get("status", vessel.status),
                    "branch_id": vessel.branch_id,
                    "grove_id": vessel.branch.grove_id if vessel.branch else ""
                },
                summary=content.summary,
                base_context=content.base_context,
                branch_context=content.branch_context,
                inherited_context=inherited_context,
                dialogues=content.dialogues
            )
            
            logger.debug(f"Vessel content retrieved successfully: {vessel_id}")
            return response
            
        except Exception as e:
            logger.error(f"Failed to get vessel content {vessel_id}: {e}")
            raise wrap_error(
                e, DryadErrorCode.VESSEL_NOT_FOUND,
                f"Failed to retrieve vessel content: {vessel_id}",
                {"vessel_id": vessel_id}
            )
    
    async def update_vessel_content(
        self,
        vessel_id: str,
        content_update: VesselContentUpdate
    ) -> None:
        """
        Update vessel content.
        
        Args:
            vessel_id: Vessel ID
            content_update: Content update data
        """
        try:
            logger.debug(f"Updating vessel content: {vessel_id}")
            
            # Get vessel from database
            stmt = select(Vessel).where(Vessel.id == vessel_id)
            result = await self.db.execute(stmt)
            vessel = result.scalar_one_or_none()
            
            if not vessel:
                raise NotFoundError("Vessel", vessel_id)
            
            # Load existing content
            existing_content = await self.persistence_service.load_vessel_content(vessel)
            
            # Update content fields
            if content_update.summary is not None:
                existing_content.summary = content_update.summary
            if content_update.base_context is not None:
                existing_content.base_context = content_update.base_context
            if content_update.branch_context is not None:
                existing_content.branch_context = content_update.branch_context
            if content_update.metadata is not None:
                existing_content.metadata.update(content_update.metadata)
            
            # Save updated content
            await self.persistence_service.save_vessel_content(vessel, existing_content)
            
            # Update vessel in database
            vessel.update_last_updated()
            await self.db.commit()
            
            logger.info(f"Vessel content updated successfully: {vessel_id}")
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to update vessel content {vessel_id}: {e}")
            raise wrap_error(
                e, DryadErrorCode.VESSEL_UPDATE_FAILED,
                f"Failed to update vessel content: {vessel_id}",
                {"vessel_id": vessel_id}
            )
    
    async def search_vessels(
        self,
        query: str,
        options: VesselSearchOptions = VesselSearchOptions()
    ) -> List[VesselSearchResult]:
        """
        Search across vessels using advanced search service.

        Args:
            query: Search query
            options: Search options

        Returns:
            List of search results
        """
        try:
            logger.debug(f"Searching vessels with query: {query}")

            # Use advanced search service for vessel search
            from app.dryad.services.search_service import AdvancedSearchService
            from app.dryad.schemas.search_schemas import (
                AdvancedSearchRequest,
                SearchType,
                SearchScope,
                SearchFilters,
                SortBy
            )

            # Build search request
            filters = SearchFilters(
                grove_ids=options.grove_ids if options.grove_ids else None,
                branch_ids=options.branch_ids if options.branch_ids else None,
                include_archived=options.include_archived
            )

            search_request = AdvancedSearchRequest(
                query=query,
                search_type=SearchType.HYBRID,  # Use hybrid for best results
                scope=SearchScope.VESSELS,
                filters=filters,
                sort_by=SortBy.RELEVANCE,
                limit=options.limit if options.limit else 10,
                offset=options.offset if options.offset else 0,
                include_snippets=True,
                include_metadata=True
            )

            # Perform search
            search_service = AdvancedSearchService(self.db)
            search_response = await search_service.search(search_request, "system")

            # Convert search results to vessel search results
            results = []
            for item in search_response.results:
                result = VesselSearchResult(
                    vessel_id=item.id,
                    branch_id=item.branch_id,
                    grove_id=item.grove_id,
                    content_snippet=item.snippet or "",
                    relevance_score=item.score,
                    created_at=item.created_at,
                    updated_at=item.updated_at
                )
                results.append(result)

            logger.info(f"Vessel search completed: {len(results)} results")
            return results

        except Exception as e:
            logger.error(f"Failed to search vessels: {e}")
            raise wrap_error(
                e, DryadErrorCode.DATABASE_ERROR,
                "Failed to search vessels",
                {"query": query}
            )
    
    async def delete_vessel(self, vessel_id: str) -> None:
        """
        Delete a vessel.
        
        Args:
            vessel_id: Vessel ID
        """
        try:
            logger.debug(f"Deleting vessel: {vessel_id}")
            
            stmt = select(Vessel).where(Vessel.id == vessel_id)
            result = await self.db.execute(stmt)
            vessel = result.scalar_one_or_none()
            
            if not vessel:
                raise NotFoundError("Vessel", vessel_id)
            
            # TODO: Clean up vessel files from disk
            
            # Delete from database
            await self.db.delete(vessel)
            await self.db.commit()
            
            logger.info(f"Vessel deleted successfully: {vessel_id}")
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to delete vessel {vessel_id}: {e}")
            raise wrap_error(
                e, DryadErrorCode.VESSEL_UPDATE_FAILED,
                f"Failed to delete vessel: {vessel_id}",
                {"vessel_id": vessel_id}
            )
    
    async def export_vessel(self, vessel_id: str, format: str = "json") -> str:
        """
        Export vessel content in specified format.
        
        Args:
            vessel_id: Vessel ID
            format: Export format (json, markdown, text)
            
        Returns:
            Exported content as string
        """
        try:
            logger.debug(f"Exporting vessel {vessel_id} in format {format}")
            
            # Get vessel content
            content_response = await self.get_vessel_content(vessel_id)
            
            if format == "json":
                import json
                return json.dumps(content_response.model_dump(), indent=2)
            elif format == "markdown":
                # TODO: Implement markdown export
                return f"# {content_response.metadata['name']}\n\n{content_response.summary}"
            elif format == "text":
                # TODO: Implement text export
                return f"{content_response.metadata['name']}\n\n{content_response.summary}"
            else:
                raise DryadError(
                    DryadErrorCode.INVALID_INPUT,
                    f"Unsupported export format: {format}",
                    {"format": format}
                )
            
        except Exception as e:
            logger.error(f"Failed to export vessel {vessel_id}: {e}")
            raise wrap_error(
                e, DryadErrorCode.VESSEL_LOAD_FAILED,
                f"Failed to export vessel: {vessel_id}",
                {"vessel_id": vessel_id, "format": format}
            )
