"""
API Key Management Endpoints for DRYAD.AI Backend
Provides secure API key creation, management, and administration.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from pydantic import BaseModel, Field
import logging

from app.core.security import get_current_user, User
from app.core.advanced_security import get_api_key_manager, APIKey
from app.core.logging_config import get_logger

logger = get_logger(__name__)
router = APIRouter()


class APIKeyCreateRequest(BaseModel):
    """Request model for creating API keys."""
    name: str = Field(..., min_length=1, max_length=100, description="Human-readable name for the API key")
    permissions: List[str] = Field(default=["read"], description="List of permissions for the API key")
    expires_in_days: Optional[int] = Field(default=None, ge=1, le=365, description="Expiration in days (max 365)")
    rate_limit: int = Field(default=1000, ge=1, le=10000, description="Requests per hour limit")


class APIKeyResponse(BaseModel):
    """Response model for API key information."""
    key_id: str
    name: str
    permissions: List[str]
    created_at: datetime
    expires_at: Optional[datetime]
    last_used_at: Optional[datetime]
    usage_count: int
    rate_limit: int
    is_active: bool


class APIKeyCreateResponse(BaseModel):
    """Response model for API key creation."""
    api_key: str = Field(..., description="The actual API key - store securely, won't be shown again")
    key_id: str
    name: str
    permissions: List[str]
    expires_at: Optional[datetime]
    rate_limit: int
    warning: str = Field(default="Store this API key securely. It will not be displayed again.")


@router.post("/create", response_model=APIKeyCreateResponse, status_code=status.HTTP_201_CREATED)
async def create_api_key(
    request: APIKeyCreateRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Create a new API key for the authenticated user.
    
    **Security Requirements:**
    - User must be authenticated via OAuth2
    - API key will be associated with the user's permissions
    - Rate limiting applies per API key
    
    **Important:** The API key will only be shown once. Store it securely.
    """
    try:
        # Validate permissions against user's permissions
        if not all(perm in current_user.permissions for perm in request.permissions):
            raise HTTPException(
                status_code=403,
                detail="Cannot grant permissions you don't have"
            )
        
        # Create the API key
        api_key_manager = get_api_key_manager()
        api_key_string, key_id = await api_key_manager.create_api_key(
            name=f"{current_user.name} - {request.name}",
            permissions=request.permissions,
            expires_in_days=request.expires_in_days,
            rate_limit=request.rate_limit
        )
        
        # Calculate expiration datetime
        expires_at = None
        if request.expires_in_days:
            expires_at = datetime.utcnow() + timedelta(days=request.expires_in_days)
        
        logger.info(f"API key created for user {current_user.id}: {request.name} ({key_id})")
        
        return APIKeyCreateResponse(
            api_key=api_key_string,
            key_id=key_id,
            name=request.name,
            permissions=request.permissions,
            expires_at=expires_at,
            rate_limit=request.rate_limit
        )
        
    except Exception as e:
        logger.error(f"Error creating API key for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to create API key"
        )


@router.get("/list", response_model=List[APIKeyResponse])
async def list_api_keys(current_user: User = Depends(get_current_user)):
    """
    List all API keys for the authenticated user.
    
    **Note:** The actual API key values are not returned for security.
    """
    try:
        api_key_manager = get_api_key_manager()
        
        # Filter API keys for this user (based on name prefix)
        user_keys = []
        user_prefix = f"{current_user.name} - "
        
        for key_id, api_key in api_key_manager.api_keys.items():
            if api_key.name.startswith(user_prefix):
                user_keys.append(APIKeyResponse(
                    key_id=key_id,
                    name=api_key.name.replace(user_prefix, ""),  # Remove user prefix
                    permissions=api_key.permissions,
                    created_at=datetime.fromtimestamp(api_key.created_at),
                    expires_at=datetime.fromtimestamp(api_key.expires_at) if api_key.expires_at else None,
                    last_used_at=datetime.fromtimestamp(api_key.last_used_at) if api_key.last_used_at else None,
                    usage_count=api_key.usage_count,
                    rate_limit=api_key.rate_limit,
                    is_active=api_key.is_active
                ))
        
        return user_keys
        
    except Exception as e:
        logger.error(f"Error listing API keys for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to list API keys"
        )


