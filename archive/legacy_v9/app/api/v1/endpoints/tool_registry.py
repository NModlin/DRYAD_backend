"""
Tool Registry API Endpoints

FastAPI router for tool registry operations.
Level 0 Component - Foundation Service for DRYAD.AI Agent Evolution Architecture.
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.database import get_db
from app.services.tool_registry.service import ToolRegistryService
from app.services.tool_registry.schemas import (
    ToolCreate,
    ToolResponse,
    ToolUpdate,
    ToolListResponse,
    ToolPermissionCreate,
    ToolPermissionResponse,
    ToolPermissionListResponse,
)
from app.services.tool_registry.exceptions import (
    ToolNotFoundError,
    ToolAlreadyExistsError,
    InvalidToolSchemaError,
    PermissionAlreadyExistsError,
)
from app.core.security import get_current_user, User, require_permission

logger = logging.getLogger(__name__)
router = APIRouter()


def get_tool_registry_service(db: AsyncSession = Depends(get_db)) -> ToolRegistryService:
    """Dependency to get tool registry service instance."""
    return ToolRegistryService(db)


@router.post(
    "/tools",
    response_model=ToolResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new tool",
    description="Register a new tool with OpenAPI 3.0 schema validation",
)
async def register_tool(
    tool_data: ToolCreate,
    service: ToolRegistryService = Depends(get_tool_registry_service),
    current_user: User = Depends(get_current_user),
):
    """
    Register a new tool in the registry.

    Args:
        tool_data: Tool creation data with OpenAPI 3.0 schema
        service: Tool registry service instance

    Returns:
        Created tool response

    Raises:
        400: Invalid OpenAPI schema
        409: Tool with same name/version already exists
    """
    try:
        return await service.register_tool(tool_data)
    except InvalidToolSchemaError as e:
        logger.error(f"Invalid tool schema: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "message": str(e),
                "validation_errors": e.validation_errors,
            },
        )
    except ToolAlreadyExistsError as e:
        logger.error(f"Tool already exists: {e}")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        )


@router.get(
    "/tools",
    response_model=ToolListResponse,
    summary="List all tools",
    description="List all tools with pagination and filtering",
)
async def list_tools(
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of tools to return"),
    offset: int = Query(0, ge=0, description="Number of tools to skip"),
    active_only: bool = Query(False, description="Only return active tools"),
    service: ToolRegistryService = Depends(get_tool_registry_service),
    current_user: User = Depends(get_current_user),
):
    """
    List all tools with pagination.

    Args:
        limit: Maximum number of tools to return
        offset: Number of tools to skip
        active_only: If True, only return active tools
        service: Tool registry service instance

    Returns:
        Paginated list of tools
    """
    return await service.list_tools(limit=limit, offset=offset, active_only=active_only)


@router.get(
    "/tools/{name}",
    response_model=list[ToolResponse],
    summary="Get all versions of a tool",
    description="Get all versions of a tool by name",
)
async def get_tool_versions(
    name: str,
    service: ToolRegistryService = Depends(get_tool_registry_service),
    current_user: User = Depends(get_current_user),
):
    """
    Get all versions of a tool.

    Args:
        name: Tool name
        service: Tool registry service instance

    Returns:
        List of all tool versions

    Raises:
        404: Tool not found
    """
    try:
        return await service.get_tool_versions(name)
    except ToolNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.get(
    "/tools/{name}/{version}",
    response_model=ToolResponse,
    summary="Get specific tool version",
    description="Get a specific tool by name and version",
)
async def get_tool(
    name: str,
    version: str,
    service: ToolRegistryService = Depends(get_tool_registry_service),
    current_user: User = Depends(get_current_user),
):
    """
    Get a specific tool by name and version.

    Args:
        name: Tool name
        version: Tool version
        service: Tool registry service instance

    Returns:
        Tool response

    Raises:
        404: Tool not found
    """
    try:
        return await service.get_tool(name, version)
    except ToolNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.put(
    "/tools/{name}/{version}",
    response_model=ToolResponse,
    summary="Update tool metadata",
    description="Update tool metadata (name, version, and schema are immutable)",
)
async def update_tool(
    name: str,
    version: str,
    update_data: ToolUpdate,
    service: ToolRegistryService = Depends(get_tool_registry_service),
    current_user: User = Depends(get_current_user),
):
    """
    Update tool metadata.

    Note: name, version, and schema_json are immutable and cannot be updated.

    Args:
        name: Tool name
        version: Tool version
        update_data: Update data (description, is_active, docker_image_uri)
        service: Tool registry service instance

    Returns:
        Updated tool response

    Raises:
        404: Tool not found
    """
    try:
            # Check if user has admin permissions to update tools
            require_permission(current_user, "admin")
            return await service.update_tool(name, version, update_data)
        except ToolNotFoundError as e:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e),
            )


@router.post(
    "/tools/{name}/{version}/permissions",
    response_model=ToolPermissionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Grant tool permission",
    description="Grant permission for an agent or role to use a tool",
)
async def grant_permission(
    name: str,
    version: str,
    permission_data: ToolPermissionCreate,
    service: ToolRegistryService = Depends(get_tool_registry_service),
    current_user: User = Depends(get_current_user),
):
    """
    Grant permission for an agent or role to use a tool.

    Args:
        name: Tool name
        version: Tool version
        permission_data: Permission creation data
        service: Tool registry service instance
        current_user: Current authenticated user

    Returns:
        Created permission response

    Raises:
        404: Tool not found
        409: Permission already exists
    """
    try:
        # Check if user has admin permissions to grant tool permissions
        require_permission(current_user, "admin")
        return await service.grant_permission(name, version, permission_data)
    except ToolNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except PermissionAlreadyExistsError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        )


@router.get(
    "/tools/{name}/{version}/permissions",
    response_model=ToolPermissionListResponse,
    summary="List tool permissions",
    description="List all permissions for a specific tool",
)
async def list_permissions(
    name: str,
    version: str,
    service: ToolRegistryService = Depends(get_tool_registry_service),
    current_user: User = Depends(get_current_user),
):
    """
    List all permissions for a tool.

    Args:
        name: Tool name
        version: Tool version
        service: Tool registry service instance

    Returns:
        List of permissions

    Raises:
        404: Tool not found
    """
    try:
        return await service.list_permissions(name, version)
    except ToolNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
@router.delete(
    "/tools/{name}/{version}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a tool",
    description="Delete a specific tool by name and version",
)
async def delete_tool(
    name: str,
    version: str,
    service: ToolRegistryService = Depends(get_tool_registry_service),
    current_user: User = Depends(get_current_user),
):
    """
    Delete a specific tool by name and version.

    Args:
        name: Tool name
        version: Tool version
        service: Tool registry service instance
        current_user: Current authenticated user

    Returns:
        No content on success

    Raises:
        404: Tool not found
    """
    try:
        # Check if user has admin permissions to delete tools
        require_permission(current_user, "admin")
        await service.delete_tool(name, version)
        return {"message": "Tool deleted successfully"}
    except ToolNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.post(
    "/tools/{tool_id}/execute",
    response_model=dict,
    status_code=status.HTTP_201_CREATED,
    summary="Execute a tool",
    description="Execute a registered tool with input parameters",
)
async def execute_tool(
    tool_id: str,
    input_data: dict,
    agent_id: str = Query(..., description="Agent executing the tool"),
    user_id: str | None = Query(None, description="Optional user context"),
    service: ToolRegistryService = Depends(get_tool_registry_service),
):
    """
    Execute a registered tool with the provided input data.

    Args:
        tool_id: Tool ID to execute
        input_data: Input parameters for tool execution
        agent_id: ID of the agent executing the tool
        user_id: Optional user context
        service: Tool registry service instance

    Returns:
        Execution result

    Raises:
        404: Tool not found
        400: Invalid input data
    """
    try:
        execution_result = await service.execute_tool(
            tool_id=tool_id,
            input_data=input_data,
            agent_id=agent_id,
            user_id=user_id
        )
        return execution_result
    except ToolNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.get(
    "/tools/{tool_id}/history",
    response_model=dict,
    summary="Get tool execution history",
    description="Get execution history for a specific tool",
)
async def get_tool_history(
    tool_id: str,
    limit: int = Query(50, ge=1, le=1000, description="Maximum number of history records"),
    offset: int = Query(0, ge=0, description="Number of records to skip"),
    service: ToolRegistryService = Depends(get_tool_registry_service),
):
    """
    Get execution history for a specific tool.

    Args:
        tool_id: Tool ID to get history for
        limit: Maximum number of history records to return
        offset: Number of records to skip
        service: Tool registry service instance

    Returns:
        Paginated execution history

    Raises:
        404: Tool not found
    """
    try:
        return await service.get_tool_history(tool_id, limit=limit, offset=offset)
    except ToolNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )

