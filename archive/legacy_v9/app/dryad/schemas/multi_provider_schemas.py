"""
Multi-Provider Oracle Schemas

Schemas for multi-provider oracle operations including consensus mode,
provider selection, health monitoring, and usage tracking.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field
from enum import Enum


class ProviderType(str, Enum):
    """Types of LLM providers."""
    LLAMACPP = "llamacpp"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    OLLAMA = "ollama"
    GOOGLE = "google"
    COHERE = "cohere"


class ProviderStatus(str, Enum):
    """Provider health status."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


class ConsensusStrategy(str, Enum):
    """Strategies for multi-provider consensus."""
    MAJORITY_VOTE = "majority_vote"
    WEIGHTED_AVERAGE = "weighted_average"
    FIRST_SUCCESS = "first_success"
    ALL_AGREE = "all_agree"
    BEST_QUALITY = "best_quality"


class ProviderHealthCheck(BaseModel):
    """Provider health check result."""
    provider_id: str
    status: ProviderStatus
    response_time_ms: float
    last_check: datetime
    error_rate: float = Field(default=0.0, ge=0.0, le=1.0)
    success_count: int = Field(default=0, ge=0)
    failure_count: int = Field(default=0, ge=0)
    message: Optional[str] = None


class ProviderUsageStats(BaseModel):
    """Provider usage statistics."""
    provider_id: str
    total_requests: int = Field(default=0, ge=0)
    successful_requests: int = Field(default=0, ge=0)
    failed_requests: int = Field(default=0, ge=0)
    total_tokens: int = Field(default=0, ge=0)
    average_response_time_ms: float = Field(default=0.0, ge=0.0)
    last_used: Optional[datetime] = None
    cost_usd: float = Field(default=0.0, ge=0.0)


class ProviderConfig(BaseModel):
    """Provider configuration."""
    provider_id: str
    provider_type: ProviderType
    enabled: bool = True
    priority: int = Field(default=0, description="Higher priority providers are tried first")
    weight: float = Field(default=1.0, ge=0.0, le=1.0, description="Weight for consensus voting")
    max_retries: int = Field(default=3, ge=0)
    timeout_seconds: int = Field(default=30, ge=1)
    rate_limit_per_minute: Optional[int] = Field(default=None, ge=1)
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    model: Optional[str] = None
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: int = Field(default=2048, ge=1)


class MultiConsultRequest(BaseModel):
    """Request for multi-provider consultation."""
    branch_id: str
    query: str
    provider_ids: Optional[List[str]] = Field(
        default=None,
        description="Specific providers to use. If None, uses all enabled providers"
    )
    consensus_strategy: ConsensusStrategy = ConsensusStrategy.MAJORITY_VOTE
    min_providers: int = Field(
        default=2,
        ge=1,
        description="Minimum number of providers that must respond"
    )
    max_providers: int = Field(
        default=5,
        ge=1,
        description="Maximum number of providers to query"
    )
    timeout_seconds: int = Field(default=60, ge=1)
    include_reasoning: bool = Field(
        default=True,
        description="Include individual provider responses in result"
    )


class ProviderResponse(BaseModel):
    """Individual provider response."""
    provider_id: str
    response: str
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    response_time_ms: float
    tokens_used: int = Field(default=0, ge=0)
    cost_usd: float = Field(default=0.0, ge=0.0)
    error: Optional[str] = None
    success: bool = True


class ConsensusResult(BaseModel):
    """Result of consensus analysis."""
    final_response: str
    confidence: float = Field(ge=0.0, le=1.0)
    strategy_used: ConsensusStrategy
    providers_used: List[str]
    providers_succeeded: int
    providers_failed: int
    total_response_time_ms: float
    individual_responses: Optional[List[ProviderResponse]] = None
    reasoning: Optional[str] = None


class MultiConsultResponse(BaseModel):
    """Response from multi-provider consultation."""
    dialogue_id: str
    consensus: ConsensusResult
    created_at: datetime


class ProviderSelectionRequest(BaseModel):
    """Request for intelligent provider selection."""
    query: str
    branch_id: Optional[str] = None
    preferred_providers: Optional[List[str]] = None
    exclude_providers: Optional[List[str]] = None
    require_fast_response: bool = False
    require_high_quality: bool = False
    max_cost_usd: Optional[float] = Field(default=None, ge=0.0)


class ProviderSelectionResponse(BaseModel):
    """Response with selected provider."""
    provider_id: str
    provider_type: ProviderType
    reason: str
    estimated_response_time_ms: float
    estimated_cost_usd: float
    confidence: float = Field(ge=0.0, le=1.0)


class ProviderHealthResponse(BaseModel):
    """Response with all provider health statuses."""
    providers: List[ProviderHealthCheck]
    healthy_count: int
    degraded_count: int
    unhealthy_count: int
    last_updated: datetime


class ProviderUsageResponse(BaseModel):
    """Response with provider usage statistics."""
    providers: List[ProviderUsageStats]
    total_requests: int
    total_tokens: int
    total_cost_usd: float
    period_start: datetime
    period_end: datetime


class FallbackChainConfig(BaseModel):
    """Configuration for provider fallback chain."""
    chain_id: str
    name: str
    description: Optional[str] = None
    provider_ids: List[str] = Field(
        min_items=1,
        description="Providers in order of preference"
    )
    enabled: bool = True
    max_attempts: int = Field(default=3, ge=1)
    retry_delay_seconds: float = Field(default=1.0, ge=0.0)


class FallbackChainResponse(BaseModel):
    """Response from fallback chain execution."""
    chain_id: str
    successful_provider_id: str
    attempts: int
    total_time_ms: float
    response: str
    errors: List[str] = Field(default_factory=list)


class LoadBalancingStrategy(str, Enum):
    """Load balancing strategies."""
    ROUND_ROBIN = "round_robin"
    LEAST_LOADED = "least_loaded"
    FASTEST_RESPONSE = "fastest_response"
    LOWEST_COST = "lowest_cost"
    WEIGHTED_RANDOM = "weighted_random"


class LoadBalancingConfig(BaseModel):
    """Configuration for load balancing."""
    strategy: LoadBalancingStrategy = LoadBalancingStrategy.ROUND_ROBIN
    enabled: bool = True
    health_check_interval_seconds: int = Field(default=60, ge=10)
    remove_unhealthy: bool = Field(
        default=True,
        description="Remove unhealthy providers from rotation"
    )


class ProviderMetrics(BaseModel):
    """Detailed provider metrics."""
    provider_id: str
    uptime_percentage: float = Field(ge=0.0, le=100.0)
    average_latency_ms: float
    p95_latency_ms: float
    p99_latency_ms: float
    error_rate: float = Field(ge=0.0, le=1.0)
    requests_per_minute: float
    tokens_per_minute: float
    cost_per_request_usd: float
    last_24h_requests: int
    last_24h_errors: int

