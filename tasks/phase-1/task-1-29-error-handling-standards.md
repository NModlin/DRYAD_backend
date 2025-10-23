# Task 1-29: Error Handling Standards & Implementation

**Phase:** 1 - Foundation & Beta Readiness  
**Week:** 2 - Testing Infrastructure  
**Priority:** CRITICAL  
**Estimated Hours:** 6 hours

---

## 📋 OVERVIEW

Implement comprehensive error handling standards with error code system, standardized error responses, error tracking integration, and error handling middleware for consistent error management across the application.

---

## 🎯 OBJECTIVES

1. Define error code system
2. Standardize error response format
3. Implement error tracking (Sentry/similar)
4. Create error handling middleware
5. Document error handling patterns
6. Add error response tests

---

## 📊 CURRENT STATE

**Existing:**
- Basic exception handling in endpoints
- HTTPException usage
- Some custom exceptions in `app/core/exceptions.py`

**Gaps:**
- No standardized error codes
- Inconsistent error response format
- No error tracking/aggregation
- No error handling middleware
- No error analytics

---

## 🔧 IMPLEMENTATION

### 1. Error Code System

Create `app/core/error_codes.py`:

```python
"""
Standardized Error Codes for DRYAD.AI

Error code format: DRYAD-{CATEGORY}-{NUMBER}
Categories: AUTH, VAL, DB, EXT, SYS
"""
from __future__ import annotations

from enum import Enum


class ErrorCode(str, Enum):
    """Standardized error codes."""
    
    # Authentication & Authorization (1000-1999)
    AUTH_INVALID_TOKEN = "DRYAD-AUTH-1001"
    AUTH_EXPIRED_TOKEN = "DRYAD-AUTH-1002"
    AUTH_MISSING_TOKEN = "DRYAD-AUTH-1003"
    AUTH_INSUFFICIENT_PERMISSIONS = "DRYAD-AUTH-1004"
    AUTH_INVALID_CREDENTIALS = "DRYAD-AUTH-1005"
    AUTH_ACCOUNT_DISABLED = "DRYAD-AUTH-1006"
    
    # Validation Errors (2000-2999)
    VAL_INVALID_INPUT = "DRYAD-VAL-2001"
    VAL_MISSING_FIELD = "DRYAD-VAL-2002"
    VAL_INVALID_FORMAT = "DRYAD-VAL-2003"
    VAL_OUT_OF_RANGE = "DRYAD-VAL-2004"
    VAL_DUPLICATE_ENTRY = "DRYAD-VAL-2005"
    VAL_FILE_TOO_LARGE = "DRYAD-VAL-2006"
    VAL_INVALID_FILE_TYPE = "DRYAD-VAL-2007"
    
    # Database Errors (3000-3999)
    DB_CONNECTION_ERROR = "DRYAD-DB-3001"
    DB_QUERY_ERROR = "DRYAD-DB-3002"
    DB_NOT_FOUND = "DRYAD-DB-3003"
    DB_CONSTRAINT_VIOLATION = "DRYAD-DB-3004"
    DB_TRANSACTION_ERROR = "DRYAD-DB-3005"
    
    # External Service Errors (4000-4999)
    EXT_SERVICE_UNAVAILABLE = "DRYAD-EXT-4001"
    EXT_SERVICE_TIMEOUT = "DRYAD-EXT-4002"
    EXT_INVALID_RESPONSE = "DRYAD-EXT-4003"
    EXT_RATE_LIMIT_EXCEEDED = "DRYAD-EXT-4004"
    EXT_API_KEY_INVALID = "DRYAD-EXT-4005"
    
    # System Errors (5000-5999)
    SYS_INTERNAL_ERROR = "DRYAD-SYS-5001"
    SYS_NOT_IMPLEMENTED = "DRYAD-SYS-5002"
    SYS_MAINTENANCE_MODE = "DRYAD-SYS-5003"
    SYS_RESOURCE_EXHAUSTED = "DRYAD-SYS-5004"
    SYS_CONFIGURATION_ERROR = "DRYAD-SYS-5005"


class ErrorCategory(str, Enum):
    """Error categories for grouping."""
    AUTHENTICATION = "authentication"
    VALIDATION = "validation"
    DATABASE = "database"
    EXTERNAL_SERVICE = "external_service"
    SYSTEM = "system"
```

---

### 2. Standardized Error Response

Create `app/core/error_responses.py`:

