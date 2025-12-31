"""
Advanced Rate Limiting Middleware

This module provides FastAPI middleware for advanced rate limiting and DDoS protection.
"""

import logging
import time
from typing import Dict, Any, Optional

from fastapi import HTTPException, Request, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse, Response

from .advanced_rate_limiting import get_advanced_rate_limiter, RateLimitStrategy

logger = logging.getLogger(__name__)


class AdvancedRateLimitingMiddleware(BaseHTTPMiddleware):
    """Advanced rate limiting middleware with DDoS protection."""
    
    def __init__(self, app, enable_ddos_protection: bool = True):
        super().__init__(app)
        self.rate_limiter = get_advanced_rate_limiter()
        self.enable_ddos_protection = enable_ddos_protection
        
        # Endpoint to rule mapping
        self.endpoint_rules = {
            "/api/v1/auth": "api_auth",
            "/api/v1/users": "api_general",
            "/api/v1/api-keys": "api_general",
            "/api/v1/upload": "api_upload",
            "/api/v1/ai": "api_ai",
            "/api/v1/chat": "api_ai",
            "/api/v1/generate": "api_ai",
        }
    
    async def dispatch(self, request: Request, call_next) -> Response:
        """Process request with advanced rate limiting."""
        start_time = time.time()
        
        # Get client identifier
        client_ip = self._get_client_ip(request)
        
        # Skip rate limiting for health checks and static files
        if self._should_skip_rate_limiting(request):
            return await call_next(request)
        
        try:
            # Analyze traffic patterns for DDoS detection
            if self.enable_ddos_protection:
                self.rate_limiter.analyze_traffic_pattern(request, client_ip)
            
            # Determine rate limiting rule
            rule_name = self._get_rate_limit_rule(request)
            
            # Check rate limit
            allowed, limit_info = self.rate_limiter.check_rate_limit(client_ip, rule_name)
            
            if not allowed:
                return self._create_rate_limit_response(limit_info, client_ip)
            
            # Process request
            response = await call_next(request)
            
            # Add rate limit headers
            self._add_rate_limit_headers(response, limit_info)
            
            # Log request processing time
            processing_time = time.time() - start_time
            if processing_time > 5.0:  # Log slow requests
                logger.warning(f"Slow request from {client_ip}: {processing_time:.2f}s")
            
            return response
            
        except Exception as e:
            logger.error(f"Error in rate limiting middleware: {e}")
            # Continue processing on middleware error
            return await call_next(request)
    
    def _get_client_ip(self, request: Request) -> str:
        """Get client IP address with proxy support."""
        # Check for forwarded headers (common in load balancer setups)
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            # Take the first IP in the chain
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        # Fallback to direct connection IP
        return request.client.host if request.client else "unknown"
    
    def _should_skip_rate_limiting(self, request: Request) -> bool:
        """Check if rate limiting should be skipped for this request."""
        skip_paths = [
            "/health",
            "/metrics",
            "/docs",
            "/openapi.json",
            "/favicon.ico",
            "/static/",
        ]
        
        path = str(request.url.path)
        return any(skip_path in path for skip_path in skip_paths)
    
    def _get_rate_limit_rule(self, request: Request) -> str:
        """Determine which rate limiting rule to apply."""
        path = str(request.url.path)
        
        # Check for exact matches first
        for endpoint, rule in self.endpoint_rules.items():
            if path.startswith(endpoint):
                return rule
        
        # Default rule for API endpoints
        if path.startswith("/api/"):
            return "api_general"
        
        # Very lenient rule for non-API endpoints
        return "api_general"
    
    def _create_rate_limit_response(self, limit_info: Dict[str, Any], client_ip: str) -> JSONResponse:
        """Create rate limit exceeded response."""
        status_code = status.HTTP_429_TOO_MANY_REQUESTS
        
        # Customize response based on limit type
        if limit_info.get("status") == "blacklisted":
            status_code = status.HTTP_403_FORBIDDEN
            message = "Access denied"
        elif limit_info.get("status") == "blocked":
            status_code = status.HTTP_403_FORBIDDEN
            message = "Temporarily blocked due to suspicious activity"
        else:
            message = "Rate limit exceeded"
        
        headers = {
            "X-RateLimit-Strategy": limit_info.get("strategy", "unknown"),
            "Retry-After": str(int(limit_info.get("wait_time", 60))),
        }
        
        # Add strategy-specific headers
        if limit_info.get("strategy") == "token_bucket":
            headers["X-RateLimit-Tokens-Remaining"] = str(limit_info.get("tokens_remaining", 0))
        elif limit_info.get("strategy") == "sliding_window":
            headers["X-RateLimit-Current-Count"] = str(limit_info.get("current_count", 0))
            headers["X-RateLimit-Max-Requests"] = str(limit_info.get("max_requests", 0))
        elif limit_info.get("strategy") == "adaptive":
            headers["X-RateLimit-Threat-Score"] = str(limit_info.get("threat_score", 0))
            headers["X-RateLimit-Adjusted-Rate"] = str(limit_info.get("adjusted_rate", 0))
        
        # Log rate limit event
        logger.warning(f"Rate limit exceeded for {client_ip}: {limit_info}")
        
        return JSONResponse(
            status_code=status_code,
            content={
                "error": message,
                "details": "Request rate limit exceeded. Please slow down your requests.",
                "limit_info": {
                    "strategy": limit_info.get("strategy"),
                    "retry_after": int(limit_info.get("wait_time", 60))
                }
            },
            headers=headers
        )
    
    def _add_rate_limit_headers(self, response: Response, limit_info: Dict[str, Any]):
        """Add rate limiting information to response headers."""
        if limit_info.get("status") == "allowed":
            response.headers["X-RateLimit-Status"] = "allowed"
            response.headers["X-RateLimit-Strategy"] = limit_info.get("strategy", "unknown")
            
            if limit_info.get("strategy") == "token_bucket":
                response.headers["X-RateLimit-Tokens-Remaining"] = str(limit_info.get("tokens_remaining", 0))
            elif limit_info.get("strategy") == "sliding_window":
                response.headers["X-RateLimit-Current-Count"] = str(limit_info.get("current_count", 0))
                response.headers["X-RateLimit-Max-Requests"] = str(limit_info.get("max_requests", 0))


