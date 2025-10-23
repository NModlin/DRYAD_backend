# Task 1-23: Performance Baseline Establishment

**Phase:** 1 - Foundation & Beta Readiness  
**Week:** 4  
**Estimated Hours:** 4 hours  
**Priority:** HIGH  
**Dependencies:** None

---

## 🎯 OBJECTIVE

Establish performance baselines for all critical endpoints and operations to track performance over time.

---

## 📋 REQUIREMENTS

### Functional Requirements
- Measure endpoint response times
- Measure database query performance
- Measure throughput
- Document baseline metrics
- Set performance targets

### Technical Requirements
- Load testing tools (Locust)
- Performance monitoring
- Metrics collection
- Baseline documentation

---

## 🔧 IMPLEMENTATION

**File:** `tests/performance/locustfile.py`

```python
"""
Performance Tests
Locust load testing configuration.
"""

from locust import HttpUser, task, between
from uuid import uuid4


class DRYADUser(HttpUser):
    """Simulated DRYAD user."""
    
    wait_time = between(1, 3)
    
    @task(3)
    def get_agent_executions(self):
        """Test agent execution history endpoint."""
        agent_id = uuid4()
        self.client.get(f"/api/v1/agent-studio/agents/{agent_id}/executions")
    
    @task(2)
    def get_agent_metrics(self):
        """Test agent metrics endpoint."""
        agent_id = uuid4()
        self.client.get(f"/api/v1/agent-studio/agents/{agent_id}/metrics")
    
    @task(1)
    def health_check(self):
        """Test health endpoint."""
        self.client.get("/api/v1/health")
```

**File:** `scripts/performance_baseline.py`

```python
"""
Performance Baseline Script
Measure and document baseline performance.
"""

from __future__ import annotations

import asyncio
import time
from statistics import mean, median, stdev
from typing import Callable

from structlog import get_logger

logger = get_logger(__name__)


class PerformanceBaseline:
    """Measure performance baselines."""
    
    def __init__(self):
        self.results = {}
    
    async def measure_endpoint(
        self,
        name: str,
        func: Callable,
        iterations: int = 100,
    ) -> dict:
        """Measure endpoint performance."""
        times = []
        
        for _ in range(iterations):
            start = time.perf_counter()
            await func()
            end = time.perf_counter()
            times.append((end - start) * 1000)  # Convert to ms
        
        return {
            'name': name,
            'iterations': iterations,
            'mean_ms': mean(times),
            'median_ms': median(times),
            'p95_ms': sorted(times)[int(0.95 * len(times))],
            'p99_ms': sorted(times)[int(0.99 * len(times))],
            'std_dev': stdev(times),
        }
    
    def generate_baseline_report(self) -> str:
        """Generate baseline report."""
        report = """
# Performance Baseline Report

## Endpoint Performance

| Endpoint | Mean (ms) | Median (ms) | P95 (ms) | P99 (ms) |
|----------|-----------|-------------|----------|----------|
"""
        for result in self.results.values():
            report += f"| {result['name']} | {result['mean_ms']:.2f} | "
            report += f"{result['median_ms']:.2f} | {result['p95_ms']:.2f} | "
            report += f"{result['p99_ms']:.2f} |\n"
        
        return report
```

**File:** `docs/PERFORMANCE_BASELINE.md`

```markdown
# DRYAD.AI Performance Baseline

**Date:** 2025-01-20  
**Version:** Beta v1.0

## Baseline Metrics

### API Endpoints

| Endpoint | Mean | P95 | P99 | Target |
|----------|------|-----|-----|--------|
| GET /agents/{id}/executions | 45ms | 80ms | 120ms | <100ms |
| GET /agents/{id}/metrics | 35ms | 60ms | 90ms | <100ms |
| POST /sandbox/cleanup | 150ms | 250ms | 350ms | <500ms |

### Database Operations

| Operation | Mean | P95 | Target |
|-----------|------|-----|--------|
| Insert execution | 5ms | 10ms | <20ms |
| Query executions | 8ms | 15ms | <30ms |
| Update status | 4ms | 8ms | <15ms |

### Throughput

- **Requests/second:** 500
- **Concurrent users:** 100
- **Error rate:** <0.1%

## Performance Targets

- API response time: <200ms (P95)
- Database queries: <50ms (P95)
- Throughput: >1000 req/s
- Error rate: <1%
```

---

## ✅ DEFINITION OF DONE

- [ ] Performance tests created
- [ ] Baseline measurements taken
- [ ] Metrics documented
- [ ] Targets established
- [ ] Monitoring configured

---

## 📊 SUCCESS METRICS

- All endpoints measured
- Baseline documented
- Targets defined
- Monitoring active

---

**Estimated Completion:** 4 hours  
**Status:** NOT STARTED