@router.delete("/{key_id}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_api_key(
    key_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Revoke (deactivate) an API key.
    
    **Security:** Users can only revoke their own API keys.
    """
    try:
        api_key_manager = get_api_key_manager()
        
        # Check if key exists and belongs to user
        if key_id not in api_key_manager.api_keys:
            raise HTTPException(
                status_code=404,
                detail="API key not found"
            )
        
        api_key = api_key_manager.api_keys[key_id]
        user_prefix = f"{current_user.name} - "
        
        if not api_key.name.startswith(user_prefix):
            raise HTTPException(
                status_code=403,
                detail="Cannot revoke API key that doesn't belong to you"
            )
        
        # Revoke the key
        success = await api_key_manager.revoke_api_key(key_id)
        
        if not success:
            raise HTTPException(
                status_code=500,
                detail="Failed to revoke API key"
            )
        
        logger.info(f"API key revoked by user {current_user.id}: {key_id}")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error revoking API key {key_id} for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to revoke API key"
        )


@router.post("/{key_id}/rotate", response_model=APIKeyCreateResponse)
async def rotate_api_key(
    key_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Rotate an API key (create new key, schedule old for deprecation).
    
    **Security:** Users can only rotate their own API keys.
    **Important:** The new API key will only be shown once. Store it securely.
    """
    try:
        api_key_manager = get_api_key_manager()
        
        # Check if key exists and belongs to user
        if key_id not in api_key_manager.api_keys:
            raise HTTPException(
                status_code=404,
                detail="API key not found"
            )
        
        api_key = api_key_manager.api_keys[key_id]
        user_prefix = f"{current_user.name} - "
        
        if not api_key.name.startswith(user_prefix):
            raise HTTPException(
                status_code=403,
                detail="Cannot rotate API key that doesn't belong to you"
            )
        
        # Rotate the key
        result = await api_key_manager.rotate_api_key(key_id)
        
        if not result:
            raise HTTPException(
                status_code=500,
                detail="Failed to rotate API key"
            )
        
        new_key_string, new_key_id = result
        new_api_key = api_key_manager.api_keys[new_key_id]
        
        logger.info(f"API key rotated by user {current_user.id}: {key_id} -> {new_key_id}")
        
        return APIKeyCreateResponse(
            api_key=new_key_string,
            key_id=new_key_id,
            name=api_key.name.replace(user_prefix, ""),
            permissions=new_api_key.permissions,
            expires_at=datetime.fromtimestamp(new_api_key.expires_at) if new_api_key.expires_at else None,
            rate_limit=new_api_key.rate_limit,
            warning="Store this new API key securely. The old key will be deprecated in 30 days."
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error rotating API key {key_id} for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to rotate API key"
        )


@router.get("/{key_id}/usage", response_model=Dict[str, Any])
async def get_api_key_usage(
    key_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Get usage statistics for an API key.
    
    **Security:** Users can only view usage for their own API keys.
    """
    try:
        api_key_manager = get_api_key_manager()
        
        # Check if key exists and belongs to user
        if key_id not in api_key_manager.api_keys:
            raise HTTPException(
                status_code=404,
                detail="API key not found"
            )
        
        api_key = api_key_manager.api_keys[key_id]
        user_prefix = f"{current_user.name} - "
        
        if not api_key.name.startswith(user_prefix):
            raise HTTPException(
                status_code=403,
                detail="Cannot view usage for API key that doesn't belong to you"
            )
        
        # Get current hour usage
        current_hour_usage = len(api_key_manager.rate_limit_storage.get(key_id, []))
        
        return {
            "key_id": key_id,
            "name": api_key.name.replace(user_prefix, ""),
            "total_usage": api_key.usage_count,
            "current_hour_usage": current_hour_usage,
            "rate_limit": api_key.rate_limit,
            "rate_limit_remaining": max(0, api_key.rate_limit - current_hour_usage),
            "last_used_at": datetime.fromtimestamp(api_key.last_used_at) if api_key.last_used_at else None,
            "is_active": api_key.is_active
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting usage for API key {key_id} for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to get API key usage"
        )
