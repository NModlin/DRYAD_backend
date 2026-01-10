"""
Decision Engine - Routes tasks to execution strategies

Makes orchestration decisions based on complexity scores:
- Sequential: Single agent execution
- Task Force: Multi-agent collaboration
- Escalation: Human intervention required

Part of Level 3 Orchestration Service.
"""

from typing import Dict, Any, Optional
from pydantic import BaseModel
from datetime import datetime
import uuid

from app.services.orchestration.complexity_scorer import ComplexityScorer, ComplexityScore
from app.services.logging.logger import StructuredLogger

logger = StructuredLogger("decision_engine")


class OrchestrationDecision(BaseModel):
    """Orchestration decision record."""
    decision_id: str
    task_id: str
    decision_type: str  # 'sequential', 'task_force', 'escalation'
    complexity_score: float
    reasoning: str
    created_at: str
    metadata: Dict[str, Any] = {}


class DecisionEngine:
    """
    Level 3 Component: Decision Engine
    
    Routes tasks to appropriate execution strategy based on
    complexity analysis and system state.
    """
    
    # Decision thresholds
    ESCALATION_THRESHOLD = 0.9  # Extremely complex tasks need human input
    
    def __init__(self, db_session=None):
        """
        Initialize decision engine.
        
        Args:
            db_session: Optional database session for logging decisions
        """
        self.db = db_session
        self.complexity_scorer = ComplexityScorer()
        logger.log_info("decision_engine_initialized", {})
    
    async def make_decision(
        self,
        task_id: str,
        task_description: str,
        context: Dict[str, Any] = None
    ) -> OrchestrationDecision:
        """
        Make orchestration decision for a task.
        
        Args:
            task_id: Unique task identifier
            task_description: Description of the task
            context: Additional context
            
        Returns:
            OrchestrationDecision with routing information
        """
        context = context or {}
        
        # Score task complexity
        complexity: ComplexityScore = self.complexity_scorer.score_task(
            task_description,
            context
        )
        
        # Determine decision type
        if complexity.total_score >= self.ESCALATION_THRESHOLD:
            decision_type = "escalation"
            reasoning = f"Task extremely complex (score: {complexity.total_score:.2f}). Requires human oversight."
        elif complexity.requires_collaboration:
            decision_type = "task_force"
            reasoning = complexity.reasoning
        else:
            decision_type = "sequential"
            reasoning = complexity.reasoning
        
        # Create decision record
        decision = OrchestrationDecision(
            decision_id=str(uuid.uuid4()),
            task_id=task_id,
            decision_type=decision_type,
            complexity_score=complexity.total_score,
            reasoning=reasoning,
            created_at=datetime.utcnow().isoformat(),
            metadata={
                "complexity_dimensions": complexity.dimensions,
                "context": context
            }
        )
        
        # Log decision
        logger.log_info(
            "orchestration_decision_made",
            {
                "decision_id": decision.decision_id,
                "task_id": task_id,
                "decision_type": decision_type,
                "complexity_score": complexity.total_score
            }
        )
        
        # Store in database if available
        if self.db:
            await self._store_decision(decision)
        
        return decision
    
    async def _store_decision(self, decision: OrchestrationDecision):
        """Store decision in database."""
        try:
            import json
            
            # Insert into orchestration_decisions table
            query = """
                INSERT INTO orchestration_decisions 
                (decision_id, task_id, decision_type, complexity_score, reasoning, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """
            
            self.db.execute(
                query,
                (
                    decision.decision_id,
                    decision.task_id,
                    decision.decision_type,
                    decision.complexity_score,
                    decision.reasoning,
                    decision.created_at
                )
            )
            self.db.commit()
            
            logger.log_info(
                "decision_stored",
                {"decision_id": decision.decision_id}
            )
        except Exception as e:
            logger.log_error(
                "decision_storage_failed",
                {"error": str(e), "decision_id": decision.decision_id}
            )
    
    def get_decision_stats(self) -> Dict[str, Any]:
        """Get statistics about orchestration decisions."""
        if not self.db:
            return {"error": "No database connection"}
        
        try:
            # Count decisions by type
            query = """
                SELECT decision_type, COUNT(*) as count
                FROM orchestration_decisions
                GROUP BY decision_type
            """
            
            cursor = self.db.execute(query)
            results = cursor.fetchall()
            
            stats = {
                "total_decisions": sum(row[1] for row in results),
                "by_type": {row[0]: row[1] for row in results},
                "avg_complexity": self._get_avg_complexity()
            }
            
            return stats
        except Exception as e:
            logger.log_error("stats_retrieval_failed", {"error": str(e)})
            return {"error": str(e)}
    
    def _get_avg_complexity(self) -> float:
        """Get average complexity score."""
        try:
            query = "SELECT AVG(complexity_score) FROM orchestration_decisions"
            cursor = self.db.execute(query)
            result = cursor.fetchone()
            return result[0] if result and result[0] else 0.0
        except Exception:
            return 0.0

