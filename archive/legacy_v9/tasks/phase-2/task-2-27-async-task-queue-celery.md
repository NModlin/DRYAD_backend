# Task 2-27: Async Task Queue Setup (Celery)

**Phase:** 2 - Performance & Production Readiness  
**Week:** 5 - Performance Optimization  
**Priority:** HIGH  
**Estimated Hours:** 6 hours

---

## 📋 OVERVIEW

Implement Celery-based async task queue for background processing of long-running tasks such as document processing, cleanup operations, notifications, and scheduled jobs.

---

## 🎯 OBJECTIVES

1. Set up Celery with Redis broker
2. Create task definitions for common operations
3. Implement task monitoring and retry logic
4. Add scheduled tasks (Celery Beat)
5. Create task result tracking
6. Test task execution and failure handling

---

## 📊 CURRENT STATE

**Existing:**
- Redis configured in docker-compose
- Basic Celery app in `app/core/celery_app.py`
- Some task definitions exist

**Gaps:**
- No comprehensive task organization
- No task monitoring
- No scheduled tasks configured
- No task result tracking

---

## 🔧 IMPLEMENTATION

### 1. Enhanced Celery Configuration

Update `app/core/celery_app.py`:

```python
"""
Celery Application Configuration

Async task queue for background processing.
"""
from __future__ import annotations

import os
from celery import Celery
from celery.schedules import crontab
from kombu import Exchange, Queue

# Create Celery app
celery_app = Celery(
    "dryad",
    broker=os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0"),
    backend=os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/0"),
)

# Celery configuration
celery_app.conf.update(
    # Task settings
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    
    # Task execution
    task_track_started=True,
    task_time_limit=3600,  # 1 hour hard limit
    task_soft_time_limit=3000,  # 50 minutes soft limit
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    
    # Result backend
    result_expires=86400,  # 24 hours
    result_persistent=True,
    
    # Worker settings
    worker_prefetch_multiplier=4,
    worker_max_tasks_per_child=1000,
    
    # Retry settings
    task_default_retry_delay=60,  # 1 minute
    task_max_retries=3,
    
    # Task routing
    task_routes={
        "app.tasks.document_tasks.*": {"queue": "documents"},
        "app.tasks.cleanup_tasks.*": {"queue": "cleanup"},
        "app.tasks.notification_tasks.*": {"queue": "notifications"},
    },
    
    # Task queues
    task_queues=(
        Queue("default", Exchange("default"), routing_key="default"),
        Queue("documents", Exchange("documents"), routing_key="documents"),
        Queue("cleanup", Exchange("cleanup"), routing_key="cleanup"),
        Queue("notifications", Exchange("notifications"), routing_key="notifications"),
    ),
    
    # Beat schedule (scheduled tasks)
    beat_schedule={
        "cleanup-temp-files-daily": {
            "task": "app.tasks.cleanup_tasks.cleanup_temp_files",
            "schedule": crontab(hour=2, minute=0),  # 2 AM daily
        },
        "cleanup-old-sessions-hourly": {
            "task": "app.tasks.cleanup_tasks.cleanup_old_sessions",
            "schedule": crontab(minute=0),  # Every hour
        },
        "generate-daily-metrics": {
            "task": "app.tasks.analytics_tasks.generate_daily_metrics",
            "schedule": crontab(hour=1, minute=0),  # 1 AM daily
        },
    },
)

# Auto-discover tasks
celery_app.autodiscover_tasks(["app.tasks"])
```

---

### 2. Task Definitions

Create `app/tasks/document_tasks.py`:

```python
"""
Document Processing Tasks

Background tasks for document operations.
"""
from __future__ import annotations

import logging
from typing import Any
from celery import Task
from app.core.celery_app import celery_app

logger = logging.getLogger(__name__)


class CallbackTask(Task):
    """Base task with callbacks."""
    
    def on_success(self, retval: Any, task_id: str, args: tuple, kwargs: dict):
        """Called on task success."""
        logger.info(f"Task {task_id} succeeded", extra={"task_id": task_id})
    
    def on_failure(self, exc: Exception, task_id: str, args: tuple, kwargs: dict, einfo):
        """Called on task failure."""
        logger.error(
            f"Task {task_id} failed: {exc}",
            extra={"task_id": task_id, "error": str(exc)}
        )


@celery_app.task(
    bind=True,
    base=CallbackTask,
    max_retries=3,
    default_retry_delay=60
)
def process_document(self, document_id: str) -> dict[str, Any]:
    """
    Process document in background.
    
    Args:
        document_id: Document ID to process
    
    Returns:
        Processing result
    """
    try:
        logger.info(f"Processing document: {document_id}")
        
        # Simulate document processing
        # In real implementation:
        # 1. Load document from database
        # 2. Extract text/metadata
        # 3. Generate embeddings
        # 4. Store in vector database
        # 5. Update document status
        
        return {
            "document_id": document_id,
            "status": "processed",
            "chunks": 10,
            "embeddings_generated": True
        }
        
    except Exception as exc:
        logger.error(f"Error processing document {document_id}: {exc}")
        # Retry with exponential backoff
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))


@celery_app.task(bind=True, base=CallbackTask)
def batch_process_documents(self, document_ids: list[str]) -> dict[str, Any]:
    """
    Process multiple documents in batch.
    
    Args:
        document_ids: List of document IDs
    
    Returns:
        Batch processing result
    """
    from celery import group
    
    # Create parallel tasks
    job = group(process_document.s(doc_id) for doc_id in document_ids)
    result = job.apply_async()
    
    return {
        "batch_id": self.request.id,
        "total_documents": len(document_ids),
        "status": "processing"
    }
```

