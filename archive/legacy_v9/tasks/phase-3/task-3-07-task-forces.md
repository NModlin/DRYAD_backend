# Task 3-07: Forest Council / Expedition Task Forces Implementation

**Phase:** 3 - Advanced Collaboration & Governance  
**Week:** 15  
**Estimated Hours:** 20 hours  
**Priority:** HIGH  
**Dependencies:** Phase 2 complete (Agent Swarm)

---

## 🎯 OBJECTIVE

Implement dynamic multi-agent collaboration through Task Forces (Forest Councils for persistent teams, Expeditions for temporary missions). This enables simultaneous specialist agent collaboration for complex problems requiring multiple expertise domains.

---

## 📋 REQUIREMENTS

### Functional Requirements
- Create temporary collaborative agent teams
- Enable real-time inter-agent communication
- Implement result synthesis from multiple agents
- Support both persistent (Forest Council) and temporary (Expedition) teams
- Provide conflict resolution mechanisms
- Enable consensus-building algorithms
- Track complete conversational history

### Technical Requirements
- Async/await patterns for concurrent agent execution
- WebSocket or message queue for real-time communication
- Database persistence for task force logs
- Agent capability matching for team composition
- Comprehensive audit logging

### Performance Requirements
- Task force creation: <2 seconds
- Agent message delivery: <500ms
- Result synthesis: <10 seconds
- Concurrent agents: Up to 10 per task force

---

## 🔧 IMPLEMENTATION STEPS

### Step 1: Create Task Force Orchestration Service (16 hours)

**File:** `app/services/task_force_orchestration.py`

