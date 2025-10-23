"""
Tool Registry Custom Exceptions

Custom exception classes for tool registry operations.
"""


class ToolRegistryError(Exception):
    """Base exception for tool registry errors."""
    pass


class ToolNotFoundError(ToolRegistryError):
    """Raised when a tool is not found in the registry."""
    
    def __init__(self, name: str, version: str | None = None):
        if version:
            message = f"Tool '{name}' version '{version}' not found"
        else:
            message = f"Tool '{name}' not found"
        super().__init__(message)
        self.name = name
        self.version = version


class ToolAlreadyExistsError(ToolRegistryError):
    """Raised when attempting to register a tool that already exists."""
    
    def __init__(self, name: str, version: str):
        message = f"Tool '{name}' version '{version}' already exists"
        super().__init__(message)
        self.name = name
        self.version = version


class InvalidToolSchemaError(ToolRegistryError):
    """Raised when a tool schema is invalid."""
    
    def __init__(self, message: str, validation_errors: list[str] | None = None):
        super().__init__(message)
        self.validation_errors = validation_errors or []


class PermissionAlreadyExistsError(ToolRegistryError):
    """Raised when a permission already exists."""
    
    def __init__(self, principal_id: str, principal_type: str, tool_name: str):
        message = f"Permission for {principal_type} '{principal_id}' on tool '{tool_name}' already exists"
        super().__init__(message)
        self.principal_id = principal_id
        self.principal_type = principal_type
        self.tool_name = tool_name


class PermissionNotFoundError(ToolRegistryError):
    """Raised when a permission is not found."""
    
    def __init__(self, permission_id: str):
        message = f"Permission '{permission_id}' not found"
        super().__init__(message)
        self.permission_id = permission_id

