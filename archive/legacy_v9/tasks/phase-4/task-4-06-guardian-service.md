# Task 4-06: Guardian Service (Security & Auth) Extraction

**Phase:** 4 - Forest Ecosystem Architecture  
**Week:** 19  
**Estimated Hours:** 16 hours  
**Priority:** HIGH  
**Dependencies:** Task 4-03 (Mycelium Network)

---

## 🎯 OBJECTIVE

Extract Guardian Service as the centralized security and authentication service. Handles JWT auth, NHI, audit logging, and security policy enforcement across all microservices.

---

## 📋 REQUIREMENTS

### Functional Requirements
- JWT authentication and authorization
- NHI (Non-Human Identity) for agents
- Audit logging
- Security policy enforcement
- Rate limiting
- API key management

### Technical Requirements
- FastAPI service
- PostgreSQL for audit logs
- Redis for session management
- JWT token generation/validation

### Performance Requirements
- Authentication: <100ms
- Authorization check: <50ms
- Audit log write: <200ms

---

## 🔧 IMPLEMENTATION

**File:** `services/guardian/app/main.py`

```python
"""
Guardian Service - Security & Authentication
Centralized security for DRYAD ecosystem.
"""

from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import HTTPBearer
from pydantic import BaseModel
import jwt

app = FastAPI(title="Guardian Service", version="1.0.0")
security = HTTPBearer()

SECRET_KEY = "your-secret-key"  # Load from env


class TokenRequest(BaseModel):
    """Token generation request."""
    subject: str
    identity_type: str
    permissions: list[str]


class TokenResponse(BaseModel):
    """Token response."""
    access_token: str
    token_type: str = "bearer"


@app.post("/v1/auth/token", response_model=TokenResponse)
async def create_token(request: TokenRequest) -> TokenResponse:
    """Generate JWT token."""
    payload = {
        "sub": request.subject,
        "identity_type": request.identity_type,
        "permissions": request.permissions,
    }
    
    token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")
    
    return TokenResponse(access_token=token)


@app.post("/v1/auth/verify")
async def verify_token(token: str) -> dict:
    """Verify JWT token."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return {"valid": True, "payload": payload}
    except jwt.JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")


@app.post("/v1/audit")
async def log_audit_event(event: dict) -> dict:
    """Log security audit event."""
    # Store in database
    return {"status": "logged"}


@app.get("/health")
async def health_check() -> dict[str, str]:
    """Health check."""
    return {"status": "healthy", "service": "guardian"}
```

---

## ✅ DEFINITION OF DONE

- [ ] Guardian service extracted
- [ ] JWT auth working
- [ ] Audit logging functional
- [ ] Docker image built
- [ ] Tests passing (>90% coverage)

---

## 📊 SUCCESS METRICS

- Authentication: <100ms
- Authorization: <50ms
- Test coverage: >90%

---

**Estimated Completion:** 16 hours  
**Status:** NOT STARTED

