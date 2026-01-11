"""
Authentication endpoints for Uni0
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import Optional
from pydantic import BaseModel
import jwt
from datetime import datetime, timedelta, timezone

from dryad.university.database.database import get_db
from dryad.university.database.models_university import University, UniversityAgent
from dryad.university.core.config import settings
from dryad.university.middleware.rate_limit import limiter

router = APIRouter()
security = HTTPBearer()

class LoginRequest(BaseModel):
    university_id: str
    agent_id: Optional[str] = None
    api_key: Optional[str] = None

class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    expires_in: int
    university_id: str
    agent_id: Optional[str] = None
    permissions: list

class TokenData(BaseModel):
    university_id: str
    agent_id: Optional[str] = None
    permissions: list

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify JWT token"""
    try:
        payload = jwt.decode(credentials.credentials, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        university_id: int = payload.get("university_id")
        agent_id: Optional[int] = payload.get("agent_id")
        permissions: list = payload.get("permissions", [])
        
        if university_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials"
            )
        
        token_data = TokenData(
            university_id=university_id,
            agent_id=agent_id,
            permissions=permissions
        )
        return token_data
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials"
        )

async def get_current_university(token_data: TokenData = Depends(verify_token), db: Session = Depends(get_db)):
    """Get current university from token"""
    university = db.query(University).filter(University.id == token_data.university_id).first()
    if university is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="University not found"
        )
    return university

async def get_current_agent(token_data: TokenData = Depends(verify_token), db: Session = Depends(get_db)):
    """Get current agent from token"""
    if token_data.agent_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Agent authentication required"
        )

    agent = db.query(UniversityAgent).filter(UniversityAgent.id == token_data.agent_id).first()
    if agent is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Agent not found"
        )
    return agent


async def get_current_agent_optional(token_data: TokenData = Depends(verify_token), db: Session = Depends(get_db)):
    """Get current agent from token (optional - returns None if no agent_id)"""
    if token_data.agent_id is None:
        return None

    agent = db.query(UniversityAgent).filter(UniversityAgent.id == token_data.agent_id).first()
    return agent

@router.post("/login", response_model=LoginResponse)
@limiter.limit("5/minute")
async def login(request: Request, login_data: LoginRequest, db: Session = Depends(get_db)):
    """Login endpoint for universities and agents - Rate limited to 5 requests per minute"""
    # Verify university exists
    university = db.query(University).filter(University.id == login_data.university_id).first()
    if not university:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid university ID"
        )
    
    # For now, we'll use a simple API key system
    # In a real implementation, you'd have proper authentication
    expected_api_key = f"uni0_{university.id}_key"
    if login_data.api_key != expected_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key"
        )
    
    permissions = ["university:read", "university:write"]
    agent_id = None
    
    # If agent_id is provided, verify agent belongs to university
    if login_data.agent_id:
        agent = db.query(UniversityAgent).filter(
            UniversityAgent.id == login_data.agent_id,
            UniversityAgent.university_id == university.id
        ).first()
        
        if not agent:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Agent not found in this university"
            )
        
        agent_id = agent.id
        permissions.extend(["agent:read", "agent:write", "agent:execute"])
    
    # Create access token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={
            "university_id": university.id,
            "agent_id": agent_id,
            "permissions": permissions
        },
        expires_delta=access_token_expires
    )
    
    return LoginResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        university_id=university.id,
        agent_id=agent_id,
        permissions=permissions
    )

@router.post("/refresh")
async def refresh_token(token_data: TokenData = Depends(verify_token)):
    """Refresh access token"""
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={
            "university_id": token_data.university_id,
            "agent_id": token_data.agent_id,
            "permissions": token_data.permissions
        },
        expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    }

@router.get("/me")
async def get_current_user(
    university: University = Depends(get_current_university),
    agent: Optional[UniversityAgent] = Depends(get_current_agent_optional)
):
    """Get current user information"""
    response = {
        "university": {
            "id": university.id,
            "name": university.name,
            "domain": getattr(university, 'domain', None),
            "status": university.status
        }
    }

    if agent:
        response["agent"] = {
            "id": agent.id,
            "name": agent.name,
            "status": agent.status,
            "specialization": agent.specialization
        }

    return response

@router.get("/permissions")
async def get_permissions(token_data: TokenData = Depends(verify_token)):
    """Get current user permissions"""
    return {
        "permissions": token_data.permissions,
        "university_id": token_data.university_id,
        "agent_id": token_data.agent_id
    }

@router.post("/logout")
async def logout():
    """Logout endpoint (token revocation would be handled by a blacklist in production)"""
    return {"message": "Successfully logged out"}

# Permission-based dependency functions
def require_permission(permission: str):
    """Dependency to require specific permission"""
    def permission_dependency(token_data: TokenData = Depends(verify_token)):
        if permission not in token_data.permissions:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission '{permission}' required"
            )
        return token_data
    return permission_dependency

def require_university_admin():
    """Dependency to require university admin permissions"""
    return require_permission("university:admin")

def require_agent_control():
    """Dependency to require agent control permissions"""
    return require_permission("agent:execute")

# Utility functions for other endpoints
def get_token_data() -> TokenData:
    """Get token data from dependency"""
    return Depends(verify_token)

def get_current_university_dependency():
    """Get current university dependency"""
    return Depends(get_current_university)

def get_current_agent_dependency():
    """Get current agent dependency"""
    return Depends(get_current_agent)