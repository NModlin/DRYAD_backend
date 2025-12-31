"""
Self-Healing API Endpoints
Implements the GAD (Governed Agentic Development) framework for autonomous code fixes.
"""

from fastapi import APIRouter, HTTPException, Depends, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from typing import Dict, Any, List
from datetime import datetime
from pydantic import BaseModel, Field

from app.database.database import AsyncSessionLocal
from app.database.self_healing_models import SelfHealingTask, TaskStatus, ErrorSeverity
from app.core.logging_config import get_logger
from app.integrations.teams_notifier import send_review_notification
from app.core.multi_agent import multi_agent_orchestrator

logger = get_logger(__name__)

router = APIRouter(prefix="/self-healing", tags=["self-healing"])


# Pydantic models
class ErrorDetails(BaseModel):
    """Error details from Guardian."""
    error_type: str
    error_message: str
    file_path: str
    line_number: int
    stack_trace: str = ""
    severity: str
    timestamp: str
    hash: str


class SelfHealingRequest(BaseModel):
    """Request to initiate self-healing."""
    task_type: str = Field(default="self_healing_fix")
    error_details: ErrorDetails
    goal: str
    timestamp: str


class ReviewDecision(BaseModel):
    """Human review decision."""
    decision: str = Field(..., pattern="^(approved|rejected)$")
    reviewer: str
    comments: str = ""


# Dependency
async def get_db():
    """Get database session."""
    async with AsyncSessionLocal() as session:
        yield session


