"""
Agent Registry API Endpoints

API endpoints for managing the 20-agent swarm system registry.
"""

import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.database import get_db
from app.services.agent_registry_service import AgentRegistryService
from app.models.agent_registry import (
    SystemAgentCreate, SystemAgentUpdate, SystemAgentResponse,
    AgentSelectionRequest, AgentSelectionResponse,
    AgentHealthCheckResponse, AgentMetricsUpdate,
    AgentTier, AgentStatus
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/agent-registry", tags=["Agent Registry"])


@router.post("/register", response_model=SystemAgentResponse, status_code=201)
async def register_agent(
    agent_data: SystemAgentCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Register a new system agent.
    
    This endpoint is used to register built-in system agents (Master Orchestrator,
    Project Manager, etc.) as opposed to user-submitted custom agents.
    """
    try:
        service = AgentRegistryService(db)
        agent = await service.register_agent(agent_data)
        return agent
    except Exception as e:
        logger.error(f"Failed to register agent: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/agents", response_model=List[SystemAgentResponse])
async def list_agents(
    tier: Optional[AgentTier] = Query(None, description="Filter by tier"),
    status: Optional[AgentStatus] = Query(None, description="Filter by status"),
    category: Optional[str] = Query(None, description="Filter by category"),
    db: AsyncSession = Depends(get_db)
):
    """
    List all system agents with optional filters.
    """
    try:
        service = AgentRegistryService(db)
        agents = await service.list_agents(tier=tier, status=status, category=category)
        return agents
    except Exception as e:
        logger.error(f"Failed to list agents: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/agents/{agent_id}", response_model=SystemAgentResponse)
async def get_agent(
    agent_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get a specific agent by ID.
    """
    try:
        service = AgentRegistryService(db)
        agent = await service.get_agent(agent_id)
        
        if not agent:
            raise HTTPException(status_code=404, detail=f"Agent not found: {agent_id}")
        
        return agent
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get agent: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/agents/{agent_id}", response_model=SystemAgentResponse)
async def update_agent(
    agent_id: str,
    update_data: SystemAgentUpdate,
    db: AsyncSession = Depends(get_db)
):
    """
    Update an agent's configuration or status.
    """
    try:
        service = AgentRegistryService(db)
        agent = await service.update_agent(agent_id, update_data)
        
        if not agent:
            raise HTTPException(status_code=404, detail=f"Agent not found: {agent_id}")
        
        return agent
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update agent: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/select", response_model=AgentSelectionResponse)
async def select_agent(
    selection_request: AgentSelectionRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Select the best agent for a task based on required capabilities.
    
    This endpoint uses a capability matching algorithm to find the most
    suitable agent for a given task.
    """
    try:
        service = AgentRegistryService(db)
        selected_agent = await service.select_agent(selection_request)
        
        if not selected_agent:
            raise HTTPException(
                status_code=404,
                detail="No suitable agent found for the requested capabilities"
            )
        
        return selected_agent
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to select agent: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/metrics", status_code=200)
async def update_metrics(
    metrics_update: AgentMetricsUpdate,
    db: AsyncSession = Depends(get_db)
):
    """
    Update agent metrics after task execution.
    
    This endpoint is called after an agent completes a task to update
    its performance metrics.
    """
    try:
        service = AgentRegistryService(db)
        success = await service.update_metrics(metrics_update)
        
        if not success:
            raise HTTPException(
                status_code=404,
                detail=f"Agent not found: {metrics_update.agent_id}"
            )
        
        return {"status": "success", "message": "Metrics updated"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health/{agent_id}", response_model=AgentHealthCheckResponse)
async def health_check(
    agent_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Perform a health check on a specific agent.
    """
    try:
        service = AgentRegistryService(db)
        health_response = await service.health_check(agent_id)
        return health_response
    except Exception as e:
        logger.error(f"Failed to perform health check: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/statistics")
async def get_statistics(
    db: AsyncSession = Depends(get_db)
):
    """
    Get overall agent registry statistics.
    
    Returns counts by tier, status, and other aggregate metrics.
    """
    try:
        service = AgentRegistryService(db)
        stats = await service.get_agent_statistics()
        return stats
    except Exception as e:
        logger.error(f"Failed to get statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tiers")
async def list_tiers():
    """
    List all available agent tiers.
    """
    return {
        "tiers": [
            {
                "value": tier.value,
                "name": tier.name,
                "description": _get_tier_description(tier)
            }
            for tier in AgentTier
        ]
    }


@router.get("/statuses")
async def list_statuses():
    """
    List all available agent statuses.
    """
    return {
        "statuses": [
            {
                "value": status.value,
                "name": status.name,
                "description": _get_status_description(status)
            }
            for status in AgentStatus
        ]
    }


def _get_tier_description(tier: AgentTier) -> str:
    """Get description for an agent tier."""
    descriptions = {
        AgentTier.ORCHESTRATOR: "Strategic coordination and task decomposition",
        AgentTier.SPECIALIST: "Tactical execution of specialized tasks",
        AgentTier.EXECUTION: "Operational execution of specific actions"
    }
    return descriptions.get(tier, "")


def _get_status_description(status: AgentStatus) -> str:
    """Get description for an agent status."""
    descriptions = {
        AgentStatus.ACTIVE: "Agent is operational and available",
        AgentStatus.INACTIVE: "Agent is temporarily disabled",
        AgentStatus.MAINTENANCE: "Agent is undergoing maintenance",
        AgentStatus.ERROR: "Agent has encountered an error"
    }
    return descriptions.get(status, "")

