# G.A.D System Design (Governance & Decision)

**Version**: 1.0.0  
**Status**: Design Phase  
**Purpose**: Human-in-the-Loop governance and decision-making system

---

## System Overview

The G.A.D (Governance & Decision) System provides:
- Decision queue management
- Human-in-the-Loop (HITL) workflows
- Policy enforcement
- Audit logging
- Compliance tracking

---

## Architecture

```
┌─────────────────────────────────────────────────────┐
│         G.A.D System (Level 3 Integration)          │
│  ┌──────────────────────────────────────────────┐  │
│  │ Decision Queue Manager                       │  │
│  │ - Queue management                           │  │
│  │ - Priority scoring                           │  │
│  │ - Timeout handling                           │  │
│  │ - Escalation                                 │  │
│  └──────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────┐  │
│  │ HITL Workflow Engine                         │  │
│  │ - Workflow definition                        │  │
│  │ - Task assignment                            │  │
│  │ - Approval routing                           │  │
│  │ - Feedback collection                        │  │
│  └──────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────┐  │
│  │ Policy Engine                                │  │
│  │ - Policy definition                          │  │
│  │ - Policy evaluation                          │  │
│  │ - Enforcement                                │  │
│  │ - Violation handling                         │  │
│  └──────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────┐  │
│  │ Audit & Compliance                           │  │
│  │ - Decision logging                           │  │
│  │ - Audit trail                                │  │
│  │ - Compliance reporting                       │  │
│  │ - Forensics                                  │  │
│  └──────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────┐
│ DRYAD Level 3 (Orchestration & HITL)                │
│ - Task routing                                      │
│ - Human feedback                                    │
│ - Decision execution                                │
└─────────────────────────────────────────────────────┘
```

---

## Core Components

### 1. Decision Queue Manager

```python
class Decision:
    decision_id: str
    type: str  # "agent_creation", "competition_start", "resource_allocation"
    status: str  # "pending", "approved", "rejected", "escalated"
    
    # Context
    context: Dict[str, Any]
    created_at: datetime
    
    # Priority
    priority: int  # 1-10
    urgency: str  # "low", "medium", "high", "critical"
    
    # HITL
    assigned_to: Optional[str]  # User ID
    assigned_at: Optional[datetime]
    
    # Review
    reviewed_at: Optional[datetime]
    reviewed_by: Optional[str]
    approved: Optional[bool]
    feedback: Optional[str]
    
    # Execution
    executed_at: Optional[datetime]
    execution_result: Optional[Dict[str, Any]]
    
    # Audit
    audit_log: List[AuditEntry]

class DecisionQueue:
    def add_decision(self, decision: Decision) -> str:
        """Add decision to queue"""
        
    def get_pending_decisions(self, user_id: str) -> List[Decision]:
        """Get decisions assigned to user"""
        
    def approve_decision(
        self,
        decision_id: str,
        user_id: str,
        feedback: str
    ) -> Decision:
        """Approve a decision"""
        
    def reject_decision(
        self,
        decision_id: str,
        user_id: str,
        reason: str
    ) -> Decision:
        """Reject a decision"""
        
    def escalate_decision(
        self,
        decision_id: str,
        reason: str
    ) -> Decision:
        """Escalate decision to higher authority"""
```

### 2. HITL Workflow Engine

```python
class HITLWorkflow:
    workflow_id: str
    name: str
    description: str
    
    # Workflow definition
    steps: List[WorkflowStep]
    approval_chain: List[str]  # User IDs in order
    
    # Configuration
    timeout_minutes: int
    escalation_enabled: bool
    parallel_approval: bool
    
    # Status
    status: str  # "active", "paused", "archived"

class WorkflowStep:
    step_id: str
    name: str
    description: str
    
    # Execution
    action: Callable
    condition: Optional[Callable]
    
    # Approval
    requires_approval: bool
    approver_role: Optional[str]
    
    # Timeout
    timeout_minutes: int
    on_timeout: str  # "escalate", "auto_approve", "auto_reject"

# Example workflow
agent_creation_workflow = HITLWorkflow(
    workflow_id="agent_creation_v1",
    name="Agent Creation Approval",
    steps=[
        WorkflowStep(
            step_id="validation",
            name="Validate Agent Configuration",
            action=validate_agent_config,
            requires_approval=False
        ),
        WorkflowStep(
            step_id="review",
            name="Review by Curator",
            action=None,
            requires_approval=True,
            approver_role="curator",
            timeout_minutes=60
        ),
        WorkflowStep(
            step_id="create",
            name="Create Agent",
            action=create_agent,
            requires_approval=False
        )
    ],
    approval_chain=["curator", "admin"],
    timeout_minutes=120
)
```

### 3. Policy Engine

