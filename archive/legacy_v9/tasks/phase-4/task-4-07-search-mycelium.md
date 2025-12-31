# Task 4-07: Search Mycelium (Discovery Service) Implementation

**Phase:** 4 - Forest Ecosystem Architecture  
**Week:** 19  
**Estimated Hours:** 8 hours  
**Priority:** HIGH  
**Dependencies:** Task 4-03 (Mycelium Network)

---

## 🎯 OBJECTIVE

Implement Search Mycelium service for discovering agents, workflows, patterns, and knowledge across the DRYAD ecosystem. Provides unified search interface with semantic search capabilities.

---

## 📋 REQUIREMENTS

### Functional Requirements
- Agent discovery by capability
- Workflow search by status/type
- Pattern search in Memory Grove
- Knowledge base search
- Semantic search support

### Technical Requirements
- FastAPI service
- Elasticsearch or Meilisearch
- Vector database integration
- Mycelium Network integration

### Performance Requirements
- Search query: <1 second
- Agent discovery: <100ms
- Indexing latency: <5 seconds

---

## 🔧 IMPLEMENTATION

**File:** `services/search-mycelium/app/main.py`

```python
"""
Search Mycelium - Discovery Service
Unified search across DRYAD ecosystem.
"""

from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="Search Mycelium", version="1.0.0")


class SearchRequest(BaseModel):
    """Search request."""
    query: str
    filters: dict[str, any] = {}
    limit: int = 10


class SearchResult(BaseModel):
    """Search result."""
    id: str
    type: str  # agent, workflow, pattern, knowledge
    title: str
    description: str
    score: float


@app.post("/v1/search", response_model=list[SearchResult])
async def search(request: SearchRequest) -> list[SearchResult]:
    """Perform search across ecosystem."""
    # Implementation would query search engine
    return []


@app.get("/v1/agents/discover")
async def discover_agents(capability: str) -> list[dict]:
    """Discover agents by capability."""
    # Query Agent Studio via Mycelium
    return []


@app.get("/health")
async def health_check() -> dict[str, str]:
    """Health check."""
    return {"status": "healthy", "service": "search-mycelium"}
```

---

## ✅ DEFINITION OF DONE

- [ ] Search service implemented
- [ ] Agent discovery working
- [ ] Semantic search functional
- [ ] Docker image built
- [ ] Tests passing (>80% coverage)

---

## 📊 SUCCESS METRICS

- Search query: <1s
- Agent discovery: <100ms
- Test coverage: >80%

---

**Estimated Completion:** 8 hours  
**Status:** NOT STARTED

