"""
Dryad Search Service Utilities

Helper functions for the advanced search service.
"""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from dryad.database.models import Grove, Branch, Vessel, Dialogue
from dryad.schemas.search_schemas import (
    SearchResultItem,
    SearchFacet,
    SearchFilters,
    SortBy
)
from dryad.core.logging_config import get_logger

logger = get_logger(__name__)


def apply_filters(
    results: List[SearchResultItem],
    filters: Optional[SearchFilters]
) -> List[SearchResultItem]:
    """Apply filters to search results."""
    if not filters:
        return results
    
    filtered = results
    
    # Filter by grove IDs
    if filters.grove_ids:
        filtered = [r for r in filtered if r.grove_id in filters.grove_ids]
    
    # Filter by branch IDs
    if filters.branch_ids:
        filtered = [r for r in filtered if r.branch_id in filters.branch_ids]
    
    # Filter by date range
    if filters.date_from:
        filtered = [r for r in filtered if r.created_at >= filters.date_from]
    
    if filters.date_to:
        filtered = [r for r in filtered if r.created_at <= filters.date_to]
    
    # Filter by minimum score
    if filters.min_score is not None:
        filtered = [r for r in filtered if r.score >= filters.min_score]
    
    return filtered


def sort_results(
    results: List[SearchResultItem],
    sort_by: SortBy
) -> List[SearchResultItem]:
    """Sort search results."""
    if sort_by == SortBy.RELEVANCE:
        return sorted(results, key=lambda x: x.score, reverse=True)
    elif sort_by == SortBy.DATE_DESC:
        return sorted(results, key=lambda x: x.created_at, reverse=True)
    elif sort_by == SortBy.DATE_ASC:
        return sorted(results, key=lambda x: x.created_at)
    elif sort_by == SortBy.TITLE:
        return sorted(results, key=lambda x: x.title.lower())
    else:
        return results


async def get_item_details(
    db: AsyncSession,
    item_id: str,
    item_type: str
) -> Optional[Dict[str, Any]]:
    """Get details for a search result item."""
    try:
        if item_type == "vessel":
            stmt = select(Vessel).where(Vessel.id == item_id)
            stmt = stmt.join(Branch).join(Grove)
            result = await db.execute(stmt)
            vessel = result.scalar_one_or_none()
            
            if vessel:
                return {
                    "title": f"Vessel in {vessel.branch.name}",
                    "grove_name": vessel.branch.grove.name,
                    "branch_name": vessel.branch.name,
                    "created_at": vessel.created_at,
                    "updated_at": vessel.updated_at
                }
        
        elif item_type == "dialogue":
            stmt = select(Dialogue).where(Dialogue.id == item_id)
            stmt = stmt.join(Branch).join(Grove)
            result = await db.execute(stmt)
            dialogue = result.scalar_one_or_none()
            
            if dialogue:
                return {
                    "title": f"Dialogue: {dialogue.query[:50]}...",
                    "grove_name": dialogue.branch.grove.name,
                    "branch_name": dialogue.branch.name,
                    "created_at": dialogue.created_at,
                    "updated_at": dialogue.updated_at
                }
        
        elif item_type == "branch":
            stmt = select(Branch).where(Branch.id == item_id)
            stmt = stmt.join(Grove)
            result = await db.execute(stmt)
            branch = result.scalar_one_or_none()
            
            if branch:
                return {
                    "title": branch.name,
                    "grove_name": branch.grove.name,
                    "branch_name": branch.name,
                    "created_at": branch.created_at,
                    "updated_at": branch.updated_at
                }
        
        return None
        
    except Exception as e:
        logger.error(f"Failed to get item details: {e}")
        return None


async def generate_facets(
    db: AsyncSession,
    user_id: str
) -> List[SearchFacet]:
    """Generate facets for filtering search results."""
    facets = []
    
    try:
        # Grove facet
        stmt = select(Grove.id, Grove.name, func.count(Branch.id).label('count'))
        stmt = stmt.join(Branch)
        stmt = stmt.group_by(Grove.id, Grove.name)
        result = await db.execute(stmt)
        grove_values = [
            {"id": str(row.id), "name": row.name, "count": row.count}
            for row in result
        ]
        
        if grove_values:
            facets.append(SearchFacet(
                name="groves",
                values=grove_values
            ))
        
        # Type facet
        type_values = [
            {"id": "vessel", "name": "Vessels", "count": 0},
            {"id": "dialogue", "name": "Dialogues", "count": 0},
            {"id": "branch", "name": "Branches", "count": 0}
        ]
        
        facets.append(SearchFacet(
            name="types",
            values=type_values
        ))
        
        return facets
        
    except Exception as e:
        logger.error(f"Failed to generate facets: {e}")
        return []


async def generate_suggestions(
    db: AsyncSession,
    query: str,
    scope: str
) -> List[str]:
    """Generate search suggestions based on query."""
    suggestions = []
    
    try:
        query_lower = query.lower()
        
        # Get recent queries that match
        # For now, return simple suggestions based on common terms
        common_terms = [
            "quantum", "knowledge", "tree", "branch", "vessel",
            "dialogue", "oracle", "wisdom", "exploration", "insight"
        ]
        
        suggestions = [
            term for term in common_terms
            if term.startswith(query_lower) and term != query_lower
        ][:5]
        
        return suggestions
        
    except Exception as e:
        logger.error(f"Failed to generate suggestions: {e}")
        return []


async def record_search_history(
    db: AsyncSession,
    user_id: str,
    query: str,
    search_type: str,
    scope: str,
    results_count: int
) -> None:
    """Record search in history."""
    try:
        # For now, just log it
        # In a full implementation, this would save to a search_history table
        logger.info(f"Search history: user={user_id}, query='{query}', type={search_type}, scope={scope}, results={results_count}")
        
    except Exception as e:
        logger.error(f"Failed to record search history: {e}")

