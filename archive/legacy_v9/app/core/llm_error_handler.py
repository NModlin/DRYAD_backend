"""
LLM Error Handler - Centralized error handling for LLM operations

Provides comprehensive error handling, circuit breaker integration,
and graceful degradation for all LLM provider interactions.
"""

import asyncio
import traceback
from typing import Any, Callable, Optional, Dict, Awaitable
from enum import Enum
from dataclasses import dataclass
from datetime import datetime

from app.core.circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerConfig,
    CircuitBreakerOpenException,
    get_circuit_breaker
)
from app.core.logging_config import get_logger

logger = get_logger(__name__)


class LLMErrorType(Enum):
    """Types of LLM errors."""
    TIMEOUT = "timeout"
    CRASH = "crash"
    ASSERTION_FAILURE = "assertion_failure"
    MEMORY_ERROR = "memory_error"
    MODEL_NOT_FOUND = "model_not_found"
    API_ERROR = "api_error"
    RATE_LIMIT = "rate_limit"
    CONTEXT_LENGTH = "context_length"
    NETWORK_ERROR = "network_error"
    UNKNOWN = "unknown"


@dataclass
class LLMError:
    """Structured LLM error information."""
    error_type: LLMErrorType
    provider_id: str
    message: str
    original_exception: Optional[Exception] = None
    timestamp: datetime = None
    recoverable: bool = True
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "error_type": self.error_type.value,
            "provider_id": self.provider_id,
            "message": self.message,
            "timestamp": self.timestamp.isoformat(),
            "recoverable": self.recoverable,
            "exception_type": type(self.original_exception).__name__ if self.original_exception else None
        }


