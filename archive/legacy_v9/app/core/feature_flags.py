"""
Feature Flag System for DRYAD.AI Backend

Provides dynamic feature toggling based on service availability,
configuration, and runtime conditions.
"""

import os
import logging
from enum import Enum
from typing import Dict, Any, Optional, Set, Callable
from dataclasses import dataclass
from datetime import datetime
import threading

logger = logging.getLogger(__name__)


class FeatureStatus(Enum):
    """Feature availability status."""
    ENABLED = "enabled"
    DISABLED = "disabled"
    DEGRADED = "degraded"
    UNAVAILABLE = "unavailable"


@dataclass
class FeatureInfo:
    """Information about a feature."""
    name: str
    description: str
    dependencies: Set[str]
    fallback_available: bool = False
    required_env_vars: Set[str] = None
    status: FeatureStatus = FeatureStatus.ENABLED
    status_reason: str = ""
    last_check: Optional[datetime] = None


class FeatureFlag:
    """
    Individual feature flag with dependency checking and status management.
    """
    
    def __init__(self, info: FeatureInfo):
        self.info = info
        self._status_checkers: Dict[str, Callable[[], bool]] = {}
        self._lock = threading.RLock()
    
    def add_status_checker(self, name: str, checker: Callable[[], bool]):
        """Add a status checker function."""
        with self._lock:
            self._status_checkers[name] = checker
    
    def check_status(self) -> FeatureStatus:
        """Check current feature status based on dependencies and conditions."""
        with self._lock:
            try:
                # Check environment variables
                if self.info.required_env_vars:
                    missing_vars = [var for var in self.info.required_env_vars 
                                  if not os.getenv(var)]
                    if missing_vars:
                        self.info.status = FeatureStatus.DISABLED
                        self.info.status_reason = f"Missing environment variables: {missing_vars}"
                        self.info.last_check = datetime.now()
                        return self.info.status
                
                # Check explicit disable
                env_disable = os.getenv(f"DISABLE_{self.info.name.upper()}", "false").lower()
                if env_disable in ("true", "1", "yes"):
                    self.info.status = FeatureStatus.DISABLED
                    self.info.status_reason = "Explicitly disabled via environment variable"
                    self.info.last_check = datetime.now()
                    return self.info.status
                
                # Run custom status checkers
                failed_checks = []
                for checker_name, checker in self._status_checkers.items():
                    try:
                        if not checker():
                            failed_checks.append(checker_name)
                    except Exception as e:
                        logger.warning(f"Status checker '{checker_name}' failed: {e}")
                        failed_checks.append(f"{checker_name} (error)")
                
                # Determine status based on failed checks
                if failed_checks:
                    if self.info.fallback_available:
                        self.info.status = FeatureStatus.DEGRADED
                        self.info.status_reason = f"Degraded due to: {', '.join(failed_checks)}"
                    else:
                        self.info.status = FeatureStatus.UNAVAILABLE
                        self.info.status_reason = f"Unavailable due to: {', '.join(failed_checks)}"
                else:
                    self.info.status = FeatureStatus.ENABLED
                    self.info.status_reason = "All dependencies satisfied"
                
                self.info.last_check = datetime.now()
                return self.info.status
                
            except Exception as e:
                logger.error(f"Error checking feature status for '{self.info.name}': {e}")
                self.info.status = FeatureStatus.UNAVAILABLE
                self.info.status_reason = f"Status check error: {str(e)}"
                self.info.last_check = datetime.now()
                return self.info.status
    
    @property
    def is_enabled(self) -> bool:
        """Check if feature is fully enabled."""
        return self.check_status() == FeatureStatus.ENABLED
    
    @property
    def is_available(self) -> bool:
        """Check if feature is available (enabled or degraded)."""
        status = self.check_status()
        return status in (FeatureStatus.ENABLED, FeatureStatus.DEGRADED)
    
    @property
    def is_degraded(self) -> bool:
        """Check if feature is in degraded mode."""
        return self.check_status() == FeatureStatus.DEGRADED
    
    def get_status_info(self) -> Dict[str, Any]:
        """Get detailed status information."""
        status = self.check_status()
        return {
            "name": self.info.name,
            "description": self.info.description,
            "status": status.value,
            "status_reason": self.info.status_reason,
            "fallback_available": self.info.fallback_available,
            "dependencies": list(self.info.dependencies),
            "required_env_vars": list(self.info.required_env_vars or []),
            "last_check": self.info.last_check.isoformat() if self.info.last_check else None
        }


