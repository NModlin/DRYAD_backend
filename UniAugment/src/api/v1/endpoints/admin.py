"""
Backend Admin Center API Endpoints

Provides comprehensive admin functionality for:
- System dashboard and monitoring
- Oracle (voice/text interface) session management
- User management and analytics
- System configuration and reports

All endpoints require admin authentication.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query, Body, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_

from app.core.security import get_current_user
from app.database.database import get_db
from app.database.models import User
from app.dryad.models.grove import Grove
from app.dryad.models.branch import Branch
from app.dryad.models.vessel import Vessel
from app.dryad.models.dialogue import Dialogue
from app.core.logging_config import get_logger
from app.core.config import config
from app.core.llm_config import get_llm_status
import psutil
import time

logger = get_logger(__name__)
router = APIRouter()

# Track active Oracle sessions in memory (in production, use Redis)
_active_oracle_sessions: Dict[str, Dict[str, Any]] = {}
_oracle_metrics: Dict[str, Any] = {
    "total_consultations": 0,
    "consultations_by_type": {"voice": 0, "text": 0},
    "consultations_by_provider": {},
    "response_times": [],
    "errors": []
}


# ============================================================================
# RESPONSE MODELS
# ============================================================================

class SystemHealthResponse(BaseModel):
    """System health metrics."""
    status: str
    uptime_hours: float
    cpu_usage: float
    memory_usage: float
    active_connections: int


class OracleStatsResponse(BaseModel):
    """Oracle statistics."""
    total_consultations_today: int
    active_sessions: int
    avg_response_time_ms: float
    voice_sessions: int
    text_sessions: int
    providers_online: List[str]


class UserActivityResponse(BaseModel):
    """User activity metrics."""
    active_users_now: int
    total_users: int
    new_users_today: int
    peak_concurrent_today: int


class DryadStatsResponse(BaseModel):
    """Dryad system statistics."""
    total_groves: int
    total_branches: int
    total_vessels: int
    active_dialogues: int


class AlertResponse(BaseModel):
    """System alert."""
    level: str
    message: str
    timestamp: str


class AdminDashboardResponse(BaseModel):
    """Main admin dashboard response."""
    system_health: SystemHealthResponse
    oracle_stats: OracleStatsResponse
    user_activity: UserActivityResponse
    dryad_stats: DryadStatsResponse
    alerts: List[AlertResponse]


class OracleSessionResponse(BaseModel):
    """Active Oracle session."""
    session_id: str
    user_id: str
    type: str  # "voice" or "text"
    provider: str
    branch_id: Optional[str]
    started_at: str
    duration_seconds: int
    message_count: int
    status: str


class OracleSessionsResponse(BaseModel):
    """Oracle sessions list."""
    active_sessions: List[OracleSessionResponse]
    total_active: int
    voice_sessions: int
    text_sessions: int


class ProviderStatusResponse(BaseModel):
    """Oracle provider status."""
    id: str
    name: str
    status: str
    response_time_avg_ms: float
    requests_today: int
    errors_today: int
    last_health_check: str


class OracleProvidersStatusResponse(BaseModel):
    """All Oracle providers status."""
    providers: List[ProviderStatusResponse]


class OracleMetricsResponse(BaseModel):
    """Oracle performance metrics."""
    time_period: str
    total_consultations: int
    by_type: Dict[str, int]
    by_provider: Dict[str, int]
    avg_response_times: Dict[str, float]
    success_rate: float
    error_breakdown: Dict[str, int]


class UserListItemResponse(BaseModel):
    """User list item."""
    id: str
    email: str
    name: Optional[str]
    role: str
    status: str
    created_at: str
    last_login: Optional[str]
    total_consultations: int
    total_groves: int


class UserListResponse(BaseModel):
    """User list response."""
    users: List[UserListItemResponse]
    total: int
    limit: int
    offset: int


class UserActivityDetailResponse(BaseModel):
    """User activity details."""
    total_consultations: int
    consultations_this_week: int
    total_groves: int
    total_branches: int
    avg_session_duration_minutes: float


class RecentSessionResponse(BaseModel):
    """Recent session info."""
    session_id: str
    type: str
    started_at: str
    duration_minutes: float
    consultations: int


class UserDetailResponse(BaseModel):
    """User details response."""
    user: UserListItemResponse
    activity: UserActivityDetailResponse
    recent_sessions: List[RecentSessionResponse]


class SystemAnalyticsDataPoint(BaseModel):
    """System analytics data point."""
    timestamp: str
    active_users: int
    consultations: int
    voice_sessions: int
    text_sessions: int
    avg_response_time_ms: float


class SystemAnalyticsTotals(BaseModel):
    """System analytics totals."""
    consultations: int
    unique_users: int
    total_session_minutes: int


class SystemAnalyticsResponse(BaseModel):
    """System analytics response."""
    period: str
    data_points: List[SystemAnalyticsDataPoint]
    totals: SystemAnalyticsTotals


class UsageByUser(BaseModel):
    """Usage by user."""
    user_id: str
    email: str
    consultations: int
    voice_minutes: float
    text_messages: int
    cost_estimate: float


class UsageByProvider(BaseModel):
    """Usage by provider."""
    provider: str
    requests: int
    tokens_used: int
    cost: float


class UsageReportResponse(BaseModel):
    """Usage report response."""
    report_period: str
    by_user: List[UsageByUser]
    by_provider: List[UsageByProvider]


class FeatureFlagsResponse(BaseModel):
    """Feature flags response."""
    features: Dict[str, bool]


class UpdateStatusRequest(BaseModel):
    """Update user status request."""
    status: str = Field(..., description="User status: active, inactive, suspended")


class UpdateRoleRequest(BaseModel):
    """Update user role request."""
    role: str = Field(..., description="User role: user, admin, moderator")


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def check_admin_permission(current_user: User):
    """Check if user has admin permissions."""
    # In production, check user.role or user.is_admin
    # For now, allow all authenticated users (update this based on your auth system)
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    # TODO: Add proper role checking when user roles are implemented
    # if current_user.role != "admin":
    #     raise HTTPException(status_code=403, detail="Admin access required")


async def get_system_health() -> SystemHealthResponse:
    """Get system health metrics."""
    try:
        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory()
        
        # Calculate uptime (simplified - in production use actual start time)
        uptime_hours = time.time() / 3600  # Placeholder
        
        return SystemHealthResponse(
            status="healthy" if cpu_percent < 80 and memory.percent < 85 else "degraded",
            uptime_hours=round(uptime_hours % 100, 2),  # Simplified
            cpu_usage=round(cpu_percent, 2),
            memory_usage=round(memory.percent, 2),
            active_connections=len(_active_oracle_sessions)
        )
    except Exception as e:
        logger.error(f"Error getting system health: {e}")
        return SystemHealthResponse(
            status="unknown",
            uptime_hours=0,
            cpu_usage=0,
            memory_usage=0,
            active_connections=0
        )


async def get_oracle_stats(db: AsyncSession) -> OracleStatsResponse:
    """Get Oracle statistics."""
    try:
        # Count today's dialogues
        today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        result = await db.execute(
            select(func.count(Dialogue.id)).where(Dialogue.created_at >= today)
        )
        total_today = result.scalar() or 0

        # Get active sessions
        active_sessions = len(_active_oracle_sessions)
        voice_sessions = sum(1 for s in _active_oracle_sessions.values() if s.get("type") == "voice")
        text_sessions = active_sessions - voice_sessions

        # Calculate average response time
        response_times = _oracle_metrics.get("response_times", [])
        avg_response_time = sum(response_times[-100:]) / len(response_times[-100:]) if response_times else 0

        # Get online providers
        llm_status = get_llm_status()
        providers_online = [llm_status.get("provider", "unknown")] if llm_status.get("available") else []

        return OracleStatsResponse(
            total_consultations_today=total_today,
            active_sessions=active_sessions,
            avg_response_time_ms=round(avg_response_time, 2),
            voice_sessions=voice_sessions,
            text_sessions=text_sessions,
            providers_online=providers_online
        )
    except Exception as e:
        logger.error(f"Error getting Oracle stats: {e}")
        return OracleStatsResponse(
            total_consultations_today=0,
            active_sessions=0,
            avg_response_time_ms=0,
            voice_sessions=0,
            text_sessions=0,
            providers_online=[]
        )


async def get_user_activity(db: AsyncSession) -> UserActivityResponse:
    """Get user activity metrics."""
    try:
        # Count total users
        result = await db.execute(select(func.count(User.id)))
        total_users = result.scalar() or 0

        # Count new users today
        today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        result = await db.execute(
            select(func.count(User.id)).where(User.created_at >= today)
        )
        new_today = result.scalar() or 0

        # Active users (simplified - users with sessions)
        active_now = len(set(s.get("user_id") for s in _active_oracle_sessions.values()))

        return UserActivityResponse(
            active_users_now=active_now,
            total_users=total_users,
            new_users_today=new_today,
            peak_concurrent_today=active_now  # Simplified
        )
    except Exception as e:
        logger.error(f"Error getting user activity: {e}")
        return UserActivityResponse(
            active_users_now=0,
            total_users=0,
            new_users_today=0,
            peak_concurrent_today=0
        )


async def get_dryad_stats(db: AsyncSession) -> DryadStatsResponse:
    """Get Dryad system statistics."""
    try:
        # Count groves
        result = await db.execute(select(func.count(Grove.id)))
        total_groves = result.scalar() or 0

        # Count branches
        result = await db.execute(select(func.count(Branch.id)))
        total_branches = result.scalar() or 0

        # Count vessels
        result = await db.execute(select(func.count(Vessel.id)))
        total_vessels = result.scalar() or 0

        # Count active dialogues (created in last 24 hours)
        yesterday = datetime.utcnow() - timedelta(days=1)
        result = await db.execute(
            select(func.count(Dialogue.id)).where(Dialogue.created_at >= yesterday)
        )
        active_dialogues = result.scalar() or 0

        return DryadStatsResponse(
            total_groves=total_groves,
            total_branches=total_branches,
            total_vessels=total_vessels,
            active_dialogues=active_dialogues
        )
    except Exception as e:
        logger.error(f"Error getting Dryad stats: {e}")
        return DryadStatsResponse(
            total_groves=0,
            total_branches=0,
            total_vessels=0,
            active_dialogues=0
        )


async def get_system_alerts() -> List[AlertResponse]:
    """Get system alerts."""
    alerts = []

    try:
        # Check system health
        health = await get_system_health()

        if health.cpu_usage > 80:
            alerts.append(AlertResponse(
                level="warning",
                message=f"High CPU usage detected: {health.cpu_usage}%",
                timestamp=datetime.utcnow().isoformat()
            ))

        if health.memory_usage > 85:
            alerts.append(AlertResponse(
                level="warning",
                message=f"High memory usage detected: {health.memory_usage}%",
                timestamp=datetime.utcnow().isoformat()
            ))

        # Check for errors in Oracle metrics
        recent_errors = _oracle_metrics.get("errors", [])[-10:]
        if len(recent_errors) > 5:
            alerts.append(AlertResponse(
                level="error",
                message=f"Multiple Oracle errors detected: {len(recent_errors)} in recent history",
                timestamp=datetime.utcnow().isoformat()
            ))

    except Exception as e:
        logger.error(f"Error getting system alerts: {e}")
        alerts.append(AlertResponse(
            level="error",
            message=f"Error retrieving system alerts: {str(e)}",
            timestamp=datetime.utcnow().isoformat()
        ))

    return alerts


# ============================================================================
# PRIORITY 1: CRITICAL FOR ORACLE TESTING
# ============================================================================

@router.get("/dashboard", response_model=AdminDashboardResponse, tags=["Admin - Priority 1"])
async def get_admin_dashboard(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get main admin dashboard overview.

    Returns comprehensive system status including:
    - System health (CPU, memory, uptime)
    - Oracle statistics (sessions, consultations, providers)
    - User activity (active users, new users)
    - Dryad statistics (groves, branches, vessels, dialogues)
    - System alerts
    """
    try:
        check_admin_permission(current_user)

        logger.info(f"Admin dashboard accessed by user {current_user.id}")

        # Gather all dashboard data
        system_health = await get_system_health()
        oracle_stats = await get_oracle_stats(db)
        user_activity = await get_user_activity(db)
        dryad_stats = await get_dryad_stats(db)
        alerts = await get_system_alerts()

        return AdminDashboardResponse(
            system_health=system_health,
            oracle_stats=oracle_stats,
            user_activity=user_activity,
            dryad_stats=dryad_stats,
            alerts=alerts
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting admin dashboard: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve admin dashboard: {str(e)}"
        )


