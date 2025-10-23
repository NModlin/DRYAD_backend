# Task 1-02: Implement Agent Performance Metrics

**Phase:** 1 - Foundation & Validation  
**Week:** 1  
**Priority:** HIGH  
**Estimated Time:** 6 hours  
**Status:** NOT STARTED

---

## Objective
Implement comprehensive agent performance metrics collection and reporting to replace the current placeholder implementation that returns an empty dictionary.

## Current State
- File: `app/services/agent_studio_service.py`
- Method: `get_agent_performance_metrics()`
- Current implementation: Returns empty dict `{}`
- Comment: `# TODO: Implement`

## Specific Requirements

### 1. Metrics Data Model
- **File:** `app/database/models/agent_metrics.py` (new file)
- **Action:** Create `AgentMetrics` model with fields:
  - `id` (UUID, primary key)
  - `agent_id` (UUID, foreign key)
  - `metric_date` (Date)
  - `total_executions` (Integer)
  - `successful_executions` (Integer)
  - `failed_executions` (Integer)
  - `avg_execution_time_ms` (Float)
  - `min_execution_time_ms` (Integer)
  - `max_execution_time_ms` (Integer)
  - `p50_execution_time_ms` (Integer)
  - `p95_execution_time_ms` (Integer)
  - `p99_execution_time_ms` (Integer)
  - `total_errors` (Integer)
  - `error_rate` (Float)
  - `success_rate` (Float)
  - `created_at` (DateTime)
  - `updated_at` (DateTime)

### 2. Real-Time Metrics Calculation
- **File:** `app/services/agent_studio_service.py`
- **Method:** `get_agent_performance_metrics(agent_id: str, time_range: str = "7d")`
- **Action:**
  - Query `AgentExecution` table for specified time range
  - Calculate metrics in real-time:
    - Total executions
    - Success/failure counts
    - Success rate percentage
    - Average execution time
    - Percentile calculations (p50, p95, p99)
    - Error rate
    - Most common errors (top 5)
  - Return comprehensive metrics dictionary

### 3. Metrics Aggregation Service
- **File:** `app/services/metrics_aggregation_service.py` (new file)
- **Action:** Create service for daily metrics aggregation:
  - `aggregate_daily_metrics(date: datetime.date)` - Aggregate metrics for a specific date
  - `aggregate_agent_metrics(agent_id: str, date: datetime.date)` - Agent-specific aggregation
  - Store aggregated metrics in `AgentMetrics` table
  - Run as scheduled task (daily at midnight)

### 4. Monitoring Integration
- **File:** `app/core/monitoring.py`
- **Action:** Add Prometheus metrics:
  - `agent_execution_total` (Counter) - Total executions per agent
  - `agent_execution_duration_seconds` (Histogram) - Execution time distribution
  - `agent_execution_errors_total` (Counter) - Total errors per agent
  - `agent_success_rate` (Gauge) - Current success rate per agent

### 5. API Endpoint Enhancement
- **File:** `app/api/v1/endpoints/agent_studio.py`
- **Endpoint:** `GET /api/v1/agent-studio/agents/{agent_id}/metrics`
- **Action:**
  - Add query parameters: `time_range` (1d, 7d, 30d, 90d)
  - Add query parameter: `metric_type` (realtime, aggregated)
  - Call updated service method
  - Return comprehensive metrics
  - Add proper response schema with all metric fields

### 6. Metrics Dashboard Data
- **File:** `app/api/v1/endpoints/agent_studio.py`
- **Endpoint:** `GET /api/v1/agent-studio/metrics/dashboard` (new)
- **Action:**
  - Return system-wide metrics:
    - Total agents
    - Total executions (24h, 7d, 30d)
    - Average success rate
    - Top performing agents
    - Agents with issues (high error rate)
    - Execution trends over time

## Acceptance Criteria
- [ ] `AgentMetrics` model created with all required fields
- [ ] Real-time metrics calculation implemented
- [ ] Metrics aggregation service created
- [ ] Daily aggregation scheduled task configured
- [ ] Prometheus metrics integrated
- [ ] `get_agent_performance_metrics()` returns real data
- [ ] API endpoint returns comprehensive metrics
- [ ] Dashboard endpoint provides system-wide metrics
- [ ] Unit tests created for all metric calculations
- [ ] Integration tests created for API endpoints
- [ ] No placeholder or TODO comments remain

## Testing Requirements

### Unit Tests
- **File:** `tests/test_agent_studio.py`
- **Tests to add:**
  - `test_get_agent_performance_metrics_returns_data()`
  - `test_calculate_success_rate()`
  - `test_calculate_percentiles()`
  - `test_calculate_error_rate()`
  - `test_metrics_for_different_time_ranges()`
  - `test_metrics_with_no_executions()`