class FeatureFlagManager:
    """
    Central manager for all feature flags.
    
    Provides registration, status checking, and monitoring of features
    based on service availability and configuration.
    """
    
    def __init__(self):
        self._features: Dict[str, FeatureFlag] = {}
        self._lock = threading.RLock()
        self._initialize_default_features()
    
    def _initialize_default_features(self):
        """Initialize default feature flags for self-contained AI system."""
        # Local AI Feature - Core self-contained AI capabilities
        local_ai = FeatureInfo(
            name="local_ai",
            description="Self-contained AI reasoning and multi-agent orchestration using local LLM",
            dependencies={"llamacpp"},
            fallback_available=False,  # No fallback - AI should work or fail explicitly
            required_env_vars=set()  # No external services required
        )
        self.register_feature(local_ai)

        # Vector Search Feature
        vector_search = FeatureInfo(
            name="vector_search",
            description="Semantic search and RAG capabilities using vector database",
            dependencies={"weaviate", "embeddings"},
            fallback_available=True,
            required_env_vars={"WEAVIATE_URL"}
        )
        self.register_feature(vector_search)

        # Multi-Agent Feature - Now self-contained with local LLM
        multi_agent = FeatureInfo(
            name="multi_agent",
            description="Multi-agent orchestration and complex task execution with local AI",
            dependencies={"local_ai"},  # Depends on local AI, not external services
            fallback_available=False,  # No fallback - should use genuine AI
            required_env_vars=set()  # No external services required
        )
        self.register_feature(multi_agent)

        # Multimodal Feature
        multimodal = FeatureInfo(
            name="multimodal",
            description="Audio, video, and image processing capabilities",
            dependencies={"ml_models", "storage"},
            fallback_available=False,
            required_env_vars=set()
        )
        self.register_feature(multimodal)
        
        # Task Queue Feature
        task_queue = FeatureInfo(
            name="task_queue",
            description="Background task processing with Celery",
            dependencies={"redis"},
            fallback_available=True,
            required_env_vars={"CELERY_BROKER_URL"}
        )
        self.register_feature(task_queue)
        
        # GraphQL Feature
        graphql = FeatureInfo(
            name="graphql",
            description="GraphQL API interface",
            dependencies={"database"},
            fallback_available=False,
            required_env_vars=set()
        )
        self.register_feature(graphql)
        
        # Real-time Features
        realtime = FeatureInfo(
            name="realtime",
            description="WebSocket connections and real-time updates",
            dependencies={"websockets"},
            fallback_available=False,
            required_env_vars=set()
        )
        self.register_feature(realtime)
        
        # Add status checkers
        self._add_default_status_checkers()
    
    def _add_default_status_checkers(self):
        """Add default status checkers for features."""
        # Vector search checker
        def check_weaviate():
            try:
                from app.core.vector_store import get_vector_store
                vector_store = get_vector_store()
                return vector_store and vector_store.is_connected
            except Exception:
                return False
        
        self.get_feature("vector_search").add_status_checker("weaviate", check_weaviate)
        
        # Task queue checker
        def check_redis():
            try:
                import redis
                redis_url = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
                r = redis.from_url(redis_url)
                r.ping()
                return True
            except Exception:
                return False
        
        self.get_feature("task_queue").add_status_checker("redis", check_redis)
        self.get_feature("multi_agent").add_status_checker("redis", check_redis)
        
        # LLM provider checker
        def check_llm():
            try:
                from app.core.llm_config import get_llm_health_status
                health = get_llm_health_status()
                return health.get("llm_available", False)
            except Exception:
                return False
        
        self.get_feature("multi_agent").add_status_checker("llm", check_llm)
        
        # Database checker
        def check_database():
            try:
                from app.database.database import get_db
                # This is a simplified check - in practice you'd test the connection
                return True
            except Exception:
                return False
        
        self.get_feature("graphql").add_status_checker("database", check_database)
    
    def register_feature(self, feature_info: FeatureInfo):
        """Register a new feature flag."""
        with self._lock:
            feature_flag = FeatureFlag(feature_info)
            self._features[feature_info.name] = feature_flag
            logger.info(f"Registered feature flag: {feature_info.name}")
    
    def get_feature(self, name: str) -> Optional[FeatureFlag]:
        """Get a feature flag by name."""
        with self._lock:
            return self._features.get(name)
    
    def is_enabled(self, name: str) -> bool:
        """Check if a feature is fully enabled."""
        feature = self.get_feature(name)
        return feature.is_enabled if feature else False
    
    def is_available(self, name: str) -> bool:
        """Check if a feature is available (enabled or degraded)."""
        feature = self.get_feature(name)
        return feature.is_available if feature else False
    
    def is_degraded(self, name: str) -> bool:
        """Check if a feature is in degraded mode."""
        feature = self.get_feature(name)
        return feature.is_degraded if feature else False
    
    def get_all_features(self) -> Dict[str, Dict[str, Any]]:
        """Get status information for all features."""
        with self._lock:
            return {name: feature.get_status_info() 
                   for name, feature in self._features.items()}
    
    def get_enabled_features(self) -> Set[str]:
        """Get set of fully enabled feature names."""
        with self._lock:
            return {name for name, feature in self._features.items() 
                   if feature.is_enabled}
    
    def get_available_features(self) -> Set[str]:
        """Get set of available feature names (enabled or degraded)."""
        with self._lock:
            return {name for name, feature in self._features.items() 
                   if feature.is_available}
    
    def get_degraded_features(self) -> Set[str]:
        """Get set of degraded feature names."""
        with self._lock:
            return {name for name, feature in self._features.items() 
                   if feature.is_degraded}
    
    def get_unavailable_features(self) -> Set[str]:
        """Get set of unavailable feature names."""
        with self._lock:
            return {name for name, feature in self._features.items() 
                   if not feature.is_available}
    
    def refresh_all_statuses(self):
        """Refresh status for all features."""
        with self._lock:
            for feature in self._features.values():
                feature.check_status()
    
    def get_system_capabilities(self) -> Dict[str, Any]:
        """Get overall system capabilities summary."""
        with self._lock:
            self.refresh_all_statuses()
            
            enabled = self.get_enabled_features()
            degraded = self.get_degraded_features()
            unavailable = self.get_unavailable_features()
            
            total_features = len(self._features)
            capability_score = 0
            if total_features > 0:
                capability_score = (len(enabled) + 0.5 * len(degraded)) / total_features * 100
            
            return {
                "capability_score": round(capability_score, 1),
                "total_features": total_features,
                "enabled_features": len(enabled),
                "degraded_features": len(degraded),
                "unavailable_features": len(unavailable),
                "enabled": list(enabled),
                "degraded": list(degraded),
                "unavailable": list(unavailable),
                "basic_mode": len(enabled) == 0 and len(degraded) == 0
            }


