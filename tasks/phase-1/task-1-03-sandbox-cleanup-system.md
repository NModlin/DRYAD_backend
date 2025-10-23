# Task 1-03: Implement Sandbox Cleanup System

**Phase:** 1 - Foundation & Validation  
**Week:** 1  
**Priority:** HIGH  
**Estimated Time:** 4 hours  
**Status:** NOT STARTED

---

## Objective
Implement automated sandbox cleanup system to manage expired sandboxes and prevent resource exhaustion.

## Current State
- File: `app/api/v1/endpoints/sandbox.py`
- Endpoint: `POST /api/v1/sandbox/cleanup`
- Current implementation: Returns `{"message": "Cleanup not implemented"}`
- Issue: No automatic cleanup of expired or abandoned sandboxes

## Specific Requirements

### 1. Sandbox Expiration Tracking
- **File:** `app/database/models.py` or existing sandbox model
- **Action:** Add/verify fields in sandbox model:
  - `expires_at` (DateTime) - When sandbox should be cleaned up
  - `last_accessed` (DateTime) - Last time sandbox was used
  - `status` (Enum: active, expired, cleaning, cleaned)
  - `retention_policy` (String) - Cleanup policy (default, extended, permanent)

### 2. Cleanup Service Implementation
- **File:** `app/services/sandbox_service.py`
- **Methods to implement:**
  - `cleanup_expired_sandboxes()` - Main cleanup orchestrator
  - `mark_sandbox_expired(sandbox_id: str)` - Mark sandbox for cleanup
  - `delete_sandbox_files(sandbox_id: str)` - Remove filesystem data
  - `archive_sandbox_metadata(sandbox_id: str)` - Archive before deletion
  - `get_expired_sandboxes(limit: int = 100)` - Query expired sandboxes

### 3. Cleanup Logic
- **File:** `app/services/sandbox_service.py`
- **Action:** Implement cleanup workflow:
  1. Query sandboxes where `expires_at < now()` or `last_accessed < now() - retention_period`
  2. For each expired sandbox:
     - Update status to 'cleaning'
     - Archive metadata to `sandbox_archive` table
     - Delete filesystem data (Docker containers, volumes, files)
     - Delete database records
     - Update status to 'cleaned'
  3. Log cleanup results
  4. Return cleanup summary

### 4. Scheduled Cleanup Task
- **File:** `app/tasks/cleanup_sandboxes.py` (new file)
- **Action:** Create scheduled task:
  - Run every hour
  - Call `cleanup_expired_sandboxes()`
  - Log cleanup statistics
  - Send alerts if cleanup fails
  - Implement retry logic for failed cleanups

### 5. Manual Cleanup Endpoint
- **File:** `app/api/v1/endpoints/sandbox.py`
- **Endpoint:** `POST /api/v1/sandbox/cleanup`
- **Action:**
  - Accept optional parameters: `force`, `sandbox_ids`, `older_than`
  - Call cleanup service
  - Return cleanup summary
  - Require admin authentication

### 6. Cleanup Configuration
- **File:** `app/core/config.py`
- **Action:** Add configuration settings:
  - `SANDBOX_DEFAULT_TTL` - Default time-to-live (default: 24 hours)
  - `SANDBOX_EXTENDED_TTL` - Extended TTL (default: 7 days)
  - `SANDBOX_CLEANUP_INTERVAL` - Cleanup frequency (default: 1 hour)
  - `SANDBOX_RETENTION_PERIOD` - Archive retention (default: 30 days)
  - `SANDBOX_MAX_CLEANUP_BATCH` - Max sandboxes per cleanup (default: 100)

### 7. Cleanup Monitoring
- **File:** `app/core/monitoring.py`
- **Action:** Add Prometheus metrics:
  - `sandbox_cleanup_total` (Counter) - Total cleanups performed
  - `sandbox_cleanup_duration_seconds` (Histogram) - Cleanup duration
  - `sandbox_cleanup_errors_total` (Counter) - Cleanup failures
  - `sandbox_active_count` (Gauge) - Active sandboxes
  - `sandbox_expired_count` (Gauge) - Expired sandboxes pending cleanup

## Acceptance Criteria
- [ ] Sandbox model includes expiration and status fields
- [ ] Cleanup service implemented with all methods
- [ ] Scheduled cleanup task runs hourly
- [ ] Manual cleanup endpoint functional
- [ ] Configuration settings added
- [ ] Prometheus metrics integrated
- [ ] Cleanup logs all operations
- [ ] Failed cleanups are retried
- [ ] Unit tests created for cleanup logic
- [ ] Integration tests created for cleanup workflow
- [ ] No resource leaks after cleanup

