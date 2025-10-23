# Task 3-09: Interactive HITL Consultation Implementation

**Phase:** 3 - Advanced Collaboration & Governance  
**Week:** 15  
**Estimated Hours:** 8 hours  
**Priority:** HIGH  
**Dependencies:** Task 3-06 (Elder Approval)

---

## 🎯 OBJECTIVE

Implement Interactive Human-in-the-Loop (HITL) Consultation system enabling real-time dialogue between humans and paused agents during review. Allows humans to ask clarifying questions and agents to respond before final approval decision.

---

## 📋 REQUIREMENTS

### Functional Requirements
- Enable real-time chat between human and agent
- Pause agent execution for consultation
- Resume agent after consultation
- Track consultation history
- Support multi-turn conversations
- Provide conversation context to agent

### Technical Requirements
- WebSocket for real-time communication
- Agent state persistence during pause
- Conversation history storage
- Async message handling
- Comprehensive logging

### Performance Requirements
- Message delivery: <500ms
- Agent response time: <10 seconds
- Conversation history retrieval: <1 second

---

## 🔧 IMPLEMENTATION STEPS

### Step 1: Create HITL Consultation Service (6 hours)

**File:** `app/services/hitl_consultation.py`

```python
"""
Interactive HITL Consultation - Real-time Human-Agent Dialogue
Enables consultation during agent execution pause.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field
from structlog import get_logger

from app.core.oracle import OracleService

logger = get_logger(__name__)


class MessageRole(str, Enum):
    """Message role in consultation."""
    
    HUMAN = "HUMAN"
    AGENT = "AGENT"
    SYSTEM = "SYSTEM"


class ConsultationMessage(BaseModel):
    """Message in HITL consultation."""
    
    message_id: UUID = Field(default_factory=uuid4)
    consultation_id: UUID
    role: MessageRole
    content: str
    metadata: dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ConsultationSession(BaseModel):
    """HITL consultation session."""
    
    consultation_id: UUID = Field(default_factory=uuid4)
    workflow_id: UUID
    agent_id: str
    agent_name: str
    context: dict[str, Any] = Field(default_factory=dict)
    messages: list[ConsultationMessage] = Field(default_factory=list)
    status: str = "ACTIVE"  # ACTIVE, COMPLETED, CANCELLED
    started_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: datetime | None = None


class HITLConsultationService:
    """
    HITL Consultation Service
    
    Manages real-time dialogue between humans and agents
    during execution pause.
    """
    
    def __init__(self, oracle_service: OracleService) -> None:
        self.oracle = oracle_service
        self.logger = logger.bind(service="hitl_consultation")
        
        # Active consultation sessions
        self._sessions: dict[UUID, ConsultationSession] = {}
    
    async def start_consultation(
        self,
        workflow_id: UUID,
        agent_id: str,
        agent_name: str,
        context: dict[str, Any],
    ) -> UUID:
        """
        Start new consultation session.
        
        Args:
            workflow_id: Associated workflow ID
            agent_id: Agent identifier
            agent_name: Agent name
            context: Execution context for agent
            
        Returns:
            Consultation ID
        """
        consultation_id = uuid4()
        
        self.logger.info(
            "starting_consultation",
            consultation_id=str(consultation_id),
            workflow_id=str(workflow_id),
            agent=agent_name,
        )
        
        session = ConsultationSession(
            consultation_id=consultation_id,
            workflow_id=workflow_id,
            agent_id=agent_id,
            agent_name=agent_name,
            context=context,
        )
        
        # Add system message
        system_msg = ConsultationMessage(
            consultation_id=consultation_id,
            role=MessageRole.SYSTEM,
            content=f"Consultation started with {agent_name}. Ask questions to clarify the execution plan.",
        )
        session.messages.append(system_msg)
        
        self._sessions[consultation_id] = session
        
        return consultation_id
    
    async def send_human_message(
        self,
        consultation_id: UUID,
        message: str,
    ) -> ConsultationMessage:
        """
        Send message from human to agent.
        
        Args:
            consultation_id: Consultation session ID
            message: Human message
            
        Returns:
            Created message
            
        Raises:
            ValueError: If consultation not found or not active
        """
        session = self._sessions.get(consultation_id)
        if not session:
            raise ValueError(f"Consultation not found: {consultation_id}")
        
        if session.status != "ACTIVE":
            raise ValueError(f"Consultation not active: {session.status}")
        
        self.logger.info(
            "human_message_received",
            consultation_id=str(consultation_id),
            message=message[:100],
        )
        
        # Create human message
        human_msg = ConsultationMessage(
            consultation_id=consultation_id,
            role=MessageRole.HUMAN,
            content=message,
        )
        session.messages.append(human_msg)
        
        # Generate agent response
        agent_response = await self._generate_agent_response(session, message)
        
        # Create agent message
        agent_msg = ConsultationMessage(
            consultation_id=consultation_id,
            role=MessageRole.AGENT,
            content=agent_response,
        )
        session.messages.append(agent_msg)
        
        return agent_msg
    
    async def _generate_agent_response(
        self,
        session: ConsultationSession,
        human_message: str,
    ) -> str:
        """Generate agent response to human question."""
        
        # Build conversation history
        conversation_history = "\n".join([
            f"{msg.role.value}: {msg.content}"
            for msg in session.messages[-10:]  # Last 10 messages
        ])
        
        # Build context summary
        context_summary = self._summarize_context(session.context)
        
        prompt = f"""You are {session.agent_name}, an AI agent currently paused for human consultation.

EXECUTION CONTEXT:
{context_summary}

CONVERSATION HISTORY:
{conversation_history}

HUMAN QUESTION:
{human_message}

Provide a clear, helpful response to the human's question. Be specific about your planned actions and reasoning.
"""
        
        response = await self.oracle.consult(
            prompt=prompt,
            model_tier="reasoning",
            temperature=0.7,
            max_tokens=1000,
        )
        
        return response
    
    def _summarize_context(self, context: dict[str, Any]) -> str:
        """Create human-readable context summary."""
        summary_parts = []
        
        if "plan" in context:
            plan = context["plan"]
            summary_parts.append(f"Plan: {plan.get('request', 'N/A')}")
            summary_parts.append(f"Steps: {len(plan.get('steps', []))}")
        
        if "risk_assessment" in context:
            assessment = context["risk_assessment"]
            summary_parts.append(f"Risk Tier: {assessment.get('risk_tier', 'N/A')}")
            summary_parts.append(f"Risk Score: {assessment.get('risk_score', 0):.1f}")
        
        return "\n".join(summary_parts)
    
    async def end_consultation(
        self,
        consultation_id: UUID,
        outcome: str = "COMPLETED",
    ) -> ConsultationSession:
        """
        End consultation session.
        
        Args:
            consultation_id: Consultation session ID
            outcome: Consultation outcome (COMPLETED, CANCELLED)
            
        Returns:
            Final session state
            
        Raises:
            ValueError: If consultation not found
        """
        session = self._sessions.get(consultation_id)
        if not session:
            raise ValueError(f"Consultation not found: {consultation_id}")
        
        self.logger.info(
            "ending_consultation",
            consultation_id=str(consultation_id),
            outcome=outcome,
            message_count=len(session.messages),
        )
        
        session.status = outcome
        session.completed_at = datetime.utcnow()
        
        # Add system message
        system_msg = ConsultationMessage(
            consultation_id=consultation_id,
            role=MessageRole.SYSTEM,
            content=f"Consultation {outcome.lower()}.",
        )
        session.messages.append(system_msg)
        
        return session
    
    def get_session(self, consultation_id: UUID) -> ConsultationSession | None:
        """Get consultation session."""
        return self._sessions.get(consultation_id)
    
    def get_active_sessions(self) -> list[ConsultationSession]:
        """Get all active consultation sessions."""
        return [
            session
            for session in self._sessions.values()
            if session.status == "ACTIVE"
        ]
```

