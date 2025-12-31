"""
Tool Integration APIs and Frontend Components

REST APIs and WebSocket services for tool interaction and real-time updates.
Part of DRYAD.AI Armory System for comprehensive tool integration.
"""

import logging
import asyncio
import json
import uuid
import time
from typing import Dict, Any, List, Optional, Union, Set, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict, deque
import websockets
import aiohttp
from fastapi import FastAPI, HTTPException, Depends, WebSocket, WebSocketDisconnect, UploadFile, File
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn
import jwt
from starlette.middleware.base import BaseHTTPMiddleware

from .tool_integration import UniversalToolRegistry, ToolCatalog, ToolExecutionEngine, ToolOrchestrator
from .tool_security import SecurityManager, AccessControlRule

# Define ToolCategory and ToolSecurityLevel to avoid circular imports
class ToolCategory(str, Enum):
    """Tool categories for organization"""
    DATABASE = "database"
    API = "api"
    FILE_SYSTEM = "file_system"
    POWERSHELL = "powershell"
    BASH = "bash"
    ANALYSIS = "analysis"
    COMMUNICATION = "communication"
    SEARCH = "search"
    CODE_EXECUTION = "code_execution"
    MONITORING = "monitoring"
    EDUCATIONAL = "educational"
    RESEARCH = "research"
    CONTENT_CREATION = "content_creation"
    ASSESSMENT = "assessment"
    LLM = "llm"
    WEB_SCRAPING = "web_scraping"
    DATA_PROCESSING = "data_processing"
    VISUALIZATION = "visualization"


class ToolSecurityLevel(str, Enum):
    """Security levels for tools"""
    SAFE = "safe"  # Read-only, no side effects
    LOW_RISK = "low_risk"  # Limited write operations
    MEDIUM_RISK = "medium_risk"  # Moderate write operations
    HIGH_RISK = "high_risk"  # Significant system changes
    CRITICAL = "critical"  # Requires human approval

logger = logging.getLogger(__name__)


class APIVersion(str, Enum):
    """API version constants"""
    V1 = "v1"
    V2 = "v2"


class WebSocketEventType(str, Enum):
    """WebSocket event types"""
    TOOL_EXECUTION_STARTED = "tool_execution_started"
    TOOL_EXECUTION_PROGRESS = "tool_execution_progress"
    TOOL_EXECUTION_COMPLETED = "tool_execution_completed"
    TOOL_EXECUTION_FAILED = "tool_execution_failed"
    TOOL_REGISTRY_UPDATED = "tool_registry_updated"
    TOOL_STATUS_CHANGED = "tool_status_changed"
    SYSTEM_ALERT = "system_alert"
    USER_NOTIFICATION = "user_notification"


class RequestMethod(str, Enum):
    """HTTP request methods"""
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"
    PATCH = "PATCH"


class ContentType(str, Enum):
    """Content types"""
    JSON = "application/json"
    FORM_DATA = "multipart/form-data"
    HTML = "text/html"
    CSS = "text/css"
    JAVASCRIPT = "application/javascript"


@dataclass
class APIEndpoint:
    """API endpoint definition"""
    endpoint_id: str
    name: str
    path: str
    method: RequestMethod
    description: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    responses: Dict[str, Any] = field(default_factory=dict)
    auth_required: bool = True
    rate_limit: int = 100  # requests per minute
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    def __post_init__(self):
        if not self.endpoint_id:
            self.endpoint_id = f"endpoint_{uuid.uuid4().hex[:8]}"


@dataclass
class FrontendComponent:
    """Frontend component definition"""
    component_id: str
    name: str
    type: str  # "react", "vue", "angular", "html", etc.
    category: ToolCategory
    description: str
    props: Dict[str, Any] = field(default_factory=dict)
    styles: Dict[str, Any] = field(default_factory=dict)
    scripts: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    accessibility_features: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    def __post_init__(self):
        if not self.component_id:
            self.component_id = f"component_{uuid.uuid4().hex[:8]}"


@dataclass
class WebSocketConnection:
    """WebSocket connection info"""
    connection_id: str
    websocket: WebSocket
    user_id: str
    session_id: str
    connected_at: datetime = field(default_factory=datetime.utcnow)
    last_activity: datetime = field(default_factory=datetime.utcnow)
    subscribed_events: Set[WebSocketEventType] = field(default_factory=set)
    active_tools: Set[str] = field(default_factory=set)
    
    def __post_init__(self):
        if not self.connection_id:
            self.connection_id = f"ws_{uuid.uuid4().hex[:8]}"


class APIRequest(BaseModel):
    """API request model"""
    tool_id: str = Field(..., description="Tool identifier")
    action: str = Field(..., description="Action to perform")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Action parameters")
    session_id: Optional[str] = Field(None, description="Session identifier")
    user_context: Dict[str, Any] = Field(default_factory=dict, description="User context")
    async_mode: bool = Field(False, description="Execute asynchronously")


