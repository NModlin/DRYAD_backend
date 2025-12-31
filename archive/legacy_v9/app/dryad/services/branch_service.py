"""
Branch Service

Platform-agnostic service for branch management.
Ported from TypeScript services/branch-service.ts
"""

import uuid
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from sqlalchemy.orm import selectinload

from app.dryad.models.branch import Branch, BranchStatus, BranchPriority
from app.dryad.models.grove import Grove
from app.dryad.schemas.branch_schemas import (
    BranchCreate, BranchUpdate, BranchResponse, BranchTreeNode, BranchPath
)
from app.dryad.core.errors import DryadError, DryadErrorCode, NotFoundError, wrap_error
from app.core.logging_config import get_logger

logger = get_logger(__name__)


class BranchService:
    """Platform-agnostic Branch Service for branch management operations."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        logger.info("BranchService initialized")
    
    async def create_branch(self, branch_data: BranchCreate) -> BranchResponse:
        """
        Create a new branch.
        
        Args:
            branch_data: Branch creation data
            
        Returns:
            Created branch response
        """
        try:
            logger.debug(f"Creating branch: {branch_data.name} in grove {branch_data.grove_id}")
            
            branch_id = str(uuid.uuid4())
            path_depth = 0
            
            # If parent specified, get parent branch and calculate depth
            if branch_data.parent_id:
                parent_stmt = select(Branch).where(Branch.id == branch_data.parent_id)
                parent_result = await self.db.execute(parent_stmt)
                parent_branch = parent_result.scalar_one_or_none()
                
                if not parent_branch:
                    raise NotFoundError("Parent Branch", branch_data.parent_id)
                
                path_depth = parent_branch.path_depth + 1
            
            # Create the branch
            branch = Branch(
                id=branch_id,
                grove_id=branch_data.grove_id,
                parent_id=branch_data.parent_id,
                name=branch_data.name,
                description=branch_data.description,
                path_depth=path_depth,
                status=BranchStatus.ACTIVE,
                priority=branch_data.priority or BranchPriority.MEDIUM,
                observation_point_id=branch_data.observation_point_id
            )
            
            self.db.add(branch)
            await self.db.commit()
            await self.db.refresh(branch)

            # Manually set child_count to avoid lazy loading issues
            branch.child_count = 0

            logger.info(f"Branch created successfully: {branch_id}")
            return BranchResponse.model_validate(branch)
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to create branch: {e}")
            raise wrap_error(
                e, DryadErrorCode.BRANCH_CREATE_FAILED,
                "Failed to create branch",
                {"branch_name": branch_data.name, "grove_id": branch_data.grove_id}
            )
    
    async def get_branch_by_id(self, branch_id: str) -> Optional[BranchResponse]:
        """
        Get a branch by ID.
        
        Args:
            branch_id: Branch ID
            
        Returns:
            Branch response or None if not found
        """
        try:
            logger.debug(f"Getting branch by ID: {branch_id}")
            
            stmt = select(Branch).where(Branch.id == branch_id)
            result = await self.db.execute(stmt)
            branch = result.scalar_one_or_none()
            
            if not branch:
                logger.warning(f"Branch not found: {branch_id}")
                return None
            
            logger.debug(f"Branch retrieved successfully: {branch_id}")
            return BranchResponse.model_validate(branch)
            
        except Exception as e:
            logger.error(f"Failed to retrieve branch {branch_id}: {e}")
            raise wrap_error(
                e, DryadErrorCode.BRANCH_NOT_FOUND,
                f"Failed to retrieve branch: {branch_id}",
                {"branch_id": branch_id}
            )
    
    async def get_child_branches(self, parent_id: str) -> List[BranchResponse]:
        """
        Get child branches for a parent branch.
        
        Args:
            parent_id: Parent branch ID
            
        Returns:
            List of child branch responses
        """
        try:
            logger.debug(f"Getting child branches for parent: {parent_id}")
            
            stmt = select(Branch).where(Branch.parent_id == parent_id).order_by(Branch.created_at.asc())
            result = await self.db.execute(stmt)
            branches = result.scalars().all()
            
            logger.debug(f"Retrieved {len(branches)} child branches for parent {parent_id}")
            return [BranchResponse.model_validate(branch) for branch in branches]
            
        except Exception as e:
            logger.error(f"Failed to retrieve child branches for {parent_id}: {e}")
            raise wrap_error(
                e, DryadErrorCode.DATABASE_ERROR,
                f"Failed to retrieve child branches: {parent_id}",
                {"parent_id": parent_id}
            )
    
    async def get_branches_by_grove(self, grove_id: str) -> List[BranchResponse]:
        """
        Get all branches in a grove.
        
        Args:
            grove_id: Grove ID
            
        Returns:
            List of branch responses
        """
        try:
            logger.debug(f"Getting branches by grove: {grove_id}")
            
            stmt = select(Branch).where(Branch.grove_id == grove_id).order_by(
                Branch.path_depth.asc(), Branch.created_at.asc()
            )
            result = await self.db.execute(stmt)
            branches = result.scalars().all()
            
            logger.debug(f"Retrieved {len(branches)} branches for grove {grove_id}")
            return [BranchResponse.model_validate(branch) for branch in branches]
            
        except Exception as e:
            logger.error(f"Failed to retrieve branches for grove {grove_id}: {e}")
            raise wrap_error(
                e, DryadErrorCode.DATABASE_ERROR,
                f"Failed to retrieve branches for grove: {grove_id}",
                {"grove_id": grove_id}
            )
    
    async def get_branch_path(self, branch_id: str) -> BranchPath:
        """
        Get the path from root to a branch.
        
        Args:
            branch_id: Branch ID
            
        Returns:
            Branch path response
        """
        try:
            logger.debug(f"Getting branch path for: {branch_id}")
            
            path = []
            current_branch_id = branch_id
            
            while current_branch_id:
                stmt = select(Branch).where(Branch.id == current_branch_id)
                result = await self.db.execute(stmt)
                branch = result.scalar_one_or_none()
                
                if not branch:
                    if not path:  # First branch not found
                        raise NotFoundError("Branch", current_branch_id)
                    break
                
                path.insert(0, BranchResponse.model_validate(branch))
                current_branch_id = branch.parent_id
            
            logger.debug(f"Branch path retrieved with {len(path)} branches")
            return BranchPath(path=path, total_depth=len(path))
            
        except Exception as e:
            logger.error(f"Failed to retrieve branch path for {branch_id}: {e}")
            raise wrap_error(
                e, DryadErrorCode.BRANCH_NOT_FOUND,
                f"Failed to retrieve branch path: {branch_id}",
                {"branch_id": branch_id}
            )
    
    async def build_branch_tree(self, grove_id: str) -> Optional[BranchTreeNode]:
        """
        Build a tree structure for a grove.
        
        Args:
            grove_id: Grove ID
            
        Returns:
            Root branch tree node or None if no branches
        """
        try:
            logger.debug(f"Building branch tree for grove: {grove_id}")
            
            # Get all branches for the grove
            branches = await self.get_branches_by_grove(grove_id)
            
            if not branches:
                logger.warning(f"No branches found for grove {grove_id}")
                return None
            
            # Find root branch
            root_branch = next((b for b in branches if b.parent_id is None), None)
            if not root_branch:
                logger.warning(f"No root branch found for grove {grove_id}")
                return None
            
            # Build tree recursively
            def build_node(branch: BranchResponse, depth: int) -> BranchTreeNode:
                children = [
                    build_node(child, depth + 1)
                    for child in branches
                    if child.parent_id == branch.id
                ]
                return BranchTreeNode(branch=branch, children=children, depth=depth)
            
            tree = build_node(root_branch, 0)
            logger.debug(f"Branch tree built successfully for grove {grove_id}")
            return tree
            
        except Exception as e:
            logger.error(f"Failed to build branch tree for grove {grove_id}: {e}")
            raise wrap_error(
                e, DryadErrorCode.DATABASE_ERROR,
                f"Failed to build branch tree for grove: {grove_id}",
                {"grove_id": grove_id}
            )
    
    async def update_branch(self, branch_id: str, branch_data: BranchUpdate) -> BranchResponse:
        """
        Update an existing branch.
        
        Args:
            branch_id: Branch ID
            branch_data: Branch update data
            
        Returns:
            Updated branch response
        """
        try:
            logger.debug(f"Updating branch {branch_id}")
            
            stmt = select(Branch).where(Branch.id == branch_id)
            result = await self.db.execute(stmt)
            branch = result.scalar_one_or_none()
            
            if not branch:
                raise NotFoundError("Branch", branch_id)
            
            # Update fields
            if branch_data.name is not None:
                branch.name = branch_data.name.strip()
            if branch_data.description is not None:
                branch.description = branch_data.description
            if branch_data.status is not None:
                branch.status = branch_data.status
            if branch_data.priority is not None:
                branch.priority = branch_data.priority
            
            await self.db.commit()
            await self.db.refresh(branch)
            
            logger.info(f"Branch updated successfully: {branch_id}")
            return BranchResponse.model_validate(branch)
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to update branch {branch_id}: {e}")
            raise wrap_error(
                e, DryadErrorCode.BRANCH_UPDATE_FAILED,
                f"Failed to update branch: {branch_id}",
                {"branch_id": branch_id}
            )
    
    async def delete_branch(self, branch_id: str) -> None:
        """
        Delete a branch and its descendants.
        
        Args:
            branch_id: Branch ID
        """
        try:
            logger.debug(f"Deleting branch {branch_id}")
            
            stmt = select(Branch).where(Branch.id == branch_id)
            result = await self.db.execute(stmt)
            branch = result.scalar_one_or_none()
            
            if not branch:
                raise NotFoundError("Branch", branch_id)
            
            # Get all descendants
            descendants = await self._get_descendants(branch_id)
            
            # Delete in reverse order (deepest first)
            for descendant in reversed(descendants):
                await self.db.delete(descendant)
            
            # Delete the branch itself
            await self.db.delete(branch)
            await self.db.commit()
            
            logger.info(f"Branch deleted successfully: {branch_id}")
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to delete branch {branch_id}: {e}")
            raise wrap_error(
                e, DryadErrorCode.BRANCH_DELETE_FAILED,
                f"Failed to delete branch: {branch_id}",
                {"branch_id": branch_id}
            )
    
    async def _get_descendants(self, branch_id: str) -> List[Branch]:
        """Get all descendants of a branch."""
        descendants = []
        
        # Get direct children
        stmt = select(Branch).where(Branch.parent_id == branch_id)
        result = await self.db.execute(stmt)
        children = result.scalars().all()
        
        for child in children:
            descendants.append(child)
            # Recursively get descendants of each child
            child_descendants = await self._get_descendants(child.id)
            descendants.extend(child_descendants)
        
        return descendants
    
    async def archive_branch(self, branch_id: str) -> BranchResponse:
        """Archive a branch."""
        return await self.update_branch(branch_id, BranchUpdate(status=BranchStatus.ARCHIVED))
    
    async def activate_branch(self, branch_id: str) -> BranchResponse:
        """Activate a branch."""
        return await self.update_branch(branch_id, BranchUpdate(status=BranchStatus.ACTIVE))
