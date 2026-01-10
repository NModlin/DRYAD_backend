"""
Security Headers Middleware
Adds security headers to all HTTP responses for defense-in-depth.
"""

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from typing import Callable
import logging

logger = logging.getLogger(__name__)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Middleware to add security headers to all responses.
    
    Headers added:
    - Content-Security-Policy: Prevents XSS and other injection attacks
    - X-Content-Type-Options: Prevents MIME-sniffing
    - X-Frame-Options: Prevents clickjacking
    - X-XSS-Protection: Enables browser XSS protection
    - Strict-Transport-Security: Forces HTTPS (when enabled)
    - Referrer-Policy: Controls referrer information
    - Permissions-Policy: Controls browser features
    """
    
    def __init__(self, app, enable_hsts: bool = False):
        """
        Initialize security headers middleware.
        
        Args:
            app: FastAPI application
            enable_hsts: Whether to enable HSTS (only for production with HTTPS)
        """
        super().__init__(app)
        self.enable_hsts = enable_hsts
        
        # Content Security Policy
        # Adjust these directives based on your application's needs
        self.csp_directives = {
            "default-src": "'self'",
            "script-src": "'self' 'unsafe-inline'",  # 'unsafe-inline' needed for some frameworks
            "style-src": "'self' 'unsafe-inline'",   # 'unsafe-inline' needed for inline styles
            "img-src": "'self' data: https:",
            "font-src": "'self' data:",
            "connect-src": "'self'",
            "frame-ancestors": "'none'",
            "base-uri": "'self'",
            "form-action": "'self'",
        }
        
        # Build CSP header value
        self.csp_header = "; ".join([f"{key} {value}" for key, value in self.csp_directives.items()])
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process request and add security headers to response.
        
        Args:
            request: Incoming HTTP request
            call_next: Next middleware/handler in chain
            
        Returns:
            Response with security headers added
        """
        try:
            # Process request
            response = await call_next(request)
            
            # Add security headers
            self._add_security_headers(response)
            
            return response
            
        except Exception as e:
            logger.error(f"Error in security headers middleware: {e}")
            # Re-raise to let error handlers deal with it
            raise
    
    def _add_security_headers(self, response: Response) -> None:
        """
        Add security headers to response.
        
        Args:
            response: HTTP response to add headers to
        """
        # Content-Security-Policy
        # Prevents XSS, clickjacking, and other code injection attacks
        response.headers["Content-Security-Policy"] = self.csp_header
        
        # X-Content-Type-Options
        # Prevents MIME-sniffing attacks
        response.headers["X-Content-Type-Options"] = "nosniff"
        
        # X-Frame-Options
        # Prevents clickjacking attacks
        response.headers["X-Frame-Options"] = "DENY"
        
        # X-XSS-Protection
        # Enables browser's XSS filter (legacy, but still useful)
        response.headers["X-XSS-Protection"] = "1; mode=block"
        
        # Referrer-Policy
        # Controls how much referrer information is sent
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        # Permissions-Policy (formerly Feature-Policy)
        # Controls which browser features can be used
        permissions = [
            "geolocation=()",
            "microphone=()",
            "camera=()",
            "payment=()",
            "usb=()",
            "magnetometer=()",
            "gyroscope=()",
            "accelerometer=()",
        ]
        response.headers["Permissions-Policy"] = ", ".join(permissions)
        
        # Strict-Transport-Security (HSTS)
        # Forces HTTPS connections (only enable in production with HTTPS)
        if self.enable_hsts:
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains; preload"
        
        # Cache-Control for sensitive endpoints
        # Prevent caching of sensitive data
        if self._is_sensitive_endpoint(response):
            response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, private"
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"
    
    def _is_sensitive_endpoint(self, response: Response) -> bool:
        """
        Check if response is from a sensitive endpoint.
        
        Args:
            response: HTTP response
            
        Returns:
            True if endpoint is sensitive, False otherwise
        """
        # Add logic to identify sensitive endpoints
        # For now, assume all endpoints are sensitive
        return True


def add_security_headers_middleware(app, enable_hsts: bool = False):
    """
    Add security headers middleware to FastAPI application.
    
    Args:
        app: FastAPI application
        enable_hsts: Whether to enable HSTS (only for production with HTTPS)
    """
    app.add_middleware(SecurityHeadersMiddleware, enable_hsts=enable_hsts)
    logger.info("Security headers middleware enabled")

