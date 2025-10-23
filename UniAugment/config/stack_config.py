"""
Stack Configuration Module
Handles runtime detection and configuration of different deployment stacks
"""

import os
from enum import Enum
from typing import Optional
from pydantic_settings import BaseSettings


class StackType(Enum):
    """Supported stack types"""
    LITE = "lite"
    HYBRID = "hybrid"
    FULL = "full"


class CacheConfig:
    """Cache configuration based on stack type"""
    
    def __init__(self, stack_type: StackType):
        self.stack_type = stack_type
    
    @property
    def enabled(self) -> bool:
        return True
    
    @property
    def backend(self) -> str:
        """Get cache backend"""
        if self.stack_type == StackType.LITE:
            return "memory"
        elif self.stack_type == StackType.HYBRID:
            return "memory"
        else:  # FULL
            return "redis"
    
    @property
    def ttl(self) -> int:
        """Get cache TTL in seconds"""
        return int(os.getenv("CACHE_TTL", "300"))
    
    @property
    def max_size(self) -> int:
        """Get max cache size"""
        return int(os.getenv("CACHE_MAX_SIZE", "1000"))


class TaskQueueConfig:
    """Task queue configuration based on stack type"""
    
    def __init__(self, stack_type: StackType):
        self.stack_type = stack_type
    
    @property
    def enabled(self) -> bool:
        return True
    
    @property
    def backend(self) -> str:
        """Get task queue backend"""
        if self.stack_type == StackType.LITE:
            return "apscheduler"
        elif self.stack_type == StackType.HYBRID:
            return "apscheduler"
        else:  # FULL
            return "celery"
    
    @property
    def broker_url(self) -> Optional[str]:
        """Get broker URL (only for Celery)"""
        if self.backend == "celery":
            return os.getenv("CELERY_BROKER_URL")
        return None
    
    @property
    def result_backend(self) -> Optional[str]:
        """Get result backend (only for Celery)"""
        if self.backend == "celery":
            return os.getenv("CELERY_RESULT_BACKEND")
        return None


class DatabaseConfig:
    """Database configuration based on stack type"""
    
    def __init__(self, stack_type: StackType):
        self.stack_type = stack_type
    
    @property
    def url(self) -> str:
        """Get database URL"""
        return os.getenv("DATABASE_URL", "sqlite:///./data/uniaugment.db")
    
    @property
    def is_sqlite(self) -> bool:
        """Check if using SQLite"""
        return self.url.startswith("sqlite")
    
    @property
    def is_postgresql(self) -> bool:
        """Check if using PostgreSQL"""
        return self.url.startswith("postgresql")
    
    @property
    def async_url(self) -> str:
        """Get async database URL"""
        if self.is_sqlite:
            return self.url.replace("sqlite:///", "sqlite+aiosqlite:///")
        elif self.is_postgresql:
            return self.url.replace("postgresql://", "postgresql+asyncpg://")
        return self.url


class VectorDBConfig:
    """Vector database configuration based on stack type"""

    def __init__(self, stack_type: StackType):
        self.stack_type = stack_type

    @property
    def enabled(self) -> bool:
        """Check if vector DB is enabled"""
        return self.stack_type in [StackType.HYBRID, StackType.FULL]

    @property
    def backend(self) -> str:
        """Get vector DB backend"""
        if self.stack_type == StackType.LITE:
            return "chroma"
        else:  # HYBRID, FULL
            return "weaviate"

    @property
    def url(self) -> Optional[str]:
        """Get vector DB URL"""
        if self.backend == "weaviate":
            return os.getenv("WEAVIATE_URL", "http://localhost:8080")
        return None


class AgentCreationStudioConfig:
    """Agent Creation Studio configuration for Phase 1 enhancements"""

    def __init__(self):
        pass

    @property
    def enabled(self) -> bool:
        """Check if Agent Creation Studio is enabled"""
        return os.getenv("AGENT_CREATION_STUDIO_ENABLED", "false").lower() == "true"

    @property
    def visual_customization(self) -> bool:
        """Check if visual customization is enabled"""
        return os.getenv("AGENT_VISUAL_CUSTOMIZATION", "true").lower() == "true"

    @property
    def behavioral_customization(self) -> bool:
        """Check if behavioral customization is enabled"""
        return os.getenv("AGENT_BEHAVIORAL_CUSTOMIZATION", "true").lower() == "true"

    @property
    def default_visual_settings(self) -> dict:
        """Get default visual settings"""
        return {
            "avatar_style": os.getenv("DEFAULT_AVATAR_STYLE", "abstract"),
            "primary_color": os.getenv("DEFAULT_PRIMARY_COLOR", "#0066CC"),
            "secondary_color": os.getenv("DEFAULT_SECONDARY_COLOR", "#00CC66"),
            "accent_color": os.getenv("DEFAULT_ACCENT_COLOR", "#CC6600"),
            "visual_theme": os.getenv("DEFAULT_VISUAL_THEME", "professional"),
            "glow_intensity": float(os.getenv("DEFAULT_GLOW_INTENSITY", "0.5")),
        }

    @property
    def default_behavioral_settings(self) -> dict:
        """Get default behavioral settings"""
        return {
            "learning_style": os.getenv("DEFAULT_LEARNING_STYLE", "visual"),
            "learning_pace": float(os.getenv("DEFAULT_LEARNING_PACE", "1.0")),
            "risk_tolerance": float(os.getenv("DEFAULT_RISK_TOLERANCE", "0.5")),
            "collaboration_style": os.getenv("DEFAULT_COLLABORATION_STYLE", "equal"),
            "communication_tone": os.getenv("DEFAULT_COMMUNICATION_TONE", "professional"),
            "decision_speed": float(os.getenv("DEFAULT_DECISION_SPEED", "0.5")),
            "decision_confidence": float(os.getenv("DEFAULT_DECISION_CONFIDENCE", "0.7")),
        }

    def get_config_summary(self) -> dict:
        """Get configuration summary"""
        return {
            "enabled": self.enabled,
            "visual_customization": self.visual_customization,
            "behavioral_customization": self.behavioral_customization,
            "default_visual": self.default_visual_settings if self.visual_customization else None,
            "default_behavioral": self.default_behavioral_settings if self.behavioral_customization else None,
        }


