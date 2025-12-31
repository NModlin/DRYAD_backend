# app/core/security.py
"""
OAuth2 Security system for DRYAD.AI Backend.
Provides Google OAuth2 authentication, JWT token validation, and user authorization.
"""

import logging
import re
import hashlib
import secrets
import jwt
import httpx
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from fastapi import HTTPException, Request, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
import html
import os

logger = logging.getLogger(__name__)

# OAuth2 Configuration - Use config system instead of direct os.getenv()
GOOGLE_DISCOVERY_URL = "https://accounts.google.com/.well-known/openid-configuration"
# JWT_SECRET_KEY is now managed by the secure config system
from app.core.config import config
from app.core.jwt_security import jwt_security_manager

# OAuth2 Configuration - Access through config system
GOOGLE_CLIENT_ID = config.GOOGLE_CLIENT_ID
GOOGLE_CLIENT_SECRET = config.GOOGLE_CLIENT_SECRET

JWT_SECRET_KEY = config.JWT_SECRET_KEY
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = int(os.getenv("JWT_EXPIRATION_HOURS", "1"))  # Short-lived access tokens (1 hour)
REFRESH_TOKEN_EXPIRATION_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRATION_DAYS", "30"))  # Long-lived refresh tokens (30 days)

# Deployment environment (affects security defaults)
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")

# Security configuration
API_KEY_LENGTH = 32  # For backward compatibility
MAX_REQUEST_SIZE = 10 * 1024 * 1024  # 10MB
RATE_LIMIT_REQUESTS = 1000  # Increased for production
RATE_LIMIT_WINDOW = 3600  # 1 hour

# In-memory storage for demo purposes (use Redis/database in production)
_rate_limit_storage: Dict[str, List[datetime]] = {}
_google_keys_cache: Dict[str, Any] = {}
_cache_expiry: Optional[datetime] = None

security = HTTPBearer()


class SecurityError(Exception):
    """Custom security exception."""
    pass


class OAuth2Error(Exception):
    """OAuth2 specific exception."""
    pass


class User(BaseModel):
    """User model for OAuth2 authentication."""
    id: str
    email: str
    name: str
    picture: Optional[str] = None
    email_verified: bool = False
    roles: List[str] = ["user"]
    permissions: List[str] = ["read", "write"]
    created_at: datetime
    last_login: Optional[datetime] = None
    is_active: bool = True


class TokenData(BaseModel):
    """Token data model parsed from DRYAD.AI access tokens."""
    user_id: str
    email: str
    name: str
    roles: List[str]
    permissions: List[str]
    email_verified: bool = False
    # Multi-client support
    client_app_id: Optional[str] = None
    tenant_id: Optional[str] = None
    organization_id: Optional[str] = None
    picture: Optional[str] = None
    exp: datetime
    iat: datetime


async def get_google_public_keys() -> Dict[str, Any]:
    """Get Google's public keys for JWT verification."""
    global _google_keys_cache, _cache_expiry

    # Check cache validity (refresh every hour)
    if _cache_expiry and datetime.utcnow() < _cache_expiry and _google_keys_cache:
        return _google_keys_cache

    try:
        async with httpx.AsyncClient() as client:
            # Get Google's OpenID configuration
            config_response = await client.get(GOOGLE_DISCOVERY_URL)
            config_response.raise_for_status()
            config = config_response.json()

            # Get the public keys
            keys_response = await client.get(config["jwks_uri"])
            keys_response.raise_for_status()
            keys_data = keys_response.json()

            _google_keys_cache = keys_data
            _cache_expiry = datetime.utcnow() + timedelta(hours=1)

            return keys_data
    except Exception as e:
        logger.error(f"Failed to fetch Google public keys: {e}")
        raise OAuth2Error("Failed to fetch Google public keys")


def create_access_token(user: User, client_ip: str = "unknown", user_agent: str = "unknown") -> str:
    """Create a secure JWT access token for a user with enhanced security."""
    # Custom claims for the user
    custom_claims = {
        "user_id": user.id,
        "email": user.email,
        "name": user.name,
        "picture": user.picture,
        "email_verified": user.email_verified,
        "roles": user.roles,
        "permissions": user.permissions
    }

    # Use enhanced JWT security manager
    token_string, token_id = jwt_security_manager.create_secure_token(
        user_id=user.id,
        token_type="access",
        client_ip=client_ip,
        user_agent=user_agent,
        custom_claims=custom_claims
    )

    return token_string


