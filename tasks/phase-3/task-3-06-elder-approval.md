# Task 3-06: Elder Approval System Implementation

**Phase:** 3 - Advanced Collaboration & Governance  
**Week:** 14  
**Estimated Hours:** 4 hours  
**Priority:** HIGH  
**Dependencies:** Task 3-02 (Sage), Task 3-04 (GAD Workflow)

---

## 🎯 OBJECTIVE

Implement the Elder Approval System - a human-in-the-loop interface for reviewing and approving high-risk (Tier 3) execution plans. Provides web UI and API for plan review, approval/rejection, and feedback.

---

## 📋 REQUIREMENTS

### Functional Requirements
- Display execution plans for human review
- Show risk assessment and recommendations
- Enable approval/rejection with comments
- Support plan modification requests
- Send notifications to appropriate reviewers
- Track approval history and audit trail

### Technical Requirements
- FastAPI endpoints for approval workflow
- WebSocket for real-time updates
- Database persistence for approvals
- Email/Teams notifications
- Comprehensive audit logging

### Performance Requirements
- Plan display: <1 second
- Approval action: <500ms
- Notification delivery: <5 seconds

---

## 🔧 IMPLEMENTATION STEPS

### Step 1: Create Elder Approval API (3 hours)

**File:** `app/api/elder_approval.py`

```python
"""
Elder Approval System - Human-in-the-Loop Review Interface
Provides API for reviewing and approving high-risk execution plans.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from structlog import get_logger

from app.core.database import get_db
from app.core.security import get_current_user
from app.database.models import User, ApprovalRequest as DBApprovalRequest

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1/approvals", tags=["approvals"])


class ApprovalAction(str, Enum):
    """Approval action types."""
    
    APPROVE = "APPROVE"
    REJECT = "REJECT"
    REQUEST_CHANGES = "REQUEST_CHANGES"


class ApprovalRequest(BaseModel):
    """Approval request details."""
    
    request_id: UUID
    workflow_id: UUID
    plan_id: UUID
    plan_summary: str
    risk_tier: str
    risk_score: float
    risk_factors: list[dict[str, Any]]
    recommended_reviewers: list[str]
    requested_at: datetime
    status: str  # PENDING, APPROVED, REJECTED


class ApprovalDecision(BaseModel):
    """Approval decision from reviewer."""
    
    action: ApprovalAction
    comments: str = Field(default="", max_length=2000)
    modifications_requested: list[str] = Field(default_factory=list)


class ApprovalResponse(BaseModel):
    """Response after approval action."""
    
    request_id: UUID
    action: ApprovalAction
    reviewer: str
    comments: str
    decided_at: datetime = Field(default_factory=datetime.utcnow)


@router.get("/pending", response_model=list[ApprovalRequest])
async def get_pending_approvals(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[ApprovalRequest]:
    """
    Get all pending approval requests for current user.
    
    Returns:
        List of pending approval requests
    """
    logger.info("fetching_pending_approvals", user=current_user.username)
    
    # Query pending approvals
    # Implementation would query database
    
    return []


@router.get("/{request_id}", response_model=ApprovalRequest)
async def get_approval_request(
    request_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ApprovalRequest:
    """
    Get specific approval request details.
    
    Args:
        request_id: Approval request ID
        
    Returns:
        Approval request details
        
    Raises:
        HTTPException: If request not found
    """
    logger.info(
        "fetching_approval_request",
        request_id=str(request_id),
        user=current_user.username,
    )
    
    # Query database for approval request
    # Implementation would fetch from database
    
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Approval request not found",
    )


@router.post("/{request_id}/decide", response_model=ApprovalResponse)
async def decide_approval(
    request_id: UUID,
    decision: ApprovalDecision,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ApprovalResponse:
    """
    Make approval decision on request.
    
    Args:
        request_id: Approval request ID
        decision: Approval decision
        
    Returns:
        Approval response
        
    Raises:
        HTTPException: If request not found or already decided
    """
    logger.info(
        "processing_approval_decision",
        request_id=str(request_id),
        action=decision.action.value,
        user=current_user.username,
    )
    
    try:
        # Validate request exists and is pending
        # Implementation would check database
        
        # Record decision
        response = ApprovalResponse(
            request_id=request_id,
            action=decision.action,
            reviewer=current_user.username,
            comments=decision.comments,
        )
        
        # Persist to database
        # Implementation would save to database
        
        # Notify workflow orchestrator
        # Implementation would trigger workflow continuation
        
        logger.info(
            "approval_decision_recorded",
            request_id=str(request_id),
            action=decision.action.value,
        )
        
        return response
        
    except Exception as e:
        logger.error(
            "approval_decision_failed",
            request_id=str(request_id),
            error=str(e),
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process approval decision",
        )


@router.get("/{request_id}/history", response_model=list[ApprovalResponse])
async def get_approval_history(
    request_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[ApprovalResponse]:
    """
    Get approval history for request.
    
    Args:
        request_id: Approval request ID
        
    Returns:
        List of approval decisions
    """
    logger.info(
        "fetching_approval_history",
        request_id=str(request_id),
    )
    
    # Query approval history from database
    # Implementation would fetch history
    
    return []
```

### Step 2: Create Tests (1 hour)

**File:** `tests/test_elder_approval.py`

```python
"""Tests for Elder Approval API."""

import pytest
from fastapi.testclient import TestClient
from uuid import uuid4

from app.main import app
from app.api.elder_approval import ApprovalAction


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def auth_headers():
    """Create authentication headers."""
    # Mock authentication
    return {"Authorization": "Bearer test_token"}


def test_get_pending_approvals(client, auth_headers):
    """Test fetching pending approvals."""
    response = client.get(
        "/api/v1/approvals/pending",
        headers=auth_headers,
    )
    
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_decide_approval(client, auth_headers):
    """Test making approval decision."""
    request_id = uuid4()
    
    response = client.post(
        f"/api/v1/approvals/{request_id}/decide",
        headers=auth_headers,
        json={
            "action": ApprovalAction.APPROVE.value,
            "comments": "Looks good to proceed",
        },
    )
    
    # Expect 404 since request doesn't exist
    assert response.status_code == 404
```

---

## ✅ DEFINITION OF DONE

- [ ] Elder Approval API implemented
- [ ] Approval workflow functional
- [ ] Notification system working
- [ ] Audit logging complete
- [ ] All tests passing (>80% coverage)
- [ ] Documentation complete

---

## 📊 SUCCESS METRICS

- Approval response time: <1 second
- Notification delivery: >99%
- Audit trail completeness: 100%
- Test coverage: >80%

---

**Estimated Completion:** 4 hours  
**Assigned To:** Backend Developer  
**Status:** NOT STARTED

