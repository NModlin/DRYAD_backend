"""
Grove Service

Platform-agnostic service for grove management.
Ported from TypeScript services/grove-service.ts
"""

import uuid
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from sqlalchemy.orm import selectinload

from dryad.database.models.grove import Grove
from dryad.database.models.branch import Branch, BranchStatus, BranchPriority
from dryad.schemas.grove_schemas import (
    GroveCreate, GroveUpdate, GroveResponse, GroveListOptions, GroveStats
)
from dryad.core.exceptions import DryadError, DryadErrorCode, NotFoundError, wrap_error
from dryad.core.logging_config import get_logger

logger = get_logger(__name__)


class GroveService:
    """Platform-agnostic Grove Service for grove management operations."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        logger.info("GroveService initialized")
    
    async def create_grove(self, grove_data: GroveCreate) -> GroveResponse:
        """
        Create a new grove with a root branch.
        
        Args:
            grove_data: Grove creation data
            
        Returns:
            Created grove response
        """
        try:
            logger.debug(f"Creating grove: {grove_data.name}")
            
            grove_id = str(uuid.uuid4())
            root_branch_id = str(uuid.uuid4())
            
            # Create the grove
            grove = Grove(
                id=grove_id,
                name=grove_data.name,
                description=grove_data.description,
                template_metadata=grove_data.template_metadata,
                is_favorite=grove_data.is_favorite or False
            )
            
            # Create root branch
            root_branch = Branch(
                id=root_branch_id,
                grove_id=grove_id,
                name="Root",
                description="Root branch of the grove",
                path_depth=0,
                status=BranchStatus.ACTIVE,
                priority=BranchPriority.MEDIUM,
                parent_id=None
            )
            
            # Save both in transaction
            self.db.add(grove)
            self.db.add(root_branch)
            await self.db.commit()
            await self.db.refresh(grove)
            
            logger.info(f"Grove created successfully: {grove_id}")
            return GroveResponse.model_validate(grove)
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to create grove: {e}")
            raise wrap_error(
                e, DryadErrorCode.GROVE_CREATE_FAILED,
                "Failed to create grove",
                {"grove_name": grove_data.name}
            )
    
    async def get_grove_by_id(
        self,
        grove_id: str,
        update_last_accessed: bool = True
    ) -> Optional[GroveResponse]:
        """
        Get a grove by ID.
        
        Args:
            grove_id: Grove ID
            update_last_accessed: Whether to update last accessed timestamp
            
        Returns:
            Grove response or None if not found
        """
        try:
            logger.debug(f"Getting grove by ID: {grove_id}")
            
            stmt = select(Grove).where(Grove.id == grove_id)
            result = await self.db.execute(stmt)
            grove = result.scalar_one_or_none()
            
            if not grove:
                logger.warning(f"Grove not found: {grove_id}")
                return None
            
            if update_last_accessed:
                grove.update_last_accessed()
                await self.db.commit()
            
            logger.debug(f"Grove retrieved successfully: {grove_id}")
            return GroveResponse.model_validate(grove)
            
        except Exception as e:
            logger.error(f"Failed to retrieve grove {grove_id}: {e}")
            raise wrap_error(
                e, DryadErrorCode.GROVE_NOT_FOUND,
                f"Failed to retrieve grove: {grove_id}",
                {"grove_id": grove_id}
            )
    
    async def list_groves(self, options: GroveListOptions = GroveListOptions()) -> List[GroveResponse]:
        """
        List groves with filtering and sorting options.
        
        Args:
            options: List options
            
        Returns:
            List of grove responses
        """
        try:
            logger.debug(f"Listing groves with options: {options}")
            
            stmt = select(Grove)
            
            # Apply filters
            if options.favorites_only:
                stmt = stmt.where(Grove.is_favorite == True)
            
            # Apply sorting
            # Note: options.sort_by and options.sort_order are already strings due to use_enum_values=True
            sort_field_name = options.sort_by if isinstance(options.sort_by, str) else options.sort_by.value
            sort_field = getattr(Grove, sort_field_name)
            sort_order = options.sort_order if isinstance(options.sort_order, str) else options.sort_order.value
            if sort_order == "DESC":
                stmt = stmt.order_by(sort_field.desc())
            else:
                stmt = stmt.order_by(sort_field.asc())
            
            # Apply pagination
            if options.limit:
                stmt = stmt.limit(options.limit)
            if options.offset:
                stmt = stmt.offset(options.offset)
            
            result = await self.db.execute(stmt)
            groves = result.scalars().all()
            
            logger.debug(f"Listed {len(groves)} groves")
            return [GroveResponse.model_validate(grove) for grove in groves]
            
        except Exception as e:
            logger.error(f"Failed to list groves: {e}")
            raise wrap_error(
                e, DryadErrorCode.DATABASE_ERROR,
                "Failed to list groves",
                {"options": options.model_dump()}
            )
    
    async def update_grove(self, grove_id: str, grove_data: GroveUpdate) -> GroveResponse:
        """
        Update an existing grove.
        
        Args:
            grove_id: Grove ID
            grove_data: Grove update data
            
        Returns:
            Updated grove response
        """
        try:
            logger.debug(f"Updating grove {grove_id}")
            
            stmt = select(Grove).where(Grove.id == grove_id)
            result = await self.db.execute(stmt)
            grove = result.scalar_one_or_none()
            
            if not grove:
                raise NotFoundError("Grove", grove_id)
            
            # Update fields
            if grove_data.name is not None:
                grove.name = grove_data.name.strip()
            if grove_data.description is not None:
                grove.description = grove_data.description
            if grove_data.template_metadata is not None:
                grove.template_metadata = grove_data.template_metadata
            if grove_data.is_favorite is not None:
                grove.is_favorite = grove_data.is_favorite
            
            grove.update_timestamp()
            
            await self.db.commit()
            await self.db.refresh(grove)
            
            logger.info(f"Grove updated successfully: {grove_id}")
            return GroveResponse.model_validate(grove)
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to update grove {grove_id}: {e}")
            raise wrap_error(
                e, DryadErrorCode.GROVE_UPDATE_FAILED,
                f"Failed to update grove: {grove_id}",
                {"grove_id": grove_id}
            )
    
    async def delete_grove(self, grove_id: str) -> None:
        """
        Delete a grove and all its branches.
        
        Args:
            grove_id: Grove ID
        """
        try:
            logger.debug(f"Deleting grove {grove_id}")
            
            stmt = select(Grove).where(Grove.id == grove_id)
            result = await self.db.execute(stmt)
            grove = result.scalar_one_or_none()
            
            if not grove:
                raise NotFoundError("Grove", grove_id)
            
            await self.db.delete(grove)
            await self.db.commit()
            
            logger.info(f"Grove deleted successfully: {grove_id}")
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to delete grove {grove_id}: {e}")
            raise wrap_error(
                e, DryadErrorCode.GROVE_DELETE_FAILED,
                f"Failed to delete grove: {grove_id}",
                {"grove_id": grove_id}
            )
    
    async def get_grove_stats(self, grove_id: str) -> GroveStats:
        """
        Get statistics for a grove.
        
        Args:
            grove_id: Grove ID
            
        Returns:
            Grove statistics
        """
        try:
            logger.debug(f"Getting grove statistics: {grove_id}")
            
            # Check if grove exists
            grove_stmt = select(Grove).where(Grove.id == grove_id)
            grove_result = await self.db.execute(grove_stmt)
            grove = grove_result.scalar_one_or_none()
            
            if not grove:
                raise NotFoundError("Grove", grove_id)
            
            # Get branch statistics
            from sqlalchemy import case
            branch_stats_stmt = select(
                func.count(Branch.id).label("total_branches"),
                func.sum(case((Branch.status == BranchStatus.ACTIVE, 1), else_=0)).label("active_branches"),
                func.sum(case((Branch.status == BranchStatus.ARCHIVED, 1), else_=0)).label("archived_branches")
            ).where(Branch.grove_id == grove_id)
            
            stats_result = await self.db.execute(branch_stats_stmt)
            stats_row = stats_result.first()
            
            stats = GroveStats(
                total_branches=stats_row.total_branches or 0,
                active_branches=stats_row.active_branches or 0,
                archived_branches=stats_row.archived_branches or 0,
                total_observations=0  # TODO: Implement observation point counting
            )
            
            logger.debug(f"Grove statistics retrieved: {grove_id}")
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get grove statistics {grove_id}: {e}")
            raise wrap_error(
                e, DryadErrorCode.GROVE_NOT_FOUND,
                f"Failed to get grove statistics: {grove_id}",
                {"grove_id": grove_id}
            )
    
    async def toggle_favorite(self, grove_id: str) -> GroveResponse:
        """
        Toggle grove favorite status.
        
        Args:
            grove_id: Grove ID
            
        Returns:
            Updated grove response
        """
        try:
            logger.debug(f"Toggling favorite status for grove {grove_id}")
            
            stmt = select(Grove).where(Grove.id == grove_id)
            result = await self.db.execute(stmt)
            grove = result.scalar_one_or_none()
            
            if not grove:
                raise NotFoundError("Grove", grove_id)
            
            grove.is_favorite = not grove.is_favorite
            grove.update_timestamp()
            
            await self.db.commit()
            await self.db.refresh(grove)
            
            logger.info(f"Favorite status toggled for grove {grove_id}: {grove.is_favorite}")
            return GroveResponse.model_validate(grove)
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to toggle favorite for grove {grove_id}: {e}")
            raise wrap_error(
                e, DryadErrorCode.GROVE_UPDATE_FAILED,
                f"Failed to toggle favorite: {grove_id}",
                {"grove_id": grove_id}
            )
