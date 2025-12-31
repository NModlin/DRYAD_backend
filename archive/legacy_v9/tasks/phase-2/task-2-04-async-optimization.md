# Task 2-04: Async Operation Optimization

**Phase:** 2 - Performance & Production Readiness  
**Week:** 5  
**Estimated Hours:** 6 hours  
**Priority:** HIGH  
**Dependencies:** None

---

## 🎯 OBJECTIVE

Optimize async operations using asyncio.gather, concurrent execution, and proper async patterns.

---

## 📋 REQUIREMENTS

### Functional Requirements
- Identify parallelizable operations
- Implement concurrent execution
- Optimize async/await usage
- Add timeout handling
- Error handling for concurrent ops

### Technical Requirements
- asyncio.gather for parallel execution
- asyncio.wait_for for timeouts
- Proper exception handling
- Resource cleanup

### Performance Requirements
- Concurrent operations: 3-5x faster
- Timeout handling: 100%
- No resource leaks

---

## 🔧 IMPLEMENTATION

**File:** `app/services/async_patterns.py`

```python
"""
Async Optimization Patterns
"""

from __future__ import annotations

import asyncio
from typing import Any

from structlog import get_logger

logger = get_logger(__name__)


async def fetch_agent_data_parallel(agent_id: UUID) -> dict[str, Any]:
    """
    Fetch agent data using parallel execution.
    
    ❌ Sequential (slow):
    executions = await get_executions(agent_id)
    metrics = await get_metrics(agent_id)
    config = await get_config(agent_id)
    
    ✅ Parallel (fast):
    """
    executions, metrics, config = await asyncio.gather(
        get_executions(agent_id),
        get_metrics(agent_id),
        get_config(agent_id),
        return_exceptions=True,  # Don't fail all if one fails
    )
    
    return {
        "executions": executions if not isinstance(executions, Exception) else [],
        "metrics": metrics if not isinstance(metrics, Exception) else {},
        "config": config if not isinstance(config, Exception) else {},
    }


async def process_with_timeout(
    coro,
    timeout: float = 30.0,
) -> Any:
    """Execute async operation with timeout."""
    try:
        return await asyncio.wait_for(coro, timeout=timeout)
    except asyncio.TimeoutError:
        logger.error("operation_timeout", timeout=timeout)
        raise


async def batch_process(
    items: list[Any],
    process_func,
    batch_size: int = 10,
) -> list[Any]:
    """Process items in batches concurrently."""
    results = []
    
    for i in range(0, len(items), batch_size):
        batch = items[i:i + batch_size]
        batch_results = await asyncio.gather(
            *[process_func(item) for item in batch],
            return_exceptions=True,
        )
        results.extend(batch_results)
    
    return results
```

---

## ✅ DEFINITION OF DONE

- [ ] Parallel operations identified
- [ ] asyncio.gather implemented
- [ ] Timeout handling added
- [ ] Performance improved
- [ ] Tests passing

---

## 📊 SUCCESS METRICS

- Parallel speedup: 3-5x
- Timeout handling: 100%
- No resource leaks

---

**Estimated Completion:** 6 hours  
**Status:** NOT STARTED