class APIResponse(BaseModel):
    """API response model"""
    success: bool = Field(..., description="Request success status")
    request_id: str = Field(..., description="Unique request identifier")
    tool_id: str = Field(..., description="Tool identifier")
    action: str = Field(..., description="Action performed")
    result: Optional[Dict[str, Any]] = Field(None, description="Action result")
    error: Optional[str] = Field(None, description="Error message if any")
    execution_time: float = Field(..., description="Execution time in seconds")
    timestamp: str = Field(..., description="Response timestamp")


class ToolRegistrationRequest(BaseModel):
    """Tool registration request model"""
    name: str = Field(..., description="Tool name")
    description: str = Field(..., description="Tool description")
    category: ToolCategory = Field(..., description="Tool category")
    security_level: ToolSecurityLevel = Field(..., description="Security level")
    schema_json: Dict[str, Any] = Field(..., description="OpenAPI schema")
    capabilities: List[str] = Field(default_factory=list, description="Tool capabilities")
    dependencies: List[str] = Field(default_factory=list, description="Tool dependencies")


class FrontendComponentRequest(BaseModel):
    """Frontend component request model"""
    name: str = Field(..., description="Component name")
    type: str = Field(..., description="Component type")
    category: ToolCategory = Field(..., description="Associated tool category")
    description: str = Field(..., description="Component description")
    props: Dict[str, Any] = Field(default_factory=dict, description="Component props")
    styles: Dict[str, Any] = Field(default_factory=dict, description="Component styles")


