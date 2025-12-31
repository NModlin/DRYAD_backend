"""
Hybrid Orchestrator - Master orchestration logic

Routes tasks to appropriate execution strategy:
- Sequential: Single agent handles task
- Task Force: Multi-agent collaboration
- Escalation: Human intervention required

Part of Level 3 Orchestration Service.
"""

from typing import Dict, Any, Optional
from pydantic import BaseModel

from app.services.orchestration.decision_engine import DecisionEngine, OrchestrationDecision
from app.services.orchestration.task_force_manager import TaskForceManager, TaskForce
from app.services.logging.logger import StructuredLogger

logger = StructuredLogger("hybrid_orchestrator")


class OrchestrationRequest(BaseModel):
    """Request to orchestrate a task."""
    task_id: str
    task_description: str
    agent_id: str
    context: Dict[str, Any] = {}


class OrchestrationResult(BaseModel):
    """Result of orchestration."""
    decision_type: str  # 'sequential', 'task_force', 'escalation'
    task_force_id: Optional[str] = None
    result: Optional[Dict[str, Any]] = None
    decision: Optional[OrchestrationDecision] = None


class HybridOrchestrator:
    """
    Level 3 Component: Hybrid Orchestrator
    
    Master orchestration service that analyzes tasks and routes them
    to the appropriate execution strategy based on complexity.
    
    Execution Strategies:
    - Sequential: Single agent execution for simple tasks
    - Task Force: Multi-agent collaboration for complex tasks
    - Escalation: Human intervention for extremely complex tasks
    """
    
    def __init__(self, db_session=None):
        """
        Initialize hybrid orchestrator.
        
        Args:
            db_session: Database session for persistence
        """
        self.db = db_session
        self.decision_engine = DecisionEngine(db_session)
        self.task_force_manager = TaskForceManager(db_session)
        
        logger.log_info("hybrid_orchestrator_initialized", {})
    
    async def orchestrate(
        self,
        request: OrchestrationRequest
    ) -> OrchestrationResult:
        """
        Orchestrate task execution.
        
        Args:
            request: Orchestration request
            
        Returns:
            OrchestrationResult with execution strategy
        """
        logger.log_info(
            "orchestration_started",
            {
                "task_id": request.task_id,
                "agent_id": request.agent_id
            }
        )
        
        # Make orchestration decision
        decision = await self.decision_engine.make_decision(
            task_id=request.task_id,
            task_description=request.task_description,
            context=request.context
        )
        
        # Route based on decision
        if decision.decision_type == "sequential":
            result = await self._execute_sequential(request, decision)
        elif decision.decision_type == "task_force":
            result = await self._execute_task_force(request, decision)
        elif decision.decision_type == "escalation":
            result = await self._execute_escalation(request, decision)
        else:
            logger.log_error(
                "unknown_decision_type",
                {"decision_type": decision.decision_type}
            )
            result = OrchestrationResult(
                decision_type="sequential",
                result={"error": "Unknown decision type"},
                decision=decision
            )
        
        logger.log_info(
            "orchestration_completed",
            {
                "task_id": request.task_id,
                "decision_type": decision.decision_type
            }
        )
        
        return result
    
    async def _execute_sequential(
        self,
        request: OrchestrationRequest,
        decision: OrchestrationDecision
    ) -> OrchestrationResult:
        """Execute task sequentially with single agent."""
        
        logger.log_info(
            "sequential_execution",
            {"task_id": request.task_id, "agent_id": request.agent_id}
        )
        
        # Mock sequential execution
        # In production, would delegate to agent execution service
        result = {
            "status": "completed",
            "execution_type": "sequential",
            "agent_id": request.agent_id,
            "message": "Task executed by single agent"
        }
        
        return OrchestrationResult(
            decision_type="sequential",
            result=result,
            decision=decision
        )
    
    async def _execute_task_force(
        self,
        request: OrchestrationRequest,
        decision: OrchestrationDecision
    ) -> OrchestrationResult:
        """Execute task with collaborative task force."""
        
        logger.log_info(
            "task_force_execution",
            {"task_id": request.task_id}
        )
        
        # Determine required agent roles based on task
        agent_roles = self._determine_required_roles(
            request.task_description,
            request.context
        )
        
        # Create task force
        task_force = await self.task_force_manager.create_task_force(
            objective=request.task_description,
            orchestrator_id=request.agent_id,
            agent_roles=agent_roles
        )
        
        # Mock task force execution
        # In production, would coordinate multi-agent collaboration
        result = {
            "status": "task_force_created",
            "execution_type": "task_force",
            "task_force_id": task_force.task_force_id,
            "num_members": len(task_force.members),
            "message": "Task force created for collaborative execution"
        }
        
        return OrchestrationResult(
            decision_type="task_force",
            task_force_id=task_force.task_force_id,
            result=result,
            decision=decision
        )
    
    async def _execute_escalation(
        self,
        request: OrchestrationRequest,
        decision: OrchestrationDecision
    ) -> OrchestrationResult:
        """Escalate task to human oversight."""
        
        logger.log_info(
            "escalation_execution",
            {"task_id": request.task_id}
        )
        
        # Mock escalation
        # In production, would integrate with HITL system
        result = {
            "status": "escalated",
            "execution_type": "escalation",
            "message": "Task escalated to human oversight",
            "requires_human_input": True
        }
        
        return OrchestrationResult(
            decision_type="escalation",
            result=result,
            decision=decision
        )
    
    def _determine_required_roles(
        self,
        task_description: str,
        context: Dict[str, Any]
    ) -> list[str]:
        """Determine required agent roles for task force."""
        
        # Mock role determination based on keywords
        # In production, would use more sophisticated analysis
        roles = []
        
        description_lower = task_description.lower()
        
        if any(word in description_lower for word in ["database", "data", "query"]):
            roles.append("database_specialist")
        
        if any(word in description_lower for word in ["api", "endpoint", "service"]):
            roles.append("api_specialist")
        
        if any(word in description_lower for word in ["test", "testing", "validation"]):
            roles.append("testing_specialist")
        
        if any(word in description_lower for word in ["security", "auth", "permission"]):
            roles.append("security_specialist")
        
        # Default roles if none detected
        if not roles:
            roles = ["generalist", "reviewer"]
        
        # Always include a coordinator
        if "coordinator" not in roles:
            roles.insert(0, "coordinator")
        
        return roles
    
    async def get_orchestration_stats(self) -> Dict[str, Any]:
        """Get orchestration statistics."""
        
        stats = self.decision_engine.get_decision_stats()
        
        # Add task force stats
        if self.db:
            try:
                query = """
                    SELECT status, COUNT(*) as count
                    FROM task_forces
                    GROUP BY status
                """
                cursor = self.db.execute(query)
                results = cursor.fetchall()
                
                stats["task_forces"] = {
                    "total": sum(row[1] for row in results),
                    "by_status": {row[0]: row[1] for row in results}
                }
            except Exception as e:
                logger.log_error("stats_retrieval_failed", {"error": str(e)})
        
        return stats

