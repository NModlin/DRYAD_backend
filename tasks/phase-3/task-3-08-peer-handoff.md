# Task 3-08: Peer-to-Peer Handoff Implementation

**Phase:** 3 - Advanced Collaboration & Governance  
**Week:** 15  
**Estimated Hours:** 12 hours  
**Priority:** HIGH  
**Dependencies:** Phase 2 complete (Agent Swarm)

---

## 🎯 OBJECTIVE

Implement Peer-to-Peer Handoff mechanism allowing specialist agents to delegate directly to other specialists without returning to the orchestrator. This reduces latency and enables more natural agent collaboration patterns.

---

## 📋 REQUIREMENTS

### Functional Requirements
- Enable direct agent-to-agent delegation
- Maintain context across handoffs
- Track handoff chains for audit
- Support handoff with context enrichment
- Implement handoff timeout and fallback
- Prevent infinite handoff loops

### Technical Requirements
- Agent capability registry
- Context serialization/deserialization
- Async message passing between agents
- Handoff chain tracking
- Comprehensive logging

### Performance Requirements
- Handoff latency: <500ms
- Context transfer: <1 second
- Max handoff chain depth: 5
- Timeout per handoff: 60 seconds

---

## 🔧 IMPLEMENTATION STEPS

### Step 1: Create Peer Handoff Service (10 hours)

**File:** `app/services/peer_handoff.py`