def create_refresh_token(user_id: str, device_info: Optional[str] = None, ip_address: Optional[str] = None) -> str:
    """Create a secure refresh token."""
    # Generate a cryptographically secure random token
    token = secrets.token_urlsafe(64)
    return token


def hash_refresh_token(token: str) -> str:
    """Hash a refresh token for secure storage."""
    return hashlib.sha256(token.encode()).hexdigest()


async def store_refresh_token(
    db,
    user_id: str,
    token: str,
    device_info: Optional[str] = None,
    ip_address: Optional[str] = None,
    parent_token_id: Optional[str] = None
) -> str:
    """Store a refresh token in the database."""
    from app.database.models import RefreshToken
    from sqlalchemy import select

    # Hash the token for storage
    token_hash = hash_refresh_token(token)

    # Calculate expiration
    expires_at = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRATION_DAYS)

    # Get current token version for the user
    stmt = select(RefreshToken).where(
        RefreshToken.user_id == user_id,
        RefreshToken.is_revoked == False
    ).order_by(RefreshToken.token_version.desc()).limit(1)
    result = await db.execute(stmt)
    latest_token = result.scalar_one_or_none()

    token_version = (latest_token.token_version + 1) if latest_token else 1

    # Create new refresh token record
    refresh_token = RefreshToken(
        token_hash=token_hash,
        user_id=user_id,
        expires_at=expires_at,
        device_info=device_info,
        ip_address=ip_address,
        token_version=token_version,
        parent_token_id=parent_token_id
    )

    db.add(refresh_token)
    await db.commit()
    await db.refresh(refresh_token)

    return refresh_token.id


async def verify_refresh_token(db, token: str) -> Optional[Dict[str, Any]]:
    """Verify a refresh token and return user info if valid (non-consuming)."""
    from app.database.models import RefreshToken, User
    from sqlalchemy import select

    token_hash = hash_refresh_token(token)

    stmt = select(RefreshToken).where(
        RefreshToken.token_hash == token_hash,
        RefreshToken.is_revoked == False,
        RefreshToken.expires_at > datetime.utcnow()
    )
    result = await db.execute(stmt)
    refresh_token = result.scalar_one_or_none()

    if not refresh_token:
        return None

    # Get the user (do not mutate token state in this function)
    stmt = select(User).where(User.id == refresh_token.user_id)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if not user or not user.is_active:
        return None

    return {
        "token_id": refresh_token.id,
        "user_id": user.id,
        "user": user,
        "token_version": refresh_token.token_version,
        "device_info": refresh_token.device_info
    }


async def consume_refresh_token(db, token: str) -> Optional[Dict[str, Any]]:
    """Atomically consume (revoke) a refresh token exactly once and return user info.

    Ensures strict single-success semantics under concurrency: the first caller that
    consumes the token will succeed; subsequent callers will observe the token as
    already revoked and must treat it as invalid.
    """
    from app.database.models import RefreshToken, User
    from sqlalchemy import select, update

    token_hash = hash_refresh_token(token)

    # Attempt to atomically mark the token as revoked if it's currently valid
    now = datetime.utcnow()
    upd = (
        update(RefreshToken)
        .where(
            RefreshToken.token_hash == token_hash,
            RefreshToken.is_revoked == False,
            RefreshToken.expires_at > now,
        )
        .values(is_revoked=True, revoked_at=now, last_used_at=now)
        .execution_options(synchronize_session=False)
    )
    try:
        result = await db.execute(upd)
        # If no row was updated, token was invalid/expired/revoked or race lost
        if getattr(result, "rowcount", 0) == 0:
            # No state change; treat as invalid without forcing rollback
            return None

        # Fetch the token (now revoked) to resolve user relation
        stmt = select(RefreshToken).where(RefreshToken.token_hash == token_hash)
        rt_res = await db.execute(stmt)
        refresh_token = rt_res.scalar_one_or_none()
        if not refresh_token:
            await db.rollback()
            return None

        # Load the user
        user_stmt = select(User).where(User.id == refresh_token.user_id)
        user_res = await db.execute(user_stmt)
        user = user_res.scalar_one_or_none()
        if not user or not user.is_active:
            await db.rollback()
            return None

        await db.commit()

        return {
            "token_id": refresh_token.id,
            "user_id": user.id,
            "user": user,
            "token_version": refresh_token.token_version,
            "device_info": refresh_token.device_info,
        }
    except Exception as e:
        # On SQLAlchemy concurrency/transaction errors, gracefully treat as invalid token
        try:
            from sqlalchemy.exc import SQLAlchemyError
            if isinstance(e, SQLAlchemyError):
                try:
                    await db.rollback()
                except Exception:
                    pass
                return None
        except Exception:
            # If SQLAlchemy isn't available or another issue, fall through to generic handling
            pass
        # Ensure the transaction is not left in a bad state for the caller
        try:
            await db.rollback()
        except Exception:
            pass
        raise


