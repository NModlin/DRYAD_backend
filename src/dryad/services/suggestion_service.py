"""
Branch Suggestion Service

AI-powered service for generating branch suggestions from oracle wisdom.
"""

import uuid
import re
import logging
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func, desc, asc
from sqlalchemy.orm import selectinload

from dryad.database.models import Dialogue, Branch, BranchSuggestion
from dryad.database.models.branch import BranchPriority
from dryad.schemas.suggestion_schemas import (
    GenerateSuggestionsRequest, GenerateSuggestionsResponse,
    BranchSuggestion as BranchSuggestionSchema, SuggestionType, SuggestionPriority,
    ListSuggestionsRequest, ListSuggestionsResponse, SuggestionFilters,
    CreateBranchFromSuggestionRequest, CreateBranchFromSuggestionResponse,
    SuggestionAnalyticsRequest, SuggestionAnalyticsResponse, SuggestionAnalytics,
    UpdateSuggestionRequest, DeleteSuggestionResponse
)
from dryad.schemas.branch_schemas import BranchCreate
from dryad.services.branch_service import BranchService
from dryad.core.exceptions import DryadError, DryadErrorCode, NotFoundError, wrap_error

logger = logging.getLogger(__name__)


class SuggestionService:
    """Service for AI-powered branch suggestions."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def generate_suggestions(
        self,
        request: GenerateSuggestionsRequest,
        user_id: str
    ) -> GenerateSuggestionsResponse:
        """
        Generate branch suggestions from oracle dialogue.
        
        Args:
            request: Generation request
            user_id: User ID
            
        Returns:
            Generated suggestions response
        """
        try:
            import time
            start_time = time.time()
            
            logger.debug(f"Generating suggestions for dialogue {request.dialogue_id}")
            
            # Get dialogue with insights
            dialogue_stmt = select(Dialogue).where(Dialogue.id == request.dialogue_id)
            dialogue_result = await self.db.execute(dialogue_stmt)
            dialogue = dialogue_result.scalar_one_or_none()
            
            if not dialogue:
                raise NotFoundError("Dialogue", request.dialogue_id)
            
            # Extract suggestions from insights
            suggestions = await self._extract_suggestions_from_dialogue(
                dialogue,
                request.max_suggestions,
                request.include_low_priority
            )
            
            # Auto-create branches for high-priority suggestions
            auto_created_count = 0
            if request.auto_create_threshold:
                auto_created_count = await self._auto_create_branches(
                    suggestions,
                    request.auto_create_threshold,
                    user_id
                )
            
            # Save suggestions to database
            for suggestion in suggestions:
                self.db.add(suggestion)
            
            await self.db.commit()
            
            # Convert to response schemas
            suggestion_schemas = [
                self._model_to_schema(s) for s in suggestions
            ]
            
            processing_time = (time.time() - start_time) * 1000
            
            logger.info(f"Generated {len(suggestions)} suggestions ({auto_created_count} auto-created)")
            
            return GenerateSuggestionsResponse(
                dialogue_id=request.dialogue_id,
                branch_id=dialogue.branch_id,
                total_suggestions=len(suggestions),
                auto_created_count=auto_created_count,
                suggestions=suggestion_schemas,
                processing_time_ms=processing_time
            )
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to generate suggestions: {e}")
            raise wrap_error(
                e, DryadErrorCode.ORACLE_CONSULTATION_FAILED,
                "Failed to generate branch suggestions",
                {"dialogue_id": request.dialogue_id}
            )
    
    async def _extract_suggestions_from_dialogue(
        self,
        dialogue: Dialogue,
        max_suggestions: int,
        include_low_priority: bool
    ) -> List[BranchSuggestion]:
        """Extract suggestions from dialogue insights."""
        suggestions = []
        insights = dialogue.insights or {}
        
        # Process themes
        for theme in insights.get("themes", []):
            suggestion = await self._create_suggestion_from_text(
                dialogue_id=dialogue.id,
                branch_id=dialogue.branch_id,
                suggestion_type=SuggestionType.THEME,
                text=theme
            )
            if suggestion:
                suggestions.append(suggestion)
        
        # Process questions
        for question in insights.get("questions", []):
            suggestion = await self._create_suggestion_from_text(
                dialogue_id=dialogue.id,
                branch_id=dialogue.branch_id,
                suggestion_type=SuggestionType.QUESTION,
                text=question
            )
            if suggestion:
                suggestions.append(suggestion)
        
        # Process decisions
        for decision in insights.get("decisions", []):
            suggestion = await self._create_suggestion_from_text(
                dialogue_id=dialogue.id,
                branch_id=dialogue.branch_id,
                suggestion_type=SuggestionType.DECISION,
                text=decision
            )
            if suggestion:
                suggestions.append(suggestion)
        
        # Process facts
        for fact in insights.get("facts", []):
            suggestion = await self._create_suggestion_from_text(
                dialogue_id=dialogue.id,
                branch_id=dialogue.branch_id,
                suggestion_type=SuggestionType.FACT,
                text=fact
            )
            if suggestion:
                suggestions.append(suggestion)
        
        # Filter by priority if needed
        if not include_low_priority:
            suggestions = [s for s in suggestions if s.priority_level != SuggestionPriority.LOW]
        
        # Sort by priority score (descending)
        suggestions.sort(key=lambda s: s.priority_score, reverse=True)
        
        # Limit to max_suggestions
        return suggestions[:max_suggestions]
    
    async def _create_suggestion_from_text(
        self,
        dialogue_id: str,
        branch_id: str,
        suggestion_type: SuggestionType,
        text: str
    ) -> Optional[BranchSuggestion]:
        """Create a suggestion from text."""
        try:
            # Generate title and description
            title, description = self._generate_title_and_description(text, suggestion_type)
            
            # Extract keywords
            keywords = self._extract_keywords(text)
            
            # Calculate scores
            priority_score = self._calculate_priority_score(text, suggestion_type, keywords)
            relevance_score = self._calculate_relevance_score(text, keywords)
            confidence = self._calculate_confidence(text, suggestion_type)
            
            # Determine priority level
            priority_level = self._get_priority_level(priority_score)
            
            # Estimate depth
            estimated_depth = self._estimate_depth(text, suggestion_type)
            
            # Create suggestion model
            suggestion = BranchSuggestion(
                id=str(uuid.uuid4()),
                dialogue_id=dialogue_id,
                branch_id=branch_id,
                suggestion_type=suggestion_type.value,
                title=title,
                description=description,
                source_text=text,
                priority_score=priority_score,
                priority_level=priority_level.value,
                relevance_score=relevance_score,
                confidence=confidence,
                estimated_depth=estimated_depth,
                keywords=keywords,
                extra_metadata={
                    "text_length": len(text),
                    "keyword_count": len(keywords)
                }
            )
            
            return suggestion
            
        except Exception as e:
            logger.error(f"Failed to create suggestion from text: {e}")
            return None
    
    def _generate_title_and_description(
        self,
        text: str,
        suggestion_type: SuggestionType
    ) -> Tuple[str, str]:
        """Generate title and description from text."""
        # Clean text
        clean_text = text.strip()
        
        # Generate title (first 100 chars or first sentence)
        title = clean_text[:100]
        if '.' in title:
            title = title.split('.')[0] + '.'
        if '?' in title:
            title = title.split('?')[0] + '?'
        
        # Add prefix based on type
        if suggestion_type == SuggestionType.THEME:
            title = f"Explore: {title}"
        elif suggestion_type == SuggestionType.QUESTION:
            title = f"Investigate: {title}"
        elif suggestion_type == SuggestionType.DECISION:
            title = f"Implement: {title}"
        elif suggestion_type == SuggestionType.FACT:
            title = f"Verify: {title}"
        
        # Description is the full text
        description = clean_text
        
        return title[:255], description
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extract keywords from text."""
        # Remove common words
        stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were', 'be',
            'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will',
            'would', 'should', 'could', 'may', 'might', 'must', 'can', 'this',
            'that', 'these', 'those', 'what', 'which', 'who', 'when', 'where',
            'why', 'how'
        }
        
        # Extract words (alphanumeric, 3+ chars)
        words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
        
        # Filter stop words and get unique
        keywords = list(set([w for w in words if w not in stop_words]))
        
        # Sort by frequency in text
        word_freq = {w: text.lower().count(w) for w in keywords}
        keywords.sort(key=lambda w: word_freq[w], reverse=True)
        
        # Return top 10
        return keywords[:10]

    def _calculate_priority_score(
        self,
        text: str,
        suggestion_type: SuggestionType,
        keywords: List[str]
    ) -> float:
        """Calculate priority score (0-100)."""
        score = 50.0  # Base score

        # Type-based scoring
        type_scores = {
            SuggestionType.THEME: 15.0,
            SuggestionType.QUESTION: 20.0,
            SuggestionType.DECISION: 25.0,
            SuggestionType.FACT: 10.0,
            SuggestionType.INSIGHT: 20.0
        }
        score += type_scores.get(suggestion_type, 0.0)

        # Length-based scoring (longer = more detailed = higher priority)
        if len(text) > 200:
            score += 10.0
        elif len(text) > 100:
            score += 5.0

        # Keyword richness
        score += min(len(keywords) * 2, 15.0)

        # Question marks indicate exploration opportunities
        if '?' in text:
            score += 5.0

        # Action words indicate implementable decisions
        action_words = ['implement', 'create', 'build', 'develop', 'design', 'explore', 'investigate']
        if any(word in text.lower() for word in action_words):
            score += 5.0

        return min(score, 100.0)

    def _calculate_relevance_score(self, text: str, keywords: List[str]) -> float:
        """Calculate relevance score (0-1)."""
        # Base relevance
        relevance = 0.5

        # Keyword density
        if keywords:
            keyword_density = len(keywords) / max(len(text.split()), 1)
            relevance += min(keyword_density * 2, 0.3)

        # Specificity (longer text with more keywords = more specific)
        if len(text) > 100 and len(keywords) > 5:
            relevance += 0.2

        return min(relevance, 1.0)

    def _calculate_confidence(self, text: str, suggestion_type: SuggestionType) -> float:
        """Calculate confidence score (0-1)."""
        confidence = 0.7  # Base confidence

        # Well-formed text increases confidence
        if text.endswith('.') or text.endswith('?') or text.endswith('!'):
            confidence += 0.1

        # Longer text = more context = higher confidence
        if len(text) > 150:
            confidence += 0.1

        # Questions are inherently exploratory (lower confidence)
        if suggestion_type == SuggestionType.QUESTION:
            confidence -= 0.1

        # Decisions and facts are more concrete (higher confidence)
        if suggestion_type in [SuggestionType.DECISION, SuggestionType.FACT]:
            confidence += 0.1

        return min(max(confidence, 0.0), 1.0)

    def _get_priority_level(self, priority_score: float) -> SuggestionPriority:
        """Get priority level from score."""
        if priority_score >= 90:
            return SuggestionPriority.CRITICAL
        elif priority_score >= 70:
            return SuggestionPriority.HIGH
        elif priority_score >= 40:
            return SuggestionPriority.MEDIUM
        else:
            return SuggestionPriority.LOW

    def _estimate_depth(self, text: str, suggestion_type: SuggestionType) -> int:
        """Estimate exploration depth."""
        # Base depth
        depth = 1

        # Questions suggest deeper exploration
        if suggestion_type == SuggestionType.QUESTION:
            depth += 1

        # Themes suggest broader exploration
        if suggestion_type == SuggestionType.THEME:
            depth += 2

        # Complex text suggests deeper exploration
        if len(text) > 200:
            depth += 1

        # Multiple questions suggest iterative exploration
        question_count = text.count('?')
        if question_count > 1:
            depth += question_count - 1

        return min(depth, 5)

    async def _auto_create_branches(
        self,
        suggestions: List[BranchSuggestion],
        threshold: float,
        user_id: str
    ) -> int:
        """Auto-create branches for high-priority suggestions."""
        created_count = 0
        branch_service = BranchService(self.db)

        for suggestion in suggestions:
            if suggestion.priority_score >= threshold:
                try:
                    # Get parent branch to determine grove_id
                    parent_stmt = select(Branch).where(Branch.id == suggestion.branch_id)
                    parent_result = await self.db.execute(parent_stmt)
                    parent_branch = parent_result.scalar_one_or_none()

                    if not parent_branch:
                        continue

                    # Map suggestion priority to branch priority
                    branch_priority = self._map_to_branch_priority(suggestion.priority_level)

                    # Create branch
                    branch_data = BranchCreate(
                        grove_id=parent_branch.grove_id,
                        parent_id=suggestion.branch_id,
                        name=suggestion.title[:255],
                        description=suggestion.description,
                        priority=branch_priority
                    )

                    created_branch = await branch_service.create_branch(branch_data)

                    # Update suggestion with created branch ID
                    suggestion.is_auto_created = True
                    suggestion.created_branch_id = created_branch.id

                    created_count += 1
                    logger.info(f"Auto-created branch {created_branch.id} from suggestion {suggestion.id}")

                except Exception as e:
                    logger.error(f"Failed to auto-create branch from suggestion {suggestion.id}: {e}")
                    continue

        return created_count

    def _map_to_branch_priority(self, suggestion_priority: str) -> BranchPriority:
        """Map suggestion priority to branch priority."""
        mapping = {
            SuggestionPriority.CRITICAL.value: BranchPriority.HIGHEST,
            SuggestionPriority.HIGH.value: BranchPriority.HIGH,
            SuggestionPriority.MEDIUM.value: BranchPriority.MEDIUM,
            SuggestionPriority.LOW.value: BranchPriority.LOW
        }
        return mapping.get(suggestion_priority, BranchPriority.MEDIUM)

    def _model_to_schema(self, model: BranchSuggestion) -> BranchSuggestionSchema:
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

    async def list_suggestions(
        self,
        request: ListSuggestionsRequest
    ) -> ListSuggestionsResponse:
        """List branch suggestions with filters."""
        from dryad.services import suggestion_service_utils
        return await suggestion_service_utils.list_suggestions(self.db, request)

    async def create_branch_from_suggestion(
        self,
        request: CreateBranchFromSuggestionRequest,
        user_id: str
    ) -> CreateBranchFromSuggestionResponse:
        """Create a branch from a suggestion."""
        from dryad.services import suggestion_service_utils
        return await suggestion_service_utils.create_branch_from_suggestion(
            self.db, request, user_id
        )

    async def get_suggestion_analytics(
        self,
        request: SuggestionAnalyticsRequest
    ) -> SuggestionAnalyticsResponse:
        """Get analytics for branch suggestions."""
        from dryad.services import suggestion_service_utils
        return await suggestion_service_utils.get_suggestion_analytics(self.db, request)

    async def update_suggestion(
        self,
        suggestion_id: str,
        request: UpdateSuggestionRequest
    ) -> BranchSuggestionSchema:
        """Update a suggestion."""
        try:
            # Get suggestion
            stmt = select(BranchSuggestion).where(BranchSuggestion.id == suggestion_id)
            result = await self.db.execute(stmt)
            suggestion = result.scalar_one_or_none()

            if not suggestion:
                raise NotFoundError("Suggestion", suggestion_id)

            # Update fields
            if request.title is not None:
                suggestion.title = request.title[:255]
            if request.description is not None:
                suggestion.description = request.description
            if request.priority_score is not None:
                suggestion.priority_score = request.priority_score
                suggestion.priority_level = self._get_priority_level(request.priority_score).value
            if request.keywords is not None:
                suggestion.keywords = request.keywords
            if request.metadata is not None:
                suggestion.extra_metadata = request.metadata

            await self.db.commit()
            await self.db.refresh(suggestion)

            logger.info(f"Updated suggestion {suggestion_id}")
            return self._model_to_schema(suggestion)

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to update suggestion: {e}")
            raise wrap_error(
                e, DryadErrorCode.BRANCH_UPDATE_FAILED,
                "Failed to update suggestion",
                {"suggestion_id": suggestion_id}
            )

    async def delete_suggestion(
        self,
        suggestion_id: str,
        reason: Optional[str] = None
    ) -> DeleteSuggestionResponse:
        """Delete a suggestion."""
        try:
            # Get suggestion
            stmt = select(BranchSuggestion).where(BranchSuggestion.id == suggestion_id)
            result = await self.db.execute(stmt)
            suggestion = result.scalar_one_or_none()

            if not suggestion:
                raise NotFoundError("Suggestion", suggestion_id)

            # Delete suggestion
            await self.db.delete(suggestion)
            await self.db.commit()

            logger.info(f"Deleted suggestion {suggestion_id}" + (f" - Reason: {reason}" if reason else ""))

            return DeleteSuggestionResponse(
                suggestion_id=suggestion_id,
                success=True,
                message="Suggestion deleted successfully"
            )

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to delete suggestion: {e}")
            raise wrap_error(
                e, DryadErrorCode.BRANCH_DELETION_FAILED,
                "Failed to delete suggestion",
                {"suggestion_id": suggestion_id}
            )

    async def get_suggestion_by_id(
        self,
        suggestion_id: str
    ) -> BranchSuggestionSchema:
        """Get a suggestion by ID."""
        try:
            stmt = select(BranchSuggestion).where(BranchSuggestion.id == suggestion_id)
            result = await self.db.execute(stmt)
            suggestion = result.scalar_one_or_none()

            if not suggestion:
                raise NotFoundError("Suggestion", suggestion_id)

            return self._model_to_schema(suggestion)

        except Exception as e:
            logger.error(f"Failed to get suggestion: {e}")
            raise