### Step 2: Create WebSocket Endpoint (2 hours)

**File:** `app/api/websocket_consultation.py`

```python
"""WebSocket endpoint for real-time HITL consultation."""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from uuid import UUID
from structlog import get_logger

from app.services.hitl_consultation import HITLConsultationService

logger = get_logger(__name__)

router = APIRouter()


@router.websocket("/ws/consultation/{consultation_id}")
async def consultation_websocket(
    websocket: WebSocket,
    consultation_id: UUID,
    hitl_service: HITLConsultationService,
) -> None:
    """
    WebSocket endpoint for real-time consultation.
    
    Args:
        websocket: WebSocket connection
        consultation_id: Consultation session ID
        hitl_service: HITL consultation service
    """
    await websocket.accept()
    
    logger.info(
        "websocket_connected",
        consultation_id=str(consultation_id),
    )
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_json()
            
            message = data.get("message", "")
            
            if not message:
                continue
            
            # Send to agent and get response
            agent_msg = await hitl_service.send_human_message(
                consultation_id=consultation_id,
                message=message,
            )
            
            # Send agent response back to client
            await websocket.send_json({
                "message_id": str(agent_msg.message_id),
                "role": agent_msg.role.value,
                "content": agent_msg.content,
                "timestamp": agent_msg.timestamp.isoformat(),
            })
            
    except WebSocketDisconnect:
        logger.info(
            "websocket_disconnected",
            consultation_id=str(consultation_id),
        )
    except Exception as e:
        logger.error(
            "websocket_error",
            consultation_id=str(consultation_id),
            error=str(e),
        )
        await websocket.close()
```

---

## ✅ DEFINITION OF DONE

- [ ] HITL consultation service implemented
- [ ] WebSocket endpoint functional
- [ ] Real-time messaging working
- [ ] Conversation history tracked
- [ ] All tests passing (>80% coverage)
- [ ] Documentation complete

---

## 📊 SUCCESS METRICS

- Message delivery latency: <500ms
- Agent response time: <10 seconds
- Conversation tracking: 100%
- Test coverage: >80%

---

**Estimated Completion:** 8 hours  
**Assigned To:** Backend Developer  
**Status:** NOT STARTED