```python
"""
Task Force Orchestration - Dynamic Multi-Agent Collaboration
Enables Forest Councils (persistent) and Expeditions (temporary) for complex problem-solving.
"""

from __future__ import annotations

import asyncio
from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from structlog import get_logger

from app.core.oracle import OracleService
from app.database.models import TaskForce as DBTaskForce, TaskForceMessage

logger = get_logger(__name__)


class TaskForceType(str, Enum):
    """Type of task force."""
    
    FOREST_COUNCIL = "FOREST_COUNCIL"  # Persistent, long-running
    EXPEDITION = "EXPEDITION"  # Temporary, mission-specific


class AgentRole(str, Enum):
    """Role of agent in task force."""
    
    COORDINATOR = "COORDINATOR"  # Leads the task force
    SPECIALIST = "SPECIALIST"  # Domain expert
    OBSERVER = "OBSERVER"  # Monitors but doesn't contribute


class Message(BaseModel):
    """Message in task force conversation."""
    
    message_id: UUID = Field(default_factory=uuid4)
    task_force_id: UUID
    agent_id: str
    agent_name: str
    content: str
    message_type: str = "contribution"  # contribution, question, answer, consensus
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: dict[str, Any] = Field(default_factory=dict)


class TaskForceConfig(BaseModel):
    """Configuration for task force."""
    
    task_force_id: UUID = Field(default_factory=uuid4)
    name: str
    task_force_type: TaskForceType
    problem_statement: str
    required_capabilities: list[str] = Field(default_factory=list)
    max_agents: int = Field(default=5, ge=2, le=10)
    max_rounds: int = Field(default=10, ge=1, le=50)
    consensus_threshold: float = Field(default=0.8, ge=0.5, le=1.0)
    timeout_minutes: int = Field(default=30, ge=5, le=120)


class TaskForceResult(BaseModel):
    """Result from task force collaboration."""
    
    task_force_id: UUID
    success: bool
    solution: str
    consensus_score: float
    participating_agents: list[str]
    message_count: int
    rounds_completed: int
    execution_time_seconds: float
    individual_contributions: dict[str, str] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class TaskForceOrchestrator:
    """
    Task Force Orchestrator
    
    Manages dynamic multi-agent collaboration through
    Forest Councils and Expeditions.
    """
    
    def __init__(
        self,
        oracle_service: OracleService,
        db_session: AsyncSession,
    ) -> None:
        self.oracle = oracle_service
        self.db = db_session
        self.logger = logger.bind(service="task_force")
        
        # Active task forces
        self._active_task_forces: dict[UUID, list[Message]] = {}
    
    async def create_task_force(
        self,
        config: TaskForceConfig,
        agent_ids: list[str],
    ) -> UUID:
        """
        Create new task force with specified agents.
        
        Args:
            config: Task force configuration
            agent_ids: List of agent IDs to include
            
        Returns:
            Task force ID
        """
        self.logger.info(
            "creating_task_force",
            task_force_id=str(config.task_force_id),
            type=config.task_force_type.value,
            agents=len(agent_ids),
        )
        
        if len(agent_ids) > config.max_agents:
            raise ValueError(f"Too many agents: {len(agent_ids)} > {config.max_agents}")
        
        # Initialize message history
        self._active_task_forces[config.task_force_id] = []
        
        # Persist to database
        await self._persist_task_force(config, agent_ids)
        
        return config.task_force_id
    
    async def execute_task_force(
        self,
        task_force_id: UUID,
        config: TaskForceConfig,
        agent_ids: list[str],
    ) -> TaskForceResult:
        """
        Execute task force collaboration.
        
        Args:
            task_force_id: Task force identifier
            config: Task force configuration
            agent_ids: Participating agent IDs
            
        Returns:
            Collaboration result with synthesized solution
        """
        self.logger.info(
            "executing_task_force",
            task_force_id=str(task_force_id),
        )
        
        start_time = datetime.utcnow()
        messages = self._active_task_forces.get(task_force_id, [])
        
        try:
            # Round 1: Initial contributions from all agents
            initial_contributions = await self._gather_initial_contributions(
                task_force_id=task_force_id,
                problem=config.problem_statement,
                agent_ids=agent_ids,
            )
            
            messages.extend(initial_contributions)
            
            # Iterative refinement rounds
            for round_num in range(1, config.max_rounds):
                self.logger.info(
                    "task_force_round",
                    task_force_id=str(task_force_id),
                    round=round_num,
                )
                
                # Check for consensus
                consensus_score = await self._calculate_consensus(messages)
                
                if consensus_score >= config.consensus_threshold:
                    self.logger.info(
                        "consensus_reached",
                        task_force_id=str(task_force_id),
                        round=round_num,
                        score=consensus_score,
                    )
                    break
                
                # Gather refinements
                refinements = await self._gather_refinements(
                    task_force_id=task_force_id,
                    previous_messages=messages,
                    agent_ids=agent_ids,
                )
                
                messages.extend(refinements)
                
                # Check timeout
                elapsed = (datetime.utcnow() - start_time).total_seconds()
                if elapsed > config.timeout_minutes * 60:
                    self.logger.warning(
                        "task_force_timeout",
                        task_force_id=str(task_force_id),
                    )
                    break
            
            # Synthesize final solution
            solution = await self._synthesize_solution(messages)
            
            # Calculate final consensus
            final_consensus = await self._calculate_consensus(messages)
            
            # Build result
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            
            result = TaskForceResult(
                task_force_id=task_force_id,
                success=final_consensus >= config.consensus_threshold,
                solution=solution,
                consensus_score=final_consensus,
                participating_agents=agent_ids,
                message_count=len(messages),
                rounds_completed=round_num,
                execution_time_seconds=execution_time,
                individual_contributions={
                    msg.agent_name: msg.content
                    for msg in initial_contributions
                },
            )
            
            self.logger.info(
                "task_force_completed",
                task_force_id=str(task_force_id),
                success=result.success,
                consensus=final_consensus,
            )
            
            return result
            
        except Exception as e:
            self.logger.error(
                "task_force_failed",
                task_force_id=str(task_force_id),
                error=str(e),
            )
            raise
    
    async def _gather_initial_contributions(
        self,
        task_force_id: UUID,
        problem: str,
        agent_ids: list[str],
    ) -> list[Message]:
        """Gather initial contributions from all agents concurrently."""
        
        async def get_agent_contribution(agent_id: str) -> Message:
            """Get contribution from single agent."""
            prompt = f"""You are participating in a collaborative task force.

PROBLEM:
{problem}

Provide your expert analysis and proposed solution. Be specific and actionable.
"""
            
            response = await self.oracle.consult(
                prompt=prompt,
                model_tier="balanced",  # Tier 2 for specialists
                temperature=0.7,
                max_tokens=1000,
            )
            
            return Message(
                task_force_id=task_force_id,
                agent_id=agent_id,
                agent_name=f"Agent-{agent_id[:8]}",
                content=response,
                message_type="contribution",
            )
        
        # Gather contributions concurrently
        contributions = await asyncio.gather(*[
            get_agent_contribution(agent_id)
            for agent_id in agent_ids
        ])
        
        return list(contributions)
    
    async def _gather_refinements(
        self,
        task_force_id: UUID,
        previous_messages: list[Message],
        agent_ids: list[str],
    ) -> list[Message]:
        """Gather refinements based on previous round."""
        
        # Build context from previous messages
        context = "\n\n".join([
            f"{msg.agent_name}: {msg.content}"
            for msg in previous_messages[-10:]  # Last 10 messages
        ])
        
        async def get_agent_refinement(agent_id: str) -> Message:
            """Get refinement from single agent."""
            prompt = f"""You are participating in a collaborative task force.

PREVIOUS DISCUSSION:
{context}

Based on the discussion, provide your refined analysis or address any concerns raised.
Focus on building consensus and resolving conflicts.
"""
            
            response = await self.oracle.consult(
                prompt=prompt,
                model_tier="balanced",
                temperature=0.6,
                max_tokens=800,
            )
            
            return Message(
                task_force_id=task_force_id,
                agent_id=agent_id,
                agent_name=f"Agent-{agent_id[:8]}",
                content=response,
                message_type="refinement",
            )
        
        refinements = await asyncio.gather(*[
            get_agent_refinement(agent_id)
            for agent_id in agent_ids
        ])
        
        return list(refinements)
    
    async def _calculate_consensus(self, messages: list[Message]) -> float:
        """Calculate consensus score from messages."""
        if len(messages) < 2:
            return 0.0
        
        # Use LLM to analyze consensus
        recent_messages = messages[-10:]
        context = "\n\n".join([
            f"{msg.agent_name}: {msg.content}"
            for msg in recent_messages
        ])
        
        prompt = f"""Analyze the following discussion and rate the consensus level.

DISCUSSION:
{context}

Rate the consensus on a scale of 0.0 to 1.0, where:
- 0.0 = Complete disagreement
- 0.5 = Partial agreement
- 1.0 = Complete consensus

Return only the numeric score.
"""
        
        try:
            response = await self.oracle.consult(
                prompt=prompt,
                model_tier="reasoning",
                temperature=0.1,
                max_tokens=10,
            )
            
            score = float(response.strip())
            return max(0.0, min(1.0, score))
            
        except Exception as e:
            self.logger.warning("consensus_calculation_failed", error=str(e))
            return 0.5  # Default to neutral
    
    async def _synthesize_solution(self, messages: list[Message]) -> str:
        """Synthesize final solution from all contributions."""
        
        all_contributions = "\n\n".join([
            f"{msg.agent_name}: {msg.content}"
            for msg in messages
        ])
        
        prompt = f"""Synthesize a comprehensive solution from the following collaborative discussion.

DISCUSSION:
{all_contributions}

Provide a clear, actionable solution that incorporates the best ideas from all participants.
"""
        
        solution = await self.oracle.consult(
            prompt=prompt,
            model_tier="reasoning",
            temperature=0.3,
            max_tokens=2000,
        )
        
        return solution
    
    async def _persist_task_force(
        self,
        config: TaskForceConfig,
        agent_ids: list[str],
    ) -> None:
        """Persist task force to database."""
        # Implementation would save to database
        pass
```

---

## ✅ DEFINITION OF DONE

- [ ] Task Force orchestrator implemented
- [ ] Concurrent agent execution working
- [ ] Consensus calculation functional
- [ ] Result synthesis operational
- [ ] Message persistence working
- [ ] All tests passing (>85% coverage)
- [ ] Integration tests complete
- [ ] Documentation complete

---

## 📊 SUCCESS METRICS

- Task force success rate: >90%
- Consensus accuracy: >85%
- Average collaboration time: <15 minutes
- Agent coordination overhead: <10%
- Test coverage: >85%

---

**Estimated Completion:** 20 hours  
**Assigned To:** Agent Specialist  
**Status:** NOT STARTED

