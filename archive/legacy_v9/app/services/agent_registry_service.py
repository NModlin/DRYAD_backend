"""
Agent Registry Service - Level 1 Component

Enhanced agent registry service for DRYAD.AI Agent Evolution Architecture.
Handles agent registration, discovery, capability management, and dynamic orchestration.

Part of DRYAD.AI Agent Evolution Architecture Level 1.
"""

import asyncio
import logging
import uuid
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func
from enum import Enum

from app.models.agent_registry import (
    SystemAgent, AgentCapabilityMatch, AgentTier, AgentStatus, OrchestrationPattern,
    SystemAgentCreate, SystemAgentUpdate, SystemAgentResponse,
    AgentSelectionRequest, AgentSelectionResponse,
    AgentHealthCheckResponse, AgentMetricsUpdate
)
from app.services.logging.logger import StructuredLogger

logger = StructuredLogger("agent_registry")


class AgentRegistryService:
    """
    Level 1 Component: Agent Registry Service

    Enhanced agent registry for DRYAD.AI Agent Evolution Architecture.
    Provides agent registration, discovery, capability management, and dynamic orchestration.

    Features:
    - Agent registration and metadata management
    - Capability-based agent discovery
    - Health monitoring and metrics tracking
    - Dynamic orchestration pattern support
    - Multi-tenant agent isolation
    """

    def __init__(self, db: AsyncSession):
        self.db = db

        # Configuration
        self.max_agents_per_tenant = 100
        self.default_health_check_interval = 300  # 5 minutes
        self.capability_cache = {}  # Cache for capability lookups

        logger.log_info(
            "agent_registry_initialized",
            {
                "max_agents_per_tenant": self.max_agents_per_tenant,
                "health_check_interval": self.default_health_check_interval
            }
        )
    
    async def register_agent(
        self,
        agent_data: SystemAgentCreate,
        tenant_id: Optional[str] = None
    ) -> SystemAgentResponse:
        """
        Register a new system agent with enhanced validation and multi-tenancy.

        Args:
            agent_data: Agent creation data
            tenant_id: Tenant identifier for isolation

        Returns:
            Created agent response
        """
        try:
            # Validate tenant limits
            if tenant_id:
                # SQLite-compatible JSON query logic
                stmt = select(func.count()).select_from(SystemAgent).filter(
                    SystemAgent.configuration.like(f'%"tenant_id": "{tenant_id}"%')
                )
                result = await self.db.execute(stmt)
                existing_count = result.scalar()

                if existing_count >= self.max_agents_per_tenant:
                    raise ValueError(f"Maximum agents per tenant exceeded: {self.max_agents_per_tenant}")

            # Check for duplicate agent_id
            stmt = select(SystemAgent).filter(SystemAgent.agent_id == agent_data.agent_id)
            result = await self.db.execute(stmt)
            existing = result.scalar_one_or_none()

            if existing:
                raise ValueError(f"Agent with ID {agent_data.agent_id} already exists")

            # Enhance configuration with tenant info
            enhanced_config = agent_data.configuration.copy()
            if tenant_id:
                enhanced_config["tenant_id"] = tenant_id
            enhanced_config["registered_at"] = datetime.now(timezone.utc).isoformat()
            enhanced_config["registry_version"] = "1.0"

            # Create agent with enhanced metadata
            agent = SystemAgent(
                agent_id=agent_data.agent_id,
                name=agent_data.name,
                display_name=agent_data.display_name,
                tier=agent_data.tier,
                category=agent_data.category,
                orchestration_pattern=getattr(agent_data, 'orchestration_pattern', OrchestrationPattern.HIERARCHICAL),
                can_collaborate_directly=getattr(agent_data, 'can_collaborate_directly', False),
                preferred_collaborators=getattr(agent_data, 'preferred_collaborators', []),
                capabilities=agent_data.capabilities,
                description=agent_data.description,
                role=agent_data.role,
                goal=agent_data.goal,
                backstory=agent_data.backstory,
                configuration=enhanced_config,
                llm_config=agent_data.llm_config,
                tools=agent_data.tools,
                status=agent_data.status
            )

            self.db.add(agent)
            await self.db.commit()
            await self.db.refresh(agent)

            # Create capability matches with enhanced proficiency tracking
            for capability in agent_data.capabilities:
                match = AgentCapabilityMatch(
                    capability=capability,
                    agent_id=agent_data.agent_id,
                    proficiency=1.0  # Default proficiency
                )
                self.db.add(match)

            await self.db.commit()

            # Clear capability cache
            self.capability_cache.clear()

            logger.log_info(
                "agent_registered",
                {
                    "agent_id": agent.agent_id,
                    "name": agent.name,
                    "tier": agent.tier.value,
                    "category": agent.category,
                    "capabilities_count": len(agent.capabilities),
                    "tenant_id": tenant_id
                }
            )

            return SystemAgentResponse.model_validate(agent)

        except Exception as e:
            await self.db.rollback()
            logger.log_error(
                "agent_registration_failed",
                {"agent_id": agent_data.agent_id, "error": str(e)}
            )
            raise
    
    async def get_agent(
        self,
        agent_id: str,
        tenant_id: Optional[str] = None
    ) -> Optional[SystemAgentResponse]:
        """
        Get an agent by ID with tenant isolation.

        Args:
            agent_id: Agent identifier
            tenant_id: Tenant identifier for isolation

        Returns:
            Agent response or None
        """
        stmt = select(SystemAgent).filter(SystemAgent.agent_id == agent_id)

        # Apply tenant filtering if specified
        if tenant_id:
            stmt = stmt.filter(
                SystemAgent.configuration.like(f'%"tenant_id": "{tenant_id}"%')
            )

        result = await self.db.execute(stmt)
        agent = result.scalar_one_or_none()

        if agent:
            logger.log_info(
                "agent_retrieved",
                {"agent_id": agent_id, "tenant_id": tenant_id}
            )
            return SystemAgentResponse.model_validate(agent)
        return None
    
    async def list_agents(
        self,
        tier: Optional[AgentTier] = None,
        status: Optional[AgentStatus] = None,
        category: Optional[str] = None,
        tenant_id: Optional[str] = None,
        capabilities: Optional[List[str]] = None
    ) -> List[SystemAgentResponse]:
        """
        List all agents with enhanced filtering and tenant isolation.

        Args:
            tier: Filter by tier
            status: Filter by status
            category: Filter by category
            tenant_id: Filter by tenant
            capabilities: Filter by required capabilities

        Returns:
            List of agent responses
        """
        stmt = select(SystemAgent)

        # Apply filters
        if tier:
            stmt = stmt.filter(SystemAgent.tier == tier)
        if status:
            stmt = stmt.filter(SystemAgent.status == status)
        if category:
            stmt = stmt.filter(SystemAgent.category == category)
        if tenant_id:
            stmt = stmt.filter(
                SystemAgent.configuration.like(f'%"tenant_id": "{tenant_id}"%')
            )

        # Filter by capabilities if specified
        if capabilities:
            for capability in capabilities:
                stmt = stmt.filter(
                    SystemAgent.capabilities.contains([capability])
                )

        stmt = stmt.order_by(SystemAgent.created_at.desc())
        
        result = await self.db.execute(stmt)
        agents = result.scalars().all()

        logger.log_info(
            "agents_listed",
            {
                "total_count": len(agents),
                "tier": tier.value if tier else None,
                "status": status.value if status else None,
                "category": category,
                "tenant_id": tenant_id,
                "capabilities_filter": capabilities
            }
        )

        return [SystemAgentResponse.model_validate(agent) for agent in agents]

    async def discover_agents_by_capabilities(
        self,
        required_capabilities: List[str],
        optional_capabilities: Optional[List[str]] = None,
        tenant_id: Optional[str] = None,
        exclude_agents: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Discover agents based on capability requirements with scoring.

        Args:
            required_capabilities: Must-have capabilities
            optional_capabilities: Nice-to-have capabilities
            tenant_id: Tenant identifier for isolation
            exclude_agents: Agent IDs to exclude

        Returns:
            List of agents with match scores
        """
        stmt = select(SystemAgent).filter(SystemAgent.status == AgentStatus.ACTIVE)

        # Apply tenant filtering
        if tenant_id:
            stmt = stmt.filter(
                SystemAgent.configuration.like(f'%"tenant_id": "{tenant_id}"%')
            )

        # Exclude specified agents
        if exclude_agents:
            stmt = stmt.filter(~SystemAgent.agent_id.in_(exclude_agents))

        result = await self.db.execute(stmt)
        agents = result.scalars().all()
        scored_agents = []

        for agent in agents:
            agent_caps = set(agent.capabilities)
            required_caps = set(required_capabilities)
            optional_caps = set(optional_capabilities or [])

            # Calculate match scores
            required_matches = required_caps & agent_caps
            optional_matches = optional_caps & agent_caps
            missing_required = required_caps - agent_caps

            # Skip agents missing required capabilities
            if missing_required:
                continue

            # Calculate score
            required_score = len(required_matches) / len(required_caps) if required_caps else 1.0
            optional_score = len(optional_matches) / len(optional_caps) if optional_caps else 0.0

            # Bonus for tier and additional capabilities
            tier_bonus = {"orchestrator": 0.3, "specialist": 0.2, "execution": 0.1}.get(agent.tier.value, 0.0)
            extra_caps_bonus = len(agent_caps - required_caps - optional_caps) * 0.05

            total_score = required_score + (optional_score * 0.3) + tier_bonus + extra_caps_bonus

            scored_agents.append({
                "agent": SystemAgentResponse.model_validate(agent),
                "match_score": min(total_score, 1.0),
                "required_matches": list(required_matches),
                "optional_matches": list(optional_matches),
                "missing_required": list(missing_required),
                "extra_capabilities": list(agent_caps - required_caps - optional_caps)
            })

        # Sort by score descending
        scored_agents.sort(key=lambda x: x["match_score"], reverse=True)

        logger.log_info(
            "agents_discovered",
            {
                "required_capabilities": required_capabilities,
                "optional_capabilities": optional_capabilities,
                "candidates_found": len(scored_agents),
                "tenant_id": tenant_id
            }
        )

        return scored_agents

    async def get_capability_registry(self, tenant_id: Optional[str] = None) -> Dict[str, List[str]]:
        """
        Get registry of all capabilities and the agents that provide them.

        Args:
            tenant_id: Tenant identifier for isolation

        Returns:
            Dictionary mapping capabilities to agent IDs
        """
        cache_key = f"capabilities_{tenant_id or 'global'}"

        if cache_key in self.capability_cache:
            return self.capability_cache[cache_key]

        stmt = select(SystemAgent).filter(SystemAgent.status == AgentStatus.ACTIVE)

        if tenant_id:
            stmt = stmt.filter(
                SystemAgent.configuration.like(f'%"tenant_id": "{tenant_id}"%')
            )

        result = await self.db.execute(stmt)
        agents = result.scalars().all()
        capability_map = {}

        for agent in agents:
            for capability in agent.capabilities:
                if capability not in capability_map:
                    capability_map[capability] = []
                capability_map[capability].append(agent.agent_id)

        # Cache the result
        self.capability_cache[cache_key] = capability_map

        logger.log_info(
            "capability_registry_generated",
            {
                "total_capabilities": len(capability_map),
                "tenant_id": tenant_id
            }
        )

        return capability_map

    async def get_orchestration_patterns(self, tenant_id: Optional[str] = None) -> Dict[str, List[str]]:
        """
        Get available orchestration patterns and supporting agents.

        Args:
            tenant_id: Tenant identifier for isolation

        Returns:
            Dictionary mapping patterns to agent IDs
        """
        stmt = select(SystemAgent).filter(SystemAgent.status == AgentStatus.ACTIVE)

        if tenant_id:
            stmt = stmt.filter(
                SystemAgent.configuration.like(f'%"tenant_id": "{tenant_id}"%')
            )

        result = await self.db.execute(stmt)
        agents = result.scalars().all()
        pattern_map = {}

        for agent in agents:
            pattern = agent.orchestration_pattern.value
            if pattern not in pattern_map:
                pattern_map[pattern] = []
            pattern_map[pattern].append(agent.agent_id)

        return pattern_map
    
    async def update_agent(self, agent_id: str, update_data: SystemAgentUpdate) -> Optional[SystemAgentResponse]:
        """
        Update an agent.
        
        Args:
            agent_id: Agent identifier
            update_data: Update data
            
        Returns:
            Updated agent response or None
        """
        stmt = select(SystemAgent).where(SystemAgent.agent_id == agent_id)
        result = await self.db.execute(stmt)
        agent = result.scalar_one_or_none()
        
        if not agent:
            return None
        
        # Update fields
        update_dict = update_data.model_dump(exclude_unset=True)
        for key, value in update_dict.items():
            setattr(agent, key, value)
        
        agent.updated_at = datetime.now(timezone.utc)
        
        await self.db.commit()
        await self.db.refresh(agent)
        
        logger.log_info("agent_updated", {"agent_id": agent_id})
        return SystemAgentResponse.model_validate(agent)
    
    async def select_agent(self, selection_request: AgentSelectionRequest) -> Optional[AgentSelectionResponse]:
        """
        Select the best agent for a task based on capabilities.
        
        Args:
            selection_request: Agent selection criteria
            
        Returns:
            Selected agent or None
        """
        required_caps = set(selection_request.required_capabilities)
        
        # Build query
        stmt = select(SystemAgent).where(
            and_(
                SystemAgent.status == AgentStatus.ACTIVE,
                SystemAgent.agent_id.notin_(selection_request.exclude_agents) if selection_request.exclude_agents else True
            )
        )
        
        if selection_request.tier_preference:
            stmt = stmt.where(SystemAgent.tier == selection_request.tier_preference)
        
        result = await self.db.execute(stmt)
        agents = result.scalars().all()
        
        # Score agents based on capability match
        best_agent = None
        best_score = 0.0
        
        for agent in agents:
            agent_caps = set(agent.capabilities)
            matched = required_caps & agent_caps
            missing = required_caps - agent_caps
            
            # Calculate match score
            if len(required_caps) > 0:
                match_score = len(matched) / len(required_caps)
            else:
                match_score = 1.0
            
            # Bonus for having extra capabilities
            extra_bonus = len(agent_caps - required_caps) * 0.1
            total_score = match_score + extra_bonus
            
            if total_score > best_score:
                best_score = total_score
                best_agent = (agent, matched, missing)
        
        if best_agent:
            agent, matched, missing = best_agent
            return AgentSelectionResponse(
                agent_id=agent.agent_id,
                name=agent.name,
                tier=agent.tier,
                match_score=best_score,
                matched_capabilities=list(matched),
                missing_capabilities=list(missing)
            )
        
        return None
    
    async def update_metrics(self, metrics_update: AgentMetricsUpdate) -> bool:
        """
        Update agent metrics after task execution.
        
        Args:
            metrics_update: Metrics update data
            
        Returns:
            True if successful
        """
        stmt = select(SystemAgent).where(SystemAgent.agent_id == metrics_update.agent_id)
        result = await self.db.execute(stmt)
        agent = result.scalar_one_or_none()
        
        if not agent:
            logger.log_warning("metrics_update_failed", {"error": "Agent not found", "agent_id": metrics_update.agent_id})
            return False
        
        agent.update_metrics(
            success=metrics_update.success,
            execution_time=metrics_update.execution_time,
            tokens_used=metrics_update.tokens_used
        )
        
        await self.db.commit()
        logger.log_debug("metrics_updated", {"agent_id": metrics_update.agent_id})
        return True
    
    async def health_check(self, agent_id: str) -> AgentHealthCheckResponse:
        """
        Perform health check on an agent.
        
        Args:
            agent_id: Agent identifier
            
        Returns:
            Health check response
        """
        stmt = select(SystemAgent).where(SystemAgent.agent_id == agent_id)
        result = await self.db.execute(stmt)
        agent = result.scalar_one_or_none()
        
        if not agent:
            return AgentHealthCheckResponse(
                agent_id=agent_id,
                status="unhealthy",
                response_time=0.0,
                last_check=datetime.now(timezone.utc),
                details={"error": "Agent not found"}
            )
        
        # Simple health check - just verify agent exists and is active
        # In a real implementation, this would ping the agent's health_check_url
        status = "healthy" if agent.status == AgentStatus.ACTIVE else "unhealthy"
        
        agent.last_health_check = datetime.now(timezone.utc)
        agent.health_status = status
        
        await self.db.commit()
        
        return AgentHealthCheckResponse(
            agent_id=agent_id,
            status=status,
            response_time=0.0,  # Would be actual response time in real implementation
            last_check=agent.last_health_check,
            details={"agent_status": agent.status.value}
        )
    
    async def get_agent_statistics(self) -> Dict[str, Any]:
        """
        Get overall agent registry statistics.
        
        Returns:
            Statistics dictionary
        """
        # Count by tier
        tier_counts = {}
        for tier in AgentTier:
            stmt = select(func.count()).select_from(SystemAgent).where(SystemAgent.tier == tier)
            result = await self.db.execute(stmt)
            tier_counts[tier.value] = result.scalar()
        
        # Count by status
        status_counts = {}
        for status in AgentStatus:
            stmt = select(func.count()).select_from(SystemAgent).where(SystemAgent.status == status)
            result = await self.db.execute(stmt)
            status_counts[status.value] = result.scalar()
        
        # Total agents
        stmt = select(func.count()).select_from(SystemAgent)
        result = await self.db.execute(stmt)
        total_agents = result.scalar()
        
        return {
            "total_agents": total_agents,
            "by_tier": tier_counts,
            "by_status": status_counts
        }
