# Task 4-04: Grove Keeper (Core DRYAD Service) Extraction

**Phase:** 4 - Forest Ecosystem Architecture  
**Week:** 18  
**Estimated Hours:** 16 hours  
**Priority:** CRITICAL  
**Dependencies:** Task 4-03 (Mycelium Network)

---

## 🎯 OBJECTIVE

Extract Grove Keeper as the core DRYAD orchestration service. This service coordinates the GAD workflow, manages agent swarms, handles task distribution, and serves as the primary entry point for all DRYAD operations.

---

## 📋 REQUIREMENTS

### Functional Requirements
- GAD workflow orchestration
- Agent swarm coordination
- Task queue management
- Workflow state management
- Event broadcasting
- API gateway for external clients

### Technical Requirements
- FastAPI with async/await
- PostgreSQL for workflow state
- Redis for task queues
- Mycelium Network integration
- WebSocket for real-time updates

### Performance Requirements
- Workflow initiation: <1 second
- Task distribution: <500ms
- State query: <100ms
- Uptime: >99.9%

---

## 🔧 IMPLEMENTATION

**File:** `services/grove-keeper/app/main.py`

```python
"""
Grove Keeper - Core DRYAD Orchestration Service
Coordinates GAD workflows and agent swarms.
"""

from fastapi import FastAPI
from pydantic import BaseModel
from uuid import UUID, uuid4

app = FastAPI(title="Grove Keeper", version="1.0.0")


class WorkflowRequest(BaseModel):
    """Request to start workflow."""
    request: str
    context_files: list[str] = []


class WorkflowStatus(BaseModel):
    """Workflow status response."""
    workflow_id: UUID
    status: str
    current_phase: str


@app.post("/v1/workflows", response_model=WorkflowStatus)
async def create_workflow(request: WorkflowRequest) -> WorkflowStatus:
    """Create and start new GAD workflow."""
    workflow_id = uuid4()
    
    # Initiate GAD workflow via Mycelium
    
    return WorkflowStatus(
        workflow_id=workflow_id,
        status="RUNNING",
        current_phase="PLAN",
    )


@app.get("/v1/workflows/{workflow_id}", response_model=WorkflowStatus)
async def get_workflow_status(workflow_id: UUID) -> WorkflowStatus:
    """Get workflow status."""
    return WorkflowStatus(
        workflow_id=workflow_id,
        status="RUNNING",
        current_phase="EXECUTE",
    )


@app.get("/health")
async def health_check() -> dict[str, str]:
    """Health check."""
    return {"status": "healthy", "service": "grove-keeper"}
```

---

## ✅ DEFINITION OF DONE

- [ ] Grove Keeper service extracted
- [ ] GAD workflow coordination working
- [ ] Mycelium integration complete
- [ ] Docker image built
- [ ] Kubernetes manifests created
- [ ] Tests passing (>85% coverage)

---

## 📊 SUCCESS METRICS

- Workflow initiation: <1s
- Task distribution: <500ms
- Uptime: >99.9%
- Test coverage: >85%

---

**Estimated Completion:** 16 hours  
**Status:** NOT STARTED