class SpecializationSkillTreeConfig:
    """Specialization & Skill Tree configuration for Phase 2 enhancements"""

    def __init__(self):
        pass

    @property
    def enabled(self) -> bool:
        """Check if Specialization & Skill Trees are enabled"""
        return os.getenv("SPECIALIZATION_SKILL_TREES_ENABLED", "false").lower() == "true"

    @property
    def default_primary_specialization(self) -> str:
        """Get default primary specialization"""
        return os.getenv("DEFAULT_PRIMARY_SPECIALIZATION", "data_science")

    @property
    def max_secondary_specializations(self) -> int:
        """Get max number of secondary specializations"""
        return int(os.getenv("MAX_SECONDARY_SPECIALIZATIONS", "3"))

    @property
    def cross_specialization_penalty(self) -> float:
        """Get cross-specialization learning penalty"""
        return float(os.getenv("CROSS_SPECIALIZATION_PENALTY", "0.2"))

    @property
    def skill_tree_enabled(self) -> bool:
        """Check if skill trees are enabled"""
        return os.getenv("SKILL_TREE_ENABLED", "true").lower() == "true"

    @property
    def progression_paths_enabled(self) -> bool:
        """Check if progression paths are enabled"""
        return os.getenv("PROGRESSION_PATHS_ENABLED", "true").lower() == "true"

    def get_config_summary(self) -> dict:
        """Get configuration summary"""
        return {
            "enabled": self.enabled,
            "default_primary_specialization": self.default_primary_specialization,
            "max_secondary_specializations": self.max_secondary_specializations,
            "cross_specialization_penalty": self.cross_specialization_penalty,
            "skill_tree_enabled": self.skill_tree_enabled,
            "progression_paths_enabled": self.progression_paths_enabled,
        }


class AgenticUniversityConfig:
    """Agentic Research University System configuration (Level 6)"""

    def __init__(self):
        pass

    @property
    def enabled(self) -> bool:
        """Check if Agentic University System is enabled"""
        return os.getenv("AGENTIC_UNIVERSITY_ENABLED", "false").lower() == "true"

    @property
    def universities_enabled(self) -> bool:
        """Check if university management is enabled"""
        return os.getenv("UNIVERSITY_MANAGEMENT_ENABLED", "true").lower() == "true"

    @property
    def curriculum_enabled(self) -> bool:
        """Check if curriculum system is enabled"""
        return os.getenv("CURRICULUM_SYSTEM_ENABLED", "true").lower() == "true"

    @property
    def competitions_enabled(self) -> bool:
        """Check if competition system is enabled"""
        return os.getenv("COMPETITION_SYSTEM_ENABLED", "true").lower() == "true"

    @property
    def default_isolation_level(self) -> str:
        """Get default university isolation level"""
        return os.getenv("DEFAULT_ISOLATION_LEVEL", "strict")

    @property
    def max_agents_per_university(self) -> int:
        """Get max agents per university"""
        return int(os.getenv("MAX_AGENTS_PER_UNIVERSITY", "1000"))

    @property
    def max_competitions_per_university(self) -> int:
        """Get max competitions per university"""
        return int(os.getenv("MAX_COMPETITIONS_PER_UNIVERSITY", "100"))

    @property
    def default_storage_limit_gb(self) -> int:
        """Get default storage limit in GB"""
        return int(os.getenv("DEFAULT_STORAGE_LIMIT_GB", "100"))

    @property
    def enable_leaderboards(self) -> bool:
        """Check if leaderboards are enabled"""
        return os.getenv("ENABLE_LEADERBOARDS", "true").lower() == "true"

    @property
    def enable_elo_ratings(self) -> bool:
        """Check if Elo rating system is enabled"""
        return os.getenv("ENABLE_ELO_RATINGS", "true").lower() == "true"

    @property
    def default_elo_k_factor(self) -> int:
        """Get default Elo K-factor"""
        return int(os.getenv("DEFAULT_ELO_K_FACTOR", "32"))

    @property
    def training_data_collection(self) -> bool:
        """Check if training data collection is enabled"""
        return os.getenv("TRAINING_DATA_COLLECTION", "true").lower() == "true"

    @property
    def arena_mode_enabled(self) -> bool:
        """Check if Arena/Dojo competition mode is enabled"""
        return os.getenv("ARENA_MODE_ENABLED", "true").lower() == "true"

    def get_config_summary(self) -> dict:
        """Get configuration summary"""
        return {
            "enabled": self.enabled,
            "universities_enabled": self.universities_enabled,
            "curriculum_enabled": self.curriculum_enabled,
            "competitions_enabled": self.competitions_enabled,
            "default_isolation_level": self.default_isolation_level,
            "max_agents_per_university": self.max_agents_per_university,
            "max_competitions_per_university": self.max_competitions_per_university,
            "default_storage_limit_gb": self.default_storage_limit_gb,
            "enable_leaderboards": self.enable_leaderboards,
            "enable_elo_ratings": self.enable_elo_ratings,
            "default_elo_k_factor": self.default_elo_k_factor,
            "training_data_collection": self.training_data_collection,
            "arena_mode_enabled": self.arena_mode_enabled,
        }


