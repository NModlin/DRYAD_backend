"""
University Authentication Integration

Provides university-aware authentication and authorization for the Agentic University System.
Integrates university context into JWT tokens and provides university-specific permissions.
"""

import logging
from typing import Optional, Dict, Any, List
from fastapi import HTTPException, Request, Depends
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.database.database import get_db
from app.core.security import User, get_current_user, require_permission, require_role
from app.database.models_university import University, UniversityAgent, UniversityMembership

logger = logging.getLogger(__name__)


class UniversityUser(User):
    """Extended User model with university context"""
    
    def __init__(self, user: User, university_context: Optional[Dict[str, Any]] = None):
        super().__init__(**user.model_dump())
        self.university_context = university_context or {}
        self.university_id = university_context.get("university_id") if university_context else None
        self.agent_id = university_context.get("agent_id") if university_context else None
        self.roles_in_university = university_context.get("roles", []) if university_context else []
        self.permissions_in_university = university_context.get("permissions", []) if university_context else []


async def get_university_context(
    db: Session,
    user_id: str,
    university_id: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """Get university context for a user"""
    try:
        # If university_id is provided, get specific university context
        if university_id:
            # Check if user is a member of this university
            membership = db.query(UniversityMembership).filter(
                UniversityMembership.user_id == user_id,
                UniversityMembership.university_id == university_id,
                UniversityMembership.status == "active"
            ).first()
            
            if membership:
                # Get university details
                university = db.query(University).filter(University.id == university_id).first()
                if university:
                    # Get user's agent in this university (if any)
                    agent = db.query(UniversityAgent).filter(
                        UniversityAgent.university_id == university_id,
                        UniversityAgent.user_id == user_id,
                        UniversityAgent.status == "active"
                    ).first()
                    
                    return {
                        "university_id": university_id,
                        "university_name": university.name,
                        "university_type": university.type,
                        "agent_id": agent.id if agent else None,
                        "agent_type": agent.agent_type if agent else None,
                        "roles": membership.roles,
                        "permissions": _get_university_permissions(membership.roles),
                        "membership_status": membership.status,
                        "joined_at": membership.joined_at.isoformat() if membership.joined_at else None
                    }
        
        # If no specific university, get all universities the user belongs to
        memberships = db.query(UniversityMembership).filter(
            UniversityMembership.user_id == user_id,
            UniversityMembership.status == "active"
        ).all()
        
        if memberships:
            # For now, return context for the first university
            # In a real implementation, you might want to handle multiple universities
            membership = memberships[0]
            university = db.query(University).filter(University.id == membership.university_id).first()
            
            if university:
                agent = db.query(UniversityAgent).filter(
                    UniversityAgent.university_id == membership.university_id,
                    UniversityAgent.user_id == user_id,
                    UniversityAgent.status == "active"
                ).first()
                
                return {
                    "university_id": membership.university_id,
                    "university_name": university.name,
                    "university_type": university.type,
                    "agent_id": agent.id if agent else None,
                    "agent_type": agent.agent_type if agent else None,
                    "roles": membership.roles,
                    "permissions": _get_university_permissions(membership.roles),
                    "membership_status": membership.status,
                    "joined_at": membership.joined_at.isoformat() if membership.joined_at else None
                }
        
        return None
        
    except Exception as e:
        logger.error(f"Failed to get university context for user {user_id}: {e}")
        return None


def _get_university_permissions(roles: List[str]) -> List[str]:
    """Map university roles to permissions"""
    permissions = set()
    
    for role in roles:
        if role == "university_admin":
            permissions.update([
                "manage_university", "manage_agents", "manage_curriculum", 
                "manage_competitions", "view_analytics", "manage_members"
            ])
        elif role == "professor":
            permissions.update([
                "manage_curriculum", "create_competitions", "evaluate_agents",
                "view_analytics", "manage_training_data"
            ])
        elif role == "student":
            permissions.update([
                "participate_curriculum", "join_competitions", "submit_training_data",
                "view_progress", "earn_achievements"
            ])
        elif role == "researcher":
            permissions.update([
                "analyze_data", "create_proposals", "view_research_data",
                "collaborate_agents"
            ])
    
    return list(permissions)


async def get_current_university_user(
    request: Request,
    university_id: Optional[str] = None,
    db: Session = Depends(get_db)
) -> UniversityUser:
    """FastAPI dependency to get current user with university context"""
    # Get the base user
    base_user = await get_current_user(request)
    
    # Get university context
    university_context = await get_university_context(db, base_user.id, university_id)
    
    # Create university-aware user
    university_user = UniversityUser(base_user, university_context)
    
    return university_user


async def get_current_university_user_optional(
    request: Request,
    university_id: Optional[str] = None,
    db: Session = Depends(get_db)
) -> Optional[UniversityUser]:
    """FastAPI dependency to get current user with university context (optional)"""
    try:
        base_user = await get_current_user(request)
    except HTTPException:
        return None
    
    university_context = await get_university_context(db, base_user.id, university_id)
    return UniversityUser(base_user, university_context) if base_user else None


def require_university_membership(user: UniversityUser, university_id: str) -> None:
    """Require that the user is a member of the specified university"""
    if not user.university_context or user.university_context.get("university_id") != university_id:
        raise HTTPException(
            status_code=403,
            detail=f"User is not a member of university {university_id}"
        )


def require_university_permission(user: UniversityUser, required_permission: str) -> None:
    """Require specific university permission"""
    if not user.university_context:
        raise HTTPException(
            status_code=403,
            detail="User does not have university context"
        )
    
    permissions = user.university_context.get("permissions", [])
    if required_permission not in permissions and "university_admin" not in user.university_context.get("roles", []):
        raise HTTPException(
            status_code=403,
            detail=f"University permission '{required_permission}' required"
        )


def require_university_role(user: UniversityUser, required_role: str) -> None:
    """Require specific university role"""
    if not user.university_context:
        raise HTTPException(
            status_code=403,
            detail="User does not have university context"
        )
    
    roles = user.university_context.get("roles", [])
    if required_role not in roles and "university_admin" not in roles:
        raise HTTPException(
            status_code=403,
            detail=f"University role '{required_role}' required"
        )


def create_university_aware_token(
    user: User,
    university_context: Dict[str, Any]
) -> str:
    """Create a JWT token with university context"""
    from app.core.security import create_access_token
    
    # Create a university-aware user
    university_user = UniversityUser(user, university_context)
    
    # Add university context to custom claims
    custom_claims = {
        "user_id": university_user.id,
        "email": university_user.email,
        "name": university_user.name,
        "picture": university_user.picture,
        "email_verified": university_user.email_verified,
        "roles": university_user.roles,
        "permissions": university_user.permissions,
        "university_context": university_context
    }
    
    # Use the enhanced JWT security manager
    from app.core.jwt_security import jwt_security_manager
    token_string, token_id = jwt_security_manager.create_secure_token(
        user_id=university_user.id,
        token_type="access",
        client_ip="unknown",  # Will be set by the request context
        user_agent="unknown",  # Will be set by the request context
        custom_claims=custom_claims
    )
    
    return token_string


async def switch_university_context(
    db: Session,
    user_id: str,
    university_id: str
) -> Optional[Dict[str, Any]]:
    """Switch user's active university context"""
    university_context = await get_university_context(db, user_id, university_id)
    
    if not university_context:
        raise HTTPException(
            status_code=404,
            detail=f"User is not a member of university {university_id}"
        )
    
    return university_context


# University-specific permission checks
def can_manage_university(user: UniversityUser) -> bool:
    """Check if user can manage university settings"""
    return "manage_university" in user.university_context.get("permissions", []) if user.university_context else False


def can_manage_agents(user: UniversityUser) -> bool:
    """Check if user can manage university agents"""
    return "manage_agents" in user.university_context.get("permissions", []) if user.university_context else False


def can_manage_curriculum(user: UniversityUser) -> bool:
    """Check if user can manage curriculum"""
    return "manage_curriculum" in user.university_context.get("permissions", []) if user.university_context else False


def can_participate_curriculum(user: UniversityUser) -> bool:
    """Check if user can participate in curriculum"""
    return "participate_curriculum" in user.university_context.get("permissions", []) if user.university_context else False


def can_join_competitions(user: UniversityUser) -> bool:
    """Check if user can join competitions"""
    return "join_competitions" in user.university_context.get("permissions", []) if user.university_context else False


def can_view_analytics(user: UniversityUser) -> bool:
    """Check if user can view university analytics"""
    return "view_analytics" in user.university_context.get("permissions", []) if user.university_context else False


# University membership management
async def add_user_to_university(
    db: Session,
    user_id: str,
    university_id: str,
    roles: List[str] = None,
    status: str = "active"
) -> UniversityMembership:
    """Add a user to a university"""
    if roles is None:
        roles = ["student"]  # Default role
    
    # Check if membership already exists
    existing = db.query(UniversityMembership).filter(
        UniversityMembership.user_id == user_id,
        UniversityMembership.university_id == university_id
    ).first()
    
    if existing:
        # Update existing membership
        existing.roles = roles
        existing.status = status
        db.commit()
        db.refresh(existing)
        return existing
    
    # Create new membership
    from datetime import datetime, timezone
    membership = UniversityMembership(
        user_id=user_id,
        university_id=university_id,
        roles=roles,
        status=status,
        joined_at=datetime.now(timezone.utc)
    )
    
    db.add(membership)
    db.commit()
    db.refresh(membership)
    
    return membership


async def remove_user_from_university(
    db: Session,
    user_id: str,
    university_id: str
) -> bool:
    """Remove a user from a university"""
    membership = db.query(UniversityMembership).filter(
        UniversityMembership.user_id == user_id,
        UniversityMembership.university_id == university_id
    ).first()
    
    if membership:
        membership.status = "inactive"
        db.commit()
        return True
    
    return False