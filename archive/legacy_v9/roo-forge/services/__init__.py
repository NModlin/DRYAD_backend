"""
ROO-Forge MCP Services

Model Context Protocol (MCP) servers that connect Roo Code to DRYAD.AI ecosystem.
Provides GAD (Governed Agentic Development) capabilities through the DRYAD backend.

Modules:
    base_mcp: Base MCP server implementation
    university_mcp: University system integration
    studio_mcp: Agent Creation Studio integration
    registry_mcp: Tool Registry Service integration
    knowledge_mcp: Knowledge Tree system integration
    multi_agent_mcp: Multi-agent collaboration integration
"""

from .base_mcp import BaseMCPServer
from .university_mcp import UniversityMCPServer
from .studio_mcp import StudioMCPServer
from .registry_mcp import RegistryMCPServer
from .knowledge_mcp import KnowledgeMCPServer
from .multi_agent_mcp import MultiAgentMCPServer

__all__ = [
    'BaseMCPServer',
    'UniversityMCPServer',
    'StudioMCPServer',
    'RegistryMCPServer',
    'KnowledgeMCPServer',
    'MultiAgentMCPServer'
]

__version__ = "1.0.0"
__author__ = "ROO-Forge Development Team"