```python
"""
Peer-to-Peer Handoff - Direct Agent Delegation
Enables specialists to delegate to other specialists without orchestrator.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Callable
from uuid import UUID, uuid4

from pydantic import BaseModel, Field
from structlog import get_logger

logger = get_logger(__name__)


class AgentCapability(str, Enum):
    """Agent capability types."""
    
    CODE_ANALYSIS = "CODE_ANALYSIS"
    SECURITY_AUDIT = "SECURITY_AUDIT"
    PERFORMANCE_OPTIMIZATION = "PERFORMANCE_OPTIMIZATION"
    DATABASE_OPERATIONS = "DATABASE_OPERATIONS"
    API_INTEGRATION = "API_INTEGRATION"
    TESTING = "TESTING"
    DEPLOYMENT = "DEPLOYMENT"


class HandoffContext(BaseModel):
    """Context passed during agent handoff."""
    
    handoff_id: UUID = Field(default_factory=uuid4)
    chain_id: UUID  # Tracks entire handoff chain
    from_agent: str
    to_agent: str
    task_description: str
    context_data: dict[str, Any] = Field(default_factory=dict)
    previous_results: list[dict[str, Any]] = Field(default_factory=list)
    chain_depth: int = Field(default=0, ge=0, le=5)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class HandoffResult(BaseModel):
    """Result from agent handoff."""
    
    handoff_id: UUID
    success: bool
    result_data: dict[str, Any]
    execution_time_seconds: float
    next_handoff: HandoffContext | None = None
    completed_at: datetime = Field(default_factory=datetime.utcnow)


class AgentRegistration(BaseModel):
    """Agent registration in capability registry."""
    
    agent_id: str
    agent_name: str
    capabilities: list[AgentCapability]
    handler: Callable[[HandoffContext], HandoffResult]
    max_concurrent_tasks: int = Field(default=5, ge=1, le=20)
    current_load: int = Field(default=0, ge=0)


class PeerHandoffService:
    """
    Peer-to-Peer Handoff Service
    
    Manages direct agent-to-agent delegation without
    orchestrator involvement.
    """
    
    MAX_CHAIN_DEPTH = 5
    HANDOFF_TIMEOUT_SECONDS = 60
    
    def __init__(self) -> None:
        self.logger = logger.bind(service="peer_handoff")
        
        # Agent capability registry
        self._agent_registry: dict[str, AgentRegistration] = {}
        
        # Active handoff chains
        self._active_chains: dict[UUID, list[HandoffContext]] = {}
    
    def register_agent(
        self,
        agent_id: str,
        agent_name: str,
        capabilities: list[AgentCapability],
        handler: Callable[[HandoffContext], HandoffResult],
        max_concurrent: int = 5,
    ) -> None:
        """
        Register agent in capability registry.
        
        Args:
            agent_id: Unique agent identifier
            agent_name: Human-readable agent name
            capabilities: List of agent capabilities
            handler: Async function to handle handoffs
            max_concurrent: Max concurrent tasks
        """
        self.logger.info(
            "registering_agent",
            agent_id=agent_id,
            capabilities=[c.value for c in capabilities],
        )
        
        self._agent_registry[agent_id] = AgentRegistration(
            agent_id=agent_id,
            agent_name=agent_name,
            capabilities=capabilities,
            handler=handler,
            max_concurrent_tasks=max_concurrent,
        )
    
    def find_agent_by_capability(
        self,
        capability: AgentCapability,
        exclude_agents: list[str] | None = None,
    ) -> str | None:
        """
        Find available agent with specified capability.
        
        Args:
            capability: Required capability
            exclude_agents: Agents to exclude from search
            
        Returns:
            Agent ID or None if no agent available
        """
        exclude_agents = exclude_agents or []
        
        # Find agents with capability and available capacity
        candidates = [
            agent
            for agent in self._agent_registry.values()
            if capability in agent.capabilities
            and agent.agent_id not in exclude_agents
            and agent.current_load < agent.max_concurrent_tasks
        ]
        
        if not candidates:
            return None
        
        # Return agent with lowest current load
        return min(candidates, key=lambda a: a.current_load).agent_id
    
    async def handoff_to_peer(
        self,
        context: HandoffContext,
    ) -> HandoffResult:
        """
        Execute handoff to peer agent.
        
        Args:
            context: Handoff context
            
        Returns:
            Handoff result
            
        Raises:
            ValueError: If handoff chain too deep or agent not found
        """
        self.logger.info(
            "executing_handoff",
            handoff_id=str(context.handoff_id),
            from_agent=context.from_agent,
            to_agent=context.to_agent,
            chain_depth=context.chain_depth,
        )
        
        # Validate chain depth
        if context.chain_depth >= self.MAX_CHAIN_DEPTH:
            raise ValueError(
                f"Handoff chain too deep: {context.chain_depth} >= {self.MAX_CHAIN_DEPTH}"
            )
        
        # Get target agent
        target_agent = self._agent_registry.get(context.to_agent)
        if not target_agent:
            raise ValueError(f"Agent not found: {context.to_agent}")
        
        # Check agent capacity
        if target_agent.current_load >= target_agent.max_concurrent_tasks:
            raise ValueError(f"Agent at capacity: {context.to_agent}")
        
        # Track handoff chain
        if context.chain_id not in self._active_chains:
            self._active_chains[context.chain_id] = []
        self._active_chains[context.chain_id].append(context)
        
        try:
            # Increment agent load
            target_agent.current_load += 1
            
            # Execute handoff
            start_time = datetime.utcnow()
            
            result = await target_agent.handler(context)
            
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            result.execution_time_seconds = execution_time
            
            # Handle cascading handoff
            if result.next_handoff:
                result.next_handoff.chain_id = context.chain_id
                result.next_handoff.chain_depth = context.chain_depth + 1
                result.next_handoff.previous_results = [
                    *context.previous_results,
                    result.result_data,
                ]
                
                # Execute next handoff
                next_result = await self.handoff_to_peer(result.next_handoff)
                
                # Merge results
                result.result_data["cascaded_result"] = next_result.result_data
            
            self.logger.info(
                "handoff_completed",
                handoff_id=str(context.handoff_id),
                success=result.success,
                execution_time=execution_time,
            )
            
            return result
            
        except Exception as e:
            self.logger.error(
                "handoff_failed",
                handoff_id=str(context.handoff_id),
                error=str(e),
            )
            
            return HandoffResult(
                handoff_id=context.handoff_id,
                success=False,
                result_data={"error": str(e)},
                execution_time_seconds=0.0,
            )
        
        finally:
            # Decrement agent load
            target_agent.current_load -= 1
    
    def get_handoff_chain(self, chain_id: UUID) -> list[HandoffContext]:
        """Get complete handoff chain."""
        return self._active_chains.get(chain_id, [])
    
    def get_agent_stats(self, agent_id: str) -> dict[str, Any]:
        """Get agent statistics."""
        agent = self._agent_registry.get(agent_id)
        if not agent:
            return {}
        
        return {
            "agent_id": agent.agent_id,
            "agent_name": agent.agent_name,
            "capabilities": [c.value for c in agent.capabilities],
            "current_load": agent.current_load,
            "max_concurrent": agent.max_concurrent_tasks,
            "utilization": agent.current_load / agent.max_concurrent_tasks,
        }
```

