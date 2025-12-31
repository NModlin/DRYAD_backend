# Task 2-45: Audit Logging Implementation

**Phase:** 2 - Performance & Production Readiness  
**Week:** 6 - Monitoring & Observability  
**Priority:** HIGH  
**Estimated Hours:** 4 hours

---

## 📋 OVERVIEW

Implement comprehensive audit logging for security-sensitive operations, user actions, and system changes to support compliance, security monitoring, and forensic analysis.

---

## 🎯 OBJECTIVES

1. Create audit log database schema
2. Implement audit logging middleware
3. Log security-sensitive operations
4. Create audit log query API
5. Implement audit log retention
6. Test audit logging

---

## 📊 CURRENT STATE

**Existing:**
- Application logging
- No audit trail

**Gaps:**
- No audit logging
- No compliance tracking
- No security event logging
- No forensic capabilities

---

## 🔧 IMPLEMENTATION

### 1. Audit Log Model

Create `app/database/models/audit_log.py`:

```python
"""
Audit Log Model

Track security-sensitive operations and user actions.
"""
from __future__ import annotations

from datetime import datetime
from sqlalchemy import Column, String, DateTime, JSON, Index
from sqlalchemy.dialects.postgresql import UUID
import uuid
from app.database.database import Base


class AuditLog(Base):
    """Audit log entry."""
    
    __tablename__ = "audit_logs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Who
    user_id = Column(String, index=True, nullable=True)
    user_email = Column(String, nullable=True)
    ip_address = Column(String, nullable=True)
    user_agent = Column(String, nullable=True)
    
    # What
    action = Column(String, index=True, nullable=False)
    resource_type = Column(String, index=True, nullable=False)
    resource_id = Column(String, nullable=True)
    
    # When
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Details
    details = Column(JSON, nullable=True)
    changes = Column(JSON, nullable=True)  # Before/after values
    
    # Context
    request_id = Column(String, index=True, nullable=True)
    session_id = Column(String, nullable=True)
    
    # Result
    status = Column(String, nullable=False)  # success, failure, error
    error_message = Column(String, nullable=True)
    
    # Indexes for common queries
    __table_args__ = (
        Index('idx_audit_user_timestamp', 'user_id', 'timestamp'),
        Index('idx_audit_action_timestamp', 'action', 'timestamp'),
        Index('idx_audit_resource', 'resource_type', 'resource_id'),
    )
```

---

### 2. Audit Logger Service

Create `app/core/audit_logger.py`:

```python
"""
Audit Logger Service

Service for creating audit log entries.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Request
from app.database.models.audit_log import AuditLog

logger = logging.getLogger(__name__)


class AuditLogger:
    """Audit logging service."""
    
    # Action types
    ACTION_LOGIN = "user.login"
    ACTION_LOGOUT = "user.logout"
    ACTION_REGISTER = "user.register"
    ACTION_PASSWORD_CHANGE = "user.password_change"
    ACTION_PROFILE_UPDATE = "user.profile_update"
    ACTION_DELETE_ACCOUNT = "user.delete_account"
    
    ACTION_CREATE = "resource.create"
    ACTION_READ = "resource.read"
    ACTION_UPDATE = "resource.update"
    ACTION_DELETE = "resource.delete"
    
    ACTION_PERMISSION_GRANT = "permission.grant"
    ACTION_PERMISSION_REVOKE = "permission.revoke"
    
    ACTION_API_KEY_CREATE = "api_key.create"
    ACTION_API_KEY_REVOKE = "api_key.revoke"
    
    async def log(
        self,
        db: AsyncSession,
        action: str,
        resource_type: str,
        user_id: Optional[str] = None,
        resource_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        changes: Optional[Dict[str, Any]] = None,
        status: str = "success",
        error_message: Optional[str] = None,
        request: Optional[Request] = None
    ):
        """
        Create audit log entry.
        
        Args:
            db: Database session
            action: Action performed
            resource_type: Type of resource
            user_id: User ID
            resource_id: Resource ID
            details: Additional details
            changes: Before/after changes
            status: Operation status
            error_message: Error message if failed
            request: FastAPI request
        """
        try:
            # Extract request context
            ip_address = None
            user_agent = None
            request_id = None
            
            if request:
                ip_address = request.client.host if request.client else None
                user_agent = request.headers.get("user-agent")
                request_id = getattr(request.state, "request_id", None)
            
            # Create audit log entry
            audit_log = AuditLog(
                user_id=user_id,
                ip_address=ip_address,
                user_agent=user_agent,
                action=action,
                resource_type=resource_type,
                resource_id=resource_id,
                details=details,
                changes=changes,
                request_id=request_id,
                status=status,
                error_message=error_message
            )
            
            db.add(audit_log)
            await db.commit()
            
            logger.info(
                f"Audit log created: {action}",
                extra={
                    "action": action,
                    "resource_type": resource_type,
                    "user_id": user_id,
                    "status": status
                }
            )
            
        except Exception as e:
            logger.error(f"Failed to create audit log: {e}")
            # Don't fail the operation if audit logging fails
    
    async def log_user_action(
        self,
        db: AsyncSession,
        action: str,
        user_id: str,
        details: Optional[Dict] = None,
        request: Optional[Request] = None
    ):
        """Log user action."""
        await self.log(
            db=db,
            action=action,
            resource_type="user",
            user_id=user_id,
            resource_id=user_id,
            details=details,
            request=request
        )
    
    async def log_resource_change(
        self,
        db: AsyncSession,
        action: str,
        resource_type: str,
        resource_id: str,
        user_id: str,
        changes: Optional[Dict] = None,
        request: Optional[Request] = None
    ):
        """Log resource change."""
        await self.log(
            db=db,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            user_id=user_id,
            changes=changes,
            request=request
        )


# Global audit logger
audit_logger = AuditLogger()
```

