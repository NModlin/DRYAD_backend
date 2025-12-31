"""
Secure Session Management for DRYAD.AI Backend
Provides secure session handling, timeout management, and session security features.
"""

import time
import secrets
import hashlib
import json
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
from enum import Enum
import threading

from app.core.logging_config import get_logger
from app.core.audit_logging import get_audit_logger, AuditEventType, AuditSeverity

logger = get_logger(__name__)


class SessionStatus(Enum):
    """Session status enumeration."""
    ACTIVE = "active"
    EXPIRED = "expired"
    INVALIDATED = "invalidated"
    SUSPICIOUS = "suspicious"


@dataclass
class SessionData:
    """Session data structure."""
    session_id: str
    user_id: str
    created_at: datetime
    last_accessed: datetime
    expires_at: datetime
    ip_address: str
    user_agent: str
    status: SessionStatus = SessionStatus.ACTIVE
    access_count: int = 0
    data: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.data is None:
            self.data = {}


class SecureSessionManager:
    """Secure session management system."""
    
    def __init__(self):
        self.audit_logger = get_audit_logger()
        self.sessions: Dict[str, SessionData] = {}
        self.user_sessions: Dict[str, List[str]] = {}  # user_id -> [session_ids]
        self.lock = threading.RLock()
        
        # Configuration
        self.session_timeout = 3600  # 1 hour in seconds
        self.max_sessions_per_user = 5
        self.session_cleanup_interval = 300  # 5 minutes
        self.suspicious_access_threshold = 100  # requests per session
        
        # Start cleanup thread
        self._start_cleanup_thread()
        
        logger.info("Secure session manager initialized")
    
    def create_session(self, user_id: str, ip_address: str, user_agent: str,
                      session_duration: Optional[int] = None) -> str:
        """Create a new secure session."""
        with self.lock:
            # Generate secure session ID
            session_id = self._generate_session_id()
            
            # Calculate expiration
            duration = session_duration or self.session_timeout
            now = datetime.now(timezone.utc)
            expires_at = now + timedelta(seconds=duration)
            
            # Create session data
            session = SessionData(
                session_id=session_id,
                user_id=user_id,
                created_at=now,
                last_accessed=now,
                expires_at=expires_at,
                ip_address=ip_address,
                user_agent=user_agent,
                status=SessionStatus.ACTIVE
            )
            
            # Check session limits per user
            self._enforce_session_limits(user_id)
            
            # Store session
            self.sessions[session_id] = session
            
            # Track user sessions
            if user_id not in self.user_sessions:
                self.user_sessions[user_id] = []
            self.user_sessions[user_id].append(session_id)
            
            # Log session creation
            self.audit_logger.log_authentication_event(
                event_type=AuditEventType.LOGIN_SUCCESS,
                user_id=user_id,
                ip_address=ip_address,
                user_agent=user_agent,
                outcome="success",
                details={
                    "session_id": session_id,
                    "expires_at": expires_at.isoformat(),
                    "duration": duration
                }
            )
            
            logger.info(f"Created session {session_id} for user {user_id}")
            return session_id
    
    def validate_session(self, session_id: str, ip_address: str = None,
                        user_agent: str = None) -> Optional[SessionData]:
        """Validate and update session."""
        with self.lock:
            session = self.sessions.get(session_id)
            if not session:
                return None
            
            now = datetime.now(timezone.utc)
            
            # Check if session is expired
            if now > session.expires_at:
                session.status = SessionStatus.EXPIRED
                self._log_session_event("session_expired", session)
                return None
            
            # Check if session is invalidated
            if session.status != SessionStatus.ACTIVE:
                return None
            
            # Validate IP address (optional strict mode)
            if ip_address and session.ip_address != ip_address:
                # Log suspicious activity but don't invalidate (could be legitimate)
                self._log_session_event("ip_address_changed", session, {
                    "original_ip": session.ip_address,
                    "new_ip": ip_address
                })
            
            # Update session
            session.last_accessed = now
            session.access_count += 1
            
            # Check for suspicious activity
            if session.access_count > self.suspicious_access_threshold:
                session.status = SessionStatus.SUSPICIOUS
                self._log_session_event("suspicious_activity", session, {
                    "access_count": session.access_count,
                    "threshold": self.suspicious_access_threshold
                })
            
            # Extend session if needed (sliding window)
            time_until_expiry = (session.expires_at - now).total_seconds()
            if time_until_expiry < self.session_timeout / 2:
                session.expires_at = now + timedelta(seconds=self.session_timeout)
            
            return session
    
    def invalidate_session(self, session_id: str, reason: str = "logout") -> bool:
        """Invalidate a specific session."""
        with self.lock:
            session = self.sessions.get(session_id)
            if not session:
                return False
            
            session.status = SessionStatus.INVALIDATED
            
            # Remove from user sessions
            if session.user_id in self.user_sessions:
                try:
                    self.user_sessions[session.user_id].remove(session_id)
                    if not self.user_sessions[session.user_id]:
                        del self.user_sessions[session.user_id]
                except ValueError:
                    pass
            
            # Log session invalidation
            self.audit_logger.log_authentication_event(
                event_type=AuditEventType.LOGOUT,
                user_id=session.user_id,
                ip_address=session.ip_address,
                user_agent=session.user_agent,
                outcome="success",
                details={
                    "session_id": session_id,
                    "reason": reason,
                    "duration": (datetime.now(timezone.utc) - session.created_at).total_seconds()
                }
            )
            
            logger.info(f"Invalidated session {session_id} for user {session.user_id} (reason: {reason})")
            return True
    
    def invalidate_user_sessions(self, user_id: str, except_session: str = None) -> int:
        """Invalidate all sessions for a user."""
        with self.lock:
            if user_id not in self.user_sessions:
                return 0
            
            session_ids = self.user_sessions[user_id].copy()
            invalidated_count = 0
            
            for session_id in session_ids:
                if session_id != except_session:
                    if self.invalidate_session(session_id, "user_logout_all"):
                        invalidated_count += 1
            
            return invalidated_count
    
    def get_session_data(self, session_id: str, key: str = None) -> Any:
        """Get session data."""
        with self.lock:
            session = self.sessions.get(session_id)
            if not session or session.status != SessionStatus.ACTIVE:
                return None
            
            if key:
                return session.data.get(key)
            return session.data.copy()
    
    def set_session_data(self, session_id: str, key: str, value: Any) -> bool:
        """Set session data."""
        with self.lock:
            session = self.sessions.get(session_id)
            if not session or session.status != SessionStatus.ACTIVE:
                return False
            
            session.data[key] = value
            return True
    
    def get_user_sessions(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all active sessions for a user."""
        with self.lock:
            if user_id not in self.user_sessions:
                return []
            
            user_session_data = []
            for session_id in self.user_sessions[user_id]:
                session = self.sessions.get(session_id)
                if session and session.status == SessionStatus.ACTIVE:
                    user_session_data.append({
                        "session_id": session_id,
                        "created_at": session.created_at.isoformat(),
                        "last_accessed": session.last_accessed.isoformat(),
                        "ip_address": session.ip_address,
                        "user_agent": session.user_agent[:100],  # Truncate for display
                        "access_count": session.access_count
                    })
            
            return user_session_data
    
    def _generate_session_id(self) -> str:
        """Generate a cryptographically secure session ID."""
        # Generate 32 bytes of random data
        random_bytes = secrets.token_bytes(32)
        
        # Add timestamp for uniqueness
        timestamp = str(time.time()).encode()
        
        # Create hash
        session_hash = hashlib.sha256(random_bytes + timestamp).hexdigest()
        
        return f"sess_{session_hash}"
    
    def _enforce_session_limits(self, user_id: str):
        """Enforce maximum sessions per user."""
        if user_id not in self.user_sessions:
            return
        
        session_ids = self.user_sessions[user_id]
        if len(session_ids) >= self.max_sessions_per_user:
            # Remove oldest session
            oldest_session_id = session_ids[0]
            self.invalidate_session(oldest_session_id, "session_limit_exceeded")
    
    def _cleanup_expired_sessions(self):
        """Clean up expired and invalidated sessions."""
        with self.lock:
            now = datetime.now(timezone.utc)
            expired_sessions = []
            
            for session_id, session in self.sessions.items():
                if (session.status != SessionStatus.ACTIVE or 
                    now > session.expires_at):
                    expired_sessions.append(session_id)
            
            # Remove expired sessions
            for session_id in expired_sessions:
                session = self.sessions.pop(session_id, None)
                if session and session.user_id in self.user_sessions:
                    try:
                        self.user_sessions[session.user_id].remove(session_id)
                        if not self.user_sessions[session.user_id]:
                            del self.user_sessions[session.user_id]
                    except (ValueError, KeyError):
                        pass
            
            if expired_sessions:
                logger.info(f"Cleaned up {len(expired_sessions)} expired sessions")
    
    def _start_cleanup_thread(self):
        """Start background thread for session cleanup."""
        def cleanup_worker():
            while True:
                try:
                    time.sleep(self.session_cleanup_interval)
                    self._cleanup_expired_sessions()
                except Exception as e:
                    logger.error(f"Session cleanup error: {e}")
        
        cleanup_thread = threading.Thread(target=cleanup_worker, daemon=True)
        cleanup_thread.start()
    
    def _log_session_event(self, event_type: str, session: SessionData, 
                          details: Dict[str, Any] = None):
        """Log session-related events."""
        try:
            event_details = {
                "session_id": session.session_id,
                "user_id": session.user_id,
                "event_type": event_type,
                "session_age": (datetime.now(timezone.utc) - session.created_at).total_seconds()
            }
            
            if details:
                event_details.update(details)
            
            severity = AuditSeverity.HIGH if event_type == "suspicious_activity" else AuditSeverity.MEDIUM
            
            self.audit_logger.log_security_event(
                event_type=AuditEventType.SUSPICIOUS_ACTIVITY if event_type == "suspicious_activity" 
                          else AuditEventType.SECURITY_VIOLATION,
                severity=severity,
                ip_address=session.ip_address,
                user_id=session.user_id,
                details=event_details,
                risk_score=70 if event_type == "suspicious_activity" else 50
            )
            
        except Exception as e:
            logger.error(f"Error logging session event: {e}")


# Global session manager instance
_session_manager: Optional[SecureSessionManager] = None


def get_session_manager() -> SecureSessionManager:
    """Get the global session manager instance."""
    global _session_manager
    if _session_manager is None:
        _session_manager = SecureSessionManager()
    return _session_manager
