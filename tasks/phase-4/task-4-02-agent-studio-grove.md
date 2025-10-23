# Task 4-02: Agent Studio Grove Service Extraction

**Phase:** 4 - Forest Ecosystem Architecture  
**Week:** 17  
**Estimated Hours:** 20 hours  
**Priority:** CRITICAL  
**Dependencies:** Task 4-01 (Oracle Service)

---

## 🎯 OBJECTIVE

Extract Agent Studio Grove into a standalone microservice responsible for agent lifecycle management, capability registry, agent deployment, and agent monitoring. This becomes the central agent management platform.

---

## 📋 REQUIREMENTS

### Functional Requirements
- Agent registration and discovery
- Agent capability management
- Agent deployment and scaling
- Agent health monitoring
- Agent performance metrics
- Agent versioning and rollback
- Agent configuration management

### Technical Requirements
- FastAPI service with async/await
- PostgreSQL for agent metadata
- Redis for agent state
- gRPC for inter-service communication
- Docker containerization
- Kubernetes CRDs for agent deployment

### Performance Requirements
- Agent discovery: <100ms
- Agent deployment: <30 seconds
- Health check response: <50ms
- Uptime: >99.9%

---

## 🔧 IMPLEMENTATION STEPS

### Step 1: Create Agent Studio Service (16 hours)

**File:** `services/agent-studio/app/main.py`

```python
"""
Agent Studio Grove - Agent Lifecycle Management Service
Manages agent registration, deployment, and monitoring.
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncIterator
from uuid import UUID

from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field
from structlog import get_logger

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Application lifespan manager."""
    logger.info("agent_studio_starting")
    yield
    logger.info("agent_studio_shutting_down")


app = FastAPI(
    title="Agent Studio Grove",
    description="Agent Lifecycle Management for DRYAD.AI",
    version="1.0.0",
    lifespan=lifespan,
)


class AgentCapability(BaseModel):
    """Agent capability definition."""
    
    name: str
    description: str
    parameters: dict[str, any] = Field(default_factory=dict)


class AgentRegistration(BaseModel):
    """Agent registration request."""
    
    agent_name: str = Field(..., min_length=1, max_length=100)
    agent_type: str  # orchestrator, specialist, execution
    capabilities: list[AgentCapability]
    model_tier: str = Field(default="balanced")
    max_concurrent_tasks: int = Field(default=5, ge=1, le=20)
    config: dict[str, any] = Field(default_factory=dict)


class AgentInfo(BaseModel):
    """Agent information."""
    
    agent_id: UUID
    agent_name: str
    agent_type: str
    capabilities: list[AgentCapability]
    status: str  # ACTIVE, INACTIVE, DEPLOYING, ERROR
    current_load: int
    max_concurrent_tasks: int
    uptime_seconds: float


@app.post("/v1/agents/register", response_model=AgentInfo)
async def register_agent(registration: AgentRegistration) -> AgentInfo:
    """
    Register new agent.
    
    Args:
        registration: Agent registration details
        
    Returns:
        Registered agent information
    """
    logger.info("registering_agent", agent_name=registration.agent_name)
    
    # Implementation would persist to database
    from uuid import uuid4
    
    agent_info = AgentInfo(
        agent_id=uuid4(),
        agent_name=registration.agent_name,
        agent_type=registration.agent_type,
        capabilities=registration.capabilities,
        status="ACTIVE",
        current_load=0,
        max_concurrent_tasks=registration.max_concurrent_tasks,
        uptime_seconds=0.0,
    )
    
    return agent_info


@app.get("/v1/agents", response_model=list[AgentInfo])
async def list_agents(
    agent_type: str | None = None,
    capability: str | None = None,
) -> list[AgentInfo]:
    """
    List all registered agents.
    
    Args:
        agent_type: Filter by agent type
        capability: Filter by capability
        
    Returns:
        List of agents
    """
    logger.info("listing_agents", agent_type=agent_type, capability=capability)
    
    # Implementation would query database
    return []


@app.get("/v1/agents/{agent_id}", response_model=AgentInfo)
async def get_agent(agent_id: UUID) -> AgentInfo:
    """
    Get agent details.
    
    Args:
        agent_id: Agent identifier
        
    Returns:
        Agent information
        
    Raises:
        HTTPException: If agent not found
    """
    logger.info("getting_agent", agent_id=str(agent_id))
    
    # Implementation would query database
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Agent not found",
    )


@app.delete("/v1/agents/{agent_id}")
async def deregister_agent(agent_id: UUID) -> dict[str, str]:
    """
    Deregister agent.
    
    Args:
        agent_id: Agent identifier
        
    Returns:
        Success message
    """
    logger.info("deregistering_agent", agent_id=str(agent_id))
    
    # Implementation would remove from database
    return {"status": "deregistered", "agent_id": str(agent_id)}


@app.get("/health")
async def health_check() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "healthy", "service": "agent-studio"}
```

### Step 2: Create Kubernetes Manifests (4 hours)

**File:** `services/agent-studio/k8s/deployment.yaml`

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: agent-studio
  labels:
    app: agent-studio
spec:
  replicas: 2
  selector:
    matchLabels:
      app: agent-studio
  template:
    metadata:
      labels:
        app: agent-studio
    spec:
      containers:
      - name: agent-studio
        image: dryad/agent-studio:latest
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: dryad-secrets
              key: database-url
        - name: REDIS_URL
          value: "redis://redis:6379"
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
---
apiVersion: v1
kind: Service
metadata:
  name: agent-studio
spec:
  selector:
    app: agent-studio
  ports:
  - port: 80
    targetPort: 8000
  type: ClusterIP
```

---

## ✅ DEFINITION OF DONE

- [ ] Agent Studio service extracted
- [ ] Agent registration working
- [ ] Agent discovery functional
- [ ] Health monitoring operational
- [ ] Docker image built
- [ ] Kubernetes manifests created
- [ ] All tests passing (>85% coverage)
- [ ] Documentation complete

---

## 📊 SUCCESS METRICS

- Agent discovery: <100ms
- Agent deployment: <30s
- Health check: <50ms
- Uptime: >99.9%
- Test coverage: >85%

---

**Estimated Completion:** 20 hours  
**Assigned To:** Backend Developer + DevOps Engineer  
**Status:** NOT STARTED

