# Task 3-02: Sage (Plan Sanity Check AI) Implementation

**Phase:** 3 - Advanced Collaboration & Governance  
**Week:** 13  
**Estimated Hours:** 12 hours  
**Priority:** CRITICAL  
**Dependencies:** Task 3-01 (Path Finder)

---

## 🎯 OBJECTIVE

Implement the Sage agent as the core component of the GAD lifecycle's **Review** phase. This agent performs risk assessment, assigns tiered review levels, and routes plans through the appropriate approval workflow.

---

## 📋 REQUIREMENTS

### Functional Requirements
- Analyze execution plans for risk factors
- Assign risk tiers (Tier 1: Auto-approve, Tier 2: Peer review, Tier 3: Elder approval)
- Identify security vulnerabilities in proposed changes
- Detect potential breaking changes
- Validate plan completeness and feasibility
- Generate detailed risk assessment reports

### Technical Requirements
- Tier 2 Specialist agent with Reasoning LLM (Tier 3)
- Integration with Path Finder output
- Rule-based and ML-based risk assessment
- Async/await patterns
- Comprehensive logging

### Performance Requirements
- Risk assessment: <10 seconds
- Plan validation: <5 seconds
- Approval routing: <2 seconds

---

## 🔧 IMPLEMENTATION STEPS

### Step 1: Create Sage Service (8 hours)

**File:** `app/services/plan_sanity_check.py`