### Step 2: Create Tests (2 hours)

**File:** `tests/test_peer_handoff.py`

```python
"""Tests for Peer-to-Peer Handoff."""

import pytest
from uuid import uuid4

from app.services.peer_handoff import (
    PeerHandoffService,
    HandoffContext,
    HandoffResult,
    AgentCapability,
)


@pytest.fixture
def handoff_service():
    """Create handoff service instance."""
    return PeerHandoffService()


@pytest.fixture
def mock_handler():
    """Create mock agent handler."""
    async def handler(context: HandoffContext) -> HandoffResult:
        return HandoffResult(
            handoff_id=context.handoff_id,
            success=True,
            result_data={"processed": True},
            execution_time_seconds=0.1,
        )
    
    return handler


def test_register_agent(handoff_service, mock_handler):
    """Test agent registration."""
    handoff_service.register_agent(
        agent_id="test_agent",
        agent_name="Test Agent",
        capabilities=[AgentCapability.CODE_ANALYSIS],
        handler=mock_handler,
    )
    
    stats = handoff_service.get_agent_stats("test_agent")
    assert stats["agent_id"] == "test_agent"
    assert AgentCapability.CODE_ANALYSIS.value in stats["capabilities"]


def test_find_agent_by_capability(handoff_service, mock_handler):
    """Test finding agent by capability."""
    handoff_service.register_agent(
        agent_id="security_agent",
        agent_name="Security Agent",
        capabilities=[AgentCapability.SECURITY_AUDIT],
        handler=mock_handler,
    )
    
    agent_id = handoff_service.find_agent_by_capability(
        AgentCapability.SECURITY_AUDIT
    )
    
    assert agent_id == "security_agent"


@pytest.mark.asyncio
async def test_handoff_execution(handoff_service, mock_handler):
    """Test handoff execution."""
    # Register agents
    handoff_service.register_agent(
        agent_id="agent_a",
        agent_name="Agent A",
        capabilities=[AgentCapability.CODE_ANALYSIS],
        handler=mock_handler,
    )
    
    # Create handoff context
    context = HandoffContext(
        chain_id=uuid4(),
        from_agent="orchestrator",
        to_agent="agent_a",
        task_description="Analyze code",
        chain_depth=0,
    )
    
    # Execute handoff
    result = await handoff_service.handoff_to_peer(context)
    
    assert result.success is True
    assert result.result_data["processed"] is True
```

---

## ✅ DEFINITION OF DONE

- [ ] Peer handoff service implemented
- [ ] Agent capability registry working
- [ ] Handoff chain tracking functional
- [ ] Context transfer operational
- [ ] All tests passing (>85% coverage)
- [ ] Documentation complete

---

## 📊 SUCCESS METRICS

- Handoff latency: <500ms
- Chain tracking accuracy: 100%
- Agent discovery success: >95%
- Test coverage: >85%

---

**Estimated Completion:** 12 hours  
**Assigned To:** Agent Specialist  
**Status:** NOT STARTED

