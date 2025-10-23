"""
Branch Suggestion Service Utilities

Utility methods for suggestion service operations.
"""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func, desc, asc
from sqlalchemy.orm import selectinload

from app.dryad.models import Branch, BranchSuggestion
from app.dryad.schemas.suggestion_schemas import (
    ListSuggestionsRequest, ListSuggestionsResponse,
    BranchSuggestion as BranchSuggestionSchema, SuggestionType, SuggestionPriority,
    CreateBranchFromSuggestionRequest, CreateBranchFromSuggestionResponse,
    SuggestionAnalyticsRequest, SuggestionAnalyticsResponse, SuggestionAnalytics,
    UpdateSuggestionRequest, DeleteSuggestionResponse, SuggestionFilters
)
from app.dryad.schemas.branch_schemas import BranchCreate
from app.dryad.services.branch_service import BranchService
from app.dryad.core.errors import NotFoundError, wrap_error, DryadErrorCode

logger = logging.getLogger(__name__)


async def list_suggestions(
    db: AsyncSession,
    request: ListSuggestionsRequest
) -> ListSuggestionsResponse:
    """List branch suggestions with filters."""
    try:
        # Build base query
        query = select(BranchSuggestion)
        
        # Apply filters
        if request.filters:
            query = apply_filters(query, request.filters)
        
        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0
        
        # Apply sorting
        if request.sort_by:
            sort_column = getattr(BranchSuggestion, request.sort_by, None)
            if sort_column is not None:
                if request.sort_desc:
                    query = query.order_by(desc(sort_column))
                else:
                    query = query.order_by(asc(sort_column))
        
        # Apply pagination
        query = query.limit(request.limit).offset(request.offset)
        
        # Execute query
        result = await db.execute(query)
        suggestions = result.scalars().all()
        
        # Convert to schemas
        suggestion_schemas = [
            model_to_schema(s) for s in suggestions
        ]
        
        return ListSuggestionsResponse(
            total=total,
            limit=request.limit,
            offset=request.offset,
            suggestions=suggestion_schemas
        )
        
    except Exception as e:
        logger.error(f"Failed to list suggestions: {e}")
        raise


def apply_filters(query, filters: SuggestionFilters):
    """Apply filters to query."""
    conditions = []
    
    if filters.branch_id:
        conditions.append(BranchSuggestion.branch_id == filters.branch_id)
    
    if filters.dialogue_id:
        conditions.append(BranchSuggestion.dialogue_id == filters.dialogue_id)
    
    if filters.suggestion_types:
        type_values = [t.value for t in filters.suggestion_types]
        conditions.append(BranchSuggestion.suggestion_type.in_(type_values))
    
    if filters.priority_levels:
        level_values = [p.value for p in filters.priority_levels]
        conditions.append(BranchSuggestion.priority_level.in_(level_values))
    
    if filters.min_priority_score is not None:
        conditions.append(BranchSuggestion.priority_score >= filters.min_priority_score)
    
    if filters.max_priority_score is not None:
        conditions.append(BranchSuggestion.priority_score <= filters.max_priority_score)
    
    if filters.is_auto_created is not None:
        conditions.append(BranchSuggestion.is_auto_created == filters.is_auto_created)
    
    if filters.created_branch_exists is not None:
        if filters.created_branch_exists:
            conditions.append(BranchSuggestion.created_branch_id.isnot(None))
        else:
            conditions.append(BranchSuggestion.created_branch_id.is_(None))
    
    if filters.keywords:
        # Filter by keywords (JSON array contains any of the specified keywords)
        keyword_conditions = []
        for keyword in filters.keywords:
            keyword_conditions.append(
                BranchSuggestion.keywords.contains([keyword])
            )
        if keyword_conditions:
            conditions.append(or_(*keyword_conditions))
    
    if conditions:
        query = query.where(and_(*conditions))
    
    return query


