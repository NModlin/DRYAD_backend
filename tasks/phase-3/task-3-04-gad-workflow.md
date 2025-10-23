# Task 3-04: GAD Workflow Orchestration Implementation

**Phase:** 3 - Advanced Collaboration & Governance  
**Week:** 14  
**Estimated Hours:** 16 hours  
**Priority:** CRITICAL  
**Dependencies:** Tasks 3-01, 3-02, 3-03 (Path Finder, Sage, Memory Grove)

---

## 🎯 OBJECTIVE

Implement the complete GAD (Governed Agentic Development) workflow orchestration system that coordinates the Plan-Review-Execute-Remember cycle. This is the core engine that ties together all GAD lifecycle components.

---

## 📋 REQUIREMENTS

### Functional Requirements
- Orchestrate complete Plan-Review-Execute-Remember cycle
- Manage workflow state transitions
- Handle approval workflows (Tier 1/2/3)
- Coordinate between Path Finder, Sage, Protected Clearing, and Memory Grove
- Support workflow pause/resume for human intervention
- Provide real-time workflow status updates
- Handle workflow failures and rollbacks

### Technical Requirements
- State machine implementation for workflow phases
- Async/await patterns for phase coordination
- Database persistence for workflow state
- Event-driven architecture for phase transitions
- Comprehensive error handling and recovery
- Audit logging for all workflow actions

### Performance Requirements
- Phase transition: <1 second
- Workflow status query: <100ms
- State persistence: <500ms
- Complete cycle (simple task): <5 minutes

---

## 🔧 IMPLEMENTATION STEPS

### Step 1: Create GAD Workflow Service (12 hours)

**File:** `app/core/gad_workflow.py`

