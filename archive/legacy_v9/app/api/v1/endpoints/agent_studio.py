"""
Agent Creation Studio API Endpoints

This module provides API endpoints for the DRYAD Agent Creation Studio,
allowing clients to submit agent sheets and admins to review and approve them.
"""

import logging
from typing import List, Optional
from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.api import deps
from app.models.user import User
from app.models.custom_agent import (
    AgentSubmission, CustomAgent, AgentExecution,
    AgentSheet, AgentSubmissionCreate, AgentSubmissionResponse,
    CustomAgentResponse, AgentExecutionRequest, AgentExecutionResponse
)
from app.services.agent_factory import (
    AgentValidator, AgentBuilder, get_agent_registry
)
from app.services.guardrail_service import GuardrailService
from app.services.agent_architect_service import AgentArchitectService
from app.database.database import get_db

logger = logging.getLogger(__name__)
router = APIRouter()


# ============================================================================
# CLIENT ENDPOINTS - Agent Submission and Execution
# ============================================================================

@router.post("/submit", response_model=AgentSubmissionResponse, status_code=status.HTTP_201_CREATED)
async def submit_agent_sheet(
    submission: AgentSubmissionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """
    Submit an agent sheet for review.
    
    Clients can submit agent specifications that will be reviewed by admins
    before being approved and made available for use.
    """
    try:
        # Validate agent sheet
        validator = AgentValidator(db_session=db)
        validation_result = await validator.validate_agent_sheet(submission.agent_sheet.dict())
        
        if not validation_result.valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "message": "Agent sheet validation failed",
                    "errors": validation_result.errors,
                    "warnings": validation_result.warnings
                }
            )
        
        # Create submission record
        agent_submission = AgentSubmission(
            client_id=current_user.username,
            agent_sheet=submission.agent_sheet.dict(),
            status="pending",
            submitted_at=datetime.utcnow(),
            validation_results=validation_result.to_dict()
        )
        
        db.add(agent_submission)
        await db.commit()
        await db.refresh(agent_submission)
        
        logger.info(f"✅ Agent sheet submitted: {agent_submission.id} by {current_user.username}")
        
        return AgentSubmissionResponse(
            submission_id=str(agent_submission.id),
            status="pending",
            message="Agent sheet submitted successfully and is pending review",
            estimated_review_time="24-48 hours"
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to submit agent sheet: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to submit agent sheet: {str(e)}"
        )


