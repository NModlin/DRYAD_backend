"""
Base MCP Server Implementation for ROO-Forge

Provides common functionality for MCP servers connecting to DRYAD.AI backend.
Handles authentication, API communication, and MCP protocol compliance.
"""

import asyncio
import json
import logging
import os
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin

import httpx
from mcp.server import Server
from mcp.server.models import (
    CallToolRequest,
    CallToolResult,
    GetPromptRequest,
    GetPromptResult,
    ListPromptsRequest,
    ListPromptsResult,
    ListResourcesRequest,
    ListResourcesResult,
    ListToolsRequest,
    ListToolsResult,
    ReadResourceRequest,
    ReadResourceResult
)
from mcp.types import (
    CallToolRequest as MCPToolRequest,
    CallToolResult as MCPToolResult,
    GetPromptRequest as MCPGetPromptRequest,
    GetPromptResult as MCPGetPromptResult,
    ListPromptsRequest as MCPListPromptsRequest,
    ListPromptsResult as MCPListPromptsResult,
    ListResourcesRequest as MCPListResourcesRequest,
    ListResourcesResult as MCPListResourcesResult,
    ListToolsRequest as MCPListToolsRequest,
    ListToolsResult as MCPListToolsResult,
    ReadResourceRequest as MCPReadResourceRequest,
    ReadResourceResult as MCPReadResourceResult,
    TextContent,
    Tool as MCPTool,
    TextContent as MCPTextContent
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DryadConnectionError(Exception):
    """Exception raised when connection to DRYAD backend fails"""
    pass


class BaseMCPServer:
    """
    Base class for MCP servers that integrate with DRYAD.AI backend.
    
    Provides:
    - DRYAD API communication
    - Authentication handling
    - Error management
    - Common MCP functionality
    """
    
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        self.server = Server(name)
        
        # DRYAD connection settings
        self.dryad_base_url = os.getenv("DRYAD_API_URL", "http://localhost:8000")
        self.dryad_api_key = os.getenv("DRYAD_API_KEY", "")
        self.dryad_timeout = 30
        self.dryad_retry_count = 3
        
        # HTTP client for DRYAD API
        self._http_client = None
        
        # Register MCP handlers
        self._register_handlers()
        
    async def __aenter__(self):
        """Async context manager entry"""
        await self.start()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.stop()
        
    @property
    def http_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client for DRYAD API"""
        if self._http_client is None:
            headers = {
                "Authorization": f"Bearer {self.dryad_api_key}",
                "Content-Type": "application/json",
                "User-Agent": f"ROO-Forge-MCP/{self.name}"
            }
            self._http_client = httpx.AsyncClient(
                headers=headers,
                timeout=self.dryad_timeout
            )
        return self._http_client
        
    async def start(self):
        """Start the MCP server"""
        logger.info(f"Starting MCP server: {self.name}")
        
        # Test DRYAD connection
        try:
            await self._test_dryad_connection()
            logger.info(f"✅ Connected to DRYAD backend: {self.dryad_base_url}")
        except Exception as e:
            logger.warning(f"⚠️ DRYAD connection failed: {e}")
            logger.warning("MCP server will continue but DRYAD features may be limited")
            
    async def stop(self):
        """Stop the MCP server"""
        logger.info(f"Stopping MCP server: {self.name}")
        if self._http_client:
            await self._http_client.aclose()
            
    async def _test_dryad_connection(self):
        """Test connection to DRYAD backend"""
        try:
            async with self.http_client as client:
                response = await client.get(f"{self.dryad_base_url}/api/v1/health/status")
                response.raise_for_status()
        except Exception as e:
            raise DryadConnectionError(f"Failed to connect to DRYAD: {e}")
            
    async def dryad_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Make a request to DRYAD API
        
        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            endpoint: API endpoint path
            data: Request data
            params: Query parameters
            
        Returns:
            Response data as dictionary
        """
        url = urljoin(self.dryad_base_url + "/", endpoint.lstrip("/"))
        
        for attempt in range(self.dryad_retry_count):
            try:
                async with self.http_client as client:
                    if method.upper() == "GET":
                        response = await client.get(url, params=params)
                    elif method.upper() == "POST":
                        response = await client.post(url, json=data)
                    elif method.upper() == "PUT":
                        response = await client.put(url, json=data)
                    elif method.upper() == "DELETE":
                        response = await client.delete(url)
                    else:
                        raise ValueError(f"Unsupported HTTP method: {method}")
                        
                    response.raise_for_status()
                    return response.json()
                    
            except httpx.HTTPStatusError as e:
                logger.error(f"HTTP error {e.response.status_code}: {e.response.text}")
                if attempt == self.dryad_retry_count - 1:
                    raise
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
                
            except Exception as e:
                logger.error(f"Request failed: {e}")
                if attempt == self.dryad_retry_count - 1:
                    raise
                await asyncio.sleep(2 ** attempt)
                
        raise Exception(f"Failed to complete request after {self.dryad_retry_count} attempts")
        
    def _register_handlers(self):
        """Register MCP protocol handlers"""
        
        @self.server.list_tools()
        async def handle_list_tools(request: MCPListToolsRequest) -> MCPListToolsResult:
            """List available tools"""
            tools = await self._list_tools()
            return MCPListToolsResult(tools=tools)
            
        @self.server.call_tool()
        async def handle_call_tool(request: MCPToolRequest) -> MCPToolResult:
            """Handle tool execution requests"""
            try:
                result = await self._call_tool(request.name, request.arguments or {})
                return MCPToolResult(
                    content=[MCPTextContent(type="text", text=json.dumps(result, indent=2))],
                    is_error=False
                )
            except Exception as e:
                logger.error(f"Tool execution failed: {e}")
                return MCPToolResult(
                    content=[MCPTextContent(type="text", text=f"Error: {str(e)}")],
                    is_error=True
                )
                
        @self.server.list_resources()
        async def handle_list_resources(request: MCPListResourcesRequest) -> MCPListResourcesResult:
            """List available resources"""
            resources = await self._list_resources()
            return MCPListResourcesResult(resources=resources)
            
        @self.server.read_resource()
        async def handle_read_resource(request: MCPReadResourceRequest) -> MCPReadResourceResult:
            """Handle resource read requests"""
            try:
                content = await self._read_resource(request.uri)
                return MCPReadResourceResult(contents=[MCPTextContent(type="text", text=content)])
            except Exception as e:
                logger.error(f"Resource read failed: {e}")
                return MCPReadResourceResult(
                    contents=[MCPTextContent(type="text", text=f"Error: {str(e)}")],
                    is_error=True
                )
                
        @self.server.list_prompts()
        async def handle_list_prompts(request: MCPListPromptsRequest) -> MCPListPromptsResult:
            """List available prompts"""
            prompts = await self._list_prompts()
            return MCPListPromptsResult(prompts=prompts)
            
        @self.server.get_prompt()
        async def handle_get_prompt(request: MCPGetPromptRequest) -> MCPGetPromptResult:
            """Handle prompt generation requests"""
            try:
                prompt = await self._get_prompt(request.name, request.arguments or {})
                return MCPGetPromptResult(description=prompt["description"], arguments=prompt.get("arguments", []))
            except Exception as e:
                logger.error(f"Prompt generation failed: {e}")
                return MCPGetPromptResult(
                    description=f"Error generating prompt: {str(e)}",
                    arguments=[]
                )
                
    async def _list_tools(self) -> List[MCPTool]:
        """List tools - to be implemented by subclasses"""
        return []
        
    async def _call_tool(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Handle tool execution - to be implemented by subclasses"""
        return {"status": "not_implemented", "message": f"Tool {name} not implemented"}
        
    async def _list_resources(self) -> List:
        """List resources - to be implemented by subclasses"""
        return []
        
    async def _read_resource(self, uri: str) -> str:
        """Handle resource reading - to be implemented by subclasses"""
        return f"Resource {uri} not found"
        
    async def _list_prompts(self) -> List:
        """List prompts - to be implemented by subclasses"""
        return []
        
    async def _get_prompt(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Handle prompt generation - to be implemented by subclasses"""
        return {"description": f"Prompt {name} not implemented"}
        
    def get_app(self):
        """Get the MCP server application"""
        return self.server.get_app()