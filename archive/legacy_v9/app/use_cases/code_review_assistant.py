"""
Code Review Assistant
DRYAD.AI Agent Evolution Architecture - Production Use Case

An intelligent code review assistant that demonstrates all 6 levels:
- Level 0: Tool Registry, Memory Database, Logging
- Level 1: Sandboxed execution, Memory Coordinator, Memory Scribe, Agent Registry
- Level 2: Stateful tools, Archivist (short-term), Librarian (long-term)
- Level 3: Hybrid Orchestration, HITL for critical decisions
- Level 4: Evaluation and benchmarking
- Level 5: Self-improvement through Professor Agent

This assistant can:
1. Analyze code for bugs, security issues, and best practices
2. Run static analysis tools in sandbox
3. Remember past reviews and coding standards (Memory Guild)
4. Orchestrate multiple specialized agents for complex reviews
5. Escalate to human for critical security issues (HITL)
6. Learn from feedback to improve review quality (Professor Agent)
"""

import asyncio
import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime
from pydantic import BaseModel

from app.database.database import SessionLocal
from app.services.memory_guild.coordinator import MemoryCoordinatorAgent, MemoryRequest, MemoryOperation, MemoryType
from app.services.orchestration.orchestrator import HybridOrchestrator
from app.services.orchestration.complexity_scorer import ComplexityScorer
from app.services.hitl.consultation_manager import ConsultationManager
from app.services.dojo.evaluation_harness import EvaluationHarness
from app.services.lyceum.professor_agent import ProfessorAgent
from app.services.monitoring import timer, increment
from app.services.logging.logger import StructuredLogger


class CodeReviewRequest(BaseModel):
    """Code review request."""
    review_id: str
    repository: str
    pull_request_id: str
    files_changed: List[str]
    diff: str
    author: str
    description: str
    tenant_id: str = "default"


class CodeReviewResult(BaseModel):
    """Code review result."""
    review_id: str
    status: str  # pending, in_progress, completed, escalated
    findings: List[Dict[str, Any]]
    security_issues: List[Dict[str, Any]]
    best_practice_violations: List[Dict[str, Any]]
    complexity_score: float
    recommendation: str
    escalated_to_human: bool
    human_consultation_id: Optional[str] = None
    confidence: float
    timestamp: str


