"""
Basic Mode Configuration for DRYAD.AI Backend

Provides a minimal operational mode when external services are unavailable,
ensuring the system can still provide basic functionality for demonstration
and testing purposes.
"""

import os
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class BasicModeConfig:
    """Configuration for basic mode operation."""
    enabled: bool = False
    mock_llm_responses: bool = True
    use_sqlite_only: bool = True
    disable_vector_search: bool = True
    disable_background_tasks: bool = True
    disable_multimodal: bool = True
    enable_health_checks: bool = True
    enable_basic_auth: bool = True
    mock_response_delay: float = 0.5  # Simulate processing time


class BasicModeManager:
    """
    Manager for basic mode operation.
    
    Provides minimal functionality when external services are unavailable,
    ensuring the system can still operate for demonstration purposes.
    """
    
    def __init__(self):
        self.config = self._load_config()
        self._mock_responses = self._initialize_mock_responses()
        self._is_active = False
        
    def _load_config(self) -> BasicModeConfig:
        """Load basic mode configuration from environment."""
        return BasicModeConfig(
            enabled=os.getenv("BASIC_MODE_ENABLED", "false").lower() == "true",
            mock_llm_responses=os.getenv("BASIC_MODE_MOCK_LLM", "true").lower() == "true",
            use_sqlite_only=os.getenv("BASIC_MODE_SQLITE_ONLY", "true").lower() == "true",
            disable_vector_search=os.getenv("BASIC_MODE_NO_VECTOR", "true").lower() == "true",
            disable_background_tasks=os.getenv("BASIC_MODE_NO_TASKS", "true").lower() == "true",
            disable_multimodal=os.getenv("BASIC_MODE_NO_MULTIMODAL", "true").lower() == "true",
            enable_health_checks=os.getenv("BASIC_MODE_HEALTH_CHECKS", "true").lower() == "true",
            enable_basic_auth=os.getenv("BASIC_MODE_AUTH", "true").lower() == "true",
            mock_response_delay=float(os.getenv("BASIC_MODE_DELAY", "0.5"))
        )
    
    def _initialize_mock_responses(self) -> Dict[str, List[str]]:
        """Initialize honest error messages for different types of queries."""
        return {
            "general": [
                "🚨 BASIC MODE ACTIVE - Limited Functionality\n\n"
                "❌ ISSUE: Advanced AI features are not available in basic mode.\n\n"
                "🔧 REQUIRED FOR FULL FUNCTIONALITY:\n"
                "- Install missing dependencies: pip install -r requirements.txt\n"
                "- Configure LLM provider (local or external)\n"
                "- Set up optional services (Weaviate, Redis) for advanced features\n\n"
                "✅ CURRENTLY AVAILABLE:\n"
                "- REST/GraphQL API endpoints\n"
                "- Database operations and chat history\n"
                "- Authentication and basic monitoring\n\n"
                "📋 See /docs for complete setup instructions."
            ],

            "search": [
                "🔍 DOCUMENT SEARCH UNAVAILABLE\n\n"
                "❌ ISSUE: Vector search and RAG capabilities require external services.\n\n"
                "🔧 REQUIRED SETUP:\n"
                "- Install Weaviate vector database\n"
                "- Configure WEAVIATE_URL environment variable\n"
                "- Install sentence-transformers for embeddings\n\n"
                "💡 ALTERNATIVE: Basic database search is available through /api/v1/documents/ endpoints."
            ],

            "multimodal": [
                "🎨 MULTIMODAL PROCESSING UNAVAILABLE\n\n"
                "❌ ISSUE: Audio, video, and image processing requires additional dependencies.\n\n"
                "🔧 REQUIRED SETUP:\n"
                "- Install multimodal dependencies: pip install whisper opencv-python pillow\n"
                "- Ensure sufficient system resources for media processing\n"
                "- Configure optional GPU acceleration\n\n"
                "📋 See MULTIMODAL_SETUP.md for detailed instructions."
            ],

            "multi_agent": [
                "🤖 MULTI-AGENT SYSTEM UNAVAILABLE\n\n"
                "❌ ISSUE: DRYAD multi-agent orchestration is not properly configured.\n\n"
                "🔧 REQUIRED SETUP:\n"
                "- Configure LLM provider for agent reasoning\n"
                "- Verify Level 3 Orchestration components are available\n"
                "- Check agent registry and memory guild services\n\n"
                "✅ ALTERNATIVE: Single-agent responses available through /api/v1/agent/ endpoints."
            ],

            "error": [
                "⚠️ SYSTEM ERROR IN BASIC MODE\n\n"
                "❌ ISSUE: An error occurred while processing your request.\n\n"
                "🔧 TROUBLESHOOTING STEPS:\n"
                "1. Check system logs in /logs/ directory\n"
                "2. Verify all required dependencies are installed\n"
                "3. Ensure external services are running if needed\n"
                "4. Try restarting the application\n\n"
                "📞 SUPPORT: Check /docs/troubleshooting for common issues and solutions.\n\n"
                "💡 TIP: Basic mode has limited error recovery. Full mode provides better error handling."
            ]
        }
    
    def activate_basic_mode(self, reason: str = "External services unavailable"):
        """
        Activate basic mode operation.
        
        Args:
            reason: Reason for activating basic mode
        """
        self._is_active = True
        logger.warning(f"Basic mode activated: {reason}")
        
        # Log current configuration
        logger.info(f"Basic mode configuration: {self.config}")
    
    def deactivate_basic_mode(self):
        """Deactivate basic mode and return to normal operation."""
        self._is_active = False
        logger.info("Basic mode deactivated - returning to normal operation")
    
    @property
    def is_active(self) -> bool:
        """Check if basic mode is currently active."""
        return self._is_active or self.config.enabled
    
    def should_use_basic_mode(self, service_health: Dict[str, Any]) -> bool:
        """
        Determine if basic mode should be activated based on service health.
        
        Args:
            service_health: Dictionary of service health statuses
            
        Returns:
            True if basic mode should be activated
        """
        if self.config.enabled:
            return True
        
        # Check critical services
        critical_services = ["database", "llm_provider"]
        critical_failures = 0
        
        for service in critical_services:
            service_status = service_health.get(service, {})
            if service_status.get("status") in ["unhealthy", "unavailable"]:
                critical_failures += 1
        
        # Activate basic mode if multiple critical services are down
        return critical_failures >= len(critical_services) // 2
    
    def get_mock_response(self, query_type: str = "general", query: str = "") -> str:
        """
        Get a mock response for a given query type.
        
        Args:
            query_type: Type of query (general, search, multimodal, multi_agent, error)
            query: Original query text (for context)
            
        Returns:
            Mock response string
        """
        import random
        import time
        
        # Simulate processing delay
        if self.config.mock_response_delay > 0:
            time.sleep(self.config.mock_response_delay)
        
        responses = self._mock_responses.get(query_type, self._mock_responses["general"])
        response = random.choice(responses)
        
        # Add query context if provided
        if query and len(query.strip()) > 0:
            response += f"\n\n(Your query: \"{query[:100]}{'...' if len(query) > 100 else ''}\")"
        
        return response
    
    def get_basic_capabilities(self) -> Dict[str, Any]:
        """
        Get available capabilities in basic mode.
        
        Returns:
            Dictionary of available capabilities
        """
        capabilities = {
            "basic_api": True,
            "health_checks": self.config.enable_health_checks,
            "authentication": self.config.enable_basic_auth,
            "mock_responses": self.config.mock_llm_responses,
            "database": self.config.use_sqlite_only,
            "vector_search": not self.config.disable_vector_search,
            "background_tasks": not self.config.disable_background_tasks,
            "multimodal": not self.config.disable_multimodal
        }
        
        return capabilities
    
    def get_status_info(self) -> Dict[str, Any]:
        """
        Get basic mode status information.
        
        Returns:
            Dictionary with basic mode status
        """
        return {
            "basic_mode_active": self.is_active,
            "configuration": {
                "enabled": self.config.enabled,
                "mock_llm_responses": self.config.mock_llm_responses,
                "use_sqlite_only": self.config.use_sqlite_only,
                "disable_vector_search": self.config.disable_vector_search,
                "disable_background_tasks": self.config.disable_background_tasks,
                "disable_multimodal": self.config.disable_multimodal,
                "enable_health_checks": self.config.enable_health_checks,
                "enable_basic_auth": self.config.enable_basic_auth,
                "mock_response_delay": self.config.mock_response_delay
            },
            "capabilities": self.get_basic_capabilities(),
            "timestamp": datetime.now().isoformat()
        }
    
    def create_basic_mode_response(self, 
                                 original_error: Optional[Exception] = None,
                                 query_type: str = "general",
                                 query: str = "") -> Dict[str, Any]:
        """
        Create a response indicating basic mode operation.
        
        Args:
            original_error: Original error that triggered basic mode
            query_type: Type of query being processed
            query: Original query text
            
        Returns:
            Dictionary with basic mode response
        """
        response = {
            "basic_mode": True,
            "message": self.get_mock_response(query_type, query),
            "capabilities": self.get_basic_capabilities(),
            "timestamp": datetime.now().isoformat()
        }
        
        if original_error:
            response["original_error"] = str(original_error)
            response["error_type"] = type(original_error).__name__
        
        return response
    
    def wrap_endpoint_for_basic_mode(self, endpoint_func):
        """
        Decorator to wrap endpoints for basic mode operation.
        
        Args:
            endpoint_func: Original endpoint function
            
        Returns:
            Wrapped function that handles basic mode
        """
        def wrapper(*args, **kwargs):
            if self.is_active:
                # Return basic mode response
                return self.create_basic_mode_response(
                    query_type="general",
                    query=str(kwargs.get("query", ""))
                )
            
            try:
                return endpoint_func(*args, **kwargs)
            except Exception as e:
                # Fallback to basic mode on error
                logger.warning(f"Endpoint failed, falling back to basic mode: {e}")
                return self.create_basic_mode_response(
                    original_error=e,
                    query_type="error",
                    query=str(kwargs.get("query", ""))
                )
        
        return wrapper


