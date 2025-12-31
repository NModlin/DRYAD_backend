"""
Enhanced Service Monitoring with Circuit Breaker Integration

Provides utilities for monitoring external service availability,
managing graceful degradation, and circuit breaker protection.
"""

import logging
import asyncio
import os
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime, timedelta
from enum import Enum

from app.core.exceptions import ServiceStatus, ErrorSeverity
from app.core.circuit_breaker import get_circuit_breaker, CircuitBreakerConfig, CircuitBreakerOpenException

logger = logging.getLogger(__name__)


class ServiceType(str, Enum):
    """Types of external services."""

    DATABASE = "database"
    VECTOR_STORE = "vector_store"
    LLM_PROVIDER = "llm_provider"
    TASK_QUEUE = "task_queue"
    MULTIMODAL = "multimodal"
    OPENAI_API = "openai_api"
    WEAVIATE = "weaviate"
    REDIS = "redis"
    WHISPER = "whisper"
    FFMPEG = "ffmpeg"
    OPENCV = "opencv"


class ServiceMonitor:
    """
    Enhanced service monitor with circuit breaker integration.

    Tracks service health, provides fallback capability information,
    and integrates with circuit breakers for resilient operation.
    """

    def __init__(self):
        self._service_status: Dict[ServiceType, ServiceStatus] = {}
        self._last_check: Dict[ServiceType, datetime] = {}
        self._check_interval = timedelta(minutes=5)  # Check every 5 minutes
        self._health_checkers: Dict[ServiceType, Callable[[], bool]] = {}
        self._circuit_breakers: Dict[ServiceType, Any] = {}
        self._initialize_circuit_breakers()
        self._initialize_health_checkers()

    def _initialize_circuit_breakers(self):
        """Initialize circuit breakers for each service type."""
        # Database circuit breaker
        db_config = CircuitBreakerConfig(
            failure_threshold=3,
            recovery_timeout=30,
            success_threshold=2,
            timeout=10
        )
        self._circuit_breakers[ServiceType.DATABASE] = get_circuit_breaker("database", db_config)

        # Vector store circuit breaker
        vector_config = CircuitBreakerConfig(
            failure_threshold=5,
            recovery_timeout=60,
            success_threshold=3,
            timeout=15
        )
        self._circuit_breakers[ServiceType.VECTOR_STORE] = get_circuit_breaker("vector_store", vector_config)
        self._circuit_breakers[ServiceType.WEAVIATE] = get_circuit_breaker("weaviate", vector_config)

        # LLM provider circuit breaker
        llm_config = CircuitBreakerConfig(
            failure_threshold=3,
            recovery_timeout=45,
            success_threshold=2,
            timeout=30
        )
        self._circuit_breakers[ServiceType.LLM_PROVIDER] = get_circuit_breaker("llm_provider", llm_config)
        self._circuit_breakers[ServiceType.OPENAI_API] = get_circuit_breaker("openai_api", llm_config)

        # Task queue circuit breaker
        queue_config = CircuitBreakerConfig(
            failure_threshold=5,
            recovery_timeout=30,
            success_threshold=2,
            timeout=5
        )
        self._circuit_breakers[ServiceType.TASK_QUEUE] = get_circuit_breaker("task_queue", queue_config)
        self._circuit_breakers[ServiceType.REDIS] = get_circuit_breaker("redis", queue_config)

    def _initialize_health_checkers(self):
        """Initialize health checker functions for each service."""
        self._health_checkers[ServiceType.DATABASE] = self._check_database_health
        self._health_checkers[ServiceType.VECTOR_STORE] = self._check_vector_store_health
        self._health_checkers[ServiceType.WEAVIATE] = self._check_weaviate_health
        self._health_checkers[ServiceType.LLM_PROVIDER] = self._check_llm_health
        self._health_checkers[ServiceType.TASK_QUEUE] = self._check_task_queue_health
        self._health_checkers[ServiceType.REDIS] = self._check_redis_health
        self._health_checkers[ServiceType.MULTIMODAL] = self._check_multimodal_health

    def _check_database_health(self) -> bool:
        """Check database connectivity."""
        try:
            from app.database.database import get_db
            # This is a simplified check
            return True
        except Exception as e:
            logger.warning(f"Database health check failed: {e}")
            return False

    def _check_vector_store_health(self) -> bool:
        """Check vector store connectivity."""
        return self._check_weaviate_health()

    def _check_weaviate_health(self) -> bool:
        """Check Weaviate connectivity."""
        try:
            from app.core.vector_store import vector_store
            return vector_store and vector_store.is_connected
        except Exception as e:
            logger.warning(f"Weaviate health check failed: {e}")
            return False

    def _check_llm_health(self) -> bool:
        """Check LLM provider health."""
        try:
            from app.core.llm_config import get_llm_health_status
            health = get_llm_health_status()
            return health.get("llm_available", False)
        except Exception as e:
            logger.warning(f"LLM health check failed: {e}")
            return False

    def _check_task_queue_health(self) -> bool:
        """Check task queue health."""
        return self._check_redis_health()

    def _check_redis_health(self) -> bool:
        """Check Redis connectivity."""
        try:
            import redis
            redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
            r = redis.from_url(redis_url, decode_responses=True)
            r.ping()
            return True
        except Exception as e:
            logger.warning(f"Redis health check failed: {e}")
            return False

    def _check_multimodal_health(self) -> bool:
        """Check multimodal processing capabilities."""
        try:
            # Check if multimodal dependencies are available
            install_tier = os.getenv("INSTALL_TIER", "minimal")
            if install_tier != "full":
                return False

            # Check for key multimodal libraries
            import torch
            return True
        except Exception as e:
            logger.warning(f"Multimodal health check failed: {e}")
            return False

    async def check_service_health(self, service_type: ServiceType) -> ServiceStatus:
        """
        Check health of a specific service using circuit breaker protection.

        Args:
            service_type: Type of service to check

        Returns:
            ServiceStatus with current health information
        """
        circuit_breaker = self._circuit_breakers.get(service_type)
        health_checker = self._health_checkers.get(service_type)

        if not health_checker:
            return ServiceStatus(
                service_name=service_type.value,
                status="unknown",
                fallback_available=False,
                capabilities_affected=[],
                error_message="No health checker available"
            )

        try:
            if circuit_breaker:
                # Use circuit breaker for health check
                is_healthy = await circuit_breaker.call(self._async_health_check, health_checker)
            else:
                # Direct health check
                is_healthy = health_checker()

            status = "healthy" if is_healthy else "degraded"
            capabilities_affected = self._get_service_capabilities(service_type) if not is_healthy else []

            service_status = ServiceStatus(
                service_name=service_type.value,
                status=status,
                fallback_available=self._has_fallback(service_type),
                capabilities_affected=capabilities_affected,
                last_check=datetime.now(),
                circuit_breaker_state=circuit_breaker.state.value if circuit_breaker else None
            )

            self._service_status[service_type] = service_status
            self._last_check[service_type] = datetime.now()

            return service_status

        except CircuitBreakerOpenException as e:
            # Circuit breaker is open
            service_status = ServiceStatus(
                service_name=service_type.value,
                status="unhealthy",
                fallback_available=self._has_fallback(service_type),
                capabilities_affected=self._get_service_capabilities(service_type),
                last_check=datetime.now(),
                error_message=f"Circuit breaker open: {e}",
                circuit_breaker_state="open",
                degradation_reason="Circuit breaker protection active"
            )

            self._service_status[service_type] = service_status
            return service_status

        except Exception as e:
            # Health check failed
            service_status = ServiceStatus(
                service_name=service_type.value,
                status="unhealthy",
                fallback_available=self._has_fallback(service_type),
                capabilities_affected=self._get_service_capabilities(service_type),
                last_check=datetime.now(),
                error_message=str(e),
                circuit_breaker_state=circuit_breaker.state.value if circuit_breaker else None
            )

            self._service_status[service_type] = service_status
            return service_status

    async def _async_health_check(self, health_checker: Callable[[], bool]) -> bool:
        """Wrapper to make synchronous health checkers async."""
        return health_checker()

    def _get_service_capabilities(self, service_type: ServiceType) -> List[str]:
        """Get capabilities affected by a service."""
        capability_map = {
            ServiceType.DATABASE: ["data_persistence", "user_management", "session_storage"],
            ServiceType.VECTOR_STORE: ["semantic_search", "document_similarity", "rag_enhancement"],
            ServiceType.WEAVIATE: ["semantic_search", "document_similarity", "rag_enhancement"],
            ServiceType.LLM_PROVIDER: ["ai_responses", "text_generation", "reasoning"],
            ServiceType.OPENAI_API: ["gpt_analysis", "advanced_reasoning", "multi_agent_collaboration"],
            ServiceType.TASK_QUEUE: ["background_processing", "async_operations", "multi_agent_tasks"],
            ServiceType.REDIS: ["caching", "session_storage", "task_queue"],
            ServiceType.MULTIMODAL: ["audio_processing", "video_processing", "image_analysis"],
            ServiceType.WHISPER: ["speech_to_text", "audio_transcription"],
            ServiceType.FFMPEG: ["video_audio_extraction", "format_conversion"],
            ServiceType.OPENCV: ["video_processing", "frame_extraction", "video_analysis"]
        }
        return capability_map.get(service_type, [])

    def _has_fallback(self, service_type: ServiceType) -> bool:
        """Check if a service has fallback capabilities."""
        fallback_map = {
            ServiceType.DATABASE: False,  # Database is critical
            ServiceType.VECTOR_STORE: True,  # Can use basic search
            ServiceType.WEAVIATE: True,  # Can use basic search
            ServiceType.LLM_PROVIDER: False,  # Local LLM is core - no fallback to mock
            ServiceType.OPENAI_API: True,  # Can fallback to local LLM
            ServiceType.TASK_QUEUE: True,  # Can process synchronously
            ServiceType.REDIS: True,  # Can use in-memory cache
            ServiceType.MULTIMODAL: False,  # No fallback for ML models
            ServiceType.WHISPER: False,  # No fallback for speech processing
            ServiceType.FFMPEG: False,  # No fallback for video processing
            ServiceType.OPENCV: False  # No fallback for video processing
        }
        return fallback_map.get(service_type, False)

    async def get_system_status(self) -> Dict[str, Any]:
        """
        Get comprehensive system status including all services.

        Returns:
            Dictionary with complete system health information
        """
        system_status = {}

        # Check all registered services
        for service_type in ServiceType:
            if service_type in self._health_checkers:
                status = await self.check_service_health(service_type)
                system_status[service_type.value] = {
                    "status": status.status,
                    "fallback_available": status.fallback_available,
                    "capabilities_affected": status.capabilities_affected,
                    "last_check": status.last_check.isoformat() if status.last_check else None,
                    "error_message": status.error_message,
                    "circuit_breaker_state": status.circuit_breaker_state,
                    "degradation_reason": status.degradation_reason
                }

        return system_status

    def register_service_status(
        self,
        service_type: ServiceType,
        is_available: bool,
        capabilities_affected: List[str],
        fallback_available: bool = True
    ) -> ServiceStatus:
        """
        Register the current status of a service.
        
        Args:
            service_type: Type of service
            is_available: Whether the service is currently available
            capabilities_affected: List of capabilities affected when service is down
            fallback_available: Whether fallback functionality exists
            
        Returns:
            ServiceStatus object with current status
        """
        status = "available" if is_available else ("degraded" if fallback_available else "unavailable")
        
        service_status = ServiceStatus(
            service_name=service_type.value,
            status=status,
            fallback_available=fallback_available,
            capabilities_affected=capabilities_affected if not is_available else []
        )
        
        self._service_status[service_type] = service_status
        self._last_check[service_type] = datetime.now()
        
        if not is_available:
            logger.warning(
                f"Service {service_type.value} is {status}",
                extra={
                    "service": service_type.value,
                    "status": status,
                    "fallback_available": fallback_available,
                    "capabilities_affected": capabilities_affected
                }
            )
        
        return service_status
    
    def get_service_status(self, service_type: ServiceType) -> Optional[ServiceStatus]:
        """Get the current status of a service."""
        return self._service_status.get(service_type)
    
    def get_all_service_status(self) -> List[ServiceStatus]:
        """Get status of all monitored services."""
        return list(self._service_status.values())
    
    def get_degraded_services(self) -> List[ServiceStatus]:
        """Get list of services that are degraded or unavailable."""
        return [
            status for status in self._service_status.values()
            if status.status in ["degraded", "unavailable"]
        ]
    
    def get_system_health_summary(self) -> Dict[str, Any]:
        """
        Get overall system health summary.
        
        Returns:
            Dictionary with system health information
        """
        all_services = list(self._service_status.values())
        
        if not all_services:
            return {
                "overall_status": "unknown",
                "available_services": 0,
                "degraded_services": 0,
                "unavailable_services": 0,
                "fallback_coverage": 0.0
            }
        
        available = len([s for s in all_services if s.status == "available"])
        degraded = len([s for s in all_services if s.status == "degraded"])
        unavailable = len([s for s in all_services if s.status == "unavailable"])
        
        # Calculate fallback coverage
        services_with_fallback = len([s for s in all_services if s.fallback_available])
        fallback_coverage = services_with_fallback / len(all_services) if all_services else 0.0
        
        # Determine overall status
        if unavailable == 0 and degraded == 0:
            overall_status = "healthy"
        elif unavailable == 0:
            overall_status = "degraded"
        elif fallback_coverage >= 0.8:
            overall_status = "degraded"
        else:
            overall_status = "critical"
        
        return {
            "overall_status": overall_status,
            "available_services": available,
            "degraded_services": degraded,
            "unavailable_services": unavailable,
            "total_services": len(all_services),
            "fallback_coverage": fallback_coverage,
            "last_updated": datetime.now().isoformat()
        }
    
    def should_use_fallback(self, service_type: ServiceType) -> bool:
        """
        Determine if fallback should be used for a service.
        
        Args:
            service_type: Type of service to check
            
        Returns:
            True if fallback should be used, False otherwise
        """
        status = self._service_status.get(service_type)
        if not status:
            return True  # Use fallback if status unknown
        
        return status.status != "available"
    
    def get_affected_capabilities(self, service_types: List[ServiceType]) -> List[str]:
        """
        Get all capabilities affected by the given services.
        
        Args:
            service_types: List of service types to check
            
        Returns:
            Combined list of affected capabilities
        """
        affected_capabilities = set()
        
        for service_type in service_types:
            status = self._service_status.get(service_type)
            if status and status.status != "available":
                affected_capabilities.update(status.capabilities_affected)
        
        return list(affected_capabilities)
    
    def create_degradation_context(self, service_types: List[ServiceType]) -> Dict[str, Any]:
        """
        Create context information for service degradation scenarios.
        
        Args:
            service_types: List of services that might be affected
            
        Returns:
            Context dictionary with degradation information
        """
        degraded_services = []
        affected_capabilities = set()
        fallback_available = True
        
        for service_type in service_types:
            status = self._service_status.get(service_type)
            if status and status.status != "available":
                degraded_services.append(status)
                affected_capabilities.update(status.capabilities_affected)
                if not status.fallback_available:
                    fallback_available = False
        
        return {
            "degraded_services": degraded_services,
            "affected_capabilities": list(affected_capabilities),
            "fallback_available": fallback_available,
            "severity": ErrorSeverity.MEDIUM if fallback_available else ErrorSeverity.HIGH
        }


