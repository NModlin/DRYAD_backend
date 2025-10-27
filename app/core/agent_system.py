# app/core/agent_system.py
"""
Agent System for managing AI agents and their interactions.
Provides a unified interface for different types of agents and their capabilities.
"""

import logging
import asyncio
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
from enum import Enum

from app.core.agent import agent_graph_app
from app.core.multi_agent import multi_agent_orchestrator
from app.core.exceptions import DRYADAIException, ErrorCode

logger = logging.getLogger(__name__)


class AgentType(str, Enum):
    """Types of available agents."""
    SIMPLE = "simple"
    MULTI_AGENT = "multi_agent"
    RAG = "rag"
    RESEARCH = "research"
    ANALYSIS = "analysis"
    CREATIVE = "creative"


class AgentStatus(str, Enum):
    """Agent execution status."""
    IDLE = "idle"
    PROCESSING = "processing"
    COMPLETED = "completed"
    ERROR = "error"
    TIMEOUT = "timeout"


class AgentTask:
    """Represents a task for an agent to execute."""
    
    def __init__(self, task_id: str, agent_type: AgentType, query: str, 
                 context: Optional[Dict[str, Any]] = None, timeout: int = 300):
        self.task_id = task_id
        self.agent_type = agent_type
        self.query = query
        self.context = context or {}
        self.timeout = timeout
        self.status = AgentStatus.IDLE
        self.result: Optional[Dict[str, Any]] = None
        self.error: Optional[str] = None
        self.created_at = datetime.utcnow()
        self.started_at: Optional[datetime] = None
        self.completed_at: Optional[datetime] = None


