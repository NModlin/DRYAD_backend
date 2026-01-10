# Task 5-01: Memory Coordinator Implementation

**Phase:** 5 - Cognitive Architecture & Self-Improvement  
**Week:** 21  
**Estimated Hours:** 12 hours  
**Priority:** HIGH  
**Dependencies:** Phase 4 complete

---

## 🎯 OBJECTIVE

Implement Memory Coordinator - the entry point for the Memory Keeper Guild. Routes memory operations to appropriate specialists (Archivist for short-term, Librarian for long-term, Ingestion Scribe for new knowledge).

---

## 📋 REQUIREMENTS

### Functional Requirements
- Route memory operations to appropriate specialists
- Coordinate between short-term and long-term memory
- Manage memory lifecycle (creation, retrieval, archival, deletion)
- Provide unified memory interface
- Handle memory prioritization

### Technical Requirements
- FastAPI service or agent implementation
- Integration with Archivist (Redis)
- Integration with Librarian (Vector DB)
- Integration with Ingestion Scribe
- Mycelium Network communication

### Performance Requirements
- Routing decision: <10ms
- Memory retrieval: <500ms
- Memory storage: <1 second

---

## 🔧 IMPLEMENTATION

**File:** `app/agents/memory_coordinator.py`

```python
"""
Memory Coordinator - Memory Keeper Guild Entry Point
Routes memory operations to appropriate specialists.
"""

from __future__ import annotations

from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import BaseModel
from structlog import get_logger

logger = get_logger(__name__)


class MemoryType(str, Enum):
    """Type of memory."""
    
    SHORT_TERM = "SHORT_TERM"  # Recent, temporary (Redis)
    LONG_TERM = "LONG_TERM"  # Persistent, searchable (Vector DB)
    WORKING = "WORKING"  # Active context


class MemoryRequest(BaseModel):
    """Memory operation request."""
    
    operation: str  # store, retrieve, search, archive
    memory_type: MemoryType
    key: str | None = None
    value: dict[str, Any] | None = None
    query: str | None = None


class MemoryCoordinator:
    """
    Memory Coordinator Agent
    
    Routes memory operations to appropriate Memory Keeper specialists.
    """
    
    def __init__(self) -> None:
        self.logger = logger.bind(agent="memory_coordinator")
    
    async def handle_memory_request(
        self,
        request: MemoryRequest,
    ) -> dict[str, Any]:
        """
        Handle memory operation request.
        
        Args:
            request: Memory operation request
            
        Returns:
            Operation result
        """
        self.logger.info(
            "handling_memory_request",
            operation=request.operation,
            memory_type=request.memory_type.value,
        )
        
        match request.operation:
            case "store":
                return await self._store_memory(request)
            case "retrieve":
                return await self._retrieve_memory(request)
            case "search":
                return await self._search_memory(request)
            case "archive":
                return await self._archive_memory(request)
            case _:
                raise ValueError(f"Unknown operation: {request.operation}")
    
    async def _store_memory(self, request: MemoryRequest) -> dict[str, Any]:
        """Store memory via appropriate specialist."""
        
        match request.memory_type:
            case MemoryType.SHORT_TERM:
                # Route to Archivist (Redis)
                return await self._call_archivist("store", request)
            
            case MemoryType.LONG_TERM:
                # Route to Librarian (Vector DB)
                return await self._call_librarian("store", request)
            
            case MemoryType.WORKING:
                # Store in both for active context
                await self._call_archivist("store", request)
                return await self._call_librarian("store", request)
    
    async def _retrieve_memory(self, request: MemoryRequest) -> dict[str, Any]:
        """Retrieve memory via appropriate specialist."""
        
        # Try short-term first (faster)
        result = await self._call_archivist("retrieve", request)
        
        if result.get("found"):
            return result
        
        # Fall back to long-term
        return await self._call_librarian("retrieve", request)
    
    async def _search_memory(self, request: MemoryRequest) -> dict[str, Any]:
        """Search memory via Librarian."""
        return await self._call_librarian("search", request)
    
    async def _archive_memory(self, request: MemoryRequest) -> dict[str, Any]:
        """Archive short-term memory to long-term."""
        
        # Retrieve from short-term
        data = await self._call_archivist("retrieve", request)
        
        if not data.get("found"):
            return {"success": False, "error": "Memory not found"}
        
        # Store in long-term
        await self._call_librarian("store", MemoryRequest(
            operation="store",
            memory_type=MemoryType.LONG_TERM,
            key=request.key,
            value=data["value"],
        ))
        
        # Delete from short-term
        await self._call_archivist("delete", request)
        
        return {"success": True, "archived": True}
    
    async def _call_archivist(
        self,
        operation: str,
        request: MemoryRequest,
    ) -> dict[str, Any]:
        """Call Archivist specialist."""
        # Implementation would use Mycelium Network
        return {"success": True}
    
    async def _call_librarian(
        self,
        operation: str,
        request: MemoryRequest,
    ) -> dict[str, Any]:
        """Call Librarian specialist."""
        # Implementation would use Mycelium Network
        return {"success": True}
```

---

## ✅ DEFINITION OF DONE

- [ ] Memory Coordinator implemented
- [ ] Routing logic functional
- [ ] Integration with specialists working
- [ ] All tests passing (>85% coverage)
- [ ] Documentation complete

---

## 📊 SUCCESS METRICS

- Routing decision: <10ms
- Memory retrieval: <500ms
- Test coverage: >85%

---

**Estimated Completion:** 12 hours  
**Status:** NOT STARTED