## Testing Requirements

### Unit Tests
- **File:** `tests/test_sandbox_service.py`
- **Tests to add:**
  - `test_get_expired_sandboxes()`
  - `test_mark_sandbox_expired()`
  - `test_delete_sandbox_files()`
  - `test_archive_sandbox_metadata()`
  - `test_cleanup_expired_sandboxes()`
  - `test_cleanup_with_retention_policy()`
  - `test_cleanup_error_handling()`

### Integration Tests
- **File:** `tests/integration/test_sandbox_cleanup.py` (new file)
- **Tests to add:**
  - `test_cleanup_endpoint()`
  - `test_scheduled_cleanup_task()`
  - `test_cleanup_removes_filesystem_data()`
  - `test_cleanup_archives_metadata()`
  - `test_cleanup_respects_retention_policy()`
  - `test_cleanup_batch_processing()`

## Dependencies
- **Blocked by:** None
- **Blocks:** None
- **Related:** Sandbox management system, monitoring infrastructure

## Definition of Done
- [ ] All code changes committed
- [ ] All tests passing (unit + integration)
- [ ] Code reviewed and approved
- [ ] Database migration tested
- [ ] Scheduled task configured and running
- [ ] API documentation updated
- [ ] Cleanup runs successfully in development
- [ ] Monitoring metrics visible
- [ ] No resource leaks detected

## Implementation Notes
- Ensure cleanup is idempotent (safe to run multiple times)
- Add transaction support for database operations
- Implement proper error handling and rollback
- Log all cleanup operations for audit trail
- Consider adding dry-run mode for testing
- Ensure Docker containers are properly stopped and removed
- Clean up associated volumes and networks
- Archive important sandbox data before deletion
- Add rate limiting to prevent cleanup storms
- Implement graceful shutdown for running sandboxes

## Files to Modify/Create
1. Modify: `app/database/models.py` (sandbox model)
2. Modify: `app/services/sandbox_service.py`
3. Create: `app/tasks/cleanup_sandboxes.py`
4. Modify: `app/api/v1/endpoints/sandbox.py`
5. Modify: `app/core/config.py`
6. Modify: `app/core/monitoring.py`
7. Modify: `tests/test_sandbox_service.py`
8. Create: `tests/integration/test_sandbox_cleanup.py`
9. Create: Alembic migration script
10. Create: `app/database/models/sandbox_archive.py`

## Success Metrics
- Cleanup runs successfully every hour
- Expired sandboxes cleaned within 1 hour of expiration
- Cleanup duration <5 minutes for 100 sandboxes
- Zero resource leaks (Docker containers, volumes)
- Cleanup success rate >99%
- Archive retention working correctly

## Cleanup Summary Response Example
```json
{
  "cleanup_started_at": "2025-01-20T10:00:00Z",
  "cleanup_completed_at": "2025-01-20T10:03:45Z",
  "duration_seconds": 225,
  "sandboxes_processed": 47,
  "sandboxes_cleaned": 45,
  "sandboxes_failed": 2,
  "disk_space_freed_mb": 1250,
  "errors": [
    {
      "sandbox_id": "uuid-1",
      "error": "Docker container not found"
    }
  ]
}
```

---

## 🔧 IMPLEMENTATION EXAMPLES

### Step 1: Enhanced Sandbox Model (1 hour)

**File:** `app/database/models/sandbox.py`

```python
"""
Sandbox Model with Expiration Tracking
Enhanced for automated cleanup.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from enum import Enum
from uuid import UUID, uuid4

from sqlalchemy import Column, DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from structlog import get_logger

from app.database.base import Base

logger = get_logger(__name__)


class SandboxStatus(str, Enum):
    """Sandbox lifecycle status."""

    ACTIVE = "ACTIVE"
    EXPIRED = "EXPIRED"
    CLEANING = "CLEANING"
    CLEANED = "CLEANED"


class Sandbox(Base):
    """Sandbox with expiration and cleanup tracking."""

    __tablename__ = "sandboxes"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(PGUUID(as_uuid=True), ForeignKey("users.id"))

    created_at = Column(DateTime, default=datetime.utcnow)
    last_accessed = Column(DateTime, default=datetime.utcnow, index=True)
    expires_at = Column(DateTime, nullable=False, index=True)
    status = Column(String(20), default=SandboxStatus.ACTIVE.value, index=True)

    def is_expired(self) -> bool:
        """Check if sandbox is expired."""
        return datetime.utcnow() >= self.expires_at
```

### Step 2: Cleanup Service (1.5 hours)

**File:** `app/services/sandbox_service.py`

```python
"""
Sandbox Cleanup Service
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

import docker
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from structlog import get_logger

from app.database.models.sandbox import Sandbox, SandboxStatus

logger = get_logger(__name__)


class SandboxCleanupService:
    """Automated sandbox cleanup."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.docker_client = docker.from_env()
        self.logger = logger.bind(service="sandbox_cleanup")

    async def cleanup_expired_sandboxes(self, limit: int = 100) -> dict:
        """Clean up expired sandboxes."""
        expired = await self.get_expired_sandboxes(limit)

        results = {"total_found": len(expired), "cleaned": 0, "failed": 0}

        for sandbox in expired:
            try:
                await self.cleanup_sandbox(sandbox.id)
                results["cleaned"] += 1
            except Exception as e:
                results["failed"] += 1
                self.logger.error("cleanup_failed", sandbox_id=str(sandbox.id), error=str(e))

        return results

    async def get_expired_sandboxes(self, limit: int) -> list[Sandbox]:
        """Get expired sandboxes."""
        query = select(Sandbox).where(
            Sandbox.status == SandboxStatus.ACTIVE.value,
            Sandbox.expires_at <= datetime.utcnow(),
        ).limit(limit)

        result = await self.db.execute(query)
        return result.scalars().all()

    async def cleanup_sandbox(self, sandbox_id: UUID) -> None:
        """Clean up single sandbox."""
        result = await self.db.execute(
            select(Sandbox).where(Sandbox.id == sandbox_id)
        )
        sandbox = result.scalar_one_or_none()

        if not sandbox:
            raise ValueError(f"Sandbox not found: {sandbox_id}")

        sandbox.status = SandboxStatus.CLEANING.value
        await self.db.commit()

        # Delete Docker resources
        await self.delete_docker_resources(sandbox_id)

        sandbox.status = SandboxStatus.CLEANED.value
        await self.db.commit()

    async def delete_docker_resources(self, sandbox_id: UUID) -> None:
        """Delete Docker containers and volumes."""
        containers = self.docker_client.containers.list(
            all=True,
            filters={"label": f"sandbox_id={sandbox_id}"},
        )

        for container in containers:
            container.remove(force=True)
```

### Step 3: API Endpoint (30 minutes)

**File:** `app/api/v1/endpoints/sandbox.py`

```python
"""Sandbox Cleanup API"""

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.services.sandbox_service import SandboxCleanupService

router = APIRouter(prefix="/api/v1/sandbox", tags=["sandbox"])


class CleanupResponse(BaseModel):
    """Cleanup response."""
    total_found: int
    cleaned: int
    failed: int


@router.post("/cleanup", response_model=CleanupResponse)
async def cleanup_sandboxes(
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
) -> CleanupResponse:
    """Clean up expired sandboxes."""
    service = SandboxCleanupService(db)
    results = await service.cleanup_expired_sandboxes(limit=limit)
    return CleanupResponse(**results)
```

### Step 4: Tests (1 hour)

**File:** `tests/test_sandbox_cleanup.py`

```python
"""Tests for Sandbox Cleanup"""

import pytest
from datetime import datetime, timedelta
from uuid import uuid4

from app.database.models.sandbox import Sandbox, SandboxStatus
from app.services.sandbox_service import SandboxCleanupService


@pytest.mark.asyncio
async def test_get_expired_sandboxes(db_session):
    """Test finding expired sandboxes."""
    service = SandboxCleanupService(db_session)

    user_id = uuid4()

    # Expired sandbox
    expired = Sandbox(
        user_id=user_id,
        expires_at=datetime.utcnow() - timedelta(hours=1),
        status=SandboxStatus.ACTIVE.value,
    )
    db_session.add(expired)

    # Active sandbox
    active = Sandbox(
        user_id=user_id,
        expires_at=datetime.utcnow() + timedelta(hours=1),
        status=SandboxStatus.ACTIVE.value,
    )
    db_session.add(active)

    await db_session.commit()

    expired_list = await service.get_expired_sandboxes(100)

    assert len(expired_list) == 1
    assert expired_list[0].id == expired.id
```

