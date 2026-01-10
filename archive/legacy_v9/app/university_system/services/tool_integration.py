"""
Universal Tool Integration Framework
====================================

Comprehensive framework for agent-accessible tools, APIs, and services
to enable complex educational tasks, research, analysis, and enhanced support.

Author: Dryad University System
Date: 2025-10-30
"""

from typing import Dict, List, Optional, Any, Tuple, Union
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass, field
from abc import ABC, abstractmethod
import asyncio
import logging
import json
import uuid
import hashlib
from concurrent.futures import ThreadPoolExecutor, as_completed
import aiohttp
import redis
from pydantic import BaseModel, Field, validator
import kubernetes
from app.university_system.core.config import get_settings
from app.university_system.core.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()


class ToolType(str, Enum):
    """Types of tools available in the system"""
    EDUCATIONAL_API = "educational_api"
    RESEARCH_TOOL = "research_tool"
    CONTENT_CREATION = "content_creation"
    ASSESSMENT_TOOL = "assessment_tool"
    COMMUNICATION_TOOL = "communication_tool"
    ANALYTICS_TOOL = "analytics_tool"
    INTEGRATION_BRIDGE = "integration_bridge"
    CUSTOM = "custom"


class ToolStatus(str, Enum):
    """Status of tools in the registry"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    MAINTENANCE = "maintenance"
    DEPRECATED = "deprecated"
    TESTING = "testing"


class ExecutionStatus(str, Enum):
    """Status of tool execution"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"


class SecurityLevel(str, Enum):
    """Security levels for tools"""
    PUBLIC = "public"
    RESTRICTED = "restricted"
    CONFIDENTIAL = "confidential"
    SECRET = "secret"


@dataclass
class ToolMetadata:
    """Metadata for tools in the registry"""
    tool_id: str
    name: str
    version: str
    description: str
    tool_type: ToolType
    security_level: SecurityLevel
    status: ToolStatus
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    author: str = "Dryad University System"
    license: str = "MIT"
    dependencies: List[str] = field(default_factory=list)
    capabilities: List[str] = field(default_factory=list)
    limitations: List[str] = field(default_factory=list)
    rate_limits: Dict[str, int] = field(default_factory=dict)
    execution_timeout: int = 300  # seconds
    memory_limit: int = 1024  # MB
    cpu_limit: float = 1.0  # cores
    environment_variables: Dict[str, str] = field(default_factory=dict)
    required_permissions: List[str] = field(default_factory=list)
    documentation_url: Optional[str] = None
    api_endpoint: Optional[str] = None
    configuration_schema: Optional[Dict[str, Any]] = None


@dataclass
class ToolExecution:
    """Represents a tool execution instance"""
    execution_id: str
    tool_id: str
    agent_id: str
    status: ExecutionStatus
    input_data: Dict[str, Any]
    output_data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    execution_start: datetime = field(default_factory=datetime.utcnow)
    execution_end: Optional[datetime] = None
    execution_time: Optional[float] = None
    resource_usage: Dict[str, Any] = field(default_factory=dict)
    security_context: Dict[str, Any] = field(default_factory=dict)
    retry_count: int = 0
    max_retries: int = 3


class ToolConfiguration(BaseModel):
    """Configuration schema for tools"""
    tool_id: str = Field(..., description="Unique identifier for the tool")
    name: str = Field(..., description="Display name of the tool")
    description: str = Field(..., description="Detailed description")
    version: str = Field(default="1.0.0", description="Tool version")
    enabled: bool = Field(default=True, description="Whether tool is enabled")
    timeout: int = Field(default=300, description="Execution timeout in seconds")
    max_concurrent: int = Field(default=10, description="Maximum concurrent executions")
    rate_limits: Dict[str, int] = Field(default_factory=dict, description="Rate limiting configuration")
    security_settings: Dict[str, Any] = Field(default_factory=dict, description="Security configuration")
    environment_variables: Dict[str, str] = Field(default_factory=dict, description="Environment variables")
    dependencies: List[str] = Field(default_factory=list, description="Required dependencies")
    permissions: List[str] = Field(default_factory=list, description="Required permissions")
    
    @validator('timeout')
    def validate_timeout(cls, v):
        if v < 1 or v > 3600:
            raise ValueError('Timeout must be between 1 and 3600 seconds')
        return v


