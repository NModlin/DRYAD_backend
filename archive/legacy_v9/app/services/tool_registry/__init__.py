"""
Tool Registry Service

Centralized, version-controlled repository for all available tools.
Provides tool registration, versioning, and permission management.
"""

from app.database.models.tool_registry import ToolRegistry as Tool, ToolPermission
from .schemas import (
    ToolCreate,
    ToolResponse,
    ToolUpdate,
    ToolPermissionCreate,
    ToolPermissionResponse,
    ToolListResponse,
)
from .service import ToolRegistryService
from .exceptions import (
    ToolNotFoundError,
    ToolAlreadyExistsError,
    InvalidToolSchemaError,
    PermissionAlreadyExistsError,
)

__all__ = [
    "Tool",
    "ToolPermission",
    "ToolCreate",
    "ToolResponse",
    "ToolUpdate",
    "ToolPermissionCreate",
    "ToolPermissionResponse",
    "ToolListResponse",
    "ToolRegistryService",
    "ToolNotFoundError",
    "ToolAlreadyExistsError",
    "InvalidToolSchemaError",
    "PermissionAlreadyExistsError",
]

