# app/api/v1/schemas/multi_agent.py
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from enum import Enum

class WorkflowType(str, Enum):
    """Available workflow types for multi-agent processing."""
    SIMPLE_RESEARCH = "simple_research"
    RESEARCH_ANALYZE_WRITE = "research_analyze_write"
    COMPLEX_ANALYSIS = "complex_analysis"
    COLLABORATIVE_WRITING = "collaborative_writing"

class AgentType(str, Enum):
    """Available agent types."""
    RESEARCHER = "researcher"
    ANALYST = "analyst"
    WRITER = "writer"
    COORDINATOR = "coordinator"

class MultiAgentRequest(BaseModel):
    """Schema for multi-agent workflow requests."""
    input: str = Field(..., description="The query or task to be processed")
    workflow_type: WorkflowType = Field(
        default=WorkflowType.SIMPLE_RESEARCH,
        description="Type of workflow to execute"
    )
    conversation_id: Optional[str] = Field(
        None, 
        description="ID of existing conversation for context"
    )
    save_conversation: bool = Field(
        True, 
        description="Whether to save this interaction to conversation history"
    )
    preferred_agents: Optional[List[AgentType]] = Field(
        None,
        description="Specific agents to use (if not specified, system will choose)"
    )
    context_depth: int = Field(
        default=10,
        ge=1,
        le=50,
        description="Number of previous messages to include as context"
    )
    metadata: Optional[Dict[str, Any]] = Field(
        None,
        description="Additional metadata for the request"
    )

class MultiAgentResponse(BaseModel):
    """Schema for multi-agent workflow responses."""
    result: str = Field(..., description="The result of the multi-agent workflow as a string")
    conversation_id: str = Field(..., description="ID of the conversation")
    workflow_type: str = Field(..., description="Type of workflow that was executed")
    agents_used: List[str] = Field(..., description="List of agents that participated")
    workflow_steps: int = Field(..., description="Number of steps in the workflow")
    execution_time: Optional[float] = Field(None, description="Execution time in seconds")
    context_used: bool = Field(..., description="Whether conversation context was used")
    message_ids: List[str] = Field(default=[], description="IDs of messages created during execution")

class AgentCapabilitiesResponse(BaseModel):
    """Schema for agent capabilities information."""
    agents: Dict[str, Dict[str, str]] = Field(..., description="Available agents and their capabilities")
    workflows: Dict[str, str] = Field(..., description="Available workflows and their descriptions")
    total_agents: int = Field(..., description="Total number of available agents")

class AgentMemoryRequest(BaseModel):
    """Schema for agent memory and context requests."""
    conversation_id: str = Field(..., description="ID of the conversation")
    agent_name: Optional[str] = Field(None, description="Specific agent to get context for")
    task_type: Optional[str] = Field(None, description="Specific task type to filter by")
    max_interactions: int = Field(
        default=10,
        ge=1,
        le=100,
        description="Maximum number of interactions to retrieve"
    )

class AgentMemoryResponse(BaseModel):
    """Schema for agent memory and context responses."""
    conversation_id: str = Field(..., description="ID of the conversation")
    agent_context: List[Dict[str, Any]] = Field(..., description="Agent interaction history")
    total_interactions: int = Field(..., description="Total number of interactions found")
    agents_involved: List[str] = Field(..., description="List of agents that have interacted")

class ConversationSummaryResponse(BaseModel):
    """Schema for conversation summary responses."""
    conversation_id: str = Field(..., description="ID of the conversation")
    title: str = Field(..., description="Title of the conversation")
    created_at: str = Field(..., description="When the conversation was created")
    updated_at: str = Field(..., description="When the conversation was last updated")
    total_messages: int = Field(..., description="Total number of messages")
    user_messages: int = Field(..., description="Number of user messages")
    assistant_messages: int = Field(..., description="Number of assistant messages")
    agent_interactions: int = Field(..., description="Number of agent interactions")
    agents_used: List[str] = Field(..., description="List of agents that have been used")
    task_types: List[str] = Field(..., description="List of task types that have been completed")

class AgentPerformanceResponse(BaseModel):
    """Schema for agent performance metrics."""
    agent_name: str = Field(..., description="Name of the agent")
    period_days: int = Field(..., description="Number of days the metrics cover")
    total_tasks: int = Field(..., description="Total number of tasks completed")
    successful_tasks: int = Field(..., description="Number of successful tasks")
    average_response_time: float = Field(..., description="Average response time in seconds")
    error_rate: float = Field(..., description="Error rate as a percentage")
    note: Optional[str] = Field(None, description="Additional notes about the metrics")

# Backward compatibility schemas
class LegacyAgentRequest(BaseModel):
    """Legacy schema for backward compatibility with Phase 1/2."""
    input: str = Field(..., description="User input/query")
    conversation_id: Optional[str] = Field(None, description="ID of existing conversation")
    save_conversation: bool = Field(True, description="Whether to save this interaction")

class LegacyAgentResponse(BaseModel):
    """Legacy schema for backward compatibility with Phase 1/2."""
    output: Dict[str, Any] = Field(..., description="Agent response")
    conversation_id: str = Field(..., description="ID of the conversation")
    message_id: str = Field(..., description="ID of the response message")
    context_used: bool = Field(..., description="Whether conversation context was used")
