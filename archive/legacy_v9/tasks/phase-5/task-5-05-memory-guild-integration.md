# Task 5-05: Memory Guild Integration & Tool Implementation

**Phase:** 5 - Cognitive Architecture & Self-Improvement  
**Week:** 22  
**Estimated Hours:** 16 hours  
**Priority:** HIGH  
**Dependencies:** Tasks 5-01 through 5-04 (All Memory Guild agents)

---

## 🎯 OBJECTIVE

Integrate Memory Keeper Guild into all agents as memory tools. Provide standardized memory access interface for all agents to store/retrieve context, learnings, and knowledge.

---

## 📋 REQUIREMENTS

### Functional Requirements
- Memory tools for all agents
- Standardized memory API
- Automatic context persistence
- Knowledge retrieval during planning
- Memory-augmented agent responses

### Technical Requirements
- Tool interface implementation
- Integration with all Tier 2/3 agents
- Mycelium Network communication
- Async memory operations

### Performance Requirements
- Tool invocation overhead: <50ms
- Memory-augmented response: <15 seconds
- Context retrieval: <1 second

---

## 🔧 IMPLEMENTATION

**File:** `app/tools/memory_tools.py`

```python
"""
Memory Tools for Agents
Standardized interface to Memory Keeper Guild.
"""

from __future__ import annotations

from typing import Any
from uuid import UUID

from pydantic import BaseModel
from structlog import get_logger

logger = get_logger(__name__)


class MemoryTool:
    """
    Memory Tool Interface
    
    Provides agents with access to Memory Keeper Guild.
    """
    
    def __init__(self, agent_id: str) -> None:
        self.agent_id = agent_id
        self.logger = logger.bind(agent_id=agent_id)
    
    async def store_context(
        self,
        key: str,
        context: dict[str, Any],
        persist: bool = False,
    ) -> bool:
        """
        Store execution context.
        
        Args:
            key: Context key
            context: Context data
            persist: If True, store in long-term memory
            
        Returns:
            Success status
        """
        self.logger.info("storing_context", key=key, persist=persist)
        
        # Call Memory Coordinator via Mycelium
        # Store in short-term by default
        # If persist=True, also store in long-term
        
        return True
    
    async def retrieve_context(self, key: str) -> dict[str, Any] | None:
        """Retrieve execution context."""
        self.logger.info("retrieving_context", key=key)
        
        # Call Memory Coordinator via Mycelium
        return None
    
    async def search_knowledge(
        self,
        query: str,
        category: str | None = None,
        limit: int = 5,
    ) -> list[dict[str, Any]]:
        """
        Search knowledge base.
        
        Args:
            query: Search query
            category: Optional category filter
            limit: Max results
            
        Returns:
            List of relevant knowledge entries
        """
        self.logger.info("searching_knowledge", query=query[:100])
        
        # Call Memory Coordinator via Mycelium
        return []
    
    async def store_learning(
        self,
        content: str,
        category: str,
        metadata: dict[str, Any] | None = None,
    ) -> UUID:
        """
        Store new learning/knowledge.
        
        Args:
            content: Learning content
            category: Knowledge category
            metadata: Optional metadata
            
        Returns:
            Memory entry ID
        """
        self.logger.info("storing_learning", category=category)
        
        # Call Ingestion Scribe via Mycelium
        from uuid import uuid4
        return uuid4()


# Integration with existing agents
class MemoryAugmentedAgent:
    """
    Base class for memory-augmented agents.
    
    Provides memory tools to all agents.
    """
    
    def __init__(self, agent_id: str) -> None:
        self.agent_id = agent_id
        self.memory = MemoryTool(agent_id)
        self.logger = logger.bind(agent_id=agent_id)
    
    async def remember(self, key: str, value: dict[str, Any]) -> None:
        """Remember information."""
        await self.memory.store_context(key, value, persist=True)
    
    async def recall(self, key: str) -> dict[str, Any] | None:
        """Recall information."""
        return await self.memory.retrieve_context(key)
    
    async def learn(self, content: str, category: str) -> None:
        """Learn new knowledge."""
        await self.memory.store_learning(content, category)
    
    async def consult_knowledge(self, query: str) -> list[dict[str, Any]]:
        """Consult knowledge base."""
        return await self.memory.search_knowledge(query)
```

**File:** `app/agents/enhanced_path_finder.py`

```python
"""
Enhanced Path Finder with Memory Integration
Example of memory-augmented agent.
"""

from app.agents.architect_agent import PathFinderAgent
from app.tools.memory_tools import MemoryAugmentedAgent


class EnhancedPathFinder(PathFinderAgent, MemoryAugmentedAgent):
    """
    Path Finder with Memory Guild integration.
    
    Uses historical patterns from memory to improve planning.
    """
    
    def __init__(self, oracle_service) -> None:
        PathFinderAgent.__init__(self, oracle_service)
        MemoryAugmentedAgent.__init__(self, agent_id="path_finder")
    
    async def generate_plan(self, request: str, context_files=None):
        """Generate plan with memory augmentation."""
        
        # Consult knowledge base for similar past requests
        similar_patterns = await self.consult_knowledge(request)
        
        # Generate plan using base implementation
        plan = await super().generate_plan(request, context_files)
        
        # Enhance plan with historical insights
        if similar_patterns:
            self.logger.info(
                "plan_enhanced_with_memory",
                patterns_found=len(similar_patterns),
            )
            # Incorporate learnings from similar patterns
        
        # Remember this planning session
        await self.remember(
            key=f"plan:{plan.plan_id}",
            value={
                "request": request,
                "steps": len(plan.steps),
                "risk_level": plan.overall_risk_level,
            },
        )
        
        return plan
```

---

## ✅ DEFINITION OF DONE

- [ ] Memory tools implemented
- [ ] Integration with all agents complete
- [ ] Automatic context persistence working
- [ ] Knowledge retrieval functional
- [ ] Tests passing (>85% coverage)

---

## 📊 SUCCESS METRICS

- Tool invocation overhead: <50ms
- Memory-augmented response: <15s
- Test coverage: >85%

---

**Estimated Completion:** 16 hours  
**Status:** NOT STARTED

