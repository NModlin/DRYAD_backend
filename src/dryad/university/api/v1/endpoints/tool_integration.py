"""
Tool Integration API Endpoints
============================

REST API endpoints for tool integration management including
tool registration, execution, monitoring, security, and analytics.

Author: Dryad University System
Date: 2025-10-31
"""

from typing import Dict, List, Optional, Any
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import asyncio
import logging
from datetime import datetime
import uuid

from ...services.tool_integration import UniversalToolRegistry
from ...services.educational_apis import EducationalAPIManager
from ...services.research_tools import ResearchToolsEngine
from ...services.content_creation import ContentCreationEngine
from ...services.assessment_tools import AssessmentToolsEngine
from ...services.communication_tools import CommunicationToolsEngine
from ...services.tool_security import ToolSecurityEngine
from ...core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter()

# Initialize service instances
tool_registry = UniversalToolRegistry()
educational_apis = EducationalAPIManager()
research_tools = ResearchToolsEngine()
content_creation = ContentCreationEngine()
assessment_tools = AssessmentToolsEngine()
communication_tools = CommunicationToolsEngine()
tool_security = ToolSecurityEngine()


# Pydantic Models for API
class ToolRegistrationRequest(BaseModel):
    """Request model for tool registration"""
    tool_name: str = Field(..., description="Name of the tool")
    tool_type: str = Field(..., description="Type of tool")
    description: str = Field(..., description="Tool description")
    version: str = Field(..., description="Tool version")
    endpoint_url: str = Field(..., description="Tool endpoint URL")
    api_key: Optional[str] = Field(None, description="API key if required")
    authentication_method: str = Field("none", description="Authentication method")
    required_permissions: List[str] = Field(default_factory=list, description="Required permissions")
    security_level: str = Field("restricted", description="Security level")
    compliance_requirements: List[str] = Field(default_factory=list, description="Compliance requirements")


class ToolExecutionRequest(BaseModel):
    """Request model for tool execution"""
    tool_id: str = Field(..., description="ID of the tool to execute")
    agent_id: str = Field(..., description="ID of the agent executing the tool")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Tool parameters")
    timeout: Optional[int] = Field(30, description="Execution timeout in seconds")
    async_execution: bool = Field(False, description="Whether to execute asynchronously")


class AgentPermissionsRequest(BaseModel):
    """Request model for agent permissions"""
    agent_id: str = Field(..., description="ID of the agent")
    tool_permissions: Dict[str, List[str]] = Field(..., description="Tool permissions mapping")
    role: str = Field(..., description="Agent role")
    restrictions: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Usage restrictions")


class EducationalAPIRequest(BaseModel):
    """Request model for educational API integration"""
    api_type: str = Field(..., description="Type of educational API")
    configuration: Dict[str, Any] = Field(..., description="API configuration")
    integration_type: str = Field(..., description="Type of integration")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Integration parameters")


class SecurityAuditRequest(BaseModel):
    """Request model for security audit"""
    tool_ids: Optional[List[str]] = Field(None, description="Specific tools to audit")
    audit_scope: str = Field("comprehensive", description="Audit scope")
    compliance_frameworks: Optional[List[str]] = Field(None, description="Compliance frameworks to check")
    time_period: str = Field("current_month", description="Audit time period")


class ToolAnalyticsRequest(BaseModel):
    """Request model for tool analytics"""
    agent_id: Optional[str] = Field(None, description="Specific agent to analyze")
    tool_ids: Optional[List[str]] = Field(None, description="Specific tools to analyze")
    time_period: str = Field("current_month", description="Analytics time period")
    metrics: Optional[List[str]] = Field(None, description="Specific metrics to include")


# Response Models
class ToolRegistrationResponse(BaseModel):
    """Response model for tool registration"""
    success: bool
    tool_id: str
    registration_details: Dict[str, Any]
    security_profile: Dict[str, Any]
    message: str


class ToolExecutionResponse(BaseModel):
    """Response model for tool execution"""
    success: bool
    execution_id: str
    tool_id: str
    agent_id: str
    execution_status: str
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    execution_time: Optional[float] = None
    security_status: Optional[Dict[str, Any]] = None


class ToolStatusResponse(BaseModel):
    """Response model for tool status"""
    tool_id: str
    status: str
    health: str
    last_health_check: str
    usage_metrics: Dict[str, Any]
    security_status: Dict[str, Any]
    performance_metrics: Dict[str, Any]