async def revoke_refresh_token(db, token: str) -> bool:
    """Revoke a refresh token."""
    from app.database.models import RefreshToken
    from sqlalchemy import select

    token_hash = hash_refresh_token(token)

    stmt = select(RefreshToken).where(RefreshToken.token_hash == token_hash)
    result = await db.execute(stmt)
    refresh_token = result.scalar_one_or_none()

    if refresh_token:
        refresh_token.is_revoked = True
        refresh_token.revoked_at = datetime.utcnow()
        await db.commit()
        return True

    return False


async def revoke_all_user_tokens(db, user_id: str) -> int:
    """Revoke all refresh tokens for a user. Returns count of revoked tokens."""
    from app.database.models import RefreshToken
    from sqlalchemy import select, update

    # Update all active tokens for the user
    stmt = update(RefreshToken).where(
        RefreshToken.user_id == user_id,
        RefreshToken.is_revoked == False
    ).values(
        is_revoked=True,
        revoked_at=datetime.utcnow()
    )

    result = await db.execute(stmt)
    await db.commit()

    return result.rowcount


async def verify_google_token(token: str) -> Dict[str, Any]:
    """Verify a Google OAuth2 token."""
    try:
        # Decode without verification first to get the header
        unverified_header = jwt.get_unverified_header(token)
        kid = unverified_header.get("kid")

        if not kid:
            raise OAuth2Error("Token missing key ID")

        # Get Google's public keys
        keys_data = await get_google_public_keys()

        # Find the correct key
        public_key = None
        for key in keys_data.get("keys", []):
            if key.get("kid") == kid:
                public_key = jwt.algorithms.RSAAlgorithm.from_jwk(key)
                break

        if not public_key:
            raise OAuth2Error("Public key not found")

        # Verify the token (allow small clock skew to avoid 'iat not yet valid')
        payload = jwt.decode(
            token,
            public_key,
            algorithms=["RS256"],
            audience=GOOGLE_CLIENT_ID,
            issuer="https://accounts.google.com",
            leeway=120  # seconds of leeway for iat/nbf/exp to tolerate minor clock drift
        )

        return payload
    except jwt.ExpiredSignatureError:
        raise OAuth2Error("Token has expired")
    except jwt.InvalidTokenError as e:
        raise OAuth2Error(f"Invalid token: {str(e)}")


def verify_access_token(token: str, client_ip: str = "unknown", user_agent: str = "unknown") -> TokenData:
    """Verify a DRYAD.AI access token with enhanced security."""
    try:
        # Use enhanced JWT security manager for validation
        payload = jwt_security_manager.validate_token_security(token, client_ip, user_agent)

        if not payload:
            raise OAuth2Error("Token validation failed")

        token_data = TokenData(
            user_id=payload.get("user_id") or payload.get("sub"),
            email=payload["email"],
            name=payload["name"],
            roles=payload["roles"],
            permissions=payload["permissions"],
            email_verified=bool(payload.get("email_verified", False)),
            picture=payload.get("picture"),
            exp=datetime.utcfromtimestamp(payload["exp"]),
            iat=datetime.utcfromtimestamp(payload["iat"])
        )

        return token_data
    except OAuth2Error:
        raise  # Re-raise OAuth2Error as-is
    except KeyError as e:
        raise OAuth2Error(f"Token missing required field: {str(e)}")
    except Exception as e:
        logger.error(f"Token verification error: {e}")
        raise OAuth2Error("Token verification failed")


