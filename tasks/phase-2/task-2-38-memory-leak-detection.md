# Task 2-38: Memory Leak Detection

**Phase:** 2 - Performance & Production Readiness  
**Week:** 6 - Monitoring & Observability  
**Priority:** HIGH  
**Estimated Hours:** 4 hours

---

## 📋 OVERVIEW

Implement memory leak detection and monitoring using memory profiling tools, tracking memory growth patterns, and automated leak detection to ensure stable long-term operation.

---

## 🎯 OBJECTIVES

1. Set up memory profiling tools
2. Implement memory growth monitoring
3. Create memory leak detection scripts
4. Add memory usage alerts
5. Test memory leak scenarios
6. Document memory management practices

---

## 📊 CURRENT STATE

**Existing:**
- Basic memory monitoring in Prometheus
- No memory profiling
- No leak detection

**Gaps:**
- No memory profiling tools
- No leak detection
- No memory growth tracking
- Risk of memory leaks in production

---

## 🔧 IMPLEMENTATION

### 1. Memory Profiling Setup

Create `app/core/memory_profiler.py`:

```python
"""
Memory Profiling and Leak Detection

Tools for detecting and analyzing memory leaks.
"""
from __future__ import annotations

import gc
import logging
import psutil
import tracemalloc
from typing import Dict, List
from datetime import datetime
from collections import defaultdict

logger = logging.getLogger(__name__)


class MemoryProfiler:
    """Memory profiling and leak detection."""
    
    def __init__(self):
        self.enabled = False
        self.snapshots: List[tracemalloc.Snapshot] = []
        self.baseline_memory = None
        self.memory_history: List[Dict] = []
    
    def start(self):
        """Start memory profiling."""
        if not self.enabled:
            tracemalloc.start()
            self.enabled = True
            self.baseline_memory = self._get_current_memory()
            logger.info("Memory profiling started")
    
    def stop(self):
        """Stop memory profiling."""
        if self.enabled:
            tracemalloc.stop()
            self.enabled = False
            logger.info("Memory profiling stopped")
    
    def take_snapshot(self) -> tracemalloc.Snapshot:
        """
        Take memory snapshot.
        
        Returns:
            Memory snapshot
        """
        if not self.enabled:
            self.start()
        
        snapshot = tracemalloc.take_snapshot()
        self.snapshots.append(snapshot)
        
        # Record memory usage
        current_memory = self._get_current_memory()
        self.memory_history.append({
            "timestamp": datetime.now().isoformat(),
            "rss_mb": current_memory["rss_mb"],
            "vms_mb": current_memory["vms_mb"],
            "percent": current_memory["percent"]
        })
        
        logger.info(
            f"Memory snapshot taken: {current_memory['rss_mb']:.2f} MB RSS"
        )
        
        return snapshot
    
    def compare_snapshots(
        self,
        snapshot1: tracemalloc.Snapshot,
        snapshot2: tracemalloc.Snapshot,
        top_n: int = 10
    ) -> List[Dict]:
        """
        Compare two memory snapshots.
        
        Args:
            snapshot1: First snapshot
            snapshot2: Second snapshot
            top_n: Number of top differences to return
        
        Returns:
            List of memory differences
        """
        stats = snapshot2.compare_to(snapshot1, "lineno")
        
        differences = []
        for stat in stats[:top_n]:
            differences.append({
                "file": stat.traceback.format()[0] if stat.traceback else "unknown",
                "size_diff_mb": stat.size_diff / 1024 / 1024,
                "count_diff": stat.count_diff,
                "size_mb": stat.size / 1024 / 1024
            })
        
        return differences
    
    def detect_leaks(self, threshold_mb: float = 10.0) -> Dict:
        """
        Detect potential memory leaks.
        
        Args:
            threshold_mb: Memory growth threshold in MB
        
        Returns:
            Leak detection results
        """
        if len(self.snapshots) < 2:
            return {"status": "insufficient_data"}
        
        # Compare first and last snapshots
        first_snapshot = self.snapshots[0]
        last_snapshot = self.snapshots[-1]
        
        differences = self.compare_snapshots(first_snapshot, last_snapshot)
        
        # Calculate total growth
        total_growth = sum(d["size_diff_mb"] for d in differences)
        
        # Detect leak
        leak_detected = total_growth > threshold_mb
        
        result = {
            "status": "leak_detected" if leak_detected else "ok",
            "total_growth_mb": total_growth,
            "threshold_mb": threshold_mb,
            "top_differences": differences,
            "snapshots_analyzed": len(self.snapshots)
        }
        
        if leak_detected:
            logger.warning(
                f"Memory leak detected: {total_growth:.2f} MB growth",
                extra=result
            )
        
        return result
    
    def _get_current_memory(self) -> Dict:
        """Get current memory usage."""
        process = psutil.Process()
        memory_info = process.memory_info()
        
        return {
            "rss_mb": memory_info.rss / 1024 / 1024,
            "vms_mb": memory_info.vms / 1024 / 1024,
            "percent": process.memory_percent()
        }
    
    def get_memory_stats(self) -> Dict:
        """Get memory statistics."""
        current_memory = self._get_current_memory()
        
        # Calculate growth since baseline
        growth_mb = 0
        if self.baseline_memory:
            growth_mb = current_memory["rss_mb"] - self.baseline_memory["rss_mb"]
        
        return {
            "current": current_memory,
            "baseline": self.baseline_memory,
            "growth_mb": growth_mb,
            "snapshots_count": len(self.snapshots),
            "history": self.memory_history[-10:]  # Last 10 records
        }
    
    def force_garbage_collection(self) -> Dict:
        """
        Force garbage collection.
        
        Returns:
            GC statistics
        """
        before = self._get_current_memory()
        
        # Force GC
        collected = gc.collect()
        
        after = self._get_current_memory()
        freed_mb = before["rss_mb"] - after["rss_mb"]
        
        logger.info(
            f"Garbage collection: {collected} objects, {freed_mb:.2f} MB freed"
        )
        
        return {
            "objects_collected": collected,
            "memory_freed_mb": freed_mb,
            "before_mb": before["rss_mb"],
            "after_mb": after["rss_mb"]
        }


# Global memory profiler
memory_profiler = MemoryProfiler()
```