```python
"""
GAD Workflow Orchestration - Complete Plan-Review-Execute-Remember Cycle
Coordinates all phases of the Governed Agentic Development lifecycle.
"""

from __future__ import annotations

import asyncio
from datetime import datetime
from enum import Enum
from typing import Any, Callable
from uuid import UUID, uuid4

from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from structlog import get_logger

from app.database.models import WorkflowExecution, WorkflowPhase as DBWorkflowPhase
from app.services.architect_agent import PathFinderAgent, ExecutionPlanModel
from app.services.plan_sanity_check import SageAgent, RiskAssessment, RiskTier
from app.services.protected_clearing import ProtectedClearingService
from app.services.memory_grove import MemoryGroveService

logger = get_logger(__name__)


class WorkflowPhase(str, Enum):
    """GAD workflow phases."""
    
    PLAN = "PLAN"
    REVIEW = "REVIEW"
    EXECUTE = "EXECUTE"
    REMEMBER = "REMEMBER"
    COMPLETE = "COMPLETE"
    FAILED = "FAILED"
    PAUSED = "PAUSED"


class WorkflowStatus(str, Enum):
    """Workflow execution status."""
    
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    AWAITING_APPROVAL = "AWAITING_APPROVAL"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class WorkflowEvent(BaseModel):
    """Event emitted during workflow execution."""
    
    event_id: UUID = Field(default_factory=uuid4)
    workflow_id: UUID
    phase: WorkflowPhase
    event_type: str  # phase_started, phase_completed, approval_required, etc.
    data: dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class WorkflowState(BaseModel):
    """Current state of workflow execution."""
    
    workflow_id: UUID
    request: str
    current_phase: WorkflowPhase
    status: WorkflowStatus
    plan: ExecutionPlanModel | None = None
    assessment: RiskAssessment | None = None
    execution_result: dict[str, Any] | None = None
    error: str | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: datetime | None = None


class GADWorkflowOrchestrator:
    """
    GAD Workflow Orchestrator
    
    Coordinates the complete Plan-Review-Execute-Remember cycle
    with state management and approval workflows.
    """
    
    def __init__(
        self,
        path_finder: PathFinderAgent,
        sage: SageAgent,
        protected_clearing: ProtectedClearingService,
        memory_grove: MemoryGroveService,
        db_session: AsyncSession,
    ) -> None:
        self.path_finder = path_finder
        self.sage = sage
        self.protected_clearing = protected_clearing
        self.memory_grove = memory_grove
        self.db = db_session
        self.logger = logger.bind(component="gad_workflow")
        
        # Event handlers
        self._event_handlers: dict[str, list[Callable]] = {}
        
        # Active workflows
        self._workflows: dict[UUID, WorkflowState] = {}
    
    async def execute_workflow(
        self,
        request: str,
        context_files: list[str] | None = None,
        auto_approve_tier1: bool = True,
    ) -> WorkflowState:
        """
        Execute complete GAD workflow.
        
        Args:
            request: Natural language task request
            context_files: Optional list of relevant files
            auto_approve_tier1: Auto-approve Tier 1 (low risk) plans
            
        Returns:
            Final workflow state
        """
        workflow_id = uuid4()
        
        self.logger.info(
            "workflow_started",
            workflow_id=str(workflow_id),
            request=request[:100],
        )
        
        # Initialize workflow state
        state = WorkflowState(
            workflow_id=workflow_id,
            request=request,
            current_phase=WorkflowPhase.PLAN,
            status=WorkflowStatus.RUNNING,
        )
        self._workflows[workflow_id] = state
        
        try:
            # Phase 1: PLAN
            state = await self._execute_plan_phase(state, context_files)
            
            # Phase 2: REVIEW
            state = await self._execute_review_phase(state, auto_approve_tier1)
            
            # Check if approved
            if state.status == WorkflowStatus.REJECTED:
                state.current_phase = WorkflowPhase.FAILED
                state.error = "Plan rejected during review"
                return state
            
            # Phase 3: EXECUTE
            state = await self._execute_execution_phase(state)
            
            # Phase 4: REMEMBER
            state = await self._execute_remember_phase(state)
            
            # Mark complete
            state.current_phase = WorkflowPhase.COMPLETE
            state.status = WorkflowStatus.COMPLETED
            state.completed_at = datetime.utcnow()
            
            self.logger.info(
                "workflow_completed",
                workflow_id=str(workflow_id),
                duration_seconds=(state.completed_at - state.created_at).total_seconds(),
            )
            
            return state
            
        except Exception as e:
            self.logger.error(
                "workflow_failed",
                workflow_id=str(workflow_id),
                error=str(e),
                phase=state.current_phase.value,
            )
            
            state.current_phase = WorkflowPhase.FAILED
            state.status = WorkflowStatus.FAILED
            state.error = str(e)
            
            return state
        
        finally:
            # Persist final state
            await self._persist_workflow_state(state)
    
    async def _execute_plan_phase(
        self,
        state: WorkflowState,
        context_files: list[str] | None,
    ) -> WorkflowState:
        """Execute PLAN phase using Path Finder."""
        self.logger.info("plan_phase_started", workflow_id=str(state.workflow_id))
        
        await self._emit_event(WorkflowEvent(
            workflow_id=state.workflow_id,
            phase=WorkflowPhase.PLAN,
            event_type="phase_started",
        ))
        
        # Generate plan
        from pathlib import Path
        context_paths = [Path(f) for f in (context_files or [])]
        plan = await self.path_finder.generate_plan(state.request, context_paths)
        
        state.plan = plan
        state.updated_at = datetime.utcnow()
        
        await self._emit_event(WorkflowEvent(
            workflow_id=state.workflow_id,
            phase=WorkflowPhase.PLAN,
            event_type="phase_completed",
            data={"plan_id": str(plan.plan_id), "steps": len(plan.steps)},
        ))
        
        self.logger.info(
            "plan_phase_completed",
            workflow_id=str(state.workflow_id),
            plan_id=str(plan.plan_id),
        )
        
        return state
    
    async def _execute_review_phase(
        self,
        state: WorkflowState,
        auto_approve_tier1: bool,
    ) -> WorkflowState:
        """Execute REVIEW phase using Sage."""
        self.logger.info("review_phase_started", workflow_id=str(state.workflow_id))
        
        state.current_phase = WorkflowPhase.REVIEW
        
        await self._emit_event(WorkflowEvent(
            workflow_id=state.workflow_id,
            phase=WorkflowPhase.REVIEW,
            event_type="phase_started",
        ))
        
        # Perform risk assessment
        if not state.plan:
            raise ValueError("No plan available for review")
        
        assessment = await self.sage.assess_plan(state.plan)
        state.assessment = assessment
        state.updated_at = datetime.utcnow()
        
        # Handle approval based on tier
        match assessment.risk_tier:
            case RiskTier.TIER_1:
                if auto_approve_tier1:
                    state.status = WorkflowStatus.APPROVED
                    self.logger.info("plan_auto_approved", workflow_id=str(state.workflow_id))
                else:
                    state.status = WorkflowStatus.AWAITING_APPROVAL
                    await self._request_approval(state, "peer_review")
            
            case RiskTier.TIER_2:
                state.status = WorkflowStatus.AWAITING_APPROVAL
                await self._request_approval(state, "peer_review")
            
            case RiskTier.TIER_3:
                state.status = WorkflowStatus.AWAITING_APPROVAL
                await self._request_approval(state, "elder_approval")
        
        # If awaiting approval, pause workflow
        if state.status == WorkflowStatus.AWAITING_APPROVAL:
            state.current_phase = WorkflowPhase.PAUSED
            
            await self._emit_event(WorkflowEvent(
                workflow_id=state.workflow_id,
                phase=WorkflowPhase.REVIEW,
                event_type="approval_required",
                data={
                    "risk_tier": assessment.risk_tier.value,
                    "risk_score": assessment.overall_risk_score,
                },
            ))
            
            # Wait for approval (in real implementation, this would be async)
            # For now, we'll simulate approval
            await asyncio.sleep(0.1)
            state.status = WorkflowStatus.APPROVED
        
        await self._emit_event(WorkflowEvent(
            workflow_id=state.workflow_id,
            phase=WorkflowPhase.REVIEW,
            event_type="phase_completed",
            data={"approved": state.status == WorkflowStatus.APPROVED},
        ))
        
        return state
    
    async def _execute_execution_phase(self, state: WorkflowState) -> WorkflowState:
        """Execute EXECUTE phase in Protected Clearing."""
        self.logger.info("execute_phase_started", workflow_id=str(state.workflow_id))
        
        state.current_phase = WorkflowPhase.EXECUTE
        
        await self._emit_event(WorkflowEvent(
            workflow_id=state.workflow_id,
            phase=WorkflowPhase.EXECUTE,
            event_type="phase_started",
        ))
        
        if not state.plan:
            raise ValueError("No plan available for execution")
        
        # Execute in Protected Clearing
        result = await self.protected_clearing.execute_plan(state.plan)
        
        state.execution_result = result
        state.updated_at = datetime.utcnow()
        
        await self._emit_event(WorkflowEvent(
            workflow_id=state.workflow_id,
            phase=WorkflowPhase.EXECUTE,
            event_type="phase_completed",
            data={"success": result.get("success", False)},
        ))
        
        return state
    
    async def _execute_remember_phase(self, state: WorkflowState) -> WorkflowState:
        """Execute REMEMBER phase - store knowledge in Memory Grove."""
        self.logger.info("remember_phase_started", workflow_id=str(state.workflow_id))
        
        state.current_phase = WorkflowPhase.REMEMBER
        
        await self._emit_event(WorkflowEvent(
            workflow_id=state.workflow_id,
            phase=WorkflowPhase.REMEMBER,
            event_type="phase_started",
        ))
        
        # Store execution results and learnings in Memory Grove
        if state.plan and state.execution_result:
            await self.memory_grove.store_execution_pattern(
                request=state.request,
                plan=state.plan,
                result=state.execution_result,
                success=state.execution_result.get("success", False),
            )
        
        state.updated_at = datetime.utcnow()
        
        await self._emit_event(WorkflowEvent(
            workflow_id=state.workflow_id,
            phase=WorkflowPhase.REMEMBER,
            event_type="phase_completed",
        ))
        
        return state
    
    async def _request_approval(self, state: WorkflowState, approval_type: str) -> None:
        """Request human approval for plan."""
        self.logger.info(
            "approval_requested",
            workflow_id=str(state.workflow_id),
            approval_type=approval_type,
        )
        
        # In real implementation, this would trigger notification
        # to appropriate reviewers via Teams, email, etc.
        pass
    
    async def _emit_event(self, event: WorkflowEvent) -> None:
        """Emit workflow event to registered handlers."""
        handlers = self._event_handlers.get(event.event_type, [])
        
        for handler in handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(event)
                else:
                    handler(event)
            except Exception as e:
                self.logger.error("event_handler_failed", event_type=event.event_type, error=str(e))
    
    async def _persist_workflow_state(self, state: WorkflowState) -> None:
        """Persist workflow state to database."""
        # Implementation would save to database
        pass
    
    def register_event_handler(
        self,
        event_type: str,
        handler: Callable[[WorkflowEvent], None],
    ) -> None:
        """Register event handler for workflow events."""
        if event_type not in self._event_handlers:
            self._event_handlers[event_type] = []
        self._event_handlers[event_type].append(handler)
    
    async def get_workflow_status(self, workflow_id: UUID) -> WorkflowState | None:
        """Get current status of workflow."""
        return self._workflows.get(workflow_id)
    
    async def approve_workflow(self, workflow_id: UUID) -> None:
        """Approve a paused workflow."""
        state = self._workflows.get(workflow_id)
        if state and state.status == WorkflowStatus.AWAITING_APPROVAL:
            state.status = WorkflowStatus.APPROVED
            state.current_phase = WorkflowPhase.REVIEW
    
    async def reject_workflow(self, workflow_id: UUID, reason: str) -> None:
        """Reject a paused workflow."""
        state = self._workflows.get(workflow_id)
        if state and state.status == WorkflowStatus.AWAITING_APPROVAL:
            state.status = WorkflowStatus.REJECTED
            state.error = reason
```

---

## ✅ DEFINITION OF DONE

- [ ] GAD workflow orchestrator implemented
- [ ] All four phases (Plan, Review, Execute, Remember) functional
- [ ] State machine working correctly
- [ ] Approval workflows operational
- [ ] Event system functional
- [ ] Database persistence working
- [ ] All tests passing (>90% coverage)
- [ ] Integration tests complete
- [ ] Documentation complete

---

## 📊 SUCCESS METRICS

- Workflow completion rate: >95%
- Phase transition time: <1 second
- State persistence reliability: >99.9%
- Event delivery success: >99%
- Test coverage: >90%

---

**Estimated Completion:** 16 hours  
**Assigned To:** Lead Developer  
**Status:** NOT STARTED

