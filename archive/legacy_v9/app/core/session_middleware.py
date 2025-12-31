"""
Session Middleware for DRYAD.AI Backend
Integrates secure session management with FastAPI requests.
"""

import time
from typing import Optional
from fastapi import Request, Response, HTTPException
from fastapi.responses import JSONResponse

from app.core.logging_config import get_logger
from app.core.session_management import get_session_manager, SessionData
from app.core.audit_logging import get_audit_logger, AuditEventType, AuditSeverity

logger = get_logger(__name__)


class SessionMiddleware:
    """Middleware for session management integration."""
    
    def __init__(self):
        self.session_manager = get_session_manager()
        self.audit_logger = get_audit_logger()
        
        # Session configuration
        self.session_cookie_name = "gremlins_session"
        self.session_cookie_secure = True  # Set to False for development
        self.session_cookie_httponly = True
        self.session_cookie_samesite = "strict"
        self.session_cookie_max_age = 3600  # 1 hour
        
        # Endpoints that require session validation
        self.session_required_endpoints = {
            '/api/v1/users/profile',
            '/api/v1/users/settings',
            '/api/v1/admin',
            '/api/v1/api-keys'
        }
        
        # Endpoints that create sessions
        self.session_creation_endpoints = {
            '/api/v1/auth/login',
            '/api/v1/auth/oauth/callback'
        }
        
        # Endpoints that destroy sessions
        self.session_destruction_endpoints = {
            '/api/v1/auth/logout'
        }
    
    async def __call__(self, request: Request, call_next):
        """Process request with session management."""
        start_time = time.time()
        
        # Get client information
        client_ip = self._get_client_ip(request)
        user_agent = request.headers.get("user-agent", "")
        path = str(request.url.path)
        
        # Check for existing session
        session_id = self._get_session_id_from_request(request)
        session_data = None
        
        if session_id:
            session_data = self.session_manager.validate_session(
                session_id, client_ip, user_agent
            )
            
            if session_data:
                # Attach session data to request
                request.state.session_id = session_id
                request.state.session_data = session_data
                request.state.user_id = session_data.user_id
            else:
                # Invalid or expired session
                await self._log_session_event(
                    "invalid_session_attempt", session_id, client_ip, user_agent
                )
        
        # Check if session is required for this endpoint
        requires_session = any(
            endpoint in path for endpoint in self.session_required_endpoints
        )
        
        if requires_session and not session_data:
            return JSONResponse(
                status_code=401,
                content={"error": "Valid session required"}
            )
        
        # Process the request
        response = await call_next(request)
        
        # Handle session creation
        if any(endpoint in path for endpoint in self.session_creation_endpoints):
            if hasattr(request.state, 'create_session') and request.state.create_session:
                new_session_id = self.session_manager.create_session(
                    user_id=request.state.user_id,
                    ip_address=client_ip,
                    user_agent=user_agent
                )
                
                # Set session cookie
                self._set_session_cookie(response, new_session_id)
                
                logger.info(f"Created new session {new_session_id} for user {request.state.user_id}")
        
        # Handle session destruction
        if any(endpoint in path for endpoint in self.session_destruction_endpoints):
            if session_id:
                self.session_manager.invalidate_session(session_id, "user_logout")
                self._clear_session_cookie(response)
                
                logger.info(f"Destroyed session {session_id}")
        
        # Update session cookie if session exists and is valid
        if session_data and session_data.session_id:
            self._refresh_session_cookie(response, session_data.session_id)
        
        # Log session activity
        duration = time.time() - start_time
        if session_data:
            logger.debug(f"Session {session_data.session_id} processed request to {path} in {duration:.3f}s")
        
        return response
    
    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP address from request."""
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip
        
        if request.client:
            return request.client.host
        
        return "unknown"
    
    def _get_session_id_from_request(self, request: Request) -> Optional[str]:
        """Extract session ID from request cookies or headers."""
        # Try cookie first
        session_id = request.cookies.get(self.session_cookie_name)
        if session_id:
            return session_id
        
        # Try Authorization header as fallback
        auth_header = request.headers.get("authorization")
        if auth_header and auth_header.startswith("Session "):
            return auth_header[8:]  # Remove "Session " prefix
        
        return None
    
    def _set_session_cookie(self, response: Response, session_id: str):
        """Set session cookie in response."""
        response.set_cookie(
            key=self.session_cookie_name,
            value=session_id,
            max_age=self.session_cookie_max_age,
            httponly=self.session_cookie_httponly,
            secure=self.session_cookie_secure,
            samesite=self.session_cookie_samesite,
            path="/"
        )
    
    def _refresh_session_cookie(self, response: Response, session_id: str):
        """Refresh session cookie expiration."""
        response.set_cookie(
            key=self.session_cookie_name,
            value=session_id,
            max_age=self.session_cookie_max_age,
            httponly=self.session_cookie_httponly,
            secure=self.session_cookie_secure,
            samesite=self.session_cookie_samesite,
            path="/"
        )
    
    def _clear_session_cookie(self, response: Response):
        """Clear session cookie from response."""
        response.delete_cookie(
            key=self.session_cookie_name,
            path="/",
            secure=self.session_cookie_secure,
            httponly=self.session_cookie_httponly,
            samesite=self.session_cookie_samesite
        )
    
    async def _log_session_event(self, event_type: str, session_id: str,
                                client_ip: str, user_agent: str):
        """Log session-related security events."""
        try:
            details = {
                "event_type": event_type,
                "session_id": session_id,
                "user_agent": user_agent[:200]  # Truncate for logging
            }
            
            self.audit_logger.log_security_event(
                event_type=AuditEventType.SECURITY_VIOLATION,
                severity=AuditSeverity.MEDIUM,
                ip_address=client_ip,
                details=details,
                risk_score=50
            )
            
        except Exception as e:
            logger.error(f"Error logging session event: {e}")


class SessionHelper:
    """Helper class for session operations in endpoints."""
    
    @staticmethod
    def get_session_data(request: Request) -> Optional[SessionData]:
        """Get session data from request."""
        return getattr(request.state, 'session_data', None)
    
    @staticmethod
    def get_user_id(request: Request) -> Optional[str]:
        """Get user ID from session."""
        return getattr(request.state, 'user_id', None)
    
    @staticmethod
    def get_session_id(request: Request) -> Optional[str]:
        """Get session ID from request."""
        return getattr(request.state, 'session_id', None)
    
    @staticmethod
    def mark_for_session_creation(request: Request, user_id: str):
        """Mark request for session creation."""
        request.state.create_session = True
        request.state.user_id = user_id
    
    @staticmethod
    def set_session_data(request: Request, key: str, value: any) -> bool:
        """Set data in current session."""
        session_id = SessionHelper.get_session_id(request)
        if not session_id:
            return False
        
        session_manager = get_session_manager()
        return session_manager.set_session_data(session_id, key, value)
    
    @staticmethod
    def get_session_value(request: Request, key: str) -> any:
        """Get data from current session."""
        session_id = SessionHelper.get_session_id(request)
        if not session_id:
            return None
        
        session_manager = get_session_manager()
        return session_manager.get_session_data(session_id, key)
    
    @staticmethod
    def invalidate_session(request: Request, reason: str = "manual") -> bool:
        """Invalidate current session."""
        session_id = SessionHelper.get_session_id(request)
        if not session_id:
            return False
        
        session_manager = get_session_manager()
        return session_manager.invalidate_session(session_id, reason)
    
    @staticmethod
    def get_user_sessions(request: Request) -> list:
        """Get all sessions for current user."""
        user_id = SessionHelper.get_user_id(request)
        if not user_id:
            return []
        
        session_manager = get_session_manager()
        return session_manager.get_user_sessions(user_id)


# Global session middleware instance
_session_middleware: Optional[SessionMiddleware] = None


def get_session_middleware() -> SessionMiddleware:
    """Get the global session middleware instance."""
    global _session_middleware
    if _session_middleware is None:
        _session_middleware = SessionMiddleware()
    return _session_middleware
