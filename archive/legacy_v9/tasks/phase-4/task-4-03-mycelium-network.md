# Task 4-03: Mycelium Network Implementation

**Phase:** 4 - Forest Ecosystem Architecture  
**Week:** 18  
**Estimated Hours:** 24 hours  
**Priority:** CRITICAL  
**Dependencies:** Tasks 4-01, 4-02 (Oracle, Agent Studio)

---

## 🎯 OBJECTIVE

Implement the Mycelium Network - the inter-service communication layer that connects all microservices in the Forest Ecosystem. Provides service discovery, load balancing, circuit breaking, and the Forest Protocol for standardized communication.

---

## 📋 REQUIREMENTS

### Functional Requirements
- Service discovery and registration
- Load balancing across service instances
- Circuit breaker pattern for fault tolerance
- Request/response tracing
- Service mesh integration
- Forest Protocol (standardized message format)
- Health checking and failover

### Technical Requirements
- gRPC for high-performance communication
- Envoy proxy for service mesh
- Consul or etcd for service discovery
- OpenTelemetry for distributed tracing
- Prometheus metrics export

### Performance Requirements
- Service discovery: <50ms
- Inter-service latency: <10ms (p95)
- Circuit breaker response: <1ms
- Throughput: >10,000 req/s

---

## 🔧 IMPLEMENTATION STEPS

### Step 1: Define Forest Protocol (8 hours)

**File:** `services/mycelium/proto/forest_protocol.proto`

```protobuf
syntax = "proto3";

package forest.v1;

// Forest Protocol - Standardized inter-service communication

message ForestRequest {
  string request_id = 1;
  string source_service = 2;
  string target_service = 3;
  string operation = 4;
  bytes payload = 5;
  map<string, string> metadata = 6;
  int64 timestamp = 7;
}

message ForestResponse {
  string request_id = 1;
  bool success = 2;
  bytes payload = 3;
  string error_message = 4;
  map<string, string> metadata = 5;
  int64 timestamp = 6;
}

service ForestCommunication {
  rpc SendMessage(ForestRequest) returns (ForestResponse);
  rpc StreamMessages(stream ForestRequest) returns (stream ForestResponse);
}
```

**File:** `services/mycelium/app/core/forest_protocol.py`

```python
"""
Forest Protocol Implementation
Standardized communication protocol for DRYAD microservices.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field
from structlog import get_logger

logger = get_logger(__name__)


class ForestMessage(BaseModel):
    """Standardized message format for Forest Protocol."""
    
    message_id: UUID = Field(default_factory=uuid4)
    source_service: str
    target_service: str
    operation: str
    payload: dict[str, Any]
    metadata: dict[str, str] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ForestResponse(BaseModel):
    """Standardized response format."""
    
    message_id: UUID
    success: bool
    payload: dict[str, Any] = Field(default_factory=dict)
    error_message: str | None = None
    metadata: dict[str, str] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class MyceliumClient:
    """
    Mycelium Network Client
    
    Provides high-level interface for inter-service communication
    using Forest Protocol.
    """
    
    def __init__(self, service_name: str) -> None:
        self.service_name = service_name
        self.logger = logger.bind(service=service_name)
    
    async def send_message(
        self,
        target_service: str,
        operation: str,
        payload: dict[str, Any],
        metadata: dict[str, str] | None = None,
    ) -> ForestResponse:
        """
        Send message to target service.
        
        Args:
            target_service: Target service name
            operation: Operation to perform
            payload: Message payload
            metadata: Optional metadata
            
        Returns:
            Response from target service
        """
        message = ForestMessage(
            source_service=self.service_name,
            target_service=target_service,
            operation=operation,
            payload=payload,
            metadata=metadata or {},
        )
        
        self.logger.info(
            "sending_message",
            message_id=str(message.message_id),
            target=target_service,
            operation=operation,
        )
        
        # In production, send via gRPC
        # For now, return mock response
        
        return ForestResponse(
            message_id=message.message_id,
            success=True,
            payload={"result": "success"},
        )
    
    async def call_oracle(
        self,
        prompt: str,
        model_tier: str = "balanced",
    ) -> str:
        """
        Convenience method to call Oracle service.
        
        Args:
            prompt: Prompt for LLM
            model_tier: Model tier to use
            
        Returns:
            LLM response text
        """
        response = await self.send_message(
            target_service="oracle",
            operation="consult",
            payload={
                "prompt": prompt,
                "model_tier": model_tier,
            },
        )
        
        if not response.success:
            raise RuntimeError(f"Oracle call failed: {response.error_message}")
        
        return response.payload.get("response", "")
    
    async def register_agent(
        self,
        agent_name: str,
        agent_type: str,
        capabilities: list[dict[str, Any]],
    ) -> UUID:
        """
        Convenience method to register agent with Agent Studio.
        
        Args:
            agent_name: Agent name
            agent_type: Agent type
            capabilities: Agent capabilities
            
        Returns:
            Agent ID
        """
        response = await self.send_message(
            target_service="agent-studio",
            operation="register_agent",
            payload={
                "agent_name": agent_name,
                "agent_type": agent_type,
                "capabilities": capabilities,
            },
        )
        
        if not response.success:
            raise RuntimeError(f"Agent registration failed: {response.error_message}")
        
        return UUID(response.payload["agent_id"])
```