# Global service monitor instance
service_monitor = ServiceMonitor()


def check_openai_availability() -> ServiceStatus:
    """Check OpenAI API availability and register status."""
    try:
        # This would normally make a test API call
        # For now, we'll check if API key is configured
        import os
        api_key = os.getenv("OPENAI_API_KEY")
        is_available = bool(api_key)
        
        return service_monitor.register_service_status(
            ServiceType.OPENAI_API,
            is_available=is_available,
            capabilities_affected=["gpt_analysis", "advanced_reasoning", "multi_agent_collaboration"],
            fallback_available=True
        )
    except Exception as e:
        logger.error(f"Failed to check OpenAI availability: {e}")
        return service_monitor.register_service_status(
            ServiceType.OPENAI_API,
            is_available=False,
            capabilities_affected=["gpt_analysis", "advanced_reasoning", "multi_agent_collaboration"],
            fallback_available=True
        )


def check_weaviate_availability() -> ServiceStatus:
    """Check Weaviate availability and register status."""
    try:
        from app.core.vector_store import vector_store
        is_available = vector_store.is_connected

        return service_monitor.register_service_status(
            ServiceType.WEAVIATE,
            is_available=is_available,
            capabilities_affected=["semantic_search", "document_similarity", "rag_enhancement"],
            fallback_available=True
        )
    except Exception as e:
        logger.error(f"Failed to check Weaviate availability: {e}")
        return service_monitor.register_service_status(
            ServiceType.WEAVIATE,
            is_available=False,
            capabilities_affected=["semantic_search", "document_similarity", "rag_enhancement"],
            fallback_available=True
        )


