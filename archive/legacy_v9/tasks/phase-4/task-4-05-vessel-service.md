# Task 4-05: Vessel Service (Context Management) Extraction

**Phase:** 4 - Forest Ecosystem Architecture  
**Week:** 19  
**Estimated Hours:** 16 hours  
**Priority:** HIGH  
**Dependencies:** Task 4-03 (Mycelium Network)

---

## 🎯 OBJECTIVE

Extract Vessel Service for managing execution context, code context, file operations, and workspace management. Provides centralized context storage and retrieval for all agents.

---

## 📋 REQUIREMENTS

### Functional Requirements
- Code context extraction and storage
- File content retrieval
- Workspace management
- Context versioning
- Context search and filtering

### Technical Requirements
- FastAPI service
- PostgreSQL for metadata
- S3/MinIO for file storage
- Vector database for code embeddings

### Performance Requirements
- Context retrieval: <500ms
- File upload: <2 seconds
- Search query: <1 second

---

## 🔧 IMPLEMENTATION

**File:** `services/vessel/app/main.py`

```python
"""
Vessel Service - Context Management
Manages execution context and workspace.
"""

from fastapi import FastAPI, UploadFile
from pydantic import BaseModel
from uuid import UUID, uuid4

app = FastAPI(title="Vessel Service", version="1.0.0")


class ContextRequest(BaseModel):
    """Request to store context."""
    workflow_id: UUID
    files: list[str]
    metadata: dict[str, any] = {}


class ContextResponse(BaseModel):
    """Context response."""
    context_id: UUID
    workflow_id: UUID
    file_count: int


@app.post("/v1/context", response_model=ContextResponse)
async def store_context(request: ContextRequest) -> ContextResponse:
    """Store execution context."""
    context_id = uuid4()
    
    return ContextResponse(
        context_id=context_id,
        workflow_id=request.workflow_id,
        file_count=len(request.files),
    )


@app.get("/v1/context/{context_id}")
async def get_context(context_id: UUID) -> dict:
    """Retrieve context."""
    return {"context_id": str(context_id), "files": []}


@app.get("/health")
async def health_check() -> dict[str, str]:
    """Health check."""
    return {"status": "healthy", "service": "vessel"}
```

---

## ✅ DEFINITION OF DONE

- [ ] Vessel service extracted
- [ ] Context storage working
- [ ] File operations functional
- [ ] Docker image built
- [ ] Tests passing (>80% coverage)

---

## 📊 SUCCESS METRICS

- Context retrieval: <500ms
- File upload: <2s
- Test coverage: >80%

---

**Estimated Completion:** 16 hours  
**Status:** NOT STARTED