### Step 2: Implement Service Discovery (8 hours)

**File:** `services/mycelium/app/core/service_discovery.py`

```python
"""Service Discovery for Mycelium Network."""

from __future__ import annotations

from typing import Any

from structlog import get_logger

logger = get_logger(__name__)


class ServiceRegistry:
    """
    Service Registry
    
    Manages service registration and discovery.
    """
    
    def __init__(self) -> None:
        self.logger = logger.bind(component="service_registry")
        
        # In production, use Consul or etcd
        self._services: dict[str, list[str]] = {}
    
    async def register_service(
        self,
        service_name: str,
        service_url: str,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """
        Register service instance.
        
        Args:
            service_name: Service name
            service_url: Service URL
            metadata: Optional metadata
        """
        if service_name not in self._services:
            self._services[service_name] = []
        
        self._services[service_name].append(service_url)
        
        self.logger.info(
            "service_registered",
            service=service_name,
            url=service_url,
        )
    
    async def discover_service(self, service_name: str) -> str | None:
        """
        Discover service instance.
        
        Args:
            service_name: Service name
            
        Returns:
            Service URL or None if not found
        """
        instances = self._services.get(service_name, [])
        
        if not instances:
            self.logger.warning("service_not_found", service=service_name)
            return None
        
        # Simple round-robin (in production, use proper load balancing)
        return instances[0]
    
    async def deregister_service(
        self,
        service_name: str,
        service_url: str,
    ) -> None:
        """
        Deregister service instance.
        
        Args:
            service_name: Service name
            service_url: Service URL
        """
        if service_name in self._services:
            self._services[service_name] = [
                url for url in self._services[service_name]
                if url != service_url
            ]
        
        self.logger.info(
            "service_deregistered",
            service=service_name,
            url=service_url,
        )
```

### Step 3: Implement Circuit Breaker (8 hours)

**File:** `services/mycelium/app/core/circuit_breaker.py`

```python
"""Circuit Breaker for fault tolerance."""

from __future__ import annotations

from datetime import datetime, timedelta
from enum import Enum

from structlog import get_logger

logger = get_logger(__name__)


class CircuitState(str, Enum):
    """Circuit breaker states."""
    
    CLOSED = "CLOSED"  # Normal operation
    OPEN = "OPEN"  # Failing, reject requests
    HALF_OPEN = "HALF_OPEN"  # Testing if recovered


class CircuitBreaker:
    """
    Circuit Breaker Pattern
    
    Prevents cascading failures by failing fast when service is down.
    """
    
    def __init__(
        self,
        failure_threshold: int = 5,
        timeout_seconds: int = 60,
    ) -> None:
        self.failure_threshold = failure_threshold
        self.timeout = timedelta(seconds=timeout_seconds)
        self.logger = logger.bind(component="circuit_breaker")
        
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.last_failure_time: datetime | None = None
    
    async def call(self, func, *args, **kwargs):
        """
        Execute function with circuit breaker protection.
        
        Args:
            func: Function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments
            
        Returns:
            Function result
            
        Raises:
            RuntimeError: If circuit is open
        """
        if self.state == CircuitState.OPEN:
            if self._should_attempt_reset():
                self.state = CircuitState.HALF_OPEN
                self.logger.info("circuit_half_open")
            else:
                raise RuntimeError("Circuit breaker is OPEN")
        
        try:
            result = await func(*args, **kwargs)
            self._on_success()
            return result
            
        except Exception as e:
            self._on_failure()
            raise
    
    def _on_success(self) -> None:
        """Handle successful call."""
        self.failure_count = 0
        
        if self.state == CircuitState.HALF_OPEN:
            self.state = CircuitState.CLOSED
            self.logger.info("circuit_closed")
    
    def _on_failure(self) -> None:
        """Handle failed call."""
        self.failure_count += 1
        self.last_failure_time = datetime.utcnow()
        
        if self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN
            self.logger.warning(
                "circuit_opened",
                failure_count=self.failure_count,
            )
    
    def _should_attempt_reset(self) -> bool:
        """Check if should attempt to reset circuit."""
        if self.last_failure_time is None:
            return False
        
        return datetime.utcnow() - self.last_failure_time >= self.timeout
```

---

## ✅ DEFINITION OF DONE

- [ ] Forest Protocol defined
- [ ] Service discovery working
- [ ] Circuit breaker implemented
- [ ] gRPC communication functional
- [ ] Load balancing operational
- [ ] All tests passing (>85% coverage)
- [ ] Documentation complete

---

## 📊 SUCCESS METRICS

- Service discovery: <50ms
- Inter-service latency: <10ms (p95)
- Circuit breaker effectiveness: >95%
- Throughput: >10,000 req/s
- Test coverage: >85%

---

**Estimated Completion:** 24 hours  
**Assigned To:** Backend Developer + Infrastructure Engineer  
**Status:** NOT STARTED