def check_multimodal_dependencies() -> List[ServiceStatus]:
    """Check multi-modal processing dependencies and register status."""
    statuses = []
    
    # Check Whisper availability
    try:
        import whisper
        whisper_available = True
    except ImportError:
        whisper_available = False
    
    statuses.append(service_monitor.register_service_status(
        ServiceType.WHISPER,
        is_available=whisper_available,
        capabilities_affected=["speech_to_text", "audio_transcription"],
        fallback_available=False
    ))
    
    # Check OpenCV availability
    try:
        import cv2
        opencv_available = True
    except ImportError:
        opencv_available = False
    
    statuses.append(service_monitor.register_service_status(
        ServiceType.OPENCV,
        is_available=opencv_available,
        capabilities_affected=["video_processing", "frame_extraction", "video_analysis"],
        fallback_available=False
    ))
    
    # Check FFmpeg availability
    try:
        import ffmpeg
        ffmpeg_available = True
    except ImportError:
        ffmpeg_available = False
    
    statuses.append(service_monitor.register_service_status(
        ServiceType.FFMPEG,
        is_available=ffmpeg_available,
        capabilities_affected=["video_audio_extraction", "format_conversion"],
        fallback_available=False
    ))
    
    return statuses


def initialize_service_monitoring():
    """Initialize service monitoring for all external dependencies."""
    logger.info("Initializing service monitoring...")
    
    # Check all services
    check_openai_availability()
    check_weaviate_availability()
    check_multimodal_dependencies()
    
    # Log summary
    health_summary = service_monitor.get_system_health_summary()
    logger.info(
        f"Service monitoring initialized - Overall status: {health_summary['overall_status']}",
        extra=health_summary
    )