```python
"""
Sage (Plan Sanity Check AI) - GAD Review Phase Implementation
Performs risk assessment and routes plans through tiered approval workflow.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field
from structlog import get_logger

from app.core.oracle import OracleService
from app.services.architect_agent import ExecutionPlanModel, PlanStep

logger = get_logger(__name__)


class RiskTier(str, Enum):
    """Risk tier levels for approval routing."""
    
    TIER_1 = "TIER_1"  # Auto-approve (low risk)
    TIER_2 = "TIER_2"  # Peer review (medium risk)
    TIER_3 = "TIER_3"  # Elder approval (high/critical risk)


class RiskFactor(BaseModel):
    """Individual risk factor identified in plan."""
    
    category: str  # e.g., "security", "breaking_change", "data_loss"
    severity: str  # LOW, MEDIUM, HIGH, CRITICAL
    description: str
    affected_steps: list[int] = Field(default_factory=list)
    mitigation: str | None = None


class RiskAssessment(BaseModel):
    """Complete risk assessment for an execution plan."""
    
    assessment_id: UUID = Field(default_factory=uuid4)
    plan_id: UUID
    risk_tier: RiskTier
    risk_factors: list[RiskFactor] = Field(default_factory=list)
    overall_risk_score: float = Field(ge=0.0, le=100.0)
    approval_required: bool
    recommended_reviewers: list[str] = Field(default_factory=list)
    blocking_issues: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    assessment_rationale: str
    created_at: datetime = Field(default_factory=datetime.utcnow)


class SageAgent:
    """
    Sage (Plan Sanity Check AI) - Tier 2 Specialist
    
    Analyzes execution plans for risks and routes through
    appropriate approval workflow.
    """
    
    # Risk scoring weights
    RISK_WEIGHTS = {
        "security_vulnerability": 30.0,
        "data_loss_potential": 25.0,
        "breaking_change": 20.0,
        "production_impact": 15.0,
        "complexity": 10.0,
    }
    
    # Tier thresholds
    TIER_1_THRESHOLD = 20.0  # Auto-approve if score < 20
    TIER_2_THRESHOLD = 50.0  # Peer review if score < 50
    # Tier 3 if score >= 50 (Elder approval)
    
    def __init__(self, oracle_service: OracleService) -> None:
        self.oracle = oracle_service
        self.logger = logger.bind(agent="sage")
    
    async def assess_plan(self, plan: ExecutionPlanModel) -> RiskAssessment:
        """
        Perform comprehensive risk assessment on execution plan.
        
        Args:
            plan: Execution plan to assess
            
        Returns:
            Complete risk assessment with tier assignment
        """
        self.logger.info("assessing_plan", plan_id=str(plan.plan_id))
        
        try:
            # Step 1: Rule-based risk detection
            rule_based_risks = self._detect_rule_based_risks(plan)
            
            # Step 2: LLM-based risk analysis
            llm_risks = await self._detect_llm_based_risks(plan)
            
            # Step 3: Combine and score risks
            all_risks = rule_based_risks + llm_risks
            risk_score = self._calculate_risk_score(all_risks)
            
            # Step 4: Determine tier and approval requirements
            risk_tier = self._determine_risk_tier(risk_score)
            approval_required = risk_tier != RiskTier.TIER_1
            
            # Step 5: Generate recommendations
            reviewers = self._recommend_reviewers(all_risks, risk_tier)
            blocking_issues = self._identify_blocking_issues(all_risks)
            warnings = self._generate_warnings(all_risks)
            
            # Step 6: Create assessment
            assessment = RiskAssessment(
                plan_id=plan.plan_id,
                risk_tier=risk_tier,
                risk_factors=all_risks,
                overall_risk_score=risk_score,
                approval_required=approval_required,
                recommended_reviewers=reviewers,
                blocking_issues=blocking_issues,
                warnings=warnings,
                assessment_rationale=self._generate_rationale(all_risks, risk_score, risk_tier),
            )
            
            self.logger.info(
                "assessment_complete",
                plan_id=str(plan.plan_id),
                risk_tier=risk_tier.value,
                risk_score=risk_score,
                approval_required=approval_required,
            )
            
            return assessment
            
        except Exception as e:
            self.logger.error("assessment_failed", plan_id=str(plan.plan_id), error=str(e))
            raise
    
    def _detect_rule_based_risks(self, plan: ExecutionPlanModel) -> list[RiskFactor]:
        """Detect risks using predefined rules."""
        risks: list[RiskFactor] = []
        
        # Check for database migrations
        for step in plan.steps:
            if step.target_file and 'migrations' in str(step.target_file):
                risks.append(RiskFactor(
                    category="data_loss_potential",
                    severity="HIGH",
                    description="Database migration detected - potential for data loss",
                    affected_steps=[step.step_number],
                    mitigation="Ensure backup before migration, test on staging first",
                ))
        
        # Check for authentication/security changes
        security_keywords = ['auth', 'password', 'token', 'secret', 'credential']
        for step in plan.steps:
            if any(keyword in step.action.lower() for keyword in security_keywords):
                risks.append(RiskFactor(
                    category="security_vulnerability",
                    severity="CRITICAL",
                    description=f"Security-related change detected: {step.action}",
                    affected_steps=[step.step_number],
                    mitigation="Security review required, penetration testing recommended",
                ))
        
        # Check for breaking changes
        breaking_keywords = ['remove', 'delete', 'deprecate', 'breaking']
        for step in plan.steps:
            if any(keyword in step.action.lower() for keyword in breaking_keywords):
                risks.append(RiskFactor(
                    category="breaking_change",
                    severity="HIGH",
                    description=f"Potential breaking change: {step.action}",
                    affected_steps=[step.step_number],
                    mitigation="Version bump required, deprecation notice needed",
                ))
        
        # Check for production file modifications
        production_paths = ['app/core/', 'app/api/', 'app/database/']
        for step in plan.steps:
            if step.target_file and any(p in str(step.target_file) for p in production_paths):
                if step.risk_level in ['HIGH', 'CRITICAL']:
                    risks.append(RiskFactor(
                        category="production_impact",
                        severity=step.risk_level,
                        description=f"High-risk change to production code: {step.target_file}",
                        affected_steps=[step.step_number],
                        mitigation="Comprehensive testing required, staged rollout recommended",
                    ))
        
        # Check for high complexity
        if plan.total_estimated_hours > 40:
            risks.append(RiskFactor(
                category="complexity",
                severity="MEDIUM",
                description=f"High complexity plan ({plan.total_estimated_hours} hours)",
                affected_steps=[],
                mitigation="Consider breaking into smaller tasks",
            ))
        
        return risks
    
    async def _detect_llm_based_risks(self, plan: ExecutionPlanModel) -> list[RiskFactor]:
        """Use LLM to detect subtle risks."""
        
        prompt = f"""Analyze this execution plan for potential risks:

PLAN:
{plan.to_yaml()}

Identify any risks in these categories:
1. Security vulnerabilities
2. Data loss potential
3. Breaking changes
4. Performance degradation
5. Scalability issues

Return JSON array of risks:
[
    {{
        "category": "security_vulnerability",
        "severity": "HIGH",
        "description": "Description of risk",
        "affected_steps": [1, 2],
        "mitigation": "Suggested mitigation"
    }}
]
"""
        
        try:
            response = await self.oracle.consult(
                prompt=prompt,
                model_tier="reasoning",
                temperature=0.2,
                max_tokens=2000,
            )
            
            import json
            risks_data = json.loads(response.strip().strip('```json').strip('```'))
            
            return [RiskFactor(**risk) for risk in risks_data]
            
        except Exception as e:
            self.logger.warning("llm_risk_detection_failed", error=str(e))
            return []
    
    def _calculate_risk_score(self, risks: list[RiskFactor]) -> float:
        """Calculate overall risk score from identified risks."""
        score = 0.0
        
        for risk in risks:
            # Base score from severity
            severity_scores = {
                "LOW": 5.0,
                "MEDIUM": 15.0,
                "HIGH": 30.0,
                "CRITICAL": 50.0,
            }
            base_score = severity_scores.get(risk.severity, 10.0)
            
            # Apply category weight
            weight = self.RISK_WEIGHTS.get(risk.category, 1.0)
            weighted_score = base_score * (weight / 30.0)  # Normalize
            
            score += weighted_score
        
        return min(score, 100.0)  # Cap at 100
    
    def _determine_risk_tier(self, risk_score: float) -> RiskTier:
        """Determine approval tier based on risk score."""
        if risk_score < self.TIER_1_THRESHOLD:
            return RiskTier.TIER_1
        elif risk_score < self.TIER_2_THRESHOLD:
            return RiskTier.TIER_2
        else:
            return RiskTier.TIER_3
    
    def _recommend_reviewers(self, risks: list[RiskFactor], tier: RiskTier) -> list[str]:
        """Recommend appropriate reviewers based on risks."""
        reviewers: set[str] = set()
        
        for risk in risks:
            match risk.category:
                case "security_vulnerability":
                    reviewers.add("security_team")
                case "data_loss_potential":
                    reviewers.add("database_admin")
                case "breaking_change":
                    reviewers.add("api_team")
                case "production_impact":
                    reviewers.add("devops_team")
        
        if tier == RiskTier.TIER_3:
            reviewers.add("tech_lead")
        
        return sorted(list(reviewers))
    
    def _identify_blocking_issues(self, risks: list[RiskFactor]) -> list[str]:
        """Identify issues that block plan execution."""
        blocking: list[str] = []
        
        for risk in risks:
            if risk.severity == "CRITICAL" and not risk.mitigation:
                blocking.append(f"{risk.category}: {risk.description}")
        
        return blocking
    
    def _generate_warnings(self, risks: list[RiskFactor]) -> list[str]:
        """Generate warning messages."""
        return [
            f"{risk.severity}: {risk.description}"
            for risk in risks
            if risk.severity in ["HIGH", "CRITICAL"]
        ]
    
    def _generate_rationale(
        self,
        risks: list[RiskFactor],
        score: float,
        tier: RiskTier,
    ) -> str:
        """Generate human-readable assessment rationale."""
        risk_count = len(risks)
        critical_count = sum(1 for r in risks if r.severity == "CRITICAL")
        high_count = sum(1 for r in risks if r.severity == "HIGH")
        
        rationale = f"Risk assessment score: {score:.1f}/100. "
        rationale += f"Identified {risk_count} risk factor(s) "
        rationale += f"({critical_count} critical, {high_count} high). "
        rationale += f"Assigned to {tier.value} for "
        
        match tier:
            case RiskTier.TIER_1:
                rationale += "auto-approval (low risk)."
            case RiskTier.TIER_2:
                rationale += "peer review (medium risk)."
            case RiskTier.TIER_3:
                rationale += "Elder approval (high risk)."
        
        return rationale
```