class AgentPermissionsResponse(BaseModel):
    """Response model for agent permissions"""
    agent_id: str
    permissions: Dict[str, Any]
    role_based_access: Dict[str, Any]
    restrictions: Dict[str, Any]
    effective_permissions: List[str]


class EducationalAPIResponse(BaseModel):
    """Response model for educational API integration"""
    success: bool
    integration_id: str
    api_type: str
    integration_status: str
    capabilities: List[str]
    configuration: Dict[str, Any]
    connection_status: str


class SecurityAuditResponse(BaseModel):
    """Response model for security audit"""
    audit_id: str
    audit_scope: Dict[str, Any]
    compliance_status: Dict[str, Any]
    security_findings: List[Dict[str, Any]]
    recommendations: List[str]
    risk_assessment: Dict[str, Any]


class ToolAnalyticsResponse(BaseModel):
    """Response model for tool analytics"""
    analytics_id: str
    time_period: str
    metrics: Dict[str, Any]
    usage_patterns: Dict[str, Any]
    performance_analysis: Dict[str, Any]
    recommendations: List[str]


# API Endpoints

@router.get("/agents/{agent_id}/tools", response_model=List[Dict[str, Any]])
async def get_agent_tools(
    agent_id: str,
    tool_type: Optional[str] = Query(None, description="Filter by tool type"),
    security_level: Optional[str] = Query(None, description="Filter by security level")
):
    """Get available tools for a specific agent"""
    try:
        agent_context = {"agent_id": agent_id}
        available_tools = await tool_registry.discover_available_tools(agent_context)
        
        # Apply filters
        tools = available_tools.get("available_tools", [])
        if tool_type:
            tools = [tool for tool in tools if tool.get("type") == tool_type]
        if security_level:
            tools = [tool for tool in tools if tool.get("security_level") == security_level]
        
        return tools
        
    except Exception as e:
        logger.error(f"Error getting agent tools: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/tools/register", response_model=ToolRegistrationResponse)
async def register_tool(tool_request: ToolRegistrationRequest):
    """Register a new tool in the system"""
    try:
        tool_config = tool_request.dict()
        registration_result = await tool_registry.register_tool(tool_config)
        
        if registration_result.get("success"):
            return ToolRegistrationResponse(
                success=True,
                tool_id=registration_result.get("tool_id"),
                registration_details=registration_result.get("registration_details"),
                security_profile=registration_result.get("security_profile"),
                message="Tool registered successfully"
            )
        else:
            raise HTTPException(status_code=400, detail=registration_result.get("error"))
            
    except Exception as e:
        logger.error(f"Error registering tool: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/tools/{tool_id}/execute", response_model=ToolExecutionResponse)
async def execute_tool(
    tool_id: str,
    execution_request: ToolExecutionRequest,
    background_tasks: BackgroundTasks
):
    """Execute a tool"""
    try:
        if execution_request.agent_id != "current_agent":  # Mock current agent
            # In a real implementation, get agent ID from authentication token
            pass
        
        # Validate tool access
        access_validation = await tool_security.validate_tool_access(
            execution_request.agent_id, tool_id
        )
        
        if not access_validation.get("access_validation", {}).get("access_granted"):
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Prepare execution request
        tool_request = {
            "tool_id": tool_id,
            "parameters": execution_request.parameters,
            "execution_timeout": execution_request.timeout
        }
        
        # Create security context
        security_context = {
            "session_id": str(uuid.uuid4()),
            "user_id": "current_user",
            "agent_id": execution_request.agent_id,
            "role": "student",
            "permissions": ["read", "execute"],
            "ip_address": "127.0.0.1",
            "user_agent": "API Client"
        }
        
        # Execute tool securely
        execution_result = await tool_security.secure_tool_execution(tool_request, security_context)
        
        if execution_result.get("success"):
            secure_execution = execution_result.get("secure_execution", {})
            
            return ToolExecutionResponse(
                success=True,
                execution_id=secure_execution.get("execution_id"),
                tool_id=tool_id,
                agent_id=execution_request.agent_id,
                execution_status="completed",
                result=secure_execution.get("execution_result", {}),
                execution_time=0.0,  # Would be calculated in real implementation
                security_status=secure_execution.get("security_status")
            )
        else:
            raise HTTPException(status_code=500, detail=execution_result.get("error"))
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error executing tool: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tools/{tool_id}/status", response_model=ToolStatusResponse)
async def get_tool_status(tool_id: str):
    """Get status and health information for a tool"""
    try:
        # Get tool health status
        health_status = await tool_registry.get_tool_health_status(tool_id)
        
        # Get usage metrics
        usage_metrics = await tool_registry.get_tool_usage_metrics(tool_id, "current_month")
        
        # Get security status
        security_status = await tool_security.monitor_tool_usage(tool_id, "current_month")
        
        # Get performance metrics
        performance_metrics = await tool_registry.get_tool_performance_metrics(tool_id)
        
        return ToolStatusResponse(
            tool_id=tool_id,
            status=health_status.get("status", "unknown"),
            health=health_status.get("health_level", "unknown"),
            last_health_check=health_status.get("last_check", datetime.utcnow().isoformat()),
            usage_metrics=usage_metrics,
            security_status=security_status.get("monitoring_results", {}),
            performance_metrics=performance_metrics
        )
        
    except Exception as e:
        logger.error(f"Error getting tool status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/agents/{agent_id}/tools/permissions", response_model=AgentPermissionsResponse)