---

Create `app/tasks/cleanup_tasks.py`:

```python
"""
Cleanup Tasks

Scheduled cleanup operations.
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta
from pathlib import Path
from app.core.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task
def cleanup_temp_files() -> dict[str, int]:
    """
    Clean up temporary files older than 24 hours.
    
    Returns:
        Cleanup statistics
    """
    logger.info("Starting temp file cleanup")
    
    temp_dir = Path("temp")
    if not temp_dir.exists():
        return {"files_deleted": 0}
    
    cutoff_time = datetime.now() - timedelta(hours=24)
    deleted_count = 0
    
    for file_path in temp_dir.glob("**/*"):
        if file_path.is_file():
            file_time = datetime.fromtimestamp(file_path.stat().st_mtime)
            if file_time < cutoff_time:
                try:
                    file_path.unlink()
                    deleted_count += 1
                except Exception as e:
                    logger.error(f"Error deleting {file_path}: {e}")
    
    logger.info(f"Cleanup complete: {deleted_count} files deleted")
    return {"files_deleted": deleted_count}


@celery_app.task
def cleanup_old_sessions() -> dict[str, int]:
    """
    Clean up expired sessions.
    
    Returns:
        Cleanup statistics
    """
    logger.info("Starting session cleanup")
    
    # In real implementation:
    # 1. Query database for expired sessions
    # 2. Delete expired sessions
    # 3. Return count
    
    return {"sessions_deleted": 0}
```

---

### 3. Task Monitoring

Create `app/api/v1/endpoints/tasks.py`:

```python
"""
Task Management Endpoints

Monitor and manage Celery tasks.
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from celery.result import AsyncResult
from app.core.celery_app import celery_app

router = APIRouter()


class TaskStatus(BaseModel):
    """Task status response."""
    task_id: str
    status: str
    result: dict | None = None
    error: str | None = None


@router.get("/tasks/{task_id}", response_model=TaskStatus)
async def get_task_status(task_id: str):
    """Get task status by ID."""
    result = AsyncResult(task_id, app=celery_app)
    
    return TaskStatus(
        task_id=task_id,
        status=result.status,
        result=result.result if result.successful() else None,
        error=str(result.info) if result.failed() else None
    )


@router.post("/tasks/{task_id}/cancel")
async def cancel_task(task_id: str):
    """Cancel a running task."""
    result = AsyncResult(task_id, app=celery_app)
    result.revoke(terminate=True)
    
    return {"task_id": task_id, "status": "cancelled"}
```

---

## ✅ ACCEPTANCE CRITERIA

- [ ] Celery configured with Redis broker
- [ ] Task queues defined and working
- [ ] Document processing tasks implemented
- [ ] Cleanup tasks scheduled
- [ ] Task monitoring endpoints working
- [ ] Task retry logic tested
- [ ] Celery Beat running scheduled tasks

---

## 🧪 TESTING

```python
# tests/test_celery_tasks.py
"""Tests for Celery tasks."""
import pytest
from app.tasks.document_tasks import process_document
from app.tasks.cleanup_tasks import cleanup_temp_files


def test_process_document_task():
    """Test document processing task."""
    result = process_document.apply(args=["doc_123"])
    assert result.successful()
    assert result.result["status"] == "processed"


def test_cleanup_temp_files_task():
    """Test temp file cleanup task."""
    result = cleanup_temp_files.apply()
    assert result.successful()
    assert "files_deleted" in result.result
```

---

## 📝 NOTES

- Use separate queues for different task types
- Monitor task execution times
- Set appropriate timeouts
- Implement proper error handling
- Use task retries with exponential backoff