### Integration Tests
- **File:** `tests/integration/test_agent_metrics.py` (new file)
- **Tests to add:**
  - `test_metrics_api_endpoint()`
  - `test_metrics_aggregation_service()`
  - `test_prometheus_metrics_updated()`
  - `test_dashboard_metrics_endpoint()`
  - `test_metrics_accuracy_with_real_executions()`

## Dependencies
- **Blocked by:** Task 1-01 (Agent Execution History - needs execution data)
- **Blocks:** None
- **Related:** Monitoring infrastructure setup (Phase 2)

## Definition of Done
- [ ] All code changes committed
- [ ] All tests passing (unit + integration)
- [ ] Code reviewed and approved
- [ ] Database migration tested
- [ ] API documentation updated
- [ ] Prometheus metrics visible in monitoring system
- [ ] Metrics calculation performance <500ms
- [ ] Aggregation job runs successfully

## Implementation Notes
- Use efficient SQL queries with aggregation functions
- Cache frequently accessed metrics (Redis)
- Consider using database views for complex metrics
- Ensure percentile calculations are accurate
- Add error handling for edge cases (no data, division by zero)
- Log metrics calculation failures
- Consider adding metrics export functionality (CSV, JSON)

## Files to Modify/Create
1. Create: `app/database/models/agent_metrics.py`
2. Modify: `app/services/agent_studio_service.py`
3. Create: `app/services/metrics_aggregation_service.py`
4. Modify: `app/core/monitoring.py`
5. Modify: `app/api/v1/endpoints/agent_studio.py`
6. Modify: `tests/test_agent_studio.py`
7. Create: `tests/integration/test_agent_metrics.py`
8. Create: Alembic migration script
9. Create: `app/tasks/aggregate_metrics.py` (scheduled task)

## Success Metrics
- Metrics API endpoint returns comprehensive data
- Metrics calculation time <500ms for 10,000 executions
- Prometheus metrics updated in real-time
- Dashboard provides actionable insights
- Zero calculation errors
- Aggregation job completes in <5 minutes for all agents

---

## 🔧 IMPLEMENTATION EXAMPLES

### Step 1: Metrics Data Model (1 hour)

**File:** `app/database/models/agent_metrics.py`

```python
"""
Agent Performance Metrics Model
Stores aggregated daily metrics for agents.
"""

from __future__ import annotations

from datetime import date, datetime
from uuid import UUID, uuid4

from sqlalchemy import Column, Date, DateTime, Float, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import relationship
from structlog import get_logger

from app.database.base import Base

logger = get_logger(__name__)


class AgentMetrics(Base):
    """
    Daily aggregated agent performance metrics.

    Stores pre-calculated metrics for efficient querying.
    """

    __tablename__ = "agent_metrics"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    agent_id = Column(PGUUID(as_uuid=True), ForeignKey("agents.id"), nullable=False, index=True)
    metric_date = Column(Date, nullable=False, index=True)

    # Execution counts
    total_executions = Column(Integer, nullable=False, default=0)
    successful_executions = Column(Integer, nullable=False, default=0)
    failed_executions = Column(Integer, nullable=False, default=0)

    # Timing metrics (milliseconds)
    avg_execution_time_ms = Column(Float, nullable=True)
    min_execution_time_ms = Column(Integer, nullable=True)
    max_execution_time_ms = Column(Integer, nullable=True)
    p50_execution_time_ms = Column(Integer, nullable=True)
    p95_execution_time_ms = Column(Integer, nullable=True)
    p99_execution_time_ms = Column(Integer, nullable=True)

    # Error metrics
    total_errors = Column(Integer, nullable=False, default=0)
    error_rate = Column(Float, nullable=False, default=0.0)
    success_rate = Column(Float, nullable=False, default=0.0)

    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    agent = relationship("Agent", back_populates="metrics")

    def __repr__(self) -> str:
        return f"<AgentMetrics(agent_id={self.agent_id}, date={self.metric_date})>"

    def to_dict(self) -> dict[str, any]:
        """Convert to dictionary for API responses."""
        return {
            "agent_id": str(self.agent_id),
            "metric_date": self.metric_date.isoformat(),
            "total_executions": self.total_executions,
            "successful_executions": self.successful_executions,
            "failed_executions": self.failed_executions,
            "success_rate": round(self.success_rate, 2),
            "error_rate": round(self.error_rate, 2),
            "execution_times": {
                "avg_ms": round(self.avg_execution_time_ms, 2) if self.avg_execution_time_ms else None,
                "min_ms": self.min_execution_time_ms,
                "max_ms": self.max_execution_time_ms,
                "p50_ms": self.p50_execution_time_ms,
                "p95_ms": self.p95_execution_time_ms,
                "p99_ms": self.p99_execution_time_ms,
            },
        }
```