---

### 2. Memory Monitoring Middleware

Create `app/middleware/memory_monitor.py`:

```python
"""
Memory Monitoring Middleware

Track memory usage per request.
"""
from __future__ import annotations

import logging
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from app.core.memory_profiler import memory_profiler

logger = logging.getLogger(__name__)


class MemoryMonitorMiddleware(BaseHTTPMiddleware):
    """Middleware for memory monitoring."""
    
    def __init__(self, app, snapshot_interval: int = 100):
        super().__init__(app)
        self.request_count = 0
        self.snapshot_interval = snapshot_interval
    
    async def dispatch(
        self,
        request: Request,
        call_next: Callable
    ) -> Response:
        """Monitor memory usage."""
        
        # Take snapshot periodically
        self.request_count += 1
        if self.request_count % self.snapshot_interval == 0:
            memory_profiler.take_snapshot()
            
            # Check for leaks
            if len(memory_profiler.snapshots) >= 5:
                leak_result = memory_profiler.detect_leaks()
                if leak_result["status"] == "leak_detected":
                    logger.warning(
                        "Memory leak detected",
                        extra=leak_result
                    )
        
        response = await call_next(request)
        return response
```

---

### 3. Memory Monitoring Endpoints

Create `app/api/v1/endpoints/memory.py`:

