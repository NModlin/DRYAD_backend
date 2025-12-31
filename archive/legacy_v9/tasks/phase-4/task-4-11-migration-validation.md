# Task 4-11: Microservices Migration Validation & Testing

**Phase:** 4 - Forest Ecosystem Architecture  
**Week:** 20  
**Estimated Hours:** 8 hours  
**Priority:** CRITICAL  
**Dependencies:** All Phase 4 tasks (4-01 through 4-10)

---

## 🎯 OBJECTIVE

Validate the complete microservices migration from monolithic architecture. Perform comprehensive integration testing, performance benchmarking, and ensure all services communicate correctly via Mycelium Network.

---

## 📋 REQUIREMENTS

### Functional Requirements
- All services operational independently
- Inter-service communication working
- Data consistency across services
- Service discovery functional
- Circuit breakers operational
- Complete GAD workflow functional

### Technical Requirements
- Integration test suite
- E2E test scenarios
- Performance benchmarks
- Load testing
- Chaos engineering tests

### Performance Requirements
- Service-to-service latency: <10ms (p95)
- Complete workflow time: <30 minutes
- System throughput: >100 workflows/hour
- Uptime: >99.9%

---

## 🔧 IMPLEMENTATION

**File:** `tests/integration/test_microservices_migration.py`

```python
"""
Microservices Migration Validation Tests
Comprehensive testing of Forest Ecosystem Architecture.
"""

import pytest
import asyncio
from uuid import uuid4


@pytest.mark.integration
@pytest.mark.asyncio
async def test_service_discovery():
    """Test all services can be discovered."""
    from services.mycelium.app.core.service_discovery import ServiceRegistry
    
    registry = ServiceRegistry()
    
    # Register all services
    await registry.register_service("oracle", "http://oracle:8000")
    await registry.register_service("agent-studio", "http://agent-studio:8000")
    await registry.register_service("grove-keeper", "http://grove-keeper:8000")
    await registry.register_service("guardian", "http://guardian:8000")
    await registry.register_service("vessel", "http://vessel:8000")
    
    # Discover each service
    oracle_url = await registry.discover_service("oracle")
    assert oracle_url is not None
    
    agent_studio_url = await registry.discover_service("agent-studio")
    assert agent_studio_url is not None


@pytest.mark.integration
@pytest.mark.asyncio
async def test_inter_service_communication():
    """Test services can communicate via Mycelium."""
    from services.mycelium.app.core.forest_protocol import MyceliumClient
    
    client = MyceliumClient(service_name="test-service")
    
    # Call Oracle service
    response = await client.call_oracle(
        prompt="Test prompt",
        model_tier="fast",
    )
    
    assert response is not None


@pytest.mark.integration
@pytest.mark.asyncio
async def test_complete_gad_workflow_microservices():
    """
    Test complete GAD workflow across microservices.
    
    Flow:
    1. Grove Keeper receives request
    2. Calls Oracle via Mycelium for plan generation
    3. Calls Guardian for authorization
    4. Calls Agent Studio for agent discovery
    5. Executes workflow
    6. Returns result
    """
    # Implementation would test complete flow
    pass


@pytest.mark.performance
@pytest.mark.asyncio
async def test_service_latency():
    """Test inter-service latency meets requirements."""
    import time
    from services.mycelium.app.core.forest_protocol import MyceliumClient
    
    client = MyceliumClient(service_name="test-service")
    
    # Measure latency
    start = time.time()
    await client.send_message(
        target_service="oracle",
        operation="health_check",
        payload={},
    )
    latency_ms = (time.time() - start) * 1000
    
    # Should be < 10ms (p95)
    assert latency_ms < 10


@pytest.mark.load
@pytest.mark.asyncio
async def test_system_throughput():
    """Test system can handle required throughput."""
    # Create 100 concurrent workflows
    tasks = [
        create_test_workflow()
        for _ in range(100)
    ]
    
    start = time.time()
    results = await asyncio.gather(*tasks)
    duration = time.time() - start
    
    # Should complete 100 workflows in < 1 hour
    assert duration < 3600
    
    # Calculate throughput
    throughput = len(results) / (duration / 3600)  # workflows/hour
    assert throughput > 100


async def create_test_workflow():
    """Helper to create test workflow."""
    # Implementation
    pass


@pytest.mark.chaos
@pytest.mark.asyncio
async def test_circuit_breaker():
    """Test circuit breaker prevents cascading failures."""
    from services.mycelium.app.core.circuit_breaker import CircuitBreaker
    
    breaker = CircuitBreaker(failure_threshold=3, timeout_seconds=10)
    
    # Simulate failures
    async def failing_function():
        raise RuntimeError("Service unavailable")
    
    # Should open circuit after threshold
    for i in range(5):
        try:
            await breaker.call(failing_function)
        except RuntimeError:
            pass
    
    # Circuit should be open
    assert breaker.state == "OPEN"
```

**File:** `tests/performance/benchmark_microservices.py`

```python
"""Performance benchmarks for microservices."""

import pytest
import time


@pytest.mark.benchmark
def test_oracle_response_time(benchmark):
    """Benchmark Oracle service response time."""
    
    async def call_oracle():
        # Call Oracle service
        pass
    
    result = benchmark(call_oracle)
    
    # Should be < 2 seconds for Fast tier
    assert result < 2.0


@pytest.mark.benchmark
def test_agent_discovery_time(benchmark):
    """Benchmark agent discovery time."""
    
    async def discover_agent():
        # Discover agent
        pass
    
    result = benchmark(discover_agent)
    
    # Should be < 100ms
    assert result < 0.1
```

---

## ✅ DEFINITION OF DONE

- [ ] All integration tests passing
- [ ] E2E scenarios validated
- [ ] Performance benchmarks met
- [ ] Load testing complete
- [ ] Chaos engineering tests passed
- [ ] Migration documentation complete
- [ ] Phase 4 sign-off obtained

---

## 📊 SUCCESS METRICS

- Integration test pass rate: 100%
- Service-to-service latency: <10ms (p95)
- System throughput: >100 workflows/hour
- Uptime: >99.9%
- All services healthy

---

**Estimated Completion:** 8 hours  
**Assigned To:** QA Lead + Integration Team  
**Status:** NOT STARTED