### Step 2: Real-Time Metrics Service (2 hours)

**File:** `app/services/agent_studio_service.py` (enhanced)

```python
"""
Agent Studio Service - Performance Metrics
Real-time metrics calculation from execution history.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any
from uuid import UUID

import numpy as np
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from structlog import get_logger

from app.database.models.agent_execution import AgentExecution, ExecutionStatus

logger = get_logger(__name__)


class AgentStudioService:
    """Agent Studio service with performance metrics."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.logger = logger.bind(service="agent_studio")

    async def get_agent_performance_metrics(
        self,
        agent_id: UUID,
        time_range: str = "7d",
    ) -> dict[str, Any]:
        """
        Calculate real-time performance metrics for agent.

        Args:
            agent_id: Agent identifier
            time_range: Time range (1d, 7d, 30d, 90d)

        Returns:
            Comprehensive performance metrics
        """
        self.logger.info(
            "calculating_performance_metrics",
            agent_id=str(agent_id),
            time_range=time_range,
        )

        # Parse time range
        days = self._parse_time_range(time_range)
        start_date = datetime.utcnow() - timedelta(days=days)

        # Query executions
        query = select(AgentExecution).where(
            AgentExecution.agent_id == agent_id,
            AgentExecution.execution_start >= start_date,
        )

        result = await self.db.execute(query)
        executions = result.scalars().all()

        if not executions:
            return self._empty_metrics(agent_id, time_range)

        # Calculate metrics
        total = len(executions)
        successful = sum(1 for e in executions if e.status == ExecutionStatus.COMPLETED.value)
        failed = sum(1 for e in executions if e.status == ExecutionStatus.FAILED.value)

        success_rate = (successful / total * 100) if total > 0 else 0.0
        error_rate = (failed / total * 100) if total > 0 else 0.0

        # Calculate execution time metrics
        execution_times = [
            e.execution_time_ms
            for e in executions
            if e.execution_time_ms is not None
        ]

        timing_metrics = self._calculate_timing_metrics(execution_times)

        # Get top errors
        top_errors = self._get_top_errors(executions)

        return {
            "agent_id": str(agent_id),
            "time_range": time_range,
            "total_executions": total,
            "successful_executions": successful,
            "failed_executions": failed,
            "success_rate": round(success_rate, 2),
            "error_rate": round(error_rate, 2),
            "execution_times": timing_metrics,
            "top_errors": top_errors,
            "trend": self._calculate_trend(executions),
        }

    def _parse_time_range(self, time_range: str) -> int:
        """Parse time range string to days."""
        mapping = {"1d": 1, "7d": 7, "30d": 30, "90d": 90}
        return mapping.get(time_range, 7)

    def _calculate_timing_metrics(
        self,
        execution_times: list[int],
    ) -> dict[str, int | float | None]:
        """Calculate timing percentiles and statistics."""
        if not execution_times:
            return {
                "avg_ms": None,
                "min_ms": None,
                "max_ms": None,
                "p50_ms": None,
                "p95_ms": None,
                "p99_ms": None,
            }

        times_array = np.array(execution_times)

        return {
            "avg_ms": round(float(np.mean(times_array)), 2),
            "min_ms": int(np.min(times_array)),
            "max_ms": int(np.max(times_array)),
            "p50_ms": int(np.percentile(times_array, 50)),
            "p95_ms": int(np.percentile(times_array, 95)),
            "p99_ms": int(np.percentile(times_array, 99)),
        }

    def _get_top_errors(
        self,
        executions: list[AgentExecution],
        limit: int = 5,
    ) -> list[dict[str, Any]]:
        """Get most common errors."""
        error_counts: dict[str, int] = {}

        for execution in executions:
            if execution.error_message:
                # Truncate error message for grouping
                error_key = execution.error_message[:100]
                error_counts[error_key] = error_counts.get(error_key, 0) + 1

        # Sort by count and return top N
        sorted_errors = sorted(
            error_counts.items(),
            key=lambda x: x[1],
            reverse=True,
        )[:limit]

        return [
            {"error": error, "count": count}
            for error, count in sorted_errors
        ]

    def _calculate_trend(self, executions: list[AgentExecution]) -> str:
        """Calculate performance trend."""
        if len(executions) < 10:
            return "insufficient_data"

        # Split into two halves
        mid = len(executions) // 2
        first_half = executions[:mid]
        second_half = executions[mid:]

        # Calculate success rates
        first_success_rate = sum(
            1 for e in first_half
            if e.status == ExecutionStatus.COMPLETED.value
        ) / len(first_half)

        second_success_rate = sum(
            1 for e in second_half
            if e.status == ExecutionStatus.COMPLETED.value
        ) / len(second_half)

        # Determine trend
        if second_success_rate > first_success_rate + 0.05:
            return "improving"
        elif second_success_rate < first_success_rate - 0.05:
            return "declining"
        else:
            return "stable"

    def _empty_metrics(self, agent_id: UUID, time_range: str) -> dict[str, Any]:
        """Return empty metrics structure."""
        return {
            "agent_id": str(agent_id),
            "time_range": time_range,
            "total_executions": 0,
            "successful_executions": 0,
            "failed_executions": 0,
            "success_rate": 0.0,
            "error_rate": 0.0,
            "execution_times": {
                "avg_ms": None,
                "min_ms": None,
                "max_ms": None,
                "p50_ms": None,
                "p95_ms": None,
                "p99_ms": None,
            },
            "top_errors": [],
            "trend": "no_data",
        }
```