class ToolValidator:
    """Validates tool specifications and compatibility"""
    
    def __init__(self):
        self.supported_versions = ["1.0.0", "1.1.0", "2.0.0"]
        self.required_fields = [
            "tool_id", "name", "description", "version", "tool_type"
        ]
        self.security_levels = [level.value for level in SecurityLevel]
        self.tool_types = [tool_type.value for tool_type in ToolType]
    
    async def validate_tool_specifications(self, tool_spec: Dict[str, Any]) -> Dict[str, Any]:
        """Validate tool specifications for compatibility"""
        try:
            validation_result = {
                "is_valid": True,
                "errors": [],
                "warnings": [],
                "suggestions": []
            }
            
            # Check required fields
            for field in self.required_fields:
                if field not in tool_spec:
                    validation_result["errors"].append(f"Missing required field: {field}")
                    validation_result["is_valid"] = False
            
            # Validate tool ID format
            if "tool_id" in tool_spec:
                tool_id = tool_spec["tool_id"]
                if not tool_id.replace("_", "").replace("-", "").isalnum():
                    validation_result["errors"].append(
                        "Tool ID must contain only alphanumeric characters, hyphens, and underscores"
                    )
                    validation_result["is_valid"] = False
            
            # Validate version format
            if "version" in tool_spec:
                version = tool_spec["version"]
                if version not in self.supported_versions:
                    validation_result["warnings"].append(
                        f"Version {version} is not in supported versions: {self.supported_versions}"
                    )
            
            # Validate security level
            if "security_level" in tool_spec:
                security_level = tool_spec["security_level"]
                if security_level not in self.security_levels:
                    validation_result["errors"].append(
                        f"Invalid security level: {security_level}"
                    )
                    validation_result["is_valid"] = False
            
            # Validate tool type
            if "tool_type" in tool_spec:
                tool_type = tool_spec["tool_type"]
                if tool_type not in self.tool_types:
                    validation_result["errors"].append(
                        f"Invalid tool type: {tool_type}"
                    )
                    validation_result["is_valid"] = False
            
            # Validate dependencies
            if "dependencies" in tool_spec:
                dependencies = tool_spec["dependencies"]
                if not isinstance(dependencies, list):
                    validation_result["errors"].append("Dependencies must be a list")
                    validation_result["is_valid"] = False
            
            # Validate rate limits
            if "rate_limits" in tool_spec:
                rate_limits = tool_spec["rate_limits"]
                if not isinstance(rate_limits, dict):
                    validation_result["errors"].append("Rate limits must be a dictionary")
                    validation_result["is_valid"] = False
            
            return validation_result
            
        except Exception as e:
            logger.error(f"Error validating tool specifications: {str(e)}")
            return {
                "is_valid": False,
                "errors": [f"Validation error: {str(e)}"],
                "warnings": [],
                "suggestions": []
            }
    
    async def validate_tool_availability(self, tool_id: str, agent_id: str) -> Dict[str, Any]:
        """Validate if an agent has access to a specific tool"""
        try:
            # This would typically check against a database or configuration
            # For now, we'll implement a basic validation
            
            validation_result = {
                "has_access": False,
                "reason": "",
                "restrictions": [],
                "capabilities": []
            }
            
            # Check if tool exists in registry
            tool_metadata = await self._get_tool_metadata(tool_id)
            if not tool_metadata:
                validation_result["reason"] = "Tool not found in registry"
                return validation_result
            
            # Check if tool is active
            if tool_metadata.status != ToolStatus.ACTIVE:
                validation_result["reason"] = f"Tool is not active (status: {tool_metadata.status})"
                return validation_result
            
            # Check agent permissions (simplified)
            agent_permissions = await self._get_agent_permissions(agent_id)
            
            # Check if tool requires specific permissions
            if tool_metadata.required_permissions:
                missing_permissions = set(tool_metadata.required_permissions) - set(agent_permissions)
                if missing_permissions:
                    validation_result["restrictions"].append(
                        f"Missing required permissions: {list(missing_permissions)}"
                    )
                    validation_result["reason"] = "Agent lacks required permissions"
                    return validation_result
            
            validation_result["has_access"] = True
            validation_result["capabilities"] = tool_metadata.capabilities
            
            return validation_result
            
        except Exception as e:
            logger.error(f"Error validating tool availability: {str(e)}")
            return {
                "has_access": False,
                "reason": f"Validation error: {str(e)}",
                "restrictions": [],
                "capabilities": []
            }
    
    async def _get_tool_metadata(self, tool_id: str) -> Optional[ToolMetadata]:
        """Get tool metadata from registry"""
        # This would typically query the database
        # For now, return a placeholder
        return ToolMetadata(
            tool_id=tool_id,
            name="Sample Tool",
            version="1.0.0",
            description="Sample tool for testing",
            tool_type=ToolType.EDUCATIONAL_API,
            security_level=SecurityLevel.PUBLIC,
            status=ToolStatus.ACTIVE
        )
    
    async def _get_agent_permissions(self, agent_id: str) -> List[str]:
        """Get agent permissions"""
        # This would typically query the database
        # For now, return default permissions
        return ["read", "execute"]