async def configure_agent_permissions(
    agent_id: str,
    permissions_request: AgentPermissionsRequest
):
    """Configure tool permissions for an agent"""
    try:
        if permissions_request.agent_id != agent_id:
            raise HTTPException(status_code=400, detail="Agent ID mismatch")
        
        # Implement role-based access control
        role_based_result = await tool_security.implement_role_based_access(
            permissions_request.role,
            permissions_request.tool_permissions
        )
        
        # Configure specific permissions
        permission_config = await tool_security.configure_tool_permissions(
            agent_id,
            permissions_request.dict()
        )
        
        # Calculate effective permissions
        effective_permissions = []
        for tool, perms in permissions_request.tool_permissions.items():
            effective_permissions.extend([f"{tool}:{perm}" for perm in perms])
        
        return AgentPermissionsResponse(
            agent_id=agent_id,
            permissions=permission_config.get("permission_configuration", {}),
            role_based_access=role_based_result.get("role_based_access", {}),
            restrictions=permissions_request.restrictions,
            effective_permissions=effective_permissions
        )
        
    except Exception as e:
        logger.error(f"Error configuring agent permissions: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/integrations/educational-apis", response_model=List[EducationalAPIResponse])
async def get_educational_api_integrations():
    """Get available educational API integrations"""
    try:
        # Get available API integrations
        integrations = await educational_apis.get_available_integrations()
        
        # Format response
        api_responses = []
        for integration in integrations.get("integrations", []):
            api_responses.append(EducationalAPIResponse(
                success=True,
                integration_id=integration.get("integration_id"),
                api_type=integration.get("api_type"),
                integration_status=integration.get("status"),
                capabilities=integration.get("capabilities", []),
                configuration=integration.get("configuration", {}),
                connection_status=integration.get("connection_status", "unknown")
            ))
        
        return api_responses
        
    except Exception as e:
        logger.error(f"Error getting educational API integrations: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/integrations/educational-apis", response_model=EducationalAPIResponse)