### Step 3: API Endpoint (1 hour)

**File:** `app/api/v1/endpoints/agent_studio.py` (enhanced)

```python
"""
Agent Studio API - Performance Metrics Endpoint
"""

from uuid import UUID

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.services.agent_studio_service import AgentStudioService

router = APIRouter(prefix="/api/v1/agent-studio", tags=["agent-studio"])


class PerformanceMetricsResponse(BaseModel):
    """Performance metrics response model."""

    agent_id: str
    time_range: str
    total_executions: int
    successful_executions: int
    failed_executions: int
    success_rate: float
    error_rate: float
    execution_times: dict[str, int | float | None]
    top_errors: list[dict[str, any]] = Field(default_factory=list)
    trend: str


@router.get(
    "/agents/{agent_id}/metrics",
    response_model=PerformanceMetricsResponse,
)
async def get_agent_performance_metrics(
    agent_id: UUID,
    time_range: str = Query("7d", regex="^(1d|7d|30d|90d)$"),
    db: AsyncSession = Depends(get_db),
) -> PerformanceMetricsResponse:
    """
    Get agent performance metrics.

    Args:
        agent_id: Agent identifier
        time_range: Time range (1d, 7d, 30d, 90d)
        db: Database session

    Returns:
        Comprehensive performance metrics
    """
    service = AgentStudioService(db)

    metrics = await service.get_agent_performance_metrics(
        agent_id=agent_id,
        time_range=time_range,
    )

    return PerformanceMetricsResponse(**metrics)
```

### Step 4: Prometheus Metrics (1 hour)

**File:** `app/core/monitoring.py`

```python
"""
Monitoring and Prometheus Metrics
Agent performance tracking.
"""

from prometheus_client import Counter, Gauge, Histogram

# Agent execution metrics
agent_execution_total = Counter(
    "agent_execution_total",
    "Total agent executions",
    ["agent_id", "status"],
)

agent_execution_duration_seconds = Histogram(
    "agent_execution_duration_seconds",
    "Agent execution duration in seconds",
    ["agent_id"],
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0],
)

agent_execution_errors_total = Counter(
    "agent_execution_errors_total",
    "Total agent execution errors",
    ["agent_id", "error_type"],
)

agent_success_rate = Gauge(
    "agent_success_rate",
    "Current agent success rate",
    ["agent_id"],
)


def record_agent_execution(
    agent_id: str,
    status: str,
    duration_seconds: float,
    error_type: str | None = None,
) -> None:
    """
    Record agent execution metrics.

    Args:
        agent_id: Agent identifier
        status: Execution status
        duration_seconds: Execution duration
        error_type: Optional error type
    """
    agent_execution_total.labels(agent_id=agent_id, status=status).inc()
    agent_execution_duration_seconds.labels(agent_id=agent_id).observe(duration_seconds)

    if error_type:
        agent_execution_errors_total.labels(
            agent_id=agent_id,
            error_type=error_type,
        ).inc()
```

### Step 5: Tests (1 hour)

**File:** `tests/test_agent_performance_metrics.py`