# Global feature flag manager
feature_flags = FeatureFlagManager()


def is_feature_enabled(name: str) -> bool:
    """Check if a feature is fully enabled."""
    return feature_flags.is_enabled(name)


def is_feature_available(name: str) -> bool:
    """Check if a feature is available (enabled or degraded)."""
    return feature_flags.is_available(name)


def is_feature_degraded(name: str) -> bool:
    """Check if a feature is in degraded mode."""
    return feature_flags.is_degraded(name)


def require_feature(name: str, allow_degraded: bool = False):
    """
    Decorator to require a feature for an endpoint.
    
    Args:
        name: Feature name
        allow_degraded: Whether to allow degraded mode
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            if allow_degraded:
                if not is_feature_available(name):
                    from fastapi import HTTPException
                    raise HTTPException(
                        status_code=503,
                        detail=f"Feature '{name}' is currently unavailable"
                    )
            else:
                if not is_feature_enabled(name):
                    from fastapi import HTTPException
                    feature = feature_flags.get_feature(name)
                    reason = feature.info.status_reason if feature else "Feature not found"
                    raise HTTPException(
                        status_code=503,
                        detail=f"Feature '{name}' is currently disabled: {reason}"
                    )
            return func(*args, **kwargs)
        return wrapper
    return decorator
