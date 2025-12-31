"""
Multi-Provider Oracle Service

Intelligent provider selection, multi-provider consensus, fallback chains,
and load balancing for oracle consultations.
"""

import asyncio
import time
from typing import List, Optional, Dict
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession

from app.dryad.schemas.multi_provider_schemas import (
    ProviderType, ProviderStatus, ConsensusStrategy,
    ProviderHealthCheck, ProviderUsageStats, ProviderConfig,
    MultiConsultRequest, ProviderResponse, ConsensusResult, MultiConsultResponse,
    ProviderSelectionRequest, ProviderSelectionResponse,
    ProviderHealthResponse, ProviderUsageResponse,
    FallbackChainConfig, FallbackChainResponse,
    LoadBalancingStrategy, LoadBalancingConfig, ProviderMetrics
)
from app.dryad.services.oracle_service import OracleService
from app.dryad.schemas.dialogue_schemas import ConsultationRequest
from app.core.config import Config
from app.core.llm_error_handler import llm_error_handler
from app.core.logging_config import get_logger

logger = get_logger(__name__)


class MultiProviderService:
    """Service for multi-provider oracle operations."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.oracle_service = OracleService(db)
        self.config = Config()

        # Provider registry
        self.providers: Dict[str, ProviderConfig] = {}
        self.provider_health: Dict[str, ProviderHealthCheck] = {}
        self.provider_usage: Dict[str, ProviderUsageStats] = {}

        # Load balancing state
        self.round_robin_index = 0
        self.load_balancing_config = LoadBalancingConfig()

        # Initialize providers
        self._initialize_providers()

        logger.info("MultiProviderService initialized")
    
    def _initialize_providers(self):
        """Initialize provider registry from configuration."""
        # LlamaCpp (local)
        self.providers["llamacpp"] = ProviderConfig(
            provider_id="llamacpp",
            provider_type=ProviderType.LLAMACPP,
            enabled=True,
            priority=10,
            weight=1.0,
            timeout_seconds=30,
            model=self.config.LLAMACPP_MODEL
        )
        
        # OpenAI
        if self.config.OPENAI_API_KEY:
            self.providers["openai"] = ProviderConfig(
                provider_id="openai",
                provider_type=ProviderType.OPENAI,
                enabled=True,
                priority=20,
                weight=1.2,
                timeout_seconds=30,
                api_key=self.config.OPENAI_API_KEY,
                model=self.config.OPENAI_MODEL
            )
        
        # Ollama (local)
        self.providers["ollama"] = ProviderConfig(
            provider_id="ollama",
            provider_type=ProviderType.OLLAMA,
            enabled=True,
            priority=15,
            weight=1.0,
            timeout_seconds=30,
            base_url=self.config.OLLAMA_BASE_URL,
            model=self.config.OLLAMA_MODEL
        )
        
        # Initialize health and usage tracking
        for provider_id in self.providers:
            self.provider_health[provider_id] = ProviderHealthCheck(
                provider_id=provider_id,
                status=ProviderStatus.UNKNOWN,
                response_time_ms=0.0,
                last_check=datetime.now()
            )
            self.provider_usage[provider_id] = ProviderUsageStats(
                provider_id=provider_id
            )
        
        logger.info(f"Initialized {len(self.providers)} providers")
    
    async def multi_consult(
        self,
        request: MultiConsultRequest
    ) -> MultiConsultResponse:
        """
        Consult multiple providers and return consensus result.
        
        Args:
            request: Multi-consultation request
            
        Returns:
            Consensus result from multiple providers
        """
        start_time = time.time()
        
        # Select providers to use
        provider_ids = request.provider_ids or [
            p_id for p_id, p in self.providers.items()
            if p.enabled
        ]
        
        # Limit to max_providers
        provider_ids = provider_ids[:request.max_providers]
        
        if len(provider_ids) < request.min_providers:
            raise ValueError(
                f"Not enough providers available. "
                f"Required: {request.min_providers}, Available: {len(provider_ids)}"
            )
        
        logger.info(
            f"Multi-consult with {len(provider_ids)} providers "
            f"using {request.consensus_strategy} strategy"
        )
        
        # Query all providers concurrently
        tasks = [
            self._query_provider(provider_id, request.branch_id, request.query)
            for provider_id in provider_ids
        ]
        
        try:
            responses = await asyncio.wait_for(
                asyncio.gather(*tasks, return_exceptions=True),
                timeout=request.timeout_seconds
            )
        except asyncio.TimeoutError:
            logger.warning(f"Multi-consult timeout after {request.timeout_seconds}s")
            responses = []
        
        # Filter successful responses
        successful_responses = [
            r for r in responses
            if isinstance(r, ProviderResponse) and r.success
        ]
        
        if len(successful_responses) < request.min_providers:
            raise ValueError(
                f"Not enough successful responses. "
                f"Required: {request.min_providers}, Got: {len(successful_responses)}"
            )
        
        # Apply consensus strategy
        consensus = await self._apply_consensus(
            successful_responses,
            request.consensus_strategy
        )
        
        # Add individual responses if requested
        if request.include_reasoning:
            consensus.individual_responses = successful_responses
        
        # Calculate total time
        total_time = (time.time() - start_time) * 1000
        consensus.total_response_time_ms = total_time

        # Create a dialogue entry with the consensus result
        # We'll use the first successful provider's dialogue_id
        # In a real implementation, we might want to create a new dialogue
        # that references all the provider dialogues
        dialogue_id = f"consensus-{request.branch_id}-{int(time.time() * 1000)}"

        return MultiConsultResponse(
            dialogue_id=dialogue_id,
            consensus=consensus,
            created_at=datetime.now()
        )
    
    async def _query_provider(
        self,
        provider_id: str,
        branch_id: str,
        query: str
    ) -> ProviderResponse:
        """Query a single provider with circuit breaker protection."""
        start_time = time.time()

        try:
            # Get provider config
            provider = self.providers.get(provider_id)
            if not provider or not provider.enabled:
                return ProviderResponse(
                    provider_id=provider_id,
                    response="",
                    response_time_ms=0.0,
                    success=False,
                    error="Provider not available"
                )

            # Check circuit breaker status
            provider_health = llm_error_handler.get_provider_health(provider_id)
            if not provider_health["is_available"]:
                logger.warning(f"Provider {provider_id} circuit breaker is OPEN, skipping")
                return ProviderResponse(
                    provider_id=provider_id,
                    response="",
                    response_time_ms=0.0,
                    success=False,
                    error=f"Provider circuit breaker is {provider_health['circuit_state']}"
                )

            # Create consultation request
            request = ConsultationRequest(
                branch_id=branch_id,
                query=query,
                provider_id=provider_id
            )

            # Consult oracle (oracle_service now uses llm_error_handler internally)
            result = await self.oracle_service.consult_oracle(request)

            # Calculate response time
            response_time = (time.time() - start_time) * 1000

            # Get the dialogue to extract the response text
            dialogue = await self.oracle_service.get_dialogue(result.dialogue_id)

            # Extract response from dialogue messages
            response_text = ""
            if dialogue and dialogue.messages:
                # Get the last assistant message
                for msg in reversed(dialogue.messages):
                    if msg.role == "assistant":
                        response_text = msg.content
                        break

            if not response_text:
                response_text = f"Consultation completed. Dialogue ID: {result.dialogue_id}"

            # Update usage stats
            self._update_usage_stats(provider_id, True, response_time)

            # Update provider health status to healthy
            self._update_provider_health(provider_id, ProviderStatus.HEALTHY)

            return ProviderResponse(
                provider_id=provider_id,
                response=response_text,
                response_time_ms=response_time,
                tokens_used=0,  # TODO: Track tokens
                success=True
            )
            
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            logger.error(f"Provider {provider_id} failed: {e}", exc_info=True)

            # Update usage stats
            self._update_usage_stats(provider_id, False, response_time)

            # Update provider health status to unhealthy
            self._update_provider_health(provider_id, ProviderStatus.UNHEALTHY)

            return ProviderResponse(
                provider_id=provider_id,
                response="",
                response_time_ms=response_time,
                success=False,
                error=str(e)
            )

    async def _apply_consensus(
        self,
        responses: List[ProviderResponse],
        strategy: ConsensusStrategy
    ) -> ConsensusResult:
        """Apply consensus strategy to provider responses."""
        if not responses:
            raise ValueError("No responses to apply consensus")

        if strategy == ConsensusStrategy.FIRST_SUCCESS:
            # Return first successful response
            final_response = responses[0].response
            confidence = responses[0].confidence
            reasoning = "First successful response"

        elif strategy == ConsensusStrategy.MAJORITY_VOTE:
            # Find most common response (simplified - just use first for now)
            # TODO: Implement proper similarity matching
            final_response = responses[0].response
            confidence = len(responses) / (len(responses) + 1)
            reasoning = f"Majority vote from {len(responses)} providers"

        elif strategy == ConsensusStrategy.WEIGHTED_AVERAGE:
            # Weight responses by provider weight
            total_weight = sum(
                self.providers[r.provider_id].weight
                for r in responses
                if r.provider_id in self.providers
            )
            # For now, use first response (TODO: implement proper weighting)
            final_response = responses[0].response
            confidence = total_weight / len(responses)
            reasoning = f"Weighted average from {len(responses)} providers"

        elif strategy == ConsensusStrategy.BEST_QUALITY:
            # Select response with highest confidence
            best_response = max(responses, key=lambda r: r.confidence)
            final_response = best_response.response
            confidence = best_response.confidence
            reasoning = f"Best quality from provider {best_response.provider_id}"

        else:  # ALL_AGREE
            # Check if all responses are similar (simplified)
            final_response = responses[0].response
            confidence = 1.0 if len(responses) == 1 else 0.8
            reasoning = f"All {len(responses)} providers agree"

        return ConsensusResult(
            final_response=final_response,
            confidence=confidence,
            strategy_used=strategy,
            providers_used=[r.provider_id for r in responses],
            providers_succeeded=len(responses),
            providers_failed=0,
            total_response_time_ms=sum(r.response_time_ms for r in responses),
            reasoning=reasoning
        )

    def _update_usage_stats(
        self,
        provider_id: str,
        success: bool,
        response_time_ms: float
    ):
        """Update provider usage statistics."""
        if provider_id not in self.provider_usage:
            self.provider_usage[provider_id] = ProviderUsageStats(
                provider_id=provider_id
            )

        stats = self.provider_usage[provider_id]
        stats.total_requests += 1

        if success:
            stats.successful_requests += 1
        else:
            stats.failed_requests += 1

        # Update average response time
        total_time = stats.average_response_time_ms * (stats.total_requests - 1)
        stats.average_response_time_ms = (total_time + response_time_ms) / stats.total_requests
        stats.last_used = datetime.now()

    async def select_provider(
        self,
        request: ProviderSelectionRequest
    ) -> ProviderSelectionResponse:
        """
        Intelligently select the best provider for a query.

        Args:
            request: Provider selection request

        Returns:
            Selected provider with reasoning
        """
        # Get available providers
        available_providers = [
            p for p_id, p in self.providers.items()
            if p.enabled
            and (not request.exclude_providers or p_id not in request.exclude_providers)
            and (not request.preferred_providers or p_id in request.preferred_providers)
        ]

        if not available_providers:
            raise ValueError("No providers available matching criteria")

        # Score providers based on criteria
        scored_providers = []
        for provider in available_providers:
            score = 0.0

            # Priority score
            score += provider.priority * 10

            # Health score
            health = self.provider_health.get(provider.provider_id)
            if health and health.status == ProviderStatus.HEALTHY:
                score += 50
            elif health and health.status == ProviderStatus.DEGRADED:
                score += 25

            # Usage stats score
            usage = self.provider_usage.get(provider.provider_id)
            if usage:
                # Prefer providers with good success rate
                if usage.total_requests > 0:
                    success_rate = usage.successful_requests / usage.total_requests
                    score += success_rate * 30

                # Fast response preference
                if request.require_fast_response and usage.average_response_time_ms > 0:
                    # Prefer faster providers
                    score += max(0, 20 - (usage.average_response_time_ms / 100))

            scored_providers.append((provider, score))

        # Select best provider
        best_provider, best_score = max(scored_providers, key=lambda x: x[1])

        # Get estimated metrics
        usage = self.provider_usage.get(best_provider.provider_id)
        estimated_time = usage.average_response_time_ms if usage else 1000.0
        estimated_cost = 0.0  # TODO: Implement cost estimation

        return ProviderSelectionResponse(
            provider_id=best_provider.provider_id,
            provider_type=best_provider.provider_type,
            reason=f"Selected based on priority, health, and performance (score: {best_score:.1f})",
            estimated_response_time_ms=estimated_time,
            estimated_cost_usd=estimated_cost,
            confidence=min(1.0, best_score / 100)
        )

    async def get_provider_health(self) -> ProviderHealthResponse:
        """Get health status of all providers."""
        # Update health checks
        await self._check_all_providers_health()

        health_checks = list(self.provider_health.values())

        healthy_count = sum(1 for h in health_checks if h.status == ProviderStatus.HEALTHY)
        degraded_count = sum(1 for h in health_checks if h.status == ProviderStatus.DEGRADED)
        unhealthy_count = sum(1 for h in health_checks if h.status == ProviderStatus.UNHEALTHY)

        return ProviderHealthResponse(
            providers=health_checks,
            healthy_count=healthy_count,
            degraded_count=degraded_count,
            unhealthy_count=unhealthy_count,
            last_updated=datetime.now()
        )

    async def _check_all_providers_health(self):
        """Check health of all providers."""
        for provider_id in self.providers:
            await self._check_provider_health(provider_id)

    async def _check_provider_health(self, provider_id: str):
        """Check health of a single provider."""
        start_time = time.time()

        try:
            # Simple health check - try to get provider info
            provider = self.providers.get(provider_id)
            if not provider or not provider.enabled:
                self.provider_health[provider_id] = ProviderHealthCheck(
                    provider_id=provider_id,
                    status=ProviderStatus.UNHEALTHY,
                    response_time_ms=0.0,
                    last_check=datetime.now(),
                    message="Provider disabled"
                )
                return

            # Calculate error rate from usage stats
            usage = self.provider_usage.get(provider_id)
            error_rate = 0.0
            if usage and usage.total_requests > 0:
                error_rate = usage.failed_requests / usage.total_requests

            # Determine status based on error rate
            if error_rate < 0.1:
                status = ProviderStatus.HEALTHY
            elif error_rate < 0.3:
                status = ProviderStatus.DEGRADED
            else:
                status = ProviderStatus.UNHEALTHY

            response_time = (time.time() - start_time) * 1000

            self.provider_health[provider_id] = ProviderHealthCheck(
                provider_id=provider_id,
                status=status,
                response_time_ms=response_time,
                last_check=datetime.now(),
                error_rate=error_rate,
                success_count=usage.successful_requests if usage else 0,
                failure_count=usage.failed_requests if usage else 0
            )

        except Exception as e:
            logger.error(f"Health check failed for {provider_id}: {e}")
            self.provider_health[provider_id] = ProviderHealthCheck(
                provider_id=provider_id,
                status=ProviderStatus.UNHEALTHY,
                response_time_ms=0.0,
                last_check=datetime.now(),
                message=str(e)
            )

    async def get_provider_usage(
        self,
        period_start: Optional[datetime] = None,
        period_end: Optional[datetime] = None
    ) -> ProviderUsageResponse:
        """Get usage statistics for all providers."""
        if not period_start:
            period_start = datetime.now() - timedelta(days=1)
        if not period_end:
            period_end = datetime.now()

        usage_stats = list(self.provider_usage.values())

        total_requests = sum(u.total_requests for u in usage_stats)
        total_tokens = sum(u.total_tokens for u in usage_stats)
        total_cost = sum(u.cost_usd for u in usage_stats)

        return ProviderUsageResponse(
            providers=usage_stats,
            total_requests=total_requests,
            total_tokens=total_tokens,
            total_cost_usd=total_cost,
            period_start=period_start,
            period_end=period_end
        )

    async def execute_fallback_chain(
        self,
        chain_config: FallbackChainConfig,
        branch_id: str,
        query: str
    ) -> FallbackChainResponse:
        """Execute a fallback chain of providers."""
        start_time = time.time()
        attempts = 0
        errors = []

        for provider_id in chain_config.provider_ids:
            if attempts >= chain_config.max_attempts:
                break

            attempts += 1

            try:
                response = await self._query_provider(provider_id, branch_id, query)

                if response.success:
                    total_time = (time.time() - start_time) * 1000
                    return FallbackChainResponse(
                        chain_id=chain_config.chain_id,
                        successful_provider_id=provider_id,
                        attempts=attempts,
                        total_time_ms=total_time,
                        response=response.response,
                        errors=errors
                    )
                else:
                    errors.append(f"{provider_id}: {response.error}")

            except Exception as e:
                errors.append(f"{provider_id}: {str(e)}")

            # Wait before next attempt
            if attempts < len(chain_config.provider_ids):
                await asyncio.sleep(chain_config.retry_delay_seconds)

        raise ValueError(
            f"All providers in fallback chain failed after {attempts} attempts. "
            f"Errors: {'; '.join(errors)}"
        )

    def _update_provider_health(self, provider_id: str, status: ProviderStatus):
        """Update provider health status."""
        if provider_id in self.provider_health:
            self.provider_health[provider_id].status = status
            self.provider_health[provider_id].last_check = datetime.now()
            logger.info(f"Provider {provider_id} health status updated to {status.value}")
        else:
            # Create new health check entry
            self.provider_health[provider_id] = ProviderHealthCheck(
                provider_id=provider_id,
                status=status,
                response_time_ms=0.0,
                last_check=datetime.now()
            )
            logger.info(f"Provider {provider_id} health status initialized to {status.value}")

