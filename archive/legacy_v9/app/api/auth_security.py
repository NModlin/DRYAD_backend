# app/api/auth_security.py
"""
Enhanced authentication security endpoints for DRYAD.AI.
Provides secure logout, token management, and security monitoring.
"""

import logging
from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse

from app.core.security import get_current_user, jwt_security_manager
from app.database.models import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["Authentication Security"])


@router.post("/logout", response_model=Dict[str, str])
async def logout(
    request: Request,
    current_user: User = Depends(get_current_user)
):
    """
    Secure logout endpoint that blacklists the current token.
    
    This endpoint:
    - Immediately blacklists the current access token
    - Prevents further use of the token
    - Logs the logout event for security monitoring
    """
    try:
        # Extract token from Authorization header
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid authorization header"
            )
        
        token = auth_header[7:].strip()
        
        # Decode token to get JWT ID for blacklisting
        import jwt
        from app.core.config import config
        
        try:
            payload = jwt.decode(
                token,
                config.JWT_SECRET_KEY,
                algorithms=[config.JWT_ALGORITHM],
                options={"verify_exp": False}  # Don't verify expiration for logout
            )
            
            token_id = payload.get("jti")
            if not token_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Token missing required ID"
                )
            
            # Blacklist the token
            jwt_security_manager.blacklist_token(token_id, "user_logout")
            
            # Log successful logout
            client_ip = request.client.host if request.client else "unknown"
            logger.info(f"User {current_user.email} logged out from {client_ip}")
            
            return {
                "message": "Successfully logged out",
                "status": "success"
            }
            
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid token during logout: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid token"
            )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Logout error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Logout failed"
        )


@router.post("/logout-all", response_model=Dict[str, Any])
async def logout_all_sessions(
    request: Request,
    current_user: User = Depends(get_current_user)
):
    """
    Logout from all sessions by revoking all user tokens.
    
    This endpoint:
    - Revokes ALL tokens for the current user
    - Forces re-authentication on all devices
    - Useful for security incidents or device theft
    """
    try:
        # Revoke all tokens for the user
        revoked_count = jwt_security_manager.revoke_all_user_tokens(
            current_user.id, 
            "user_logout_all"
        )
        
        # Log the security action
        client_ip = request.client.host if request.client else "unknown"
        logger.warning(
            f"User {current_user.email} revoked all sessions ({revoked_count} tokens) from {client_ip}"
        )
        
        return {
            "message": "Successfully logged out from all sessions",
            "revoked_tokens": revoked_count,
            "status": "success"
        }
    
    except Exception as e:
        logger.error(f"Logout all sessions error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to logout from all sessions"
        )


@router.get("/security-status", response_model=Dict[str, Any])
async def get_security_status(
    current_user: User = Depends(get_current_user)
):
    """
    Get security status and statistics.
    
    Provides information about:
    - Active tokens and sessions
    - Security statistics
    - Token blacklist status
    """
    try:
        # Get security statistics
        stats = jwt_security_manager.get_security_stats()
        
        return {
            "user_id": current_user.id,
            "security_stats": stats,
            "status": "active"
        }
    
    except Exception as e:
        logger.error(f"Security status error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get security status"
        )


@router.post("/refresh-token", response_model=Dict[str, str])
async def refresh_access_token(
    request: Request,
    current_user: User = Depends(get_current_user)
):
    """
    Refresh access token with enhanced security.
    
    This endpoint:
    - Validates the current token
    - Issues a new access token
    - Maintains security context
    """
    try:
        # Get client information
        client_ip = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("User-Agent", "unknown")
        
        # Create new access token with enhanced security
        from app.core.security import create_access_token
        new_token = create_access_token(current_user, client_ip, user_agent)
        
        logger.info(f"Access token refreshed for user {current_user.email}")
        
        return {
            "access_token": new_token,
            "token_type": "bearer",
            "expires_in": config.JWT_EXPIRATION_HOURS * 3600
        }
    
    except Exception as e:
        logger.error(f"Token refresh error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to refresh token"
        )


@router.post("/security-incident", response_model=Dict[str, str])
async def report_security_incident(
    request: Request,
    current_user: User = Depends(get_current_user)
):
    """
    Report a security incident and revoke all tokens.
    
    Use this endpoint if:
    - Device is stolen or compromised
    - Suspicious activity detected
    - Account may be compromised
    """
    try:
        # Revoke all tokens immediately
        revoked_count = jwt_security_manager.revoke_all_user_tokens(
            current_user.id,
            "security_incident_reported"
        )
        
        # Log the security incident
        client_ip = request.client.host if request.client else "unknown"
        logger.critical(
            f"SECURITY INCIDENT reported by user {current_user.email} from {client_ip}. "
            f"Revoked {revoked_count} tokens."
        )
        
        return {
            "message": "Security incident reported. All sessions terminated.",
            "status": "incident_handled",
            "revoked_tokens": str(revoked_count)
        }
    
    except Exception as e:
        logger.error(f"Security incident handling error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to handle security incident"
        )


# Cleanup task for expired tokens
@router.post("/admin/cleanup-tokens", response_model=Dict[str, str])
async def cleanup_expired_tokens(
    current_user: User = Depends(get_current_user)
):
    """
    Admin endpoint to cleanup expired tokens.
    
    Note: In production, this should be a scheduled background task.
    """
    # Check if user has admin permissions
    if "admin" not in current_user.roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    try:
        # Cleanup expired tokens
        jwt_security_manager.cleanup_expired_tokens()
        
        logger.info(f"Token cleanup performed by admin {current_user.email}")
        
        return {
            "message": "Token cleanup completed",
            "status": "success"
        }
    
    except Exception as e:
        logger.error(f"Token cleanup error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Token cleanup failed"
        )