### Step 2: Create Tests (4 hours)

**File:** `tests/test_plan_sanity_check.py`

```python
"""Tests for Sage (Plan Sanity Check AI)."""

import pytest
from unittest.mock import AsyncMock
from uuid import uuid4

from app.services.plan_sanity_check import SageAgent, RiskTier, RiskFactor
from app.services.architect_agent import ExecutionPlanModel, PlanStep


@pytest.fixture
def mock_oracle():
    """Mock Oracle service."""
    oracle = AsyncMock()
    oracle.consult.return_value = '[]'  # No LLM-detected risks
    return oracle


@pytest.fixture
def sage_agent(mock_oracle):
    """Create Sage agent instance."""
    return SageAgent(oracle_service=mock_oracle)


@pytest.fixture
def low_risk_plan():
    """Create low-risk execution plan."""
    return ExecutionPlanModel(
        plan_id=uuid4(),
        request="Add logging to function",
        steps=[
            PlanStep(
                step_number=1,
                action="Add logging statements",
                target_file="app/utils/helpers.py",
                estimated_hours=1.0,
                risk_level="LOW",
            )
        ],
        total_estimated_hours=1.0,
        overall_risk_level="LOW",
    )


@pytest.fixture
def high_risk_plan():
    """Create high-risk execution plan."""
    return ExecutionPlanModel(
        plan_id=uuid4(),
        request="Modify authentication system",
        steps=[
            PlanStep(
                step_number=1,
                action="Update password hashing algorithm",
                target_file="app/core/auth.py",
                estimated_hours=4.0,
                risk_level="CRITICAL",
            )
        ],
        total_estimated_hours=4.0,
        overall_risk_level="CRITICAL",
    )


@pytest.mark.asyncio
async def test_assess_low_risk_plan(sage_agent, low_risk_plan):
    """Test assessment of low-risk plan."""
    assessment = await sage_agent.assess_plan(low_risk_plan)
    
    assert assessment.risk_tier == RiskTier.TIER_1
    assert not assessment.approval_required
    assert assessment.overall_risk_score < 20.0


@pytest.mark.asyncio
async def test_assess_high_risk_plan(sage_agent, high_risk_plan):
    """Test assessment of high-risk plan."""
    assessment = await sage_agent.assess_plan(high_risk_plan)
    
    assert assessment.risk_tier == RiskTier.TIER_3
    assert assessment.approval_required
    assert assessment.overall_risk_score >= 50.0
    assert "security_team" in assessment.recommended_reviewers


@pytest.mark.asyncio
async def test_detect_security_risks(sage_agent):
    """Test detection of security-related risks."""
    plan = ExecutionPlanModel(
        plan_id=uuid4(),
        request="Update token generation",
        steps=[
            PlanStep(
                step_number=1,
                action="Modify JWT token generation",
                estimated_hours=2.0,
                risk_level="HIGH",
            )
        ],
        total_estimated_hours=2.0,
        overall_risk_level="HIGH",
    )
    
    risks = sage_agent._detect_rule_based_risks(plan)
    
    security_risks = [r for r in risks if r.category == "security_vulnerability"]
    assert len(security_risks) > 0
    assert security_risks[0].severity == "CRITICAL"
```

---

## ✅ DEFINITION OF DONE

- [ ] Sage agent service implemented
- [ ] Rule-based risk detection working
- [ ] LLM-based risk analysis functional
- [ ] Risk scoring algorithm validated
- [ ] Tier assignment logic correct
- [ ] All tests passing (>90% coverage)
- [ ] Integration with Path Finder tested
- [ ] Documentation complete

---

## 📊 SUCCESS METRICS

- Risk assessment accuracy: >95%
- False positive rate: <10%
- Assessment time: <10 seconds
- Tier assignment accuracy: >98%
- Test coverage: >90%

---

**Estimated Completion:** 12 hours  
**Assigned To:** Agent Specialist  
**Status:** NOT STARTED