def sanitize_input(text: str, max_length: int = 10000) -> str:
    """Sanitize user input to prevent XSS and injection attacks."""
    if not text:
        return ""

    # Truncate if too long
    if len(text) > max_length:
        text = text[:max_length]

    # HTML escape
    text = html.escape(text)

    # Remove potentially dangerous patterns
    dangerous_patterns = [
        r'<script[^>]*>.*?</script>',
        r'javascript:',
        r'vbscript:',
        r'onload\s*=',
        r'onerror\s*=',
        r'onclick\s*=',
        r'onmouseover\s*=',
    ]

    for pattern in dangerous_patterns:
        text = re.sub(pattern, '', text, flags=re.IGNORECASE | re.DOTALL)

    return text.strip()


def sanitize_filename(filename: str) -> str:
    """Sanitize filename to prevent directory traversal and command injection."""
    if not filename:
        return "unnamed_file"

    # Remove path separators and dangerous characters
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    filename = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', filename)  # Remove control characters

    # Remove shell command injection patterns
    dangerous_patterns = [
        r'\$\(',  # Command substitution
        r'`',     # Backticks
        r'\|',    # Pipes
        r'&',     # Background execution
        r';',     # Command separator
        r'\.\./', # Directory traversal
        r'\.\.\\', # Directory traversal (Windows)
    ]

    for pattern in dangerous_patterns:
        filename = re.sub(pattern, '_', filename)

    # Ensure filename is not empty and has reasonable length
    filename = filename.strip()
    if not filename or filename in ['.', '..']:
        filename = "sanitized_file"

    if len(filename) > 255:
        filename = filename[:255]

    return filename


def check_rate_limit(client_id: str, limit: int = RATE_LIMIT_REQUESTS,
                    window: int = RATE_LIMIT_WINDOW) -> bool:
    """Check if client has exceeded rate limit."""
    now = datetime.utcnow()
    cutoff = now - timedelta(seconds=window)

    # Clean old entries
    if client_id in _rate_limit_storage:
        _rate_limit_storage[client_id] = [
            req_time for req_time in _rate_limit_storage[client_id]
            if req_time > cutoff
        ]
    else:
        _rate_limit_storage[client_id] = []

    # Check limit
    if len(_rate_limit_storage[client_id]) >= limit:
        return False

    # Record this request
    _rate_limit_storage[client_id].append(now)
    return True


def get_security_headers() -> Dict[str, str]:
    """Get security headers for HTTP responses."""
    return {
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY",
        "X-XSS-Protection": "1; mode=block",
        "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
        "Content-Security-Policy": "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'",
        "Referrer-Policy": "strict-origin-when-cross-origin",
        "Permissions-Policy": "geolocation=(), microphone=(), camera=()"
    }


def get_cors_headers() -> Dict[str, str]:
    """Get CORS headers for cross-origin requests."""
    return {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type, Authorization, X-API-Key",
        "Access-Control-Max-Age": "86400"
    }


