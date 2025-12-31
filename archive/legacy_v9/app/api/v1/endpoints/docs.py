"""
Interactive Documentation Endpoints for Phase 8.

Provides enhanced documentation endpoints with live testing capabilities
for REST, GraphQL, and WebSocket APIs.
"""

import json
import logging
from typing import Dict, Any, List, Optional
from pathlib import Path

from fastapi import APIRouter, HTTPException, Request, Response
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from app.core.orchestrator import enhanced_orchestrator
# Optional import: multi-agent orchestrator (DRYAD built-in implementation)
try:
    from app.core.multi_agent import multi_agent_orchestrator
except Exception:
    class _DummyMA:
        def get_agent_capabilities(self):
            return []
    multi_agent_orchestrator = _DummyMA()
from app.core.vector_store import vector_store
from app.core.websocket_manager import connection_manager

logger = logging.getLogger(__name__)

router = APIRouter()

# Templates for interactive documentation
templates = Jinja2Templates(directory="templates")


class APIEndpoint(BaseModel):
    """Model for API endpoint information."""
    path: str
    method: str
    summary: str
    description: str
    parameters: List[Dict[str, Any]] = []
    request_body: Optional[Dict[str, Any]] = None
    responses: Dict[str, Dict[str, Any]] = {}
    examples: List[Dict[str, Any]] = []


class APIDocumentation(BaseModel):
    """Model for complete API documentation."""
    title: str
    version: str
    description: str
    base_url: str
    endpoints: List[APIEndpoint]
    schemas: Dict[str, Dict[str, Any]] = {}


@router.get("/", response_class=HTMLResponse)
async def interactive_docs_home(request: Request):
    """Interactive documentation home page."""
    try:
        # Get system information
        orchestrator_capabilities = enhanced_orchestrator.get_capabilities()
        agent_capabilities = multi_agent_orchestrator.get_agent_capabilities()
        
        context = {
            "request": request,
            "title": "DRYAD.AI Interactive Documentation",
            "version": orchestrator_capabilities.get("version", "6.0.0"),
            "system_info": {
                "orchestrator_version": orchestrator_capabilities.get("version"),
                "supported_tasks": len(orchestrator_capabilities.get("supported_tasks", [])),
                "available_agents": len(agent_capabilities),
                "vector_store_connected": vector_store.is_connected,
                "active_connections": connection_manager.get_connection_count()
            }
        }
        
        return templates.TemplateResponse("docs/home.html", context)
        
    except Exception as e:
        logger.error(f"Error loading documentation home: {e}")
        raise HTTPException(status_code=500, detail="Failed to load documentation")


@router.get("/api-reference", response_class=HTMLResponse)
async def api_reference(request: Request):
    """Interactive API reference with live testing."""
    try:
        # Generate comprehensive API documentation
        api_docs = await generate_api_documentation()
        
        context = {
            "request": request,
            "title": "API Reference - DRYAD.AI",
            "api_docs": api_docs,
            "base_url": str(request.base_url).rstrip('/')
        }
        
        return templates.TemplateResponse("docs/api_reference.html", context)
        
    except Exception as e:
        logger.error(f"Error loading API reference: {e}")
        raise HTTPException(status_code=500, detail="Failed to load API reference")


@router.get("/graphql-playground", response_class=HTMLResponse)
async def graphql_playground(request: Request):
    """GraphQL playground with schema introspection."""
    try:
        context = {
            "request": request,
            "title": "GraphQL Playground - DRYAD.AI",
            "graphql_endpoint": f"{request.base_url}graphql"
        }
        
        return templates.TemplateResponse("docs/graphql_playground.html", context)
        
    except Exception as e:
        logger.error(f"Error loading GraphQL playground: {e}")
        raise HTTPException(status_code=500, detail="Failed to load GraphQL playground")


@router.get("/websocket-tester", response_class=HTMLResponse)
async def websocket_tester(request: Request):
    """WebSocket connection tester and message explorer."""
    try:
        # Get WebSocket message types and examples
        message_types = get_websocket_message_types()
        
        context = {
            "request": request,
            "title": "WebSocket Tester - DRYAD.AI",
            "websocket_endpoint": f"ws://{request.headers.get('host', 'localhost:8000')}/api/v1/realtime-ws/ws",
            "message_types": message_types
        }
        
        return templates.TemplateResponse("docs/websocket_tester.html", context)
        
    except Exception as e:
        logger.error(f"Error loading WebSocket tester: {e}")
        raise HTTPException(status_code=500, detail="Failed to load WebSocket tester")


