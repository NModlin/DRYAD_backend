"""
Project Manager Agent API Endpoints

Endpoints for project planning, task management, and progress tracking.
"""

import logging
from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.database import get_db
from app.services.project_manager_agent import ProjectManagerAgent, TaskStatus

logger = logging.getLogger(__name__)

router = APIRouter()


# Pydantic schemas
class ProjectPlanRequest(BaseModel):
    """Request to create a project plan."""
    grove_id: str = Field(..., description="DRYAD grove ID for the project")
    project_description: str = Field(..., description="Description of the project")
    context: Optional[Dict[str, Any]] = Field(default=None, description="Additional context")


class TaskProgressUpdate(BaseModel):
    """Request to update task progress."""
    task_id: str = Field(..., description="Task ID")
    progress: float = Field(..., ge=0.0, le=1.0, description="Progress (0.0 to 1.0)")
    status: Optional[str] = Field(default=None, description="Task status")


class ProjectPlanResponse(BaseModel):
    """Response for project plan creation."""
    status: str
    grove_id: Optional[str] = None
    total_tasks: Optional[int] = None
    execution_waves: Optional[int] = None
    tasks: Optional[list] = None
    execution_plan: Optional[list] = None
    message: Optional[str] = None
    error: Optional[str] = None


class TaskProgressResponse(BaseModel):
    """Response for task progress update."""
    status: str
    task_id: Optional[str] = None
    progress: Optional[float] = None
    task_status: Optional[str] = None
    error: Optional[str] = None


class ProjectStatusResponse(BaseModel):
    """Response for project status."""
    total_tasks: int
    status_breakdown: Dict[str, int]
    overall_progress: float
    completed_tasks: int
    in_progress_tasks: int
    pending_tasks: int
    blocked_tasks: int


@router.post(
    "/project-manager/create-plan",
    response_model=ProjectPlanResponse,
    summary="Create Project Plan",
    description="Create a comprehensive project plan with task breakdown and agent assignments"
)
async def create_project_plan(
    request: ProjectPlanRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Create a project plan.
    
    This endpoint:
    1. Decomposes the project into subtasks
    2. Creates DRYAD branches for each task
    3. Assigns agents to tasks based on capabilities
    4. Creates an execution plan
    
    Args:
        request: Project plan request
        db: Database session
        
    Returns:
        Project plan with tasks and execution plan
    """
    try:
        logger.info(f"Creating project plan for grove {request.grove_id}")
        
        pm_agent = ProjectManagerAgent(db)
        result = await pm_agent.create_project_plan(
            grove_id=request.grove_id,
            project_description=request.project_description,
            context=request.context
        )
        
        if result.get("status") == "error":
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result.get("error", "Failed to create project plan")
            )
        
        return ProjectPlanResponse(**result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create project plan: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post(
    "/project-manager/update-progress",
    response_model=TaskProgressResponse,
    summary="Update Task Progress",
    description="Update the progress and status of a task"
)
async def update_task_progress(
    request: TaskProgressUpdate,
    db: AsyncSession = Depends(get_db)
):
    """
    Update task progress.
    
    Args:
        request: Task progress update request
        db: Database session
        
    Returns:
        Updated task status
    """
    try:
        logger.info(f"Updating progress for task {request.task_id}")
        
        pm_agent = ProjectManagerAgent(db)
        
        # Validate status if provided
        task_status = None
        if request.status:
            try:
                task_status = TaskStatus(request.status)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid status: {request.status}"
                )
        
        result = await pm_agent.update_task_progress(
            task_id=request.task_id,
            progress=request.progress,
            status=task_status
        )
        
        if result.get("status") == "error":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=result.get("error", "Task not found")
            )
        
        return TaskProgressResponse(**result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update task progress: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get(
    "/project-manager/status",
    response_model=ProjectStatusResponse,
    summary="Get Project Status",
    description="Get overall project status and progress"
)
async def get_project_status(
    grove_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Get project status.
    
    Args:
        grove_id: Optional grove ID to filter by
        db: Database session
        
    Returns:
        Project status with task breakdown
    """
    try:
        logger.info(f"Getting project status (grove_id: {grove_id})")
        
        pm_agent = ProjectManagerAgent(db)
        result = pm_agent.get_project_status(grove_id=grove_id)
        
        if result.get("status") == "no_tasks":
            return ProjectStatusResponse(
                total_tasks=0,
                status_breakdown={},
                overall_progress=0.0,
                completed_tasks=0,
                in_progress_tasks=0,
                pending_tasks=0,
                blocked_tasks=0
            )
        
        return ProjectStatusResponse(**result)
        
    except Exception as e:
        logger.error(f"Failed to get project status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get(
    "/project-manager/health",
    summary="Project Manager Health Check",
    description="Check if the Project Manager agent is operational"
)
async def health_check():
    """
    Health check endpoint.
    
    Returns:
        Health status
    """
    return {
        "status": "healthy",
        "agent": "project_manager",
        "tier": "orchestrator",
        "capabilities": [
            "project_planning",
            "task_breakdown",
            "agent_assignment",
            "progress_tracking",
            "dependency_management"
        ]
    }


@router.get(
    "/project-manager/capabilities",
    summary="Get Project Manager Capabilities",
    description="Get detailed capabilities of the Project Manager agent"
)
async def get_capabilities():
    """
    Get Project Manager capabilities.
    
    Returns:
        Detailed capabilities
    """
    return {
        "agent_id": "project_manager",
        "name": "Project Manager",
        "tier": "orchestrator",
        "capabilities": {
            "project_planning": {
                "description": "Create comprehensive project plans",
                "features": [
                    "Task decomposition",
                    "DRYAD branch creation",
                    "Agent assignment",
                    "Execution planning"
                ]
            },
            "task_management": {
                "description": "Manage tasks and dependencies",
                "features": [
                    "Task tracking",
                    "Dependency management",
                    "Progress monitoring",
                    "Status updates"
                ]
            },
            "progress_tracking": {
                "description": "Track project and task progress",
                "features": [
                    "Real-time progress updates",
                    "Status breakdown",
                    "Completion tracking",
                    "Blocked task identification"
                ]
            }
        },
        "supported_task_statuses": [status.value for status in TaskStatus],
        "integration": {
            "dryad": "Full integration with grove and branch management",
            "agent_registry": "Automatic agent selection and assignment",
            "task_decomposition": "LLM-powered task breakdown"
        }
    }