async def authenticate_request(request: Request) -> Optional[User]:
    """Authenticate a request using secure OAuth2 Bearer token.

    Security-first authentication that:
    - Only accepts Authorization: Bearer <token> header (RFC 6750 compliant)
    - Validates token format before processing
    - Implements proper error handling without information disclosure
    - Logs security events for monitoring
    """
    # Only accept Authorization header - no fallbacks for security
    auth_header = request.headers.get("Authorization")

    if not auth_header:
        logger.debug("No Authorization header provided")
        return None

    if not auth_header.startswith("Bearer "):
        logger.warning("Invalid Authorization header format - must be 'Bearer <token>'")
        return None

    token = auth_header[7:].strip()

    if not token:
        logger.warning("Empty token in Authorization header")
        return None

    # Validate token format (basic checks)
    if len(token) < 10:  # Minimum reasonable token length
        logger.warning("Token too short - possible attack")
        return None

    if len(token) > 4096:  # Maximum reasonable token length
        logger.warning("Token too long - possible attack")
        return None

    # Log authentication attempt (without token content)
    client_ip = request.client.host if request.client else "unknown"
    logger.info(f"Authentication attempt from {client_ip} (token length: {len(token)})")

    try:
        # Get user agent for enhanced security
        user_agent = request.headers.get("User-Agent", "unknown")

        # Try to verify as DRYAD.AI access token with enhanced security
        token_data = verify_access_token(token, client_ip, user_agent)

        # Create user object from verified token data
        user = User(
            id=token_data.user_id,
            email=token_data.email,
            name=token_data.name,
            picture=token_data.picture,
            email_verified=token_data.email_verified,
            roles=token_data.roles,
            permissions=token_data.permissions,
            created_at=token_data.iat,
            last_login=datetime.utcnow(),
            is_active=True
        )

        logger.info(f"Successful DRYAD.AI token authentication for user: {user.email}")
        return user

    except OAuth2Error as e:
        logger.warning(f"Authentication failed for {client_ip}: {e}")
        # SECURITY: No fallback authentication - explicit failure
        return None

    except Exception as e:
        logger.error(f"Unexpected authentication error for {client_ip}: {type(e).__name__}")
        return None


def require_authentication(user: Optional[User]) -> User:
    """Require authentication and raise exception if not authenticated."""
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Authentication required. Please provide a valid OAuth2 token.",
            headers={"WWW-Authenticate": "Bearer"}
        )
    return user


def require_permission(user: User, required_permission: str) -> None:
    """Require specific permission and raise exception if not authorized."""
    if required_permission not in user.permissions and "admin" not in user.roles:
        raise HTTPException(
            status_code=403,
            detail=f"Permission '{required_permission}' required"
        )


def require_role(user: User, required_role: str) -> None:
    """Require specific role and raise exception if not authorized."""
    if required_role not in user.roles and "admin" not in user.roles:
        raise HTTPException(
            status_code=403,
            detail=f"Role '{required_role}' required"
        )


# FastAPI Dependencies for authentication
async def get_current_user(request: Request) -> User:
    """FastAPI dependency to get current authenticated user (required)."""
    user = await authenticate_request(request)
    return require_authentication(user)


async def get_current_user_optional(request: Request) -> Optional[User]:
    """FastAPI dependency to get current user (optional authentication).

    Security Note: This function allows unauthenticated access.
    Only use for endpoints that can safely handle anonymous users.
    Always validate user permissions before accessing sensitive data.
    """
    try:
        user = await authenticate_request(request)
        if user:
            logger.debug(f"Optional authentication successful for user: {user.email}")
        else:
            logger.debug("Optional authentication: no valid token provided")
        return user
    except Exception as e:
        logger.warning(f"Optional authentication error: {type(e).__name__}")
        return None