@router.get("/available", response_model=List[CustomAgentResponse])
async def list_available_agents(
    category: Optional[str] = Query(None, description="Filter by category"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """
    List all available custom agents for the current user.
    
    Returns agents that are approved and active, optionally filtered by category.
    """
    try:
        stmt = select(CustomAgent).where(
            CustomAgent.status == "active",
            CustomAgent.client_id == current_user.username
        )
        
        if category:
            stmt = stmt.where(CustomAgent.category == category)
        
        result = await db.execute(stmt)
        agents = result.scalars().all()
        
        # Convert to response format
        response = []
        for agent in agents:
            config = agent.agent_configuration
            capabilities = config.get("capabilities", {}).get("skills", [])
            
            response.append(CustomAgentResponse(
                agent_id=str(agent.id),
                name=agent.name,
                display_name=agent.display_name,
                description=agent.description,
                category=agent.category,
                capabilities=capabilities,
                status=agent.status,
                usage_count=agent.usage_count,
                success_rate=agent.success_rate
            ))
        
        return response
    
    except Exception as e:
        logger.error(f"❌ Failed to list available agents: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list agents: {str(e)}"
        )


@router.post("/execute", response_model=AgentExecutionResponse)
async def execute_custom_agent(
    request: AgentExecutionRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """
    Execute a custom agent with a query.
    
    Executes the specified custom agent and returns the response.
    """
    try:
        # Get agent from database
        result = await db.execute(
            select(CustomAgent).where(
                CustomAgent.name == request.agent_name,
                CustomAgent.client_id == current_user.username,
                CustomAgent.status == "active"
            )
        )
        agent_record = result.scalars().first()
        
        if not agent_record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Agent '{request.agent_name}' not found or not available"
            )
        
        # Get agent instance from registry
        registry = get_agent_registry()
        agent_instance = registry.get_agent(request.agent_name)
        
        # If not in registry, build and register it
        if not agent_instance:
            logger.info(f"Agent {request.agent_name} not in registry, building...")
            await registry.register_agent(agent_record.agent_configuration, db=db)
            agent_instance = registry.get_agent(request.agent_name)
        
        if not agent_instance:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to instantiate agent '{request.agent_name}'"
            )
        
        # Execute agent
        import time
        start_time = time.time()
        result = await agent_instance.execute(request.query, request.context)
        execution_time_ms = int((time.time() - start_time) * 1000)

        # Create execution record first to get execution_id
        execution = AgentExecution(
            agent_id=agent_record.id,
            client_id=current_user.username,
            query=request.query,
            response=result.get("response"),
            context=request.context,
            execution_time=result.get("execution_time", execution_time_ms),
            tokens_used=result.get("tokens_used"),
            success=result.get("success"),
            error_message=result.get("error"),
            branch_id=request.branch_id if request.branch_id else None
        )

        db.add(execution)
        db.flush()  # Get execution ID

        # Run guardrail checks
        guardrail_service = GuardrailService(db)
        guardrail_result = await guardrail_service.check_all_guardrails(
            execution_id=str(execution.id),
            agent_id=str(agent_record.id),
            input_text=request.query,
            output_text=result.get("response", ""),
            execution_time_ms=execution_time_ms,
            token_count=result.get("tokens_used", 0),
            context=request.context
        )

        # Handle guardrail violations
        final_response = result.get("response")
        guardrail_warnings = []

        if not guardrail_result["passed"]:
            logger.warning(
                f"⚠️ Guardrail violations detected for execution {execution.id}: "
                f"{guardrail_result['violations_count']} violations"
            )

            # If should block, raise error
            if guardrail_result["should_block"]:
                db.rollback()
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail={
                        "message": "Agent execution blocked by guardrails",
                        "violations": guardrail_result["violations"]
                    }
                )

            # If output was modified, use modified version
            if guardrail_result["modified_output"]:
                final_response = guardrail_result["modified_output"]
                execution.response = final_response
                guardrail_warnings.append("Output was modified by content filter")

            # Collect warnings
            for violation in guardrail_result["violations"]:
                if violation["action"].value == "warn":
                    guardrail_warnings.append(
                        f"{violation['guardrail']}: {violation['details']}"
                    )

        # Update agent metrics
        agent_record.update_metrics(
            execution_time=result.get("execution_time", 0),
            tokens_used=result.get("tokens_used", 0),
            success=result.get("success", False)
        )

        db.commit()
        db.refresh(execution)
        
        if not result.get("success"):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Agent execution failed: {result.get('error')}"
            )

        # Build response with guardrail info
        response_data = {
            "execution_id": str(execution.id),
            "agent_name": request.agent_name,
            "response": final_response,
            "execution_time": result["execution_time"],
            "tokens_used": result["tokens_used"],
            "success": result["success"]
        }

        # Add guardrail warnings if any
        if guardrail_warnings:
            response_data["warnings"] = guardrail_warnings
            logger.info(f"⚠️ Execution {execution.id} completed with {len(guardrail_warnings)} warnings")

        return AgentExecutionResponse(**response_data)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to execute agent: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to execute agent: {str(e)}"
        )


# ============================================================================
# ADMIN ENDPOINTS - Agent Review and Management
# ============================================================================

@router.get("/admin/submissions", dependencies=[Depends(deps.require_admin)])
async def list_agent_submissions(
    status_filter: Optional[str] = Query(None, description="Filter by status"),
    client_id: Optional[str] = Query(None, description="Filter by client ID"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db)
):
    """
    [ADMIN] List all agent submissions.
    
    Returns all agent submissions with optional filtering by status and client.
    """
    try:
        stmt = select(AgentSubmission)
        
        if status_filter:
            stmt = stmt.where(AgentSubmission.status == status_filter)
        
        if client_id:
            stmt = stmt.where(AgentSubmission.client_id == client_id)
        
        # Get count (needs separate query in async)
        # Using a simpler approach for count or skipping it?
        # A separate count query is standard.
        from sqlalchemy import func
        count_stmt = select(func.count()).select_from(AgentSubmission)
        if status_filter:
            count_stmt = count_stmt.where(AgentSubmission.status == status_filter)
        if client_id:
            count_stmt = count_stmt.where(AgentSubmission.client_id == client_id)
        
        count_result = await db.execute(count_stmt)
        total = count_result.scalar()

        result = await db.execute(
            stmt.order_by(AgentSubmission.submitted_at.desc()).offset(skip).limit(limit)
        )
        submissions = result.scalars().all()
        
        return {
            "submissions": [
                {
                    "submission_id": str(s.id),
                    "agent_name": s.agent_sheet.get("agent_definition", {}).get("name"),
                    "client_id": s.client_id,
                    "status": s.status,
                    "submitted_at": s.submitted_at.isoformat(),
                    "reviewed_at": s.reviewed_at.isoformat() if s.reviewed_at else None
                }
                for s in submissions
            ],
            "total": total,
            "page": skip // limit + 1,
            "page_size": limit
        }
    
    except Exception as e:
        logger.error(f"❌ Failed to list submissions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list submissions: {str(e)}"
        )