```python
"""
Memory Monitoring Endpoints

Expose memory profiling data.
"""
from __future__ import annotations

from fastapi import APIRouter
from app.core.memory_profiler import memory_profiler

router = APIRouter()


@router.get("/memory/stats")
async def get_memory_stats():
    """Get current memory statistics."""
    return memory_profiler.get_memory_stats()


@router.post("/memory/snapshot")
async def take_memory_snapshot():
    """Take memory snapshot."""
    snapshot = memory_profiler.take_snapshot()
    return {"status": "snapshot_taken", "count": len(memory_profiler.snapshots)}


@router.get("/memory/leaks")
async def detect_memory_leaks(threshold_mb: float = 10.0):
    """Detect memory leaks."""
    return memory_profiler.detect_leaks(threshold_mb)


@router.post("/memory/gc")
async def force_garbage_collection():
    """Force garbage collection."""
    return memory_profiler.force_garbage_collection()
```

---

### 4. Memory Leak Detection Script

Create `scripts/monitoring/detect-memory-leaks.py`:

```python
#!/usr/bin/env python3
"""
Memory Leak Detection Script

Automated memory leak detection.
"""
import asyncio
import httpx
import time


async def monitor_memory():
    """Monitor memory usage over time."""
    client = httpx.AsyncClient()
    base_url = "http://localhost:8000/api/v1"
    
    print("🔍 Starting memory leak detection...")
    print("Taking snapshots every 60 seconds for 10 minutes...")
    
    # Take initial snapshot
    await client.post(f"{base_url}/memory/snapshot")
    
    # Monitor for 10 minutes
    for i in range(10):
        await asyncio.sleep(60)
        
        # Take snapshot
        await client.post(f"{base_url}/memory/snapshot")
        
        # Get stats
        stats = await client.get(f"{base_url}/memory/stats")
        data = stats.json()
        
        print(f"\n📊 Snapshot {i+1}/10:")
        print(f"  Memory: {data['current']['rss_mb']:.2f} MB")
        print(f"  Growth: {data['growth_mb']:.2f} MB")
    
    # Check for leaks
    leak_result = await client.get(f"{base_url}/memory/leaks")
    leak_data = leak_result.json()
    
    print("\n" + "="*50)
    print("🔍 Leak Detection Results:")
    print(f"  Status: {leak_data['status']}")
    print(f"  Total Growth: {leak_data['total_growth_mb']:.2f} MB")
    
    if leak_data['status'] == 'leak_detected':
        print("\n⚠️  MEMORY LEAK DETECTED!")
        print("\nTop Memory Consumers:")
        for diff in leak_data['top_differences'][:5]:
            print(f"  {diff['file']}: +{diff['size_diff_mb']:.2f} MB")
    else:
        print("\n✅ No memory leaks detected")
    
    await client.aclose()


if __name__ == "__main__":
    asyncio.run(monitor_memory())
```

---

## ✅ ACCEPTANCE CRITERIA

- [ ] Memory profiling implemented
- [ ] Memory snapshots working
- [ ] Leak detection functional
- [ ] Memory monitoring endpoints working
- [ ] Automated leak detection script created
- [ ] Memory alerts configured
- [ ] Documentation complete

---

## 🧪 TESTING

```python
# tests/test_memory_profiler.py
"""Tests for memory profiler."""
import pytest
from app.core.memory_profiler import memory_profiler


def test_memory_profiler_start():
    """Test starting memory profiler."""
    memory_profiler.start()
    assert memory_profiler.enabled is True


def test_take_snapshot():
    """Test taking memory snapshot."""
    memory_profiler.start()
    snapshot = memory_profiler.take_snapshot()
    assert snapshot is not None
    assert len(memory_profiler.snapshots) > 0


def test_detect_leaks():
    """Test leak detection."""
    memory_profiler.start()
    memory_profiler.take_snapshot()
    memory_profiler.take_snapshot()
    
    result = memory_profiler.detect_leaks()
    assert "status" in result
    assert "total_growth_mb" in result
```

---

## 📝 NOTES

- Run memory profiling in staging first
- Monitor memory growth over time
- Use garbage collection to free memory
- Profile memory-intensive operations
- Set up alerts for memory growth