async def get_current_user_api_key(request: Request) -> User:
    """FastAPI dependency for API key authentication (separate from OAuth2).

    This provides a secure alternative authentication method for:
    - Server-to-server communication
    - CLI tools and scripts
    - Third-party integrations

    API keys must be provided via X-API-Key header only.
    """
    from app.core.advanced_security import get_api_key_manager

    api_key = request.headers.get("X-API-Key")

    if not api_key:
        raise HTTPException(
            status_code=401,
            detail="API key required. Provide via X-API-Key header.",
            headers={"WWW-Authenticate": "ApiKey"}
        )

    # Validate API key format - support both old and new formats
    if not (api_key.startswith("gai_") or ":" in api_key):
        raise HTTPException(
            status_code=401,
            detail="Invalid API key format",
            headers={"WWW-Authenticate": "ApiKey"}
        )

    if len(api_key) < 32:
        raise HTTPException(
            status_code=401,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "ApiKey"}
        )

    try:
        # Use the advanced API key manager for validation
        api_key_manager = get_api_key_manager()
        validated_key = await api_key_manager.validate_api_key(api_key)

        if not validated_key:
            logger.warning(f"Invalid API key attempted from {request.client.host if request.client else 'unknown'}")
            raise HTTPException(
                status_code=401,
                detail="Invalid API key",
                headers={"WWW-Authenticate": "ApiKey"}
            )

        # Check rate limiting for this API key
        if not await api_key_manager.check_rate_limit(validated_key.key_id):
            logger.warning(f"Rate limit exceeded for API key {validated_key.key_id}")
            raise HTTPException(
                status_code=429,
                detail="Rate limit exceeded for API key",
                headers={"Retry-After": "3600"}
            )

        # Create a User object from the API key
        user = User(
            id=f"api_key_{validated_key.key_id}",
            email=f"api_key_{validated_key.key_id}@system.local",
            name=validated_key.name,
            roles=["api_user"],
            permissions=validated_key.permissions,
            is_active=True,
            created_at=validated_key.created_at,
            last_login=validated_key.last_used_at
        )

        # Log successful API key authentication
        logger.info(f"API key authentication successful: {validated_key.name} ({validated_key.key_id})")

        return user

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error during API key authentication: {e}")
        raise HTTPException(
            status_code=500,
            detail="Authentication service error",
            headers={"WWW-Authenticate": "ApiKey"}
        )


# User management functions

def normalize_user_id(email: str) -> str:
    """Derive a stable, deterministic user ID from an email address.

    Rules:
    - Lowercase the email to ensure case-insensitivity
    - Use a hash-based prefix to avoid leaking raw emails in primary keys and to keep IDs compact
    - The same email will always map to the same ID
    - Format: 'uid_' + blake2s(email).hexdigest()[:16]

    Backward compatibility:
    - Existing users created with provider 'sub' as primary key remain valid.
    - New users will use normalized IDs; lookups should attempt normalized ID, provider_id, or email.
    - Full DB migration to convert primary keys can be planned separately via Alembic if desired.
    """
    import hashlib
    normalized = email.strip().lower()
    digest = hashlib.blake2s(normalized.encode("utf-8"), digest_size=8).hexdigest()
    return f"uid_{digest}"


def create_user_from_google(google_payload: Dict[str, Any]) -> User:
    """Create a User object from Google OAuth2 payload, using normalized user ID.
    The provider's subject is stored in provider_id for traceability.
    """
    email = google_payload["email"]
    user_id = normalize_user_id(email)
    return User(
        id=user_id,
        email=email,
        name=google_payload.get("name", ""),
        picture=google_payload.get("picture"),
        email_verified=google_payload.get("email_verified", False),
        roles=["user"],  # Default role for new users
        permissions=["read", "write"],  # Default permissions
        created_at=datetime.utcnow(),
        last_login=datetime.utcnow(),
        is_active=True
    )


def get_user_permissions(user: User) -> List[str]:
    """Get all permissions for a user based on their roles."""
    permissions = set(user.permissions)

    # Add role-based permissions
    for role in user.roles:
        if role == "admin":
            permissions.update(["read", "write", "delete", "admin", "manage_users"])
        elif role == "moderator":
            permissions.update(["read", "write", "moderate"])
        elif role == "user":
            permissions.update(["read", "write"])

    return list(permissions)


def check_user_access(user: User, resource_owner_id: str) -> bool:
    """Check if user can access a resource owned by another user."""
    # Users can always access their own resources
    if user.id == resource_owner_id:
        return True

    # Admins can access all resources
    if "admin" in user.roles:
        return True

    # Moderators can access user resources but not admin resources
    if "moderator" in user.roles:
        return True

    return False


