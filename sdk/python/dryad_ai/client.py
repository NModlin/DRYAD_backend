"""
DRYAD.AI Python Client

Main client class for interacting with the DRYAD.AI API.
"""

import asyncio
import json
import logging
from typing import Dict, List, Optional, Any, AsyncGenerator
from urllib.parse import urljoin

import httpx
import websockets

from .exceptions import APIError, ValidationError, RateLimitError, AuthenticationError
from .models import Conversation, Message, Document, Agent, Task, SystemHealth


logger = logging.getLogger(__name__)


class DRYAD.AIClient:
    """
    Main client for interacting with the DRYAD.AI API.
    
    Supports REST, GraphQL, and WebSocket APIs with automatic error handling,
    retry logic, and connection management.
    """
    
    def __init__(
        self,
        base_url: str = "http://localhost:8000",
        api_key: Optional[str] = None,
        timeout: int = 30,
        max_retries: int = 3
    ):
        """
        Initialize the DRYAD.AI client.
        
        Args:
            base_url: Base URL of the DRYAD.AI API
            api_key: API key for authentication (optional in development)
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
        """
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.timeout = timeout
        self.max_retries = max_retries
        
        # Initialize HTTP client
        headers = {"Content-Type": "application/json"}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
            
        self.http_client = httpx.AsyncClient(
            base_url=self.base_url,
            headers=headers,
            timeout=timeout
        )
        
        # WebSocket connection
        self._websocket = None
        self._websocket_url = f"ws://{base_url.split('://', 1)[1]}/api/v1/ws/ws"
    
    async def __aenter__(self):
        """Async context manager entry."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
    
    async def close(self):
        """Close all connections."""
        await self.http_client.aclose()
        if self._websocket:
            await self._websocket.close()
    
    def _handle_response(self, response: httpx.Response) -> Dict[str, Any]:
        """Handle HTTP response and raise appropriate exceptions."""
        if response.status_code == 200 or response.status_code == 201:
            return response.json()
        elif response.status_code == 400:
            raise ValidationError(response.json().get("message", "Validation error"))
        elif response.status_code == 401:
            raise AuthenticationError("Invalid API key")
        elif response.status_code == 429:
            raise RateLimitError("Rate limit exceeded")
        else:
            error_data = response.json() if response.content else {}
            raise APIError(
                f"API error {response.status_code}: {error_data.get('message', 'Unknown error')}"
            )
    
    # Agent Methods
    async def invoke_agent(
        self,
        input_text: str,
        conversation_id: Optional[str] = None,
        save_conversation: bool = False
    ) -> Dict[str, Any]:
        """
        Invoke the core AI agent with a query.
        
        Args:
            input_text: The input query for the agent
            conversation_id: Optional conversation ID to continue
            save_conversation: Whether to save the interaction
            
        Returns:
            Agent response with output and metadata
        """
        payload = {
            "input": input_text,
            "save_conversation": save_conversation
        }
        if conversation_id:
            payload["conversation_id"] = conversation_id
            
        response = await self.http_client.post("/api/v1/agent/invoke", json=payload)
        return self._handle_response(response)
    
    # Conversation Methods
    async def create_conversation(self, title: Optional[str] = None) -> Conversation:
        """Create a new conversation."""
        payload = {}
        if title:
            payload["title"] = title
            
        response = await self.http_client.post("/api/v1/history/conversations", json=payload)
        data = self._handle_response(response)
        return Conversation.from_dict(data)
    
    async def get_conversation(self, conversation_id: str) -> Conversation:
        """Get a specific conversation with all messages."""
        response = await self.http_client.get(f"/api/v1/history/conversations/{conversation_id}")
        data = self._handle_response(response)
        return Conversation.from_dict(data)
    
    async def list_conversations(
        self,
        limit: int = 10,
        offset: int = 0
    ) -> List[Conversation]:
        """List conversations with pagination."""
        params = {"limit": limit, "offset": offset}
        response = await self.http_client.get("/api/v1/history/conversations", params=params)
        data = self._handle_response(response)
        return [Conversation.from_dict(conv) for conv in data["conversations"]]
    
    async def add_message(
        self,
        conversation_id: str,
        role: str,
        content: str,
        tool_calls: Optional[str] = None,
        extra_data: Optional[Dict[str, Any]] = None
    ) -> Message:
        """Add a message to a conversation."""
        payload = {
            "role": role,
            "content": content
        }
        if tool_calls:
            payload["tool_calls"] = tool_calls
        if extra_data:
            payload["extra_data"] = extra_data
            
        response = await self.http_client.post(
            f"/api/v1/history/conversations/{conversation_id}/messages",
            json=payload
        )
        data = self._handle_response(response)
        return Message.from_dict(data)
    
    # Multi-Agent Methods
    async def get_agent_capabilities(self) -> Dict[str, Agent]:
        """Get information about available agents."""
        response = await self.http_client.get("/api/v1/multi-agent/capabilities")
        data = self._handle_response(response)
        return {
            name: Agent.from_dict(info) 
            for name, info in data["agents"].items()
        }
    
    async def execute_multi_agent_workflow(
        self,
        workflow_type: str,
        input_text: str,
        conversation_id: Optional[str] = None,
        save_conversation: bool = False
    ) -> Dict[str, Any]:
        """Execute a multi-agent workflow."""
        payload = {
            "workflow_type": workflow_type,
            "input": input_text,
            "save_conversation": save_conversation
        }
        if conversation_id:
            payload["conversation_id"] = conversation_id
            
        response = await self.http_client.post("/api/v1/multi-agent/execute", json=payload)
        return self._handle_response(response)
    
    # Document Methods
    async def upload_document(
        self,
        file_path: str,
        title: Optional[str] = None
    ) -> Document:
        """Upload a document for processing."""
        with open(file_path, "rb") as f:
            files = {"file": f}
            data = {}
            if title:
                data["title"] = title
                
            response = await self.http_client.post(
                "/api/v1/documents/upload",
                files=files,
                data=data
            )
            
        response_data = self._handle_response(response)
        return Document.from_dict(response_data)
    
    async def search_documents(
        self,
        query: str,
        limit: int = 5,
        score_threshold: Optional[float] = None,
        use_rag: bool = False
    ) -> Dict[str, Any]:
        """Search documents using semantic search."""
        payload = {
            "query": query,
            "limit": limit,
            "use_rag": use_rag
        }
        if score_threshold:
            payload["score_threshold"] = score_threshold
            
        response = await self.http_client.post("/api/v1/documents/search", json=payload)
        return self._handle_response(response)
    
    async def list_documents(
        self,
        limit: int = 10,
        offset: int = 0,
        search: Optional[str] = None
    ) -> List[Document]:
        """List documents with pagination."""
        params = {"limit": limit, "offset": offset}
        if search:
            params["search"] = search
            
        response = await self.http_client.get("/api/v1/documents", params=params)
        data = self._handle_response(response)
        return [Document.from_dict(doc) for doc in data["documents"]]
    
    # Orchestrator Methods
    async def get_orchestrator_capabilities(self) -> Dict[str, Any]:
        """Get orchestrator capabilities."""
        response = await self.http_client.get("/api/v1/orchestrator/capabilities")
        return self._handle_response(response)
    
    async def execute_task(
        self,
        task_type: str,
        payload: Dict[str, Any],
        execution_mode: str = "sync",
        priority: int = 1,
        timeout: Optional[int] = None
    ) -> Task:
        """Execute a task through the orchestrator."""
        request_payload = {
            "task_type": task_type,
            "payload": payload,
            "execution_mode": execution_mode,
            "priority": priority
        }
        if timeout:
            request_payload["timeout"] = timeout
            
        response = await self.http_client.post("/api/v1/orchestrator/execute", json=request_payload)
        data = self._handle_response(response)
        return Task.from_dict(data)
    
    async def get_task_status(self, task_id: str) -> Task:
        """Get the status of an asynchronous task."""
        response = await self.http_client.get(f"/api/v1/orchestrator/tasks/{task_id}/status")
        data = self._handle_response(response)
        return Task.from_dict(data)
    
    # GraphQL Methods
    async def graphql_query(self, query: str, variables: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Execute a GraphQL query."""
        payload = {"query": query}
        if variables:
            payload["variables"] = variables
            
        response = await self.http_client.post("/graphql", json=payload)
        return self._handle_response(response)
    
    # WebSocket Methods
    async def connect_websocket(self) -> None:
        """Connect to the WebSocket endpoint."""
        if self._websocket:
            return
            
        self._websocket = await websockets.connect(self._websocket_url)
        
        # Wait for connection established message
        message = await self._websocket.recv()
        data = json.loads(message)
        logger.info(f"WebSocket connected: {data}")
    
    async def subscribe_to_conversation(self, conversation_id: str) -> str:
        """Subscribe to conversation updates."""
        if not self._websocket:
            await self.connect_websocket()
            
        subscribe_message = {
            "type": "subscribe",
            "subscription_type": "conversation",
            "conversation_id": conversation_id
        }
        
        await self._websocket.send(json.dumps(subscribe_message))
        
        # Wait for subscription confirmation
        message = await self._websocket.recv()
        data = json.loads(message)
        return data.get("subscription_id")
    
    async def listen_for_updates(self) -> AsyncGenerator[Dict[str, Any], None]:
        """Listen for WebSocket updates."""
        if not self._websocket:
            raise RuntimeError("WebSocket not connected")
            
        async for message in self._websocket:
            yield json.loads(message)
    
    # System Methods
    async def get_system_health(self) -> SystemHealth:
        """Get system health status."""
        response = await self.http_client.get("/api/v1/realtime/system/status")
        data = self._handle_response(response)
        return SystemHealth.from_dict(data)
    
    async def get_realtime_info(self) -> Dict[str, Any]:
        """Get real-time API information."""
        response = await self.http_client.get("/api/v1/realtime/info")
        return self._handle_response(response)


# Convenience functions for quick usage
async def quick_chat(message: str, base_url: str = "http://localhost:8000") -> str:
    """Quick chat function for simple interactions."""
    async with DRYAD.AIClient(base_url=base_url) as client:
        response = await client.invoke_agent(message)
        return response["output"]


async def quick_search(query: str, base_url: str = "http://localhost:8000") -> List[Dict[str, Any]]:
    """Quick document search function."""
    async with DRYAD.AIClient(base_url=base_url) as client:
        response = await client.search_documents(query, use_rag=True)
        return response["results"]
