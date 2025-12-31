"""
Advanced Security Hardening for DRYAD.AI Backend
Implements comprehensive security measures, vulnerability protection, and security monitoring.
"""

import hashlib
import hmac
import os
import secrets
import time
import re
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Set
from functools import wraps
from collections import defaultdict, deque
from ipaddress import ip_address, ip_network
import jwt

from fastapi import Request, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from passlib.context import CryptContext
from passlib.hash import bcrypt

from app.core.logging_config import get_logger, metrics_logger
from app.core.error_handling import error_handler, ErrorCategory, ErrorSeverity

logger = get_logger(__name__)


class SecurityConfig:
    """Security configuration settings."""
    
    def __init__(self):
        # Password security
        self.min_password_length = 8
        self.require_uppercase = True
        self.require_lowercase = True
        self.require_numbers = True
        self.require_special_chars = True
        self.password_history_count = 5
        
        # Rate limiting
        self.rate_limit_requests = 100
        self.rate_limit_window = 3600  # 1 hour
        self.burst_limit = 20
        self.burst_window = 60  # 1 minute
        
        # Session security
        self.session_timeout = 3600  # 1 hour
        self.max_concurrent_sessions = 5
        self.session_rotation_interval = 1800  # 30 minutes
        
        # API security
        self.api_key_length = 32
        self.api_key_prefix = "gai_"
        self.max_api_keys_per_user = 10
        
        # Content security
        self.max_file_size = 100 * 1024 * 1024  # 100MB
        self.allowed_file_types = {
            'application/pdf', 'text/plain', 'text/csv',
            'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'image/jpeg', 'image/png', 'image/gif',
            'audio/mpeg', 'audio/wav', 'video/mp4'
        }
        
        # IP security
        self.blocked_ips: Set[str] = set()
        self.allowed_networks: List[str] = []  # Empty means all allowed
        self.max_failed_attempts = 5
        self.lockout_duration = 900  # 15 minutes


security_config = SecurityConfig()