# OAuth2 Configuration validation
def validate_oauth2_config():
    """Validate OAuth2 configuration on startup."""
    if not GOOGLE_CLIENT_ID:
        logger.warning("GOOGLE_CLIENT_ID not set. OAuth2 authentication will not work.")

    if not GOOGLE_CLIENT_SECRET:
        logger.warning("GOOGLE_CLIENT_SECRET not set. OAuth2 authentication will not work.")

    if not os.getenv("JWT_SECRET_KEY"):
        # If ENVIRONMENT is development and key is missing, warn loudly to prevent token invalidation on reloads
        # Using a generated key causes a new key per reload which invalidates existing tokens
        logger.warning("JWT_SECRET_KEY missing. A random key will be generated on each reload which will invalidate existing tokens. Set JWT_SECRET_KEY in your .env (e.g., secrets.token_urlsafe(48)).")
    else:
        logger.info("JWT secret configured.")

    logger.info(f"OAuth2 security system initialized (env={ENVIRONMENT})")


class ClientApplicationAuth:
    """Authentication and authorization for client applications."""

    @staticmethod
    def generate_api_key() -> tuple[str, str]:
        """Generate a new API key and return (key, hash)."""
        api_key = f"gai_{secrets.token_urlsafe(32)}"
        api_key_hash = hashlib.sha256(api_key.encode()).hexdigest()
        return api_key, api_key_hash

    @staticmethod
    def verify_api_key(api_key: str, stored_hash: str) -> bool:
        """Verify an API key against its stored hash."""
        computed_hash = hashlib.sha256(api_key.encode()).hexdigest()
        return secrets.compare_digest(computed_hash, stored_hash)

    @staticmethod
    def get_api_key_prefix(api_key: str) -> str:
        """Get the prefix of an API key for identification."""
        return api_key[:12] + "..."


async def get_client_context(request: Request) -> Optional[Dict[str, Any]]:
    """
    Extract client application context from request headers.
    Supports both OAuth2 tokens and API key authentication.
    """
    try:
        # Check for API key in headers
        api_key = request.headers.get("X-API-Key")
        if api_key:
            # TODO: Validate API key against database
            # For now, return basic context
            return {
                "auth_type": "api_key",
                "client_app_id": "unknown",
                "tenant_id": None,
                "organization_id": None
            }

        # Check for OAuth2 token
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
            try:
                token_data = verify_access_token(token)
                if token_data:
                    return {
                        "auth_type": "oauth2",
                        "client_app_id": "DRYAD.AI-web",  # Default client app
                        "tenant_id": None,  # TODO: Extract from token if needed
                        "organization_id": None,  # TODO: Extract from token if needed
                        "user_id": token_data.user_id
                    }
            except OAuth2Error:
                # Token invalid, continue to return None
                pass

        return None

    except Exception as e:
        logger.error(f"Failed to extract client context: {e}")
        return None


def create_jwt_token_with_client_context(
    user_data: Dict[str, Any],
    client_app_id: Optional[str] = None,
    tenant_id: Optional[str] = None,
    organization_id: Optional[str] = None
) -> str:
    """Create JWT token with client application context."""
    payload = {
        "user_id": user_data["id"],
        "email": user_data["email"],
        "name": user_data["name"],
        "roles": user_data.get("roles", ["user"]),
        "permissions": user_data.get("permissions", ["read", "write"]),
        "email_verified": user_data.get("email_verified", False),
        "client_app_id": client_app_id,
        "tenant_id": tenant_id,
        "organization_id": organization_id,
        "iat": datetime.utcnow(),
        "exp": datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS),
        "iss": "DRYAD.AI",
        "aud": "DRYAD.AI-api"
    }

    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


# =============================================================================
# FILE SECURITY AND VIRUS SCANNING
# =============================================================================