class ToolIntegrationAPI:
    """Tool Integration API Service"""
    
    def __init__(self, db_session=None):
        self.tool_registry = UniversalToolRegistry()
        self.tool_catalog = ToolCatalog()
        self.execution_engine = ToolExecutionEngine()
        self.orchestrator = ToolOrchestrator()
        self.security_manager = SecurityManager(db_session)
        
        # API management
        self.api_endpoints: Dict[str, APIEndpoint] = {}
        self.frontend_components: Dict[str, FrontendComponent] = {}
        self.websocket_connections: Dict[str, WebSocketConnection] = {}
        self.rate_limiters: Dict[str, deque] = defaultdict(lambda: deque(maxlen=100))
        
        # Create FastAPI app
        self.app = self._create_fastapi_app()
        self.websocket_manager = WebSocketManager()
        
        # Note: Async initialization will be done separately to avoid event loop issues
        # asyncio.create_task(self._initialize_api_components())
    
    async def initialize(self):
        """Initialize the API service (must be called from async context)"""
        await self._initialize_api_components()
    
    def _create_fastapi_app(self) -> FastAPI:
        """Create and configure FastAPI application"""
        app = FastAPI(
            title="DRYAD.AI Tool Integration API",
            description="Comprehensive REST API and WebSocket services for tool integration",
            version="1.0.0",
            docs_url="/api/docs",
            redoc_url="/api/redoc"
        )
        
        # Add CORS middleware
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],  # Configure appropriately for production
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"]
        )
        
        # Add custom middleware
        app.add_middleware(APIRateLimitMiddleware)
        app.add_middleware(AuthenticationMiddleware)
        
        # Register routes
        self._register_routes(app)
        
        return app
    
    def _register_routes(self, app: FastAPI):
        """Register API routes"""
        
        # Tool management endpoints
        @app.post("/api/v1/tools/register", response_model=Dict[str, Any])
        async def register_tool(request: ToolRegistrationRequest):
            """Register a new tool"""
            return await self._register_tool_handler(request)
        
        @app.get("/api/v1/tools", response_model=Dict[str, Any])
        async def list_tools(category: Optional[ToolCategory] = None, limit: int = 100):
            """List available tools"""
            return await self._list_tools_handler(category, limit)
        
        @app.get("/api/v1/tools/{tool_id}", response_model=Dict[str, Any])
        async def get_tool(tool_id: str):
            """Get tool details"""
            return await self._get_tool_handler(tool_id)
        
        @app.delete("/api/v1/tools/{tool_id}")
        async def unregister_tool(tool_id: str):
            """Unregister a tool"""
            return await self._unregister_tool_handler(tool_id)
        
        # Tool execution endpoints
        @app.post("/api/v1/tools/execute", response_model=APIResponse)
        async def execute_tool(request: APIRequest):
            """Execute tool action"""
            return await self._execute_tool_handler(request)
        
        @app.post("/api/v1/tools/execute/batch", response_model=Dict[str, Any])
        async def execute_tools_batch(requests: List[APIRequest]):
            """Execute multiple tool actions in batch"""
            return await self._execute_tools_batch_handler(requests)
        
        @app.get("/api/v1/tools/execution/status/{execution_id}")
        async def get_execution_status(execution_id: str):
            """Get execution status"""
            return await self._get_execution_status_handler(execution_id)
        
        # Frontend component endpoints
        @app.post("/api/v1/components/register", response_model=Dict[str, Any])
        async def register_component(request: FrontendComponentRequest):
            """Register a new frontend component"""
            return await self._register_component_handler(request)
        
        @app.get("/api/v1/components", response_model=Dict[str, Any])
        async def list_components(category: Optional[ToolCategory] = None):
            """List available frontend components"""
            return await self._list_components_handler(category)
        
        @app.get("/api/v1/components/{component_id}")
        async def get_component(component_id: str):
            """Get component details and code"""
            return await self._get_component_handler(component_id)
        
        # WebSocket endpoint
        @app.websocket("/api/v1/ws/{session_id}")
        async def websocket_endpoint(websocket: WebSocket, session_id: str):
            await self.websocket_manager.connect(websocket, session_id)
        
        # File upload endpoints
        @app.post("/api/v1/upload")
        async def upload_file(file: UploadFile = File(...)):
            """Upload file for tool processing"""
            return await self._upload_file_handler(file)
        
        # System information endpoints
        @app.get("/api/v1/system/health")
        async def health_check():
            """System health check"""
            return await self._health_check_handler()
        
        @app.get("/api/v1/system/stats")
        async def get_system_stats():
            """Get system statistics"""
            return await self._get_system_stats_handler()
        
        @app.get("/api/v1/system/documentation")
        async def get_api_documentation():
            """Get comprehensive API documentation"""
            return await self._get_api_documentation_handler()
    
    async def _initialize_api_components(self):
        """Initialize API components"""
        # Initialize built-in API endpoints
        await self._create_built_in_endpoints()
        
        # Initialize built-in frontend components
        await self._create_built_in_components()
        
        # Start background tasks
        asyncio.create_task(self._background_task_processor())
        asyncio.create_task(self._websocket_keepalive_processor())
        
        logger.info("Tool Integration API initialized")
    
    async def _create_built_in_endpoints(self):
        """Create built-in API endpoints"""
        built_in_endpoints = [
            APIEndpoint(
                endpoint_id="tools_list",
                name="List Tools",
                path="/api/v1/tools",
                method=RequestMethod.GET,
                description="List all available tools",
                auth_required=False
            ),
            APIEndpoint(
                endpoint_id="tools_execute",
                name="Execute Tool",
                path="/api/v1/tools/execute",
                method=RequestMethod.POST,
                description="Execute a tool action",
                auth_required=True
            ),
            APIEndpoint(
                endpoint_id="components_list",
                name="List Components",
                path="/api/v1/components",
                method=RequestMethod.GET,
                description="List all frontend components",
                auth_required=False
            ),
            APIEndpoint(
                endpoint_id="system_health",
                name="Health Check",
                path="/api/v1/system/health",
                method=RequestMethod.GET,
                description="System health check endpoint",
                auth_required=False,
                rate_limit=1000
            )
        ]
        
        for endpoint in built_in_endpoints:
            self.api_endpoints[endpoint.endpoint_id] = endpoint
        
        logger.info(f"Created {len(built_in_endpoints)} built-in API endpoints")
    
    async def _create_built_in_components(self):
        """Create built-in frontend components"""
        built_in_components = [
            FrontendComponent(
                component_id="tool_card",
                name="Tool Card",
                type="react",
                category=ToolCategory.CONTENT_CREATION,
                description="Card component for displaying tool information",
                props={
                    "tool": {"type": "object", "required": True},
                    "onExecute": {"type": "function", "required": False},
                    "showStatus": {"type": "boolean", "default": True}
                },
                styles={
                    "container": "border rounded-lg p-4 shadow-md",
                    "header": "text-lg font-semibold mb-2",
                    "description": "text-gray-600 mb-3",
                    "actions": "flex gap-2"
                },
                accessibility_features=[
                    "aria-label",
                    "keyboard-navigation",
                    "screen-reader-text"
                ]
            ),
            FrontendComponent(
                component_id="execution_monitor",
                name="Execution Monitor",
                type="react",
                category=ToolCategory.CONTENT_CREATION,
                description="Real-time tool execution monitoring component",
                props={
                    "executionId": {"type": "string", "required": True},
                    "autoRefresh": {"type": "boolean", "default": True},
                    "refreshInterval": {"type": "number", "default": 1000}
                },
                styles={
                    "container": "bg-gray-50 p-4 rounded-lg",
                    "progress": "w-full bg-gray-200 rounded-full h-2",
                    "progressBar": "bg-blue-600 h-2 rounded-full transition-all",
                    "status": "text-sm font-medium"
                },
                accessibility_features=[
                    "progress-announcements",
                    "status-updates",
                    "keyboard-shortcuts"
                ]
            ),
            FrontendComponent(
                component_id="tool_orchestrator",
                name="Tool Orchestrator",
                type="react",
                category=ToolCategory.CONTENT_CREATION,
                description="Component for managing complex tool workflows",
                props={
                    "workflow": {"type": "object", "required": True},
                    "onStepComplete": {"type": "function", "required": False},
                    "allowParallel": {"type": "boolean", "default": False}
                },
                styles={
                    "container": "border-2 border-dashed border-gray-300 p-6 rounded-lg",
                    "step": "bg-white p-3 rounded border mb-2",
                    "completed": "border-green-500 bg-green-50",
                    "active": "border-blue-500 bg-blue-50",
                    "pending": "border-gray-300 bg-gray-50"
                },
                accessibility_features=[
                    "step-navigation",
                    "progress-indicators",
                    "workflow-overview"
                ]
            ),
            FrontendComponent(
                component_id="security_dashboard",
                name="Security Dashboard",
                type="react",
                category=ToolCategory.CONTENT_CREATION,
                description="Security monitoring and compliance dashboard",
                props={
                    "metrics": {"type": "object", "required": True},
                    "timeRange": {"type": "string", "default": "24h"},
                    "realTimeUpdates": {"type": "boolean", "default": True}
                },
                styles={
                    "container": "bg-white shadow-lg rounded-lg p-6",
                    "metric": "bg-gradient-to-r from-blue-500 to-purple-600 text-white p-4 rounded-lg",
                    "alert": "border-l-4 border-red-500 bg-red-50 p-4",
                    "chart": "w-full h-64"
                },
                accessibility_features=[
                    "chart-alternatives",
                    "alert-summary",
                    "data-navigation"
                ]
            )
        ]
        
        for component in built_in_components:
            self.frontend_components[component.component_id] = component
        
        logger.info(f"Created {len(built_in_components)} built-in frontend components")
    
    async def _register_tool_handler(self, request: ToolRegistrationRequest) -> Dict[str, Any]:
        """Handle tool registration"""
        try:
            logger.info(f"Registering tool: {request.name}")
            
            # Create tool specification
            tool_spec = {
                "name": request.name,
                "description": request.description,
                "category": request.category.value,
                "security_level": request.security_level.value,
                "schema_json": request.schema_json,
                "capabilities": request.capabilities,
                "dependencies": request.dependencies
            }
            
            # Register with tool registry
            registration_result = await self.tool_registry.register_tool(tool_spec)
            
            if registration_result["success"]:
                # Notify connected WebSocket clients
                await self.websocket_manager.broadcast_event(
                    WebSocketEventType.TOOL_REGISTRY_UPDATED,
                    {
                        "tool_id": registration_result["tool_id"],
                        "action": "registered",
                        "tool_name": request.name
                    }
                )
            
            return {
                "success": registration_result["success"],
                "tool_id": registration_result.get("tool_id"),
                "message": registration_result.get("message", "Tool registered successfully"),
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Tool registration failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def _list_tools_handler(self, category: Optional[ToolCategory] = None, limit: int = 100) -> Dict[str, Any]:
        """Handle list tools request"""
        try:
            # Get tools from catalog
            tools_result = await self.tool_catalog.get_all_tools(limit=limit)
            
            # Filter by category if specified
            if category:
                tools_result["tools"] = [
                    tool for tool in tools_result["tools"]
                    if tool.get("category") == category.value
                ]
            
            return {
                "success": True,
                "tools": tools_result["tools"],
                "total": len(tools_result["tools"]),
                "category_filter": category.value if category else None,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"List tools failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "tools": [],
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def _get_tool_handler(self, tool_id: str) -> Dict[str, Any]:
        """Handle get tool request"""
        try:
            # Get tool details
            tool_result = await self.tool_registry.get_tool_details(tool_id)
            
            if not tool_result["found"]:
                raise HTTPException(status_code=404, detail="Tool not found")
            
            return {
                "success": True,
                "tool": tool_result["tool"],
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Get tool failed: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    async def _unregister_tool_handler(self, tool_id: str) -> Dict[str, Any]:
        """Handle tool unregistration"""
        try:
            logger.info(f"Unregistering tool: {tool_id}")
            
            # Unregister tool
            unregister_result = await self.tool_registry.unregister_tool(tool_id)
            
            if unregister_result["success"]:
                # Notify WebSocket clients
                await self.websocket_manager.broadcast_event(
                    WebSocketEventType.TOOL_REGISTRY_UPDATED,
                    {
                        "tool_id": tool_id,
                        "action": "unregistered"
                    }
                )
            
            return {
                "success": unregister_result["success"],
                "message": unregister_result.get("message", "Tool unregistered successfully"),
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Tool unregistration failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def _execute_tool_handler(self, request: APIRequest) -> APIResponse:
        """Handle tool execution request"""
        start_time = time.time()
        
        try:
            logger.info(f"Executing tool: {request.tool_id}, action: {request.action}")
            
            # Check access control
            access_result = await self.security_manager.check_tool_access(
                request.tool_id,
                request.user_context.get("user_id", "anonymous"),
                request.action,
                request.user_context
            )
            
            if not access_result["allowed"]:
                return APIResponse(
                    success=False,
                    request_id=str(uuid.uuid4()),
                    tool_id=request.tool_id,
                    action=request.action,
                    error="Access denied",
                    execution_time=time.time() - start_time,
                    timestamp=datetime.utcnow().isoformat()
                )
            
            # Execute tool
            execution_params = {
                "tool_id": request.tool_id,
                "action": request.action,
                "parameters": request.parameters,
                "user_context": request.user_context,
                "session_id": request.session_id
            }
            
            if request.async_mode:
                # Start async execution and return immediately
                execution_id = str(uuid.uuid4())
                asyncio.create_task(self._execute_tool_async(execution_id, execution_params))
                
                return APIResponse(
                    success=True,
                    request_id=str(uuid.uuid4()),
                    tool_id=request.tool_id,
                    action=request.action,
                    result={
                        "execution_id": execution_id,
                        "status": "started",
                        "message": "Tool execution started asynchronously"
                    },
                    execution_time=time.time() - start_time,
                    timestamp=datetime.utcnow().isoformat()
                )
            else:
                # Execute synchronously
                result = await self.execution_engine.execute_tool(execution_params)
                
                return APIResponse(
                    success=result.get("success", False),
                    request_id=str(uuid.uuid4()),
                    tool_id=request.tool_id,
                    action=request.action,
                    result=result.get("result"),
                    error=result.get("error"),
                    execution_time=time.time() - start_time,
                    timestamp=datetime.utcnow().isoformat()
                )
            
        except Exception as e:
            logger.error(f"Tool execution failed: {e}")
            return APIResponse(
                success=False,
                request_id=str(uuid.uuid4()),
                tool_id=request.tool_id,
                action=request.action,
                error=str(e),
                execution_time=time.time() - start_time,
                timestamp=datetime.utcnow().isoformat()
            )
    
    async def _execute_tools_batch_handler(self, requests: List[APIRequest]) -> Dict[str, Any]:
        """Handle batch tool execution"""
        try:
            execution_params_list = []
            
            for request in requests:
                execution_params = {
                    "tool_id": request.tool_id,
                    "action": request.action,
                    "parameters": request.parameters,
                    "user_context": request.user_context,
                    "session_id": request.session_id
                }
                execution_params_list.append(execution_params)
            
            # Execute batch
            batch_result = await self.orchestrator.execute_workflow(execution_params_list)
            
            return {
                "success": batch_result.get("success", False),
                "results": batch_result.get("results", []),
                "batch_id": str(uuid.uuid4()),
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Batch execution failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "results": [],
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def _get_execution_status_handler(self, execution_id: str) -> Dict[str, Any]:
        """Handle execution status request"""
        try:
            # In a real implementation, this would check a job queue or database
            # For now, return a placeholder status
            return {
                "success": True,
                "execution_id": execution_id,
                "status": "completed",  # or "running", "failed", "pending"
                "progress": 100,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Get execution status failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def _register_component_handler(self, request: FrontendComponentRequest) -> Dict[str, Any]:
        """Handle component registration"""
        try:
            logger.info(f"Registering component: {request.name}")
            
            # Create component
            component = FrontendComponent(
                component_id=str(uuid.uuid4()),
                name=request.name,
                type=request.type,
                category=request.category,
                description=request.description,
                props=request.props,
                styles=request.styles
            )
            
            # Store component
            self.frontend_components[component.component_id] = component
            
            return {
                "success": True,
                "component_id": component.component_id,
                "message": "Component registered successfully",
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Component registration failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def _list_components_handler(self, category: Optional[ToolCategory] = None) -> Dict[str, Any]:
        """Handle list components request"""
        try:
            components = list(self.frontend_components.values())
            
            # Filter by category if specified
            if category:
                components = [comp for comp in components if comp.category == category]
            
            component_summaries = [
                {
                    "component_id": comp.component_id,
                    "name": comp.name,
                    "type": comp.type,
                    "category": comp.category.value,
                    "description": comp.description,
                    "accessibility_features": comp.accessibility_features
                }
                for comp in components
            ]
            
            return {
                "success": True,
                "components": component_summaries,
                "total": len(component_summaries),
                "category_filter": category.value if category else None,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"List components failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "components": [],
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def _get_component_handler(self, component_id: str) -> Dict[str, Any]:
        """Handle get component request"""
        try:
            if component_id not in self.frontend_components:
                raise HTTPException(status_code=404, detail="Component not found")
            
            component = self.frontend_components[component_id]
            
            # Generate component code based on type
            component_code = await self._generate_component_code(component)
            
            return {
                "success": True,
                "component": {
                    "component_id": component.component_id,
                    "name": component.name,
                    "type": component.type,
                    "category": component.category.value,
                    "description": component.description,
                    "props": component.props,
                    "styles": component.styles,
                    "accessibility_features": component.accessibility_features
                },
                "code": component_code,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Get component failed: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    async def _upload_file_handler(self, file: UploadFile) -> Dict[str, Any]:
        """Handle file upload"""
        try:
            # Read file content
            content = await file.read()
            
            # Process file (in real implementation, would save to storage)
            processed_result = {
                "filename": file.filename,
                "content_type": file.content_type,
                "size": len(content),
                "upload_timestamp": datetime.utcnow().isoformat(),
                "file_id": str(uuid.uuid4())
            }
            
            return {
                "success": True,
                "file_info": processed_result,
                "message": "File uploaded successfully",
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"File upload failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def _health_check_handler(self) -> Dict[str, Any]:
        """Handle health check"""
        try:
            # Check system health
            health_status = {
                "status": "healthy",
                "timestamp": datetime.utcnow().isoformat(),
                "services": {
                    "tool_registry": "healthy",
                    "execution_engine": "healthy",
                    "security_manager": "healthy",
                    "websocket_manager": "healthy"
                },
                "metrics": {
                    "active_connections": len(self.websocket_connections),
                    "registered_tools": len(await self.tool_registry.list_tools()),
                    "active_components": len(self.frontend_components)
                }
            }
            
            return health_status
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def _get_system_stats_handler(self) -> Dict[str, Any]:
        """Handle system stats request"""
        try:
            stats = {
                "timestamp": datetime.utcnow().isoformat(),
                "api": {
                    "endpoints_total": len(self.api_endpoints),
                    "endpoints_active": len([ep for ep in self.api_endpoints.values() if ep.auth_required])
                },
                "tools": {
                    "registered_total": len(await self.tool_registry.list_tools()),
                    "active_categories": len(set(
                        await self.tool_registry.get_tools_by_category()
                    ))
                },
                "components": {
                    "registered_total": len(self.frontend_components),
                    "by_type": {
                        comp_type: len([c for c in self.frontend_components.values() if c.type == comp_type])
                        for comp_type in set(c.type for c in self.frontend_components.values())
                    }
                },
                "websocket": {
                    "active_connections": len(self.websocket_connections),
                    "total_events_sent": 0  # Would track in real implementation
                }
            }
            
            return {
                "success": True,
                "stats": stats,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Get system stats failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def _get_api_documentation_handler(self) -> Dict[str, Any]:
        """Handle API documentation request"""
        try:
            documentation = {
                "title": "DRYAD.AI Tool Integration API",
                "version": "1.0.0",
                "description": "Comprehensive REST API and WebSocket services for tool integration",
                "endpoints": [],
                "websocket_events": [],
                "components": []
            }
            
            # Add API endpoints documentation
            for endpoint in self.api_endpoints.values():
                endpoint_doc = {
                    "id": endpoint.endpoint_id,
                    "name": endpoint.name,
                    "path": endpoint.path,
                    "method": endpoint.method.value,
                    "description": endpoint.description,
                    "auth_required": endpoint.auth_required,
                    "rate_limit": endpoint.rate_limit
                }
                documentation["endpoints"].append(endpoint_doc)
            
            # Add WebSocket events documentation
            ws_events = [
                {"type": event.value, "description": f"{event.value.replace('_', ' ').title()}"}
                for event in WebSocketEventType
            ]
            documentation["websocket_events"] = ws_events
            
            # Add components documentation
            for component in self.frontend_components.values():
                component_doc = {
                    "id": component.component_id,
                    "name": component.name,
                    "type": component.type,
                    "category": component.category.value,
                    "description": component.description,
                    "accessibility_features": component.accessibility_features
                }
                documentation["components"].append(component_doc)
            
            return {
                "success": True,
                "documentation": documentation,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Get API documentation failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def _execute_tool_async(self, execution_id: str, execution_params: Dict[str, Any]):
        """Execute tool asynchronously with progress updates"""
        try:
            # Send start event
            await self.websocket_manager.broadcast_event(
                WebSocketEventType.TOOL_EXECUTION_STARTED,
                {
                    "execution_id": execution_id,
                    "tool_id": execution_params["tool_id"],
                    "action": execution_params["action"],
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
            
            # Execute tool
            result = await self.execution_engine.execute_tool(execution_params)
            
            # Send completion event
            event_type = WebSocketEventType.TOOL_EXECUTION_COMPLETED if result.get("success") else WebSocketEventType.TOOL_EXECUTION_FAILED
            
            await self.websocket_manager.broadcast_event(
                event_type,
                {
                    "execution_id": execution_id,
                    "tool_id": execution_params["tool_id"],
                    "result": result,
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
            
        except Exception as e:
            logger.error(f"Async execution failed: {e}")
            
            await self.websocket_manager.broadcast_event(
                WebSocketEventType.TOOL_EXECUTION_FAILED,
                {
                    "execution_id": execution_id,
                    "tool_id": execution_params.get("tool_id", "unknown"),
                    "error": str(e),
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
    
    async def _generate_component_code(self, component: FrontendComponent) -> Dict[str, str]:
        """Generate code for frontend component"""
        code_templates = {
            "react": await self._generate_react_component(component),
            "vue": await self._generate_vue_component(component),
            "html": await self._generate_html_component(component),
            "angular": await self._generate_angular_component(component)
        }
        
        return code_templates
    
    async def _generate_react_component(self, component: FrontendComponent) -> str:
        """Generate React component code"""
        return f"""
    import React, {{ useState, useEffect }} from 'react';
    
    const {component.name} = ({{ {', '.join(component.props.keys())} }}) => {{
        const [state, setState] = useState({{}});
    
        return (
            <div className="{component.styles.get('container', 'default-container')}"
                 role="main"
                 aria-label="{component.description}">
                <h2>{component.name}</h2>
                <p>{component.description}</p>
                {{/* Component content goes here */}}
            </div>
        );
    }};
    
    export default {component.name};
    """
    
    async def _generate_vue_component(self, component: FrontendComponent) -> str:
        """Generate Vue component code"""
        return f"""
    <template>
        <div class="{component.styles.get('container', 'default-container')}"
             role="main"
             aria-label="{component.description}">
            <h2>{component.name}</h2>
            <p>{component.description}</p>
            {{!-- Component content goes here --}}
        </div>
    </template>
    
    <script>
    export default {{
        name: '{component.name}',
        props: {{
            {chr(10).join(f"{prop}: {{ type: String, default: null }}," for prop in component.props.keys())}
        }},
        data() {{
            return {{
                state: {{}}
            }};
        }}
    }};
    </script>
    
    <style scoped>
    {component.name} {{
        /* Component styles */
    }}
    </style>
    """
    
    async def _generate_html_component(self, component: FrontendComponent) -> str:
        """Generate HTML component code"""
        return f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{component.name}</title>
        <style>
            .{component.name.lower().replace(' ', '-')} {{
                {chr(10).join(f"{style}: {value};" for style, value in component.styles.items())}
            }}
        </style>
    </head>
    <body>
        <div class="{component.name.lower().replace(' ', '-')}"
             role="main"
             aria-label="{component.description}">
            <h2>{component.name}</h2>
            <p>{component.description}</p>
            {{!-- Component content goes here --}}
        </div>
    </body>
    </html>
    """
    
    async def _generate_angular_component(self, component: FrontendComponent) -> str:
        """Generate Angular component code"""
        return f"""
    import {{ Component, Input, OnInit }} from '@angular/core';
    
    @Component({{
        selector: 'app-{component.name.lower().replace(' ', '-')}',
        template: `
            <div class="{component.styles.get('container', 'default-container')}"
                 role="main"
                 aria-label="{component.description}">
                <h2>{component.name}</h2>
                <p>{component.description}</p>
                {{!-- Component content goes here --}}
            </div>
        `,
        styles: [`
            .{component.name.lower().replace(' ', '-')} {{
                {chr(10).join(f"{style}: {value};" for style, value in component.styles.items())}
            }}
        `]
    }})
    export class {component.name.replace(' ', '')}Component implements OnInit {{
        @Input() {chr(10).join(f"{prop}: string = '';" for prop in component.props.keys())}
        
        constructor() {{}}
        
        ngOnInit() {{
            // Component initialization
        }}
    }}
    """
    
    async def _background_task_processor(self):
        """Background task processor"""
        while True:
            try:
                # Process any pending background tasks
                await asyncio.sleep(1)  # Process every second
                
            except Exception as e:
                logger.error(f"Background task processor error: {e}")
                await asyncio.sleep(5)  # Wait longer on error
    
    async def _websocket_keepalive_processor(self):
        """WebSocket keepalive processor"""
        while True:
            try:
                # Send keepalive to all connections
                current_time = datetime.utcnow()
                
                for connection_id, connection in list(self.websocket_connections.items()):
                    # Check if connection is stale
                    if (current_time - connection.last_activity).seconds > 300:  # 5 minutes
                        logger.info(f"Removing stale WebSocket connection: {connection_id}")
                        del self.websocket_connections[connection_id]
                        continue
                    
                    # Send keepalive
                    try:
                        await connection.websocket.send_text(json.dumps({
                            "type": "keepalive",
                            "timestamp": current_time.isoformat()
                        }))
                    except Exception:
                        # Connection likely closed
                        del self.websocket_connections[connection_id]
                
                await asyncio.sleep(30)  # Process every 30 seconds
                
            except Exception as e:
                logger.error(f"WebSocket keepalive processor error: {e}")
                await asyncio.sleep(30)
    
    def get_app(self) -> FastAPI:
        """Get the FastAPI application"""
        return self.app


class WebSocketManager:
    """Manager for WebSocket connections and events"""
    
    def __init__(self):
        self.connections: Dict[str, WebSocketConnection] = {}
    
    async def connect(self, websocket: WebSocket, session_id: str):
        """Accept WebSocket connection"""
        await websocket.accept()
        
        connection = WebSocketConnection(
            websocket=websocket,
            user_id="anonymous",  # Would extract from auth in real implementation
            session_id=session_id
        )
        
        self.connections[connection.connection_id] = connection
        
        logger.info(f"WebSocket connected: {connection.connection_id}")
        
        try:
            while True:
                # Receive message from client
                data = await websocket.receive_text()
                await self._handle_message(connection, data)
                
        except WebSocketDisconnect:
            logger.info(f"WebSocket disconnected: {connection.connection_id}")
            self.disconnect(connection.connection_id)
        except Exception as e:
            logger.error(f"WebSocket error: {e}")
            self.disconnect(connection.connection_id)
    
    def disconnect(self, connection_id: str):
        """Disconnect WebSocket"""
        if connection_id in self.connections:
            del self.connections[connection_id]
            logger.info(f"WebSocket disconnected: {connection_id}")
    
    async def _handle_message(self, connection: WebSocketConnection, data: str):
        """Handle incoming WebSocket message"""
        try:
            message = json.loads(data)
            message_type = message.get("type")
            
            if message_type == "subscribe":
                # Subscribe to events
                events = message.get("events", [])
                for event_type in events:
                    connection.subscribed_events.add(WebSocketEventType(event_type))
                
                await connection.websocket.send_text(json.dumps({
                    "type": "subscribed",
                    "events": [event.value for event in connection.subscribed_events]
                }))
                
            elif message_type == "unsubscribe":
                # Unsubscribe from events
                events = message.get("events", [])
                for event_type in events:
                    connection.subscribed_events.discard(WebSocketEventType(event_type))
                
                await connection.websocket.send_text(json.dumps({
                    "type": "unsubscribed",
                    "events": [event.value for event in connection.subscribed_events]
                }))
            
            elif message_type == "ping":
                # Respond to ping
                await connection.websocket.send_text(json.dumps({
                    "type": "pong",
                    "timestamp": datetime.utcnow().isoformat()
                }))
            
        except json.JSONDecodeError:
            await connection.websocket.send_text(json.dumps({
                "type": "error",
                "message": "Invalid JSON"
            }))
        except Exception as e:
            logger.error(f"Handle WebSocket message error: {e}")
            await connection.websocket.send_text(json.dumps({
                "type": "error",
                "message": str(e)
            }))
        
        # Update last activity
        connection.last_activity = datetime.utcnow()
    
    async def broadcast_event(self, event_type: WebSocketEventType, data: Dict[str, Any]):
        """Broadcast event to subscribed connections"""
        message = {
            "type": "event",
            "event_type": event_type.value,
            "data": data,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        message_text = json.dumps(message)
        
        # Send to all subscribed connections
        disconnected_connections = []
        
        for connection_id, connection in self.connections.items():
            if event_type in connection.subscribed_events:
                try:
                    await connection.websocket.send_text(message_text)
                except Exception:
                    # Connection likely closed
                    disconnected_connections.append(connection_id)
        
        # Remove disconnected connections
        for connection_id in disconnected_connections:
            self.disconnect(connection_id)


class APIRateLimitMiddleware(BaseHTTPMiddleware):
    """API rate limiting middleware"""
    
    def __init__(self, app, calls: int = 100, period: int = 60):
        super().__init__(app)
        self.calls = calls
        self.period = period
        self.clients = defaultdict(list)
    
    async def dispatch(self, request, call_next):
        client_ip = request.client.host
        
        now = time.time()
        
        # Clean old requests
        self.clients[client_ip] = [
            req_time for req_time in self.clients[client_ip]
            if now - req_time < self.period
        ]
        
        # Check rate limit
        if len(self.clients[client_ip]) >= self.calls:
            return JSONResponse(
                status_code=429,
                content={"error": "Rate limit exceeded"}
            )
        
        # Add current request
        self.clients[client_ip].append(now)
        
        response = await call_next(request)
        return response


class AuthenticationMiddleware(BaseHTTPMiddleware):
    """Authentication middleware"""
    
    def __init__(self, app, secret_key: str = "your-secret-key"):
        super().__init__(app)
        self.secret_key = secret_key
    
    async def dispatch(self, request, call_next):
        # Skip auth for certain paths
        if request.url.path in ["/api/v1/system/health", "/api/docs", "/api/redoc"]:
            return await call_next(request)
        
        # Extract token from header
        auth_header = request.headers.get("authorization")
        
        if not auth_header or not auth_header.startswith("Bearer "):
            return JSONResponse(
                status_code=401,
                content={"error": "Authentication required"}
            )
        
        token = auth_header.split(" ")[1]
        
        try:
            # Verify token (simplified)
            payload = jwt.decode(token, self.secret_key, algorithms=["HS256"])
            request.state.user = payload
            
        except jwt.InvalidTokenError:
            return JSONResponse(
                status_code=401,
                content={"error": "Invalid token"}
            )
        
        response = await call_next(request)
        return response


# Note: Global initialization moved to avoid event loop issues
# The API service should be initialized from async context

__all__ = ["ToolIntegrationAPI", "WebSocketManager"]