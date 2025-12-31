"""
Sandbox API Endpoints - Level 1 Component

API endpoints for the Sandboxed Execution Environment.
Provides secure tool execution with resource monitoring.

Part of DRYAD.AI Agent Evolution Architecture Level 1.
"""

from typing import Dict, Any, Optional, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from app.database.database import get_db
from app.services.sandbox_service import SandboxExecutionEnvironment
from app.services.logging.logger import StructuredLogger
from app.core.security import get_current_user

router = APIRouter(prefix="/sandbox", tags=["sandbox"])
logger = StructuredLogger("sandbox_api")


# Pydantic schemas
class SandboxSessionCreate(BaseModel):
    """Schema for creating a sandbox session."""
    agent_id: str = Field(..., description="ID of the agent requesting the sandbox")
    tool_id: str = Field(..., description="ID of the tool to execute")
    timeout_seconds: Optional[int] = Field(300, description="Session timeout in seconds")
    resource_limits: Optional[Dict[str, Any]] = Field(None, description="Custom resource limits")


class SandboxSessionResponse(BaseModel):
    """Schema for sandbox session response."""
    session_id: str
    container_id: Optional[str]
    status: str
    expires_at: str
    resource_limits: Dict[str, Any]
    docker_available: bool


class SandboxExecutionRequest(BaseModel):
    """Schema for sandbox execution request."""
    command: str = Field(..., description="Command to execute")
    working_directory: Optional[str] = Field(None, description="Working directory")
    environment_variables: Optional[Dict[str, str]] = Field(None, description="Environment variables")
    input_parameters: Optional[Dict[str, Any]] = Field(None, description="Input parameters for tracking")


class SandboxExecutionResponse(BaseModel):
    """Schema for sandbox execution response."""
    execution_id: str
    success: bool
    stdout: str
    stderr: str
    exit_code: int
    execution_time_ms: int
    memory_usage_mb: Optional[int]
    cpu_usage_percent: Optional[int]
    resource_limits_enforced: bool


class SandboxSessionState(BaseModel):
    """Schema for sandbox session state."""
    session_id: str
    status: str
    container_id: Optional[str]
    sandbox_status: Optional[str]
    created_at: str
    expires_at: Optional[str]
    active_executions: int


@router.post("/sessions", response_model=SandboxSessionResponse)
async def create_sandbox_session(
    request: SandboxSessionCreate,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Create a new sandboxed execution session.
    
    Creates an isolated Docker container for secure tool execution
    with proper resource limits and monitoring.
    """
    try:
        sandbox_service = SandboxExecutionEnvironment(db)
        
        logger.log_info(
            "sandbox_session_create_request",
            {
                "agent_id": request.agent_id,
                "tool_id": request.tool_id,
                "user_id": current_user.get("user_id"),
                "timeout_seconds": request.timeout_seconds
            }
        )
        
        result = await sandbox_service.create_sandbox_session(
            agent_id=request.agent_id,
            tool_id=request.tool_id,
            timeout_seconds=request.timeout_seconds,
            resource_limits=request.resource_limits
        )
        
        return SandboxSessionResponse(**result)
        
    except ValueError as e:
        logger.log_warning(
            "sandbox_session_create_validation_error",
            {"error": str(e), "agent_id": request.agent_id}
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.log_error(
            "sandbox_session_create_error",
            {"error": str(e), "agent_id": request.agent_id}
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create sandbox session"
        )


@router.post("/sessions/{session_id}/execute", response_model=SandboxExecutionResponse)
async def execute_in_sandbox(
    session_id: str,
    request: SandboxExecutionRequest,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Execute a command in the sandbox session.
    
    Executes the command with comprehensive monitoring and tracking.
    """
    try:
        sandbox_service = SandboxExecutionEnvironment(db)
        
        logger.log_info(
            "sandbox_execution_request",
            {
                "session_id": session_id,
                "command": request.command[:100],  # Truncate for logging
                "user_id": current_user.get("user_id")
            }
        )
        
        result = await sandbox_service.execute_in_sandbox(
            session_id=session_id,
            command=request.command,
            working_directory=request.working_directory,
            environment_variables=request.environment_variables,
            input_parameters=request.input_parameters
        )
        
        return SandboxExecutionResponse(**result)
        
    except ValueError as e:
        logger.log_warning(
            "sandbox_execution_validation_error",
            {"error": str(e), "session_id": session_id}
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.log_error(
            "sandbox_execution_error",
            {"error": str(e), "session_id": session_id}
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to execute command in sandbox"
        )


@router.get("/sessions/{session_id}", response_model=SandboxSessionState)
async def get_sandbox_session(
    session_id: str,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Get the current state of a sandbox session.
    
    Returns session status, container information, and execution metrics.
    """
    try:
        sandbox_service = SandboxExecutionEnvironment(db)
        
        state = await sandbox_service.get_sandbox_state(session_id)
        
        return SandboxSessionState(**state)
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.log_error(
            "sandbox_session_get_error",
            {"error": str(e), "session_id": session_id}
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get sandbox session state"
        )


@router.delete("/sessions/{session_id}")
async def close_sandbox_session(
    session_id: str,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Close a sandbox session and clean up resources.
    
    Stops the container and marks the session as closed.
    """
    try:
        sandbox_service = SandboxExecutionEnvironment(db)
        
        await sandbox_service.close_sandbox_session(session_id)
        
        logger.log_info(
            "sandbox_session_closed",
            {"session_id": session_id, "user_id": current_user.get("user_id")}
        )
        
        return {"message": "Sandbox session closed successfully"}
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.log_error(
            "sandbox_session_close_error",
            {"error": str(e), "session_id": session_id}
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to close sandbox session"
        )


@router.get("/sessions")
async def list_sandbox_sessions(
    agent_id: Optional[str] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    List sandbox sessions with optional filtering.
    
    Returns a list of sessions matching the specified criteria.
    """
    try:
        sandbox_service = SandboxExecutionEnvironment(db)
        
        sessions = await sandbox_service.list_sandbox_sessions(
            agent_id=agent_id,
            status=status
        )
        
        return {"sessions": sessions}
        
    except Exception as e:
        logger.log_error(
            "sandbox_sessions_list_error",
            {"error": str(e), "agent_id": agent_id}
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list sandbox sessions"
        )
