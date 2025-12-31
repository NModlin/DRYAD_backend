"""
Code Editor Agent API Endpoints
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.database import get_db
from app.services.code_editor_agent import CodeEditorAgent
from app.core.logging_config import get_logger

logger = get_logger(__name__)
router = APIRouter()

# Initialize agent
code_editor_agent = CodeEditorAgent()


# Request/Response Models
class CodeChange(BaseModel):
    """Represents a single code change."""
    old_code: str = Field(..., description="Code to replace")
    new_code: str = Field(..., description="New code to insert")
    description: Optional[str] = Field(None, description="Description of the change")


class EditCodeRequest(BaseModel):
    """Request to edit code."""
    file_path: str = Field(..., description="Path to file to edit")
    changes: List[CodeChange] = Field(..., description="List of changes to apply")
    validate: bool = Field(True, description="Whether to validate syntax after changes")
    create_backup: bool = Field(True, description="Whether to create backup before changes")
    branch_id: Optional[str] = Field(None, description="Optional DRYAD branch ID for context storage")


class EditCodeResponse(BaseModel):
    """Response from code editing."""
    success: bool
    file_path: Optional[str] = None
    changes_applied: Optional[int] = None
    validated: Optional[bool] = None
    error: Optional[str] = None


class ValidateSyntaxRequest(BaseModel):
    """Request to validate syntax."""
    file_path: str = Field(..., description="Path to file to validate")


class ValidateSyntaxResponse(BaseModel):
    """Response from syntax validation."""
    valid: bool
    file_path: Optional[str] = None
    error: Optional[str] = None
    line: Optional[int] = None
    offset: Optional[int] = None
    message: Optional[str] = None


class FormatCodeRequest(BaseModel):
    """Request to format code."""
    file_path: str = Field(..., description="Path to file to format")
    style: str = Field("black", description="Formatting style (black, autopep8)")


class FormatCodeResponse(BaseModel):
    """Response from code formatting."""
    success: bool
    file_path: Optional[str] = None
    formatted: Optional[bool] = None
    error: Optional[str] = None


# Endpoints
@router.post("/code-editor/edit", response_model=EditCodeResponse)
async def edit_code(
    request: EditCodeRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Edit code with validation and rollback support.
    
    This endpoint applies code changes to a file with:
    - Automatic backup creation
    - Syntax validation
    - Rollback on failure
    - DRYAD context storage
    """
    try:
        # Convert Pydantic models to dicts
        changes = [change.model_dump() for change in request.changes]
        
        result = await code_editor_agent.edit_code(
            db=db,
            file_path=request.file_path,
            changes=changes,
            validate=request.validate,
            create_backup=request.create_backup,
            branch_id=request.branch_id
        )
        
        return EditCodeResponse(**result)
    
    except Exception as e:
        logger.error(f"Error editing code: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/code-editor/validate", response_model=ValidateSyntaxResponse)
async def validate_syntax(request: ValidateSyntaxRequest):
    """
    Validate Python syntax.
    
    This endpoint validates the syntax of a Python file using AST parsing.
    """
    try:
        result = await code_editor_agent.validate_syntax(request.file_path)
        return ValidateSyntaxResponse(**result)
    
    except Exception as e:
        logger.error(f"Error validating syntax: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/code-editor/format", response_model=FormatCodeResponse)
async def format_code(request: FormatCodeRequest):
    """
    Format code using standard tools.
    
    This endpoint formats Python code using Black or autopep8.
    """
    try:
        # TODO: Implement code formatting
        # This would integrate with Black or autopep8
        return FormatCodeResponse(
            success=False,
            error="Code formatting not yet implemented"
        )
    
    except Exception as e:
        logger.error(f"Error formatting code: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/code-editor/capabilities")
async def get_capabilities():
    """
    Get Code Editor Agent capabilities.
    
    Returns information about the agent's capabilities and status.
    """
    try:
        return code_editor_agent.get_capabilities()
    
    except Exception as e:
        logger.error(f"Error getting capabilities: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/code-editor/health")
async def health_check():
    """
    Check Code Editor Agent health.
    
    Returns the current health status of the agent.
    """
    try:
        return await code_editor_agent.health_check()
    
    except Exception as e:
        logger.error(f"Error checking health: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

