from typing import List, Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from dryad.infrastructure.database import get_db
from dryad.domain.tool.schemas import ToolResponse, ToolCreate, ToolUpdate
from dryad.services.tool_registry import ToolRegistryService
from dryad.api.v1.auth import get_current_user
from dryad.domain.user.models import User

router = APIRouter()

@router.post("/", response_model=ToolResponse, status_code=status.HTTP_201_CREATED)
async def register_tool(
    tool_in: ToolCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """
    Register a new tool. (Authenticated users only)
    """
    service = ToolRegistryService(db)
    try:
        return await service.register_tool(tool_in)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/", response_model=List[ToolResponse])
async def list_tools(
    db: Annotated[AsyncSession, Depends(get_db)],
    skip: int = 0, 
    limit: int = 100
):
    """
    List all available tools.
    """
    service = ToolRegistryService(db)
    return await service.list_tools(skip=skip, limit=limit)

@router.get("/{tool_id}", response_model=ToolResponse)
async def get_tool(
    tool_id: str,
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """
    Get generic tool details.
    """
    service = ToolRegistryService(db)
    tool = await service.get_tool(tool_id)
    if not tool:
        raise HTTPException(status_code=404, detail="Tool not found")
    return tool
