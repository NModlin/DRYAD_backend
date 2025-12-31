# Task 1-28: API Versioning & Deprecation Strategy

**Phase:** 1 - Foundation & Beta Readiness  
**Week:** 4 - Phase 1 Validation & Documentation  
**Priority:** CRITICAL  
**Estimated Hours:** 4 hours

---

## 📋 OVERVIEW

Implement comprehensive API versioning strategy with deprecation policies, backward compatibility testing, and version migration guides to prevent breaking changes from affecting clients.

---

## 🎯 OBJECTIVES

1. Document API versioning policy
2. Create deprecation procedures
3. Implement version negotiation
4. Add backward compatibility tests
5. Create API changelog
6. Implement version headers

---

## 📊 CURRENT STATE

**Existing:**
- API endpoints use `/api/v1/` prefix
- No formal versioning strategy
- No deprecation policy
- No version migration guides

**Gaps:**
- No version negotiation mechanism
- No backward compatibility testing
- No deprecation warnings
- No API changelog

---

## 🔧 IMPLEMENTATION

### 1. API Versioning Policy

Create `docs/api/VERSIONING_POLICY.md`:

```markdown
# API Versioning Policy

## Version Format

- **URL-based versioning:** `/api/v{major}/endpoint`
- **Current version:** v1
- **Version format:** Semantic versioning (MAJOR.MINOR.PATCH)

## Version Lifecycle

### Active (v1)
- Full support
- Bug fixes
- Security updates
- New features

### Deprecated (v0)
- Security updates only
- 6-month deprecation period
- Deprecation warnings in responses
- Migration guide provided

### Sunset (removed)
- No longer available
- Returns 410 Gone status

## Breaking Changes

Breaking changes require new major version:
- Removing endpoints
- Removing request/response fields
- Changing field types
- Changing authentication
- Changing error codes

## Non-Breaking Changes

Can be added to current version:
- Adding new endpoints
- Adding optional request fields
- Adding response fields
- Adding new error codes
- Performance improvements

## Deprecation Process

1. **Announce (T-6 months)**
   - Add deprecation warning to responses
   - Update documentation
   - Notify API consumers

2. **Migrate (T-3 months)**
   - Provide migration guide
   - Offer migration support
   - Monitor usage metrics

3. **Sunset (T-0)**
   - Remove deprecated version
   - Return 410 Gone
   - Redirect to new version docs
```

---

### 2. Version Middleware

Create `app/middleware/versioning.py`:

```python
"""
API Versioning Middleware

Handles API version negotiation and deprecation warnings.
"""
from __future__ import annotations

import logging
from datetime import datetime
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

logger = logging.getLogger(__name__)


class APIVersion:
    """API version information."""
    
    def __init__(
        self,
        version: str,
        status: str,
        sunset_date: datetime | None = None,
        migration_guide: str | None = None
    ):
        self.version = version
        self.status = status  # active, deprecated, sunset
        self.sunset_date = sunset_date
        self.migration_guide = migration_guide


class VersioningMiddleware(BaseHTTPMiddleware):
    """Middleware for API versioning and deprecation."""
    
    # Define supported versions
    VERSIONS = {
        "v1": APIVersion(
            version="1.0.0",
            status="active",
            sunset_date=None,
            migration_guide=None
        ),
        # Example deprecated version
        # "v0": APIVersion(
        #     version="0.9.0",
        #     status="deprecated",
        #     sunset_date=datetime(2025, 7, 1),
        #     migration_guide="/docs/migration/v0-to-v1"
        # ),
    }
    
    async def dispatch(
        self,
        request: Request,
        call_next: Callable
    ) -> Response:
        """Process request with version handling."""
        
        # Extract version from URL
        version = self._extract_version(request.url.path)
        
        if version:
            # Validate version
            if version not in self.VERSIONS:
                return JSONResponse(
                    status_code=404,
                    content={
                        "error": "API version not found",
                        "version": version,
                        "supported_versions": list(self.VERSIONS.keys()),
                        "latest_version": "v1"
                    }
                )
            
            # Check if version is sunset
            version_info = self.VERSIONS[version]
            if version_info.status == "sunset":
                return JSONResponse(
                    status_code=410,
                    content={
                        "error": "API version no longer available",
                        "version": version,
                        "status": "sunset",
                        "migration_guide": version_info.migration_guide,
                        "latest_version": "v1"
                    }
                )
        
        # Process request
        response = await call_next(request)
        
        # Add version headers
        if version:
            version_info = self.VERSIONS[version]
            response.headers["X-API-Version"] = version_info.version
            response.headers["X-API-Status"] = version_info.status
            
            # Add deprecation warning
            if version_info.status == "deprecated":
                response.headers["Deprecation"] = "true"
                if version_info.sunset_date:
                    response.headers["Sunset"] = version_info.sunset_date.isoformat()
                if version_info.migration_guide:
                    response.headers["Link"] = f'<{version_info.migration_guide}>; rel="deprecation"'
                
                logger.warning(
                    f"Deprecated API version used: {version} "
                    f"(sunset: {version_info.sunset_date})"
                )
        
        return response
    
    def _extract_version(self, path: str) -> str | None:
        """Extract API version from URL path."""
        parts = path.split("/")
        if len(parts) >= 3 and parts[1] == "api":
            return parts[2]  # e.g., "v1"
        return None
```