# Global basic mode manager
basic_mode = BasicModeManager()


def is_basic_mode_active() -> bool:
    """Check if basic mode is currently active."""
    return basic_mode.is_active


def get_basic_mode_response(query_type: str = "general", query: str = "") -> str:
    """Get a mock response for basic mode."""
    return basic_mode.get_mock_response(query_type, query)


def activate_basic_mode(reason: str = "Service degradation"):
    """Activate basic mode."""
    basic_mode.activate_basic_mode(reason)


def deactivate_basic_mode():
    """Deactivate basic mode."""
    basic_mode.deactivate_basic_mode()


def basic_mode_fallback(query_type: str = "general"):
    """
    Decorator for basic mode fallback.
    
    Args:
        query_type: Type of query for appropriate mock response
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            if is_basic_mode_active():
                query = str(kwargs.get("query", args[0] if args else ""))
                return basic_mode.create_basic_mode_response(
                    query_type=query_type,
                    query=query
                )
            
            try:
                return func(*args, **kwargs)
            except Exception as e:
                logger.warning(f"Function failed, using basic mode fallback: {e}")
                query = str(kwargs.get("query", args[0] if args else ""))
                return basic_mode.create_basic_mode_response(
                    original_error=e,
                    query_type=query_type,
                    query=query
                )
        
        return wrapper
    return decorator
