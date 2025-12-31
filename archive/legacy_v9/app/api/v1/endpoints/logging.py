"""
Logging API Endpoints

FastAPI router for structured logging service.
"""

from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.database import get_async_db
from app.services.logging.models import SystemLog
from app.services.logging.schemas import (
    LogEntry,
    LogEntryCreate,
    LogLevel,
    LogListResponse,
    LogQueryParams,
)
from app.services.logging.query_service import LogQueryService

router = APIRouter(prefix="/logs", tags=["Logging"])


def get_log_query_service(
    db: AsyncSession = Depends(get_async_db),
) -> LogQueryService:
    """Dependency for log query service."""
    return LogQueryService(db)


@router.post(
    "",
    response_model=LogEntry,
    status_code=status.HTTP_201_CREATED,
    summary="Write log entry",
    description="Write a structured log entry to the system logs",
)
async def write_log(
    log_data: LogEntryCreate,
    db: AsyncSession = Depends(get_async_db),
) -> LogEntry:
    """
    Write a structured log entry.
    
    Args:
        log_data: Log entry data
        db: Database session
        
    Returns:
        Created log entry
    """
    # Create log entry
    log_entry = SystemLog(
        level=log_data.level.value,
        component=log_data.component,
        event_type=log_data.event_type,
        message=log_data.message,
        log_metadata=log_data.metadata,
        trace_id=log_data.trace_id,
        span_id=log_data.span_id,
        agent_id=log_data.agent_id,
        task_id=log_data.task_id,
    )
    
    db.add(log_entry)
    await db.commit()
    await db.refresh(log_entry)
    
    return LogEntry(
        log_id=log_entry.log_id,
        timestamp=log_entry.timestamp,
        level=LogLevel(log_entry.level),
        component=log_entry.component,
        event_type=log_entry.event_type,
        message=log_entry.message,
        metadata=log_entry.log_metadata,
        trace_id=log_entry.trace_id,
        span_id=log_entry.span_id,
        agent_id=log_entry.agent_id,
        task_id=log_entry.task_id,
    )


@router.get(
    "",
    response_model=LogListResponse,
    summary="Query logs",
    description="Query structured logs with filtering and pagination",
)
async def query_logs(
    start_time: Annotated[datetime | None, Query(description="Start time filter")] = None,
    end_time: Annotated[datetime | None, Query(description="End time filter")] = None,
    level: Annotated[LogLevel | None, Query(description="Log level filter")] = None,
    component: Annotated[str | None, Query(description="Component filter")] = None,
    event_type: Annotated[str | None, Query(description="Event type filter")] = None,
    agent_id: Annotated[str | None, Query(description="Agent ID filter")] = None,
    task_id: Annotated[str | None, Query(description="Task ID filter")] = None,
    trace_id: Annotated[str | None, Query(description="Trace ID filter")] = None,
    limit: Annotated[int, Query(ge=1, le=1000, description="Maximum results")] = 100,
    offset: Annotated[int, Query(ge=0, description="Offset for pagination")] = 0,
    service: LogQueryService = Depends(get_log_query_service),
) -> LogListResponse:
    """
    Query structured logs with filtering and pagination.
    
    Args:
        start_time: Filter logs after this time
        end_time: Filter logs before this time
        level: Filter by log level
        component: Filter by component name
        event_type: Filter by event type
        agent_id: Filter by agent ID
        task_id: Filter by task ID
        trace_id: Filter by trace ID
        limit: Maximum number of results (1-1000)
        offset: Offset for pagination
        service: Log query service
        
    Returns:
        Paginated list of log entries
    """
    params = LogQueryParams(
        start_time=start_time,
        end_time=end_time,
        level=level,
        component=component,
        event_type=event_type,
        agent_id=agent_id,
        task_id=task_id,
        trace_id=trace_id,
        limit=limit,
        offset=offset,
    )
    
    return await service.query_logs(params)


@router.get(
    "/{log_id}",
    response_model=LogEntry,
    summary="Get log by ID",
    description="Get a specific log entry by ID",
)
async def get_log(
    log_id: int,
    service: LogQueryService = Depends(get_log_query_service),
) -> LogEntry:
    """
    Get a specific log entry by ID.
    
    Args:
        log_id: Log entry ID
        service: Log query service
        
    Returns:
        Log entry
        
    Raises:
        HTTPException: If log not found
    """
    from fastapi import HTTPException
    
    log_entry = await service.get_log_by_id(log_id)
    
    if not log_entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Log entry {log_id} not found",
        )
    
    return log_entry


@router.get(
    "/trace/{trace_id}",
    response_model=list[LogEntry],
    summary="Get logs by trace ID",
    description="Get all logs for a distributed trace",
)
async def get_trace_logs(
    trace_id: str,
    service: LogQueryService = Depends(get_log_query_service),
) -> list[LogEntry]:
    """
    Get all logs for a distributed trace.
    
    Args:
        trace_id: Distributed trace ID
        service: Log query service
        
    Returns:
        List of log entries for the trace
    """
    return await service.get_trace_logs(trace_id)


@router.get(
    "/stats/{component}",
    response_model=dict[str, int],
    summary="Get component statistics",
    description="Get log statistics for a component",
)
async def get_component_stats(
    component: str,
    start_time: Annotated[datetime | None, Query(description="Start time filter")] = None,
    end_time: Annotated[datetime | None, Query(description="End time filter")] = None,
    service: LogQueryService = Depends(get_log_query_service),
) -> dict[str, int]:
    """
    Get log statistics for a component.
    
    Args:
        component: Component name
        start_time: Optional start time filter
        end_time: Optional end time filter
        service: Log query service
        
    Returns:
        Dictionary with log counts by level
    """
    return await service.get_component_stats(component, start_time, end_time)