```python
class Policy:
    policy_id: str
    name: str
    description: str
    
    # Definition
    rules: List[PolicyRule]
    conditions: List[PolicyCondition]
    
    # Enforcement
    enforcement_level: str  # "strict", "moderate", "advisory"
    on_violation: str  # "block", "warn", "log"
    
    # Lifecycle
    created_at: datetime
    effective_date: datetime
    expiration_date: Optional[datetime]
    status: str  # "active", "inactive", "archived"

class PolicyRule:
    rule_id: str
    name: str
    
    # Condition
    condition: Callable  # Returns bool
    
    # Action
    action: str  # "allow", "deny", "require_approval"
    
    # Metadata
    priority: int
    description: str

# Example policies
policies = [
    Policy(
        policy_id="max_agents_per_user",
        name="Maximum Agents Per User",
        rules=[
            PolicyRule(
                rule_id="rule_1",
                name="Limit to 100 agents",
                condition=lambda user: len(user.agents) < 100,
                action="allow"
            )
        ],
        enforcement_level="strict"
    ),
    Policy(
        policy_id="resource_quota",
        name="Resource Quota Enforcement",
        rules=[
            PolicyRule(
                rule_id="rule_1",
                name="CPU limit",
                condition=lambda agent: agent.cpu_usage < 80,
                action="allow"
            ),
            PolicyRule(
                rule_id="rule_2",
                name="Memory limit",
                condition=lambda agent: agent.memory_usage < 90,
                action="allow"
            )
        ],
        enforcement_level="strict"
    )
]
```

### 4. Audit & Compliance

```python
class AuditEntry:
    entry_id: str
    timestamp: datetime
    
    # Actor
    actor_id: str
    actor_type: str  # "user", "system", "agent"
    
    # Action
    action: str
    resource_type: str
    resource_id: str
    
    # Details
    details: Dict[str, Any]
    
    # Result
    result: str  # "success", "failure"
    error_message: Optional[str]

class ComplianceReport:
    report_id: str
    period: Tuple[datetime, datetime]
    
    # Metrics
    total_decisions: int
    approved_decisions: int
    rejected_decisions: int
    escalated_decisions: int
    
    # Policy violations
    policy_violations: int
    violation_details: List[Dict[str, Any]]
    
    # Audit trail
    audit_entries: List[AuditEntry]
    
    # Recommendations
    recommendations: List[str]
```

---

## Decision Types

### Type 1: Agent Creation
```python
class AgentCreationDecision(Decision):
    type = "agent_creation"
    context = {
        "agent_name": str,
        "creator_id": str,
        "specialization": str,
        "tools": List[str],
        "estimated_resources": Dict[str, Any]
    }
    
    # Approval criteria
    requires_approval = True
    approver_role = "curator"
```

### Type 2: Competition Start
```python
class CompetitionStartDecision(Decision):
    type = "competition_start"
    context = {
        "competition_id": str,
        "participants": List[str],
        "estimated_duration": int,
        "resource_requirements": Dict[str, Any]
    }
    
    requires_approval = False  # Auto-approved if resources available
```

### Type 3: Resource Allocation
```python
class ResourceAllocationDecision(Decision):
    type = "resource_allocation"
    context = {
        "university_id": str,
        "resource_type": str,
        "amount": int,
        "justification": str
    }
    
    requires_approval = True
    approver_role = "admin"
```

---

## HITL Dashboard

### Decision Queue View
- Pending decisions
- Priority indicators
- Context information
- Approve/Reject buttons
- Feedback form

### Policy Management
- View active policies
- Create new policies
- Edit policies
- Policy history
- Violation reports

### Audit Log
- All decisions made
- Who made them
- When they were made
- Feedback provided
- Compliance metrics

---

## API Endpoints

```
# Decision Management
GET    /api/v1/decisions                 # List decisions
GET    /api/v1/decisions/{id}            # Get decision
POST   /api/v1/decisions                 # Create decision
PATCH  /api/v1/decisions/{id}/approve    # Approve decision
PATCH  /api/v1/decisions/{id}/reject     # Reject decision
PATCH  /api/v1/decisions/{id}/escalate   # Escalate decision

# Workflow Management
GET    /api/v1/workflows                 # List workflows
POST   /api/v1/workflows                 # Create workflow
PATCH  /api/v1/workflows/{id}            # Update workflow

# Policy Management
GET    /api/v1/policies                  # List policies
POST   /api/v1/policies                  # Create policy
PATCH  /api/v1/policies/{id}             # Update policy
DELETE /api/v1/policies/{id}             # Delete policy

# Audit & Compliance
GET    /api/v1/audit/log                 # Get audit log
GET    /api/v1/compliance/report         # Get compliance report
GET    /api/v1/compliance/violations     # Get violations
```

---

## Integration with DRYAD Level 3

The G.A.D system integrates with DRYAD's Level 3 (Orchestration & HITL):
- Decision queue feeds into Level 3 task routing
- HITL workflows use Level 3 human feedback mechanisms
- Audit logging integrates with Level 3 logging system
- Policy enforcement uses Level 3 decision engine

---

## Implementation Phases

**Phase 1**: Decision queue and basic HITL  
**Phase 2**: Policy engine  
**Phase 3**: Audit and compliance  
**Phase 4**: Advanced workflows  
**Phase 5**: Analytics and reporting  

**Status**: Ready for implementation

