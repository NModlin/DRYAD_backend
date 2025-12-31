# Task 1-17: Comprehensive Authentication & Authorization

**Phase:** 1 - Foundation & Beta Readiness  
**Week:** 3  
**Estimated Hours:** 8 hours  
**Priority:** CRITICAL  
**Dependencies:** None

---

## 🎯 OBJECTIVE

Implement comprehensive authentication and authorization system with JWT tokens, role-based access control (RBAC), and secure password handling.

---

## 📋 REQUIREMENTS

### Functional Requirements
- JWT-based authentication
- Role-based access control (RBAC)
- Secure password hashing (bcrypt)
- Token refresh mechanism
- Permission-based authorization

### Technical Requirements
- python-jose for JWT
- passlib for password hashing
- FastAPI security dependencies
- Token expiration handling

### Performance Requirements
- Token generation: <100ms
- Token validation: <50ms
- Password hashing: <500ms

---

## 🔧 IMPLEMENTATION

### Step 1: Authentication Service (3 hours)

**File:** `app/services/auth_service.py`

```python
"""
Authentication Service
JWT-based authentication with RBAC.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel
from structlog import get_logger

logger = get_logger(__name__)

# Configuration
SECRET_KEY = "your-secret-key-here"  # Use environment variable
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class TokenData(BaseModel):
    """JWT token data."""
    user_id: str
    username: str
    roles: list[str]
    exp: datetime


class AuthService:
    """Authentication service."""
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash password using bcrypt."""
        return pwd_context.hash(password)
    
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify password against hash."""
        return pwd_context.verify(plain_password, hashed_password)
    
    @staticmethod
    def create_access_token(
        data: dict[str, Any],
        expires_delta: timedelta | None = None,
    ) -> str:
        """
        Create JWT access token.
        
        Args:
            data: Token payload
            expires_delta: Optional expiration time
            
        Returns:
            JWT token string
        """
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        
        to_encode.update({"exp": expire})
        
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt
    
    @staticmethod
    def decode_token(token: str) -> TokenData:
        """
        Decode and validate JWT token.
        
        Args:
            token: JWT token string
            
        Returns:
            Token data
            
        Raises:
            JWTError: If token is invalid
        """
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            
            return TokenData(
                user_id=payload.get("sub"),
                username=payload.get("username"),
                roles=payload.get("roles", []),
                exp=datetime.fromtimestamp(payload.get("exp")),
            )
        except JWTError as e:
            logger.error("token_decode_failed", error=str(e))
            raise
```

### Step 2: Authorization Dependencies (2 hours)

**File:** `app/api/dependencies/auth.py`

```python
"""
Authentication Dependencies
FastAPI dependencies for authentication and authorization.
"""

from __future__ import annotations

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError

from app.services.auth_service import AuthService, TokenData

security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> TokenData:
    """
    Get current authenticated user from JWT token.
    
    Args:
        credentials: HTTP bearer credentials
        
    Returns:
        Token data
        
    Raises:
        HTTPException: If authentication fails
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        token_data = AuthService.decode_token(credentials.credentials)
        
        if token_data is None:
            raise credentials_exception
        
        return token_data
        
    except JWTError:
        raise credentials_exception


def require_role(required_role: str):
    """
    Dependency factory for role-based access control.
    
    Args:
        required_role: Required role name
        
    Returns:
        Dependency function
    """
    async def role_checker(
        current_user: TokenData = Depends(get_current_user),
    ) -> TokenData:
        """Check if user has required role."""
        if required_role not in current_user.roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{required_role}' required",
            )
        
        return current_user
    
    return role_checker


# Common role dependencies
require_admin = require_role("admin")
require_user = require_role("user")
```

### Step 3: Login Endpoint (1 hour)

**File:** `app/api/v1/endpoints/auth.py`

```python
"""
Authentication Endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.services.auth_service import AuthService

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


class LoginRequest(BaseModel):
    """Login request."""
    username: str
    password: str


class TokenResponse(BaseModel):
    """Token response."""
    access_token: str
    token_type: str = "bearer"


@router.post("/login", response_model=TokenResponse)
async def login(
    request: LoginRequest,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    """
    Login and get access token.
    
    Args:
        request: Login credentials
        db: Database session
        
    Returns:
        Access token
    """
    # Verify credentials (simplified - add user lookup)
    # user = await get_user_by_username(db, request.username)
    # if not user or not AuthService.verify_password(request.password, user.hashed_password):
    #     raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Create token
    token = AuthService.create_access_token(
        data={
            "sub": "user_id",
            "username": request.username,
            "roles": ["user"],
        }
    )
    
    return TokenResponse(access_token=token)
```

### Step 4: Tests (2 hours)

**File:** `tests/test_auth.py`

```python
"""
Authentication Tests
"""

import pytest
from datetime import timedelta

from app.services.auth_service import AuthService


def test_password_hashing():
    """Test password hashing."""
    password = "test_password_123"
    
    hashed = AuthService.hash_password(password)
    
    assert hashed != password
    assert AuthService.verify_password(password, hashed) is True
    assert AuthService.verify_password("wrong", hashed) is False


def test_create_access_token():
    """Test JWT token creation."""
    data = {"sub": "user123", "username": "testuser"}
    
    token = AuthService.create_access_token(data)
    
    assert isinstance(token, str)
    assert len(token) > 0


def test_decode_token():
    """Test token decoding."""
    data = {
        "sub": "user123",
        "username": "testuser",
        "roles": ["user", "admin"],
    }
    
    token = AuthService.create_access_token(data)
    decoded = AuthService.decode_token(token)
    
    assert decoded.user_id == "user123"
    assert decoded.username == "testuser"
    assert "admin" in decoded.roles


def test_expired_token():
    """Test expired token handling."""
    from jose import JWTError
    
    data = {"sub": "user123"}
    
    # Create token that expires immediately
    token = AuthService.create_access_token(
        data,
        expires_delta=timedelta(seconds=-1),
    )
    
    with pytest.raises(JWTError):
        AuthService.decode_token(token)
```

---

## ✅ DEFINITION OF DONE

- [ ] JWT authentication implemented
- [ ] RBAC working
- [ ] Password hashing secure
- [ ] Token refresh implemented
- [ ] All auth tests passing
- [ ] Protected endpoints working

---

## 📊 SUCCESS METRICS

- Token generation: <100ms
- Token validation: <50ms
- Password hashing: <500ms
- Auth test coverage: >90%

---

**Estimated Completion:** 8 hours  
**Status:** NOT STARTED

