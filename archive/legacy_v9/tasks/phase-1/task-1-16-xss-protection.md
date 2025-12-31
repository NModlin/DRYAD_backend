# Task 1-16: XSS Protection

**Phase:** 1 - Foundation & Beta Readiness  
**Week:** 3  
**Estimated Hours:** 6 hours  
**Priority:** CRITICAL  
**Dependencies:** None

---

## 🎯 OBJECTIVE

Implement Cross-Site Scripting (XSS) protection across all API responses, user inputs, and rendered content.

---

## 📋 REQUIREMENTS

### Functional Requirements
- HTML escaping for all user-generated content
- Content Security Policy (CSP) headers
- Input sanitization
- Output encoding
- XSS testing suite

### Technical Requirements
- FastAPI security headers
- Pydantic input validation
- HTML sanitization library
- CSP middleware

### Performance Requirements
- Sanitization overhead: <10ms
- No impact on API response time

---

## 🔧 IMPLEMENTATION

### Step 1: Security Headers Middleware (2 hours)

**File:** `app/middleware/security_headers.py`

```python
"""
Security Headers Middleware
Adds security headers to all responses.
"""

from __future__ import annotations

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to responses."""
    
    async def dispatch(self, request: Request, call_next):
        """Add security headers."""
        response = await call_next(request)
        
        # Content Security Policy
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self' data:; "
            "connect-src 'self'; "
            "frame-ancestors 'none';"
        )
        
        # XSS Protection
        response.headers["X-XSS-Protection"] = "1; mode=block"
        
        # Content Type Options
        response.headers["X-Content-Type-Options"] = "nosniff"
        
        # Frame Options
        response.headers["X-Frame-Options"] = "DENY"
        
        return response
```

### Step 2: Input Sanitization (2 hours)

**File:** `app/core/sanitization.py`

```python
"""
Input Sanitization
HTML and script sanitization for user inputs.
"""

from __future__ import annotations

import html
import re

from structlog import get_logger

logger = get_logger(__name__)


class InputSanitizer:
    """Sanitize user inputs to prevent XSS."""
    
    # Dangerous HTML tags
    DANGEROUS_TAGS = [
        "script", "iframe", "object", "embed",
        "applet", "meta", "link", "style",
    ]
    
    # Dangerous attributes
    DANGEROUS_ATTRS = [
        "onclick", "onload", "onerror", "onmouseover",
        "onfocus", "onblur", "onchange",
    ]
    
    @classmethod
    def sanitize_html(cls, text: str) -> str:
        """
        Sanitize HTML content.
        
        Args:
            text: Input text
            
        Returns:
            Sanitized text
        """
        if not text:
            return text
        
        # HTML escape
        sanitized = html.escape(text)
        
        return sanitized
    
    @classmethod
    def sanitize_text(cls, text: str) -> str:
        """
        Sanitize plain text input.
        
        Args:
            text: Input text
            
        Returns:
            Sanitized text
        """
        if not text:
            return text
        
        # Remove script tags
        for tag in cls.DANGEROUS_TAGS:
            pattern = re.compile(f"<{tag}[^>]*>.*?</{tag}>", re.IGNORECASE | re.DOTALL)
            text = pattern.sub("", text)
        
        # Remove dangerous attributes
        for attr in cls.DANGEROUS_ATTRS:
            pattern = re.compile(f'{attr}\\s*=\\s*["\'][^"\']*["\']', re.IGNORECASE)
            text = pattern.sub("", text)
        
        return text.strip()
    
    @classmethod
    def validate_safe_input(cls, text: str) -> bool:
        """
        Check if input is safe.
        
        Args:
            text: Input to validate
            
        Returns:
            True if safe
        """
        if not text:
            return True
        
        # Check for script tags
        if re.search(r"<script", text, re.IGNORECASE):
            return False
        
        # Check for javascript: protocol
        if re.search(r"javascript:", text, re.IGNORECASE):
            return False
        
        # Check for event handlers
        for attr in cls.DANGEROUS_ATTRS:
            if attr in text.lower():
                return False
        
        return True
```

### Step 3: Pydantic Validators (1 hour)

**File:** `app/api/validators.py` (enhanced)

```python
"""
Input Validators with XSS Protection
"""

from __future__ import annotations

from pydantic import BaseModel, Field, field_validator

from app.core.sanitization import InputSanitizer


class SafeTextInput(BaseModel):
    """Safe text input with XSS protection."""
    
    content: str = Field(..., min_length=1, max_length=10000)
    
    @field_validator("content")
    @classmethod
    def validate_content(cls, v: str) -> str:
        """Validate and sanitize content."""
        if not InputSanitizer.validate_safe_input(v):
            raise ValueError("Input contains potentially dangerous content")
        
        return InputSanitizer.sanitize_text(v)
```

### Step 4: XSS Tests (1 hour)

**File:** `tests/security/test_xss_protection.py`

```python
"""
XSS Protection Tests
"""

import pytest

from app.core.sanitization import InputSanitizer
from app.api.validators import SafeTextInput


def test_sanitize_script_tag():
    """Test script tag sanitization."""
    malicious = "<script>alert('XSS')</script>"
    
    sanitized = InputSanitizer.sanitize_html(malicious)
    
    assert "<script>" not in sanitized
    assert "alert" not in sanitized or "&lt;script&gt;" in sanitized


def test_sanitize_event_handler():
    """Test event handler sanitization."""
    malicious = '<img src="x" onerror="alert(1)">'
    
    sanitized = InputSanitizer.sanitize_text(malicious)
    
    assert "onerror" not in sanitized


def test_validate_safe_input():
    """Test input validation."""
    safe = "This is safe text"
    unsafe = "<script>alert('XSS')</script>"
    
    assert InputSanitizer.validate_safe_input(safe) is True
    assert InputSanitizer.validate_safe_input(unsafe) is False


def test_pydantic_validator_blocks_xss():
    """Test Pydantic validator blocks XSS."""
    with pytest.raises(ValueError):
        SafeTextInput(content="<script>alert(1)</script>")
    
    # Safe input should work
    safe = SafeTextInput(content="Safe text")
    assert safe.content == "Safe text"


def test_security_headers_present(client):
    """Test security headers in response."""
    response = client.get("/api/v1/health")
    
    assert "Content-Security-Policy" in response.headers
    assert "X-XSS-Protection" in response.headers
    assert "X-Content-Type-Options" in response.headers
```

---

## ✅ DEFINITION OF DONE

- [ ] Security headers middleware implemented
- [ ] Input sanitization working
- [ ] Pydantic validators enhanced
- [ ] XSS tests passing
- [ ] CSP headers configured
- [ ] All inputs validated

---

## 📊 SUCCESS METRICS

- XSS vulnerabilities: 0
- Security headers: 100% coverage
- Input sanitization: <10ms overhead
- All XSS tests passing

---

**Estimated Completion:** 6 hours  
**Status:** NOT STARTED