@router.post("/", response_model=Dict[str, Any])
async def create_self_healing_task(
    request: SelfHealingRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new self-healing task (called by Guardian).
    
    This endpoint receives error details from the Guardian agent,
    creates a task, and initiates the planning phase.
    """
    try:
        logger.info(f"🔧 Received self-healing request for {request.error_details.error_type}")
        
        # Create task in database
        task = SelfHealingTask(
            error_type=request.error_details.error_type,
            error_message=request.error_details.error_message,
            file_path=request.error_details.file_path,
            line_number=request.error_details.line_number,
            stack_trace=request.error_details.stack_trace,
            severity=ErrorSeverity(request.error_details.severity),
            error_hash=request.error_details.hash,
            goal=request.goal,
            status=TaskStatus.PENDING_REVIEW
        )
        
        db.add(task)
        await db.commit()
        await db.refresh(task)
        
        logger.info(f"✅ Created task {task.id}")
        
        # Generate fix plan using Planning Agent (async)
        # This will be done in background to avoid blocking
        import asyncio
        asyncio.create_task(_generate_fix_plan(task.id, request))
        
        return {
            "success": True,
            "task_id": task.id,
            "status": task.status.value,
            "message": "Self-healing task created, generating fix plan..."
        }
    
    except Exception as e:
        logger.error(f"Error creating self-healing task: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


async def _generate_fix_plan(task_id: str, request: SelfHealingRequest):
    """
    Generate fix plan using Planning Agent (background task).
    
    This uses the existing multi-agent orchestrator to analyze
    the error and generate a structured fix plan.
    """
    try:
        logger.info(f"🤖 Generating fix plan for task {task_id}")
        
        # Prepare context for Planning Agent
        context = {
            "error_type": request.error_details.error_type,
            "error_message": request.error_details.error_message,
            "file_path": request.error_details.file_path,
            "line_number": request.error_details.line_number,
            "goal": request.goal
        }
        
        # Use Planning Agent to analyze and create plan
        # This is a simplified version - in production, you'd use the full agent workflow
        plan = {
            "changes": [
                {
                    "file": request.error_details.file_path,
                    "line_start": max(1, request.error_details.line_number - 2),
                    "line_end": request.error_details.line_number + 2,
                    "rationale": f"Fix {request.error_details.error_type} by adding proper validation"
                }
            ],
            "tests_to_run": [
                f"tests/test_{request.error_details.file_path.split('/')[-1].replace('.py', '')}.py"
            ],
            "rollback_plan": "Revert changes if tests fail"
        }
        
        # Update task with plan
        async with AsyncSessionLocal() as db:
            stmt = (
                update(SelfHealingTask)
                .where(SelfHealingTask.id == task_id)
                .values(plan=plan)
            )
            await db.execute(stmt)
            await db.commit()
            
            # Get updated task
            result = await db.execute(
                select(SelfHealingTask).where(SelfHealingTask.id == task_id)
            )
            task = result.scalar_one_or_none()
        
        if task:
            # Send Teams notification for review
            await send_review_notification(task.to_dict())
            logger.info(f"✅ Fix plan generated and sent for review: {task_id}")
        
    except Exception as e:
        logger.error(f"Error generating fix plan: {e}", exc_info=True)


@router.post("/review/{task_id}", response_model=Dict[str, Any])
async def review_task(
    task_id: str,
    decision: ReviewDecision,
    db: AsyncSession = Depends(get_db)
):
    """
    Submit human review decision (called from Teams).
    
    This is the critical GAD safety gate - no code changes
    are applied without explicit human approval.
    """
    try:
        logger.info(f"📋 Received review for task {task_id}: {decision.decision}")
        
        # Get task
        result = await db.execute(
            select(SelfHealingTask).where(SelfHealingTask.id == task_id)
        )
        task = result.scalar_one_or_none()
        
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        
        # Check if already reviewed
        if task.status != TaskStatus.PENDING_REVIEW:
            return {
                "success": False,
                "message": f"Task already {task.status.value}",
                "task_id": task_id
            }
        
        # Update task with review decision
        new_status = TaskStatus.APPROVED if decision.decision == "approved" else TaskStatus.REJECTED
        
        stmt = (
            update(SelfHealingTask)
            .where(SelfHealingTask.id == task_id)
            .values(
                status=new_status,
                reviewer=decision.reviewer,
                review_comments=decision.comments,
                reviewed_at=datetime.now()
            )
        )
        await db.execute(stmt)
        await db.commit()
        
        logger.info(f"✅ Task {task_id} {decision.decision} by {decision.reviewer}")
        
        return {
            "success": True,
            "task_id": task_id,
            "status": new_status.value,
            "message": f"Task {decision.decision} successfully"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error reviewing task: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tasks/{task_id}", response_model=Dict[str, Any])
async def get_task(
    task_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get detailed task information."""
    try:
        result = await db.execute(
            select(SelfHealingTask).where(SelfHealingTask.id == task_id)
        )
        task = result.scalar_one_or_none()
        
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        
        return task.to_dict()
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting task: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tasks", response_model=List[Dict[str, Any]])
async def list_tasks(
    status: str = None,
    severity: str = None,
    limit: int = 50,
    db: AsyncSession = Depends(get_db)
):
    """List self-healing tasks with optional filters."""
    try:
        stmt = select(SelfHealingTask).order_by(SelfHealingTask.created_at.desc())
        
        if status:
            stmt = stmt.where(SelfHealingTask.status == TaskStatus(status))
        
        if severity:
            stmt = stmt.where(SelfHealingTask.severity == ErrorSeverity(severity))
        
        stmt = stmt.limit(limit)
        
        result = await db.execute(stmt)
        tasks = result.scalars().all()
        
        return [task.to_dict() for task in tasks]
    
    except Exception as e:
        logger.error(f"Error listing tasks: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats", response_model=Dict[str, Any])
async def get_stats(db: AsyncSession = Depends(get_db)):
    """Get self-healing system statistics."""
    try:
        from sqlalchemy import func
        
        # Count by status
        status_counts = {}
        for status in TaskStatus:
            result = await db.execute(
                select(func.count(SelfHealingTask.id))
                .where(SelfHealingTask.status == status)
            )
            status_counts[status.value] = result.scalar()
        
        # Count by severity
        severity_counts = {}
        for severity in ErrorSeverity:
            result = await db.execute(
                select(func.count(SelfHealingTask.id))
                .where(SelfHealingTask.severity == severity)
            )
            severity_counts[severity.value] = result.scalar()
        
        # Get Guardian stats
        from app.core.guardian import get_guardian_stats
        guardian_stats = get_guardian_stats()
        
        return {
            "status_counts": status_counts,
            "severity_counts": severity_counts,
            "guardian": guardian_stats
        }
    
    except Exception as e:
        logger.error(f"Error getting stats: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