async def create_branch_from_suggestion(
    db: AsyncSession,
    request: CreateBranchFromSuggestionRequest,
    user_id: str
) -> CreateBranchFromSuggestionResponse:
    """Create a branch from a suggestion."""
    try:
        # Get suggestion
        stmt = select(BranchSuggestion).where(BranchSuggestion.id == request.suggestion_id)
        result = await db.execute(stmt)
        suggestion = result.scalar_one_or_none()
        
        if not suggestion:
            raise NotFoundError("Suggestion", request.suggestion_id)
        
        # Check if already created
        if suggestion.created_branch_id:
            return CreateBranchFromSuggestionResponse(
                suggestion_id=request.suggestion_id,
                branch_id=suggestion.created_branch_id,
                branch_name=suggestion.title,
                success=False,
                message="Branch already created from this suggestion"
            )
        
        # Get parent branch
        parent_stmt = select(Branch).where(Branch.id == suggestion.branch_id)
        parent_result = await db.execute(parent_stmt)
        parent_branch = parent_result.scalar_one_or_none()
        
        if not parent_branch:
            raise NotFoundError("Parent Branch", suggestion.branch_id)
        
        # Create branch
        branch_service = BranchService(db)
        
        # Use custom name/description if provided
        branch_name = request.custom_name or suggestion.title
        branch_description = request.custom_description or suggestion.description
        
        # Map suggestion priority to branch priority
        from app.dryad.models.branch import BranchPriority
        priority_mapping = {
            SuggestionPriority.CRITICAL.value: BranchPriority.HIGHEST,
            SuggestionPriority.HIGH.value: BranchPriority.HIGH,
            SuggestionPriority.MEDIUM.value: BranchPriority.MEDIUM,
            SuggestionPriority.LOW.value: BranchPriority.LOW
        }
        branch_priority = priority_mapping.get(suggestion.priority_level, BranchPriority.MEDIUM)
        
        branch_data = BranchCreate(
            grove_id=parent_branch.grove_id,
            parent_id=suggestion.branch_id,
            name=branch_name[:255],
            description=branch_description,
            priority=branch_priority
        )
        
        created_branch = await branch_service.create_branch(branch_data)
        
        # Update suggestion
        suggestion.created_branch_id = created_branch.id
        await db.commit()
        
        logger.info(f"Created branch {created_branch.id} from suggestion {request.suggestion_id}")
        
        return CreateBranchFromSuggestionResponse(
            suggestion_id=request.suggestion_id,
            branch_id=created_branch.id,
            branch_name=created_branch.name,
            success=True,
            message="Branch created successfully"
        )
        
    except Exception as e:
        await db.rollback()
        logger.error(f"Failed to create branch from suggestion: {e}")
        raise wrap_error(
            e, DryadErrorCode.BRANCH_CREATION_FAILED,
            "Failed to create branch from suggestion",
            {"suggestion_id": request.suggestion_id}
        )


async def get_suggestion_analytics(
    db: AsyncSession,
    request: SuggestionAnalyticsRequest
) -> SuggestionAnalyticsResponse:
    """Get analytics for branch suggestions."""
    try:
        # Build base query
        query = select(BranchSuggestion)
        
        # Apply filters
        conditions = []
        
        if request.branch_id:
            conditions.append(BranchSuggestion.branch_id == request.branch_id)
        
        if request.grove_id:
            # Join with Branch to filter by grove_id
            query = query.join(Branch, BranchSuggestion.branch_id == Branch.id)
            conditions.append(Branch.grove_id == request.grove_id)
        
        if request.start_date:
            conditions.append(BranchSuggestion.created_at >= request.start_date)
        
        if request.end_date:
            conditions.append(BranchSuggestion.created_at <= request.end_date)
        
        if conditions:
            query = query.where(and_(*conditions))
        
        # Execute query
        result = await db.execute(query)
        suggestions = result.scalars().all()
        
        # Calculate analytics
        total_suggestions = len(suggestions)
        auto_created_count = sum(1 for s in suggestions if s.is_auto_created)
        manually_created_count = sum(1 for s in suggestions if s.created_branch_id and not s.is_auto_created)
        
        # Count by type
        by_type = {}
        for s in suggestions:
            by_type[s.suggestion_type] = by_type.get(s.suggestion_type, 0) + 1
        
        # Count by priority
        by_priority = {}
        for s in suggestions:
            by_priority[s.priority_level] = by_priority.get(s.priority_level, 0) + 1
        
        # Calculate averages
        avg_priority = sum(s.priority_score for s in suggestions) / total_suggestions if total_suggestions > 0 else 0.0
        avg_confidence = sum(s.confidence for s in suggestions) / total_suggestions if total_suggestions > 0 else 0.0
        
        # Get top keywords
        keyword_freq = {}
        for s in suggestions:
            for keyword in (s.keywords or []):
                keyword_freq[keyword] = keyword_freq.get(keyword, 0) + 1
        
        top_keywords = [
            {"keyword": k, "count": v}
            for k, v in sorted(keyword_freq.items(), key=lambda x: x[1], reverse=True)[:10]
        ]
        
        analytics = SuggestionAnalytics(
            total_suggestions=total_suggestions,
            auto_created_count=auto_created_count,
            manually_created_count=manually_created_count,
            by_type=by_type,
            by_priority=by_priority,
            average_priority_score=avg_priority,
            average_confidence=avg_confidence,
            top_keywords=top_keywords
        )
        
        return SuggestionAnalyticsResponse(
            analytics=analytics,
            period_start=request.start_date,
            period_end=request.end_date,
            generated_at=datetime.utcnow()
        )
        
    except Exception as e:
        logger.error(f"Failed to get suggestion analytics: {e}")
        raise


def model_to_schema(model: BranchSuggestion) -> BranchSuggestionSchema:
    """Convert model to schema."""
    return BranchSuggestionSchema(
        id=model.id,
        dialogue_id=model.dialogue_id,
        branch_id=model.branch_id,
        suggestion_type=SuggestionType(model.suggestion_type),
        title=model.title,
        description=model.description,
        priority_score=model.priority_score,
        priority_level=SuggestionPriority(model.priority_level),
        keywords=model.keywords or [],
        estimated_depth=model.estimated_depth,
        relevance_score=model.relevance_score,
        confidence=model.confidence,
        source_text=model.source_text,
        is_auto_created=model.is_auto_created,
        created_branch_id=model.created_branch_id,
        created_at=model.created_at,
        metadata=model.extra_metadata
    )

