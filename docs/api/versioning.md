# DRYAD.AI API Versioning Guide

**Version:** 1.0  
**Last Updated:** 2025-10-13

---

## Overview

DRYAD.AI uses semantic versioning for the API to ensure backward compatibility and smooth upgrades.

**Current Version:** v1  
**Base URL:** `https://api.dryad.ai/v1`

---

## Versioning Strategy

### URL-Based Versioning

The API version is specified in the URL path:

```
https://api.dryad.ai/v1/agents
https://api.dryad.ai/v2/agents  (future)
```

### Version Format

- **Major version** (v1, v2): Breaking changes
- **Minor updates**: Backward-compatible features (no version change)
- **Patches**: Bug fixes (no version change)

---

## Version Lifecycle

| Version | Status | Support End | Notes |
|---------|--------|-------------|-------|
| v1 | Current | TBD | Active development |
| v2 | Planned | N/A | Planned for Q2 2026 |

---

## Breaking vs Non-Breaking Changes

### Breaking Changes (Require New Major Version)

- Removing endpoints
- Removing request/response fields
- Changing field types
- Changing authentication methods
- Changing error response format

### Non-Breaking Changes (Same Version)

- Adding new endpoints
- Adding optional request fields
- Adding response fields
- Adding new error codes
- Performance improvements

---

## Deprecation Policy

### Timeline

1. **Announcement:** 6 months before deprecation
2. **Warning Headers:** 3 months before deprecation
3. **Deprecation:** Version becomes deprecated
4. **Sunset:** 12 months after deprecation

### Deprecation Headers

Deprecated endpoints return warning headers:

```
Deprecation: true
Sunset: Sat, 31 Dec 2025 23:59:59 GMT
Link: <https://docs.dryad.ai/migration/v1-to-v2>; rel="deprecation"
```

### Example

```python
response = client.get("/agents")

if 'Deprecation' in response.headers:
    print(f"Warning: This endpoint is deprecated")
    print(f"Sunset date: {response.headers.get('Sunset')}")
    print(f"Migration guide: {response.headers.get('Link')}")
```

---

## Migration Guides

### v1 to v2 (Future)

When v2 is released, a comprehensive migration guide will be provided at:
https://docs.dryad.ai/migration/v1-to-v2

**Expected Changes:**
- Enhanced authentication with OAuth 2.1
- Improved error responses
- New workflow execution model
- Enhanced memory search capabilities

---

## Version Selection

### Default Version

If no version is specified, the latest stable version is used:

```bash
# Uses latest stable (currently v1)
curl https://api.dryad.ai/agents
```

### Explicit Version

Always specify version explicitly in production:

```bash
# Explicitly use v1
curl https://api.dryad.ai/v1/agents
```

### Version Header (Alternative)

You can also specify version via header:

```bash
curl -H "X-API-Version: v1" https://api.dryad.ai/agents
```

---

## Backward Compatibility

### Guaranteed Compatibility

Within a major version, we guarantee:

- Existing endpoints continue to work
- Existing fields remain in responses
- Request validation rules don't become stricter
- Authentication methods remain supported

### Best Practices

1. **Don't rely on field order** in JSON responses
2. **Ignore unknown fields** in responses
3. **Use explicit versions** in production
4. **Test against beta versions** before migration
5. **Subscribe to changelog** for updates

---

## Version-Specific Features

### v1 Features

- OAuth 2.0 authentication
- RESTful API design
- JSON request/response format
- Rate limiting
- Webhook support
- Batch operations

### v2 Features (Planned)

- OAuth 2.1 authentication
- GraphQL support
- WebSocket real-time updates
- Enhanced batch operations
- Improved error handling
- Advanced filtering and pagination

---

## API Changelog

Subscribe to changelog updates:
- **RSS Feed:** https://api.dryad.ai/changelog.rss
- **Email:** Subscribe at https://dryad.ai/api-updates
- **GitHub:** Watch https://github.com/dryad-ai/api-changelog

---

## Testing New Versions

### Beta Access

Test upcoming versions before release:

```bash
# Access beta version
curl https://api.dryad.ai/v2-beta/agents \
  -H "X-API-Key: your_api_key"
```

### Sandbox Environment

Test in sandbox before production:

```bash
# Sandbox environment
curl https://sandbox.api.dryad.ai/v1/agents \
  -H "X-API-Key: your_sandbox_key"
```

---

## Version Compatibility Checker

Check if your integration is compatible:

```python
def check_api_compatibility(client, required_version="v1"):
    """Check if API version is compatible."""
    response = client.get("/")
    api_version = response.json().get("version")
    
    if api_version != required_version:
        print(f"Warning: Using {api_version}, expected {required_version}")
        return False
    
    return True
```

---

## Support

For versioning questions:
- **Documentation:** https://docs.dryad.ai/versioning
- **Migration Help:** support@dryad.ai
- **Changelog:** https://api.dryad.ai/changelog

---

**Last Updated:** 2025-10-13