class DDoSProtectionMiddleware(BaseHTTPMiddleware):
    """Dedicated DDoS protection middleware."""
    
    def __init__(self, app):
        super().__init__(app)
        self.rate_limiter = get_advanced_rate_limiter()
    
    async def dispatch(self, request: Request, call_next) -> Response:
        """Process request with DDoS protection."""
        client_ip = self._get_client_ip(request)
        
        # Check for active DDoS alerts
        active_alerts = [
            alert for alert in self.rate_limiter.ddos_alerts.values()
            if not alert.resolved and client_ip in alert.source_ips
        ]
        
        if active_alerts:
            # Block requests from IPs involved in active attacks
            logger.warning(f"Blocking request from {client_ip} due to active DDoS alert")
            return JSONResponse(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                content={
                    "error": "Service temporarily unavailable",
                    "details": "Your IP is involved in a detected attack pattern"
                },
                headers={"Retry-After": "300"}  # 5 minutes
            )
        
        return await call_next(request)
    
    def _get_client_ip(self, request: Request) -> str:
        """Get client IP address with proxy support."""
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        return request.client.host if request.client else "unknown"


def create_rate_limiting_middleware(enable_ddos_protection: bool = True):
    """Create rate limiting middleware with optional DDoS protection."""
    def middleware(app):
        # Add DDoS protection first (outermost layer)
        if enable_ddos_protection:
            app.add_middleware(DDoSProtectionMiddleware)
        
        # Add advanced rate limiting
        app.add_middleware(AdvancedRateLimitingMiddleware, enable_ddos_protection=enable_ddos_protection)
        
        return app
    
    return middleware


# Utility functions for manual rate limiting checks
async def check_rate_limit_for_user(user_id: str, rule_name: str = "api_general") -> Dict[str, Any]:
    """Check rate limit for a specific user."""
    rate_limiter = get_advanced_rate_limiter()
    allowed, limit_info = rate_limiter.check_rate_limit(f"user_{user_id}", rule_name)
    return {"allowed": allowed, "limit_info": limit_info}


async def get_traffic_dashboard() -> Dict[str, Any]:
    """Get traffic statistics for monitoring dashboard."""
    rate_limiter = get_advanced_rate_limiter()
    stats = rate_limiter.get_traffic_statistics()
    
    # Add recent alerts
    recent_alerts = [
        {
            "id": alert.id,
            "type": alert.alert_type,
            "threat_level": alert.threat_level.value,
            "start_time": alert.start_time,
            "resolved": alert.resolved,
            "source_ips_count": len(alert.source_ips),
            "mitigation_actions": len(alert.mitigation_actions)
        }
        for alert in rate_limiter.ddos_alerts.values()
        if time.time() - alert.start_time < 3600  # Last hour
    ]
    
    stats["recent_alerts"] = recent_alerts
    return stats