```python
"""
Standardized Error Response Models
"""
from __future__ import annotations

from datetime import datetime
from typing import Any
from pydantic import BaseModel, Field
from app.core.error_codes import ErrorCode, ErrorCategory


class ErrorDetail(BaseModel):
    """Detailed error information."""
    field: str | None = Field(None, description="Field that caused the error")
    message: str = Field(..., description="Human-readable error message")
    code: str | None = Field(None, description="Specific error code")


class ErrorResponse(BaseModel):
    """Standardized error response format."""
    
    error: str = Field(..., description="Error type/title")
    message: str = Field(..., description="Human-readable error message")
    code: ErrorCode = Field(..., description="Machine-readable error code")
    category: ErrorCategory = Field(..., description="Error category")
    status_code: int = Field(..., description="HTTP status code")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    request_id: str | None = Field(None, description="Request ID for tracking")
    details: list[ErrorDetail] | None = Field(None, description="Additional error details")
    help_url: str | None = Field(None, description="URL to error documentation")
    
    class Config:
        json_schema_extra = {
            "example": {
                "error": "Validation Error",
                "message": "Invalid input data provided",
                "code": "DRYAD-VAL-2001",
                "category": "validation",
                "status_code": 400,
                "timestamp": "2025-01-20T12:00:00Z",
                "request_id": "req_abc123",
                "details": [
                    {
                        "field": "email",
                        "message": "Invalid email format",
                        "code": "DRYAD-VAL-2003"
                    }
                ],
                "help_url": "https://docs.dryad.ai/errors/DRYAD-VAL-2001"
            }
        }


def create_error_response(
    error: str,
    message: str,
    code: ErrorCode,
    category: ErrorCategory,
    status_code: int,
    request_id: str | None = None,
    details: list[ErrorDetail] | None = None
) -> ErrorResponse:
    """Create standardized error response."""
    return ErrorResponse(
        error=error,
        message=message,
        code=code,
        category=category,
        status_code=status_code,
        request_id=request_id,
        details=details,
        help_url=f"https://docs.dryad.ai/errors/{code}"
    )
```

---

### 3. Error Handling Middleware

Create `app/middleware/error_handling.py`:

```python
"""
Error Handling Middleware

Catches and standardizes all errors.
"""
from __future__ import annotations

import logging
import traceback
from typing import Callable
from fastapi import Request, Response, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from sqlalchemy.exc import SQLAlchemyError
from pydantic import ValidationError

from app.core.error_codes import ErrorCode, ErrorCategory
from app.core.error_responses import create_error_response, ErrorDetail

logger = logging.getLogger(__name__)


class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """Middleware for centralized error handling."""
    
    async def dispatch(
        self,
        request: Request,
        call_next: Callable
    ) -> Response:
        """Process request with error handling."""
        try:
            response = await call_next(request)
            return response
            
        except ValidationError as e:
            return self._handle_validation_error(e, request)
        
        except SQLAlchemyError as e:
            return self._handle_database_error(e, request)
        
        except Exception as e:
            return self._handle_unexpected_error(e, request)
    
    def _handle_validation_error(
        self,
        error: ValidationError,
        request: Request
    ) -> JSONResponse:
        """Handle Pydantic validation errors."""
        details = [
            ErrorDetail(
                field=".".join(str(x) for x in err["loc"]),
                message=err["msg"],
                code=ErrorCode.VAL_INVALID_INPUT
            )
            for err in error.errors()
        ]
        
        error_response = create_error_response(
            error="Validation Error",
            message="Invalid input data provided",
            code=ErrorCode.VAL_INVALID_INPUT,
            category=ErrorCategory.VALIDATION,
            status_code=status.HTTP_400_BAD_REQUEST,
            request_id=request.state.request_id if hasattr(request.state, "request_id") else None,
            details=details
        )
        
        logger.warning(f"Validation error: {error}")
        
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=error_response.model_dump()
        )
    
    def _handle_database_error(
        self,
        error: SQLAlchemyError,
        request: Request
    ) -> JSONResponse:
        """Handle database errors."""
        logger.error(f"Database error: {error}", exc_info=True)
        
        error_response = create_error_response(
            error="Database Error",
            message="A database error occurred",
            code=ErrorCode.DB_QUERY_ERROR,
            category=ErrorCategory.DATABASE,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            request_id=request.state.request_id if hasattr(request.state, "request_id") else None
        )
        
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=error_response.model_dump()
        )
    
    def _handle_unexpected_error(
        self,
        error: Exception,
        request: Request
    ) -> JSONResponse:
        """Handle unexpected errors."""
        logger.error(
            f"Unexpected error: {error}",
            exc_info=True,
            extra={
                "path": request.url.path,
                "method": request.method,
                "traceback": traceback.format_exc()
            }
        )
        
        error_response = create_error_response(
            error="Internal Server Error",
            message="An unexpected error occurred",
            code=ErrorCode.SYS_INTERNAL_ERROR,
            category=ErrorCategory.SYSTEM,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            request_id=request.state.request_id if hasattr(request.state, "request_id") else None
        )
        
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=error_response.model_dump()
        )
```

---

## ✅ ACCEPTANCE CRITERIA

- [ ] Error code system defined
- [ ] Error response format standardized
- [ ] Error handling middleware implemented
- [ ] Error tracking integrated
- [ ] Error documentation complete
- [ ] Error response tests passing

---

## 🧪 TESTING

```python
# tests/test_error_handling.py
"""Tests for error handling."""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_validation_error_format():
    """Test validation error returns standard format."""
    response = client.post("/api/v1/dryad/groves", json={})
    assert response.status_code == 400
    data = response.json()
    assert "error" in data
    assert "code" in data
    assert "category" in data
    assert data["category"] == "validation"


def test_error_includes_request_id():
    """Test error response includes request ID."""
    response = client.get("/api/v1/nonexistent")
    data = response.json()
    assert "request_id" in data
```

---

## 📝 NOTES

- Log all errors with context
- Include request ID in all errors
- Provide helpful error messages
- Document all error codes