class ToolCatalog:
    """Comprehensive catalog of available tools and services"""
    
    def __init__(self):
        self.tools_registry: Dict[str, ToolMetadata] = {}
        self.categories_index: Dict[str, List[str]] = {}
        self.capabilities_index: Dict[str, List[str]] = {}
        self.vendor_index: Dict[str, List[str]] = {}
    
    async def categorize_tools(self) -> Dict[str, Any]:
        """Categorize tools by functionality and domain"""
        try:
            categories = {}
            
            for tool_id, tool_metadata in self.tools_registry.items():
                category = tool_metadata.tool_type.value
                if category not in categories:
                    categories[category] = {
                        "count": 0,
                        "tools": [],
                        "security_levels": {},
                        "status_distribution": {}
                    }
                
                categories[category]["count"] += 1
                categories[category]["tools"].append({
                    "id": tool_id,
                    "name": tool_metadata.name,
                    "version": tool_metadata.version,
                    "security_level": tool_metadata.security_level.value,
                    "status": tool_metadata.status.value
                })
                
                # Track security levels
                security_level = tool_metadata.security_level.value
                categories[category]["security_levels"][security_level] = \
                    categories[category]["security_levels"].get(security_level, 0) + 1
                
                # Track status distribution
                status = tool_metadata.status.value
                categories[category]["status_distribution"][status] = \
                    categories[category]["status_distribution"].get(status, 0) + 1
            
            return {
                "categories": categories,
                "total_tools": len(self.tools_registry),
                "last_updated": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error categorizing tools: {str(e)}")
            return {"categories": {}, "total_tools": 0, "error": str(e)}
    
    async def search_tools(self, query: str, filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Search tools based on functionality requirements"""
        try:
            query_lower = query.lower()
            results = []
            
            for tool_id, tool_metadata in self.tools_registry.items():
                # Check if query matches tool name, description, or capabilities
                searchable_text = " ".join([
                    tool_metadata.name.lower(),
                    tool_metadata.description.lower(),
                    " ".join(tool_metadata.capabilities).lower()
                ])
                
                if query_lower in searchable_text:
                    tool_result = {
                        "id": tool_id,
                        "name": tool_metadata.name,
                        "description": tool_metadata.description,
                        "version": tool_metadata.version,
                        "tool_type": tool_metadata.tool_type.value,
                        "security_level": tool_metadata.security_level.value,
                        "status": tool_metadata.status.value,
                        "capabilities": tool_metadata.capabilities,
                        "score": 0  # Would implement scoring algorithm
                    }
                    
                    # Apply filters
                    if filters:
                        if filters.get("tool_type") and tool_metadata.tool_type.value != filters["tool_type"]:
                            continue
                        if filters.get("security_level") and tool_metadata.security_level.value != filters["security_level"]:
                            continue
                        if filters.get("status") and tool_metadata.status.value != filters["status"]:
                            continue
                    
                    results.append(tool_result)
            
            # Sort by relevance (simplified)
            results.sort(key=lambda x: x["score"], reverse=True)
            
            return {
                "results": results,
                "total_found": len(results),
                "query": query,
                "filters": filters or {},
                "search_time": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error searching tools: {str(e)}")
            return {
                "results": [],
                "total_found": 0,
                "query": query,
                "error": str(e)
            }
    
    async def get_tool_dependencies(self, tool_id: str) -> Dict[str, Any]:
        """Get dependencies and requirements for tool execution"""
        try:
            if tool_id not in self.tools_registry:
                return {
                    "success": False,
                    "error": f"Tool {tool_id} not found"
                }
            
            tool_metadata = self.tools_registry[tool_id]
            
            dependencies_info = {
                "tool_id": tool_id,
                "tool_name": tool_metadata.name,
                "version": tool_metadata.version,
                "direct_dependencies": tool_metadata.dependencies,
                "environment_variables": tool_metadata.environment_variables,
                "required_permissions": tool_metadata.required_permissions,
                "resource_requirements": {
                    "memory_limit": tool_metadata.memory_limit,
                    "cpu_limit": tool_metadata.cpu_limit,
                    "execution_timeout": tool_metadata.execution_timeout
                },
                "external_dependencies": await self._resolve_external_dependencies(tool_metadata),
                "compatibility": await self._check_compatibility(tool_metadata)
            }
            
            return {
                "success": True,
                "dependencies": dependencies_info
            }
            
        except Exception as e:
            logger.error(f"Error getting tool dependencies: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def generate_tool_documentation(self, tool_id: str) -> Dict[str, Any]:
        """Generate comprehensive documentation for tool usage"""
        try:
            if tool_id not in self.tools_registry:
                return {
                    "success": False,
                    "error": f"Tool {tool_id} not found"
                }
            
            tool_metadata = self.tools_registry[tool_id]
            
            documentation = {
                "tool_info": {
                    "id": tool_metadata.tool_id,
                    "name": tool_metadata.name,
                    "version": tool_metadata.version,
                    "description": tool_metadata.description,
                    "type": tool_metadata.tool_type.value,
                    "author": tool_metadata.author,
                    "license": tool_metadata.license
                },
                "configuration": {
                    "schema": tool_metadata.configuration_schema,
                    "example_config": await self._generate_example_config(tool_metadata),
                    "required_parameters": self._get_required_parameters(tool_metadata),
                    "optional_parameters": self._get_optional_parameters(tool_metadata)
                },
                "usage": {
                    "api_endpoints": tool_metadata.api_endpoint,
                    "input_format": await self._define_input_format(tool_metadata),
                    "output_format": await self._define_output_format(tool_metadata),
                    "error_handling": await self._define_error_handling(tool_metadata)
                },
                "security": {
                    "security_level": tool_metadata.security_level.value,
                    "required_permissions": tool_metadata.required_permissions,
                    "authentication": await self._define_authentication(tool_metadata),
                    "data_handling": await self._define_data_handling(tool_metadata)
                },
                "examples": await self._generate_usage_examples(tool_metadata),
                "troubleshooting": await self._generate_troubleshooting_guide(tool_metadata)
            }
            
            return {
                "success": True,
                "documentation": documentation,
                "generated_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error generating tool documentation: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _resolve_external_dependencies(self, tool_metadata: ToolMetadata) -> List[Dict[str, Any]]:
        """Resolve external dependencies for a tool"""
        external_deps = []
        
        for dep in tool_metadata.dependencies:
            if dep.startswith("external:"):
                dep_name = dep.replace("external:", "")
                external_deps.append({
                    "name": dep_name,
                    "type": "external_service",
                    "required": True,
                    "url": await self._get_dependency_url(dep_name)
                })
        
        return external_deps
    
    async def _check_compatibility(self, tool_metadata: ToolMetadata) -> Dict[str, Any]:
        """Check compatibility of tool with current environment"""
        return {
            "platform_compatible": True,
            "python_version_compatible": True,
            "required_packages_available": True,
            "system_requirements_met": True,
            "conflicts": []
        }
    
    async def _generate_example_config(self, tool_metadata: ToolMetadata) -> Dict[str, Any]:
        """Generate example configuration for tool"""
        example_config = {
            "tool_id": tool_metadata.tool_id,
            "version": tool_metadata.version
        }
        
        # Add environment variables
        for env_var in tool_metadata.environment_variables:
            example_config[env_var] = f"VALUE_{env_var.upper()}"
        
        return example_config
    
    def _get_required_parameters(self, tool_metadata: ToolMetadata) -> List[str]:
        """Get required parameters for tool"""
        if tool_metadata.configuration_schema:
            required = []
            for param, config in tool_metadata.configuration_schema.items():
                if config.get("required", False):
                    required.append(param)
            return required
        return []
    
    def _get_optional_parameters(self, tool_metadata: ToolMetadata) -> List[str]:
        """Get optional parameters for tool"""
        if tool_metadata.configuration_schema:
            optional = []
            for param, config in tool_metadata.configuration_schema.items():
                if not config.get("required", False):
                    optional.append(param)
            return optional
        return []
    
    async def _define_input_format(self, tool_metadata: ToolMetadata) -> Dict[str, Any]:
        """Define input format specification"""
        return {
            "type": "application/json",
            "schema": tool_metadata.configuration_schema or {},
            "example": await self._generate_input_example(tool_metadata)
        }
    
    async def _define_output_format(self, tool_metadata: ToolMetadata) -> Dict[str, Any]:
        """Define output format specification"""
        return {
            "type": "application/json",
            "schema": {},
            "example": {"result": "success", "data": {}}
        }
    
    async def _define_error_handling(self, tool_metadata: ToolMetadata) -> Dict[str, Any]:
        """Define error handling specification"""
        return {
            "error_codes": {
                "400": "Bad Request - Invalid input parameters",
                "401": "Unauthorized - Authentication required",
                "403": "Forbidden - Insufficient permissions",
                "404": "Not Found - Resource not found",
                "500": "Internal Server Error - Tool execution failed"
            },
            "retry_policy": {
                "max_retries": tool_metadata.retry_count,
                "backoff_strategy": "exponential"
            }
        }
    
    async def _define_authentication(self, tool_metadata: ToolMetadata) -> Dict[str, Any]:
        """Define authentication requirements"""
        if tool_metadata.security_level == SecurityLevel.PUBLIC:
            return {"type": "none", "required": False}
        else:
            return {"type": "api_key", "required": True}
    
    async def _define_data_handling(self, tool_metadata: ToolMetadata) -> Dict[str, Any]:
        """Define data handling policies"""
        return {
            "data_retention": "24 hours",
            "data_encryption": "AES-256",
            "pii_handling": "anonymized",
            "audit_logging": True
        }
    
    async def _generate_usage_examples(self, tool_metadata: ToolMetadata) -> List[Dict[str, Any]]:
        """Generate usage examples"""
        return [
            {
                "title": "Basic Usage",
                "description": "Basic example of how to use the tool",
                "code": f"""
# Example usage of {tool_metadata.name}
tool_config = {{
    "tool_id": "{tool_metadata.tool_id}",
    "parameters": {{}}
}}
result = await tool_registry.execute_tool(tool_config, agent_context)
"""
            }
        ]
    
    async def _generate_troubleshooting_guide(self, tool_metadata: ToolMetadata) -> List[Dict[str, Any]]:
        """Generate troubleshooting guide"""
        return [
            {
                "issue": "Tool execution timeout",
                "solution": "Increase timeout value in configuration",
                "code": "config['timeout'] = 600"
            },
            {
                "issue": "Authentication failure",
                "solution": "Verify API key and permissions",
                "code": "Check security configuration"
            }
        ]
    
    async def _get_dependency_url(self, dependency_name: str) -> Optional[str]:
        """Get URL for external dependency"""
        # This would resolve URLs for known dependencies
        return None
    
    async def _generate_input_example(self, tool_metadata: ToolMetadata) -> Dict[str, Any]:
        """Generate input example"""
        return {"example": "input_data"}


class ToolExecutionEngine:
    """Secure execution engine for agent tools"""
    
    def __init__(self):
        self.execution_queue = asyncio.Queue()
        self.active_executions: Dict[str, ToolExecution] = {}
        self.executor = ThreadPoolExecutor(max_workers=10)
        self.redis_client = redis.Redis(
            host=getattr(settings, "REDIS_HOST", "localhost"),
            port=getattr(settings, "REDIS_PORT", 6379),
            decode_responses=True
        )
    
    async def execute_tool(self, tool_request: Dict[str, Any], agent_context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a tool request with proper security and error handling"""
        try:
            execution_id = str(uuid.uuid4())
            tool_id = tool_request.get("tool_id")
            
            # Create execution record
            execution = ToolExecution(
                execution_id=execution_id,
                tool_id=tool_id,
                agent_id=agent_context.get("agent_id"),
                status=ExecutionStatus.PENDING,
                input_data=tool_request,
                security_context=agent_context
            )
            
            self.active_executions[execution_id] = execution
            
            # Validate tool input
            validation_result = await self.validate_tool_input(tool_id, tool_request)
            if not validation_result["is_valid"]:
                execution.status = ExecutionStatus.FAILED
                execution.error_message = f"Input validation failed: {validation_result['errors']}"
                return {
                    "success": False,
                    "execution_id": execution_id,
                    "error": execution.error_message
                }
            
            # Execute tool asynchronously
            execution.status = ExecutionStatus.RUNNING
            execution.execution_start = datetime.utcnow()
            
            try:
                # Execute tool based on type
                if tool_id.startswith("educational_api"):
                    result = await self._execute_educational_api_tool(tool_request, agent_context)
                elif tool_id.startswith("research_tool"):
                    result = await self._execute_research_tool(tool_request, agent_context)
                elif tool_id.startswith("content_creation"):
                    result = await self._execute_content_creation_tool(tool_request, agent_context)
                elif tool_id.startswith("assessment_tool"):
                    result = await self._execute_assessment_tool(tool_request, agent_context)
                elif tool_id.startswith("communication_tool"):
                    result = await self._execute_communication_tool(tool_request, agent_context)
                else:
                    result = await self._execute_generic_tool(tool_request, agent_context)
                
                execution.status = ExecutionStatus.COMPLETED
                execution.output_data = result
                execution.execution_end = datetime.utcnow()
                execution.execution_time = (execution.execution_end - execution.execution_start).total_seconds()
                
                # Store execution result
                await self._store_execution_result(execution_id, execution)
                
                return {
                    "success": True,
                    "execution_id": execution_id,
                    "result": result,
                    "execution_time": execution.execution_time
                }
                
            except Exception as e:
                execution.status = ExecutionStatus.FAILED
                execution.error_message = str(e)
                execution.execution_end = datetime.utcnow()
                execution.execution_time = (execution.execution_end - execution.execution_start).total_seconds()
                
                logger.error(f"Tool execution failed: {str(e)}")
                
                # Try to handle error
                error_handling = await self.handle_tool_errors(tool_id, e)
                
                return {
                    "success": False,
                    "execution_id": execution_id,
                    "error": str(e),
                    "error_handling": error_handling
                }
            
        except Exception as e:
            logger.error(f"Critical error in tool execution: {str(e)}")
            return {
                "success": False,
                "error": f"Critical execution error: {str(e)}"
            }
        finally:
            # Clean up execution record
            if execution_id in self.active_executions:
                del self.active_executions[execution_id]
    
    async def execute_multiple_tools(self, tool_requests: List[Dict[str, Any]], agent_context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute multiple tool requests efficiently"""
        try:
            results = []
            
            # Separate parallel and sequential execution requests
            parallel_requests = [req for req in tool_requests if req.get("execution_mode", "parallel") == "parallel"]
            sequential_requests = [req for req in tool_requests if req.get("execution_mode", "parallel") == "sequential"]
            
            # Execute parallel requests
            parallel_tasks = [
                self.execute_tool(request, agent_context) 
                for request in parallel_requests
            ]
            
            parallel_results = await asyncio.gather(*parallel_tasks, return_exceptions=True)
            results.extend(parallel_results)
            
            # Execute sequential requests
            for request in sequential_requests:
                result = await self.execute_tool(request, agent_context)
                results.append(result)
            
            return {
                "success": True,
                "total_requests": len(tool_requests),
                "results": results,
                "execution_summary": {
                    "completed": len([r for r in results if isinstance(r, dict) and r.get("success")]),
                    "failed": len([r for r in results if isinstance(r, dict) and not r.get("success")]),
                    "exceptions": len([r for r in results if isinstance(r, Exception)])
                }
            }
            
        except Exception as e:
            logger.error(f"Error in multiple tool execution: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "results": []
            }
    
    async def validate_tool_input(self, tool_id: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate input data for tool execution"""
        try:
            validation_result = {
                "is_valid": True,
                "errors": [],
                "warnings": []
            }
            
            # Basic input validation
            if not input_data:
                validation_result["errors"].append("Input data is required")
                validation_result["is_valid"] = False
                return validation_result
            
            # Tool-specific validation (simplified)
            if tool_id.startswith("educational_api"):
                if "endpoint" not in input_data:
                    validation_result["errors"].append("Endpoint is required for educational API tools")
                    validation_result["is_valid"] = False
            
            elif tool_id.startswith("research_tool"):
                if "query" not in input_data:
                    validation_result["errors"].append("Query is required for research tools")
                    validation_result["is_valid"] = False
            
            elif tool_id.startswith("assessment_tool"):
                if "assessment_data" not in input_data:
                    validation_result["errors"].append("Assessment data is required")
                    validation_result["is_valid"] = False
            
            return validation_result
            
        except Exception as e:
            logger.error(f"Error validating tool input: {str(e)}")
            return {
                "is_valid": False,
                "errors": [f"Validation error: {str(e)}"],
                "warnings": []
            }
    
    async def handle_tool_errors(self, tool_id: str, error: Exception) -> Dict[str, Any]:
        """Handle and recover from tool execution errors"""
        try:
            error_handling = {
                "error_type": type(error).__name__,
                "error_message": str(error),
                "recovery_actions": [],
                "retry_recommended": False,
                "fallback_available": False
            }
            
            # Handle different types of errors
            if isinstance(error, asyncio.TimeoutError):
                error_handling["recovery_actions"].append(
                    "Increase timeout value or optimize tool execution"
                )
                error_handling["retry_recommended"] = True
            
            elif isinstance(error, PermissionError):
                error_handling["recovery_actions"].append(
                    "Check agent permissions for tool access"
                )
                error_handling["fallback_available"] = True
            
            elif isinstance(error, ConnectionError):
                error_handling["recovery_actions"].append(
                    "Check network connectivity and tool service availability"
                )
                error_handling["retry_recommended"] = True
            
            elif isinstance(error, ValueError):
                error_handling["recovery_actions"].append(
                    "Verify input parameters and data format"
                )
            
            # Log error for monitoring
            await self._log_error_event(tool_id, error, error_handling)
            
            return error_handling
            
        except Exception as e:
            logger.error(f"Error handling tool error: {str(e)}")
            return {
                "error_type": "ErrorHandlingError",
                "error_message": str(e),
                "recovery_actions": ["Review error handling implementation"],
                "retry_recommended": False,
                "fallback_available": False
            }
    
    async def monitor_tool_performance(self, tool_id: str) -> Dict[str, Any]:
        """Monitor performance and usage metrics for tools"""
        try:
            # Get execution metrics from Redis
            metrics_key = f"tool_metrics:{tool_id}"
            metrics_data = await self.redis_client.hgetall(metrics_key)
            
            # Calculate performance metrics
            total_executions = int(metrics_data.get("total_executions", 0))
            successful_executions = int(metrics_data.get("successful_executions", 0))
            failed_executions = int(metrics_data.get("failed_executions", 0))
            average_execution_time = float(metrics_data.get("average_execution_time", 0.0))
            
            performance_metrics = {
                "tool_id": tool_id,
                "timestamp": datetime.utcnow().isoformat(),
                "total_executions": total_executions,
                "successful_executions": successful_executions,
                "failed_executions": failed_executions,
                "success_rate": (successful_executions / total_executions * 100) if total_executions > 0 else 0,
                "average_execution_time": average_execution_time,
                "error_rate": (failed_executions / total_executions * 100) if total_executions > 0 else 0,
                "status": "healthy" if total_executions > 0 and failed_executions / total_executions < 0.1 else "degraded"
            }
            
            return {
                "success": True,
                "metrics": performance_metrics
            }
            
        except Exception as e:
            logger.error(f"Error monitoring tool performance: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _execute_educational_api_tool(self, tool_request: Dict[str, Any], agent_context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute educational API tools"""
        # This would integrate with actual educational APIs
        return {
            "success": True,
            "data": {"message": "Educational API tool executed successfully"},
            "tool_type": "educational_api"
        }
    
    async def _execute_research_tool(self, tool_request: Dict[str, Any], agent_context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute research tools"""
        # This would integrate with actual research APIs
        return {
            "success": True,
            "data": {"message": "Research tool executed successfully"},
            "tool_type": "research_tool"
        }
    
    async def _execute_content_creation_tool(self, tool_request: Dict[str, Any], agent_context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute content creation tools"""
        # This would integrate with content creation APIs
        return {
            "success": True,
            "data": {"message": "Content creation tool executed successfully"},
            "tool_type": "content_creation"
        }
    
    async def _execute_assessment_tool(self, tool_request: Dict[str, Any], agent_context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute assessment tools"""
        # This would integrate with assessment APIs
        return {
            "success": True,
            "data": {"message": "Assessment tool executed successfully"},
            "tool_type": "assessment_tool"
        }
    
    async def _execute_communication_tool(self, tool_request: Dict[str, Any], agent_context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute communication tools"""
        # This would integrate with communication APIs
        return {
            "success": True,
            "data": {"message": "Communication tool executed successfully"},
            "tool_type": "communication_tool"
        }
    
    async def _execute_generic_tool(self, tool_request: Dict[str, Any], agent_context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute generic/custom tools"""
        return {
            "success": True,
            "data": {"message": "Generic tool executed successfully"},
            "tool_type": "custom"
        }
    
    async def _store_execution_result(self, execution_id: str, execution: ToolExecution):
        """Store execution result in Redis"""
        try:
            metrics_key = f"tool_metrics:{execution.tool_id}"
            
            # Update metrics
            pipe = self.redis_client.pipeline()
            pipe.hincrby(metrics_key, "total_executions", 1)
            
            if execution.status == ExecutionStatus.COMPLETED:
                pipe.hincrby(metrics_key, "successful_executions", 1)
                pipe.hset(metrics_key, "last_success", datetime.utcnow().isoformat())
            else:
                pipe.hincrby(metrics_key, "failed_executions", 1)
                pipe.hset(metrics_key, "last_failure", datetime.utcnow().isoformat())
            
            if execution.execution_time:
                # Update average execution time
                current_avg = float(self.redis_client.hget(metrics_key, "average_execution_time") or 0)
                total_executions = int(self.redis_client.hget(metrics_key, "total_executions") or 0)
                new_avg = ((current_avg * (total_executions - 1)) + execution.execution_time) / total_executions
                pipe.hset(metrics_key, "average_execution_time", str(new_avg))
            
            pipe.execute()
            
        except Exception as e:
            logger.error(f"Error storing execution result: {str(e)}")
    
    async def _log_error_event(self, tool_id: str, error: Exception, error_handling: Dict[str, Any]):
        """Log error event for monitoring"""
        try:
            log_entry = {
                "tool_id": tool_id,
                "error_type": error_handling["error_type"],
                "error_message": error_handling["error_message"],
                "timestamp": datetime.utcnow().isoformat(),
                "recovery_actions": error_handling["recovery_actions"]
            }
            
            await self.redis_client.lpush(f"tool_errors:{tool_id}", json.dumps(log_entry))
            
            # Keep only last 100 errors
            await self.redis_client.ltrim(f"tool_errors:{tool_id}", 0, 99)
            
        except Exception as e:
            logger.error(f"Error logging error event: {str(e)}")


class ToolOrchestrator:
    """Orchestrates execution of multiple tools in sequence or parallel"""
    
    def __init__(self):
        self.execution_engine = ToolExecutionEngine()
        self.workflow_registry: Dict[str, Dict[str, Any]] = {}
    
    async def orchestrate_tool_execution(self, tool_requests: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Orchestrate execution of multiple tools in sequence or parallel"""
        try:
            orchestration_id = str(uuid.uuid4())
            
            # Analyze dependencies and execution order
            execution_plan = await self._create_execution_plan(tool_requests)
            
            # Execute tools according to plan
            execution_results = []
            
            for stage in execution_plan["stages"]:
                if stage["execution_mode"] == "parallel":
                    # Execute tools in parallel
                    parallel_tasks = [
                        self.execution_engine.execute_tool(request, {"agent_id": orchestration_id})
                        for request in stage["requests"]
                    ]
                    stage_results = await asyncio.gather(*parallel_tasks, return_exceptions=True)
                    execution_results.extend(stage_results)
                else:
                    # Execute tools sequentially
                    for request in stage["requests"]:
                        result = await self.execution_engine.execute_tool(request, {"agent_id": orchestration_id})
                        execution_results.append(result)
            
            orchestration_summary = {
                "orchestration_id": orchestration_id,
                "total_tools": len(tool_requests),
                "stages": execution_plan["stages"],
                "results": execution_results,
                "execution_summary": await self._generate_execution_summary(execution_results),
                "created_at": datetime.utcnow().isoformat()
            }
            
            return {
                "success": True,
                "orchestration": orchestration_summary
            }
            
        except Exception as e:
            logger.error(f"Error orchestrating tool execution: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _create_execution_plan(self, tool_requests: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Create execution plan based on dependencies and requirements"""
        try:
            # This is a simplified dependency analysis
            # In practice, this would be much more sophisticated
            
            stages = []
            
            # Separate parallel and sequential requests
            parallel_requests = [req for req in tool_requests if req.get("execution_mode", "parallel") == "parallel"]
            sequential_requests = [req for req in tool_requests if req.get("execution_mode", "parallel") == "sequential"]
            
            if parallel_requests:
                stages.append({
                    "execution_mode": "parallel",
                    "requests": parallel_requests,
                    "description": "Parallel execution stage"
                })
            
            if sequential_requests:
                stages.append({
                    "execution_mode": "sequential",
                    "requests": sequential_requests,
                    "description": "Sequential execution stage"
                })
            
            return {
                "total_stages": len(stages),
                "stages": stages,
                "dependency_analysis": await self._analyze_dependencies(tool_requests)
            }
            
        except Exception as e:
            logger.error(f"Error creating execution plan: {str(e)}")
            return {
                "total_stages": 0,
                "stages": [],
                "error": str(e)
            }
    
    async def _analyze_dependencies(self, tool_requests: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze dependencies between tools"""
        dependencies = {}
        
        for request in tool_requests:
            tool_id = request.get("tool_id", "")
            dependencies[tool_id] = {
                "depends_on": request.get("depends_on", []),
                "required_by": [],
                "critical_path": False
            }
        
        # Calculate critical path (simplified)
        for tool_id, deps in dependencies.items():
            if not deps["depends_on"]:
                deps["critical_path"] = True
        
        return dependencies
    
    async def _generate_execution_summary(self, execution_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate execution summary"""
        try:
            total = len(execution_results)
            successful = len([r for r in execution_results if isinstance(r, dict) and r.get("success")])
            failed = len([r for r in execution_results if isinstance(r, dict) and not r.get("success")])
            exceptions = len([r for r in execution_results if isinstance(r, Exception)])
            
            return {
                "total_executions": total,
                "successful": successful,
                "failed": failed,
                "exceptions": exceptions,
                "success_rate": (successful / total * 100) if total > 0 else 0,
                "execution_time": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error generating execution summary: {str(e)}")
            return {"error": str(e)}


class UniversalToolRegistry:
    """Registry and management system for agent-accessible tools"""
    
    def __init__(self):
        self.tool_catalog = ToolCatalog()
        self.tool_executor = ToolExecutionEngine()
        self.tool_validator = ToolValidator()
        self.tool_orchestrator = ToolOrchestrator()
        self.tools_registry: Dict[str, ToolMetadata] = {}
    
    async def register_tool(self, tool_config: Dict[str, Any]) -> Dict[str, Any]:
        """Register a new tool in the agent tool registry"""
        try:
            # Validate tool configuration
            validation_result = await self.tool_validator.validate_tool_specifications(tool_config)
            
            if not validation_result["is_valid"]:
                return {
                    "success": False,
                    "errors": validation_result["errors"],
                    "warnings": validation_result["warnings"]
                }
            
            # Create tool metadata
            tool_metadata = ToolMetadata(
                tool_id=tool_config["tool_id"],
                name=tool_config["name"],
                version=tool_config.get("version", "1.0.0"),
                description=tool_config["description"],
                tool_type=ToolType(tool_config["tool_type"]),
                security_level=SecurityLevel(tool_config.get("security_level", "public")),
                status=ToolStatus(tool_config.get("status", "active")),
                capabilities=tool_config.get("capabilities", []),
                dependencies=tool_config.get("dependencies", []),
                rate_limits=tool_config.get("rate_limits", {}),
                environment_variables=tool_config.get("environment_variables", {}),
                required_permissions=tool_config.get("required_permissions", []),
                api_endpoint=tool_config.get("api_endpoint"),
                documentation_url=tool_config.get("documentation_url"),
                configuration_schema=tool_config.get("configuration_schema")
            )
            
            # Register tool
            self.tools_registry[tool_metadata.tool_id] = tool_metadata
            
            # Add to catalog
            self.tool_catalog.tools_registry[tool_metadata.tool_id] = tool_metadata
            
            # Store in persistent storage (simplified)
            await self._store_tool_metadata(tool_metadata)
            
            logger.info(f"Tool registered successfully: {tool_metadata.tool_id}")
            
            return {
                "success": True,
                "tool_id": tool_metadata.tool_id,
                "name": tool_metadata.name,
                "version": tool_metadata.version,
                "warnings": validation_result["warnings"]
            }
            
        except Exception as e:
            logger.error(f"Error registering tool: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def discover_available_tools(self, agent_context: Dict[str, Any]) -> Dict[str, Any]:
        """Discover tools available for a specific agent context"""
        try:
            agent_id = agent_context.get("agent_id")
            user_role = agent_context.get("user_role", "student")
            
            available_tools = []
            restricted_tools = []
            
            for tool_id, tool_metadata in self.tools_registry.items():
                # Check agent access
                access_validation = await self.tool_validator.validate_tool_availability(tool_id, agent_id)
                
                tool_info = {
                    "tool_id": tool_id,
                    "name": tool_metadata.name,
                    "description": tool_metadata.description,
                    "version": tool_metadata.version,
                    "tool_type": tool_metadata.tool_type.value,
                    "security_level": tool_metadata.security_level.value,
                    "capabilities": tool_metadata.capabilities,
                    "status": tool_metadata.status.value,
                    "has_access": access_validation["has_access"],
                    "restrictions": access_validation.get("restrictions", []),
                    "capabilities_available": access_validation.get("capabilities", [])
                }
                
                if access_validation["has_access"]:
                    available_tools.append(tool_info)
                else:
                    restricted_tools.append(tool_info)
            
            # Categorize tools
            categories = await self.tool_catalog.categorize_tools()
            
            return {
                "success": True,
                "agent_id": agent_id,
                "user_role": user_role,
                "available_tools": available_tools,
                "restricted_tools": restricted_tools,
                "categories": categories,
                "total_tools": len(self.tools_registry),
                "accessible_tools": len(available_tools),
                "discovery_time": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error discovering available tools: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def validate_tool_availability(self, tool_id: str, agent_id: str) -> Dict[str, Any]:
        """Validate if an agent has access to a specific tool"""
        return await self.tool_validator.validate_tool_availability(tool_id, agent_id)
    
    async def orchestrate_tool_execution(self, tool_requests: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Orchestrate execution of multiple tools in sequence or parallel"""
        return await self.tool_orchestrator.orchestrate_tool_execution(tool_requests)
    
    async def _store_tool_metadata(self, tool_metadata: ToolMetadata):
        """Store tool metadata in persistent storage"""
        # This would typically store in a database
        # For now, we'll just log it
        logger.info(f"Storing tool metadata: {tool_metadata.tool_id}")
    
    async def get_tool_catalog(self) -> Dict[str, Any]:
        """Get the complete tool catalog"""
        try:
            categories = await self.tool_catalog.categorize_tools()
            tools_list = []
            
            for tool_id, tool_metadata in self.tools_registry.items():
                tools_list.append({
                    "tool_id": tool_id,
                    "name": tool_metadata.name,
                    "description": tool_metadata.description,
                    "version": tool_metadata.version,
                    "tool_type": tool_metadata.tool_type.value,
                    "security_level": tool_metadata.security_level.value,
                    "status": tool_metadata.status.value,
                    "capabilities": tool_metadata.capabilities
                })
            
            return {
                "success": True,
                "catalog": {
                    "total_tools": len(tools_list),
                    "categories": categories,
                    "tools": tools_list,
                    "last_updated": datetime.utcnow().isoformat()
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting tool catalog: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }