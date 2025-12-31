# app/core/jwt_security.py
"""
Enhanced JWT Security System for DRYAD.AI.
Implements token blacklisting, refresh token rotation, and comprehensive security measures.
"""

import time
import hashlib
import secrets
import logging
from typing import Dict, Set, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from threading import Lock
import jwt

from app.core.config import config

logger = logging.getLogger(__name__)


@dataclass
class TokenSecurityInfo:
    """Security information for a JWT token."""
    token_id: str
    user_id: str
    issued_at: float
    expires_at: float
    token_type: str  # 'access' or 'refresh'
    client_ip: str
    user_agent: str
    is_revoked: bool = False
    revoked_at: Optional[float] = None
    revoked_reason: Optional[str] = None


class JWTSecurityManager:
    """
    Enhanced JWT security manager with blacklisting and rotation.
    
    Features:
    - Token blacklisting for immediate revocation
    - Refresh token rotation for enhanced security
    - Concurrent session management
    - Suspicious activity detection
    - Comprehensive audit logging
    """
    
    def __init__(self):
        self._blacklisted_tokens: Set[str] = set()
        self._active_tokens: Dict[str, TokenSecurityInfo] = {}
        self._user_sessions: Dict[str, Set[str]] = {}  # user_id -> set of token_ids
        self._lock = Lock()
        
        # Security configuration
        self.max_concurrent_sessions = int(getattr(config, "MAX_CONCURRENT_SESSIONS", 5))
        self.token_rotation_threshold = 0.5  # Rotate when 50% of lifetime remaining
        self.suspicious_activity_threshold = 10  # Max failed attempts per hour
        
        # Cleanup old tokens periodically
        self._last_cleanup = time.time()
        self._cleanup_interval = 3600  # 1 hour
    
    def generate_token_id(self) -> str:
        """Generate a unique token ID."""
        return secrets.token_urlsafe(16)
    
    def create_secure_token(self, user_id: str, token_type: str, 
                          client_ip: str, user_agent: str,
                          custom_claims: Optional[Dict] = None) -> Tuple[str, str]:
        """
        Create a secure JWT token with enhanced security features.
        
        Returns:
            Tuple of (token_string, token_id)
        """
        now = time.time()
        token_id = self.generate_token_id()
        
        # Determine expiration based on token type
        if token_type == "access":
            expires_in = config.JWT_EXPIRATION_HOURS * 3600  # 1 hour default
        elif token_type == "refresh":
            expires_in = config.REFRESH_TOKEN_EXPIRATION_DAYS * 24 * 3600  # 7 days default
        else:
            raise ValueError(f"Invalid token type: {token_type}")
        
        expires_at = now + expires_in
        
        # Create JWT payload with security claims
        payload = {
            "jti": token_id,  # JWT ID for blacklisting
            "sub": user_id,   # Subject (user ID)
            "iat": int(now),  # Issued at
            "exp": int(expires_at),  # Expires at
            "iss": "DRYAD.AI",  # Issuer
            "aud": "DRYAD.AI-api",  # Audience
            "token_type": token_type,
            "client_ip": client_ip,
            "user_agent_hash": hashlib.sha256(user_agent.encode()).hexdigest()[:16],
            "security_version": "2.0"  # For future token format changes
        }
        
        # Add custom claims if provided
        if custom_claims:
            payload.update(custom_claims)
        
        # Sign the token
        token_string = jwt.encode(payload, config.JWT_SECRET_KEY, algorithm=config.JWT_ALGORITHM)
        
        # Store token security info
        token_info = TokenSecurityInfo(
            token_id=token_id,
            user_id=user_id,
            issued_at=now,
            expires_at=expires_at,
            token_type=token_type,
            client_ip=client_ip,
            user_agent=user_agent
        )
        
        with self._lock:
            self._active_tokens[token_id] = token_info
            
            # Track user sessions
            if user_id not in self._user_sessions:
                self._user_sessions[user_id] = set()
            self._user_sessions[user_id].add(token_id)
            
            # Enforce concurrent session limits
            self._enforce_session_limits(user_id)
        
        logger.info(f"Created {token_type} token for user {user_id} from {client_ip}")
        return token_string, token_id
    
    def validate_token_security(self, token_string: str, client_ip: str, 
                               user_agent: str) -> Optional[Dict]:
        """
        Validate token with enhanced security checks.
        
        Returns:
            Token payload if valid, None if invalid
        """
        try:
            # Decode token
            payload = jwt.decode(
                token_string,
                config.JWT_SECRET_KEY,
                algorithms=[config.JWT_ALGORITHM],
                audience="DRYAD.AI-api",
                issuer="DRYAD.AI"
            )
            
            token_id = payload.get("jti")
            if not token_id:
                logger.warning("Token missing JWT ID (jti)")
                return None
            
            # Check if token is blacklisted
            if self.is_token_blacklisted(token_id):
                logger.warning(f"Attempted use of blacklisted token: {token_id}")
                return None
            
            # Validate security claims
            if not self._validate_security_claims(payload, client_ip, user_agent):
                return None
            
            # Check if token needs rotation (for refresh tokens)
            if payload.get("token_type") == "refresh":
                self._check_token_rotation(token_id, payload)
            
            return payload
            
        except jwt.ExpiredSignatureError:
            logger.debug("Token expired")
            return None
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid token: {e}")
            return None
        except Exception as e:
            logger.error(f"Token validation error: {e}")
            return None
    
    def blacklist_token(self, token_id: str, reason: str = "manual_revocation") -> bool:
        """
        Blacklist a token immediately.
        
        Args:
            token_id: The JWT ID (jti) of the token to blacklist
            reason: Reason for blacklisting
            
        Returns:
            True if successfully blacklisted
        """
        with self._lock:
            self._blacklisted_tokens.add(token_id)
            
            # Update token info if it exists
            if token_id in self._active_tokens:
                token_info = self._active_tokens[token_id]
                token_info.is_revoked = True
                token_info.revoked_at = time.time()
                token_info.revoked_reason = reason
                
                # Remove from user sessions
                user_id = token_info.user_id
                if user_id in self._user_sessions:
                    self._user_sessions[user_id].discard(token_id)
        
        logger.info(f"Token {token_id} blacklisted: {reason}")
        return True
    
    def is_token_blacklisted(self, token_id: str) -> bool:
        """Check if a token is blacklisted."""
        return token_id in self._blacklisted_tokens
    
    def revoke_all_user_tokens(self, user_id: str, reason: str = "security_incident") -> int:
        """
        Revoke all tokens for a specific user.
        
        Returns:
            Number of tokens revoked
        """
        revoked_count = 0
        
        with self._lock:
            user_tokens = self._user_sessions.get(user_id, set()).copy()
            
            for token_id in user_tokens:
                if self.blacklist_token(token_id, reason):
                    revoked_count += 1
        
        logger.warning(f"Revoked {revoked_count} tokens for user {user_id}: {reason}")
        return revoked_count
    
    def _validate_security_claims(self, payload: Dict, client_ip: str, user_agent: str) -> bool:
        """Validate security-specific claims in the token."""
        # Check client IP (optional - can be disabled for mobile users)
        token_ip = payload.get("client_ip")
        if token_ip and token_ip != client_ip:
            logger.warning(f"Token IP mismatch: {token_ip} vs {client_ip}")
            # Don't fail - IP can change legitimately
        
        # Check user agent hash
        token_ua_hash = payload.get("user_agent_hash")
        if token_ua_hash:
            current_ua_hash = hashlib.sha256(user_agent.encode()).hexdigest()[:16]
            if token_ua_hash != current_ua_hash:
                logger.warning("Token user agent mismatch - possible token theft")
                return False
        
        return True
    
    def _enforce_session_limits(self, user_id: str):
        """Enforce maximum concurrent sessions per user."""
        user_tokens = self._user_sessions.get(user_id, set())
        
        if len(user_tokens) > self.max_concurrent_sessions:
            # Remove oldest tokens
            tokens_to_remove = len(user_tokens) - self.max_concurrent_sessions
            
            # Sort by issued time (oldest first)
            token_infos = [(tid, self._active_tokens.get(tid)) for tid in user_tokens]
            token_infos = [(tid, info) for tid, info in token_infos if info]
            token_infos.sort(key=lambda x: x[1].issued_at)
            
            for i in range(tokens_to_remove):
                token_id = token_infos[i][0]
                self.blacklist_token(token_id, "session_limit_exceeded")
    
    def _check_token_rotation(self, token_id: str, payload: Dict):
        """Check if refresh token should be rotated."""
        issued_at = payload.get("iat", 0)
        expires_at = payload.get("exp", 0)
        now = time.time()
        
        # Calculate remaining lifetime percentage
        total_lifetime = expires_at - issued_at
        remaining_lifetime = expires_at - now
        remaining_percentage = remaining_lifetime / total_lifetime if total_lifetime > 0 else 0
        
        if remaining_percentage < self.token_rotation_threshold:
            logger.info(f"Refresh token {token_id} should be rotated (remaining: {remaining_percentage:.2%})")
    
    def cleanup_expired_tokens(self):
        """Clean up expired and old blacklisted tokens."""
        now = time.time()
        
        # Only cleanup periodically
        if now - self._last_cleanup < self._cleanup_interval:
            return
        
        with self._lock:
            # Remove expired tokens from active tokens
            expired_tokens = []
            for token_id, token_info in self._active_tokens.items():
                if token_info.expires_at < now:
                    expired_tokens.append(token_id)
            
            for token_id in expired_tokens:
                token_info = self._active_tokens.pop(token_id, None)
                if token_info:
                    user_id = token_info.user_id
                    if user_id in self._user_sessions:
                        self._user_sessions[user_id].discard(token_id)
            
            # Remove old blacklisted tokens (keep for 24 hours after expiration)
            old_blacklisted = []
            for token_id in self._blacklisted_tokens:
                token_info = self._active_tokens.get(token_id)
                if token_info and token_info.expires_at < (now - 86400):  # 24 hours
                    old_blacklisted.append(token_id)
            
            for token_id in old_blacklisted:
                self._blacklisted_tokens.discard(token_id)
        
        self._last_cleanup = now
        logger.info(f"Cleaned up {len(expired_tokens)} expired tokens and {len(old_blacklisted)} old blacklisted tokens")
    
    def get_security_stats(self) -> Dict:
        """Get security statistics."""
        with self._lock:
            return {
                "active_tokens": len(self._active_tokens),
                "blacklisted_tokens": len(self._blacklisted_tokens),
                "active_users": len(self._user_sessions),
                "total_sessions": sum(len(sessions) for sessions in self._user_sessions.values())
            }


# Global JWT security manager instance
jwt_security_manager = JWTSecurityManager()
