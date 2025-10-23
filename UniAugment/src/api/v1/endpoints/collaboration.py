"""
Collaboration API Endpoints

API endpoints for managing multi-agent collaboration workflows and patterns.
"""

import logging
from typing import List, Optional
from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.database.database import SessionLocal
from app.services.collaboration_service import CollaborationService
from app.models.agent_collaboration import (
    CollaborationWorkflow, CollaborationStep, CollaborationPattern,
    WorkflowStatus, StepStatus, PatternType
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/collaboration", tags=["Collaboration"])


# Dependency to get sync database session
def get_db():
    """Dependency to get sync database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ============================================================================
# WORKFLOW MANAGEMENT ENDPOINTS
# ============================================================================

@router.post("/workflows", status_code=status.HTTP_201_CREATED)
async def create_workflow(
    workflow_data: dict,
    db: Session = Depends(get_db)
):
    """
    Create a new collaboration workflow from a pattern.

    Request body:
    {
        "pattern_id": "uuid",
        "initiator_agent_id": "master_orchestrator",
        "task_description": "Analyze and fix security vulnerabilities",
        "context": {...},
        "custom_steps": [...]  // Optional: override pattern steps
    }
    """
    try:
        service = CollaborationService(db)

        workflow = await service.create_workflow(
            pattern_id=workflow_data.get("pattern_id"),
            initiator_agent_id=workflow_data.get("initiator_agent_id"),
            task_description=workflow_data.get("task_description"),
            context=workflow_data.get("context", {}),
            custom_steps=workflow_data.get("custom_steps")
        )

        logger.info(f"✅ Created collaboration workflow: {workflow['id']}")

        return workflow

    except Exception as e:
        logger.error(f"❌ Failed to create workflow: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create workflow: {str(e)}"
        )


@router.get("/workflows")
async def list_workflows(
    status: Optional[str] = Query(None, description="Filter by status"),
    initiator_agent_id: Optional[str] = Query(None, description="Filter by initiator"),
    limit: int = Query(50, description="Maximum number of records"),
    db: Session = Depends(get_db)
):
    """
    List all collaboration workflows with optional filters.
    """
    try:
        query = db.query(CollaborationWorkflow)

        if status:
            query = query.filter(CollaborationWorkflow.status == status)

        if initiator_agent_id:
            query = query.filter(CollaborationWorkflow.initiator_agent_id == initiator_agent_id)

        workflows = query.order_by(
            CollaborationWorkflow.created_at.desc()
        ).limit(limit).all()

        return {
            "workflows": [
                {
                    "id": str(workflow.id),
                    "pattern_id": str(workflow.pattern_id),
                    "initiator_agent_id": workflow.initiator_agent_id,
                    "task_description": workflow.task_description,
                    "status": workflow.status,
                    "current_step": workflow.current_step,
                    "total_steps": workflow.total_steps,
                    "created_at": workflow.created_at.isoformat() if workflow.created_at else None,
                    "started_at": workflow.started_at.isoformat() if workflow.started_at else None,
                    "completed_at": workflow.completed_at.isoformat() if workflow.completed_at else None
                }
                for workflow in workflows
            ],
            "total": len(workflows)
        }

    except Exception as e:
        logger.error(f"❌ Failed to list workflows: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list workflows: {str(e)}"
        )


@router.get("/workflows/{workflow_id}")
async def get_workflow_status(
    workflow_id: str,
    db: Session = Depends(get_db)
):
    """
    Get detailed status of a specific workflow.
    """
    try:
        service = CollaborationService(db)

        status_info = await service.get_workflow_status(workflow_id)

        if not status_info:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Workflow not found: {workflow_id}"
            )

        return status_info

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to get workflow status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get workflow status: {str(e)}"
        )


# ============================================================================
# WORKFLOW EXECUTION ENDPOINTS
# ============================================================================

@router.post("/workflows/{workflow_id}/execute")
async def execute_workflow(
    workflow_id: str,
    execution_data: dict,
    db: Session = Depends(get_db)
):
    """
    Execute a collaboration workflow.

    Request body:
    {
        "max_steps": 10  // Optional: limit number of steps
    }
    """
    try:
        service = CollaborationService(db)

        result = await service.execute_workflow(
            workflow_id=workflow_id,
            max_steps=execution_data.get("max_steps")
        )

        logger.info(f"✅ Executed workflow: {workflow_id}")

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to execute workflow: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to execute workflow: {str(e)}"
        )


@router.post("/workflows/{workflow_id}/cancel")
async def cancel_workflow(
    workflow_id: str,
    cancellation_data: dict,
    db: Session = Depends(get_db)
):
    """
    Cancel a running workflow.

    Request body:
    {
        "reason": "User requested cancellation"
    }
    """
    try:
        service = CollaborationService(db)

        result = await service.cancel_workflow(
            workflow_id=workflow_id,
            reason=cancellation_data.get("reason", "Cancelled by user")
        )

        logger.info(f"✅ Cancelled workflow: {workflow_id}")

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to cancel workflow: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to cancel workflow: {str(e)}"
        )


# ============================================================================
# PATTERN MANAGEMENT ENDPOINTS
# ============================================================================

@router.get("/patterns")
async def list_patterns(
    pattern_type: Optional[str] = Query(None, description="Filter by pattern type"),
    enabled: Optional[bool] = Query(None, description="Filter by enabled status"),
    db: Session = Depends(get_db)
):
    """
    List all available collaboration patterns.
    """
    try:
        service = CollaborationService(db)

        patterns = await service.get_available_patterns(
            pattern_type=PatternType(pattern_type) if pattern_type else None,
            enabled=enabled
        )

        return {
            "patterns": patterns,
            "total": len(patterns)
        }

    except Exception as e:
        logger.error(f"❌ Failed to list patterns: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list patterns: {str(e)}"
        )


@router.get("/patterns/{pattern_id}")
async def get_pattern(
    pattern_id: str,
    db: Session = Depends(get_db)
):
    """
    Get detailed information about a specific pattern.
    """
    try:
        service = CollaborationService(db)

        pattern = await service.get_pattern_by_id(pattern_id)

        if not pattern:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Pattern not found: {pattern_id}"
            )

        return pattern

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to get pattern: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get pattern: {str(e)}"
        )


@router.post("/patterns", status_code=status.HTTP_201_CREATED)
async def register_pattern(
    pattern_data: dict,
    db: Session = Depends(get_db)
):
    """
    Register a new collaboration pattern.

    Request body:
    {
        "name": "Security Analysis Pipeline",
        "description": "Collaborative security analysis workflow",
        "pattern_type": "hierarchical",
        "required_agents": ["security_analyst", "code_reviewer"],
        "optional_agents": ["test_engineer"],
        "step_definitions": [...],
        "decision_points": [...],
        "max_steps": 10,
        "max_execution_time": 300
    }
    """
    try:
        service = CollaborationService(db)

        pattern = await service.register_pattern(
            name=pattern_data.get("name"),
            description=pattern_data.get("description"),
            pattern_type=PatternType(pattern_data.get("pattern_type")),
            required_agents=pattern_data.get("required_agents", []),
            optional_agents=pattern_data.get("optional_agents", []),
            step_definitions=pattern_data.get("step_definitions", []),
            decision_points=pattern_data.get("decision_points", []),
            max_steps=pattern_data.get("max_steps"),
            max_execution_time=pattern_data.get("max_execution_time")
        )

        logger.info(f"✅ Registered collaboration pattern: {pattern['name']}")

        return pattern

    except Exception as e:
        logger.error(f"❌ Failed to register pattern: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to register pattern: {str(e)}"
        )


# ============================================================================
# STEP MANAGEMENT ENDPOINTS
# ============================================================================

@router.get("/workflows/{workflow_id}/steps")
async def get_workflow_steps(
    workflow_id: str,
    db: Session = Depends(get_db)
):
    """
    Get all steps for a specific workflow.
    """
    try:
        steps = db.query(CollaborationStep).filter(
            CollaborationStep.workflow_id == workflow_id
        ).order_by(CollaborationStep.step_number).all()

        return {
            "workflow_id": workflow_id,
            "steps": [
                {
                    "id": str(step.id),
                    "step_number": step.step_number,
                    "agent_id": step.agent_id,
                    "action": step.action,
                    "status": step.status,
                    "started_at": step.started_at.isoformat() if step.started_at else None,
                    "completed_at": step.completed_at.isoformat() if step.completed_at else None,
                    "result": step.result,
                    "error_message": step.error_message
                }
                for step in steps
            ],
            "total": len(steps)
        }

    except Exception as e:
        logger.error(f"❌ Failed to get workflow steps: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get workflow steps: {str(e)}"
        )



# ============================================================================
# PHASE 5: TASK FORCE COLLABORATION ENDPOINTS
# ============================================================================

@router.post("/task-forces", status_code=status.HTTP_201_CREATED)
async def create_task_force(
    task_force_data: dict,
    db: Session = Depends(get_db)
):
    """
    Create a temporary Task Force for collaborative problem-solving.

    Request body:
    {
        "specialist_agent_ids": ["agent1", "agent2", "agent3"],
        "task_description": "Solve complex problem X",
        "initiator_agent_id": "orchestrator_agent",
        "context": {"key": "value"}
    }
    """
    try:
        service = CollaborationService(db)

        workflow = await service.create_task_force(
            specialist_agent_ids=task_force_data.get("specialist_agent_ids", []),
            task_description=task_force_data["task_description"],
            initiator_agent_id=task_force_data["initiator_agent_id"],
            context=task_force_data.get("context")
        )

        return {
            "workflow_id": workflow.workflow_id,
            "task_description": workflow.task_description,
            "specialists": workflow.participating_agents,
            "status": workflow.status.value if hasattr(workflow.status, 'value') else str(workflow.status),
            "workflow_type": workflow.workflow_type,
            "created_at": workflow.started_at.isoformat() if workflow.started_at else datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.error(f"❌ Failed to create task force: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create task force: {str(e)}"
        )


@router.get("/task-forces/{workflow_id}/conversation")
async def get_task_force_conversation(
    workflow_id: str,
    db: Session = Depends(get_db)
):
    """Get the full conversation history of a task force."""
    try:
        service = CollaborationService(db)
        conversation = await service.get_task_force_conversation(workflow_id)

        return {
            "workflow_id": workflow_id,
            "messages": conversation,
            "total": len(conversation)
        }

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"❌ Failed to get task force conversation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get task force conversation: {str(e)}"
        )


@router.post("/task-forces/{workflow_id}/message")
async def add_task_force_message(
    workflow_id: str,
    message_data: dict,
    db: Session = Depends(get_db)
):
    """
    Add a message to the task force conversation.

    Request body:
    {
        "agent_id": "specialist_agent_1",
        "message": "I propose solution X",
        "message_type": "proposal"
    }
    """
    try:
        service = CollaborationService(db)

        result = await service.add_task_force_message(
            workflow_id=workflow_id,
            agent_id=message_data["agent_id"],
            message=message_data["message"],
            message_type=message_data.get("message_type", "response")
        )

        return result

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"❌ Failed to add task force message: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to add task force message: {str(e)}"
        )


@router.get("/task-forces/{workflow_id}/status")
async def get_task_force_status(
    workflow_id: str,
    db: Session = Depends(get_db)
):
    """Evaluate if the task force has reached a terminal state."""
    try:
        service = CollaborationService(db)
        status_info = await service.evaluate_task_force_completion(workflow_id)

        return status_info

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"❌ Failed to get task force status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get task force status: {str(e)}"
        )