---

### 3. API Changelog

Create `docs/api/CHANGELOG.md`:

```markdown
# API Changelog

## v1.0.0 (2025-01-20) - Current

### Added
- Initial API release
- All DRYAD endpoints (Groves, Branches, Vessels, Oracle)
- Authentication endpoints
- Document management endpoints
- Health check endpoints

### Security
- JWT authentication
- Rate limiting
- Input validation
- CORS configuration

## Future Versions

### v1.1.0 (Planned)
- Enhanced search capabilities
- Batch operations
- WebSocket improvements

### v2.0.0 (Future)
- GraphQL API
- Improved error responses
- Enhanced filtering
```

---

### 4. Backward Compatibility Tests

Create `tests/test_api_versioning.py`:

```python
"""
Tests for API versioning and backward compatibility.
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestAPIVersioning:
    """Test API versioning functionality."""
    
    def test_current_version_accessible(self):
        """Test current API version is accessible."""
        response = client.get("/api/v1/health/status")
        assert response.status_code == 200
        assert "X-API-Version" in response.headers
        assert response.headers["X-API-Status"] == "active"
    
    def test_invalid_version_returns_404(self):
        """Test invalid API version returns 404."""
        response = client.get("/api/v99/health/status")
        assert response.status_code == 404
        data = response.json()
        assert "supported_versions" in data
        assert "latest_version" in data
    
    def test_deprecated_version_warning(self):
        """Test deprecated version returns warning headers."""
        # This test will be relevant when we have deprecated versions
        pass
    
    def test_sunset_version_returns_410(self):
        """Test sunset version returns 410 Gone."""
        # This test will be relevant when we sunset versions
        pass


class TestBackwardCompatibility:
    """Test backward compatibility of API changes."""
    
    def test_new_optional_field_backward_compatible(self):
        """Test adding optional field doesn't break existing clients."""
        # Old request format (without new field)
        response = client.post(
            "/api/v1/dryad/groves",
            json={"name": "Test Grove", "description": "Test"}
        )
        assert response.status_code in [200, 201]
    
    def test_response_includes_all_documented_fields(self):
        """Test response includes all documented fields."""
        response = client.get("/api/v1/health/status")
        assert response.status_code == 200
        data = response.json()
        
        # Verify documented fields are present
        assert "status" in data
        assert "timestamp" in data
```

---

## ✅ ACCEPTANCE CRITERIA

- [ ] Versioning policy documented
- [ ] Version middleware implemented
- [ ] Deprecation warnings working
- [ ] API changelog created
- [ ] Backward compatibility tests passing
- [ ] Migration guides template created

---

## 📚 DOCUMENTATION

Update API documentation with versioning information and deprecation policies.

---

## 📝 NOTES

- Always maintain backward compatibility within major versions
- Provide 6-month deprecation period
- Document all breaking changes
- Monitor deprecated endpoint usage


