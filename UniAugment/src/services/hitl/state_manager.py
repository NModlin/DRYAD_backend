"""
Agent State Manager - Manages agent execution states

Handles agent state transitions including:
- IDLE, ACTIVE, PAUSED_FOR_CONSULTATION, ERROR, TERMINATED

Part of Level 3 HITL Service.
"""

from typing import Dict, Any, Optional
from pydantic import BaseModel
from datetime import datetime
from enum import Enum

from app.services.logging.logger import StructuredLogger

logger = StructuredLogger("agent_state_manager")


class AgentState(str, Enum):
    """Agent execution states."""
    IDLE = "idle"
    ACTIVE = "active"
    PAUSED_FOR_CONSULTATION = "paused_for_consultation"
    ERROR = "error"
    TERMINATED = "terminated"


class AgentStateInfo(BaseModel):
    """Agent state information."""
    agent_id: str
    state: AgentState
    task_id: Optional[str] = None
    consultation_id: Optional[str] = None
    metadata: Dict[str, Any] = {}
    updated_at: str


class AgentStateManager:
    """
    Level 3 Component: Agent State Manager
    
    Manages agent execution states and transitions, particularly
    for HITL pausing and resumption.
    """
    
    def __init__(self):
        """Initialize agent state manager."""
        # In-memory state storage (would use Redis in production)
        self._states: Dict[str, AgentStateInfo] = {}
        logger.log_info("agent_state_manager_initialized", {})
    
    async def get_state(self, agent_id: str) -> AgentStateInfo:
        """
        Get current agent state.
        
        Args:
            agent_id: Agent identifier
            
        Returns:
            AgentStateInfo
        """
        if agent_id not in self._states:
            # Default to IDLE if not found
            return AgentStateInfo(
                agent_id=agent_id,
                state=AgentState.IDLE,
                updated_at=datetime.utcnow().isoformat()
            )
        
        return self._states[agent_id]
    
    async def set_state(
        self,
        agent_id: str,
        state: AgentState,
        task_id: Optional[str] = None,
        consultation_id: Optional[str] = None,
        metadata: Dict[str, Any] = None
    ) -> AgentStateInfo:
        """
        Set agent state.
        
        Args:
            agent_id: Agent identifier
            state: New state
            task_id: Optional task ID
            consultation_id: Optional consultation ID
            metadata: Additional metadata
            
        Returns:
            Updated AgentStateInfo
        """
        state_info = AgentStateInfo(
            agent_id=agent_id,
            state=state,
            task_id=task_id,
            consultation_id=consultation_id,
            metadata=metadata or {},
            updated_at=datetime.utcnow().isoformat()
        )
        
        self._states[agent_id] = state_info
        
        logger.log_info(
            "agent_state_changed",
            {
                "agent_id": agent_id,
                "state": state.value,
                "task_id": task_id,
                "consultation_id": consultation_id
            }
        )
        
        return state_info
    
    async def pause_for_consultation(
        self,
        agent_id: str,
        task_id: str,
        consultation_id: str
    ) -> AgentStateInfo:
        """
        Pause agent for human consultation.
        
        Args:
            agent_id: Agent identifier
            task_id: Current task ID
            consultation_id: Consultation request ID
            
        Returns:
            Updated AgentStateInfo
        """
        return await self.set_state(
            agent_id=agent_id,
            state=AgentState.PAUSED_FOR_CONSULTATION,
            task_id=task_id,
            consultation_id=consultation_id,
            metadata={"paused_at": datetime.utcnow().isoformat()}
        )
    
    async def resume_from_consultation(
        self,
        agent_id: str,
        resolution: Dict[str, Any]
    ) -> AgentStateInfo:
        """
        Resume agent after consultation resolved.
        
        Args:
            agent_id: Agent identifier
            resolution: Human resolution/guidance
            
        Returns:
            Updated AgentStateInfo
        """
        current_state = await self.get_state(agent_id)
        
        return await self.set_state(
            agent_id=agent_id,
            state=AgentState.ACTIVE,
            task_id=current_state.task_id,
            metadata={
                "resumed_at": datetime.utcnow().isoformat(),
                "resolution": resolution
            }
        )
    
    async def is_paused(self, agent_id: str) -> bool:
        """Check if agent is paused for consultation."""
        state = await self.get_state(agent_id)
        return state.state == AgentState.PAUSED_FOR_CONSULTATION
    
    async def get_all_paused_agents(self) -> list[AgentStateInfo]:
        """Get all agents currently paused for consultation."""
        return [
            state for state in self._states.values()
            if state.state == AgentState.PAUSED_FOR_CONSULTATION
        ]
    
    async def clear_state(self, agent_id: str):
        """Clear agent state (set to IDLE)."""
        await self.set_state(agent_id, AgentState.IDLE)