class StackConfig(BaseSettings):
    """Main stack configuration"""
    
    # Stack type
    stack_type: str = os.getenv("STACK_TYPE", "lite")
    
    # Environment
    environment: str = os.getenv("ENVIRONMENT", "development")
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    
    # API
    api_title: str = os.getenv("API_TITLE", "UniAugment API")
    api_version: str = os.getenv("API_VERSION", "1.0.0")
    api_description: str = os.getenv("API_DESCRIPTION", "Agentic University System API")
    
    # Security
    jwt_secret_key: str = os.getenv("JWT_SECRET_KEY", "dev-secret-key")
    jwt_algorithm: str = os.getenv("JWT_ALGORITHM", "HS256")
    jwt_expiration_hours: int = int(os.getenv("JWT_EXPIRATION_HOURS", "24"))
    
    # Application
    deployment_domain: str = os.getenv("DEPLOYMENT_DOMAIN", "localhost")
    enable_ssl: bool = os.getenv("ENABLE_SSL", "false").lower() == "true"
    
    # CORS
    cors_origins: list = ["http://localhost:3000", "http://localhost:8000"]
    cors_allow_credentials: bool = True
    cors_allow_methods: list = ["*"]
    cors_allow_headers: list = ["*"]
    
    # Rate limiting
    rate_limit_enabled: bool = os.getenv("RATE_LIMIT_ENABLED", "true").lower() == "true"
    rate_limit_requests: int = int(os.getenv("RATE_LIMIT_REQUESTS", "100"))
    rate_limit_period: int = int(os.getenv("RATE_LIMIT_PERIOD", "60"))
    
    class Config:
        env_file = ".env"
        case_sensitive = False
    
    def __init__(self, **data):
        super().__init__(**data)
        self._stack_type = StackType(self.stack_type)
        self.cache = CacheConfig(self._stack_type)
        self.task_queue = TaskQueueConfig(self._stack_type)
        self.database = DatabaseConfig(self._stack_type)
        self.vector_db = VectorDBConfig(self._stack_type)
        self.agent_studio = AgentCreationStudioConfig()
        self.specialization_skill_tree = SpecializationSkillTreeConfig()
        self.agentic_university = AgenticUniversityConfig()
    
    @property
    def is_lite(self) -> bool:
        """Check if running LITE stack"""
        return self._stack_type == StackType.LITE
    
    @property
    def is_hybrid(self) -> bool:
        """Check if running HYBRID stack"""
        return self._stack_type == StackType.HYBRID
    
    @property
    def is_full(self) -> bool:
        """Check if running FULL stack"""
        return self._stack_type == StackType.FULL
    
    @property
    def is_production(self) -> bool:
        """Check if running in production"""
        return self.environment == "production"
    
    @property
    def is_development(self) -> bool:
        """Check if running in development"""
        return self.environment == "development"
    
    def get_stack_info(self) -> dict:
        """Get stack information"""
        return {
            "stack_type": self.stack_type,
            "environment": self.environment,
            "database": {
                "type": "sqlite" if self.database.is_sqlite else "postgresql",
                "url": self.database.url,
            },
            "cache": {
                "backend": self.cache.backend,
                "ttl": self.cache.ttl,
            },
            "task_queue": {
                "backend": self.task_queue.backend,
            },
            "vector_db": {
                "enabled": self.vector_db.enabled,
                "backend": self.vector_db.backend,
            },
            "agent_studio": self.agent_studio.get_config_summary(),
            "specialization_skill_tree": self.specialization_skill_tree.get_config_summary(),
            "agentic_university": self.agentic_university.get_config_summary(),
        }


# Global configuration instance
_config: Optional[StackConfig] = None


def get_config() -> StackConfig:
    """Get global configuration instance"""
    global _config
    if _config is None:
        _config = StackConfig()
    return _config


def reload_config() -> StackConfig:
    """Reload configuration"""
    global _config
    _config = StackConfig()
    return _config

