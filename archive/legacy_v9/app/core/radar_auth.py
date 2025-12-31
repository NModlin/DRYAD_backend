"""
RADAR Authentication Module

Flexible JWT authentication that supports both DRYAD.AI and RADAR token formats.
"""

import logging
import os
from typing import Optional, Dict, Any
from datetime import datetime, timezone
import jwt
from fastapi import Request, HTTPException
from pydantic import BaseModel

from app.core.config import config
from app.core.security import User

logger = logging.getLogger(__name__)


class RADARTokenData(BaseModel):
    """Token data parsed from RADAR JWT tokens."""
    sub: str  # User ID
    userId: str
    email: str
    username: str
    role: str  # 'user', 'admin', 'support'
    iss: str  # Issuer
    aud: str  # Audience
    iat: datetime
    exp: datetime


class RADARAuthManager:
    """
    Manages authentication for RADAR integration.
    
    Supports both:
    - DRYAD.AI tokens (issuer="DRYAD.AI", audience="DRYAD.AI-api")
    - RADAR tokens (issuer="radar-auth-service", audience="radar-platform")
    """
    
    def __init__(self):
        # JWT configuration for RADAR tokens
        self.radar_jwt_secret = os.getenv("RADAR_JWT_SECRET", config.JWT_SECRET_KEY)
        self.radar_jwt_algorithm = os.getenv("RADAR_JWT_ALGORITHM", "HS256")
        
        # Expected RADAR token claims
        self.radar_issuer = "radar-auth-service"
        self.radar_audience = "radar-platform"
        
        # DRYAD.AI token claims (for backward compatibility)
        self.gremlins_issuer = "DRYAD.AI"
        self.gremlins_audience = "DRYAD.AI-api"
        
        logger.info("✅ RADAR Auth Manager initialized")
        if self.radar_jwt_secret != config.JWT_SECRET_KEY:
            logger.info("🔐 Using separate JWT secret for RADAR tokens")
    
    def validate_radar_token(self, token: str) -> Optional[RADARTokenData]:
        """
        Validate a RADAR JWT token.
        
        Args:
            token: JWT token string
            
        Returns:
            RADARTokenData if valid, None if invalid
        """
        try:
            # Decode and validate RADAR token
            payload = jwt.decode(
                token,
                self.radar_jwt_secret,
                algorithms=[self.radar_jwt_algorithm],
                audience=self.radar_audience,
                issuer=self.radar_issuer
            )
            
            # Extract required fields
            token_data = RADARTokenData(
                sub=payload.get("sub"),
                userId=payload.get("userId") or payload.get("sub"),
                email=payload.get("email"),
                username=payload.get("username"),
                role=payload.get("role", "user"),
                iss=payload.get("iss"),
                aud=payload.get("aud"),
                iat=datetime.fromtimestamp(payload["iat"], tz=timezone.utc),
                exp=datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
            )
            
            logger.debug(f"✅ Valid RADAR token for user: {token_data.username}")
            return token_data
            
        except jwt.ExpiredSignatureError:
            logger.debug("RADAR token expired")
            return None
        except jwt.InvalidAudienceError:
            logger.debug("Invalid RADAR token audience")
            return None
        except jwt.InvalidIssuerError:
            logger.debug("Invalid RADAR token issuer")
            return None
        except jwt.InvalidTokenError as e:
            logger.debug(f"Invalid RADAR token: {e}")
            return None
        except Exception as e:
            logger.error(f"Error validating RADAR token: {e}")
            return None
    
    def validate_gremlins_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Validate a DRYAD.AI JWT token.
        
        Args:
            token: JWT token string
            
        Returns:
            Token payload if valid, None if invalid
        """
        try:
            # Decode and validate DRYAD.AI token
            payload = jwt.decode(
                token,
                config.JWT_SECRET_KEY,
                algorithms=[config.JWT_ALGORITHM],
                audience=self.gremlins_audience,
                issuer=self.gremlins_issuer
            )
            
            logger.debug(f"✅ Valid DRYAD.AI token for user: {payload.get('email')}")
            return payload
            
        except jwt.ExpiredSignatureError:
            logger.debug("DRYAD.AI token expired")
            return None
        except jwt.InvalidTokenError as e:
            logger.debug(f"Invalid DRYAD.AI token: {e}")
            return None
        except Exception as e:
            logger.error(f"Error validating DRYAD.AI token: {e}")
            return None
    
    def validate_token_flexible(self, token: str) -> Optional[User]:
        """
        Validate token with flexible issuer/audience support.
        
        Tries RADAR token format first, then falls back to DRYAD.AI format.
        
        Args:
            token: JWT token string
            
        Returns:
            User object if valid, None if invalid
        """
        # Try RADAR token format first
        radar_data = self.validate_radar_token(token)
        if radar_data:
            # Convert RADAR token data to User object
            return User(
                id=radar_data.userId,
                email=radar_data.email,
                name=radar_data.username,
                picture=None,
                email_verified=True,
                roles=[radar_data.role],
                permissions=self._get_permissions_for_role(radar_data.role),
                created_at=radar_data.iat,
                last_login=datetime.now(timezone.utc),
                is_active=True
            )
        
        # Fall back to DRYAD.AI token format
        gremlins_payload = self.validate_gremlins_token(token)
        if gremlins_payload:
            # Convert DRYAD.AI token to User object
            return User(
                id=gremlins_payload.get("user_id") or gremlins_payload.get("sub"),
                email=gremlins_payload["email"],
                name=gremlins_payload["name"],
                picture=gremlins_payload.get("picture"),
                email_verified=bool(gremlins_payload.get("email_verified", False)),
                roles=gremlins_payload.get("roles", ["user"]),
                permissions=gremlins_payload.get("permissions", ["read", "write"]),
                created_at=datetime.fromtimestamp(gremlins_payload["iat"], tz=timezone.utc),
                last_login=datetime.now(timezone.utc),
                is_active=True
            )
        
        return None
    
    def _get_permissions_for_role(self, role: str) -> list:
        """Map RADAR roles to permissions."""
        role_permissions = {
            "admin": ["read", "write", "delete", "admin"],
            "support": ["read", "write"],
            "user": ["read", "write"]
        }
        return role_permissions.get(role, ["read"])


# Global RADAR auth manager instance
radar_auth_manager = RADARAuthManager()


async def authenticate_radar_request(request: Request) -> Optional[User]:
    """
    Authenticate a request using flexible JWT validation.
    
    Supports both RADAR and DRYAD.AI token formats.
    
    Args:
        request: FastAPI request object
        
    Returns:
        User object if authenticated, None otherwise
    """
    # Extract Bearer token from Authorization header
    auth_header = request.headers.get("Authorization")
    
    if not auth_header:
        logger.debug("No Authorization header provided")
        return None
    
    if not auth_header.startswith("Bearer "):
        logger.warning("Invalid Authorization header format - must be 'Bearer <token>'")
        return None
    
    token = auth_header[7:]  # Remove "Bearer " prefix
    
    # Validate token with flexible issuer/audience support
    user = radar_auth_manager.validate_token_flexible(token)
    
    if user:
        logger.info(f"✅ Authenticated user: {user.email} (roles: {user.roles})")
    else:
        logger.warning("❌ Token validation failed")
    
    return user


async def get_radar_user(request: Request) -> User:
    """
    FastAPI dependency to get authenticated RADAR user (required).
    
    Raises HTTPException if not authenticated.
    """
    user = await authenticate_radar_request(request)
    
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Authentication required. Please provide a valid JWT token.",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    return user


async def get_radar_user_optional(request: Request) -> Optional[User]:
    """
    FastAPI dependency to get authenticated RADAR user (optional).
    
    Returns None if not authenticated (no exception raised).
    """
    return await authenticate_radar_request(request)