async def scan_file_for_viruses(file_content: bytes, filename: str) -> dict:
    """Scan file content for viruses using ClamAV.

    Args:
        file_content: The file content as bytes
        filename: The filename for logging purposes

    Returns:
        dict: {
            "clean": bool,
            "threat": str or None,
            "scanner": str,
            "scan_time": float
        }
    """
    import os
    import time

    start_time = time.time()

    # Check if virus scanning is disabled via environment variable
    if os.getenv("DISABLE_VIRUS_SCANNING", "false").lower() == "true":
        scan_time = time.time() - start_time
        logger.info(f"Virus scanning disabled via DISABLE_VIRUS_SCANNING environment variable for '{filename}'")
        return {
            "clean": True,
            "threat": None,
            "scanner": "disabled",
            "scan_time": scan_time
        }

    try:
        # Try to import pyclamd for ClamAV integration
        try:
            import pyclamd
            clamav_available = True
        except ImportError:
            clamav_available = False
            logger.warning("pyclamd not installed - virus scanning disabled")

        if not clamav_available:
            # Fallback: basic file content analysis
            return await _basic_file_security_scan(file_content, filename, start_time)

        # Try to connect to ClamAV daemon
        try:
            cd = pyclamd.ClamdUnixSocket()
            if not cd.ping():
                raise ConnectionError("ClamAV daemon not responding")
        except Exception:
            try:
                # Try network socket
                cd = pyclamd.ClamdNetworkSocket()
                if not cd.ping():
                    raise ConnectionError("ClamAV daemon not responding")
            except Exception as e:
                logger.warning(f"ClamAV daemon not available: {e}")
                return await _basic_file_security_scan(file_content, filename, start_time)

        # Scan file content with ClamAV
        scan_result = cd.scan_stream(file_content)
        scan_time = time.time() - start_time

        if scan_result is None:
            # Clean file
            logger.debug(f"ClamAV scan clean for '{filename}' ({scan_time:.3f}s)")
            return {
                "clean": True,
                "threat": None,
                "scanner": "clamav",
                "scan_time": scan_time
            }
        else:
            # Threat detected
            threat_info = scan_result.get('stream', 'Unknown threat')
            logger.warning(f"ClamAV detected threat in '{filename}': {threat_info}")
            return {
                "clean": False,
                "threat": threat_info,
                "scanner": "clamav",
                "scan_time": scan_time
            }

    except Exception as e:
        logger.error(f"ClamAV scanning error for '{filename}': {e}")
        # Fallback to basic scanning
        return await _basic_file_security_scan(file_content, filename, start_time)


async def _basic_file_security_scan(file_content: bytes, filename: str, start_time: float) -> dict:
    """Basic file security scanning when ClamAV is not available.

    This provides minimal security checks:
    - File signature validation
    - Suspicious content patterns
    - Known malicious patterns
    """
    import time

    scan_time = time.time() - start_time

    # Check for suspicious file signatures
    suspicious_signatures = [
        b'\x4d\x5a',  # PE executable
        b'\x7f\x45\x4c\x46',  # ELF executable
        b'\xca\xfe\xba\xbe',  # Mach-O executable
        b'\xfe\xed\xfa\xce',  # Mach-O executable (reverse)
        b'\x50\x4b\x03\x04',  # ZIP (could contain executables)
    ]

    # Check file header for suspicious signatures
    file_header = file_content[:16] if len(file_content) >= 16 else file_content

    for signature in suspicious_signatures:
        if file_header.startswith(signature):
            logger.warning(f"Suspicious file signature detected in '{filename}'")
            return {
                "clean": False,
                "threat": "Suspicious file signature detected",
                "scanner": "basic",
                "scan_time": scan_time
            }

    # Check for suspicious content patterns
    suspicious_patterns = [
        b'<script',
        b'javascript:',
        b'vbscript:',
        b'onload=',
        b'onerror=',
        b'eval(',
        b'document.write',
        b'innerHTML',
        b'CreateObject',
        b'WScript.Shell',
        b'cmd.exe',
        b'powershell',
        b'/bin/sh',
        b'/bin/bash'
    ]

    content_lower = file_content.lower()
    for pattern in suspicious_patterns:
        if pattern in content_lower:
            logger.warning(f"Suspicious content pattern detected in '{filename}': {pattern.decode('utf-8', errors='ignore')}")
            return {
                "clean": False,
                "threat": f"Suspicious content pattern: {pattern.decode('utf-8', errors='ignore')}",
                "scanner": "basic",
                "scan_time": scan_time
            }

    # File appears clean
    logger.debug(f"Basic security scan clean for '{filename}' ({scan_time:.3f}s)")
    return {
        "clean": True,
        "threat": None,
        "scanner": "basic",
        "scan_time": scan_time
    }


# OAuth2 validation is now called explicitly from main.py after config is loaded
# validate_oauth2_config()