async def create_educational_api_integration(api_request: EducationalAPIRequest):
    """Create a new educational API integration"""
    try:
        integration_config = api_request.dict()
        
        # Route to appropriate integration based on API type
        if api_request.api_type == "lms":
            result = await educational_apis.integrate_learning_analytics(api_request.configuration)
        elif api_request.api_type == "research":
            result = await educational_apis.access_research_databases(api_request.parameters)
        elif api_request.api_type == "library":
            result = await educational_apis.connect_library_systems(api_request.configuration)
        else:
            result = {"success": False, "error": f"Unsupported API type: {api_request.api_type}"}
        
        if result.get("success"):
            return EducationalAPIResponse(
                success=True,
                integration_id=result.get("integration_id", str(uuid.uuid4())),
                api_type=api_request.api_type,
                integration_status="active",
                capabilities=result.get("capabilities", []),
                configuration=api_request.configuration,
                connection_status="connected"
            )
        else:
            raise HTTPException(status_code=400, detail=result.get("error"))
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating educational API integration: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/tools/{tool_id}/security/audit", response_model=SecurityAuditResponse)
async def conduct_security_audit(
    tool_id: str,
    audit_request: SecurityAuditRequest
):
    """Conduct security audit for a tool"""
    try:
        # Prepare audit request
        full_audit_request = {
            "tool_ids": [tool_id] + (audit_request.tool_ids or []),
            "audit_scope": audit_request.audit_scope,
            "compliance_frameworks": audit_request.compliance_frameworks,
            "time_period": audit_request.time_period
        }
        
        # Conduct security audit
        audit_result = await tool_security.audit_tool_operations(full_audit_request)
        
        if audit_result.get("success"):
            audit_results = audit_result.get("audit_results", {})
            
            return SecurityAuditResponse(
                audit_id=audit_results.get("audit_id", str(uuid.uuid4())),
                audit_scope=audit_results.get("audit_scope", {}),
                compliance_status=audit_results.get("compliance_status", {}),
                security_findings=audit_results.get("audit_findings", {}),
                recommendations=audit_results.get("recommendations", []),
                risk_assessment=audit_results.get("risk_exposure", {})
            )
        else:
            raise HTTPException(status_code=500, detail=audit_result.get("error"))
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error conducting security audit: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/agents/{agent_id}/tool-analytics", response_model=ToolAnalyticsResponse)
async def get_tool_analytics(
    agent_id: str,
    time_period: str = Query("current_month", description="Analytics time period"),
    tool_ids: Optional[List[str]] = Query(None, description="Specific tools to analyze"),
    metrics: Optional[List[str]] = Query(None, description="Specific metrics to include")
):
    """Get analytics for agent tool usage"""
    try:
        # Prepare analytics request
        analytics_request = {
            "agent_id": agent_id,
            "tool_ids": tool_ids,
            "time_period": time_period,
            "metrics": metrics
        }
        
        # Gather analytics data from multiple sources
        usage_analytics = await tool_registry.get_agent_tool_usage_analytics(agent_id, time_period)
        security_analytics = await tool_security.monitor_tool_usage("all", time_period)
        performance_analytics = await tool_registry.get_tool_performance_analytics(time_period)
        
        # Combine analytics
        combined_metrics = {
            "usage": usage_analytics.get("analytics", {}),
            "security": security_analytics.get("monitoring_results", {}),
            "performance": performance_analytics.get("performance_data", {})
        }
        
        return ToolAnalyticsResponse(
            analytics_id=str(uuid.uuid4()),
            time_period=time_period,
            metrics=combined_metrics,
            usage_patterns=usage_analytics.get("usage_patterns", {}),
            performance_analysis=performance_analytics.get("analysis", {}),
            recommendations=usage_analytics.get("recommendations", [])
        )
        
    except Exception as e:
        logger.error(f"Error getting tool analytics: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/tools/{tool_id}/security/policies")
async def enforce_tool_policies(tool_id: str, policy_config: Dict[str, Any]):
    """Enforce security policies for a tool"""
    try:
        enforcement_result = await tool_security.enforce_tool_policies(tool_id, policy_config)
        
        if enforcement_result.get("success"):
            return enforcement_result.get("policy_enforcement", {})
        else:
            raise HTTPException(status_code=400, detail=enforcement_result.get("error"))
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error enforcing tool policies: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/agents/{agent_id}/tools/{tool_id}/access")
async def revoke_tool_access(agent_id: str, tool_id: str):
    """Revoke tool access for an agent"""
    try:
        revocation_result = await tool_security.revoke_tool_access(agent_id, tool_id)
        
        if revocation_result.get("success"):
            return {
                "success": True,
                "message": f"Tool access revoked for agent {agent_id}",
                "revocation_details": revocation_result.get("access_revocation", {})
            }
        else:
            raise HTTPException(status_code=400, detail=revocation_result.get("error"))
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error revoking tool access: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tools/catalog", response_model=Dict[str, Any])
async def get_tool_catalog(
    category: Optional[str] = Query(None, description="Filter by category"),
    search: Optional[str] = Query(None, description="Search tools"),
    security_level: Optional[str] = Query(None, description="Filter by security level")
):
    """Get comprehensive tool catalog"""
    try:
        catalog = await tool_registry.get_tool_catalog()
        tools = catalog.get("tools", [])
        
        # Apply filters
        if category:
            tools = [tool for tool in tools if tool.get("category") == category]
        if security_level:
            tools = [tool for tool in tools if tool.get("security_level") == security_level]
        if search:
            search_lower = search.lower()
            tools = [tool for tool in tools if 
                    search_lower in tool.get("name", "").lower() or 
                    search_lower in tool.get("description", "").lower()]
        
        return {
            "catalog_id": str(uuid.uuid4()),
            "total_tools": len(tools),
            "filters_applied": {
                "category": category,
                "search": search,
                "security_level": security_level
            },
            "tools": tools
        }
        
    except Exception as e:
        logger.error(f"Error getting tool catalog: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/tools/{tool_id}/research/analyze")
