
"""
Tool Registry MCP Server for ROO-Forge

Integrates with DRYAD Tool Registry Service for GAD agent tool access,
validation, and permission management. Supports the Guardian (Layer 2) role
for quality enforcement and tool validation.
"""

import logging
from typing import Any, Dict, List, Optional

from .base_mcp import BaseMCPServer

logger = logging.getLogger(__name__)


class RegistryMCPServer(BaseMCPServer):
    """
    MCP Server for DRYAD Tool Registry Service integration.
    
    Provides GAD agent tool validation, access management, and
    security enforcement through DRYAD's Tool Registry API.
    """
    
    def __init__(self):
        super().__init__(
            name="tool_registry",
            description="DRYAD Tool Registry Service integration for GAD agent tool access and validation"
        )
        
    async def _list_tools(self):
        """List Tool Registry MCP tools"""
        return [
            {
                "name": "validate_tool_request",
                "description": "Validate tool request for GAD agent (Guardian function)",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "tool_id": {"type": "string", "description": "Tool ID to validate"},
                        "agent_category": {"type": "string", "description": "GAD agent category (orchestrator, reviewer, executor, supervisor)"},
                        "agent_name": {"type": "string", "description": "Agent name requesting tool"},
                        "use_case": {"type": "string", "description": "Intended use case for the tool"}
                    },
                    "required": ["tool_id", "agent_category"]
                }
            },
            {
                "name": "get_available_tools",
                "description": "Get available tools for GAD agent role",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "gad_role": {"type": "string", "description": "GAD role (forest-keeper, guardian-reviewer, branch-weaver, human-provost)"},
                        "category": {"type": "string", "description": "Tool category filter"},
                        "status": {"type": "string", "enum": ["active", "deprecated", "all"], "description": "Tool status", "default": "active"}
                    },
                    "required": ["gad_role"]
                }
            },
            {
                "name": "request_tool_approval",
                "description": "Request approval for restricted tool usage",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "tool_id": {"type": "string", "description": "Tool ID to request approval for"},
                        "agent_name": {"type": "string", "description": "Agent name"},
                        "gad_role": {"type": "string", "description": "GAD role"},
                        "justification": {"type": "string", "description": "Justification for tool usage"},
                        "risk_assessment": {"type": "string", "description": "Risk assessment"}
                    },
                    "required": ["tool_id", "agent_name", "gad_role", "justification"]
                }
            },
            {
                "name": "check_tool_permissions",
                "description": "Check agent permissions for specific tools",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "agent_name": {"type": "string", "description": "Agent name"},
                        "gad_role": {"type": "string", "description": "GAD role"},
                        "tool_ids": {"type": "array", "items": {"type": "string"}, "description": "List of tool IDs to check"}
                    },
                    "required": ["agent_name", "gad_role", "tool_ids"]
                }
            },
            {
                "name": "get_tool_usage_analytics",
                "description": "Get tool usage analytics for GAD agents",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "timeframe": {"type": "string", "description": "Timeframe (1h, 24h, 7d, 30d)", "default": "24h"},
                        "gad_role": {"type": "string", "description": "Filter by GAD role"},
                        "tool_category": {"type": "string", "description": "Filter by tool category"}
                    }
                }
            },
            {
                "name": "enforce_security_policy",
                "description": "Enforce security policy for GAD agent operations",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "operation": {"type": "string", "description": "Operation to check"},
                        "agent_name": {"type": "string", "description": "Agent name"},
                        "gad_role": {"type": "string", "description": "GAD role"},
                        "context": {"type": "object", "description": "Operation context"}
                    },
                    "required": ["operation", "agent_name", "gad_role"]
                }
            },
            {
                "name": "manage_tool_access",
                "description": "Manage tool access permissions for GAD agents",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "agent_name": {"type": "string", "description": "Agent name"},
                        "gad_role": {"type": "string", "description": "GAD role"},
                        "tool_id": {"type": "string", "description": "Tool ID"},
                        "action": {"type": "string", "enum": ["grant", "revoke", "suspend"], "description": "Access action"},
                        "reason": {"type": "string", "description": "Reason for action"}
                    },
                    "required": ["agent_name", "gad_role", "tool_id", "action"]
                }
            }
        ]
        
    async def _call_tool(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Handle Tool Registry tool execution"""
        
        if name == "validate_tool_request":
            return await self._validate_tool_request(arguments)
        elif name == "get_available_tools":
            return await self._get_available_tools(arguments)
        elif name == "request_tool_approval":
            return await self._request_tool_approval(arguments)
        elif name == "check_tool_permissions":
            return await self._check_tool_permissions(arguments)
        elif name == "get_tool_usage_analytics":
            return await self._get_tool_usage_analytics(arguments)
        elif name == "enforce_security_policy":
            return await self._enforce_security_policy(arguments)
        elif name == "manage_tool_access":
            return await self._manage_tool_access(arguments)
        else:
            return {"status": "error", "message": f"Unknown tool: {name}"}
            
    async def _validate_tool_request(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Validate tool request for GAD agent"""
        try:
            validation_data = {
                "tool_id": args["tool_id"],
                "agent_category": args["agent_category"],
                "agent_name": args.get("agent_name", "unknown"),
                "use_case": args.get("use_case", ""),
                "validation_type": "gad_agent_request",
                "gad_integration": {
                    "hierarchy_level": self._get_agent_hierarchy_level(args["agent_category"]),
                    "phase_focus": self._get_phase_focus(args["agent_category"]),
                    "security_requirements": self._get_security_requirements(args["agent_category"])
                }
            }
            
            result = await self.dryad_request("POST", "/api/v1/tool-registry/validate", data=validation_data)
            
            return {
                "status": "success",
                "validation_id": result.get("validation_id"),
                "tool_id": args["tool_id"],
                "agent_category": args["agent_category"],
                "allowed": result.get("allowed", False),
                "approval_required": result.get("requires_approval", False),
                "constraints": result.get("constraints", []),
                "security_checks": result.get("security_validations", []),
                "risk_level": result.get("risk_level", "unknown"),
                "message": f"Tool validation completed for {args['agent_category']}"
