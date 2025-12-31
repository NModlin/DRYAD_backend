# app/api/v1/endpoints/auth.py
"""
OAuth2 Authentication endpoints for DRYAD.AI Backend.
Handles Google OAuth2 login, token exchange, and user management.
"""

import logging
from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Depends, Request, Response, Cookie
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, ConfigDict, model_validator
from sqlalchemy.ext.asyncio import AsyncSession
import httpx
import secrets
from urllib.parse import urlencode

import app.core.security as security
import app.database.database as database
from app.database.models import User as UserModel
from sqlalchemy import select, or_
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

router = APIRouter()

# Wrapper dependency so tests can patch app.api.v1.endpoints.auth.database.get_db and have it take effect
# FastAPI captures the callable at definition time; this wrapper defers to the module attribute at runtime.
async def get_db_dep():
    async for session in database.get_db():
        yield session


class TokenRequest(BaseModel):
    """Request model for token exchange via Google ID token or Authorization Code."""
    model_config = ConfigDict(extra='forbid')
    google_token: Optional[str] = None
    authorization_code: Optional[str] = None
    redirect_uri: Optional[str] = None

    @model_validator(mode="before")
    def _require_one_of(cls, data):
        if not isinstance(data, dict):
            return data
        if not data.get("google_token") and not data.get("authorization_code"):
            raise ValueError("Either google_token or authorization_code must be provided")
        return data

# --- Google OAuth2 (Authorization Code Flow) helpers & endpoints ---
async def _get_google_oauth_endpoints() -> Dict[str, str]:
    """Fetch Google's OpenID configuration and return endpoints."""
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.get(security.GOOGLE_DISCOVERY_URL)
        resp.raise_for_status()
        cfg = resp.json()
        return {
            "authorization_endpoint": cfg.get("authorization_endpoint"),
            "token_endpoint": cfg.get("token_endpoint"),
        }


def _generate_pkce_pair() -> Dict[str, str]:
    """Generate PKCE code_verifier and S256 code_challenge."""
    verifier = secrets.token_urlsafe(64)
    import hashlib, base64
    challenge = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).rstrip(b"=").decode()
    return {"verifier": verifier, "challenge": challenge}


@router.get("/google/authorize")
async def google_oauth_authorize(request: Request, redirect_uri: Optional[str] = None, scope: Optional[str] = None):
    """Redirect user to Google OAuth consent screen using Authorization Code + PKCE."""
    if not security.GOOGLE_CLIENT_ID:
        raise HTTPException(status_code=500, detail="GOOGLE_CLIENT_ID not configured")

    endpoints = await _get_google_oauth_endpoints()
    authorization_endpoint = endpoints["authorization_endpoint"]
    if not authorization_endpoint:
        raise HTTPException(status_code=500, detail="Google authorization endpoint not available")

    # PKCE
    pkce = _generate_pkce_pair()
    state = secrets.token_urlsafe(24)

    # Persist state and verifier in HttpOnly cookies (dev-friendly; consider signed cookies/session store for prod)
    response = RedirectResponse(url="/")  # temp, will update url below
    response.set_cookie("oauth_state", state, httponly=True, samesite="lax", secure=False, max_age=600)
    response.set_cookie("oauth_code_verifier", pkce["verifier"], httponly=True, samesite="lax", secure=False, max_age=600)

    # Build redirect_uri default to our backend callback
    callback_url = str(request.url_for("google_oauth_callback"))
    final_redirect_uri = redirect_uri or callback_url

    # Scopes
    scopes = scope.split(" ") if scope else ["openid", "email", "profile"]

    params = {
        "client_id": security.GOOGLE_CLIENT_ID,
        "redirect_uri": final_redirect_uri,
        "response_type": "code",
        "scope": " ".join(scopes),
        "state": state,
        "code_challenge": pkce["challenge"],
        "code_challenge_method": "S256",
        "access_type": "online",
        "prompt": "consent",
    }

    auth_url = authorization_endpoint + "?" + urlencode(params)
    response.headers["Location"] = auth_url
    response.status_code = 302
    return response


async def _exchange_code_for_tokens(*, code: str, redirect_uri: str, code_verifier: Optional[str] = None) -> Dict[str, Any]:
    """Exchange authorization code for Google tokens."""
    endpoints = await _get_google_oauth_endpoints()
    token_endpoint = endpoints["token_endpoint"]
    if not token_endpoint:
        raise HTTPException(status_code=500, detail="Google token endpoint not available")

    data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": redirect_uri,
        "client_id": security.GOOGLE_CLIENT_ID,
    }
    # Web app flow usually includes client_secret; include if configured
    if security.GOOGLE_CLIENT_SECRET:
        data["client_secret"] = security.GOOGLE_CLIENT_SECRET
    if code_verifier:
        data["code_verifier"] = code_verifier

    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.post(token_endpoint, data=data, headers={"Content-Type": "application/x-www-form-urlencoded"})
        try:
            resp.raise_for_status()
        except httpx.HTTPStatusError as e:
            detail = resp.text[:300]
            logger.error(f"Google token exchange failed: {e} {detail}")
            raise HTTPException(status_code=401, detail="Google token exchange failed")
        return resp.json()


@router.get("/google/callback", name="google_oauth_callback")
async def google_oauth_callback(request: Request, response: Response, code: Optional[str] = None, state: Optional[str] = None, error: Optional[str] = None, db: AsyncSession = Depends(get_db_dep)):
    """Handle Google OAuth2 callback: validate state, exchange code, issue local tokens."""
    if error:
        raise HTTPException(status_code=401, detail=f"Google OAuth error: {error}")
    if not code or not state:
        raise HTTPException(status_code=400, detail="Missing code or state")

    # Validate state
    state_cookie = request.cookies.get("oauth_state")
    if not state_cookie or state_cookie != state:
        raise HTTPException(status_code=401, detail="Invalid OAuth state")

    # Get code_verifier
    code_verifier = request.cookies.get("oauth_code_verifier")

    # Use our callback URL as redirect_uri
    redirect_uri = str(request.url_for("google_oauth_callback"))

    # Exchange code for tokens
    tokens = await _exchange_code_for_tokens(code=code, redirect_uri=redirect_uri, code_verifier=code_verifier)
    id_token = tokens.get("id_token")
    if not id_token:
        raise HTTPException(status_code=401, detail="No id_token returned from Google")

    # Verify id_token and upsert user, then issue local tokens
    google_payload = await security.verify_google_token(id_token)

    # Upsert user (normalize id; allow lookup by provider_id/email for compatibility)
    normalized_id = security.normalize_user_id(google_payload["email"])
    stmt = select(UserModel).where(
        or_(
            UserModel.id == normalized_id,
            UserModel.provider_id == google_payload.get("sub"),
            UserModel.email == google_payload["email"]
        )
    )
    result = await db.execute(stmt)
    db_user = result.scalar_one_or_none()

    from datetime import datetime
    if db_user:
        db_user.last_login = datetime.now(timezone.utc)
        db_user.name = google_payload.get("name", db_user.name)
        db_user.picture = google_payload.get("picture", db_user.picture)
        db_user.email_verified = google_payload.get("email_verified", db_user.email_verified)
        await db.commit()

        user = security.User(
            id=db_user.id,
            email=db_user.email,
            name=db_user.name,
            picture=db_user.picture,
            email_verified=db_user.email_verified,
            roles=db_user.roles,
            permissions=db_user.permissions,
            created_at=db_user.created_at,
            last_login=db_user.last_login,
            is_active=db_user.is_active
        )
    else:
        user = security.create_user_from_google(google_payload)
        db_user = UserModel(
            id=user.id,
            email=user.email,
            name=user.name,
            picture=user.picture,
            email_verified=user.email_verified,
            roles=user.roles,
            permissions=user.permissions,
            provider="google",
            provider_id=google_payload.get("sub"),
            created_at=user.created_at,
            last_login=user.last_login,
            is_active=user.is_active,
            is_verified=user.email_verified
        )
        db.add(db_user)
        await db.commit()
        await db.refresh(db_user)

    # Extract client information for security
    device_info = request.headers.get("user-agent", "")[:500]
    client_ip = request.client.host if request.client else "unknown"

    # Issue local tokens with security context
    access_token = security.create_access_token(user, client_ip=client_ip, user_agent=device_info)
    refresh_token = security.create_refresh_token(user.id)
    await security.store_refresh_token(db=db, user_id=user.id, token=refresh_token, device_info=device_info, ip_address=client_ip)

    # Set refresh cookie
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        max_age=30 * 24 * 60 * 60,
        httponly=True,
        secure=False,
        samesite="lax",
        path="/"
    )

    # Clear temporary OAuth cookies
    response.delete_cookie("oauth_state")
    response.delete_cookie("oauth_code_verifier")

    return TokenResponse(
        access_token=access_token,
        user={
            "id": user.id,
            "email": user.email,
            "name": user.name,
            "picture": user.picture,
            "email_verified": True if user.email_verified is None else bool(user.email_verified),
            "roles": user.roles,
            "permissions": user.permissions,
            "created_at": user.created_at.isoformat(),
            "last_login": user.last_login.isoformat() if user.last_login else None,
            "is_active": user.is_active
        }
    )



class TokenResponse(BaseModel):
    """Response model for token exchange."""
    access_token: str
    token_type: str = "bearer"
    expires_in: int = 3600  # 1 hour for access token
    user: Dict[str, Any]


class RefreshRequest(BaseModel):
    """Request model for token refresh."""
    remember_me: Optional[bool] = False


class UserResponse(BaseModel):
    """Response model for user information."""
    id: str
    email: str
    name: str
    picture: Optional[str] = None
    email_verified: bool
    roles: list
    permissions: list
    created_at: str
    last_login: str = None
    is_active: bool


@router.get("/config")
async def get_auth_config():
    """Get OAuth2 configuration for frontend."""
    if not security.GOOGLE_CLIENT_ID:
        raise HTTPException(
            status_code=500,
            detail="OAuth2 not configured. Please set GOOGLE_CLIENT_ID environment variable."
        )

    # Use FRONTEND_URL from environment configuration
    from app.core.config import config
    frontend_url = config.FRONTEND_URL or "http://localhost:3000"
    redirect_uri = f"{frontend_url}/auth/callback"

    return {
        "google_client_id": security.GOOGLE_CLIENT_ID,
        "redirect_uri": redirect_uri,
        "scopes": ["openid", "email", "profile"]
    }


@router.post("/token", response_model=TokenResponse)
async def exchange_token(
    token_request: TokenRequest,
    response: Response,
    request: Request,
    db: AsyncSession = Depends(get_db_dep)
):
    """Exchange Google ID token or Authorization Code for DRYAD.AI tokens."""
    try:
        google_payload: Dict[str, Any]

        if token_request.google_token:
            # ID token exchange path
            logger.info("Exchanging Google ID token for local tokens")
            try:
                google_payload = await security.verify_google_token(token_request.google_token)
            except Exception as e:
                logger.warning(f"Google verification failed: {e}")
                raise HTTPException(status_code=401, detail="Invalid token")
        elif token_request.authorization_code:
            # Authorization code exchange path
            logger.info("Exchanging Google authorization code for ID token")
            # Determine redirect_uri (fallback to backend callback)
            default_redirect = str(request.url_for("google_oauth_callback"))
            redirect_uri = token_request.redirect_uri or default_redirect
            google_tokens = await _exchange_code_for_tokens(
                code=token_request.authorization_code,
                redirect_uri=redirect_uri
            )
            id_token = google_tokens.get("id_token")
            if not id_token:
                raise HTTPException(status_code=401, detail="No id_token returned from Google")
            try:
                google_payload = await security.verify_google_token(id_token)
            except Exception as e:
                logger.warning(f"Google verification failed: {e}")
                raise HTTPException(status_code=401, detail="Invalid token")
        else:
            raise HTTPException(status_code=422, detail="Either google_token or authorization_code must be provided")

        # Upsert user using normalized ID (backward-compatible lookup by provider_id/email)
        normalized_id = security.normalize_user_id(google_payload["email"])
        stmt = select(UserModel).where(
            or_(
                UserModel.id == normalized_id,
                UserModel.provider_id == google_payload.get("sub"),
                UserModel.email == google_payload["email"]
            )
        )
        result = await db.execute(stmt)
        db_user = result.scalar_one_or_none()

        if db_user:
            db_user.last_login = datetime.now(timezone.utc)
            db_user.name = google_payload.get("name", db_user.name)
            db_user.picture = google_payload.get("picture", db_user.picture)
            db_user.email_verified = google_payload.get("email_verified", db_user.email_verified)
            await db.commit()

            user = security.User(
                id=db_user.id,
                email=db_user.email,
                name=db_user.name,
                picture=db_user.picture,
                email_verified=db_user.email_verified,
                roles=db_user.roles,
                permissions=db_user.permissions,
                created_at=db_user.created_at,
                last_login=db_user.last_login,
                is_active=db_user.is_active
            )
        else:
            user = security.create_user_from_google(google_payload)
            db_user = UserModel(
                id=user.id,
                email=user.email,
                name=user.name,
                picture=user.picture,
                email_verified=user.email_verified,
                roles=user.roles,
                permissions=user.permissions,
                provider="google",
                provider_id=google_payload.get("sub"),
                created_at=user.created_at,
                last_login=user.last_login,
                is_active=user.is_active,
                is_verified=user.email_verified
            )
            db.add(db_user)
            await db.commit()
            await db.refresh(db_user)

        # Extract client information for security
        device_info = request.headers.get("user-agent", "")[:500]
        client_ip = request.client.host if request.client else "unknown"

        # Issue local access and refresh tokens with security context
        access_token = security.create_access_token(user, client_ip=client_ip, user_agent=device_info)
        refresh_token = security.create_refresh_token(user.id)
        await security.store_refresh_token(
            db=db,
            user_id=user.id,
            token=refresh_token,
            device_info=device_info,
            ip_address=client_ip
        )
        response.set_cookie(
            key="refresh_token",
            value=refresh_token,
            max_age=30 * 24 * 60 * 60,
            httponly=True,
            secure=False,
            samesite="lax",
            path="/"
        )

        return TokenResponse(
            access_token=access_token,
            user={
                "id": user.id,
                "email": user.email,
                "name": user.name,
                "picture": user.picture,
                "email_verified": True if user.email_verified is None else bool(user.email_verified),
                "roles": user.roles,
                "permissions": user.permissions,
                "created_at": user.created_at.isoformat(),
                "last_login": user.last_login.isoformat() if user.last_login else None,
                "is_active": user.is_active
            }
        )

    except security.OAuth2Error as e:
        raise HTTPException(status_code=401, detail=str(e))
    except HTTPException:
        raise
    except security.OAuth2Error as e:
        # Already handled above, but keep for safety
        raise HTTPException(status_code=401, detail=str(e))
    except Exception as e:
        # Map Google verification errors/timeouts to 401
        import asyncio
        if isinstance(e, asyncio.TimeoutError) or "google" in str(e).lower() or "verify" in str(e).lower():
            logger.warning(f"Google verification failed: {e}")
            raise HTTPException(status_code=401, detail="Invalid token")
        logger.error(f"Token exchange failed: {e}")
        raise HTTPException(status_code=500, detail="Token exchange failed")


@router.post("/refresh", response_model=TokenResponse)
async def refresh_access_token(
    refresh_request: Optional[RefreshRequest] = None,
    response: Response = None,
    request: Request = None,
    refresh_token: Optional[str] = Cookie(None),
    db: AsyncSession = Depends(get_db_dep)
):
    """Refresh access token using refresh token from cookie."""
    try:
        if not refresh_token:
            raise HTTPException(status_code=401, detail="Refresh token not provided")

        # Atomically consume the refresh token to enforce single-use semantics
        token_data = await security.consume_refresh_token(db, refresh_token)
        if not token_data:
            raise HTTPException(status_code=401, detail="Invalid or expired refresh token")

        user = token_data["user"]

        # Create new access token
        access_token = security.create_access_token(user)

        # Create new refresh token (token rotation)
        device_info = request.headers.get("user-agent", "")[:500]
        client_ip = request.client.host if request.client else None
        new_refresh_token = security.create_refresh_token(user.id, device_info, client_ip)

        # Store new refresh token (link to consumed parent)
        await security.store_refresh_token(
            db=db,
            user_id=user.id,
            token=new_refresh_token,
            device_info=device_info,
            ip_address=client_ip,
            parent_token_id=token_data["token_id"]
        )

        # Set new refresh token cookie
        remember_me = bool(refresh_request.remember_me) if refresh_request else False
        cookie_max_age = 30 * 24 * 60 * 60 if remember_me else None  # 30 days or session
        response.set_cookie(
            key="refresh_token",
            value=new_refresh_token,
            max_age=cookie_max_age,
            httponly=True,
            secure=False,  # Set to False for localhost development
            samesite="lax",
            path="/"
        )

        return TokenResponse(
            access_token=access_token,
            user={
                "id": user.id,
                "email": user.email,
                "name": user.name,
                "picture": user.picture,
                "email_verified": True if user.email_verified is None else bool(user.email_verified),
                "roles": user.roles,
                "permissions": user.permissions,
                "created_at": user.created_at.isoformat(),
                "last_login": user.last_login.isoformat() if user.last_login else None,
                "is_active": user.is_active
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token refresh failed: {e}")
        raise HTTPException(status_code=500, detail="Token refresh failed")


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: security.User = Depends(security.get_current_user)):
    """Get current user information."""
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        name=current_user.name,
        picture=current_user.picture,
        email_verified=True if current_user.email_verified is None else bool(current_user.email_verified),
        roles=current_user.roles,
        permissions=current_user.permissions,
        created_at=current_user.created_at.isoformat(),
        last_login=current_user.last_login.isoformat() if current_user.last_login else None,
        is_active=current_user.is_active
    )


@router.post("/logout")
async def logout(
    response: Response,
    refresh_token: Optional[str] = Cookie(None),
    current_user: Optional[security.User] = Depends(security.get_current_user_optional),
    db: AsyncSession = Depends(get_db_dep)
):
    """Logout current user and revoke refresh tokens."""
    try:
        # Revoke the specific refresh token if provided
        if refresh_token:
            await security.revoke_refresh_token(db, refresh_token)

        # Optionally revoke all user tokens for complete logout
        # await revoke_all_user_tokens(db, current_user.id)

        # Clear refresh token cookie
        response.delete_cookie(
            key="refresh_token",
            httponly=True,
            secure=True,
            samesite="lax",
            path="/"
        )

        logger.info(f"User {current_user.email} logged out")
        return {"message": "Successfully logged out"}

    except Exception as e:
        logger.error(f"Logout failed: {e}")
        # Still return success to avoid revealing internal errors
        return {"message": "Successfully logged out"}


@router.get("/verify")
async def verify_token(current_user: security.User = Depends(security.get_current_user_optional)):
    """Verify if the current token is valid."""
    if current_user:
        return {
            "valid": True,
            "user": {
                "id": current_user.id,
                "email": current_user.email,
                "name": current_user.name
            }
        }
    else:
        return {"valid": False}
