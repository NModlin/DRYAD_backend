"""
Agent Registry API Endpoints - Level 1 Component

API endpoints for the Agent Registry Service.
Provides agent registration, discovery, and capability management.

Part of DRYAD.AI Agent Evolution Architecture Level 1.
"""

from typing import Dict, Any, Optional, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from app.database.database import get_db
from app.services.agent_registry_service import AgentRegistryService
from app.models.agent_registry import (
    SystemAgentCreate, SystemAgentResponse, AgentTier, AgentStatus,
    OrchestrationPattern
)
from app.services.logging.logger import StructuredLogger
from app.core.security import get_current_user

router = APIRouter(prefix="/agents", tags=["agents"])
logger = StructuredLogger("agents_api")


# API Schemas
class AgentRegistrationRequest(BaseModel):
    """Schema for agent registration."""
    agent_id: str = Field(..., description="Unique agent identifier")
    name: str = Field(..., description="Agent name")
    display_name: str = Field(..., description="Human-readable display name")
    tier: AgentTier = Field(..., description="Agent tier")
    category: str = Field(..., description="Agent category")
    capabilities: List[str] = Field([], description="Agent capabilities")
    description: Optional[str] = Field(None, description="Agent description")
    role: Optional[str] = Field(None, description="Agent role")
    goal: Optional[str] = Field(None, description="Agent goal")
    backstory: Optional[str] = Field(None, description="Agent backstory")
    orchestration_pattern: OrchestrationPattern = Field(OrchestrationPattern.HIERARCHICAL, description="Orchestration pattern")
    can_collaborate_directly: bool = Field(False, description="Can collaborate peer-to-peer")
    preferred_collaborators: List[str] = Field([], description="Preferred collaborator agent IDs")
    configuration: Dict[str, Any] = Field({}, description="Agent configuration")
    llm_config: Optional[Dict[str, Any]] = Field(None, description="LLM configuration")
    tools: List[str] = Field([], description="Available tools")


class AgentDiscoveryRequest(BaseModel):
    """Schema for agent discovery."""
    required_capabilities: List[str] = Field(..., description="Required capabilities")
    optional_capabilities: Optional[List[str]] = Field(None, description="Optional capabilities")
    exclude_agents: Optional[List[str]] = Field(None, description="Agent IDs to exclude")
    min_score: float = Field(0.5, description="Minimum match score")


class AgentDiscoveryResponse(BaseModel):
    """Schema for agent discovery response."""
    agent: SystemAgentResponse
    match_score: float
    required_matches: List[str]
    optional_matches: List[str]
    missing_required: List[str]
    extra_capabilities: List[str]


class CapabilityRegistryResponse(BaseModel):
    """Schema for capability registry response."""
    capabilities: Dict[str, List[str]]
    total_capabilities: int
    total_agents: int


