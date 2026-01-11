"""
Dryad Advanced Search Service

Provides comprehensive search functionality across the Dryad knowledge system.
"""

import time
import logging
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func, desc, asc
from sqlalchemy.orm import joinedload

from dryad.database.models import Grove, Branch, Vessel, Dialogue
from dryad.schemas.search_schemas import (
    AdvancedSearchRequest,
    AdvancedSearchResponse,
    SearchResultItem,
    SearchFacet,
    SearchFilters,
    SearchType,
    SearchScope,
    SortBy,
    SearchSuggestionRequest,
    SearchSuggestionResponse,
    SaveSearchRequest,
    SaveSearchResponse,
    SavedSearch,
    SearchHistoryItem,
    SearchHistoryResponse,
    SearchAnalytics,
    SearchAnalyticsResponse
)
from dryad.core.vector_store import vector_store
from dryad.core.logging_config import get_logger
from dryad.core.exceptions import DryadError, DryadErrorCode, wrap_error
from dryad.services import search_service_utils as utils

logger = get_logger(__name__)


class AdvancedSearchService:
    """Service for advanced search across Dryad knowledge system."""
    
    def __init__(self, db: AsyncSession):
        """Initialize search service."""
        self.db = db
        self.vector_store = vector_store
    
    async def search(
        self,
        request: AdvancedSearchRequest,
        user_id: str
    ) -> AdvancedSearchResponse:
        """
        Perform advanced search across Dryad system.
        
        Args:
            request: Search request parameters
            user_id: Current user ID
            
        Returns:
            Search response with results
        """
        start_time = time.time()
        
        try:
            logger.info(f"Performing {request.search_type} search: '{request.query}' (scope: {request.scope})")
            
            # Perform search based on type
            if request.search_type == SearchType.SEMANTIC:
                results = await self._semantic_search(request, user_id)
            elif request.search_type == SearchType.KEYWORD:
                results = await self._keyword_search(request, user_id)
            else:  # HYBRID
                results = await self._hybrid_search(request, user_id)
            
            # Apply filters
            results = self._apply_filters(results, request.filters)
            
            # Sort results
            results = self._sort_results(results, request.sort_by)
            
            # Paginate
            total = len(results)
            results = results[request.offset:request.offset + request.limit]
            
            # Generate facets
            facets = await self._generate_facets(request, user_id) if request.include_metadata else None
            
            # Generate suggestions
            suggestions = await self._generate_suggestions(request.query, request.scope) if request.include_metadata else None
            
            execution_time = time.time() - start_time
            
            # Record search in history
            await self._record_search_history(user_id, request, len(results))
            
            logger.info(f"Search completed: {len(results)} results in {execution_time:.2f}s")
            
            return AdvancedSearchResponse(
                results=results,
                total=total,
                query=request.query,
                search_type=request.search_type,
                scope=request.scope,
                execution_time=execution_time,
                facets=facets,
                suggestions=suggestions,
                has_more=total > (request.offset + request.limit)
            )
            
        except Exception as e:
            logger.error(f"Search failed: {e}")
            raise wrap_error(
                e, DryadErrorCode.DATABASE_ERROR,
                "Failed to perform search",
                {"query": request.query, "scope": request.scope}
            )
    
    async def _semantic_search(
        self,
        request: AdvancedSearchRequest,
        user_id: str
    ) -> List[SearchResultItem]:
        """Perform semantic (vector) search using Weaviate."""
        results = []
        
        try:
            # Check if vector store is available
            if not self.vector_store or not self.vector_store.is_connected:
                logger.warning("Vector store not available, falling back to keyword search")
                return await self._keyword_search(request, user_id)
            
            # Perform vector search
            vector_results = self.vector_store.search(
                query=request.query,
                limit=request.limit * 2,  # Get more results for filtering
                score_threshold=request.filters.min_score if request.filters and request.filters.min_score else 0.5
            )
            
            # Convert vector results to search result items
            for vr in vector_results:
                metadata = vr.get('metadata', {})
                
                # Extract IDs from metadata
                item_id = metadata.get('id', '')
                item_type = metadata.get('type', 'vessel')
                grove_id = metadata.get('grove_id', '')
                branch_id = metadata.get('branch_id', '')
                
                # Get additional details from database
                details = await self._get_item_details(item_id, item_type)
                if not details:
                    continue
                
                result_item = SearchResultItem(
                    id=item_id,
                    type=item_type,
                    title=details.get('title', ''),
                    snippet=vr.get('content', '')[:200] + '...' if request.include_snippets else None,
                    score=vr.get('score', 0.0),
                    grove_id=grove_id,
                    grove_name=details.get('grove_name', ''),
                    branch_id=branch_id if item_type != 'grove' else None,
                    branch_name=details.get('branch_name', '') if item_type != 'grove' else None,
                    created_at=details.get('created_at', datetime.now()),
                    updated_at=details.get('updated_at', datetime.now()),
                    metadata=metadata if request.include_metadata else None,
                    highlights=[vr.get('content', '')[:100]] if request.include_snippets else None
                )
                results.append(result_item)
            
            logger.debug(f"Semantic search found {len(results)} results")
            return results
            
        except Exception as e:
            logger.error(f"Semantic search failed: {e}")
            # Fall back to keyword search
            return await self._keyword_search(request, user_id)
    
    async def _keyword_search(
        self,
        request: AdvancedSearchRequest,
        user_id: str
    ) -> List[SearchResultItem]:
        """Perform keyword-based search using database."""
        results = []
        
        try:
            query_lower = request.query.lower()
            
            # Search based on scope
            if request.scope in [SearchScope.VESSELS, SearchScope.ALL]:
                vessel_results = await self._search_vessels(query_lower, request, user_id)
                results.extend(vessel_results)
            
            if request.scope in [SearchScope.DIALOGUES, SearchScope.ALL]:
                dialogue_results = await self._search_dialogues(query_lower, request, user_id)
                results.extend(dialogue_results)
            
            if request.scope in [SearchScope.BRANCHES, SearchScope.ALL]:
                branch_results = await self._search_branches(query_lower, request, user_id)
                results.extend(branch_results)
            
            logger.debug(f"Keyword search found {len(results)} results")
            return results
            
        except Exception as e:
            logger.error(f"Keyword search failed: {e}")
            raise
    
    async def _hybrid_search(
        self,
        request: AdvancedSearchRequest,
        user_id: str
    ) -> List[SearchResultItem]:
        """Perform hybrid search combining semantic and keyword."""
        try:
            # Get results from both methods
            semantic_results = await self._semantic_search(request, user_id)
            keyword_results = await self._keyword_search(request, user_id)
            
            # Merge and deduplicate results
            results_dict = {}
            
            # Add semantic results with higher weight
            for result in semantic_results:
                results_dict[result.id] = result
                result.score = result.score * 0.7  # Weight semantic results
            
            # Add keyword results
            for result in keyword_results:
                if result.id in results_dict:
                    # Combine scores
                    results_dict[result.id].score = (results_dict[result.id].score + result.score * 0.3) / 2
                else:
                    result.score = result.score * 0.3  # Weight keyword results
                    results_dict[result.id] = result
            
            results = list(results_dict.values())
            logger.debug(f"Hybrid search found {len(results)} results")
            return results
            
        except Exception as e:
            logger.error(f"Hybrid search failed: {e}")
            raise

    async def _search_vessels(
        self,
        query: str,
        request: AdvancedSearchRequest,
        user_id: str
    ) -> List[SearchResultItem]:
        """Search vessels by content."""
        results = []

        try:
            # Build query
            stmt = select(Vessel).join(Branch).join(Grove)

            # Apply filters
            conditions = [Vessel.content.ilike(f"%{query}%")]

            if request.filters:
                if request.filters.grove_ids:
                    conditions.append(Grove.id.in_(request.filters.grove_ids))
                if request.filters.branch_ids:
                    conditions.append(Branch.id.in_(request.filters.branch_ids))
                if not request.filters.include_archived:
                    conditions.append(Vessel.is_archived == False)
                if request.filters.date_from:
                    conditions.append(Vessel.created_at >= request.filters.date_from)
                if request.filters.date_to:
                    conditions.append(Vessel.created_at <= request.filters.date_to)

            stmt = stmt.where(and_(*conditions))
            stmt = stmt.options(joinedload(Vessel.branch).joinedload(Branch.grove))
            stmt = stmt.limit(request.limit * 2)

            result = await self.db.execute(stmt)
            vessels = result.scalars().unique().all()

            # Convert to search results
            for vessel in vessels:
                # Calculate simple relevance score based on query matches
                content_lower = (vessel.content or '').lower()
                score = min(1.0, content_lower.count(query) / 10.0)

                if request.filters and request.filters.min_score and score < request.filters.min_score:
                    continue

                snippet = None
                highlights = None
                if request.include_snippets and vessel.content:
                    # Find snippet around first match
                    idx = content_lower.find(query)
                    if idx >= 0:
                        start = max(0, idx - 50)
                        end = min(len(vessel.content), idx + 150)
                        snippet = "..." + vessel.content[start:end] + "..."
                        highlights = [snippet]

                result_item = SearchResultItem(
                    id=str(vessel.id),
                    type="vessel",
                    title=f"Vessel in {vessel.branch.name}",
                    snippet=snippet,
                    score=score,
                    grove_id=str(vessel.branch.grove_id),
                    grove_name=vessel.branch.grove.name,
                    branch_id=str(vessel.branch_id),
                    branch_name=vessel.branch.name,
                    created_at=vessel.created_at,
                    updated_at=vessel.updated_at,
                    metadata={"content_length": len(vessel.content or '')} if request.include_metadata else None,
                    highlights=highlights
                )
                results.append(result_item)

            return results

        except Exception as e:
            logger.error(f"Vessel search failed: {e}")
            return []

    async def _search_dialogues(
        self,
        query: str,
        request: AdvancedSearchRequest,
        user_id: str
    ) -> List[SearchResultItem]:
        """Search dialogues by content."""
        results = []

        try:
            # Build query
            stmt = select(Dialogue).join(Branch).join(Grove)

            # Search in both query and response
            conditions = [
                or_(
                    Dialogue.query.ilike(f"%{query}%"),
                    Dialogue.response.ilike(f"%{query}%")
                )
            ]

            if request.filters:
                if request.filters.grove_ids:
                    conditions.append(Grove.id.in_(request.filters.grove_ids))
                if request.filters.branch_ids:
                    conditions.append(Branch.id.in_(request.filters.branch_ids))
                if request.filters.date_from:
                    conditions.append(Dialogue.created_at >= request.filters.date_from)
                if request.filters.date_to:
                    conditions.append(Dialogue.created_at <= request.filters.date_to)

            stmt = stmt.where(and_(*conditions))
            stmt = stmt.options(joinedload(Dialogue.branch).joinedload(Branch.grove))
            stmt = stmt.limit(request.limit * 2)

            result = await self.db.execute(stmt)
            dialogues = result.scalars().unique().all()

            # Convert to search results
            for dialogue in dialogues:
                # Calculate relevance score
                query_lower = (dialogue.query or '').lower()
                response_lower = (dialogue.response or '').lower()
                score = min(1.0, (query_lower.count(query) + response_lower.count(query)) / 10.0)

                if request.filters and request.filters.min_score and score < request.filters.min_score:
                    continue

                snippet = None
                if request.include_snippets:
                    snippet = (dialogue.query or '')[:100] + "..."

                result_item = SearchResultItem(
                    id=str(dialogue.id),
                    type="dialogue",
                    title=f"Dialogue: {dialogue.query[:50]}...",
                    snippet=snippet,
                    score=score,
                    grove_id=str(dialogue.branch.grove_id),
                    grove_name=dialogue.branch.grove.name,
                    branch_id=str(dialogue.branch_id),
                    branch_name=dialogue.branch.name,
                    created_at=dialogue.created_at,
                    updated_at=dialogue.updated_at,
                    metadata={"provider": dialogue.provider} if request.include_metadata else None,
                    highlights=[dialogue.query[:100]] if request.include_snippets else None
                )
                results.append(result_item)

            return results

        except Exception as e:
            logger.error(f"Dialogue search failed: {e}")
            return []

    async def _search_branches(
        self,
        query: str,
        request: AdvancedSearchRequest,
        user_id: str
    ) -> List[SearchResultItem]:
        """Search branches by name and description."""
        results = []

        try:
            # Build query
            stmt = select(Branch).join(Grove)

            # Search in name and description
            conditions = [
                or_(
                    Branch.name.ilike(f"%{query}%"),
                    Branch.description.ilike(f"%{query}%")
                )
            ]

            if request.filters:
                if request.filters.grove_ids:
                    conditions.append(Grove.id.in_(request.filters.grove_ids))
                if request.filters.branch_ids:
                    conditions.append(Branch.id.in_(request.filters.branch_ids))
                if request.filters.date_from:
                    conditions.append(Branch.created_at >= request.filters.date_from)
                if request.filters.date_to:
                    conditions.append(Branch.created_at <= request.filters.date_to)

            stmt = stmt.where(and_(*conditions))
            stmt = stmt.options(joinedload(Branch.grove))
            stmt = stmt.limit(request.limit * 2)

            result = await self.db.execute(stmt)
            branches = result.scalars().unique().all()

            # Convert to search results
            for branch in branches:
                # Calculate relevance score
                name_lower = (branch.name or '').lower()
                desc_lower = (branch.description or '').lower()
                score = min(1.0, (name_lower.count(query) + desc_lower.count(query)) / 5.0)

                if request.filters and request.filters.min_score and score < request.filters.min_score:
                    continue

                snippet = None
                if request.include_snippets and branch.description:
                    snippet = branch.description[:200] + "..."

                result_item = SearchResultItem(
                    id=str(branch.id),
                    type="branch",
                    title=branch.name,
                    snippet=snippet,
                    score=score,
                    grove_id=str(branch.grove_id),
                    grove_name=branch.grove.name,
                    branch_id=str(branch.id),
                    branch_name=branch.name,
                    created_at=branch.created_at,
                    updated_at=branch.updated_at,
                    metadata={"status": branch.status} if request.include_metadata else None,
                    highlights=[branch.name] if request.include_snippets else None
                )
                results.append(result_item)

            return results

        except Exception as e:
            logger.error(f"Branch search failed: {e}")
            return []

    def _apply_filters(
        self,
        results: List[SearchResultItem],
        filters: Optional[SearchFilters]
    ) -> List[SearchResultItem]:
        """Apply filters to search results."""
        return utils.apply_filters(results, filters)

    def _sort_results(
        self,
        results: List[SearchResultItem],
        sort_by: SortBy
    ) -> List[SearchResultItem]:
        """Sort search results."""
        return utils.sort_results(results, sort_by)

    async def _get_item_details(
        self,
        item_id: str,
        item_type: str
    ) -> Optional[Dict[str, Any]]:
        """Get details for a search result item."""
        return await utils.get_item_details(self.db, item_id, item_type)

    async def _generate_facets(
        self,
        request: AdvancedSearchRequest,
        user_id: str
    ) -> List[SearchFacet]:
        """Generate facets for filtering."""
        return await utils.generate_facets(self.db, user_id)

    async def _generate_suggestions(
        self,
        query: str,
        scope: SearchScope
    ) -> List[str]:
        """Generate search suggestions."""
        return await utils.generate_suggestions(self.db, query, scope.value)

    async def _record_search_history(
        self,
        user_id: str,
        request: AdvancedSearchRequest,
        results_count: int
    ) -> None:
        """Record search in history."""
        await utils.record_search_history(
            self.db,
            user_id,
            request.query,
            request.search_type.value,
            request.scope.value,
            results_count
        )

    async def get_suggestions(
        self,
        request: SearchSuggestionRequest
    ) -> SearchSuggestionResponse:
        """Get search suggestions."""
        try:
            suggestions = await self._generate_suggestions(request.query, request.scope)
            suggestions = suggestions[:request.limit]

            return SearchSuggestionResponse(
                suggestions=suggestions,
                query=request.query
            )

        except Exception as e:
            logger.error(f"Failed to get suggestions: {e}")
            raise wrap_error(
                e, DryadErrorCode.DATABASE_ERROR,
                "Failed to get search suggestions",
                {"query": request.query}
            )

