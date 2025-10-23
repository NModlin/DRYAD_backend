"""
Input Validation Middleware for DRYAD.AI Backend
Automatically validates and sanitizes all incoming request data.
"""

import json
import time
from typing import Dict, Any, Optional
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse

from app.core.logging_config import get_logger
from app.core.input_validation import get_input_validator, InputType, ValidationResult
from app.core.audit_logging import get_audit_logger, AuditEventType, AuditSeverity

logger = get_logger(__name__)


class InputValidationMiddleware:
    """Middleware for automatic input validation and sanitization."""
    
    def __init__(self):
        self.validator = get_input_validator()
        self.audit_logger = get_audit_logger()
        
        # Endpoints that require strict validation
        self.strict_validation_endpoints = {
            '/api/v1/admin',
            '/api/v1/users',
            '/api/v1/api-keys',
            '/api/v1/documents/upload',
            '/api/v1/agent/invoke',
            '/api/v1/multi-agent/invoke'
        }
        
        # Parameter validation rules by endpoint pattern
        self.validation_rules = {
            '/api/v1/users': {
                'email': InputType.EMAIL,
                'name': InputType.TEXT,
                'password': InputType.PASSWORD
            },
            '/api/v1/documents': {
                'filename': InputType.FILENAME,
                'content': InputType.TEXT,
                'description': InputType.TEXT
            },
            '/api/v1/agent': {
                'prompt': InputType.TEXT,
                'context': InputType.TEXT,
                'parameters': InputType.JSON
            },
            '/api/v1/chat': {
                'message': InputType.TEXT,
                'context': InputType.TEXT
            }
        }
        
        # Maximum request sizes by endpoint
        self.max_request_sizes = {
            '/api/v1/documents/upload': 50 * 1024 * 1024,  # 50MB
            '/api/v1/agent/invoke': 1 * 1024 * 1024,       # 1MB
            '/api/v1/chat': 100 * 1024,                    # 100KB
            'default': 10 * 1024 * 1024                    # 10MB
        }
    
    async def __call__(self, request: Request, call_next):
        """Process request with input validation."""
        start_time = time.time()
        
        # Get request information
        client_ip = self._get_client_ip(request)
        user_id = None
        if hasattr(request.state, 'user') and request.state.user:
            user_id = request.state.user.id
        
        path = str(request.url.path)
        method = request.method
        
        try:
            # Check if this endpoint needs validation
            needs_validation = any(
                endpoint in path for endpoint in self.strict_validation_endpoints
            )
            
            if needs_validation and method in ['POST', 'PUT', 'PATCH']:
                # Validate request size
                content_length = request.headers.get('content-length')
                if content_length:
                    size = int(content_length)
                    max_size = self._get_max_request_size(path)
                    
                    if size > max_size:
                        await self._log_validation_violation(
                            "Request size exceeded", path, user_id, client_ip,
                            {"size": size, "max_size": max_size}
                        )
                        raise HTTPException(
                            status_code=413,
                            detail=f"Request too large. Maximum size: {max_size} bytes"
                        )
                
                # Validate request body
                await self._validate_request_body(request, path, user_id, client_ip)
            
            # Validate query parameters for all requests
            await self._validate_query_parameters(request, user_id, client_ip)
            
            # Process the request
            response = await call_next(request)
            
            # Log successful validation
            duration = time.time() - start_time
            if needs_validation:
                logger.debug(f"Input validation completed for {path} in {duration:.3f}s")
            
            return response
            
        except HTTPException:
            # Re-raise HTTP exceptions (validation failures)
            raise
        except Exception as e:
            # Log unexpected errors
            logger.error(f"Input validation middleware error: {e}")
            await self._log_validation_violation(
                "Validation middleware error", path, user_id, client_ip,
                {"error": str(e)}
            )
            raise HTTPException(
                status_code=500,
                detail="Internal validation error"
            )
    
    async def _validate_request_body(self, request: Request, path: str, 
                                   user_id: Optional[str], client_ip: str):
        """Validate request body content."""
        try:
            # Read request body
            body = await request.body()
            if not body:
                return
            
            # Parse JSON body
            try:
                json_body = json.loads(body.decode('utf-8'))
            except json.JSONDecodeError as e:
                await self._log_validation_violation(
                    "Invalid JSON in request body", path, user_id, client_ip,
                    {"error": str(e)}
                )
                raise HTTPException(
                    status_code=400,
                    detail="Invalid JSON in request body"
                )
            
            # Get validation rules for this endpoint
            validation_rules = self._get_validation_rules(path)
            
            # Validate each field
            violations = []
            sanitized_data = {}
            
            for field_name, field_value in json_body.items():
                if field_name in validation_rules:
                    input_type = validation_rules[field_name]
                    result = self.validator.validate_input(
                        field_value, input_type, 
                        user_id=user_id, ip_address=client_ip
                    )
                    
                    if not result.is_valid:
                        violations.extend([f"{field_name}: {v}" for v in result.violations])
                    
                    sanitized_data[field_name] = result.sanitized_value
                else:
                    # General text validation for unknown fields
                    result = self.validator.validate_input(
                        field_value, InputType.TEXT,
                        user_id=user_id, ip_address=client_ip
                    )
                    
                    if result.risk_score >= 70:  # High risk threshold
                        violations.append(f"{field_name}: High risk content detected")
                    
                    sanitized_data[field_name] = result.sanitized_value
            
            # Handle validation violations
            if violations:
                await self._log_validation_violation(
                    "Request body validation failed", path, user_id, client_ip,
                    {"violations": violations}
                )
                raise HTTPException(
                    status_code=400,
                    detail=f"Input validation failed: {'; '.join(violations[:3])}"
                )
            
            # Store sanitized data in request state
            request.state.sanitized_body = sanitized_data
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error validating request body: {e}")
            raise HTTPException(
                status_code=500,
                detail="Request validation error"
            )
    
    async def _validate_query_parameters(self, request: Request, 
                                       user_id: Optional[str], client_ip: str):
        """Validate query parameters."""
        try:
            violations = []
            
            for param_name, param_value in request.query_params.items():
                # Validate parameter value
                result = self.validator.validate_input(
                    param_value, InputType.TEXT, max_length=500,
                    user_id=user_id, ip_address=client_ip
                )
                
                if result.risk_score >= 80:  # Very high risk threshold for query params
                    violations.append(f"{param_name}: {'; '.join(result.violations)}")
            
            if violations:
                await self._log_validation_violation(
                    "Query parameter validation failed", str(request.url.path), 
                    user_id, client_ip, {"violations": violations}
                )
                raise HTTPException(
                    status_code=400,
                    detail="Invalid query parameters detected"
                )
                
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error validating query parameters: {e}")
    
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
    
    def _get_validation_rules(self, path: str) -> Dict[str, InputType]:
        """Get validation rules for a specific path."""
        for pattern, rules in self.validation_rules.items():
            if pattern in path:
                return rules
        return {}
    
    def _get_max_request_size(self, path: str) -> int:
        """Get maximum request size for a specific path."""
        for pattern, size in self.max_request_sizes.items():
            if pattern in path:
                return size
        return self.max_request_sizes['default']
    
    async def _log_validation_violation(self, violation_type: str, path: str,
                                      user_id: Optional[str], client_ip: str,
                                      details: Dict[str, Any]):
        """Log validation violations for security monitoring."""
        try:
            audit_details = {
                "violation_type": violation_type,
                "path": path,
                "details": details
            }
            
            self.audit_logger.log_security_event(
                event_type=AuditEventType.SECURITY_VIOLATION,
                severity=AuditSeverity.HIGH,
                ip_address=client_ip,
                user_id=user_id,
                details=audit_details,
                risk_score=75
            )
            
        except Exception as e:
            logger.error(f"Error logging validation violation: {e}")


# Global input validation middleware instance
_input_validation_middleware: Optional[InputValidationMiddleware] = None


def get_input_validation_middleware() -> InputValidationMiddleware:
    """Get the global input validation middleware instance."""
    global _input_validation_middleware
    if _input_validation_middleware is None:
        _input_validation_middleware = InputValidationMiddleware()
    return _input_validation_middleware
