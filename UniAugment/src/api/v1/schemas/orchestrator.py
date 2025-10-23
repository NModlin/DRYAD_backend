"""
Pydantic schemas for orchestrator API endpoints in Phase 5.
"""

from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional, Union
from enum import Enum

class TaskTypeEnum(str, Enum):
    """Enumeration of available task types."""
    AGENT_CHAT = "agent_chat"
    MULTI_AGENT_WORKFLOW = "multi_agent_workflow"
    DOCUMENT_SEARCH = "document_search"
    RAG_QUERY = "rag_query"
    DOCUMENT_PROCESSING = "document_processing"
    SYSTEM_ANALYSIS = "system_analysis"
    COMPREHENSIVE_WORKFLOW = "comprehensive_workflow"
    HEALTH_CHECK = "health_check"
    DATA_CLEANUP = "data_cleanup"

class ExecutionModeEnum(str, Enum):
    """Enumeration of execution modes."""
    SYNCHRONOUS = "sync"
    ASYNCHRONOUS = "async"

class TaskRequest(BaseModel):
    """Schema for task execution requests."""
    task_type: TaskTypeEnum = Field(..., description="Type of task to execute")
    payload: Dict[str, Any] = Field(..., description="Task payload with parameters")
    execution_mode: ExecutionModeEnum = Field(
        ExecutionModeEnum.SYNCHRONOUS, 
        description="Execution mode (sync or async)"
    )
    priority: int = Field(1, ge=1, le=10, description="Task priority (1-10)")
    timeout: Optional[int] = Field(None, description="Task timeout in seconds")

class TaskResponse(BaseModel):
    """Schema for task execution responses."""
    task_id: Optional[str] = Field(None, description="Task ID for async tasks")
    status: str = Field(..., description="Task execution status")
    result: Optional[Dict[str, Any]] = Field(None, description="Task execution result")
    execution_time: float = Field(..., description="Task execution time in seconds")
    error: Optional[str] = Field(None, description="Error message if task failed")

class TaskStatusResponse(BaseModel):
    """Schema for task status responses."""
    task_id: str = Field(..., description="Task ID")
    status: str = Field(..., description="Current task status")
    result: Optional[Dict[str, Any]] = Field(None, description="Task result if completed")
    info: Optional[Dict[str, Any]] = Field(None, description="Additional task information")
    ready: bool = Field(..., description="Whether task is ready/completed")
    successful: Optional[bool] = Field(None, description="Whether task was successful")
    failed: Optional[bool] = Field(None, description="Whether task failed")
    error: Optional[str] = Field(None, description="Error message if task failed")

class OrchestratorCapabilities(BaseModel):
    """Schema for orchestrator capabilities."""
    supported_tasks: List[str] = Field(..., description="List of supported task types")
    execution_modes: List[str] = Field(..., description="List of supported execution modes")
    features: Dict[str, bool] = Field(..., description="Available features")
    version: str = Field(..., description="Orchestrator version")

class WorkflowStep(BaseModel):
    """Schema for workflow step configuration."""
    type: str = Field(..., description="Step type")
    config: Dict[str, Any] = Field(default_factory=dict, description="Step configuration")

class WorkflowRequest(BaseModel):
    """Schema for comprehensive workflow requests."""
    name: str = Field(..., description="Workflow name")
    input: str = Field(..., description="Initial workflow input")
    steps: List[WorkflowStep] = Field(..., description="Workflow steps to execute")
    conversation_id: Optional[str] = Field(None, description="Optional conversation ID")
    save_conversation: bool = Field(True, description="Whether to save conversation")
    execution_mode: ExecutionModeEnum = Field(
        ExecutionModeEnum.ASYNCHRONOUS,
        description="Execution mode (workflows are typically async)"
    )
    priority: int = Field(1, ge=1, le=10, description="Workflow priority")

class WorkflowResponse(BaseModel):
    """Schema for workflow execution responses."""
    workflow_name: str = Field(..., description="Workflow name")
    task_id: Optional[str] = Field(None, description="Task ID for async workflows")
    status: str = Field(..., description="Workflow execution status")
    result: Optional[Dict[str, Any]] = Field(None, description="Workflow execution result")
    execution_time: float = Field(..., description="Workflow execution time in seconds")
    error: Optional[str] = Field(None, description="Error message if workflow failed")

class HealthCheckResponse(BaseModel):
    """Schema for health check responses."""
    task_id: Optional[str] = Field(None, description="Task ID for async health checks")
    status: str = Field(..., description="Health check status")
    health_data: Optional[Dict[str, Any]] = Field(None, description="Health check data")
    execution_time: float = Field(..., description="Health check execution time")
    async_mode: bool = Field(..., description="Whether health check was async")

