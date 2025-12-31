"""
Log Query Service

High-performance log querying with filtering and pagination.
"""

from datetime import datetime

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from .models import SystemLog
from .schemas import LogEntry, LogQueryParams, LogListResponse, LogLevel


class LogQueryService:
    """
    Service for querying structured logs.
    
    Provides efficient filtering, pagination, and aggregation
    of log entries with proper indexing.
    """
    
    def __init__(self, db: AsyncSession):
        """
        Initialize log query service.
        
        Args:
            db: Database session
        """
        self.db = db
    
    async def query_logs(
        self,
        params: LogQueryParams,
    ) -> LogListResponse:
        """
        Query logs with filtering and pagination.
        
        Args:
            params: Query parameters (filters, pagination)
            
        Returns:
            Paginated list of log entries with total count
        """
        # Build base query
        query = select(SystemLog)
        
        # Apply filters
        if params.start_time:
            query = query.where(SystemLog.timestamp >= params.start_time)
        
        if params.end_time:
            query = query.where(SystemLog.timestamp <= params.end_time)
        
        if params.level:
            query = query.where(SystemLog.level == params.level.value)
        
        if params.component:
            query = query.where(SystemLog.component == params.component)
        
        if params.event_type:
            query = query.where(SystemLog.event_type == params.event_type)
        
        if params.agent_id:
            query = query.where(SystemLog.agent_id == params.agent_id)
        
        if params.task_id:
            query = query.where(SystemLog.task_id == params.task_id)
        
        if params.trace_id:
            query = query.where(SystemLog.trace_id == params.trace_id)
        
        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        result = await self.db.execute(count_query)
        total = result.scalar_one()
        
        # Apply ordering (reverse chronological)
        query = query.order_by(SystemLog.timestamp.desc())
        
        # Apply pagination
        query = query.limit(params.limit).offset(params.offset)
        
        # Execute query
        result = await self.db.execute(query)
        logs = result.scalars().all()
        
        # Convert to response schema
        log_entries = [
            LogEntry(
                log_id=log.log_id,
                timestamp=log.timestamp,
                level=LogLevel(log.level),
                component=log.component,
                event_type=log.event_type,
                message=log.message,
                metadata=log.log_metadata,
                trace_id=log.trace_id,
                span_id=log.span_id,
                agent_id=log.agent_id,
                task_id=log.task_id,
            )
            for log in logs
        ]
        
        return LogListResponse(
            logs=log_entries,
            total=total,
            limit=params.limit,
            offset=params.offset,
        )
    
    async def get_log_by_id(self, log_id: int) -> LogEntry | None:
        """
        Get a specific log entry by ID.
        
        Args:
            log_id: Log entry ID
            
        Returns:
            Log entry if found, None otherwise
        """
        result = await self.db.execute(
            select(SystemLog).where(SystemLog.log_id == log_id)
        )
        log = result.scalar_one_or_none()
        
        if not log:
            return None
        
        return LogEntry(
            log_id=log.log_id,
            timestamp=log.timestamp,
            level=LogLevel(log.level),
            component=log.component,
            event_type=log.event_type,
            message=log.message,
            metadata=log.log_metadata,
            trace_id=log.trace_id,
            span_id=log.span_id,
            agent_id=log.agent_id,
            task_id=log.task_id,
        )
    
    async def get_trace_logs(self, trace_id: str) -> list[LogEntry]:
        """
        Get all logs for a distributed trace.
        
        Args:
            trace_id: Distributed trace ID
            
        Returns:
            List of log entries for the trace, ordered by timestamp
        """
        result = await self.db.execute(
            select(SystemLog)
            .where(SystemLog.trace_id == trace_id)
            .order_by(SystemLog.timestamp.asc())
        )
        logs = result.scalars().all()
        
        return [
            LogEntry(
                log_id=log.log_id,
                timestamp=log.timestamp,
                level=LogLevel(log.level),
                component=log.component,
                event_type=log.event_type,
                message=log.message,
                metadata=log.log_metadata,
                trace_id=log.trace_id,
                span_id=log.span_id,
                agent_id=log.agent_id,
                task_id=log.task_id,
            )
            for log in logs
        ]
    
    async def get_component_stats(
        self,
        component: str,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
    ) -> dict[str, int]:
        """
        Get log statistics for a component.
        
        Args:
            component: Component name
            start_time: Optional start time filter
            end_time: Optional end time filter
            
        Returns:
            Dictionary with log counts by level
        """
        query = select(
            SystemLog.level,
            func.count(SystemLog.log_id).label("count"),
        ).where(SystemLog.component == component)
        
        if start_time:
            query = query.where(SystemLog.timestamp >= start_time)
        
        if end_time:
            query = query.where(SystemLog.timestamp <= end_time)
        
        query = query.group_by(SystemLog.level)
        
        result = await self.db.execute(query)
        rows = result.all()
        
        return {row.level: row.count for row in rows}

