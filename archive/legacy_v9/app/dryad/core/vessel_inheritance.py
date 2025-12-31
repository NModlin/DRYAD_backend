"""
Vessel Inheritance Manager

Manages context inheritance between parent and child vessels.
Ported from TypeScript core/vessel/vessel-inheritance-manager.ts
"""

from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.dryad.models.vessel import Vessel
from app.dryad.models.branch import Branch
from app.dryad.core.vessel_generator import VesselContent
from app.dryad.core.errors import DryadError, DryadErrorCode
from app.core.logging_config import get_logger

logger = get_logger(__name__)


class VesselInheritanceManager:
    """Manages context inheritance between vessels."""
    
    def __init__(self):
        logger.info("VesselInheritanceManager initialized")
    
    async def resolve_full_inherited_context(
        self,
        vessel: Vessel,
        db: Optional[AsyncSession] = None
    ) -> str:
        """
        Resolve the full inherited context for a vessel by traversing up the branch tree.
        
        Args:
            vessel: The vessel to resolve context for
            db: Database session (optional, for future use)
            
        Returns:
            Combined inherited context from all parent branches
        """
        try:
            logger.debug(f"Resolving inherited context for vessel {vessel.id}")
            
            # For now, return empty string as we need database integration
            # This will be implemented when we integrate with the database layer
            inherited_contexts = []
            
            # TODO: Implement full context resolution
            # 1. Get branch hierarchy from vessel.branch up to root
            # 2. Load vessel content for each parent branch
            # 3. Combine contexts in hierarchical order
            # 4. Apply context optimization (truncation, summarization)
            
            if inherited_contexts:
                combined_context = "\n\n".join(inherited_contexts)
                logger.debug(f"Resolved inherited context length: {len(combined_context)}")
                return combined_context
            
            return ""
            
        except Exception as e:
            logger.error(f"Failed to resolve inherited context for vessel {vessel.id}: {e}")
            raise DryadError(
                DryadErrorCode.VESSEL_LOAD_FAILED,
                f"Failed to resolve inherited context: {str(e)}",
                {"vessel_id": vessel.id}
            )
    
    async def get_parent_vessel_context(
        self,
        branch_id: str,
        db: Optional[AsyncSession] = None
    ) -> Optional[str]:
        """
        Get the context from the parent vessel.
        
        Args:
            branch_id: ID of the current branch
            db: Database session (optional, for future use)
            
        Returns:
            Parent vessel context or None if no parent
        """
        try:
            logger.debug(f"Getting parent vessel context for branch {branch_id}")
            
            # TODO: Implement parent context retrieval
            # 1. Get parent branch ID from current branch
            # 2. Find vessel for parent branch
            # 3. Load and return parent vessel's context
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get parent vessel context for branch {branch_id}: {e}")
            return None
    
    async def inherit_context_from_parent(
        self,
        child_vessel: Vessel,
        parent_vessel: Vessel,
        inheritance_options: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Inherit context from parent vessel to child vessel.
        
        Args:
            child_vessel: The child vessel receiving context
            parent_vessel: The parent vessel providing context
            inheritance_options: Options for context inheritance
            
        Returns:
            Inherited context string
        """
        try:
            options = inheritance_options or {}
            max_context_length = options.get("max_context_length", 4000)
            include_dialogues = options.get("include_dialogues", True)
            
            logger.debug(f"Inheriting context from {parent_vessel.id} to {child_vessel.id}")
            
            # TODO: Implement context inheritance
            # 1. Load parent vessel content
            # 2. Extract relevant context (base + branch + selected dialogues)
            # 3. Apply context optimization (summarization, truncation)
            # 4. Return inherited context
            
            inherited_context = ""
            
            if len(inherited_context) > max_context_length:
                inherited_context = self._truncate_context(inherited_context, max_context_length)
            
            logger.debug(f"Inherited context length: {len(inherited_context)}")
            return inherited_context
            
        except Exception as e:
            logger.error(f"Failed to inherit context from {parent_vessel.id} to {child_vessel.id}: {e}")
            raise DryadError(
                DryadErrorCode.VESSEL_UPDATE_FAILED,
                f"Failed to inherit context: {str(e)}",
                {"child_vessel_id": child_vessel.id, "parent_vessel_id": parent_vessel.id}
            )
    
    def _truncate_context(self, context: str, max_length: int) -> str:
        """
        Truncate context to maximum length while preserving structure.
        
        Args:
            context: The context to truncate
            max_length: Maximum allowed length
            
        Returns:
            Truncated context
        """
        if len(context) <= max_length:
            return context
        
        # Simple truncation for now - could be improved with smart truncation
        truncated = context[:max_length - 50]  # Leave room for truncation notice
        truncated += "\n\n[Context truncated due to length limits...]"
        
        logger.debug(f"Context truncated from {len(context)} to {len(truncated)} characters")
        return truncated
    
    def _optimize_context(self, context: str, options: Dict[str, Any]) -> str:
        """
        Optimize context for better LLM consumption.
        
        Args:
            context: The context to optimize
            options: Optimization options
            
        Returns:
            Optimized context
        """
        # TODO: Implement context optimization
        # 1. Remove redundant information
        # 2. Summarize long sections
        # 3. Prioritize recent and relevant content
        # 4. Format for better LLM understanding
        
        return context