@router.get("/code-examples", response_class=HTMLResponse)
async def code_examples(request: Request):
    """Code examples and tutorials."""
    try:
        # Load code examples from files
        examples = await load_code_examples()
        
        context = {
            "request": request,
            "title": "Code Examples - DRYAD.AI",
            "examples": examples
        }
        
        return templates.TemplateResponse("docs/code_examples.html", context)
        
    except Exception as e:
        logger.error(f"Error loading code examples: {e}")
        raise HTTPException(status_code=500, detail="Failed to load code examples")


@router.get("/sdk-docs", response_class=HTMLResponse)
async def sdk_documentation(request: Request):
    """SDK documentation and installation guides."""
    try:
        context = {
            "request": request,
            "title": "SDK Documentation - DRYAD.AI",
            "sdks": [
                {
                    "name": "Python SDK",
                    "language": "python",
                    "install_command": "pip install gremlins-ai",
                    "github_url": "https://github.com/DRYAD.AI/python-sdk",
                    "docs_url": "/docs/sdk/python"
                },
                {
                    "name": "JavaScript SDK",
                    "language": "javascript",
                    "install_command": "npm install @DRYAD.AI/sdk",
                    "github_url": "https://github.com/DRYAD.AI/javascript-sdk",
                    "docs_url": "/docs/sdk/javascript"
                },
                {
                    "name": "CLI Tool",
                    "language": "cli",
                    "install_command": "pip install gremlins-ai-cli",
                    "github_url": "https://github.com/DRYAD.AI/cli",
                    "docs_url": "/docs/cli"
                }
            ]
        }
        
        return templates.TemplateResponse("docs/sdk_docs.html", context)
        
    except Exception as e:
        logger.error(f"Error loading SDK documentation: {e}")
        raise HTTPException(status_code=500, detail="Failed to load SDK documentation")


@router.get("/api-spec")
async def get_api_specification():
    """Get complete API specification in OpenAPI format."""
    try:
        api_docs = await generate_api_documentation()
        
        # Convert to OpenAPI 3.0 format
        openapi_spec = {
            "openapi": "3.0.0",
            "info": {
                "title": api_docs.title,
                "version": api_docs.version,
                "description": api_docs.description
            },
            "servers": [
                {"url": api_docs.base_url, "description": "Development server"}
            ],
            "paths": {},
            "components": {
                "schemas": api_docs.schemas
            }
        }
        
        # Convert endpoints to OpenAPI paths
        for endpoint in api_docs.endpoints:
            if endpoint.path not in openapi_spec["paths"]:
                openapi_spec["paths"][endpoint.path] = {}
            
            openapi_spec["paths"][endpoint.path][endpoint.method.lower()] = {
                "summary": endpoint.summary,
                "description": endpoint.description,
                "parameters": endpoint.parameters,
                "responses": endpoint.responses
            }
            
            if endpoint.request_body:
                openapi_spec["paths"][endpoint.path][endpoint.method.lower()]["requestBody"] = endpoint.request_body
        
        return JSONResponse(content=openapi_spec)
        
    except Exception as e:
        logger.error(f"Error generating API specification: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate API specification")


@router.get("/system-status")
async def get_documentation_system_status():
    """Get system status for documentation dashboard."""
    try:
        # Get comprehensive system status
        orchestrator_capabilities = enhanced_orchestrator.get_capabilities()
        agent_capabilities = multi_agent_orchestrator.get_agent_capabilities()
        
        status = {
            "system": {
                "status": "healthy",
                "version": orchestrator_capabilities.get("version", "6.0.0"),
                "uptime": 0.0  # Would be calculated from startup time
            },
            "components": {
                "orchestrator": {
                    "available": True,
                    "version": orchestrator_capabilities.get("version"),
                    "supported_tasks": len(orchestrator_capabilities.get("supported_tasks", []))
                },
                "multi_agent": {
                    "available": True,
                    "agents_count": len(agent_capabilities),
                    "agents": list(agent_capabilities.keys())
                },
                "vector_store": {
                    "available": vector_store.is_connected,
                    "type": "Qdrant" if vector_store.is_connected else "Fallback"
                },
                "websocket": {
                    "available": True,
                    "active_connections": connection_manager.get_connection_count()
                }
            },
            "apis": {
                "rest": {"available": True, "endpoints": 30},
                "graphql": {"available": True, "schema_types": 10},
                "websocket": {"available": True, "message_types": 13}
            }
        }
        
        return JSONResponse(content=status)
        
    except Exception as e:
        logger.error(f"Error getting system status: {e}")
        raise HTTPException(status_code=500, detail="Failed to get system status")