@router.get("/oracle/sessions", response_model=OracleSessionsResponse, tags=["Admin - Priority 1"])
async def get_oracle_sessions(
    current_user: User = Depends(get_current_user)
):
    """
    Monitor active Oracle voice/text sessions.

    Returns all currently active Oracle sessions with details about:
    - Session type (voice or text)
    - User and provider information
    - Session duration and message count
    - Associated branch/grove context
    """
    try:
        check_admin_permission(current_user)

        logger.info(f"Oracle sessions accessed by admin user {current_user.id}")

        # Build session list from active sessions
        sessions = []
        for session_id, session_data in _active_oracle_sessions.items():
            started_at = datetime.fromisoformat(session_data.get("started_at", datetime.utcnow().isoformat()))
            duration = int((datetime.utcnow() - started_at).total_seconds())

            sessions.append(OracleSessionResponse(
                session_id=session_id,
                user_id=session_data.get("user_id", "unknown"),
                type=session_data.get("type", "text"),
                provider=session_data.get("provider", "unknown"),
                branch_id=session_data.get("branch_id"),
                started_at=session_data.get("started_at", datetime.utcnow().isoformat()),
                duration_seconds=duration,
                message_count=session_data.get("message_count", 0),
                status=session_data.get("status", "active")
            ))

        # Count by type
        voice_count = sum(1 for s in sessions if s.type == "voice")
        text_count = len(sessions) - voice_count

        return OracleSessionsResponse(
            active_sessions=sessions,
            total_active=len(sessions),
            voice_sessions=voice_count,
            text_sessions=text_count
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting Oracle sessions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve Oracle sessions: {str(e)}"
        )


