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
from datetime import datetime

# Import models from the correct location
from app.database.models.tool_registry import ToolRegistry, ToolPermission, ToolExecution, ToolSession
from app.services.tool_registry.schemas import (
    ToolCreate,
    ToolUpdate,
    ToolResponse,
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
        
        # Validate OpenAPI 3.0 schema (simplified validation)
        if not isinstance(tool_data.schema_json, dict):
            raise InvalidToolSchemaError("Schema must be a dictionary")
        
        if "openapi" not in tool_data.schema_json:
            raise InvalidToolSchemaError("Schema must contain 'openapi' field")
        
        # Create tool instance using the ToolRegistry model
        tool = ToolRegistry(
            name=tool_data.name,
            version=tool_data.version,
            description=tool_data.description,
            function_signature=tool_data.schema_json,
            permissions={},
            requires_sandbox=False,
            max_session_duration=300,
            stateful=False,
            active=True,
        )
        
        try:
            self.db.add(tool)
            await self.db.commit()
            await self.db.refresh(tool)
            logger.info(f"Tool registered successfully: {tool.id}")
            return ToolResponse(
                tool_id=tool.id,
                name=tool.name,
                version=tool.version,
                description=tool.description,
                schema_json=tool.function_signature,
                docker_image_uri=None,  # Not in ToolRegistry model
                created_at=tool.created_at,
                updated_at=tool.updated_at,
                is_active=tool.active,
            )
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
        stmt = select(ToolRegistry).where(
            and_(ToolRegistry.name == name, ToolRegistry.version == version)
        )
        result = await self.db.execute(stmt)
        tool = result.scalar_one_or_none()

        if not tool:
            raise ToolNotFoundError(name, version)

        return ToolResponse(
            tool_id=tool.id,
            name=tool.name,
            version=tool.version,
            description=tool.description,
            schema_json=tool.function_signature,
            docker_image_uri=None,
            created_at=tool.created_at,
            updated_at=tool.updated_at,
            is_active=tool.active,
        )

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
        stmt = select(ToolRegistry).where(ToolRegistry.id == tool_id)
        result = await self.db.execute(stmt)
        tool = result.scalar_one_or_none()

        if not tool:
            raise ToolNotFoundError(tool_id)

        return ToolResponse(
            tool_id=tool.id,
            name=tool.name,
            version=tool.version,
            description=tool.description,
            schema_json=tool.function_signature,
            docker_image_uri=None,
            created_at=tool.created_at,
            updated_at=tool.updated_at,
            is_active=tool.active,
        )
    
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
        stmt = select(ToolRegistry).where(ToolRegistry.name == name).order_by(ToolRegistry.created_at.desc())
        result = await self.db.execute(stmt)
        tools = result.scalars().all()
        
        if not tools:
            raise ToolNotFoundError(name)
        
        return [
            ToolResponse(
                tool_id=tool.id,
                name=tool.name,
                version=tool.version,
                description=tool.description,
                schema_json=tool.function_signature,
                docker_image_uri=None,
                created_at=tool.created_at,
                updated_at=tool.updated_at,
                is_active=tool.active,
            )
            for tool in tools
        ]
    
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
        stmt = select(ToolRegistry)
        if active_only:
            stmt = stmt.where(ToolRegistry.active == True)
        
        # Get total count
        count_stmt = select(func.count()).select_from(ToolRegistry)
        if active_only:
            count_stmt = count_stmt.where(ToolRegistry.active == True)
        total_result = await self.db.execute(count_stmt)
        total = total_result.scalar()
        
        # Get paginated results
        stmt = stmt.order_by(ToolRegistry.created_at.desc()).limit(limit).offset(offset)
        result = await self.db.execute(stmt)
        tools = result.scalars().all()
        
        return ToolListResponse(
            tools=[
                ToolResponse(
                    tool_id=tool.id,
                    name=tool.name,
                    version=tool.version,
                    description=tool.description,
                    schema_json=tool.function_signature,
                    docker_image_uri=None,
                    created_at=tool.created_at,
                    updated_at=tool.updated_at,
                    is_active=tool.active,
                )
                for tool in tools
            ],
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
        stmt = select(ToolRegistry).where(
            and_(ToolRegistry.name == name, ToolRegistry.version == version)
        )
        result = await self.db.execute(stmt)
        tool = result.scalar_one_or_none()
        
        if not tool:
            raise ToolNotFoundError(name, version)
        
        # Update only provided fields
        update_dict = update_data.model_dump(exclude_unset=True)
        for field, value in update_dict.items():
            if hasattr(tool, field):
                setattr(tool, field, value)
        
        tool.updated_at = datetime.utcnow()
        await self.db.commit()
        await self.db.refresh(tool)
        logger.info(f"Tool updated: {name} v{version}")

        return ToolResponse(
            tool_id=tool.id,
            name=tool.name,
            version=tool.version,
            description=tool.description,
            schema_json=tool.function_signature,
            docker_image_uri=None,
            created_at=tool.created_at,
            updated_at=tool.updated_at,
            is_active=tool.active,
        )

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
        stmt = select(ToolRegistry).where(
            and_(ToolRegistry.name == name, ToolRegistry.version == version)
        )
        result = await self.db.execute(stmt)
        tool = result.scalar_one_or_none()

        if not tool:
            raise ToolNotFoundError(name, version)

        # Create permission using the ToolPermission model
        permission = ToolPermission(
            tool_id=tool.id,
            principal_id=permission_data.principal_id,
            principal_type=permission_data.principal_type,
            permission_level="execute",  # Default permission level
        )

        try:
            self.db.add(permission)
            await self.db.commit()
            await self.db.refresh(permission)
            logger.info(
                f"Permission granted: {permission_data.principal_type}:"
                f"{permission_data.principal_id} -> {name} v{version}"
            )
            return ToolPermissionResponse(
                permission_id=permission.id,
                principal_id=permission.principal_id,
                principal_type=permission.principal_type,
                tool_id=permission.tool_id,
                allow_stateful_execution=False,  # Default value
                created_at=permission.created_at,
                created_by=None,
            )
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
        stmt = select(ToolRegistry).where(
            and_(ToolRegistry.name == name, ToolRegistry.version == version)
        )
        result = await self.db.execute(stmt)
        tool = result.scalar_one_or_none()

        if not tool:
            raise ToolNotFoundError(name, version)

        # Get permissions
        perm_stmt = select(ToolPermission).where(
            ToolPermission.tool_id == tool.id
        ).order_by(ToolPermission.created_at.desc())
        perm_result = await self.db.execute(perm_stmt)
        permissions = perm_result.scalars().all()

        return ToolPermissionListResponse(
            permissions=[
                ToolPermissionResponse(
                    permission_id=perm.id,
                    principal_id=perm.principal_id,
                    principal_type=perm.principal_type,
                    tool_id=perm.tool_id,
                    allow_stateful_execution=False,  # Default value
                    created_at=perm.created_at,
                    created_by=None,
                )
                for perm in permissions
            ],
            total=len(permissions),
        )

    async def delete_tool(self, name: str, version: str) -> None:
        """
        Delete a specific tool by name and version.
        
        Args:
            name: Tool name
            version: Tool version
            
        Raises:
            ToolNotFoundError: If tool not found
        """
        stmt = select(ToolRegistry).where(
            and_(ToolRegistry.name == name, ToolRegistry.version == version)
        )
        result = await self.db.execute(stmt)
        tool = result.scalar_one_or_none()
        
        if not tool:
            raise ToolNotFoundError(name, version)
        
        # Delete associated permissions first
        perm_stmt = select(ToolPermission).where(ToolPermission.tool_id == tool.id)
        perm_result = await self.db.execute(perm_stmt)
        permissions = perm_result.scalars().all()
        
        for permission in permissions:
            await self.db.delete(permission)
        
        # Delete the tool
        await self.db.delete(tool)
        await self.db.commit()
        logger.info(f"Tool deleted successfully: {name} v{version}")

    async def execute_tool(
        self,
        tool_id: str,
        input_data: dict,
        agent_id: str,
        user_id: str | None = None
    ) -> dict:
        """
        Execute a tool and record the execution.
        
        Args:
            tool_id: Tool ID to execute
            input_data: Input parameters for execution
            agent_id: ID of the agent executing the tool
            user_id: Optional user context
            
        Returns:
            Execution result
            
        Raises:
            ToolNotFoundError: If tool not found
        """
        # Get tool details
        stmt = select(ToolRegistry).where(ToolRegistry.id == tool_id)
        result = await self.db.execute(stmt)
        tool = result.scalar_one_or_none()
        
        if not tool:
            raise ToolNotFoundError(tool_id)
        
        # Validate input against tool schema (simplified validation)
        if tool.function_signature and isinstance(tool.function_signature, dict):
            # Basic validation - in production, this would be more sophisticated
            schema_paths = tool.function_signature.get("paths", {})
            if not any(paths for paths in schema_paths.values()):
                raise ValueError("Tool schema contains no valid paths")
        
        # Simulate tool execution (in real implementation, this would call the actual tool)
        import time
        start_time = time.time()
        
        # Create execution record using ToolExecution model
        execution = ToolExecution(
            tool_id=tool_id,
            session_id=None,  # No session for direct execution
            agent_id=agent_id,
            user_id=user_id,
            input_data=input_data,
            output_data={"result": f"Executed {tool.name} v{tool.version}", "timestamp": time.time()},
            execution_time_ms=int((time.time() - start_time) * 1000),
            status="completed",
            progress=1.0,
        )
        
        try:
            self.db.add(execution)
            
            # Update tool's last_used_at timestamp
            tool.last_used_at = datetime.utcnow()
            
            await self.db.commit()
            await self.db.refresh(execution)
            
            logger.info(f"Tool executed successfully: {tool.name} v{tool.version} by agent {agent_id}")
            
            return {
                "execution_id": execution.id,
                "tool_id": tool_id,
                "tool_name": tool.name,
                "tool_version": tool.version,
                "status": "completed",
                "execution_time_ms": execution.execution_time_ms,
                "output_data": execution.output_data,
                "created_at": execution.created_at.isoformat() if execution.created_at else None,
            }
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Tool execution failed: {e}")
            raise

    async def get_tool_history(
        self,
        tool_id: str,
        limit: int = 50,
        offset: int = 0
    ) -> dict:
        """
        Get execution history for a specific tool.
        
        Args:
            tool_id: Tool ID to get history for
            limit: Maximum number of records to return
            offset: Number of records to skip
            
        Returns:
            Paginated execution history
            
        Raises:
            ToolNotFoundError: If tool not found
        """
        # Verify tool exists
        stmt = select(ToolRegistry).where(ToolRegistry.id == tool_id)
        result = await self.db.execute(stmt)
        tool = result.scalar_one_or_none()
        
        if not tool:
            raise ToolNotFoundError(tool_id)
        
        # Get execution history
        count_stmt = select(func.count()).select_from(ToolExecution).where(ToolExecution.tool_id == tool_id)
        total_result = await self.db.execute(count_stmt)
        total = total_result.scalar()
        
        # Get paginated executions
        exec_stmt = select(ToolExecution).where(ToolExecution.tool_id == tool_id).order_by(ToolExecution.created_at.desc()).limit(limit).offset(offset)
        exec_result = await self.db.execute(exec_stmt)
        executions = exec_result.scalars().all()
        
        history_data = {
            "tool_id": tool_id,
            "tool_name": tool.name,
            "tool_version": tool.version,
            "executions": [
                {
                    "execution_id": exec.id,
                    "agent_id": exec.agent_id,
                    "user_id": exec.user_id,
                    "status": exec.status,
                    "execution_time_ms": exec.execution_time_ms,
                    "input_data": exec.input_data,
                    "output_data": exec.output_data,
                    "error_message": exec.error_message,
                    "created_at": exec.created_at.isoformat() if exec.created_at else None,
                    "started_at": exec.started_at.isoformat() if exec.started_at else None,
                    "completed_at": exec.completed_at.isoformat() if exec.completed_at else None,
                }
                for exec in executions
            ],
            "total": total,
            "limit": limit,
            "offset": offset,
        }
        
        logger.info(f"Retrieved execution history for tool: {tool.name} v{tool.version}")
        
        return history_data
