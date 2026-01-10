"""
Agent Factory Service for DRYAD Agent Creation Studio

This service handles validation, instantiation, and management of custom agents
created through the Agent Creation Studio.
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
import uuid
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.custom_agent import (
    AgentSheet, AgentSubmission, CustomAgent, AgentExecution,
    AgentSubmissionCreate, AgentExecutionRequest
)
from app.core.llm_config import get_llm, LLMConfig

logger = logging.getLogger(__name__)


class ValidationResult:
    """Result of agent sheet validation."""
    
    def __init__(self, valid: bool, errors: List[str] = None, warnings: List[str] = None):
        self.valid = valid
        self.errors = errors or []
        self.warnings = warnings or []
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "valid": self.valid,
            "errors": self.errors,
            "warnings": self.warnings
        }


class AgentValidator:
    """Validates agent sheets for correctness and security."""

    FORBIDDEN_OPERATIONS = [
        "system_modification",
        "file_system_access",
        "network_access",
        "credential_storage",
        "database_modification",
        "code_execution"
    ]

    REQUIRED_FIELDS = [
        "agent_sheet_version",
        "metadata.submitted_by",
        "agent_definition.name",
        "agent_definition.display_name",
        "capabilities.role",
        "capabilities.goal",
        "capabilities.backstory",
        "behavior.temperature",
        "integration.dryad_compatible"
    ]

    def __init__(self, db_session=None):
        """Initialize validator with optional database session for tool validation."""
        self.db_session = db_session

    async def validate_agent_sheet(self, sheet: Dict[str, Any]) -> ValidationResult:
        """Validate an agent sheet for correctness and security."""
        errors = []
        warnings = []
        
        # Validate required fields
        for field_path in self.REQUIRED_FIELDS:
            if not self._get_nested_value(sheet, field_path):
                errors.append(f"Required field missing: {field_path}")
        
        # Validate agent name format
        agent_name = sheet.get("agent_definition", {}).get("name", "")
        if not agent_name.replace("_", "").isalnum():
            errors.append("Agent name must contain only alphanumeric characters and underscores")
        
        # Security checks - forbidden operations
        allowed_ops = sheet.get("constraints", {}).get("allowed_operations", [])
        for op in allowed_ops:
            if op in self.FORBIDDEN_OPERATIONS:
                errors.append(f"Forbidden operation not allowed: {op}")
        
        # Validate temperature range
        temp = sheet.get("behavior", {}).get("temperature", 0.5)
        if not isinstance(temp, (int, float)) or not 0.0 <= temp <= 1.0:
            errors.append("Temperature must be a number between 0.0 and 1.0")
        
        # Validate max_tokens
        max_tokens = sheet.get("behavior", {}).get("max_tokens", 2048)
        if not isinstance(max_tokens, int) or not 100 <= max_tokens <= 8192:
            errors.append("max_tokens must be an integer between 100 and 8192")
        
        # Validate LLM provider
        provider = sheet.get("llm_preferences", {}).get("preferred_provider", "")
        valid_providers = ["llamacpp", "ollama", "claude", "gemini"]
        if provider not in valid_providers:
            errors.append(f"Invalid LLM provider: {provider}. Must be one of {valid_providers}")
        
        # DRYAD compatibility checks
        if sheet.get("integration", {}).get("dryad_compatible"):
            if not sheet.get("integration", {}).get("oracle_integration"):
                warnings.append("DRYAD-compatible agents should enable oracle_integration for best results")
        
        # Rate limit validation
        rate_limit = sheet.get("constraints", {}).get("rate_limit", 20)
        if not isinstance(rate_limit, int) or rate_limit < 1 or rate_limit > 100:
            errors.append("rate_limit must be an integer between 1 and 100")
        
        # Execution time validation
        max_exec_time = sheet.get("constraints", {}).get("max_execution_time", 60)
        if not isinstance(max_exec_time, int) or max_exec_time < 5 or max_exec_time > 300:
            errors.append("max_execution_time must be an integer between 5 and 300 seconds")
        
        # Validate test queries exist
        test_queries = sheet.get("validation", {}).get("test_queries", [])
        if not test_queries or len(test_queries) < 1:
            warnings.append("At least one test query is recommended for validation")

        # Validate tools if present
        tools = sheet.get("tools", [])
        if tools and self.db_session:
            tool_validation = await self._validate_tools(tools, sheet)
            errors.extend(tool_validation.get("errors", []))
            warnings.extend(tool_validation.get("warnings", []))
        elif tools and not self.db_session:
            warnings.append("Tool validation skipped - no database session provided")

        return ValidationResult(
            valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )

    async def _validate_tools(self, tools: List[Dict[str, Any]], sheet: Dict[str, Any]) -> Dict[str, Any]:
        """Validate requested tools against tool catalog."""
        errors = []
        warnings = []

        if not tools:
            return {"errors": errors, "warnings": warnings}

        try:
            from app.services.tool_registry.service import ToolRegistryService
            tool_service = ToolRegistryService(self.db_session)

            agent_category = sheet.get("agent_definition", {}).get("category", "unknown")

            for tool in tools:
                tool_id = tool.get("tool_id") or tool.get("name")
                if not tool_id:
                    errors.append("Tool missing 'tool_id' field")
                    continue

                # Validate tool exists and is allowed
                validation = await tool_service.validate_tool_request(
                    tool_id=tool_id,
                    agent_category=agent_category
                )

                if not validation.get("allowed"):
                    errors.append(f"Tool '{tool_id}': {validation.get('reason')}")
                else:
                    constraints = validation.get("constraints", {})
                    if constraints.get("requires_approval"):
                        warnings.append(f"Tool '{tool_id}' requires human approval for execution")

                    # Validate tool configuration if schema exists
                    tool_config = tool.get("configuration", {})
                    if tool_config:
                        # TODO: Validate against configuration_schema
                        pass

        except Exception as e:
            warnings.append(f"Tool validation error: {str(e)}")

        return {"errors": errors, "warnings": warnings}
    
    def _get_nested_value(self, data: Dict[str, Any], path: str) -> Any:
        """Get nested value from dictionary using dot notation."""
        keys = path.split(".")
        value = data
        for key in keys:
            if isinstance(value, dict):
                value = value.get(key)
            else:
                return None
        return value


class CustomAgentInstance:
    """Runtime instance of a custom agent."""
    
    def __init__(
        self,
        name: str,
        role: str,
        goal: str,
        backstory: str,
        temperature: float,
        max_tokens: int,
        llm_provider: str,
        tools: List[Any] = None
    ):
        self.name = name
        self.role = role
        self.goal = goal
        self.backstory = backstory
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.llm_provider = llm_provider
        self.tools = tools or []
        self.llm = None
        
        # Initialize LLM
        self._initialize_llm()
    
    def _initialize_llm(self):
        """Initialize the LLM for this agent."""
        try:
            # Get LLM with custom configuration
            config = LLMConfig(
                provider=self.llm_provider,
                temperature=self.temperature,
                max_tokens=self.max_tokens
            )
            self.llm = get_llm(config)
            logger.info(f"✅ Initialized LLM for agent {self.name} with provider {self.llm_provider}")
        except Exception as e:
            logger.error(f"❌ Failed to initialize LLM for agent {self.name}: {e}")
            raise
    
    async def execute(self, query: str, context: Optional[str] = None) -> Dict[str, Any]:
        """Execute the agent with a query."""
        start_time = datetime.utcnow()
        
        try:
            # Build prompt with agent context
            prompt = self._build_prompt(query, context)
            
            # Execute LLM
            response = await self.llm.ainvoke(prompt)
            
            # Calculate execution time
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            
            # Extract response text
            response_text = response.content if hasattr(response, 'content') else str(response)
            
            # Estimate tokens (rough estimate)
            tokens_used = len(prompt.split()) + len(response_text.split())
            
            return {
                "response": response_text,
                "execution_time": execution_time,
                "tokens_used": tokens_used,
                "success": True
            }
        
        except Exception as e:
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            logger.error(f"❌ Agent {self.name} execution failed: {e}")
            
            return {
                "response": None,
                "execution_time": execution_time,
                "tokens_used": 0,
                "success": False,
                "error": str(e)
            }
    
    def _build_prompt(self, query: str, context: Optional[str] = None) -> str:
        """Build the prompt for the agent."""
        prompt_parts = [
            f"You are a {self.role}.",
            f"Your goal is to: {self.goal}",
            f"Background: {self.backstory}",
            ""
        ]
        
        if context:
            prompt_parts.extend([
                "Context:",
                context,
                ""
            ])
        
        prompt_parts.extend([
            "User Query:",
            query,
            "",
            "Please provide a helpful and accurate response based on your role and expertise."
        ])
        
        return "\n".join(prompt_parts)


class AgentBuilder:
    """Builds agent instances from approved agent sheets."""
    
    async def build_agent(self, sheet: Dict[str, Any], db: Optional[AsyncSession] = None) -> CustomAgentInstance:
        """Build an agent instance from an approved agent sheet."""
        
        # Extract configuration
        config = sheet["agent_definition"]
        capabilities = sheet["capabilities"]
        behavior = sheet["behavior"]
        llm_prefs = sheet["llm_preferences"]
        
        # Create agent instance
        agent = CustomAgentInstance(
            name=config["name"],
            role=capabilities["role"],
            goal=capabilities["goal"],
            backstory=capabilities["backstory"],
            temperature=behavior["temperature"],
            max_tokens=behavior["max_tokens"],
            llm_provider=llm_prefs["preferred_provider"],
            tools=await self._create_tools(sheet.get("tools", []), db)
        )
        
        logger.info(f"✅ Built custom agent: {agent.name}")
        return agent
    
    async def _create_tools(self, tool_configs: List[Dict[str, Any]], db: Optional[AsyncSession] = None) -> List[Any]:
        """Create tools for the agent."""
        # TODO: Implement tool creation based on tool configurations
        # For now, return empty list
        return []


class AgentRegistryManager:
    """Manages the lifecycle of custom agents."""
    
    def __init__(self):
        self.registry: Dict[str, CustomAgentInstance] = {}
        self.builder = AgentBuilder()
    
    async def register_agent(self, agent_config: Dict[str, Any], db: Optional[AsyncSession] = None) -> str:
        """Register a new custom agent."""
        agent_name = agent_config["agent_definition"]["name"]
        
        # Build agent instance
        agent_instance = await self.builder.build_agent(agent_config, db)
        
        # Store in registry
        self.registry[agent_name] = agent_instance
        
        logger.info(f"✅ Registered agent: {agent_name}")
        return agent_name
    
    def get_agent(self, agent_name: str) -> Optional[CustomAgentInstance]:
        """Get an agent from the registry."""
        return self.registry.get(agent_name)
    
    def deactivate_agent(self, agent_name: str):
        """Deactivate an agent."""
        if agent_name in self.registry:
            del self.registry[agent_name]
            logger.info(f"✅ Deactivated agent: {agent_name}")
    
    def list_agents(self) -> List[str]:
        """List all registered agents."""
        return list(self.registry.keys())


# Global registry instance
agent_registry = AgentRegistryManager()


def get_agent_registry() -> AgentRegistryManager:
    """Get the global agent registry."""
    return agent_registry