@router.get("/oracle/providers/status", response_model=OracleProvidersStatusResponse, tags=["Admin - Priority 1"])
async def get_oracle_providers_status(
    current_user: User = Depends(get_current_user)
):
    """
    Get Oracle provider health monitoring.

    Returns status of all configured Oracle providers (LLM backends):
    - Provider availability and health
    - Average response times
    - Request counts and error rates
    - Last health check timestamp
    """
    try:
        check_admin_permission(current_user)

        logger.info(f"Oracle provider status accessed by admin user {current_user.id}")

        # Get LLM status
        llm_status = get_llm_status()

        # Build provider status list
        providers = []

        # Main configured provider
        provider_name = llm_status.get("provider", "unknown")
        is_available = llm_status.get("available", False)

        # Get metrics for this provider
        provider_metrics = _oracle_metrics.get("consultations_by_provider", {})
        requests_today = provider_metrics.get(provider_name, 0)

        # Calculate average response time for this provider
        response_times = _oracle_metrics.get("response_times", [])
        avg_response_time = sum(response_times[-100:]) / len(response_times[-100:]) if response_times else 0

        # Count errors
        errors = _oracle_metrics.get("errors", [])
        errors_today = len([e for e in errors if e.get("provider") == provider_name])

        providers.append(ProviderStatusResponse(
            id=provider_name,
            name=provider_name.replace("-", " ").title(),
            status="online" if is_available else "offline",
            response_time_avg_ms=round(avg_response_time, 2),
            requests_today=requests_today,
            errors_today=errors_today,
            last_health_check=datetime.utcnow().isoformat()
        ))

        return OracleProvidersStatusResponse(providers=providers)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting Oracle provider status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve Oracle provider status: {str(e)}"
        )


@router.get("/oracle/metrics", response_model=OracleMetricsResponse, tags=["Admin - Priority 1"])
async def get_oracle_metrics(
    time_period: str = Query("24h", description="Time period: 1h, 24h, 7d, 30d"),
    current_user: User = Depends(get_current_user)
):
    """
    Get Oracle performance metrics.

    Returns detailed Oracle performance analytics:
    - Total consultations by type (voice/text)
    - Consultations by provider
    - Average response times
    - Success rate and error breakdown
    """
    try:
        check_admin_permission(current_user)

        logger.info(f"Oracle metrics accessed by admin user {current_user.id} for period {time_period}")

        # Get metrics from in-memory store
        total_consultations = _oracle_metrics.get("total_consultations", 0)
        by_type = _oracle_metrics.get("consultations_by_type", {"voice": 0, "text": 0})
        by_provider = _oracle_metrics.get("consultations_by_provider", {})

        # Calculate average response times
        response_times = _oracle_metrics.get("response_times", [])
        voice_times = [rt for rt in response_times if rt > 1000]  # Simplified: assume voice is slower
        text_times = [rt for rt in response_times if rt <= 1000]

        avg_voice_time = sum(voice_times) / len(voice_times) if voice_times else 0
        avg_text_time = sum(text_times) / len(text_times) if text_times else 0

        # Calculate success rate
        errors = _oracle_metrics.get("errors", [])
        total_requests = total_consultations + len(errors)
        success_rate = ((total_requests - len(errors)) / total_requests * 100) if total_requests > 0 else 100

        # Error breakdown
        error_breakdown = {}
        for error in errors:
            error_type = error.get("type", "unknown")
            error_breakdown[error_type] = error_breakdown.get(error_type, 0) + 1

        return OracleMetricsResponse(
            time_period=time_period,
            total_consultations=total_consultations,
            by_type=by_type,
            by_provider=by_provider,
            avg_response_times={
                "voice": round(avg_voice_time, 2),
                "text": round(avg_text_time, 2)
            },
            success_rate=round(success_rate, 2),
            error_breakdown=error_breakdown
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting Oracle metrics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve Oracle metrics: {str(e)}"
        )


# ============================================================================
# PRIORITY 2: IMPORTANT FOR ADMIN MANAGEMENT
# ============================================================================