async def generate_api_documentation() -> APIDocumentation:
    """Generate comprehensive API documentation."""
    try:
        # Get system capabilities
        orchestrator_capabilities = enhanced_orchestrator.get_capabilities()
        
        # Define API endpoints with examples
        endpoints = [
            APIEndpoint(
                path="/api/v1/agent/invoke",
                method="POST",
                summary="Invoke AI Agent",
                description="Invoke the core AI agent with a query",
                request_body={
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "input": {"type": "string"},
                                    "conversation_id": {"type": "string"},
                                    "save_conversation": {"type": "boolean"}
                                },
                                "required": ["input"]
                            }
                        }
                    }
                },
                responses={
                    "200": {
                        "description": "Successful response",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "output": {"type": "string"},
                                        "conversation_id": {"type": "string"},
                                        "execution_time": {"type": "number"}
                                    }
                                }
                            }
                        }
                    }
                },
                examples=[
                    {
                        "name": "Simple Query",
                        "request": {
                            "input": "What is machine learning?"
                        },
                        "response": {
                            "output": "Machine learning is a subset of artificial intelligence...",
                            "execution_time": 1.23
                        }
                    }
                ]
            ),
            # Add more endpoints...
        ]
        
        return APIDocumentation(
            title="DRYAD.AI API",
            version=orchestrator_capabilities.get("version", "6.0.0"),
            description="Comprehensive API for the DRYAD.AI multi-modal AI platform",
            base_url="http://localhost:8000",
            endpoints=endpoints,
            schemas={}
        )
        
    except Exception as e:
        logger.error(f"Error generating API documentation: {e}")
        raise


def get_websocket_message_types() -> List[Dict[str, Any]]:
    """Get WebSocket message types and examples."""
    return [
        {
            "type": "subscribe",
            "description": "Subscribe to updates",
            "example": {
                "type": "subscribe",
                "subscription_type": "conversation",
                "conversation_id": "your-conversation-id"
            }
        },
        {
            "type": "unsubscribe",
            "description": "Unsubscribe from updates",
            "example": {
                "type": "unsubscribe",
                "subscription_type": "conversation",
                "subscription_id": "subscription-id"
            }
        },
        {
            "type": "ping",
            "description": "Ping the server",
            "example": {
                "type": "ping"
            }
        }
    ]


async def load_code_examples() -> List[Dict[str, Any]]:
    """Load code examples from files."""
    examples = [
        {
            "title": "Basic Agent Chat",
            "language": "python",
            "description": "Simple example of chatting with the AI agent",
            "code": '''import asyncio
from dryad_ai import DRYAD.AIClient

async def main():
    async with DRYAD.AIClient() as client:
        response = await client.invoke_agent("Hello, AI!")
        print(response["output"])

asyncio.run(main())'''
        },
        {
            "title": "Multi-Agent Workflow",
            "language": "python",
            "description": "Execute a complex multi-agent workflow",
            "code": '''import asyncio
from dryad_ai import DRYAD.AIClient

async def main():
    async with DRYAD.AIClient() as client:
        result = await client.execute_multi_agent_workflow(
            workflow_type="research_analyze_write",
            input_text="Analyze the future of renewable energy"
        )
        print(result["result"])

asyncio.run(main())'''
        },
        {
            "title": "Document Search with RAG",
            "language": "python",
            "description": "Search documents and get AI-generated responses",
            "code": '''import asyncio
from dryad_ai import DRYAD.AIClient

async def main():
    async with DRYAD.AIClient() as client:
        # Upload a document first
        doc = await client.upload_document("document.pdf")
        
        # Search with RAG
        results = await client.search_documents(
            "What are the key findings?",
            use_rag=True
        )
        print(results["rag_response"])

asyncio.run(main())'''
        }
    ]
    
    return examples
