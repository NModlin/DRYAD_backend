"""
Circuit Breaker Implementation for DRYAD.AI Backend

Provides circuit breaker patterns for external service calls to prevent
cascading failures and enable graceful degradation.
"""

import asyncio
import time
import logging
from enum import Enum
from typing import Dict, Any, Optional, Callable, Awaitable, Union
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import threading

logger = logging.getLogger(__name__)


class CircuitState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Circuit is open, calls fail fast
    HALF_OPEN = "half_open"  # Testing if service is back


@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker."""
    failure_threshold: int = 5          # Failures before opening
    recovery_timeout: int = 60          # Seconds before trying half-open
    success_threshold: int = 3          # Successes to close from half-open
    timeout: int = 30                   # Request timeout in seconds
    expected_exception: tuple = (Exception,)  # Exceptions that count as failures


@dataclass
class CircuitBreakerStats:
    """Statistics for circuit breaker."""
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    consecutive_failures: int = 0
    consecutive_successes: int = 0
    last_failure_time: Optional[datetime] = None
    last_success_time: Optional[datetime] = None
    state_changes: int = 0
    current_state: CircuitState = CircuitState.CLOSED


class CircuitBreakerOpenException(Exception):
    """Exception raised when circuit breaker is open."""
    def __init__(self, service_name: str, last_failure: Optional[str] = None):
        self.service_name = service_name
        self.last_failure = last_failure
        message = f"Circuit breaker is OPEN for service '{service_name}'"
        if last_failure:
            message += f". Last failure: {last_failure}"
        super().__init__(message)


class CircuitBreaker:
    """
    Circuit breaker implementation for protecting external service calls.
    
    Implements the circuit breaker pattern to prevent cascading failures
    and provide graceful degradation when external services are unavailable.
    """
    
    def __init__(self, name: str, config: Optional[CircuitBreakerConfig] = None):
        self.name = name
        self.config = config or CircuitBreakerConfig()
        self.stats = CircuitBreakerStats()
        self._lock = threading.RLock()
        self._last_failure_exception: Optional[Exception] = None
        
        logger.info(f"Circuit breaker '{name}' initialized with config: {self.config}")
    
    @property
    def state(self) -> CircuitState:
        """Get current circuit state."""
        with self._lock:
            return self.stats.current_state
    
    @property
    def is_available(self) -> bool:
        """Check if service is available (circuit not open)."""
        return self.state != CircuitState.OPEN
    
    def _should_attempt_reset(self) -> bool:
        """Check if we should attempt to reset from OPEN to HALF_OPEN."""
        if self.stats.current_state != CircuitState.OPEN:
            return False
        
        if not self.stats.last_failure_time:
            return True
        
        time_since_failure = datetime.now() - self.stats.last_failure_time
        return time_since_failure.total_seconds() >= self.config.recovery_timeout
    
    def _record_success(self):
        """Record a successful call."""
        with self._lock:
            self.stats.total_requests += 1
            self.stats.successful_requests += 1
            self.stats.consecutive_successes += 1
            self.stats.consecutive_failures = 0
            self.stats.last_success_time = datetime.now()
            
            # State transitions
            if self.stats.current_state == CircuitState.HALF_OPEN:
                if self.stats.consecutive_successes >= self.config.success_threshold:
                    self._transition_to_closed()
            elif self.stats.current_state == CircuitState.OPEN:
                # This shouldn't happen, but handle it gracefully
                self._transition_to_half_open()
    
    def _record_failure(self, exception: Exception):
        """Record a failed call."""
        with self._lock:
            self.stats.total_requests += 1
            self.stats.failed_requests += 1
            self.stats.consecutive_failures += 1
            self.stats.consecutive_successes = 0
            self.stats.last_failure_time = datetime.now()
            self._last_failure_exception = exception
            
            # State transitions
            if self.stats.current_state == CircuitState.CLOSED:
                if self.stats.consecutive_failures >= self.config.failure_threshold:
                    self._transition_to_open()
            elif self.stats.current_state == CircuitState.HALF_OPEN:
                self._transition_to_open()
    
    def _transition_to_open(self):
        """Transition circuit to OPEN state."""
        if self.stats.current_state != CircuitState.OPEN:
            logger.warning(
                f"Circuit breaker '{self.name}' transitioning to OPEN state "
                f"after {self.stats.consecutive_failures} consecutive failures"
            )
            self.stats.current_state = CircuitState.OPEN
            self.stats.state_changes += 1
    
    def _transition_to_half_open(self):
        """Transition circuit to HALF_OPEN state."""
        if self.stats.current_state != CircuitState.HALF_OPEN:
            logger.info(f"Circuit breaker '{self.name}' transitioning to HALF_OPEN state")
            self.stats.current_state = CircuitState.HALF_OPEN
            self.stats.state_changes += 1
            self.stats.consecutive_successes = 0
    
    def _transition_to_closed(self):
        """Transition circuit to CLOSED state."""
        if self.stats.current_state != CircuitState.CLOSED:
            logger.info(f"Circuit breaker '{self.name}' transitioning to CLOSED state")
            self.stats.current_state = CircuitState.CLOSED
            self.stats.state_changes += 1
            self.stats.consecutive_failures = 0
    
    async def call(self, func: Callable[..., Awaitable[Any]], *args, **kwargs) -> Any:
        """
        Execute a function call through the circuit breaker.
        
        Args:
            func: Async function to call
            *args: Function arguments
            **kwargs: Function keyword arguments
            
        Returns:
            Function result
            
        Raises:
            CircuitBreakerOpenException: When circuit is open
            Original exception: When function fails
        """
        # Check if we should attempt reset
        if self.stats.current_state == CircuitState.OPEN and self._should_attempt_reset():
            self._transition_to_half_open()
        
        # Fail fast if circuit is open
        if self.stats.current_state == CircuitState.OPEN:
            last_failure = str(self._last_failure_exception) if self._last_failure_exception else None
            raise CircuitBreakerOpenException(self.name, last_failure)
        
        # Attempt the call
        try:
            # Apply timeout
            result = await asyncio.wait_for(
                func(*args, **kwargs),
                timeout=self.config.timeout
            )
            self._record_success()
            return result
            
        except self.config.expected_exception as e:
            self._record_failure(e)
            raise
        except asyncio.TimeoutError as e:
            timeout_error = Exception(f"Request timeout after {self.config.timeout}s")
            self._record_failure(timeout_error)
            raise timeout_error
    
    def call_sync(self, func: Callable[..., Any], *args, **kwargs) -> Any:
        """
        Execute a synchronous function call through the circuit breaker.
        
        Args:
            func: Synchronous function to call
            *args: Function arguments
            **kwargs: Function keyword arguments
            
        Returns:
            Function result
            
        Raises:
            CircuitBreakerOpenException: When circuit is open
            Original exception: When function fails
        """
        # Check if we should attempt reset
        if self.stats.current_state == CircuitState.OPEN and self._should_attempt_reset():
            self._transition_to_half_open()
        
        # Fail fast if circuit is open
        if self.stats.current_state == CircuitState.OPEN:
            last_failure = str(self._last_failure_exception) if self._last_failure_exception else None
            raise CircuitBreakerOpenException(self.name, last_failure)
        
        # Attempt the call
        try:
            result = func(*args, **kwargs)
            self._record_success()
            return result
            
        except self.config.expected_exception as e:
            self._record_failure(e)
            raise
    
    def get_stats(self) -> Dict[str, Any]:
        """Get circuit breaker statistics."""
        with self._lock:
            success_rate = 0
            if self.stats.total_requests > 0:
                success_rate = (self.stats.successful_requests / self.stats.total_requests) * 100
            
            return {
                "name": self.name,
                "state": self.stats.current_state.value,
                "total_requests": self.stats.total_requests,
                "successful_requests": self.stats.successful_requests,
                "failed_requests": self.stats.failed_requests,
                "success_rate": round(success_rate, 2),
                "consecutive_failures": self.stats.consecutive_failures,
                "consecutive_successes": self.stats.consecutive_successes,
                "last_failure_time": self.stats.last_failure_time.isoformat() if self.stats.last_failure_time else None,
                "last_success_time": self.stats.last_success_time.isoformat() if self.stats.last_success_time else None,
                "state_changes": self.stats.state_changes,
                "config": {
                    "failure_threshold": self.config.failure_threshold,
                    "recovery_timeout": self.config.recovery_timeout,
                    "success_threshold": self.config.success_threshold,
                    "timeout": self.config.timeout
                }
            }
    
    def reset(self):
        """Reset circuit breaker to initial state."""
        with self._lock:
            logger.info(f"Resetting circuit breaker '{self.name}'")
            self.stats = CircuitBreakerStats()
            self._last_failure_exception = None


class CircuitBreakerManager:
    """
    Manager for multiple circuit breakers.
    
    Provides centralized management and monitoring of circuit breakers
    for different services.
    """
    
    def __init__(self):
        self._breakers: Dict[str, CircuitBreaker] = {}
        self._lock = threading.RLock()
    
    def get_breaker(self, name: str, config: Optional[CircuitBreakerConfig] = None) -> CircuitBreaker:
        """
        Get or create a circuit breaker.
        
        Args:
            name: Circuit breaker name
            config: Optional configuration
            
        Returns:
            CircuitBreaker instance
        """
        with self._lock:
            if name not in self._breakers:
                self._breakers[name] = CircuitBreaker(name, config)
            return self._breakers[name]
    
    def get_all_stats(self) -> Dict[str, Dict[str, Any]]:
        """Get statistics for all circuit breakers."""
        with self._lock:
            return {name: breaker.get_stats() for name, breaker in self._breakers.items()}
    
    def reset_all(self):
        """Reset all circuit breakers."""
        with self._lock:
            for breaker in self._breakers.values():
                breaker.reset()
    
    def get_health_summary(self) -> Dict[str, Any]:
        """Get overall health summary of all circuit breakers."""
        with self._lock:
            total_breakers = len(self._breakers)
            if total_breakers == 0:
                return {
                    "status": "healthy",
                    "total_breakers": 0,
                    "healthy_breakers": 0,
                    "degraded_breakers": 0,
                    "failed_breakers": 0
                }
            
            healthy = sum(1 for b in self._breakers.values() if b.state == CircuitState.CLOSED)
            degraded = sum(1 for b in self._breakers.values() if b.state == CircuitState.HALF_OPEN)
            failed = sum(1 for b in self._breakers.values() if b.state == CircuitState.OPEN)
            
            # Determine overall status
            if failed == 0:
                status = "healthy" if degraded == 0 else "degraded"
            elif failed < total_breakers:
                status = "degraded"
            else:
                status = "failed"
            
            return {
                "status": status,
                "total_breakers": total_breakers,
                "healthy_breakers": healthy,
                "degraded_breakers": degraded,
                "failed_breakers": failed,
                "breaker_states": {name: breaker.state.value for name, breaker in self._breakers.items()}
            }


# Global circuit breaker manager
circuit_breaker_manager = CircuitBreakerManager()


def get_circuit_breaker(name: str, config: Optional[CircuitBreakerConfig] = None) -> CircuitBreaker:
    """
    Get a circuit breaker instance.
    
    Args:
        name: Circuit breaker name
        config: Optional configuration
        
    Returns:
        CircuitBreaker instance
    """
    return circuit_breaker_manager.get_breaker(name, config)