# Additional schemas for specific task types

class AgentChatRequest(BaseModel):
    """Schema for enhanced agent chat requests."""
    input: str = Field(..., description="User input message")
    conversation_id: Optional[str] = Field(None, description="Optional conversation ID")
    use_multi_agent: bool = Field(False, description="Whether to use multi-agent processing")
    use_rag: bool = Field(False, description="Whether to use RAG for document context")
    save_conversation: bool = Field(True, description="Whether to save the conversation")
    async_mode: bool = Field(False, description="Whether to execute asynchronously")

class MultiAgentWorkflowRequest(BaseModel):
    """Schema for multi-agent workflow requests."""
    workflow_type: str = Field(..., description="Type of workflow to execute")
    input: str = Field(..., description="Input data for the workflow")
    conversation_id: Optional[str] = Field(None, description="Optional conversation ID")
    save_conversation: bool = Field(True, description="Whether to save the conversation")
    async_mode: bool = Field(False, description="Whether to execute asynchronously")

class RAGQueryRequest(BaseModel):
    """Schema for RAG query requests."""
    query: str = Field(..., description="The query to process")
    search_limit: int = Field(5, ge=1, le=20, description="Number of documents to retrieve")
    use_multi_agent: bool = Field(False, description="Whether to use multi-agent processing")
    conversation_id: Optional[str] = Field(None, description="Optional conversation ID")
    save_conversation: bool = Field(True, description="Whether to save the conversation")
    async_mode: bool = Field(False, description="Whether to execute asynchronously")

class DocumentSearchRequest(BaseModel):
    """Schema for document search requests."""
    query: str = Field(..., description="Search query")
    limit: int = Field(5, ge=1, le=50, description="Maximum number of results")
    score_threshold: float = Field(0.1, ge=0.0, le=1.0, description="Minimum similarity score")
    search_type: str = Field("chunks", description="Type of search (chunks, documents, both)")

class SystemAnalysisRequest(BaseModel):
    """Schema for system analysis requests."""
    analysis_type: str = Field("basic", description="Type of analysis to perform")
    async_mode: bool = Field(False, description="Whether to execute asynchronously")

class DataCleanupRequest(BaseModel):
    """Schema for data cleanup requests."""
    days_old: int = Field(30, ge=1, description="Number of days old data should be for cleanup")

# Response schemas for specific operations

class EnhancedChatResponse(BaseModel):
    """Schema for enhanced chat responses."""
    task_id: Optional[str] = Field(None, description="Task ID for async operations")
    status: str = Field(..., description="Operation status")
    response: Optional[Dict[str, Any]] = Field(None, description="Chat response data")
    execution_time: float = Field(..., description="Execution time in seconds")
    async_mode: bool = Field(..., description="Whether operation was async")
    error: Optional[str] = Field(None, description="Error message if operation failed")

class WorkflowExecutionResponse(BaseModel):
    """Schema for workflow execution responses."""
    task_id: Optional[str] = Field(None, description="Task ID for async workflows")
    status: str = Field(..., description="Workflow status")
    workflow_result: Optional[Dict[str, Any]] = Field(None, description="Workflow result data")
    execution_time: float = Field(..., description="Execution time in seconds")
    async_mode: bool = Field(..., description="Whether workflow was async")
    error: Optional[str] = Field(None, description="Error message if workflow failed")

class RAGQueryResponse(BaseModel):
    """Schema for RAG query responses."""
    task_id: Optional[str] = Field(None, description="Task ID for async queries")
    status: str = Field(..., description="Query status")
    rag_result: Optional[Dict[str, Any]] = Field(None, description="RAG query result data")
    execution_time: float = Field(..., description="Execution time in seconds")
    async_mode: bool = Field(..., description="Whether query was async")
    error: Optional[str] = Field(None, description="Error message if query failed")

class SystemStatusResponse(BaseModel):
    """Schema for system status responses."""
    status: str = Field(..., description="Overall system status")
    system_info: Optional[Dict[str, Any]] = Field(None, description="System information")
    execution_time: float = Field(..., description="Status check execution time")
    orchestrator_version: str = Field(..., description="Orchestrator version")

class CleanupResponse(BaseModel):
    """Schema for cleanup operation responses."""
    task_id: str = Field(..., description="Cleanup task ID")
    status: str = Field(..., description="Cleanup status")
    message: str = Field(..., description="Cleanup status message")
    execution_time: float = Field(..., description="Execution time in seconds")
