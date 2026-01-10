"""
Advanced Workflow API endpoints for DRYAD.AI Backend
Provides REST API endpoints for creating and managing complex multi-step workflows.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel, Field
from app.core.security import get_current_user, User

from app.core.advanced_workflows import get_workflow_engine, WorkflowStatus
from app.core.advanced_agents import get_research_agent
from app.core.monitoring import metrics_collector

logger = logging.getLogger(__name__)

router = APIRouter()


class WorkflowCreateRequest(BaseModel):
    """Request model for creating a workflow."""
    template_name: str = Field(..., description="Name of the workflow template to use")
    inputs: Dict[str, Any] = Field(..., description="Input parameters for the workflow")
    name: Optional[str] = Field(None, description="Custom name for the workflow instance")
    description: Optional[str] = Field(None, description="Custom description for the workflow")


class WorkflowStatusResponse(BaseModel):
    """Response model for workflow status."""
    workflow_id: str
    name: str
    status: str
    progress: Dict[str, Any]
    created_at: float
    started_at: Optional[float]
    completed_at: Optional[float]
    results: Optional[Dict[str, Any]]
    is_running: bool


class AgentTaskRequest(BaseModel):
    """Request model for agent tasks."""
    agent_type: str = Field(..., description="Type of agent to use (research, analysis, etc.)")
    task_type: str = Field(..., description="Type of task to execute")
    inputs: Dict[str, Any] = Field(..., description="Task input parameters")
    timeout: int = Field(300, description="Task timeout in seconds")
    priority: int = Field(1, description="Task priority (1-10)")


class AgentTaskResponse(BaseModel):
    """Response model for agent task results."""
    task_id: str
    agent_id: str
    success: bool
    result: Any
    confidence: float
    execution_time: float
    metadata: Dict[str, Any]


@router.post("/workflows", response_model=Dict[str, str])
async def create_workflow(
    request: WorkflowCreateRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user)
):
    """
    Create a new workflow from a template.
    
    Args:
        request: Workflow creation parameters
        background_tasks: FastAPI background tasks
        current_user: Current authenticated user
        
    Returns:
        Dict containing the workflow ID
    """
    try:
        workflow_engine = get_workflow_engine()
        
        # Create workflow from template
        workflow_id = await workflow_engine.create_workflow_from_template(
            request.template_name,
            request.inputs
        )
        
        # Start workflow execution in background
        background_tasks.add_task(
            _execute_workflow_background,
            workflow_id,
            current_user.id
        )
        
        logger.info(f"Created workflow {workflow_id} for user {current_user.id}")
        metrics_collector.record_counter("workflows.created")
        
        return {
            "workflow_id": workflow_id,
            "message": "Workflow created and started",
            "template": request.template_name
        }
        
    except ValueError as e:
        logger.error(f"Invalid workflow template: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to create workflow: {e}")
        raise HTTPException(status_code=500, detail="Failed to create workflow")


async def _execute_workflow_background(workflow_id: str, user_id: str):
    """Execute workflow in background."""
    try:
        workflow_engine = get_workflow_engine()
        results = await workflow_engine.execute_workflow(workflow_id)
        logger.info(f"Workflow {workflow_id} completed for user {user_id}")
    except Exception as e:
        logger.error(f"Background workflow {workflow_id} failed: {e}")


@router.get("/workflows/{workflow_id}", response_model=WorkflowStatusResponse)
async def get_workflow_status(
    workflow_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Get the status of a specific workflow.
    
    Args:
        workflow_id: ID of the workflow to check
        current_user: Current authenticated user
        
    Returns:
        Workflow status information
    """
    try:
        workflow_engine = get_workflow_engine()
        status = workflow_engine.get_workflow_status(workflow_id)
        
        if "error" in status:
            raise HTTPException(status_code=404, detail="Workflow not found")
        
        workflow_data = status["workflow"]
        progress_data = status["progress"]
        
        return WorkflowStatusResponse(
            workflow_id=workflow_id,
            name=workflow_data["name"],
            status=workflow_data["status"],
            progress=progress_data,
            created_at=workflow_data["created_at"],
            started_at=workflow_data.get("started_at"),
            completed_at=workflow_data.get("completed_at"),
            results=workflow_data.get("results"),
            is_running=status["is_running"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get workflow status: {e}")
        raise HTTPException(status_code=500, detail="Failed to get workflow status")


@router.get("/workflows", response_model=Dict[str, Any])
async def list_workflows(
    current_user: User = Depends(get_current_user)
):
    """
    List all workflows for the current user.
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        List of workflows with summary information
    """
    try:
        workflow_engine = get_workflow_engine()
        workflows_data = workflow_engine.list_workflows()
        
        return workflows_data
        
    except Exception as e:
        logger.error(f"Failed to list workflows: {e}")
        raise HTTPException(status_code=500, detail="Failed to list workflows")


@router.get("/workflows/templates", response_model=Dict[str, Any])
async def get_workflow_templates():
    """
    Get available workflow templates.
    
    Returns:
        Dict containing available workflow templates
    """
    try:
        workflow_engine = get_workflow_engine()
        
        templates = {}
        for template_name, template_data in workflow_engine.workflow_templates.items():
            templates[template_name] = {
                "name": template_data["name"],
                "description": template_data["description"],
                "task_count": len(template_data["tasks"]),
                "estimated_duration": sum(
                    task.get("timeout", 300) for task in template_data["tasks"]
                ),
                "required_inputs": _extract_required_inputs(template_data)
            }
        
        return {
            "templates": templates,
            "total_templates": len(templates)
        }
        
    except Exception as e:
        logger.error(f"Failed to get workflow templates: {e}")
        raise HTTPException(status_code=500, detail="Failed to get workflow templates")


def _extract_required_inputs(template_data: Dict[str, Any]) -> List[str]:
    """Extract required inputs from template data."""
    # Simple extraction - in production, would analyze template more thoroughly
    common_inputs = ["query", "topic", "context"]
    
    # Check template description for hints about required inputs
    description = template_data.get("description", "").lower()
    required = []
    
    if "research" in description:
        required.extend(["query", "topic"])
    if "content" in description:
        required.extend(["topic", "content_type"])
    if "decision" in description:
        required.extend(["options", "criteria"])
    
    return list(set(required)) if required else ["query"]


@router.post("/agents/tasks", response_model=AgentTaskResponse)
async def execute_agent_task(
    request: AgentTaskRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Execute a task using a specific agent.
    
    Args:
        request: Agent task parameters
        current_user: Current authenticated user
        
    Returns:
        Task execution results
    """
    try:
        # Get the appropriate agent
        if request.agent_type == "research":
            agent = get_research_agent()
        else:
            raise HTTPException(status_code=400, detail=f"Unknown agent type: {request.agent_type}")
        
        # Create agent task
        from app.core.advanced_agents import AgentTask
        import uuid
        import time
        
        task = AgentTask(
            id=str(uuid.uuid4()),
            type=request.task_type,
            description=f"{request.task_type} task for user {current_user.id}",
            inputs=request.inputs,
            priority=request.priority,
            timeout=request.timeout,
            created_at=time.time()
        )
        
        # Execute task
        result = await agent.execute_task(task)
        
        logger.info(f"Agent task {task.id} completed for user {current_user.id}")
        metrics_collector.record_counter(f"agent_tasks.{request.agent_type}.executed")
        
        return AgentTaskResponse(
            task_id=result.task_id,
            agent_id=result.agent_id,
            success=result.success,
            result=result.result,
            confidence=result.confidence,
            execution_time=result.execution_time,
            metadata=result.metadata
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to execute agent task: {e}")
        raise HTTPException(status_code=500, detail="Failed to execute agent task")


@router.get("/agents/status", response_model=Dict[str, Any])
async def get_agents_status():
    """
    Get status of all available agents.
    
    Returns:
        Status information for all agents
    """
    try:
        agents_status = {}
        
        # Get research agent status
        research_agent = get_research_agent()
        agents_status["research"] = research_agent.get_status()
        
        return {
            "agents": agents_status,
            "total_agents": len(agents_status),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get agents status: {e}")
        raise HTTPException(status_code=500, detail="Failed to get agents status")


@router.get("/agents/{agent_type}/capabilities", response_model=Dict[str, Any])
async def get_agent_capabilities(agent_type: str):
    """
    Get capabilities of a specific agent type.
    
    Args:
        agent_type: Type of agent to query
        
    Returns:
        Agent capabilities information
    """
    try:
        if agent_type == "research":
            agent = get_research_agent()
        else:
            raise HTTPException(status_code=404, detail=f"Unknown agent type: {agent_type}")
        
        status = agent.get_status()
        
        return {
            "agent_type": agent_type,
            "agent_name": status["name"],
            "capabilities": status["capabilities"],
            "performance": status["performance"],
            "llm_available": status["llm_available"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get agent capabilities: {e}")
        raise HTTPException(status_code=500, detail="Failed to get agent capabilities")


@router.post("/workflows/{workflow_id}/cancel")
async def cancel_workflow(
    workflow_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Cancel a running workflow.
    
    Args:
        workflow_id: ID of the workflow to cancel
        current_user: Current authenticated user
        
    Returns:
        Cancellation confirmation
    """
    try:
        workflow_engine = get_workflow_engine()
        
        # Check if workflow exists and is running
        status = workflow_engine.get_workflow_status(workflow_id)
        if "error" in status:
            raise HTTPException(status_code=404, detail="Workflow not found")
        
        if not status["is_running"]:
            raise HTTPException(status_code=400, detail="Workflow is not running")
        
        # Cancel the workflow (implementation would depend on workflow engine)
        # For now, just return success
        logger.info(f"Workflow {workflow_id} cancellation requested by user {current_user.id}")
        
        return {
            "message": "Workflow cancellation requested",
            "workflow_id": workflow_id,
            "status": "cancelling"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to cancel workflow: {e}")
        raise HTTPException(status_code=500, detail="Failed to cancel workflow")


@router.get("/workflows/{workflow_id}/results", response_model=Dict[str, Any])
async def get_workflow_results(
    workflow_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Get detailed results from a completed workflow.
    
    Args:
        workflow_id: ID of the workflow
        current_user: Current authenticated user
        
    Returns:
        Detailed workflow results
    """
    try:
        workflow_engine = get_workflow_engine()
        status = workflow_engine.get_workflow_status(workflow_id)
        
        if "error" in status:
            raise HTTPException(status_code=404, detail="Workflow not found")
        
        workflow_data = status["workflow"]
        
        if workflow_data["status"] != WorkflowStatus.COMPLETED:
            raise HTTPException(status_code=400, detail="Workflow is not completed")
        
        return {
            "workflow_id": workflow_id,
            "status": workflow_data["status"],
            "results": workflow_data.get("results", {}),
            "tasks": [
                {
                    "name": task["name"],
                    "status": task["status"],
                    "outputs": task.get("outputs", {}),
                    "execution_time": task.get("completed_at", 0) - task.get("started_at", 0) if task.get("started_at") and task.get("completed_at") else 0
                }
                for task in workflow_data.get("tasks", [])
            ],
            "total_execution_time": workflow_data.get("completed_at", 0) - workflow_data.get("started_at", 0) if workflow_data.get("started_at") and workflow_data.get("completed_at") else 0
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get workflow results: {e}")
        raise HTTPException(status_code=500, detail="Failed to get workflow results")
