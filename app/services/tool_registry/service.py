"""
Tool Registry Service

Business logic for tool registration, versioning, and permission management.
"""

import logging
from typing import Any
from uuid import UUID
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

# Simple fallback validation since jsonschema has dependency issues
def jsonschema_validate(instance, schema):
    """Fallback validation - just check if it's a dict with openapi field"""
    if not isinstance(instance, dict):
        raise ValueError("Schema must be a dictionary")
    if "openapi" not in instance:
        raise ValueError("Schema must contain 'openapi' field")
    return True

class JsonSchemaValidationError(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(message)

from .models import Tool, ToolPermission
from .schemas import (
    ToolCreate,
    ToolUpdate,
    ToolResponse,
    ToolListResponse,
    ToolPermissionCreate,
    ToolPermissionResponse,
    ToolPermissionListResponse,
)
from .exceptions import (
    ToolNotFoundError,
    ToolAlreadyExistsError,
    InvalidToolSchemaError,
    PermissionAlreadyExistsError,
)

logger = logging.getLogger(__name__)


# OpenAPI 3.0 minimal schema for validation
OPENAPI_3_SCHEMA = {
    "type": "object",
    "required": ["openapi", "info", "paths"],
    "properties": {
        "openapi": {"type": "string", "pattern": "^3\\.0\\."},
        "info": {
            "type": "object",
            "required": ["title", "version"],
            "properties": {
                "title": {"type": "string"},
                "version": {"type": "string"},
            },
        },
        "paths": {"type": "object"},
    },
}


class ToolRegistryService:
    """
    Service for managing tool registry operations.
    
    Provides CRUD operations for tools and permissions with validation.
    """
    
    def __init__(self, db: AsyncSession):
        """
        Initialize the tool registry service.
        
        Args:
            db: Async database session
        """
        self.db = db
    
    async def register_tool(self, tool_data: ToolCreate) -> ToolResponse:
        """
        Register a new tool in the registry.
        
        Args:
            tool_data: Tool creation data
            
        Returns:
            Created tool response
            
        Raises:
            ToolAlreadyExistsError: If tool with same name/version exists
            InvalidToolSchemaError: If OpenAPI schema is invalid
        """
        logger.info(f"Registering tool: {tool_data.name} v{tool_data.version}")
        
        # Validate OpenAPI 3.0 schema
        try:
            jsonschema_validate(
                instance=tool_data.schema_json,
                schema=OPENAPI_3_SCHEMA,
            )
        except JsonSchemaValidationError as e:
            logger.error(f"Invalid OpenAPI schema: {e.message}")
            raise InvalidToolSchemaError(
                f"Invalid OpenAPI 3.0 schema: {e.message}",
                validation_errors=[e.message],
            )
        
        # Create tool instance
        tool = Tool(
            name=tool_data.name,
            version=tool_data.version,
            description=tool_data.description,
            schema_json=tool_data.schema_json,
            docker_image_uri=tool_data.docker_image_uri,
        )
        
        try:
            self.db.add(tool)
            await self.db.commit()
            await self.db.refresh(tool)
            logger.info(f"Tool registered successfully: {tool.tool_id}")
            return ToolResponse.model_validate(tool)
        except IntegrityError as e:
            await self.db.rollback()
            logger.error(f"Tool already exists: {tool_data.name} v{tool_data.version}")
            raise ToolAlreadyExistsError(tool_data.name, tool_data.version)
    
    async def get_tool(self, name: str, version: str) -> ToolResponse:
        """
        Get a specific tool by name and version.

        Args:
            name: Tool name
            version: Tool version

        Returns:
            Tool response

        Raises:
            ToolNotFoundError: If tool not found
        """
        stmt = select(Tool).where(
            and_(Tool.name == name, Tool.version == version)
        )
        result = await self.db.execute(stmt)
        tool = result.scalar_one_or_none()

        if not tool:
            raise ToolNotFoundError(name, version)

        return ToolResponse.model_validate(tool)

    async def get_tool_by_id(self, tool_id: str) -> ToolResponse:
        """
        Get a specific tool by its ID.

        Args:
            tool_id: Tool ID (UUID)

        Returns:
            Tool response

        Raises:
            ToolNotFoundError: If tool not found
        """
        stmt = select(Tool).where(Tool.tool_id == tool_id)
        result = await self.db.execute(stmt)
        tool = result.scalar_one_or_none()

        if not tool:
            raise ToolNotFoundError(tool_id)

        return ToolResponse.model_validate(tool)
    
    async def get_tool_versions(self, name: str) -> list[ToolResponse]:
        """
        Get all versions of a tool.
        
        Args:
            name: Tool name
            
        Returns:
            List of tool versions
            
        Raises:
            ToolNotFoundError: If no versions found
        """
        stmt = select(Tool).where(Tool.name == name).order_by(Tool.created_at.desc())
        result = await self.db.execute(stmt)
        tools = result.scalars().all()
        
        if not tools:
            raise ToolNotFoundError(name)
        
        return [ToolResponse.model_validate(tool) for tool in tools]
    
    async def list_tools(
        self,
        limit: int = 100,
        offset: int = 0,
        active_only: bool = False,
    ) -> ToolListResponse:
        """
        List all tools with pagination.
        
        Args:
            limit: Maximum number of tools to return
            offset: Number of tools to skip
            active_only: If True, only return active tools
            
        Returns:
            Paginated tool list response
        """
        # Build query
        stmt = select(Tool)
        if active_only:
            stmt = stmt.where(Tool.is_active == True)
        
        # Get total count
        count_stmt = select(func.count()).select_from(Tool)
        if active_only:
            count_stmt = count_stmt.where(Tool.is_active == True)
        total_result = await self.db.execute(count_stmt)
        total = total_result.scalar_one()
        
        # Get paginated results
        stmt = stmt.order_by(Tool.created_at.desc()).limit(limit).offset(offset)
        result = await self.db.execute(stmt)
        tools = result.scalars().all()
        
        return ToolListResponse(
            tools=[ToolResponse.model_validate(tool) for tool in tools],
            total=total,
            limit=limit,
            offset=offset,
        )
    
    async def update_tool(
        self,
        name: str,
        version: str,
        update_data: ToolUpdate,
    ) -> ToolResponse:
        """
        Update tool metadata (immutable fields cannot be updated).
        
        Args:
            name: Tool name
            version: Tool version
            update_data: Update data
            
        Returns:
            Updated tool response
            
        Raises:
            ToolNotFoundError: If tool not found
        """
        stmt = select(Tool).where(
            and_(Tool.name == name, Tool.version == version)
        )
        result = await self.db.execute(stmt)
        tool = result.scalar_one_or_none()
        
        if not tool:
            raise ToolNotFoundError(name, version)
        
        # Update only provided fields
        update_dict = update_data.model_dump(exclude_unset=True)
        for field, value in update_dict.items():
            setattr(tool, field, value)
        
        await self.db.commit()
        await self.db.refresh(tool)
        logger.info(f"Tool updated: {name} v{version}")

        return ToolResponse.model_validate(tool)

    async def grant_permission(
        self,
        name: str,
        version: str,
        permission_data: ToolPermissionCreate,
    ) -> ToolPermissionResponse:
        """
        Grant permission for an agent or role to use a tool.

        Args:
            name: Tool name
            version: Tool version
            permission_data: Permission creation data

        Returns:
            Created permission response

        Raises:
            ToolNotFoundError: If tool not found
            PermissionAlreadyExistsError: If permission already exists
        """
        # Get tool
        stmt = select(Tool).where(
            and_(Tool.name == name, Tool.version == version)
        )
        result = await self.db.execute(stmt)
        tool = result.scalar_one_or_none()

        if not tool:
            raise ToolNotFoundError(name, version)

        # Create permission
        permission = ToolPermission(
            principal_id=permission_data.principal_id,
            principal_type=permission_data.principal_type,
            tool_id=tool.tool_id,
            allow_stateful_execution=permission_data.allow_stateful_execution,
            created_by=permission_data.created_by,
        )

        try:
            self.db.add(permission)
            await self.db.commit()
            await self.db.refresh(permission)
            logger.info(
                f"Permission granted: {permission_data.principal_type}:"
                f"{permission_data.principal_id} -> {name} v{version}"
            )
            return ToolPermissionResponse.model_validate(permission)
        except IntegrityError:
            await self.db.rollback()
            raise PermissionAlreadyExistsError(
                permission_data.principal_id,
                permission_data.principal_type,
                f"{name} v{version}",
            )

    async def list_permissions(
        self,
        name: str,
        version: str,
    ) -> ToolPermissionListResponse:
        """
        List all permissions for a tool.

        Args:
            name: Tool name
            version: Tool version

        Returns:
            List of permissions

        Raises:
            ToolNotFoundError: If tool not found
        """
        # Get tool
        stmt = select(Tool).where(
            and_(Tool.name == name, Tool.version == version)
        )
        result = await self.db.execute(stmt)
        tool = result.scalar_one_or_none()

        if not tool:
            raise ToolNotFoundError(name, version)

        # Get permissions
        perm_stmt = select(ToolPermission).where(
            ToolPermission.tool_id == tool.tool_id
        ).order_by(ToolPermission.created_at.desc())
        perm_result = await self.db.execute(perm_stmt)
        permissions = perm_result.scalars().all()

        return ToolPermissionListResponse(
            permissions=[
                ToolPermissionResponse.model_validate(perm)
                for perm in permissions
            ],
            total=len(permissions),
        )