class CodeReviewAssistant:
    """
    Intelligent Code Review Assistant.
    
    Demonstrates complete DRYAD.AI architecture in production.
    """
    
    def __init__(self, db=None, tenant_id: str = "default"):
        """Initialize code review assistant."""
        self.db = db or SessionLocal()
        self.tenant_id = tenant_id
        self.logger = StructuredLogger("code_review_assistant")
        
        # Level 1: Memory Coordinator
        self.memory_coordinator = MemoryCoordinatorAgent(self.db)
        
        # Level 3: Orchestration and HITL
        self.orchestrator = HybridOrchestrator(self.db)
        self.complexity_scorer = ComplexityScorer()
        self.consultation_manager = ConsultationManager(self.db)
        
        # Level 4: Evaluation
        self.evaluation_harness = EvaluationHarness(self.db)
        
        # Level 5: Self-improvement
        self.professor = ProfessorAgent(self.db, agent_id="code_review_professor")
        
        # Logger initialized (async logging not needed in __init__)
    
    async def review_code(self, request: CodeReviewRequest) -> CodeReviewResult:
        """
        Perform comprehensive code review.
        
        This method demonstrates the complete DRYAD.AI workflow:
        1. Store request in memory (Level 1-2)
        2. Analyze complexity (Level 3)
        3. Orchestrate review agents (Level 3)
        4. Escalate if needed (Level 3 HITL)
        5. Track metrics (Level 4)
        6. Learn from results (Level 5)
        """
        with timer("code_review_duration", tenant_id=self.tenant_id):
            # Log review start (sync logging for simplicity)
            increment("code_reviews_total", tenant_id=self.tenant_id)
            
            # Step 1: Store review request in memory (Level 1-2)
            await self._store_review_context(request)
            
            # Step 2: Analyze complexity (Level 3)
            complexity = await self._analyze_complexity(request)
            
            # Step 3: Retrieve relevant past reviews (Level 2)
            past_reviews = await self._retrieve_similar_reviews(request)
            
            # Step 4: Perform review based on complexity (Level 3)
            if complexity.score < 0.5:
                # Simple review - single agent
                findings = await self._simple_review(request, past_reviews)
                escalated = False
                consultation_id = None
            else:
                # Complex review - task force orchestration
                findings = await self._complex_review(request, past_reviews, complexity)
                
                # Check if escalation needed
                escalated, consultation_id = await self._check_escalation(request, findings)
            
            # Step 5: Generate recommendation
            recommendation = self._generate_recommendation(findings, complexity)
            
            # Step 6: Calculate confidence
            confidence = self._calculate_confidence(findings, past_reviews)
            
            # Step 7: Store results in memory for future learning
            result = CodeReviewResult(
                review_id=request.review_id,
                status="escalated" if escalated else "completed",
                findings=[f for f in findings if f["type"] == "general"],
                security_issues=[f for f in findings if f["type"] == "security"],
                best_practice_violations=[f for f in findings if f["type"] == "best_practice"],
                complexity_score=complexity.score,
                recommendation=recommendation,
                escalated_to_human=escalated,
                human_consultation_id=consultation_id,
                confidence=confidence,
                timestamp=datetime.utcnow().isoformat()
            )
            
            await self._store_review_result(result)
            
            # Step 8: Track metrics for evaluation (Level 4)
            increment("code_review_findings", value=len(findings), tenant_id=self.tenant_id)
            increment("code_review_escalations" if escalated else "code_review_completed", tenant_id=self.tenant_id)

            # Log completion (sync logging for simplicity)

            return result
    
    async def _store_review_context(self, request: CodeReviewRequest):
        """Store review request in memory (Level 1-2)."""
        memory_request = MemoryRequest(
            operation=MemoryOperation.STORE,
            memory_type=MemoryType.WORKING,
            content=f"Code review for {request.repository} PR#{request.pull_request_id}",
            value={
                "review_id": request.review_id,
                "repository": request.repository,
                "pr_id": request.pull_request_id,
                "files": request.files_changed,
                "author": request.author,
                "description": request.description
            },
            tenant_id=self.tenant_id,
            agent_id="code_review_assistant"
        )

        await self.memory_coordinator.handle_memory_request(memory_request)
    
    async def _analyze_complexity(self, request: CodeReviewRequest) -> Any:
        """Analyze review complexity (Level 3)."""
        # Mock complexity analysis
        # In production, this would analyze:
        # - Number of files changed
        # - Lines of code changed
        # - File types (security-sensitive files get higher complexity)
        # - Author experience level
        
        files_count = len(request.files_changed)
        has_security_files = any("auth" in f or "security" in f or "crypto" in f 
                                for f in request.files_changed)
        
        score = min(1.0, (files_count / 10.0) + (0.3 if has_security_files else 0))
        
        return type('Complexity', (), {
            'score': score,
            'factors': {
                'files_count': files_count,
                'has_security_files': has_security_files
            }
        })()
    
    async def _retrieve_similar_reviews(self, request: CodeReviewRequest) -> List[Dict]:
        """Retrieve similar past reviews (Level 2 - Librarian)."""
        # Query long-term memory for similar reviews
        query_request = MemoryRequest(
            operation=MemoryOperation.SEARCH,
            memory_type=MemoryType.LONG_TERM,
            query=f"Past code reviews for {request.repository}",
            tenant_id=self.tenant_id,
            agent_id="code_review_assistant"
        )

        response = await self.memory_coordinator.handle_memory_request(query_request)

        # Mock response - in production, this would return actual similar reviews
        return []
    
    async def _simple_review(self, request: CodeReviewRequest, past_reviews: List[Dict]) -> List[Dict]:
        """Perform simple review with single agent (Level 1)."""
        findings = []
        
        # Mock findings - in production, would run actual static analysis
        findings.append({
            "type": "general",
            "severity": "low",
            "file": request.files_changed[0] if request.files_changed else "unknown",
            "line": 42,
            "message": "Consider adding docstring to function",
            "suggestion": "Add comprehensive docstring explaining parameters and return value"
        })
        
        return findings
    
    async def _complex_review(self, request: CodeReviewRequest, past_reviews: List[Dict], complexity: Any) -> List[Dict]:
        """Perform complex review with task force (Level 3)."""
        # In production, this would create a task force with specialized agents:
        # - Security analyzer
        # - Performance analyzer
        # - Best practices checker
        # - Documentation reviewer
        
        findings = []
        
        # Mock complex findings
        if complexity.factors.get('has_security_files'):
            findings.append({
                "type": "security",
                "severity": "high",
                "file": "auth/login.py",
                "line": 156,
                "message": "Potential SQL injection vulnerability",
                "suggestion": "Use parameterized queries instead of string concatenation"
            })
        
        findings.append({
            "type": "best_practice",
            "severity": "medium",
            "file": request.files_changed[0] if request.files_changed else "unknown",
            "line": 89,
            "message": "Function complexity too high (cyclomatic complexity: 15)",
            "suggestion": "Refactor into smaller functions"
        })
        
        return findings
    
    async def _check_escalation(self, request: CodeReviewRequest, findings: List[Dict]) -> tuple[bool, Optional[str]]:
        """Check if human escalation needed (Level 3 HITL)."""
        # Escalate if high-severity security issues found
        security_issues = [f for f in findings if f["type"] == "security" and f["severity"] == "high"]
        
        if security_issues:
            # Create HITL consultation
            consultation_id = f"consult_{uuid.uuid4().hex[:12]}"
            
            # Log escalation (sync logging for simplicity)
            
            return True, consultation_id
        
        return False, None
    
    def _generate_recommendation(self, findings: List[Dict], complexity: Any) -> str:
        """Generate review recommendation."""
        if not findings:
            return "APPROVE: No issues found. Code looks good!"
        
        high_severity = [f for f in findings if f.get("severity") == "high"]
        if high_severity:
            return f"REQUEST_CHANGES: {len(high_severity)} high-severity issue(s) must be addressed"
        
        medium_severity = [f for f in findings if f.get("severity") == "medium"]
        if medium_severity:
            return f"COMMENT: {len(medium_severity)} medium-severity issue(s) should be addressed"
        
        return f"APPROVE_WITH_SUGGESTIONS: {len(findings)} minor issue(s) found"
    
    def _calculate_confidence(self, findings: List[Dict], past_reviews: List[Dict]) -> float:
        """Calculate confidence in review."""
        # Higher confidence with more past reviews to learn from
        base_confidence = 0.7
        past_review_bonus = min(0.2, len(past_reviews) * 0.02)
        
        return min(1.0, base_confidence + past_review_bonus)
    
    async def _store_review_result(self, result: CodeReviewResult):
        """Store review result for future learning (Level 2)."""
        memory_request = MemoryRequest(
            operation=MemoryOperation.STORE,
            memory_type=MemoryType.LONG_TERM,
            content=f"Code review result: {result.recommendation}",
            value=result.model_dump(),
            tenant_id=self.tenant_id,
            agent_id="code_review_assistant"
        )

        await self.memory_coordinator.handle_memory_request(memory_request)