class AgentSystem:
    """
    Central agent system for managing different types of AI agents.
    Provides a unified interface for agent execution and monitoring.
    """
    
    def __init__(self):
        self.active_tasks: Dict[str, AgentTask] = {}
        self.task_history: List[AgentTask] = []
        self.max_concurrent_tasks = 10
        self.max_history_size = 1000
    
    async def execute_agent_task(self, task: AgentTask) -> Dict[str, Any]:
        """Execute an agent task and return the result."""
        if len(self.active_tasks) >= self.max_concurrent_tasks:
            raise DRYADAIException(
                ErrorCode.RATE_LIMIT_EXCEEDED,
                "Maximum concurrent agent tasks reached"
            )
        
        self.active_tasks[task.task_id] = task
        task.status = AgentStatus.PROCESSING
        task.started_at = datetime.utcnow()
        
        try:
            logger.info(f"Starting agent task {task.task_id} with type {task.agent_type}")
            
            # Execute based on agent type
            if task.agent_type == AgentType.SIMPLE:
                result = await self._execute_simple_agent(task)
            elif task.agent_type == AgentType.MULTI_AGENT:
                result = await self._execute_multi_agent(task)
            elif task.agent_type == AgentType.RAG:
                result = await self._execute_rag_agent(task)
            else:
                # Default to simple agent
                result = await self._execute_simple_agent(task)
            
            task.result = result
            task.status = AgentStatus.COMPLETED
            task.completed_at = datetime.utcnow()
            
            logger.info(f"Completed agent task {task.task_id}")
            return result
            
        except asyncio.TimeoutError:
            task.status = AgentStatus.TIMEOUT
            task.error = f"Task timed out after {task.timeout} seconds"
            logger.error(f"Agent task {task.task_id} timed out")
            raise DRYADAIException(ErrorCode.TIMEOUT, task.error)
            
        except Exception as e:
            task.status = AgentStatus.ERROR
            task.error = str(e)
            logger.error(f"Agent task {task.task_id} failed: {e}")
            raise DRYADAIException(ErrorCode.AGENT_EXECUTION_FAILED, str(e))
            
        finally:
            # Move to history and clean up
            self.active_tasks.pop(task.task_id, None)
            self._add_to_history(task)
    
    async def _execute_simple_agent(self, task: AgentTask) -> Dict[str, Any]:
        """Execute a simple agent task."""
        try:
            # Use the existing agent system
            result = await asyncio.wait_for(
                asyncio.to_thread(agent_graph_app.invoke, {"input": task.query}),
                timeout=task.timeout
            )
            
            return {
                "task_id": task.task_id,
                "agent_type": task.agent_type.value,
                "query": task.query,
                "result": result.get("output", "No output generated"),
                "execution_time": (datetime.utcnow() - task.started_at).total_seconds(),
                "status": "completed"
            }
        except Exception as e:
            logger.error(f"Simple agent execution failed: {e}")
            raise
    
    async def _execute_multi_agent(self, task: AgentTask) -> Dict[str, Any]:
        """Execute a multi-agent task."""
        try:
            # Use the multi-agent orchestrator
            result = await asyncio.wait_for(
                asyncio.to_thread(
                    multi_agent_orchestrator.execute_complex_workflow,
                    "research_analyze_write",
                    task.query,
                    task.context
                ),
                timeout=task.timeout
            )
            
            return {
                "task_id": task.task_id,
                "agent_type": task.agent_type.value,
                "query": task.query,
                "result": result,
                "execution_time": (datetime.utcnow() - task.started_at).total_seconds(),
                "status": "completed"
            }
        except Exception as e:
            logger.error(f"Multi-agent execution failed: {e}")
            # Fallback to simple execution
            return await self._execute_simple_agent(task)
    
    async def _execute_rag_agent(self, task: AgentTask) -> Dict[str, Any]:
        """Execute a RAG-enhanced agent task."""
        try:
            from app.core.rag_system import rag_system
            
            # Use RAG system for enhanced responses
            result = await asyncio.wait_for(
                rag_system.query_with_rag(task.query, task.context),
                timeout=task.timeout
            )
            
            return {
                "task_id": task.task_id,
                "agent_type": task.agent_type.value,
                "query": task.query,
                "result": result,
                "execution_time": (datetime.utcnow() - task.started_at).total_seconds(),
                "status": "completed"
            }
        except Exception as e:
            logger.error(f"RAG agent execution failed: {e}")
            # Fallback to simple execution
            return await self._execute_simple_agent(task)
    
    def _add_to_history(self, task: AgentTask):
        """Add completed task to history."""
        self.task_history.append(task)
        
        # Maintain history size limit
        if len(self.task_history) > self.max_history_size:
            self.task_history = self.task_history[-self.max_history_size:]
    
    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get the status of a specific task."""
        # Check active tasks first
        if task_id in self.active_tasks:
            task = self.active_tasks[task_id]
            return self._task_to_dict(task)
        
        # Check history
        for task in reversed(self.task_history):
            if task.task_id == task_id:
                return self._task_to_dict(task)
        
        return None
    
    def _task_to_dict(self, task: AgentTask) -> Dict[str, Any]:
        """Convert task to dictionary representation."""
        return {
            "task_id": task.task_id,
            "agent_type": task.agent_type.value,
            "status": task.status.value,
            "query": task.query,
            "result": task.result,
            "error": task.error,
            "created_at": task.created_at.isoformat(),
            "started_at": task.started_at.isoformat() if task.started_at else None,
            "completed_at": task.completed_at.isoformat() if task.completed_at else None,
            "execution_time": (
                (task.completed_at - task.started_at).total_seconds() 
                if task.completed_at and task.started_at else None
            )
        }
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get overall system status."""
        return {
            "active_tasks": len(self.active_tasks),
            "max_concurrent_tasks": self.max_concurrent_tasks,
            "total_tasks_in_history": len(self.task_history),
            "available_agent_types": [agent_type.value for agent_type in AgentType],
            "system_health": "operational" if len(self.active_tasks) < self.max_concurrent_tasks else "at_capacity"
        }
    
    def cancel_task(self, task_id: str) -> bool:
        """Cancel an active task."""
        if task_id in self.active_tasks:
            task = self.active_tasks[task_id]
            task.status = AgentStatus.ERROR
            task.error = "Task cancelled by user"
            task.completed_at = datetime.utcnow()
            
            # Move to history
            self.active_tasks.pop(task_id)
            self._add_to_history(task)
            
            logger.info(f"Cancelled task {task_id}")
            return True
        
        return False


# Global agent system instance
agent_system = AgentSystem()


# Convenience functions for backward compatibility
async def execute_agent(query: str, agent_type: str = "simple", 
                       context: Optional[Dict[str, Any]] = None,
                       task_id: Optional[str] = None) -> Dict[str, Any]:
    """Execute an agent task with the specified parameters."""
    import uuid
    
    if not task_id:
        task_id = str(uuid.uuid4())
    
    try:
        agent_type_enum = AgentType(agent_type)
    except ValueError:
        agent_type_enum = AgentType.SIMPLE
    
    task = AgentTask(task_id, agent_type_enum, query, context)
    return await agent_system.execute_agent_task(task)


def get_agent_capabilities() -> Dict[str, Any]:
    """Get information about available agent capabilities."""
    return {
        "available_agents": [
            {
                "type": AgentType.SIMPLE.value,
                "description": "Basic AI agent for simple queries and responses",
                "capabilities": ["text_generation", "question_answering", "web_search"]
            },
            {
                "type": AgentType.MULTI_AGENT.value,
                "description": "Multi-agent system for complex reasoning and collaboration",
                "capabilities": ["research", "analysis", "writing", "collaboration"]
            },
            {
                "type": AgentType.RAG.value,
                "description": "RAG-enhanced agent with document retrieval capabilities",
                "capabilities": ["document_search", "context_aware_responses", "knowledge_retrieval"]
            }
        ],
        "system_status": agent_system.get_system_status()
    }
