# app/services/analytics_service.py
import logging
import hashlib
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, and_, or_
from datetime import datetime, timedelta

from app.database.models import Document, DocumentAnalytics, SearchAnalytics, UserEngagement

logger = logging.getLogger(__name__)

class AnalyticsService:
    """Service for document analytics and usage tracking."""
    
    @staticmethod
    async def track_document_view(
        db: AsyncSession,
        document_id: str,
        user_session: str,
        duration_seconds: Optional[float] = None
    ):
        """Track a document view event."""
        try:
            # Update document analytics
            analytics = await AnalyticsService._get_or_create_document_analytics(db, document_id)
            analytics.view_count += 1
            
            if duration_seconds:
                # Update average time spent
                total_time = analytics.avg_time_spent * (analytics.view_count - 1) + duration_seconds
                analytics.avg_time_spent = total_time / analytics.view_count
            
            # Track user engagement
            engagement = UserEngagement(
                user_session=user_session,
                action_type="view",
                resource_type="document",
                resource_id=document_id,
                duration_seconds=duration_seconds
            )
            db.add(engagement)
            
            await db.commit()
            logger.info(f"Tracked document view: {document_id}")
            
        except Exception as e:
            logger.error(f"Failed to track document view: {e}")
            await db.rollback()
    
    @staticmethod
    async def track_search_query(
        db: AsyncSession,
        query: str,
        search_type: str,
        results_count: int,
        results_returned: int,
        execution_time_ms: float,
        user_session: Optional[str] = None,
        filters_applied: Optional[Dict[str, Any]] = None
    ) -> str:
        """Track a search query and return search analytics ID."""
        try:
            query_hash = hashlib.sha256(query.encode()).hexdigest()
            
            search_analytics = SearchAnalytics(
                query=query,
                query_hash=query_hash,
                search_type=search_type,
                results_count=results_count,
                results_returned=results_returned,
                execution_time_ms=execution_time_ms,
                user_session=user_session,
                filters_applied=filters_applied
            )
            
            db.add(search_analytics)
            
            # Track user engagement
            if user_session:
                engagement = UserEngagement(
                    user_session=user_session,
                    action_type="search",
                    resource_type="search",
                    resource_id=search_analytics.id,
                    context_data={
                        "query": query,
                        "search_type": search_type,
                        "results_count": results_count
                    }
                )
                db.add(engagement)
            
            await db.commit()
            logger.info(f"Tracked search query: {query[:50]}")
            return search_analytics.id
            
        except Exception as e:
            logger.error(f"Failed to track search query: {e}")
            await db.rollback()
            return ""
    
    @staticmethod
    async def track_search_click(
        db: AsyncSession,
        search_analytics_id: str,
        document_id: str,
        user_session: Optional[str] = None
    ):
        """Track when a user clicks on a search result."""
        try:
            # Update search analytics
            search_analytics = await db.get(SearchAnalytics, search_analytics_id)
            if search_analytics:
                if not search_analytics.clicked_results:
                    search_analytics.clicked_results = []
                search_analytics.clicked_results.append(document_id)
            
            # Update document analytics
            doc_analytics = await AnalyticsService._get_or_create_document_analytics(db, document_id)
            doc_analytics.search_count += 1
            
            # Track user engagement
            if user_session:
                engagement = UserEngagement(
                    user_session=user_session,
                    action_type="search_click",
                    resource_type="document",
                    resource_id=document_id,
                    context_data={"search_analytics_id": search_analytics_id}
                )
                db.add(engagement)
            
            await db.commit()
            logger.info(f"Tracked search click: {document_id}")
            
        except Exception as e:
            logger.error(f"Failed to track search click: {e}")
            await db.rollback()
    
    @staticmethod
    async def get_document_analytics(
        db: AsyncSession,
        document_id: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get document analytics data."""
        try:
            query = select(
                DocumentAnalytics,
                Document.title,
                Document.content_type,
                Document.created_at
            ).join(Document)
            
            if document_id:
                query = query.where(DocumentAnalytics.document_id == document_id)
            
            query = query.order_by(desc(DocumentAnalytics.view_count)).limit(limit)
            
            result = await db.execute(query)
            rows = result.all()
            
            analytics_data = []
            for analytics, title, content_type, created_at in rows:
                analytics_data.append({
                    "document_id": analytics.document_id,
                    "title": title,
                    "content_type": content_type,
                    "view_count": analytics.view_count,
                    "search_count": analytics.search_count,
                    "download_count": analytics.download_count,
                    "share_count": analytics.share_count,
                    "avg_time_spent": analytics.avg_time_spent,
                    "bounce_rate": analytics.bounce_rate,
                    "avg_search_rank": analytics.avg_search_rank,
                    "click_through_rate": analytics.click_through_rate,
                    "created_at": created_at.isoformat() if created_at else None,
                    "last_updated": analytics.updated_at.isoformat() if analytics.updated_at else None
                })
            
            return analytics_data
            
        except Exception as e:
            logger.error(f"Failed to get document analytics: {e}")
            return []
    
    @staticmethod
    async def get_search_analytics(
        db: AsyncSession,
        days: int = 30,
        limit: int = 100
    ) -> Dict[str, Any]:
        """Get search analytics data."""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            # Get popular queries
            popular_queries = await db.execute(
                select(
                    SearchAnalytics.query,
                    func.count(SearchAnalytics.id).label('count'),
                    func.avg(SearchAnalytics.execution_time_ms).label('avg_time'),
                    func.avg(SearchAnalytics.results_count).label('avg_results')
                )
                .where(SearchAnalytics.created_at >= cutoff_date)
                .group_by(SearchAnalytics.query)
                .order_by(desc('count'))
                .limit(limit)
            )
            
            popular_queries_data = []
            for row in popular_queries:
                popular_queries_data.append({
                    "query": row.query,
                    "search_count": row.count,
                    "avg_execution_time_ms": round(row.avg_time, 2),
                    "avg_results_count": round(row.avg_results, 2)
                })
            
            # Get search type distribution
            search_types = await db.execute(
                select(
                    SearchAnalytics.search_type,
                    func.count(SearchAnalytics.id).label('count')
                )
                .where(SearchAnalytics.created_at >= cutoff_date)
                .group_by(SearchAnalytics.search_type)
            )
            
            search_type_data = {row.search_type: row.count for row in search_types}
            
            # Get daily search volume
            daily_searches = await db.execute(
                select(
                    func.date(SearchAnalytics.created_at).label('date'),
                    func.count(SearchAnalytics.id).label('count')
                )
                .where(SearchAnalytics.created_at >= cutoff_date)
                .group_by(func.date(SearchAnalytics.created_at))
                .order_by('date')
            )
            
            daily_search_data = []
            for row in daily_searches:
                daily_search_data.append({
                    "date": row.date.isoformat() if row.date else None,
                    "search_count": row.count
                })
            
            return {
                "popular_queries": popular_queries_data,
                "search_type_distribution": search_type_data,
                "daily_search_volume": daily_search_data,
                "period_days": days
            }
            
        except Exception as e:
            logger.error(f"Failed to get search analytics: {e}")
            return {}
    
    @staticmethod
    async def get_user_engagement_metrics(
        db: AsyncSession,
        days: int = 30
    ) -> Dict[str, Any]:
        """Get user engagement metrics."""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            # Get action type distribution
            actions = await db.execute(
                select(
                    UserEngagement.action_type,
                    func.count(UserEngagement.id).label('count')
                )
                .where(UserEngagement.created_at >= cutoff_date)
                .group_by(UserEngagement.action_type)
            )
            
            action_data = {row.action_type: row.count for row in actions}
            
            # Get unique sessions
            unique_sessions = await db.execute(
                select(func.count(func.distinct(UserEngagement.user_session)))
                .where(UserEngagement.created_at >= cutoff_date)
            )
            
            session_count = unique_sessions.scalar() or 0
            
            # Get average session duration
            avg_duration = await db.execute(
                select(func.avg(UserEngagement.duration_seconds))
                .where(
                    and_(
                        UserEngagement.created_at >= cutoff_date,
                        UserEngagement.duration_seconds.isnot(None)
                    )
                )
            )
            
            avg_duration_value = avg_duration.scalar() or 0.0
            
            return {
                "action_distribution": action_data,
                "unique_sessions": session_count,
                "avg_session_duration_seconds": round(avg_duration_value, 2),
                "period_days": days
            }
            
        except Exception as e:
            logger.error(f"Failed to get user engagement metrics: {e}")
            return {}
    
    @staticmethod
    async def _get_or_create_document_analytics(
        db: AsyncSession,
        document_id: str
    ) -> DocumentAnalytics:
        """Get or create document analytics record."""
        analytics = await db.execute(
            select(DocumentAnalytics).where(DocumentAnalytics.document_id == document_id)
        )
        analytics_obj = analytics.scalar_one_or_none()
        
        if not analytics_obj:
            analytics_obj = DocumentAnalytics(document_id=document_id)
            db.add(analytics_obj)
        
        return analytics_obj