@router.post("/register", response_model=SystemAgentResponse)
async def register_agent(
    request: AgentRegistrationRequest,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Register a new agent in the registry.
    
    Creates a new agent with specified capabilities and configuration.
    """
    try:
        registry = AgentRegistryService(db)
        
        # Convert to internal format
        agent_data = SystemAgentCreate(
            agent_id=request.agent_id,
            name=request.name,
            display_name=request.display_name,
            tier=request.tier,
            category=request.category,
            capabilities=request.capabilities,
            description=request.description,
            role=request.role,
            goal=request.goal,
            backstory=request.backstory,
            configuration=request.configuration,
            llm_config=request.llm_config,
            tools=request.tools,
            status=AgentStatus.ACTIVE
        )
        
        logger.log_info(
            "agent_registration_request",
            {
                "agent_id": request.agent_id,
                "name": request.name,
                "tier": request.tier,
                "category": request.category,
                "capabilities_count": len(request.capabilities),
                "user_id": current_user.get("user_id"),
                "tenant_id": current_user.get("tenant_id")
            }
        )
        
        result = registry.register_agent(
            agent_data, 
            tenant_id=current_user.get("tenant_id")
        )
        
        return result
        
    except ValueError as e:
        logger.log_warning(
            "agent_registration_validation_error",
            {"error": str(e), "agent_id": request.agent_id}
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.log_error(
            "agent_registration_error",
            {"error": str(e), "agent_id": request.agent_id}
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to register agent"
        )


@router.get("/list", response_model=List[SystemAgentResponse])
async def list_agents(
    tier: Optional[AgentTier] = None,
    status: Optional[AgentStatus] = None,
    category: Optional[str] = None,
    capabilities: Optional[str] = None,  # Comma-separated capabilities
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    List agents with optional filtering.
    
    Returns agents matching the specified criteria.
    """
    try:
        registry = AgentRegistryService(db)
        
        # Parse capabilities if provided
        capability_list = None
        if capabilities:
            capability_list = [cap.strip() for cap in capabilities.split(",")]
        
        agents = registry.list_agents(
            tier=tier,
            status=status,
            category=category,
            tenant_id=current_user.get("tenant_id"),
            capabilities=capability_list
        )
        
        logger.log_info(
            "agents_list_request",
            {
                "filter_tier": tier,
                "filter_status": status,
                "filter_category": category,
                "filter_capabilities": capability_list,
                "results_count": len(agents),
                "user_id": current_user.get("user_id")
            }
        )
        
        return agents
        
    except Exception as e:
        logger.log_error(
            "agents_list_error",
            {"error": str(e), "user_id": current_user.get("user_id")}
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list agents"
        )


@router.get("/{agent_id}", response_model=SystemAgentResponse)
async def get_agent(
    agent_id: str,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Get a specific agent by ID.
    
    Returns agent details if found and accessible.
    """
    try:
        registry = AgentRegistryService(db)
        
        agent = registry.get_agent(
            agent_id=agent_id,
            tenant_id=current_user.get("tenant_id")
        )
        
        if not agent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Agent {agent_id} not found"
            )
        
        return agent
        
    except HTTPException:
        raise
    except Exception as e:
        logger.log_error(
            "agent_get_error",
            {"error": str(e), "agent_id": agent_id}
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get agent"
        )


@router.post("/discover", response_model=List[AgentDiscoveryResponse])
async def discover_agents(
    request: AgentDiscoveryRequest,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Discover agents based on capability requirements.
    
    Returns agents that match the required capabilities with scoring.
    """
    try:
        registry = AgentRegistryService(db)
        
        logger.log_info(
            "agent_discovery_request",
            {
                "required_capabilities": request.required_capabilities,
                "optional_capabilities": request.optional_capabilities,
                "exclude_agents": request.exclude_agents,
                "min_score": request.min_score,
                "user_id": current_user.get("user_id")
            }
        )
        
        discovered = registry.discover_agents_by_capabilities(
            required_capabilities=request.required_capabilities,
            optional_capabilities=request.optional_capabilities,
            tenant_id=current_user.get("tenant_id"),
            exclude_agents=request.exclude_agents
        )
        
        # Filter by minimum score
        filtered = [
            AgentDiscoveryResponse(**agent_data)
            for agent_data in discovered
            if agent_data["match_score"] >= request.min_score
        ]
        
        logger.log_info(
            "agent_discovery_completed",
            {
                "candidates_found": len(discovered),
                "candidates_after_filtering": len(filtered),
                "min_score": request.min_score
            }
        )
        
        return filtered
        
    except Exception as e:
        logger.log_error(
            "agent_discovery_error",
            {"error": str(e), "required_capabilities": request.required_capabilities}
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to discover agents"
        )


@router.get("/capabilities/registry", response_model=CapabilityRegistryResponse)
async def get_capability_registry(
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Get the capability registry.
    
    Returns all available capabilities and the agents that provide them.
    """
    try:
        registry = AgentRegistryService(db)
        
        capabilities = registry.get_capability_registry(
            tenant_id=current_user.get("tenant_id")
        )
        
        total_agents = len(set(
            agent_id 
            for agent_list in capabilities.values() 
            for agent_id in agent_list
        ))
        
        return CapabilityRegistryResponse(
            capabilities=capabilities,
            total_capabilities=len(capabilities),
            total_agents=total_agents
        )
        
    except Exception as e:
        logger.log_error(
            "capability_registry_error",
            {"error": str(e), "user_id": current_user.get("user_id")}
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get capability registry"
        )


@router.get("/orchestration/patterns")
async def get_orchestration_patterns(
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Get available orchestration patterns.
    
    Returns orchestration patterns and supporting agents.
    """
    try:
        registry = AgentRegistryService(db)
        
        patterns = registry.get_orchestration_patterns(
            tenant_id=current_user.get("tenant_id")
        )
        
        return {
            "patterns": patterns,
            "available_patterns": list(patterns.keys()),
            "total_agents": len(set(
                agent_id 
                for agent_list in patterns.values() 
                for agent_id in agent_list
            ))
        }
        
    except Exception as e:
        logger.log_error(
            "orchestration_patterns_error",
            {"error": str(e), "user_id": current_user.get("user_id")}
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get orchestration patterns"
        )
