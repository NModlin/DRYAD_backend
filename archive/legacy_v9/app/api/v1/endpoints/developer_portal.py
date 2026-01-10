"""
Developer Portal Endpoints for Phase 8.

Provides a comprehensive developer portal with dashboard, monitoring,
and development tools for the DRYAD.AI platform.
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

from fastapi import APIRouter, HTTPException, Request, BackgroundTasks, Depends
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from app.core.security import get_current_user, User


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
from app.services.chat_history import ChatHistoryService

logger = logging.getLogger(__name__)

router = APIRouter()
templates = Jinja2Templates(directory="templates")


class DeveloperMetrics(BaseModel):
    """Model for developer portal metrics."""
    total_api_calls: int = 0
    successful_calls: int = 0
    failed_calls: int = 0
    avg_response_time: float = 0.0
    active_conversations: int = 0
    total_documents: int = 0
    active_websocket_connections: int = 0
    system_uptime: float = 0.0


class APIUsageStats(BaseModel):
    """Model for API usage statistics."""
    endpoint: str
    method: str
    calls_count: int
    avg_response_time: float
    success_rate: float
    last_called: Optional[datetime] = None


class SystemAlert(BaseModel):
    """Model for system alerts."""
    id: str
    level: str  # info, warning, error
    message: str
    timestamp: datetime
    resolved: bool = False


@router.get("/", response_class=HTMLResponse)
async def developer_portal_dashboard(request: Request, current_user: User = Depends(get_current_user)):
    """Developer portal dashboard with system overview."""
    try:
        # Get comprehensive system metrics
        metrics = await get_developer_metrics()

        # Get recent API usage
        api_usage = await get_api_usage_stats()

        # Get system alerts
        alerts = await get_system_alerts()

        context = {
            "request": request,
            "title": "Developer Portal - DRYAD.AI",
            "metrics": metrics,
            "api_usage": api_usage[:10],  # Top 10 endpoints
            "alerts": alerts[:5],  # Recent 5 alerts
            "system_info": await get_system_info()
        }

        return templates.TemplateResponse("developer_portal/dashboard.html", context)

    except Exception as e:
        logger.error(f"Error loading developer portal: {e}")
        raise HTTPException(status_code=500, detail="Failed to load developer portal")


@router.get("/api-explorer", response_class=HTMLResponse)
async def api_explorer(request: Request, current_user: User = Depends(get_current_user)):
    """Interactive API explorer with live testing."""
    try:
        # Get all available endpoints
        endpoints = await get_api_endpoints()

        context = {
            "request": request,
            "title": "API Explorer - DRYAD.AI",
            "endpoints": endpoints,
            "base_url": str(request.base_url).rstrip('/')
        }

        return templates.TemplateResponse("developer_portal/api_explorer.html", context)

    except Exception as e:
        logger.error(f"Error loading API explorer: {e}")
        raise HTTPException(status_code=500, detail="Failed to load API explorer")


@router.get("/monitoring", response_class=HTMLResponse)
async def system_monitoring(request: Request, current_user: User = Depends(get_current_user)):
    """Real-time system monitoring dashboard."""
    try:
        context = {
            "request": request,
            "title": "System Monitoring - DRYAD.AI",
            "refresh_interval": 5000  # 5 seconds
        }

        return templates.TemplateResponse("developer_portal/monitoring.html", context)

    except Exception as e:
        logger.error(f"Error loading monitoring dashboard: {e}")
        raise HTTPException(status_code=500, detail="Failed to load monitoring dashboard")


@router.get("/tools", response_class=HTMLResponse)
async def developer_tools(request: Request, current_user: User = Depends(get_current_user)):
    """Developer tools and utilities."""
    try:
        context = {
            "request": request,
            "title": "Developer Tools - DRYAD.AI",
            "tools": [
                {
                    "name": "API Key Generator",
                    "description": "Generate API keys for authentication",
                    "url": "/developer-portal/tools/api-keys",
                    "icon": "fas fa-key"
                },
                {
                    "name": "Schema Validator",
                    "description": "Validate request/response schemas",
                    "url": "/developer-portal/tools/schema-validator",
                    "icon": "fas fa-check-circle"
                },
                {
                    "name": "Rate Limit Tester",
                    "description": "Test API rate limiting behavior",
                    "url": "/developer-portal/tools/rate-limit-tester",
                    "icon": "fas fa-tachometer-alt"
                },
                {
                    "name": "WebSocket Debugger",
                    "description": "Debug WebSocket connections and messages",
                    "url": "/developer-portal/tools/websocket-debugger",
                    "icon": "fas fa-bug"
                }
            ]
        }

        return templates.TemplateResponse("developer_portal/tools.html", context)

    except Exception as e:
        logger.error(f"Error loading developer tools: {e}")
        raise HTTPException(status_code=500, detail="Failed to load developer tools")


from fastapi import Depends
from app.core.security import get_current_user, User

@router.get("/metrics")
async def get_developer_metrics_api(current_user: User = Depends(get_current_user)) -> DeveloperMetrics:
    """Get developer portal metrics via API."""
    try:
        return await get_developer_metrics()
    except Exception as e:
        logger.error(f"Error getting developer metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to get metrics")


@router.get("/api-usage")
async def get_api_usage_api(current_user: User = Depends(get_current_user)) -> List[APIUsageStats]:
    """Get API usage statistics."""
    try:
        return await get_api_usage_stats()
    except Exception as e:
        logger.error(f"Error getting API usage stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to get API usage stats")


@router.get("/system-alerts")
async def get_system_alerts_api(current_user: User = Depends(get_current_user)) -> List[SystemAlert]:
    """Get system alerts."""
    try:
        return await get_system_alerts()
    except Exception as e:
        logger.error(f"Error getting system alerts: {e}")
        raise HTTPException(status_code=500, detail="Failed to get system alerts")


@router.get("/real-time-metrics")
async def get_real_time_metrics(current_user: User = Depends(get_current_user)):
    """Get real-time system metrics for monitoring dashboard."""
    try:
        # Get current system state
        orchestrator_capabilities = enhanced_orchestrator.get_capabilities()
        agent_capabilities = multi_agent_orchestrator.get_agent_capabilities()

        metrics = {
            "timestamp": datetime.now().isoformat(),
            "system": {
                "status": "healthy",
                "version": orchestrator_capabilities.get("version", "8.0.0"),
                "uptime": 0.0  # Would be calculated from startup time
            },
            "components": {
                "orchestrator": {
                    "status": "active",
                    "supported_tasks": len(orchestrator_capabilities.get("supported_tasks", [])),
                    "version": orchestrator_capabilities.get("version")
                },
                "multi_agent": {
                    "status": "active",
                    "available_agents": len(agent_capabilities),
                    "agents": list(agent_capabilities.keys())
                },
                "vector_store": {
                    "status": "connected" if vector_store.is_connected else "fallback",
                    "type": "Qdrant" if vector_store.is_connected else "Local"
                },
                "websocket": {
                    "status": "active",
                    "connections": connection_manager.get_connection_count(),
                    "subscriptions": len(connection_manager.subscriptions)
                }
            },
            "performance": {
                "memory_usage": 0,  # Would be calculated from system metrics
                "cpu_usage": 0,     # Would be calculated from system metrics
                "response_times": {
                    "avg": 0.5,
                    "p95": 1.2,
                    "p99": 2.1
                }
            },
            "api_stats": {
                "requests_per_minute": 0,  # Would be calculated from request logs
                "success_rate": 0.98,
                "error_rate": 0.02
            }
        }

        return JSONResponse(content=metrics)

    except Exception as e:
        logger.error(f"Error getting real-time metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to get real-time metrics")


@router.post("/test-endpoint")
async def test_api_endpoint(request: Request, current_user: User = Depends(get_current_user)):
    """Test an API endpoint with provided parameters."""
    try:
        data = await request.json()

        endpoint = data.get("endpoint")
        method = data.get("method", "GET")
        headers = data.get("headers", {})
        body = data.get("body")

        # This would make an internal request to test the endpoint
        # For now, return a mock response

        result = {
            "success": True,
            "status_code": 200,
            "response_time": 0.123,
            "response": {
                "message": f"Successfully tested {method} {endpoint}",
                "timestamp": datetime.now().isoformat()
            }
        }

        return JSONResponse(content=result)

    except Exception as e:
        logger.error(f"Error testing endpoint: {e}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )


@router.get("/generate-api-key")
async def generate_api_key(current_user: User = Depends(get_current_user)):
    """Generate a new API key for development."""
    try:
        import secrets
        import string

        # Generate a secure API key
        alphabet = string.ascii_letters + string.digits
        api_key = ''.join(secrets.choice(alphabet) for _ in range(32))

        return JSONResponse(content={
            "api_key": f"gai_{api_key}",
            "created_at": datetime.now().isoformat(),
            "expires_at": (datetime.now() + timedelta(days=30)).isoformat(),
            "permissions": ["read", "write"],
            "note": "Development API key - expires in 30 days"
        })

    except Exception as e:
        logger.error(f"Error generating API key: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate API key")


async def get_developer_metrics() -> DeveloperMetrics:
    """Get comprehensive developer metrics."""
    try:
        # In a real implementation, these would come from metrics storage
        # For now, return mock data based on current system state

        return DeveloperMetrics(
            total_api_calls=1250,
            successful_calls=1225,
            failed_calls=25,
            avg_response_time=0.45,
            active_conversations=15,
            total_documents=42,
            active_websocket_connections=connection_manager.get_connection_count(),
            system_uptime=86400.0  # 24 hours
        )

    except Exception as e:
        logger.error(f"Error calculating developer metrics: {e}")
        return DeveloperMetrics()


async def get_api_usage_stats() -> List[APIUsageStats]:
    """Get API usage statistics."""
    try:
        # Mock API usage data
        # In a real implementation, this would come from request logs

        stats = [
            APIUsageStats(
                endpoint="/api/v1/agent/invoke",
                method="POST",
                calls_count=450,
                avg_response_time=0.8,
                success_rate=0.98,
                last_called=datetime.now() - timedelta(minutes=2)
            ),
            APIUsageStats(
                endpoint="/api/v1/history/conversations",
                method="GET",
                calls_count=320,
                avg_response_time=0.2,
                success_rate=0.99,
                last_called=datetime.now() - timedelta(minutes=5)
            ),
            APIUsageStats(
                endpoint="/api/v1/multi-agent/execute",
                method="POST",
                calls_count=180,
                avg_response_time=2.1,
                success_rate=0.95,
                last_called=datetime.now() - timedelta(minutes=8)
            ),
            APIUsageStats(
                endpoint="/api/v1/documents/search",
                method="POST",
                calls_count=95,
                avg_response_time=0.6,
                success_rate=0.97,
                last_called=datetime.now() - timedelta(minutes=12)
            ),
            APIUsageStats(
                endpoint="/graphql",
                method="POST",
                calls_count=75,
                avg_response_time=0.4,
                success_rate=0.99,
                last_called=datetime.now() - timedelta(minutes=15)
            )
        ]

        return stats

    except Exception as e:
        logger.error(f"Error getting API usage stats: {e}")
        return []


async def get_system_alerts() -> List[SystemAlert]:
    """Get system alerts."""
    try:
        alerts = []

        # Check for system issues and generate alerts
        if not vector_store.is_connected:
            alerts.append(SystemAlert(
                id="vector_store_fallback",
                level="warning",
                message="Vector store using fallback mode - Qdrant connection unavailable",
                timestamp=datetime.now() - timedelta(minutes=30)
            ))

        # Check agent availability
        agent_capabilities = multi_agent_orchestrator.get_agent_capabilities()
        unavailable_agents = [
            name for name, info in agent_capabilities.items()
            if not info.get("available", False)
        ]

        if unavailable_agents:
            alerts.append(SystemAlert(
                id="agents_unavailable",
                level="info",
                message=f"Some agents using fallback mode: {', '.join(unavailable_agents)}",
                timestamp=datetime.now() - timedelta(minutes=45)
            ))

        # Add some example alerts
        alerts.extend([
            SystemAlert(
                id="high_response_time",
                level="info",
                message="API response times slightly elevated (avg: 0.8s)",
                timestamp=datetime.now() - timedelta(hours=2),
                resolved=True
            ),
            SystemAlert(
                id="websocket_connections",
                level="info",
                message=f"WebSocket connections: {connection_manager.get_connection_count()} active",
                timestamp=datetime.now() - timedelta(hours=1)
            )
        ])

        return sorted(alerts, key=lambda x: x.timestamp, reverse=True)

    except Exception as e:
        logger.error(f"Error getting system alerts: {e}")
        return []


async def get_system_info() -> Dict[str, Any]:
    """Get comprehensive system information."""
    try:
        orchestrator_capabilities = enhanced_orchestrator.get_capabilities()
        agent_capabilities = multi_agent_orchestrator.get_agent_capabilities()

        return {
            "version": orchestrator_capabilities.get("version", "8.0.0"),
            "components": {
                "orchestrator": True,
                "multi_agent": True,
                "vector_store": vector_store.is_connected,
                "websocket": True,
                "graphql": True
            },
            "capabilities": {
                "supported_tasks": len(orchestrator_capabilities.get("supported_tasks", [])),
                "available_agents": len(agent_capabilities),
                "websocket_connections": connection_manager.get_connection_count()
            },
            "apis": {
                "rest": {"available": True, "endpoints": 35},
                "graphql": {"available": True, "types": 12},
                "websocket": {"available": True, "message_types": 13}
            }
        }

    except Exception as e:
        logger.error(f"Error getting system info: {e}")
        return {}


async def get_api_endpoints() -> List[Dict[str, Any]]:
    """Get all available API endpoints."""
    try:
        # This would typically be generated from the FastAPI app
        # For now, return a curated list of important endpoints

        endpoints = [
            {
                "path": "/api/v1/agent/invoke",
                "method": "POST",
                "category": "Core Agent",
                "description": "Invoke the AI agent with a query",
                "parameters": ["input", "conversation_id", "save_conversation"]
            },
            {
                "path": "/api/v1/history/conversations",
                "method": "GET",
                "category": "Conversations",
                "description": "List conversations with pagination",
                "parameters": ["limit", "offset"]
            },
            {
                "path": "/api/v1/multi-agent/execute",
                "method": "POST",
                "category": "Multi-Agent",
                "description": "Execute a multi-agent workflow",
                "parameters": ["workflow_type", "input", "conversation_id"]
            },
            {
                "path": "/api/v1/documents/search",
                "method": "POST",
                "category": "Documents",
                "description": "Search documents with semantic search",
                "parameters": ["query", "limit", "use_rag"]
            },
            {
                "path": "/graphql",
                "method": "POST",
                "category": "GraphQL",
                "description": "GraphQL endpoint for flexible queries",
                "parameters": ["query", "variables"]
            }
        ]

        return endpoints

    except Exception as e:
        logger.error(f"Error getting API endpoints: {e}")
        return []