@router.get("/admin/submissions/{submission_id}", dependencies=[Depends(deps.require_admin)])
async def get_agent_submission(
    submission_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """
    [ADMIN] Get detailed information about an agent submission.
    """
    try:
        result = await db.execute(
            select(AgentSubmission).where(AgentSubmission.id == submission_id)
        )
        submission = result.scalars().first()
        
        if not submission:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Submission {submission_id} not found"
            )
        
        return {
            "submission_id": str(submission.id),
            "agent_sheet": submission.agent_sheet,
            "validation_results": submission.validation_results,
            "status": submission.status,
            "submitted_at": submission.submitted_at.isoformat(),
            "reviewed_at": submission.reviewed_at.isoformat() if submission.reviewed_at else None,
            "rejection_reason": submission.rejection_reason
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to get submission: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get submission: {str(e)}"
        )


@router.post("/admin/submissions/{submission_id}/approve", dependencies=[Depends(deps.require_admin)])
async def approve_agent_submission(
    submission_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """
    [ADMIN] Approve an agent submission and create the custom agent.
    """
    try:
        result = await db.execute(
            select(AgentSubmission).where(AgentSubmission.id == submission_id)
        )
        submission = result.scalars().first()
        
        if not submission:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Submission {submission_id} not found"
            )
        
        if submission.status != "pending":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Submission is not pending (current status: {submission.status})"
            )
        
        # Extract agent information
        agent_sheet = submission.agent_sheet
        agent_def = agent_sheet["agent_definition"]
        
        # Create custom agent record
        custom_agent = CustomAgent(
            submission_id=submission.id,
            name=agent_def["name"],
            display_name=agent_def["display_name"],
            description=agent_def.get("description"),
            category=agent_def.get("category"),
            client_id=submission.client_id,
            agent_configuration=agent_sheet,
            status="active"
        )
        
        db.add(custom_agent)
        
        # Update submission status
        submission.status = "approved"
        submission.reviewed_at = datetime.utcnow()
        submission.reviewed_by = current_user.id
        
        await db.commit()
        await db.refresh(custom_agent)
        
        # Register agent in runtime registry
        registry = get_agent_registry()
        await registry.register_agent(agent_sheet, db=db)
        
        logger.info(f"✅ Agent approved and registered: {custom_agent.name}")
        
        return {
            "agent_id": str(custom_agent.id),
            "agent_name": custom_agent.name,
            "status": "approved",
            "message": "Agent approved and registered successfully",
            "available_at": datetime.utcnow().isoformat()
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to approve submission: {e}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to approve submission: {str(e)}"
        )


@router.post("/admin/submissions/{submission_id}/reject", dependencies=[Depends(deps.require_admin)])
async def reject_agent_submission(
    submission_id: UUID,
    reason: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """
    [ADMIN] Reject an agent submission with a reason.
    """
    try:
        result = await db.execute(
            select(AgentSubmission).where(AgentSubmission.id == submission_id)
        )
        submission = result.scalars().first()
        
        if not submission:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Submission {submission_id} not found"
            )
        
        submission.status = "rejected"
        submission.reviewed_at = datetime.utcnow()
        submission.reviewed_by = current_user.id
        submission.rejection_reason = reason
        
        await db.commit()
        
        logger.info(f"✅ Agent submission rejected: {submission_id}")
        
        return {
            "submission_id": str(submission.id),
            "status": "rejected",
            "message": "Agent submission rejected",
            "reason": reason
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to reject submission: {e}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reject submission: {str(e)}"
        )


# ============================================================================
# AGENT ARCHITECT ASSISTANT - Interactive Agent Design
# ============================================================================

@router.post("/assist/start")
async def start_agent_design_assistance(
    request: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """
    Start an interactive agent design session.

    The Agent Architect will guide you through creating a high-quality
    agent sheet by asking questions and converting your responses into
    a validated JSON specification.

    Request body:
    {
        "description": "I want an agent to help with customer support tickets"
    }
    """
    try:
        description = request.get("description", "")
        if not description:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Description is required"
            )

        architect_service = AgentArchitectService(db)
        result = await architect_service.start_conversation(
            user_id=current_user.username,
            initial_request=description
        )

        logger.info(f"✅ Started agent design assistance for user: {current_user.username}")

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to start agent design assistance: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start assistance: {str(e)}"
        )


@router.post("/assist/continue")
async def continue_agent_design_assistance(
    request: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """
    Continue an interactive agent design session.

    Provide your response to the Agent Architect's question.

    Request body:
    {
        "conversation_id": "user123_1234567890.123",
        "response": "Yes, customer support specialist"
    }
    """
    try:
        conversation_id = request.get("conversation_id", "")
        user_response = request.get("response", "")

        if not conversation_id or not user_response:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="conversation_id and response are required"
            )

        architect_service = AgentArchitectService(db)
        result = await architect_service.continue_conversation(
            conversation_id=conversation_id,
            user_response=user_response
        )

        logger.info(f"✅ Continued agent design conversation: {conversation_id}")

        return result

    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"❌ Failed to continue agent design assistance: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to continue assistance: {str(e)}"
        )

