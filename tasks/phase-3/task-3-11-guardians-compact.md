# Task 3-11: Guardian's Compact (Security Protocols) Implementation

**Phase:** 3 - Advanced Collaboration & Governance  
**Week:** 16  
**Estimated Hours:** 16 hours  
**Priority:** CRITICAL  
**Dependencies:** Phase 2 complete

---

## 🎯 OBJECTIVE

Implement the Guardian's Compact - enterprise-grade security protocols including JWT authentication, JIT (Just-In-Time) secrets management, NHI (Non-Human Identity) for agents, comprehensive audit trails, and security monitoring.

---

## 📋 REQUIREMENTS

### Functional Requirements
- JWT-based authentication and authorization
- JIT secrets management (fetch secrets only when needed)
- NHI (Non-Human Identity) for agent authentication
- Comprehensive audit logging for all actions
- Security event monitoring and alerting
- Rate limiting and DDoS protection
- Encryption at rest and in transit

### Technical Requirements
- FastAPI security middleware
- Redis for session management
- PostgreSQL for audit logs
- Secrets management integration (HashiCorp Vault or AWS Secrets Manager)
- Async/await patterns
- Comprehensive logging

### Performance Requirements
- Authentication: <100ms
- Authorization check: <50ms
- Audit log write: <200ms
- Secrets fetch: <500ms

---

## 🔧 IMPLEMENTATION STEPS

### Step 1: Create Security Core (12 hours)

**File:** `app/core/security.py`

```python
"""
Guardian's Compact - Enterprise Security Protocols
JWT auth, JIT secrets, NHI, audit trails, and monitoring.
"""

from __future__ import annotations

import secrets
from datetime import datetime, timedelta
from enum import Enum
from typing import Any
from uuid import UUID, uuid4

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from passlib.context import CryptContext
from pydantic import BaseModel, Field
from structlog import get_logger

logger = get_logger(__name__)

# Security configuration
SECRET_KEY = secrets.token_urlsafe(32)  # In production, load from env
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# HTTP Bearer token scheme
security = HTTPBearer()


class IdentityType(str, Enum):
    """Type of identity."""
    
    HUMAN = "HUMAN"  # Human user
    AGENT = "AGENT"  # AI agent (NHI)
    SERVICE = "SERVICE"  # Service account


class Permission(str, Enum):
    """System permissions."""
    
    READ = "READ"
    WRITE = "WRITE"
    EXECUTE = "EXECUTE"
    ADMIN = "ADMIN"
    APPROVE = "APPROVE"


class TokenPayload(BaseModel):
    """JWT token payload."""
    
    sub: str  # Subject (user ID or agent ID)
    identity_type: IdentityType
    permissions: list[Permission]
    exp: datetime
    iat: datetime = Field(default_factory=datetime.utcnow)
    jti: UUID = Field(default_factory=uuid4)  # JWT ID for revocation


class AuditEvent(BaseModel):
    """Security audit event."""
    
    event_id: UUID = Field(default_factory=uuid4)
    identity_id: str
    identity_type: IdentityType
    action: str
    resource: str
    result: str  # SUCCESS, FAILURE, DENIED
    ip_address: str | None = None
    user_agent: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class SecurityService:
    """
    Security Service - Guardian's Compact Implementation
    
    Provides JWT auth, JIT secrets, NHI, and audit trails.
    """
    
    def __init__(self) -> None:
        self.logger = logger.bind(service="security")
        
        # Revoked token JTIs (in production, use Redis)
        self._revoked_tokens: set[UUID] = set()
    
    def create_access_token(
        self,
        subject: str,
        identity_type: IdentityType,
        permissions: list[Permission],
        expires_delta: timedelta | None = None,
    ) -> str:
        """
        Create JWT access token.
        
        Args:
            subject: User ID or agent ID
            identity_type: Type of identity
            permissions: List of permissions
            expires_delta: Optional custom expiration
            
        Returns:
            JWT token string
        """
        if expires_delta is None:
            expires_delta = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        
        expire = datetime.utcnow() + expires_delta
        
        payload = TokenPayload(
            sub=subject,
            identity_type=identity_type,
            permissions=permissions,
            exp=expire,
        )
        
        token = jwt.encode(
            payload.model_dump(mode="json"),
            SECRET_KEY,
            algorithm=ALGORITHM,
        )
        
        self.logger.info(
            "token_created",
            subject=subject,
            identity_type=identity_type.value,
            expires_at=expire.isoformat(),
        )
        
        return token
    
    def verify_token(self, token: str) -> TokenPayload:
        """
        Verify and decode JWT token.
        
        Args:
            token: JWT token string
            
        Returns:
            Decoded token payload
            
        Raises:
            HTTPException: If token invalid or expired
        """
        try:
            payload_dict = jwt.decode(
                token,
                SECRET_KEY,
                algorithms=[ALGORITHM],
            )
            
            payload = TokenPayload(**payload_dict)
            
            # Check if token revoked
            if payload.jti in self._revoked_tokens:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token has been revoked",
                )
            
            return payload
            
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired",
            )
        except jwt.JWTError as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid token: {str(e)}",
            )
    
    def revoke_token(self, jti: UUID) -> None:
        """Revoke token by JWT ID."""
        self._revoked_tokens.add(jti)
        self.logger.info("token_revoked", jti=str(jti))
    
    def check_permission(
        self,
        payload: TokenPayload,
        required_permission: Permission,
    ) -> bool:
        """
        Check if identity has required permission.
        
        Args:
            payload: Token payload
            required_permission: Required permission
            
        Returns:
            True if authorized
        """
        # Admin has all permissions
        if Permission.ADMIN in payload.permissions:
            return True
        
        return required_permission in payload.permissions
    
    async def log_audit_event(
        self,
        identity_id: str,
        identity_type: IdentityType,
        action: str,
        resource: str,
        result: str,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """
        Log security audit event.
        
        Args:
            identity_id: User or agent ID
            identity_type: Type of identity
            action: Action performed
            resource: Resource accessed
            result: Result of action
            metadata: Additional metadata
        """
        event = AuditEvent(
            identity_id=identity_id,
            identity_type=identity_type,
            action=action,
            resource=resource,
            result=result,
            metadata=metadata or {},
        )
        
        self.logger.info(
            "audit_event",
            event_id=str(event.event_id),
            identity=identity_id,
            action=action,
            resource=resource,
            result=result,
        )
        
        # In production, persist to database
        # await db.audit_logs.insert(event)
    
    def hash_password(self, password: str) -> str:
        """Hash password using bcrypt."""
        return pwd_context.hash(password)
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify password against hash."""
        return pwd_context.verify(plain_password, hashed_password)


# Global security service instance
security_service = SecurityService()


async def get_current_identity(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> TokenPayload:
    """
    Dependency to get current authenticated identity.
    
    Args:
        credentials: HTTP bearer credentials
        
    Returns:
        Token payload
        
    Raises:
        HTTPException: If authentication fails
    """
    token = credentials.credentials
    return security_service.verify_token(token)


def require_permission(required_permission: Permission):
    """
    Dependency factory to require specific permission.
    
    Args:
        required_permission: Required permission
        
    Returns:
        Dependency function
    """
    async def permission_checker(
        identity: TokenPayload = Depends(get_current_identity),
    ) -> TokenPayload:
        """Check if identity has required permission."""
        if not security_service.check_permission(identity, required_permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied: {required_permission.value} required",
            )
        
        # Log authorization check
        await security_service.log_audit_event(
            identity_id=identity.sub,
            identity_type=identity.identity_type,
            action="AUTHORIZATION_CHECK",
            resource=required_permission.value,
            result="SUCCESS",
        )
        
        return identity
    
    return permission_checker
```