class PasswordValidator:
    """Advanced password validation and security."""
    
    def __init__(self):
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        self.common_passwords = self._load_common_passwords()
    
    def _load_common_passwords(self) -> Set[str]:
        """Load common passwords list."""
        # In production, load from a file
        return {
            "password", "123456", "password123", "admin", "qwerty",
            "letmein", "welcome", "monkey", "dragon", "master"
        }
    
    def validate_password(self, password: str, user_info: Optional[Dict] = None) -> Dict[str, Any]:
        """Comprehensive password validation."""
        errors = []
        score = 0
        
        # Length check
        if len(password) < security_config.min_password_length:
            errors.append(f"Password must be at least {security_config.min_password_length} characters long")
        else:
            score += min(len(password) - security_config.min_password_length, 10)
        
        # Character requirements
        if security_config.require_uppercase and not re.search(r'[A-Z]', password):
            errors.append("Password must contain at least one uppercase letter")
        else:
            score += 5
        
        if security_config.require_lowercase and not re.search(r'[a-z]', password):
            errors.append("Password must contain at least one lowercase letter")
        else:
            score += 5
        
        if security_config.require_numbers and not re.search(r'\d', password):
            errors.append("Password must contain at least one number")
        else:
            score += 5
        
        if security_config.require_special_chars and not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            errors.append("Password must contain at least one special character")
        else:
            score += 5
        
        # Common password check
        if password.lower() in self.common_passwords:
            errors.append("Password is too common")
        else:
            score += 10
        
        # Personal information check
        if user_info:
            personal_info = [
                user_info.get('email', '').split('@')[0].lower(),
                user_info.get('full_name', '').lower(),
                user_info.get('username', '').lower()
            ]
            
            for info in personal_info:
                if info and info in password.lower():
                    errors.append("Password should not contain personal information")
                    break
            else:
                score += 10
        
        # Pattern checks
        if re.search(r'(.)\1{2,}', password):  # Repeated characters
            errors.append("Password should not contain repeated characters")
        else:
            score += 5
        
        if re.search(r'(012|123|234|345|456|567|678|789|890|abc|bcd|cde)', password.lower()):
            errors.append("Password should not contain sequential characters")
        else:
            score += 5
        
        # Strength assessment
        if score >= 40:
            strength = "very_strong"
        elif score >= 30:
            strength = "strong"
        elif score >= 20:
            strength = "medium"
        elif score >= 10:
            strength = "weak"
        else:
            strength = "very_weak"
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "strength": strength,
            "score": score
        }
    
    def hash_password(self, password: str) -> str:
        """Hash password securely."""
        return self.pwd_context.hash(password)
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify password against hash."""
        return self.pwd_context.verify(plain_password, hashed_password)


class RateLimiter:
    """Advanced rate limiting with multiple strategies."""
    
    def __init__(self):
        self.requests = defaultdict(deque)
        self.blocked_ips = defaultdict(float)  # IP -> unblock_time
        self.user_requests = defaultdict(deque)
        self.api_key_requests = defaultdict(deque)
    
    def is_rate_limited(self, identifier: str, limit: int, window: int) -> bool:
        """Check if identifier is rate limited."""
        now = time.time()
        
        # Clean old requests
        request_times = self.requests[identifier]
        while request_times and request_times[0] < now - window:
            request_times.popleft()
        
        # Check limit
        if len(request_times) >= limit:
            return True
        
        # Add current request
        request_times.append(now)
        return False
    
    def check_ip_rate_limit(self, ip: str) -> bool:
        """Check IP-based rate limiting."""
        # Check if IP is temporarily blocked
        if ip in self.blocked_ips:
            if time.time() < self.blocked_ips[ip]:
                return True
            else:
                del self.blocked_ips[ip]
        
        # Check burst limit
        if self.is_rate_limited(f"ip_burst_{ip}", security_config.burst_limit, security_config.burst_window):
            logger.warning(f"IP {ip} exceeded burst limit")
            return True
        
        # Check hourly limit
        if self.is_rate_limited(f"ip_hour_{ip}", security_config.rate_limit_requests, security_config.rate_limit_window):
            logger.warning(f"IP {ip} exceeded hourly limit")
            return True
        
        return False
    
    def check_user_rate_limit(self, user_id: str) -> bool:
        """Check user-based rate limiting."""
        return self.is_rate_limited(f"user_{user_id}", security_config.rate_limit_requests * 2, security_config.rate_limit_window)
    
    def block_ip(self, ip: str, duration: int = None):
        """Block IP for specified duration."""
        duration = duration or security_config.lockout_duration
        self.blocked_ips[ip] = time.time() + duration
        logger.warning(f"Blocked IP {ip} for {duration} seconds")
    
    def get_rate_limit_info(self, identifier: str) -> Dict[str, Any]:
        """Get rate limit information for identifier."""
        now = time.time()
        request_times = self.requests[identifier]
        
        # Clean old requests
        while request_times and request_times[0] < now - security_config.rate_limit_window:
            request_times.popleft()
        
        remaining = max(0, security_config.rate_limit_requests - len(request_times))
        reset_time = request_times[0] + security_config.rate_limit_window if request_times else now
        
        return {
            "limit": security_config.rate_limit_requests,
            "remaining": remaining,
            "reset": int(reset_time),
            "retry_after": max(0, int(reset_time - now)) if remaining == 0 else 0
        }


class SecurityMonitor:
    """Security event monitoring and threat detection."""
    
    def __init__(self):
        self.failed_attempts = defaultdict(list)
        self.suspicious_activities = deque(maxlen=1000)
        self.security_events = deque(maxlen=1000)
    
    def record_failed_login(self, ip: str, user_identifier: str):
        """Record failed login attempt."""
        now = time.time()
        self.failed_attempts[ip].append({
            "timestamp": now,
            "user_identifier": user_identifier,
            "type": "failed_login"
        })
        
        # Clean old attempts
        self.failed_attempts[ip] = [
            attempt for attempt in self.failed_attempts[ip]
            if attempt["timestamp"] > now - 3600  # Keep last hour
        ]
        
        # Check for brute force
        if len(self.failed_attempts[ip]) >= security_config.max_failed_attempts:
            self.record_security_event("brute_force_detected", {
                "ip": ip,
                "attempts": len(self.failed_attempts[ip]),
                "user_identifier": user_identifier
            })
            return True
        
        return False
    
    def record_security_event(self, event_type: str, details: Dict[str, Any]):
        """Record security event."""
        event = {
            "timestamp": time.time(),
            "type": event_type,
            "details": details
        }
        
        self.security_events.append(event)
        
        # Log security event
        logger.warning(f"Security event: {event_type}", extra={
            "security_event": event,
            "event_type": event_type
        })
        
        # Record metric
        metrics_logger.increment_counter("security_events", tags={"type": event_type})
    
    def detect_suspicious_activity(self, request: Request, user_id: Optional[str] = None):
        """Detect suspicious activity patterns."""
        suspicious_indicators = []
        
        # Check for suspicious user agents
        user_agent = request.headers.get("user-agent", "").lower()
        suspicious_agents = ["bot", "crawler", "scanner", "hack", "exploit"]
        if any(agent in user_agent for agent in suspicious_agents):
            suspicious_indicators.append("suspicious_user_agent")
        
        # Check for suspicious headers
        suspicious_headers = ["x-forwarded-for", "x-real-ip", "x-originating-ip"]
        for header in suspicious_headers:
            if header in request.headers:
                suspicious_indicators.append(f"suspicious_header_{header}")
        
        # Check for unusual request patterns
        if len(request.query_params) > 20:
            suspicious_indicators.append("excessive_query_params")
        
        # Check for SQL injection patterns
        query_string = str(request.url.query).lower()
        sql_patterns = ["union", "select", "drop", "insert", "update", "delete", "'", "\"", ";"]
        if any(pattern in query_string for pattern in sql_patterns):
            suspicious_indicators.append("potential_sql_injection")
        
        # Check for XSS patterns
        xss_patterns = ["<script", "javascript:", "onerror=", "onload="]
        if any(pattern in query_string for pattern in xss_patterns):
            suspicious_indicators.append("potential_xss")
        
        if suspicious_indicators:
            self.record_security_event("suspicious_activity", {
                "ip": request.client.host if request.client else "unknown",
                "user_id": user_id,
                "indicators": suspicious_indicators,
                "user_agent": user_agent,
                "path": request.url.path
            })
        
        return suspicious_indicators
    
    def get_security_summary(self) -> Dict[str, Any]:
        """Get security monitoring summary."""
        now = time.time()
        last_hour = now - 3600
        last_day = now - 86400
        
        # Count events by time period
        events_last_hour = sum(1 for event in self.security_events if event["timestamp"] > last_hour)
        events_last_day = sum(1 for event in self.security_events if event["timestamp"] > last_day)
        
        # Count by event type
        event_types = defaultdict(int)
        for event in self.security_events:
            if event["timestamp"] > last_day:
                event_types[event["type"]] += 1
        
        # Failed login statistics
        total_failed_attempts = sum(len(attempts) for attempts in self.failed_attempts.values())
        
        return {
            "events_last_hour": events_last_hour,
            "events_last_day": events_last_day,
            "event_types": dict(event_types),
            "total_failed_attempts": total_failed_attempts,
            "blocked_ips": len(rate_limiter.blocked_ips),
            "timestamp": now
        }


class InputSanitizer:
    """Input sanitization and validation."""
    
    @staticmethod
    def sanitize_string(input_str: str, max_length: int = 1000) -> str:
        """Sanitize string input."""
        if not isinstance(input_str, str):
            return ""
        
        # Remove null bytes
        sanitized = input_str.replace('\x00', '')
        
        # Limit length
        sanitized = sanitized[:max_length]
        
        # Remove control characters except newlines and tabs
        sanitized = ''.join(char for char in sanitized if ord(char) >= 32 or char in '\n\t')
        
        return sanitized.strip()
    
    @staticmethod
    def validate_email(email: str) -> bool:
        """Validate email format."""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email)) and len(email) <= 254
    
    @staticmethod
    def validate_filename(filename: str) -> bool:
        """Validate filename for security."""
        # Check for path traversal
        if '..' in filename or '/' in filename or '\\' in filename:
            return False
        
        # Check for null bytes
        if '\x00' in filename:
            return False
        
        # Check length
        if len(filename) > 255:
            return False
        
        # Check for reserved names (Windows)
        reserved_names = {'CON', 'PRN', 'AUX', 'NUL', 'COM1', 'COM2', 'COM3', 'COM4', 'COM5', 'COM6', 'COM7', 'COM8', 'COM9', 'LPT1', 'LPT2', 'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9'}
        if filename.upper().split('.')[0] in reserved_names:
            return False
        
        return True
    
    @staticmethod
    def validate_content_type(content_type: str) -> bool:
        """Validate content type."""
        return content_type in security_config.allowed_file_types


# Global instances
password_validator = PasswordValidator()
rate_limiter = RateLimiter()
security_monitor = SecurityMonitor()
input_sanitizer = InputSanitizer()


def security_headers_middleware(request: Request, call_next):
    """Add comprehensive security headers to responses."""
    async def middleware(request: Request, call_next):
        response = await call_next(request)

        # Core security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # HSTS (HTTP Strict Transport Security)
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains; preload"

        # Permissions Policy (formerly Feature Policy)
        permissions_policy = (
            "geolocation=(), "
            "microphone=(), "
            "camera=(), "
            "payment=(), "
            "usb=(), "
            "magnetometer=(), "
            "gyroscope=(), "
            "speaker=(), "
            "vibrate=(), "
            "fullscreen=(self), "
            "sync-xhr=()"
        )
        response.headers["Permissions-Policy"] = permissions_policy

        # Content Security Policy (Enhanced)
        csp_directives = [
            "default-src 'self'",
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'",  # Allow inline for API docs
            "style-src 'self' 'unsafe-inline'",
            "img-src 'self' data: https:",
            "font-src 'self' data:",
            "connect-src 'self'",
            "media-src 'self'",
            "object-src 'none'",
            "child-src 'none'",
            "frame-src 'none'",
            "frame-ancestors 'none'",
            "form-action 'self'",
            "base-uri 'self'",
            "manifest-src 'self'",
            "worker-src 'self'"
        ]
        response.headers["Content-Security-Policy"] = "; ".join(csp_directives)

        # Additional security headers
        response.headers["X-Permitted-Cross-Domain-Policies"] = "none"
        response.headers["Cross-Origin-Embedder-Policy"] = "require-corp"
        response.headers["Cross-Origin-Opener-Policy"] = "same-origin"
        response.headers["Cross-Origin-Resource-Policy"] = "same-origin"

        # Cache control for sensitive endpoints
        if any(sensitive in str(request.url.path) for sensitive in ['/api/v1/admin', '/api/v1/users', '/api/v1/api-keys']):
            response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, private"
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"

        # Server information hiding
        response.headers.pop("Server", None)
        response.headers["Server"] = "DRYAD.AI"

        return response

    return middleware


def rate_limit_middleware(request: Request):
    """Rate limiting middleware."""
    # Skip rate limiting if disabled (for testing)
    if os.getenv("DISABLE_RATE_LIMITING", "false").lower() == "true":
        return

    client_ip = request.client.host if request.client else "unknown"

    # Check IP rate limit
    if rate_limiter.check_ip_rate_limit(client_ip):
        rate_info = rate_limiter.get_rate_limit_info(f"ip_hour_{client_ip}")
        
        # Record security event
        security_monitor.record_security_event("rate_limit_exceeded", {
            "ip": client_ip,
            "path": request.url.path,
            "method": request.method
        })
        
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded",
            headers={
                "X-RateLimit-Limit": str(rate_info["limit"]),
                "X-RateLimit-Remaining": str(rate_info["remaining"]),
                "X-RateLimit-Reset": str(rate_info["reset"]),
                "Retry-After": str(rate_info["retry_after"])
            }
        )


def security_monitoring_middleware(request: Request, user_id: Optional[str] = None):
    """Security monitoring middleware."""
    client_ip = request.client.host if request.client else "unknown"
    
    # Check for suspicious activity
    suspicious_indicators = security_monitor.detect_suspicious_activity(request, user_id)
    
    # Block if too many suspicious indicators
    if len(suspicious_indicators) >= 3:
        rate_limiter.block_ip(client_ip, 3600)  # Block for 1 hour
        security_monitor.record_security_event("ip_blocked_suspicious", {
            "ip": client_ip,
            "indicators": suspicious_indicators
        })
        
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied due to suspicious activity"
        )


def get_security_status() -> Dict[str, Any]:
    """Get comprehensive security status."""
    return {
        "security_monitor": security_monitor.get_security_summary(),
        "rate_limiter": {
            "blocked_ips": len(rate_limiter.blocked_ips),
            "active_limits": len(rate_limiter.requests)
        },
        "password_policy": {
            "min_length": security_config.min_password_length,
            "require_uppercase": security_config.require_uppercase,
            "require_lowercase": security_config.require_lowercase,
            "require_numbers": security_config.require_numbers,
            "require_special_chars": security_config.require_special_chars
        },
        "file_security": {
            "max_file_size": security_config.max_file_size,
            "allowed_types": list(security_config.allowed_file_types)
        },
        "timestamp": time.time()
    }