---

### 3. Audit Logging Decorator

Create `app/core/audit_decorator.py`:

```python
"""
Audit Logging Decorator

Decorator for automatic audit logging.
"""
from __future__ import annotations

from functools import wraps
from typing import Callable
from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.audit_logger import audit_logger


def audit_log(
    action: str,
    resource_type: str,
    get_resource_id: Callable = None
):
    """
    Decorator for audit logging.
    
    Args:
        action: Action being performed
        resource_type: Type of resource
        get_resource_id: Function to extract resource ID from result
    
    Example:
        @audit_log(
            action=audit_logger.ACTION_UPDATE,
            resource_type="user",
            get_resource_id=lambda result: result.id
        )
        async def update_user(db: AsyncSession, user_id: str, ...):
            ...
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract db and request from kwargs
            db = kwargs.get("db")
            request = kwargs.get("request")
            user_id = getattr(request.state, "user_id", None) if request else None
            
            try:
                # Execute function
                result = await func(*args, **kwargs)
                
                # Extract resource ID
                resource_id = None
                if get_resource_id and result:
                    resource_id = get_resource_id(result)
                
                # Log success
                if db:
                    await audit_logger.log(
                        db=db,
                        action=action,
                        resource_type=resource_type,
                        user_id=user_id,
                        resource_id=resource_id,
                        status="success",
                        request=request
                    )
                
                return result
                
            except Exception as e:
                # Log failure
                if db:
                    await audit_logger.log(
                        db=db,
                        action=action,
                        resource_type=resource_type,
                        user_id=user_id,
                        status="failure",
                        error_message=str(e),
                        request=request
                    )
                raise
        
        return wrapper
    return decorator
```

---

### 4. Audit Log Query API

Create `app/api/v1/endpoints/audit_logs.py`:

```python
"""
Audit Log Endpoints

Query and export audit logs.
"""
from __future__ import annotations

from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from app.database.database import get_db
from app.database.models.audit_log import AuditLog
from app.core.auth import require_admin

router = APIRouter()


class AuditLogResponse(BaseModel):
    """Audit log response."""
    id: str
    user_id: str | None
    action: str
    resource_type: str
    resource_id: str | None
    timestamp: datetime
    status: str
    ip_address: str | None


@router.get("/audit-logs", response_model=list[AuditLogResponse])
async def get_audit_logs(
    db: AsyncSession = Depends(get_db),
    user_id: str | None = None,
    action: str | None = None,
    resource_type: str | None = None,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    limit: int = Query(100, le=1000),
    _: None = Depends(require_admin)
):
    """
    Get audit logs (admin only).
    
    Args:
        db: Database session
        user_id: Filter by user ID
        action: Filter by action
        resource_type: Filter by resource type
        start_date: Filter by start date
        end_date: Filter by end date
        limit: Maximum results
    
    Returns:
        List of audit logs
    """
    # Build query
    conditions = []
    
    if user_id:
        conditions.append(AuditLog.user_id == user_id)
    if action:
        conditions.append(AuditLog.action == action)
    if resource_type:
        conditions.append(AuditLog.resource_type == resource_type)
    if start_date:
        conditions.append(AuditLog.timestamp >= start_date)
    if end_date:
        conditions.append(AuditLog.timestamp <= end_date)
    
    query = select(AuditLog).order_by(AuditLog.timestamp.desc()).limit(limit)
    
    if conditions:
        query = query.where(and_(*conditions))
    
    result = await db.execute(query)
    logs = result.scalars().all()
    
    return [
        AuditLogResponse(
            id=str(log.id),
            user_id=log.user_id,
            action=log.action,
            resource_type=log.resource_type,
            resource_id=log.resource_id,
            timestamp=log.timestamp,
            status=log.status,
            ip_address=log.ip_address
        )
        for log in logs
    ]


@router.get("/audit-logs/user/{user_id}")
async def get_user_audit_logs(
    user_id: str,
    db: AsyncSession = Depends(get_db),
    days: int = Query(30, le=90)
):
    """Get audit logs for specific user."""
    start_date = datetime.utcnow() - timedelta(days=days)
    
    query = select(AuditLog).where(
        and_(
            AuditLog.user_id == user_id,
            AuditLog.timestamp >= start_date
        )
    ).order_by(AuditLog.timestamp.desc()).limit(100)
    
    result = await db.execute(query)
    logs = result.scalars().all()
    
    return {"logs": [log.__dict__ for log in logs]}
```

---

## ✅ ACCEPTANCE CRITERIA

- [ ] Audit log model created
- [ ] Audit logger service implemented
- [ ] Audit logging decorator working
- [ ] Security operations logged
- [ ] Audit log query API working
- [ ] Retention policy implemented
- [ ] Documentation complete

---

## 🧪 TESTING

```python
# tests/test_audit_logging.py
"""Tests for audit logging."""
import pytest
from app.core.audit_logger import audit_logger


@pytest.mark.asyncio
async def test_audit_log_creation(db):
    """Test audit log creation."""
    await audit_logger.log(
        db=db,
        action=audit_logger.ACTION_LOGIN,
        resource_type="user",
        user_id="user_123"
    )
    
    # Verify log created
    from sqlalchemy import select
    from app.database.models.audit_log import AuditLog
    
    result = await db.execute(
        select(AuditLog).where(AuditLog.user_id == "user_123")
    )
    log = result.scalar_one()
    
    assert log.action == audit_logger.ACTION_LOGIN
    assert log.status == "success"
```

---

## 📝 NOTES

- Log all security-sensitive operations
- Implement retention policy (90 days)
- Protect audit logs from tampering
- Regular audit log reviews
- Export logs for compliance