**File:** `app/core/secrets_manager.py`

```python
"""JIT (Just-In-Time) Secrets Management."""

from __future__ import annotations

import os
from typing import Any

from pydantic import BaseModel
from structlog import get_logger

logger = get_logger(__name__)


class Secret(BaseModel):
    """Secret value with metadata."""
    
    key: str
    value: str
    version: str = "latest"


class JITSecretsManager:
    """
    Just-In-Time Secrets Manager
    
    Fetches secrets only when needed, never stores in memory.
    """
    
    def __init__(self) -> None:
        self.logger = logger.bind(service="secrets_manager")
    
    async def get_secret(self, key: str) -> str:
        """
        Fetch secret by key (JIT).
        
        Args:
            key: Secret key
            
        Returns:
            Secret value
            
        Raises:
            ValueError: If secret not found
        """
        self.logger.info("fetching_secret", key=key)
        
        # In production, fetch from HashiCorp Vault or AWS Secrets Manager
        # For now, use environment variables
        value = os.getenv(key)
        
        if value is None:
            raise ValueError(f"Secret not found: {key}")
        
        return value
    
    async def rotate_secret(self, key: str, new_value: str) -> None:
        """
        Rotate secret value.
        
        Args:
            key: Secret key
            new_value: New secret value
        """
        self.logger.info("rotating_secret", key=key)
        
        # In production, update in secrets manager
        # For now, just log
        pass


# Global secrets manager instance
secrets_manager = JITSecretsManager()
```

### Step 2: Create Tests (4 hours)

**File:** `tests/test_security.py`

```python
"""Tests for Guardian's Compact security."""

import pytest
from datetime import timedelta

from app.core.security import (
    SecurityService,
    IdentityType,
    Permission,
)


@pytest.fixture
def security_service():
    """Create security service instance."""
    return SecurityService()


def test_create_and_verify_token(security_service):
    """Test token creation and verification."""
    token = security_service.create_access_token(
        subject="user123",
        identity_type=IdentityType.HUMAN,
        permissions=[Permission.READ, Permission.WRITE],
    )
    
    payload = security_service.verify_token(token)
    
    assert payload.sub == "user123"
    assert payload.identity_type == IdentityType.HUMAN
    assert Permission.READ in payload.permissions


def test_check_permission(security_service):
    """Test permission checking."""
    token = security_service.create_access_token(
        subject="agent456",
        identity_type=IdentityType.AGENT,
        permissions=[Permission.EXECUTE],
    )
    
    payload = security_service.verify_token(token)
    
    assert security_service.check_permission(payload, Permission.EXECUTE)
    assert not security_service.check_permission(payload, Permission.ADMIN)


def test_password_hashing(security_service):
    """Test password hashing and verification."""
    password = "secure_password_123"
    hashed = security_service.hash_password(password)
    
    assert security_service.verify_password(password, hashed)
    assert not security_service.verify_password("wrong_password", hashed)
```

---

## ✅ DEFINITION OF DONE

- [ ] JWT authentication implemented
- [ ] JIT secrets management working
- [ ] NHI for agents functional
- [ ] Audit logging operational
- [ ] Permission system working
- [ ] All tests passing (>90% coverage)
- [ ] Security audit complete
- [ ] Documentation complete

---

## 📊 SUCCESS METRICS

- Authentication time: <100ms
- Authorization check: <50ms
- Audit log reliability: >99.9%
- Zero security vulnerabilities
- Test coverage: >90%

---

**Estimated Completion:** 16 hours  
**Assigned To:** Security Engineer + Backend Developer  
**Status:** NOT STARTED