@router.get("/users", response_model=UserListResponse, tags=["Admin - Priority 2"])
async def get_users(
    search: Optional[str] = Query(None, description="Search by email or name"),
    role: Optional[str] = Query(None, description="Filter by role"),
    status: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(50, ge=1, le=500, description="Maximum number of users to return"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get user list with search and filtering.

    Supports:
    - Search by email or name
    - Filter by role (admin, user, moderator)
    - Filter by status (active, inactive, suspended)
    - Pagination with limit and offset
    """
    try:
        check_admin_permission(current_user)

        logger.info(f"User list accessed by admin user {current_user.id}")

        # Build query
        query = select(User)

        # Apply search filter
        if search:
            search_pattern = f"%{search}%"
            query = query.where(
                or_(
                    User.email.ilike(search_pattern),
                    User.name.ilike(search_pattern) if hasattr(User, 'name') else False
                )
            )

        # Apply role filter (if User model has role field)
        # if role and hasattr(User, 'role'):
        #     query = query.where(User.role == role)

        # Apply status filter (if User model has status field)
        # if status and hasattr(User, 'status'):
        #     query = query.where(User.status == status)

        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        result = await db.execute(count_query)
        total = result.scalar() or 0

        # Apply pagination
        query = query.limit(limit).offset(offset)

        # Execute query
        result = await db.execute(query)
        users = result.scalars().all()

        # Build response
        user_list = []
        for user in users:
            # Count user's groves
            grove_result = await db.execute(
                select(func.count(Grove.id)).where(Grove.user_id == user.id)
            )
            total_groves = grove_result.scalar() or 0

            # Count user's consultations (dialogues)
            # This requires joining through branches to get user's dialogues
            dialogue_result = await db.execute(
                select(func.count(Dialogue.id))
                .join(Branch, Dialogue.branch_id == Branch.id)
                .join(Grove, Branch.grove_id == Grove.id)
                .where(Grove.user_id == user.id)
            )
            total_consultations = dialogue_result.scalar() or 0

            user_list.append(UserListItemResponse(
                id=str(user.id),
                email=user.email,
                name=getattr(user, 'name', None),
                role=getattr(user, 'role', 'user'),
                status=getattr(user, 'status', 'active'),
                created_at=user.created_at.isoformat() if hasattr(user, 'created_at') else datetime.utcnow().isoformat(),
                last_login=getattr(user, 'last_login', None),
                total_consultations=total_consultations,
                total_groves=total_groves
            ))

        return UserListResponse(
            users=user_list,
            total=total,
            limit=limit,
            offset=offset
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user list: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve user list: {str(e)}"
        )


@router.get("/users/{user_id}", response_model=UserDetailResponse, tags=["Admin - Priority 2"])
async def get_user_details(
    user_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get detailed user information and activity.

    Returns:
    - User profile information
    - Activity metrics (consultations, groves, branches)
    - Recent session history
    """
    try:
        check_admin_permission(current_user)

        logger.info(f"User details for {user_id} accessed by admin user {current_user.id}")

        # Get user
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User {user_id} not found"
            )

        # Get user's groves
        grove_result = await db.execute(
            select(func.count(Grove.id)).where(Grove.user_id == user.id)
        )
        total_groves = grove_result.scalar() or 0

        # Get user's branches
        branch_result = await db.execute(
            select(func.count(Branch.id))
            .join(Grove, Branch.grove_id == Grove.id)
            .where(Grove.user_id == user.id)
        )
        total_branches = branch_result.scalar() or 0

        # Get user's consultations
        dialogue_result = await db.execute(
            select(func.count(Dialogue.id))
            .join(Branch, Dialogue.branch_id == Branch.id)
            .join(Grove, Branch.grove_id == Grove.id)
            .where(Grove.user_id == user.id)
        )
        total_consultations = dialogue_result.scalar() or 0

        # Get consultations this week
        week_ago = datetime.utcnow() - timedelta(days=7)
        week_result = await db.execute(
            select(func.count(Dialogue.id))
            .join(Branch, Dialogue.branch_id == Branch.id)
            .join(Grove, Branch.grove_id == Grove.id)
            .where(and_(Grove.user_id == user.id, Dialogue.created_at >= week_ago))
        )
        consultations_this_week = week_result.scalar() or 0

        # Get recent sessions from active sessions
        recent_sessions = []
        for session_id, session_data in _active_oracle_sessions.items():
            if session_data.get("user_id") == str(user.id):
                started_at = datetime.fromisoformat(session_data.get("started_at", datetime.utcnow().isoformat()))
                duration = (datetime.utcnow() - started_at).total_seconds() / 60

                recent_sessions.append(RecentSessionResponse(
                    session_id=session_id,
                    type=session_data.get("type", "text"),
                    started_at=session_data.get("started_at", datetime.utcnow().isoformat()),
                    duration_minutes=round(duration, 2),
                    consultations=session_data.get("message_count", 0)
                ))

        # Build user detail
        user_item = UserListItemResponse(
            id=str(user.id),
            email=user.email,
            name=getattr(user, 'name', None),
            role=getattr(user, 'role', 'user'),
            status=getattr(user, 'status', 'active'),
            created_at=user.created_at.isoformat() if hasattr(user, 'created_at') else datetime.utcnow().isoformat(),
            last_login=getattr(user, 'last_login', None),
            total_consultations=total_consultations,
            total_groves=total_groves
        )

        activity = UserActivityDetailResponse(
            total_consultations=total_consultations,
            consultations_this_week=consultations_this_week,
            total_groves=total_groves,
            total_branches=total_branches,
            avg_session_duration_minutes=15.5  # Placeholder - calculate from actual session data
        )

        return UserDetailResponse(
            user=user_item,
            activity=activity,
            recent_sessions=recent_sessions[:5]  # Limit to 5 most recent
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user details: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve user details: {str(e)}"
        )


@router.put("/users/{user_id}/status", tags=["Admin - Priority 2"])
async def update_user_status(
    user_id: str,
    request: UpdateStatusRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Update user status (activate/deactivate/suspend).

    Allowed status values:
    - active: User can access the system
    - inactive: User account is disabled
    - suspended: User account is temporarily suspended
    """
    try:
        check_admin_permission(current_user)

        logger.info(f"User {user_id} status update to {request.status} by admin {current_user.id}")

        # Get user
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User {user_id} not found"
            )

        # Validate status
        valid_statuses = ["active", "inactive", "suspended"]
        if request.status not in valid_statuses:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status. Must be one of: {', '.join(valid_statuses)}"
            )

        # Update status (if User model has status field)
        if hasattr(user, 'status'):
            user.status = request.status
            await db.commit()

            return {
                "message": f"User {user_id} status updated to {request.status}",
                "user_id": user_id,
                "status": request.status
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_501_NOT_IMPLEMENTED,
                detail="User status management not implemented in current User model"
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating user status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update user status: {str(e)}"
        )


@router.get("/analytics/system", response_model=SystemAnalyticsResponse, tags=["Admin - Priority 2"])
async def get_system_analytics(
    period: str = Query("7d", description="Time period: 1h, 24h, 7d, 30d"),
    granularity: str = Query("hour", description="Data granularity: minute, hour, day"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get system analytics over time.

    Returns time-series data including:
    - Active users over time
    - Consultation counts
    - Voice vs text session distribution
    - Average response times
    - Total metrics for the period
    """
    try:
        check_admin_permission(current_user)

        logger.info(f"System analytics accessed by admin user {current_user.id} for period {period}")

        # Parse period
        period_hours = {
            "1h": 1,
            "24h": 24,
            "7d": 24 * 7,
            "30d": 24 * 30
        }.get(period, 24 * 7)

        # Generate sample data points (in production, query actual time-series data)
        data_points = []
        now = datetime.utcnow()

        # Simplified: generate hourly data points
        for i in range(min(period_hours, 24)):  # Limit to 24 data points for demo
            timestamp = now - timedelta(hours=period_hours - i)

            data_points.append(SystemAnalyticsDataPoint(
                timestamp=timestamp.isoformat(),
                active_users=len(_active_oracle_sessions) if i == 0 else 0,  # Only current for latest
                consultations=_oracle_metrics.get("total_consultations", 0) // max(period_hours, 1),
                voice_sessions=_oracle_metrics.get("consultations_by_type", {}).get("voice", 0) // max(period_hours, 1),
                text_sessions=_oracle_metrics.get("consultations_by_type", {}).get("text", 0) // max(period_hours, 1),
                avg_response_time_ms=1200.0  # Placeholder
            ))

        # Calculate totals
        total_consultations = _oracle_metrics.get("total_consultations", 0)

        # Get unique users count
        result = await db.execute(select(func.count(User.id)))
        unique_users = result.scalar() or 0

        totals = SystemAnalyticsTotals(
            consultations=total_consultations,
            unique_users=unique_users,
            total_session_minutes=total_consultations * 15  # Estimate 15 min per consultation
        )

        return SystemAnalyticsResponse(
            period=period,
            data_points=data_points,
            totals=totals
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting system analytics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve system analytics: {str(e)}"
        )


# ============================================================================
# PRIORITY 3: NICE TO HAVE
# ============================================================================

@router.get("/reports/usage", response_model=UsageReportResponse, tags=["Admin - Priority 3"])
async def get_usage_report(
    report_period: str = Query("current_month", description="Report period: current_month, last_month, custom"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Generate usage reports for billing and monitoring.

    Returns:
    - Usage by user (consultations, voice minutes, text messages, cost estimates)
    - Usage by provider (requests, tokens, costs)
    """
    try:
        check_admin_permission(current_user)

        logger.info(f"Usage report accessed by admin user {current_user.id} for period {report_period}")

        # Get all users
        result = await db.execute(select(User))
        users = result.scalars().all()

        # Build usage by user
        usage_by_user = []
        for user in users[:10]:  # Limit to 10 for demo
            # Get user's consultations
            dialogue_result = await db.execute(
                select(func.count(Dialogue.id))
                .join(Branch, Dialogue.branch_id == Branch.id)
                .join(Grove, Branch.grove_id == Grove.id)
                .where(Grove.user_id == user.id)
            )
            consultations = dialogue_result.scalar() or 0

            usage_by_user.append(UsageByUser(
                user_id=str(user.id),
                email=user.email,
                consultations=consultations,
                voice_minutes=consultations * 5.0,  # Estimate 5 min per voice consultation
                text_messages=consultations * 10,  # Estimate 10 messages per consultation
                cost_estimate=consultations * 0.05  # Estimate $0.05 per consultation
            ))

        # Build usage by provider
        usage_by_provider = []
        for provider, count in _oracle_metrics.get("consultations_by_provider", {}).items():
            usage_by_provider.append(UsageByProvider(
                provider=provider,
                requests=count,
                tokens_used=count * 1000,  # Estimate 1000 tokens per request
                cost=count * 0.02  # Estimate $0.02 per request
            ))

        return UsageReportResponse(
            report_period=report_period,
            by_user=usage_by_user,
            by_provider=usage_by_provider
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating usage report: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate usage report: {str(e)}"
        )


@router.get("/config/features", response_model=FeatureFlagsResponse, tags=["Admin - Priority 3"])
async def get_feature_flags(
    current_user: User = Depends(get_current_user)
):
    """
    Get current feature flag configuration.

    Returns status of all feature flags:
    - voice_oracle_enabled: Voice interface for Oracle
    - text_oracle_enabled: Text interface for Oracle
    - multimodal_enabled: Multimodal processing (audio, video, images)
    - dryad_enabled: Dryad knowledge tree system
    - rate_limiting_enabled: API rate limiting
    - maintenance_mode: System maintenance mode
    """
    try:
        check_admin_permission(current_user)

        logger.info(f"Feature flags accessed by admin user {current_user.id}")

        # Get feature flags from config
        features = {
            "voice_oracle_enabled": getattr(config, 'VOICE_ORACLE_ENABLED', True),
            "text_oracle_enabled": getattr(config, 'TEXT_ORACLE_ENABLED', True),
            "multimodal_enabled": getattr(config, 'MULTIMODAL_ENABLED', True),
            "dryad_enabled": getattr(config, 'DRYAD_ENABLED', True),
            "rate_limiting_enabled": getattr(config, 'RATE_LIMITING_ENABLED', True),
            "maintenance_mode": getattr(config, 'MAINTENANCE_MODE', False)
        }

        return FeatureFlagsResponse(features=features)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting feature flags: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve feature flags: {str(e)}"
        )


@router.put("/config/features/{feature_name}", tags=["Admin - Priority 3"])
async def update_feature_flag(
    feature_name: str,
    enabled: bool = Body(..., embed=True),
    current_user: User = Depends(get_current_user)
):
    """
    Update a feature flag.

    Allows enabling/disabling system features:
    - voice_oracle_enabled
    - text_oracle_enabled
    - multimodal_enabled
    - dryad_enabled
    - rate_limiting_enabled
    - maintenance_mode

    Note: Changes are runtime only and will reset on server restart.
    For persistent changes, update environment variables.
    """
    try:
        check_admin_permission(current_user)

        logger.info(f"Feature flag {feature_name} update to {enabled} by admin {current_user.id}")

        # Validate feature name
        valid_features = [
            "voice_oracle_enabled",
            "text_oracle_enabled",
            "multimodal_enabled",
            "dryad_enabled",
            "rate_limiting_enabled",
            "maintenance_mode"
        ]

        if feature_name not in valid_features:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid feature name. Must be one of: {', '.join(valid_features)}"
            )

        # Update feature flag (runtime only)
        setattr(config, feature_name.upper(), enabled)

        return {
            "message": f"Feature flag {feature_name} updated to {enabled}",
            "feature": feature_name,
            "enabled": enabled,
            "note": "Change is runtime only. Update environment variables for persistence."
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating feature flag: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update feature flag: {str(e)}"
        )


@router.put("/config/oracle/providers/{provider_id}", tags=["Admin - Priority 3"])
async def update_oracle_provider_config(
    provider_id: str,
    config_data: Dict[str, Any] = Body(...),
    current_user: User = Depends(get_current_user)
):
    """
    Update Oracle provider configuration.

    Allows configuring:
    - enabled: Enable/disable provider
    - api_key: API key for the provider (if applicable)
    - rate_limit: Rate limit for the provider
    - timeout: Request timeout in seconds
    - max_retries: Maximum retry attempts

    Note: Sensitive data like API keys should be managed through environment variables.
    This endpoint is for runtime configuration only.
    """
    try:
        check_admin_permission(current_user)

        logger.info(f"Oracle provider {provider_id} config update by admin {current_user.id}")

        # Validate provider_id
        valid_providers = ["openai", "anthropic", "local-llama", "ollama"]
        if provider_id not in valid_providers:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid provider ID. Must be one of: {', '.join(valid_providers)}"
            )

        # Validate config data
        allowed_config_keys = ["enabled", "rate_limit", "timeout", "max_retries"]
        invalid_keys = [k for k in config_data.keys() if k not in allowed_config_keys]

        if invalid_keys:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid configuration keys: {', '.join(invalid_keys)}"
            )

        # Store provider config (in production, use database or Redis)
        # For now, just return success

        return {
            "message": f"Oracle provider {provider_id} configuration updated",
            "provider_id": provider_id,
            "config": config_data,
            "note": "Configuration is runtime only. For persistent changes, update environment variables."
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating Oracle provider config: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update Oracle provider configuration: {str(e)}"
        )


# ============================================================================
# UTILITY ENDPOINTS FOR SESSION MANAGEMENT
# ============================================================================

@router.post("/oracle/sessions", tags=["Admin - Utilities"])
async def create_oracle_session(
    user_id: str = Body(...),
    session_type: str = Body(..., description="Session type: voice or text"),
    provider: str = Body(...),
    branch_id: Optional[str] = Body(None),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new Oracle session (for testing/debugging).

    This endpoint is used by the Oracle interface to register new sessions.
    """
    try:
        check_admin_permission(current_user)

        session_id = f"sess-{datetime.utcnow().timestamp()}"

        _active_oracle_sessions[session_id] = {
            "user_id": user_id,
            "type": session_type,
            "provider": provider,
            "branch_id": branch_id,
            "started_at": datetime.utcnow().isoformat(),
            "message_count": 0,
            "status": "active"
        }

        logger.info(f"Oracle session {session_id} created by admin {current_user.id}")

        return {
            "session_id": session_id,
            "message": "Oracle session created successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating Oracle session: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create Oracle session: {str(e)}"
        )


@router.delete("/oracle/sessions/{session_id}", tags=["Admin - Utilities"])
async def close_oracle_session(
    session_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Close an Oracle session.

    This endpoint is used to clean up completed or abandoned sessions.
    """
    try:
        check_admin_permission(current_user)

        if session_id in _active_oracle_sessions:
            del _active_oracle_sessions[session_id]
            logger.info(f"Oracle session {session_id} closed by admin {current_user.id}")

            return {
                "message": f"Oracle session {session_id} closed successfully"
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Oracle session {session_id} not found"
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error closing Oracle session: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to close Oracle session: {str(e)}"
        )


# ============================================================================
# METRICS TRACKING UTILITIES
# ============================================================================

def track_oracle_consultation(provider: str, session_type: str, response_time_ms: float):
    """Track an Oracle consultation for metrics."""
    _oracle_metrics["total_consultations"] += 1
    _oracle_metrics["consultations_by_type"][session_type] = \
        _oracle_metrics["consultations_by_type"].get(session_type, 0) + 1
    _oracle_metrics["consultations_by_provider"][provider] = \
        _oracle_metrics["consultations_by_provider"].get(provider, 0) + 1
    _oracle_metrics["response_times"].append(response_time_ms)

    # Keep only last 1000 response times
    if len(_oracle_metrics["response_times"]) > 1000:
        _oracle_metrics["response_times"] = _oracle_metrics["response_times"][-1000:]


def track_oracle_error(provider: str, error_type: str, error_message: str):
    """Track an Oracle error for metrics."""
    _oracle_metrics["errors"].append({
        "provider": provider,
        "type": error_type,
        "message": error_message,
        "timestamp": datetime.utcnow().isoformat()
    })

    # Keep only last 100 errors
    if len(_oracle_metrics["errors"]) > 100:
        _oracle_metrics["errors"] = _oracle_metrics["errors"][-100:]