```python
"""
Tests for Agent Performance Metrics
Comprehensive test coverage for metrics calculation.
"""

import pytest
from datetime import datetime, timedelta
from uuid import uuid4

from app.database.models.agent_execution import AgentExecution, ExecutionStatus
from app.services.agent_studio_service import AgentStudioService


@pytest.mark.asyncio
async def test_get_agent_performance_metrics_returns_data(db_session):
    """Test metrics calculation with real data."""
    service = AgentStudioService(db_session)

    agent_id = uuid4()
    user_id = uuid4()

    # Create test executions
    for i in range(10):
        execution = AgentExecution(
            agent_id=agent_id,
            user_id=user_id,
            input_data={"test": i},
            status=ExecutionStatus.COMPLETED.value if i < 8 else ExecutionStatus.FAILED.value,
            execution_start=datetime.utcnow() - timedelta(hours=i),
            execution_end=datetime.utcnow() - timedelta(hours=i) + timedelta(seconds=i+1),
            execution_time_ms=(i+1) * 1000,
        )
        db_session.add(execution)

    await db_session.commit()

    # Get metrics
    metrics = await service.get_agent_performance_metrics(agent_id, "7d")

    assert metrics["total_executions"] == 10
    assert metrics["successful_executions"] == 8
    assert metrics["failed_executions"] == 2
    assert metrics["success_rate"] == 80.0
    assert metrics["error_rate"] == 20.0
    assert metrics["execution_times"]["avg_ms"] is not None


@pytest.mark.asyncio
async def test_calculate_percentiles(db_session):
    """Test percentile calculations."""
    service = AgentStudioService(db_session)

    agent_id = uuid4()
    user_id = uuid4()

    # Create executions with known timing
    execution_times = [100, 200, 300, 400, 500, 600, 700, 800, 900, 1000]

    for time_ms in execution_times:
        execution = AgentExecution(
            agent_id=agent_id,
            user_id=user_id,
            input_data={},
            status=ExecutionStatus.COMPLETED.value,
            execution_start=datetime.utcnow(),
            execution_end=datetime.utcnow() + timedelta(milliseconds=time_ms),
            execution_time_ms=time_ms,
        )
        db_session.add(execution)

    await db_session.commit()

    metrics = await service.get_agent_performance_metrics(agent_id, "7d")

    assert metrics["execution_times"]["min_ms"] == 100
    assert metrics["execution_times"]["max_ms"] == 1000
    assert metrics["execution_times"]["p50_ms"] == 500
    assert metrics["execution_times"]["avg_ms"] == 550.0


@pytest.mark.asyncio
async def test_metrics_with_no_executions(db_session):
    """Test metrics for agent with no executions."""
    service = AgentStudioService(db_session)

    agent_id = uuid4()

    metrics = await service.get_agent_performance_metrics(agent_id, "7d")

    assert metrics["total_executions"] == 0
    assert metrics["success_rate"] == 0.0
    assert metrics["execution_times"]["avg_ms"] is None
    assert metrics["trend"] == "no_data"


@pytest.mark.asyncio
async def test_metrics_for_different_time_ranges(db_session):
    """Test metrics calculation for different time ranges."""
    service = AgentStudioService(db_session)

    agent_id = uuid4()
    user_id = uuid4()

    # Create executions at different times
    for days_ago in range(60):
        execution = AgentExecution(
            agent_id=agent_id,
            user_id=user_id,
            input_data={},
            status=ExecutionStatus.COMPLETED.value,
            execution_start=datetime.utcnow() - timedelta(days=days_ago),
            execution_end=datetime.utcnow() - timedelta(days=days_ago) + timedelta(seconds=1),
            execution_time_ms=1000,
        )
        db_session.add(execution)

    await db_session.commit()

    # Test different time ranges
    metrics_1d = await service.get_agent_performance_metrics(agent_id, "1d")
    metrics_7d = await service.get_agent_performance_metrics(agent_id, "7d")
    metrics_30d = await service.get_agent_performance_metrics(agent_id, "30d")

    assert metrics_1d["total_executions"] < metrics_7d["total_executions"]
    assert metrics_7d["total_executions"] < metrics_30d["total_executions"]
```

---

## Response Schema Example
```json
{
  "agent_id": "uuid",
  "time_range": "7d",
  "total_executions": 1250,
  "successful_executions": 1180,
  "failed_executions": 70,
  "success_rate": 94.4,
  "error_rate": 5.6,
  "execution_times": {
    "avg_ms": 1250,
    "min_ms": 450,
    "max_ms": 5600,
    "p50_ms": 1100,
    "p95_ms": 2800,
    "p99_ms": 4200
  },
  "top_errors": [
    {"error": "Connection timeout", "count": 25},
    {"error": "Invalid input", "count": 18}
  ],
  "trend": "improving"
}
```

