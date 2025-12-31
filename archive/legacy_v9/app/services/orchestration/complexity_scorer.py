"""
Complexity Scorer - Analyzes task complexity

Scores tasks on multiple dimensions to determine if they require:
- Sequential delegation (simple)
- Task Force collaboration (complex)

Part of Level 3 Orchestration Service.
"""

from typing import Dict, Any, List
from pydantic import BaseModel
from app.services.logging.logger import StructuredLogger

logger = StructuredLogger("complexity_scorer")


class ComplexityScore(BaseModel):
    """Task complexity score breakdown."""
    total_score: float  # 0.0 to 1.0
    dimensions: Dict[str, float]  # Individual dimension scores
    reasoning: str
    requires_collaboration: bool  # True if score > threshold


class ComplexityScorer:
    """
    Level 3 Component: Complexity Scorer
    
    Analyzes task complexity across multiple dimensions to determine
    optimal execution strategy (sequential vs collaborative).
    """
    
    # Threshold for requiring task force (0.0 to 1.0)
    COLLABORATION_THRESHOLD = 0.55  # Lowered slightly to catch more complex tasks
    
    # Dimension weights (must sum to 1.0)
    DIMENSION_WEIGHTS = {
        "scope": 0.30,           # How broad is the task?
        "uncertainty": 0.15,     # How much ambiguity?
        "interdependence": 0.15, # How many dependencies?
        "expertise": 0.30,       # How many specializations needed?
        "risk": 0.10             # What's the impact of failure?
    }
    
    def __init__(self):
        """Initialize complexity scorer."""
        logger.log_info("complexity_scorer_initialized", {})
    
    def score_task(
        self,
        task_description: str,
        context: Dict[str, Any] = None
    ) -> ComplexityScore:
        """
        Score task complexity.
        
        Args:
            task_description: Description of the task
            context: Additional context about the task
            
        Returns:
            ComplexityScore with breakdown
        """
        context = context or {}
        
        # Score each dimension
        dimensions = {
            "scope": self._score_scope(task_description, context),
            "uncertainty": self._score_uncertainty(task_description, context),
            "interdependence": self._score_interdependence(task_description, context),
            "expertise": self._score_expertise(task_description, context),
            "risk": self._score_risk(task_description, context)
        }
        
        # Calculate weighted total
        total_score = sum(
            dimensions[dim] * self.DIMENSION_WEIGHTS[dim]
            for dim in dimensions
        )
        
        # Determine if collaboration is needed
        requires_collaboration = total_score > self.COLLABORATION_THRESHOLD
        
        # Generate reasoning
        reasoning = self._generate_reasoning(dimensions, total_score, requires_collaboration)
        
        score = ComplexityScore(
            total_score=total_score,
            dimensions=dimensions,
            reasoning=reasoning,
            requires_collaboration=requires_collaboration
        )
        
        logger.log_info(
            "task_complexity_scored",
            {
                "total_score": total_score,
                "requires_collaboration": requires_collaboration,
                "dimensions": dimensions
            }
        )
        
        return score
    
    def _score_scope(self, description: str, context: Dict[str, Any]) -> float:
        """Score task scope (0.0 = narrow, 1.0 = broad)."""
        score = 0.0

        # Check for broad scope indicators
        broad_indicators = [
            "multiple", "various", "several", "many", "all",
            "comprehensive", "complete", "entire", "full", "across"
        ]

        description_lower = description.lower()
        for indicator in broad_indicators:
            if indicator in description_lower:
                score += 0.2  # Increased from 0.15

        # Check context for scope hints
        if context.get("num_subtasks", 0) > 3:
            score += 0.4  # Increased from 0.3

        if context.get("estimated_duration_hours", 0) > 4:
            score += 0.3  # Increased from 0.2

        return min(score, 1.0)
    
    def _score_uncertainty(self, description: str, context: Dict[str, Any]) -> float:
        """Score task uncertainty (0.0 = clear, 1.0 = ambiguous)."""
        score = 0.0
        
        # Check for uncertainty indicators
        uncertainty_indicators = [
            "unclear", "ambiguous", "uncertain", "maybe", "possibly",
            "investigate", "explore", "research", "determine", "figure out"
        ]
        
        description_lower = description.lower()
        for indicator in uncertainty_indicators:
            if indicator in description_lower:
                score += 0.2
        
        # Check for question marks
        if "?" in description:
            score += 0.3
        
        # Check context
        if not context.get("requirements_clear", True):
            score += 0.3
        
        return min(score, 1.0)
    
    def _score_interdependence(self, description: str, context: Dict[str, Any]) -> float:
        """Score task interdependence (0.0 = independent, 1.0 = highly dependent)."""
        score = 0.0
        
        # Check for dependency indicators
        dependency_indicators = [
            "depends on", "requires", "needs", "after", "before",
            "coordinate", "integrate", "combine", "merge"
        ]
        
        description_lower = description.lower()
        for indicator in dependency_indicators:
            if indicator in description_lower:
                score += 0.2
        
        # Check context
        num_dependencies = context.get("num_dependencies", 0)
        if num_dependencies > 0:
            score += min(num_dependencies * 0.2, 0.5)
        
        return min(score, 1.0)
    
    def _score_expertise(self, description: str, context: Dict[str, Any]) -> float:
        """Score expertise requirements (0.0 = single skill, 1.0 = multiple specializations)."""
        score = 0.0

        # Check for multi-domain indicators
        domain_indicators = [
            "database", "api", "frontend", "backend", "security",
            "testing", "deployment", "monitoring", "documentation", "audit"
        ]

        description_lower = description.lower()
        domains_mentioned = sum(1 for indicator in domain_indicators if indicator in description_lower)

        if domains_mentioned > 1:
            score += min(domains_mentioned * 0.3, 0.8)  # Increased multiplier and cap

        # Check context
        required_skills = context.get("required_skills", [])
        if len(required_skills) > 2:
            score += 0.4  # Increased from 0.3

        return min(score, 1.0)
    
    def _score_risk(self, description: str, context: Dict[str, Any]) -> float:
        """Score task risk (0.0 = low impact, 1.0 = high impact)."""
        score = 0.0
        
        # Check for high-risk indicators
        risk_indicators = [
            "critical", "production", "security", "data loss",
            "irreversible", "permanent", "delete", "remove"
        ]
        
        description_lower = description.lower()
        for indicator in risk_indicators:
            if indicator in description_lower:
                score += 0.25
        
        # Check context
        if context.get("affects_production", False):
            score += 0.4
        
        if context.get("requires_approval", False):
            score += 0.3
        
        return min(score, 1.0)
    
    def _generate_reasoning(
        self,
        dimensions: Dict[str, float],
        total_score: float,
        requires_collaboration: bool
    ) -> str:
        """Generate human-readable reasoning for the score."""
        
        # Find highest scoring dimensions
        sorted_dims = sorted(dimensions.items(), key=lambda x: x[1], reverse=True)
        top_dims = [dim for dim, score in sorted_dims[:2] if score > 0.3]
        
        if requires_collaboration:
            reasoning = f"Task requires collaboration (score: {total_score:.2f}). "
            if top_dims:
                reasoning += f"High complexity in: {', '.join(top_dims)}. "
            reasoning += "Recommend Task Force for multi-agent collaboration."
        else:
            reasoning = f"Task suitable for sequential execution (score: {total_score:.2f}). "
            if top_dims:
                reasoning += f"Moderate complexity in: {', '.join(top_dims)}. "
            reasoning += "Single agent can handle this task."
        
        return reasoning