class LLMErrorHandler:
    """
    Centralized error handler for LLM operations.
    
    Features:
    - Circuit breaker integration per provider
    - Error classification and recovery suggestions
    - Graceful degradation
    - Timeout protection
    - Retry logic with exponential backoff
    """
    
    def __init__(self):
        self._circuit_breakers: Dict[str, CircuitBreaker] = {}
        self._error_history: Dict[str, list] = {}
        logger.info("LLM Error Handler initialized")
    
    def get_circuit_breaker(self, provider_id: str) -> CircuitBreaker:
        """Get or create circuit breaker for provider."""
        if provider_id not in self._circuit_breakers:
            config = CircuitBreakerConfig(
                failure_threshold=3,  # Open after 3 consecutive failures
                recovery_timeout=60,  # Try again after 60 seconds
                success_threshold=2,  # Close after 2 consecutive successes
                timeout=120,  # 120 second timeout for LLM calls (increased for Ollama model loading)
                expected_exception=(Exception,)
            )
            self._circuit_breakers[provider_id] = get_circuit_breaker(
                f"llm_provider_{provider_id}",
                config
            )
        return self._circuit_breakers[provider_id]
    
    def classify_error(self, exception: Exception, provider_id: str) -> LLMError:
        """
        Classify an LLM error and determine if it's recoverable.
        
        Args:
            exception: The exception that occurred
            provider_id: ID of the LLM provider
            
        Returns:
            Structured LLM error
        """
        error_str = str(exception).lower()
        exception_type = type(exception).__name__
        
        # GGML/llama-cpp-python crashes
        if "ggml_assert" in error_str or "assertion" in error_str:
            return LLMError(
                error_type=LLMErrorType.ASSERTION_FAILURE,
                provider_id=provider_id,
                message=f"LLM assertion failure: {exception}",
                original_exception=exception,
                recoverable=False  # Assertion failures are not recoverable
            )
        
        # Timeout errors
        if isinstance(exception, asyncio.TimeoutError) or "timeout" in error_str:
            return LLMError(
                error_type=LLMErrorType.TIMEOUT,
                provider_id=provider_id,
                message=f"LLM request timeout: {exception}",
                original_exception=exception,
                recoverable=True
            )
        
        # Memory errors
        if "memory" in error_str or "oom" in error_str or isinstance(exception, MemoryError):
            return LLMError(
                error_type=LLMErrorType.MEMORY_ERROR,
                provider_id=provider_id,
                message=f"LLM memory error: {exception}",
                original_exception=exception,
                recoverable=False
            )
        
        # Model not found
        if "model" in error_str and ("not found" in error_str or "missing" in error_str):
            return LLMError(
                error_type=LLMErrorType.MODEL_NOT_FOUND,
                provider_id=provider_id,
                message=f"LLM model not found: {exception}",
                original_exception=exception,
                recoverable=False
            )
        
        # API errors
        if "api" in error_str or "401" in error_str or "403" in error_str:
            return LLMError(
                error_type=LLMErrorType.API_ERROR,
                provider_id=provider_id,
                message=f"LLM API error: {exception}",
                original_exception=exception,
                recoverable=True
            )
        
        # Rate limit errors
        if "rate limit" in error_str or "429" in error_str:
            return LLMError(
                error_type=LLMErrorType.RATE_LIMIT,
                provider_id=provider_id,
                message=f"LLM rate limit exceeded: {exception}",
                original_exception=exception,
                recoverable=True
            )
        
        # Context length errors
        if "context" in error_str and ("length" in error_str or "window" in error_str):
            return LLMError(
                error_type=LLMErrorType.CONTEXT_LENGTH,
                provider_id=provider_id,
                message=f"LLM context length exceeded: {exception}",
                original_exception=exception,
                recoverable=True
            )
        
        # Network errors
        if "connection" in error_str or "network" in error_str or "unreachable" in error_str:
            return LLMError(
                error_type=LLMErrorType.NETWORK_ERROR,
                provider_id=provider_id,
                message=f"LLM network error: {exception}",
                original_exception=exception,
                recoverable=True
            )
        
        # Unknown error
        return LLMError(
            error_type=LLMErrorType.UNKNOWN,
            provider_id=provider_id,
            message=f"Unknown LLM error: {exception}",
            original_exception=exception,
            recoverable=True  # Assume recoverable unless proven otherwise
        )
    
    def record_error(self, error: LLMError):
        """Record error in history."""
        if error.provider_id not in self._error_history:
            self._error_history[error.provider_id] = []
        
        self._error_history[error.provider_id].append(error)
        
        # Keep only last 100 errors per provider
        if len(self._error_history[error.provider_id]) > 100:
            self._error_history[error.provider_id] = self._error_history[error.provider_id][-100:]
    
    async def safe_llm_call(
        self,
        provider_id: str,
        llm_func: Callable[..., Awaitable[Any]],
        *args,
        fallback_response: Optional[str] = None,
        **kwargs
    ) -> Any:
        """
        Execute an LLM call with comprehensive error handling.
        
        Args:
            provider_id: ID of the LLM provider
            llm_func: Async function to call the LLM
            *args: Arguments for llm_func
            fallback_response: Optional fallback response if LLM fails
            **kwargs: Keyword arguments for llm_func
            
        Returns:
            LLM response or fallback response
            
        Raises:
            LLMError: If error is not recoverable and no fallback provided
        """
        circuit_breaker = self.get_circuit_breaker(provider_id)
        
        try:
            # Execute through circuit breaker (includes timeout)
            result = await circuit_breaker.call(llm_func, *args, **kwargs)
            return result
            
        except CircuitBreakerOpenException as e:
            # Circuit is open - provider is unavailable
            error = LLMError(
                error_type=LLMErrorType.CRASH,
                provider_id=provider_id,
                message=f"Provider circuit breaker is OPEN: {e}",
                original_exception=e,
                recoverable=False
            )
            self.record_error(error)
            logger.error(f"Circuit breaker OPEN for provider {provider_id}: {e}")
            
            if fallback_response:
                logger.info(f"Using fallback response for provider {provider_id}")
                return fallback_response
            raise
            
        except Exception as e:
            # Classify and handle the error
            error = self.classify_error(e, provider_id)
            self.record_error(error)
            
            logger.error(
                f"LLM error for provider {provider_id}: {error.error_type.value} - {error.message}",
                exc_info=True
            )
            
            # Use fallback if available
            if fallback_response:
                logger.info(f"Using fallback response for provider {provider_id} after {error.error_type.value}")
                return fallback_response
            
            # Re-raise if not recoverable
            if not error.recoverable:
                raise
            
            # For recoverable errors, raise with context
            raise Exception(f"LLM {error.error_type.value}: {error.message}") from e
    
    def get_provider_health(self, provider_id: str) -> Dict[str, Any]:
        """Get health status for a provider."""
        circuit_breaker = self.get_circuit_breaker(provider_id)
        stats = circuit_breaker.get_stats()
        
        # Get recent errors
        recent_errors = self._error_history.get(provider_id, [])[-10:]
        
        return {
            "provider_id": provider_id,
            "circuit_state": stats["state"],
            "is_available": circuit_breaker.is_available,
            "total_requests": stats["total_requests"],
            "success_rate": stats["success_rate"],
            "consecutive_failures": stats["consecutive_failures"],
            "last_failure_time": stats["last_failure_time"],
            "recent_errors": [e.to_dict() for e in recent_errors]
        }
    
    def get_all_provider_health(self) -> Dict[str, Dict[str, Any]]:
        """Get health status for all providers."""
        return {
            provider_id: self.get_provider_health(provider_id)
            for provider_id in self._circuit_breakers.keys()
        }


# Global LLM error handler instance
llm_error_handler = LLMErrorHandler()

