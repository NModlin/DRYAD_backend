"""
Audit Middleware for DRYAD.AI Backend
Automatically logs security events, API requests, and compliance-related activities.
"""

import time
import json
from typing import Optional, Dict, Any
from fastapi import Request, Response
from fastapi.responses import JSONResponse

from app.core.logging_config import get_logger
from app.core.audit_logging import (
    get_audit_logger, AuditEventType, AuditSeverity, AuditEvent
)

logger = get_logger(__name__)


class AuditMiddleware:
    """Middleware for automatic audit logging."""
    
    def __init__(self):
        self.audit_logger = get_audit_logger()
        
        # Endpoints that require special audit logging
        self.high_risk_endpoints = {
            '/api/v1/users',
            '/api/v1/admin',
            '/api/v1/api-keys',
            '/api/v1/documents/upload',
            '/api/v1/agent/invoke',
            '/api/v1/multi-agent/invoke'
        }
        
        # Sensitive parameters to redact in logs
        self.sensitive_params = {
            'password', 'token', 'api_key', 'secret', 'private_key',
            'authorization', 'x-api-key', 'bearer'
        }
    
    async def __call__(self, request: Request, call_next):
        """Process request and log audit events."""
        start_time = time.time()
        
        # Extract request information
        client_ip = self._get_client_ip(request)
        user_agent = request.headers.get("user-agent", "")
        method = request.method
        path = str(request.url.path)
        
        # Get user information if available
        user_id = None
        if hasattr(request.state, 'user') and request.state.user:
            user_id = request.state.user.id
        
        # Log API request for high-risk endpoints
        if any(endpoint in path for endpoint in self.high_risk_endpoints):
            await self._log_api_request(request, user_id, client_ip, user_agent)
        
        # Process the request
        response = None
        error_occurred = False
        
        try:
            response = await call_next(request)
            
            # Log successful access to protected resources
            if response.status_code < 400 and user_id:
                await self._log_successful_access(
                    request, response, user_id, client_ip
                )
            
        except Exception as e:
            error_occurred = True
            logger.error(f"Request processing error: {e}")
            
            # Log the error
            await self._log_request_error(
                request, str(e), user_id, client_ip, user_agent
            )
            
            # Re-raise the exception
            raise
        
        finally:
            # Calculate request duration
            duration = time.time() - start_time
            
            # Log access denied events
            if response and response.status_code in [401, 403]:
                await self._log_access_denied(
                    request, response, user_id, client_ip, user_agent
                )
            
            # Log slow requests (potential DoS attempts)
            if duration > 10.0:  # 10 seconds threshold
                await self._log_slow_request(
                    request, duration, user_id, client_ip, user_agent
                )
        
        return response
    
    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP address from request."""
        # Check for forwarded headers first
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip
        
        # Fall back to direct client IP
        if request.client:
            return request.client.host
        
        return "unknown"
    
    async def _log_api_request(self, request: Request, user_id: Optional[str],
                              client_ip: str, user_agent: str):
        """Log API request for high-risk endpoints."""
        try:
            # Prepare request details (sanitized)
            details = {
                "method": request.method,
                "path": str(request.url.path),
                "query_params": self._sanitize_params(dict(request.query_params)),
                "headers": self._sanitize_headers(dict(request.headers)),
                "content_type": request.headers.get("content-type", ""),
                "content_length": request.headers.get("content-length", "0")
            }
            
            self.audit_logger.log_event(AuditEvent(
                event_id=self._generate_event_id(),
                event_type=AuditEventType.API_REQUEST,
                severity=AuditSeverity.MEDIUM,
                timestamp=self._get_current_timestamp(),
                user_id=user_id,
                ip_address=client_ip,
                user_agent=user_agent,
                resource=str(request.url.path),
                action=request.method,
                outcome="initiated",
                details=details,
                compliance_tags=["api_access", "monitoring"]
            ))
            
        except Exception as e:
            logger.error(f"Error logging API request: {e}")
    
    async def _log_successful_access(self, request: Request, response: Response,
                                   user_id: str, client_ip: str):
        """Log successful access to protected resources."""
        try:
            details = {
                "method": request.method,
                "path": str(request.url.path),
                "status_code": response.status_code,
                "response_size": len(response.body) if hasattr(response, 'body') else 0
            }
            
            # Determine event type based on method
            event_type = AuditEventType.DATA_READ
            if request.method in ["POST", "PUT", "PATCH"]:
                event_type = AuditEventType.DATA_WRITE
            elif request.method == "DELETE":
                event_type = AuditEventType.DATA_DELETE
            
            self.audit_logger.log_data_access_event(
                event_type=event_type,
                user_id=user_id,
                resource=str(request.url.path),
                action=request.method,
                ip_address=client_ip,
                outcome="success",
                details=details
            )
            
        except Exception as e:
            logger.error(f"Error logging successful access: {e}")
    
    async def _log_access_denied(self, request: Request, response: Response,
                               user_id: Optional[str], client_ip: str, user_agent: str):
        """Log access denied events."""
        try:
            details = {
                "method": request.method,
                "path": str(request.url.path),
                "status_code": response.status_code,
                "reason": "authentication_failed" if response.status_code == 401 else "authorization_failed"
            }
            
            severity = AuditSeverity.HIGH if response.status_code == 403 else AuditSeverity.MEDIUM
            
            self.audit_logger.log_event(AuditEvent(
                event_id=self._generate_event_id(),
                event_type=AuditEventType.ACCESS_DENIED,
                severity=severity,
                timestamp=self._get_current_timestamp(),
                user_id=user_id,
                ip_address=client_ip,
                user_agent=user_agent,
                resource=str(request.url.path),
                action=request.method,
                outcome="denied",
                details=details,
                risk_score=70 if response.status_code == 403 else 50,
                compliance_tags=["access_control", "security"]
            ))
            
        except Exception as e:
            logger.error(f"Error logging access denied: {e}")
    
    async def _log_request_error(self, request: Request, error: str,
                               user_id: Optional[str], client_ip: str, user_agent: str):
        """Log request processing errors."""
        try:
            details = {
                "method": request.method,
                "path": str(request.url.path),
                "error": error[:500],  # Limit error message length
                "error_type": "request_processing_error"
            }
            
            self.audit_logger.log_security_event(
                event_type=AuditEventType.SECURITY_VIOLATION,
                severity=AuditSeverity.HIGH,
                ip_address=client_ip,
                user_id=user_id,
                details=details,
                risk_score=60
            )
            
        except Exception as e:
            logger.error(f"Error logging request error: {e}")
    
    async def _log_slow_request(self, request: Request, duration: float,
                              user_id: Optional[str], client_ip: str, user_agent: str):
        """Log slow requests that might indicate DoS attempts."""
        try:
            details = {
                "method": request.method,
                "path": str(request.url.path),
                "duration_seconds": round(duration, 2),
                "threshold_exceeded": "slow_request_detected"
            }
            
            self.audit_logger.log_security_event(
                event_type=AuditEventType.SUSPICIOUS_ACTIVITY,
                severity=AuditSeverity.MEDIUM,
                ip_address=client_ip,
                user_id=user_id,
                details=details,
                risk_score=40
            )
            
        except Exception as e:
            logger.error(f"Error logging slow request: {e}")
    
    def _sanitize_params(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitize query parameters by removing sensitive data."""
        sanitized = {}
        for key, value in params.items():
            if key.lower() in self.sensitive_params:
                sanitized[key] = "[REDACTED]"
            else:
                sanitized[key] = str(value)[:100]  # Limit length
        return sanitized
    
    def _sanitize_headers(self, headers: Dict[str, str]) -> Dict[str, str]:
        """Sanitize headers by removing sensitive data."""
        sanitized = {}
        for key, value in headers.items():
            key_lower = key.lower()
            if any(sensitive in key_lower for sensitive in self.sensitive_params):
                sanitized[key] = "[REDACTED]"
            else:
                # Keep only important headers for audit
                if key_lower in ['content-type', 'content-length', 'user-agent', 'accept']:
                    sanitized[key] = value[:200]  # Limit length
        return sanitized
    
    def _generate_event_id(self) -> str:
        """Generate a unique event ID."""
        import uuid
        return str(uuid.uuid4())
    
    def _get_current_timestamp(self):
        """Get current timestamp."""
        from datetime import datetime, timezone
        return datetime.now(timezone.utc)


# Global audit middleware instance
_audit_middleware: Optional[AuditMiddleware] = None


def get_audit_middleware() -> AuditMiddleware:
    """Get the global audit middleware instance."""
    global _audit_middleware
    if _audit_middleware is None:
        _audit_middleware = AuditMiddleware()
    return _audit_middleware