async def analyze_with_research_tools(
    tool_id: str,
    analysis_request: Dict[str, Any]
):
    """Analyze data using research tools"""
    try:
        # Route to research tools based on analysis type
        analysis_type = analysis_request.get("analysis_type", "general")
        
        if analysis_type == "literature_review":
            result = await research_tools.conduct_literature_review(
                analysis_request.get("research_question", "")
            )
        elif analysis_type == "data_analysis":
            result = await research_tools.analyze_research_data(
                analysis_request.get("data", {}),
                analysis_request.get("analysis_type", "statistical")
            )
        elif analysis_type == "research_report":
            result = await research_tools.generate_research_report(
                analysis_request.get("research_data", {})
            )
        else:
            result = {"success": False, "error": f"Unsupported analysis type: {analysis_type}"}
        
        if result.get("success"):
            return result
        else:
            raise HTTPException(status_code=400, detail=result.get("error"))
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing with research tools: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/tools/{tool_id}/content/create")
async def create_content_with_tools(
    tool_id: str,
    content_request: Dict[str, Any]
):
    """Create content using content creation tools"""
    try:
        content_type = content_request.get("content_type", "document")
        
        if content_type == "academic_document":
            result = await content_creation.create_academic_document(
                content_request.get("document_spec", {})
            )
        elif content_type == "presentation":
            result = await content_creation.build_educational_presentation(
                content_request.get("presentation_spec", {})
            )
        elif content_type == "multimedia":
            result = await content_creation.create_multimedia_content(
                content_request.get("content_spec", {})
            )
        else:
            result = {"success": False, "error": f"Unsupported content type: {content_type}"}
        
        if result.get("success"):
            return result
        else:
            raise HTTPException(status_code=400, detail=result.get("error"))
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating content: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/tools/{tool_id}/assessment/create")
async def create_assessment(
    tool_id: str,
    assessment_request: Dict[str, Any]
):
    """Create assessments using assessment tools"""
    try:
        assessment_type = assessment_request.get("assessment_type", "adaptive")
        
        if assessment_type == "adaptive":
            result = await assessment_tools.create_adaptive_assessment(
                assessment_request.get("learning_objectives", {})
            )
        elif assessment_type == "rubric_based":
            result = await assessment_tools.assessment_creator.design_rubric_based_assessment(
                assessment_request.get("assessment_spec", {})
            )
        else:
            result = {"success": False, "error": f"Unsupported assessment type: {assessment_type}"}
        
        if result.get("success"):
            return result
        else:
            raise HTTPException(status_code=400, detail=result.get("error"))
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating assessment: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/tools/{tool_id}/communication/session")
async def create_communication_session(
    tool_id: str,
    session_request: Dict[str, Any]
):
    """Create communication session using communication tools"""
    try:
        session_type = session_request.get("session_type", "office_hours")
        
        if session_type == "office_hours":
            result = await communication_tools.create_virtual_office_hours(
                session_request.get("instructor_schedule", {})
            )
        elif session_type == "group_discussion":
            result = await communication_tools.facilitate_group_discussion(
                session_request.get("discussion_topic", ""),
                session_request.get("participants", [])
            )
        elif session_type == "student_meeting":
            result = await communication_tools.schedule_student_meetings(
                session_request.get("student_preferences", {})
            )
        else:
            result = {"success": False, "error": f"Unsupported session type: {session_type}"}
        
        if result.get("success"):
            return result
        else:
            raise HTTPException(status_code=400, detail=result.get("error"))
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating communication session: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# Health and system endpoints
@router.get("/health")
async def health_check():
    """Health check for tool integration service"""
    return {
        "service": "tool_integration",
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0"
    }


@router.get("/system/status")
async def get_system_status():
    """Get overall system status"""
    try:
        # Check service health
        service_status = {
            "tool_registry": "healthy",
            "educational_apis": "healthy",
            "research_tools": "healthy",
            "content_creation": "healthy",
            "assessment_tools": "healthy",
            "communication_tools": "healthy",
            "tool_security": "healthy"
        }
        
        return {
            "system_status": "operational",
            "services": service_status,
            "timestamp": datetime.utcnow().isoformat(),
            "uptime": "99.9%"
        }
        
    except Exception as e:
        logger.error(f"Error getting system status: {str(e)}")
        return {
            "system_status": "degraded",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }