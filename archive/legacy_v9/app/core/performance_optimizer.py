#!/usr/bin/env python3
"""
DRYAD.AI Performance Optimizer

CPU optimization, memory management, request queuing, and concurrent inference
handling for local LLM systems.
"""

import os
import psutil
import threading
import time
import logging
import asyncio
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from queue import Queue, PriorityQueue
from concurrent.futures import ThreadPoolExecutor, Future
import gc
import platform

# Platform-specific imports
try:
    import resource
    HAS_RESOURCE = True
except ImportError:
    # resource module is not available on Windows
    HAS_RESOURCE = False
    resource = None

logger = logging.getLogger(__name__)

@dataclass
class PerformanceMetrics:
    """Performance metrics for monitoring."""
    timestamp: str
    cpu_usage_percent: float
    memory_usage_gb: float
    memory_available_gb: float
    active_requests: int
    queue_size: int
    avg_response_time: float
    tokens_per_second: float
    cache_hit_rate: float
    model_load_time: float

@dataclass
class RequestMetrics:
    """Metrics for individual requests."""
    request_id: str
    start_time: float
    end_time: Optional[float] = None
    tokens_generated: int = 0
    priority: int = 1
    model_used: str = ""
    cache_hit: bool = False

class ResourceMonitor:
    """Monitor system resources and performance."""
    
    def __init__(self, monitoring_interval: float = 1.0):
        self.monitoring_interval = monitoring_interval
        self.metrics_history: List[PerformanceMetrics] = []
        self.max_history_size = 1000
        self.is_monitoring = False
        self.monitor_thread: Optional[threading.Thread] = None
        self.lock = threading.RLock()
    
    def start_monitoring(self):
        """Start resource monitoring."""
        if self.is_monitoring:
            return
        
        self.is_monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        logger.info("Resource monitoring started")
    
    def stop_monitoring(self):
        """Stop resource monitoring."""
        self.is_monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=2.0)
        logger.info("Resource monitoring stopped")
    
    def _monitor_loop(self):
        """Main monitoring loop."""
        while self.is_monitoring:
            try:
                metrics = self._collect_metrics()
                
                with self.lock:
                    self.metrics_history.append(metrics)
                    # Keep only recent metrics
                    if len(self.metrics_history) > self.max_history_size:
                        self.metrics_history = self.metrics_history[-self.max_history_size:]
                
                time.sleep(self.monitoring_interval)
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                time.sleep(self.monitoring_interval)
    
    def _collect_metrics(self) -> PerformanceMetrics:
        """Collect current system metrics."""
        # CPU usage
        cpu_usage = psutil.cpu_percent(interval=0.1)
        
        # Memory usage
        memory = psutil.virtual_memory()
        memory_usage_gb = (memory.total - memory.available) / (1024**3)
        memory_available_gb = memory.available / (1024**3)
        
        # Get metrics from performance optimizer if available
        active_requests = 0
        queue_size = 0
        avg_response_time = 0.0
        tokens_per_second = 0.0
        cache_hit_rate = 0.0
        model_load_time = 0.0
        
        # Try to get metrics from global optimizer
        try:
            from app.core.performance_optimizer import performance_optimizer
            if hasattr(performance_optimizer, 'get_current_metrics'):
                opt_metrics = performance_optimizer.get_current_metrics()
                active_requests = opt_metrics.get('active_requests', 0)
                queue_size = opt_metrics.get('queue_size', 0)
                avg_response_time = opt_metrics.get('avg_response_time', 0.0)
                tokens_per_second = opt_metrics.get('tokens_per_second', 0.0)
                cache_hit_rate = opt_metrics.get('cache_hit_rate', 0.0)
                model_load_time = opt_metrics.get('model_load_time', 0.0)
        except:
            pass
        
        return PerformanceMetrics(
            timestamp=datetime.now().isoformat(),
            cpu_usage_percent=cpu_usage,
            memory_usage_gb=memory_usage_gb,
            memory_available_gb=memory_available_gb,
            active_requests=active_requests,
            queue_size=queue_size,
            avg_response_time=avg_response_time,
            tokens_per_second=tokens_per_second,
            cache_hit_rate=cache_hit_rate,
            model_load_time=model_load_time
        )
    
    def get_recent_metrics(self, minutes: int = 5) -> List[PerformanceMetrics]:
        """Get metrics from the last N minutes."""
        cutoff_time = datetime.now() - timedelta(minutes=minutes)
        
        with self.lock:
            recent_metrics = []
            for metric in reversed(self.metrics_history):
                metric_time = datetime.fromisoformat(metric.timestamp)
                if metric_time >= cutoff_time:
                    recent_metrics.append(metric)
                else:
                    break
            
            return list(reversed(recent_metrics))
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get performance summary statistics."""
        recent_metrics = self.get_recent_metrics(5)
        
        if not recent_metrics:
            return {"status": "no_data"}
        
        # Calculate averages
        avg_cpu = sum(m.cpu_usage_percent for m in recent_metrics) / len(recent_metrics)
        avg_memory = sum(m.memory_usage_gb for m in recent_metrics) / len(recent_metrics)
        avg_response_time = sum(m.avg_response_time for m in recent_metrics) / len(recent_metrics)
        avg_tokens_per_sec = sum(m.tokens_per_second for m in recent_metrics) / len(recent_metrics)
        
        # Get current values
        current = recent_metrics[-1]
        
        return {
            "status": "active",
            "current": {
                "cpu_usage_percent": current.cpu_usage_percent,
                "memory_usage_gb": current.memory_usage_gb,
                "memory_available_gb": current.memory_available_gb,
                "active_requests": current.active_requests,
                "queue_size": current.queue_size
            },
            "averages_5min": {
                "cpu_usage_percent": avg_cpu,
                "memory_usage_gb": avg_memory,
                "avg_response_time": avg_response_time,
                "tokens_per_second": avg_tokens_per_sec
            },
            "metrics_count": len(recent_metrics),
            "monitoring_since": recent_metrics[0].timestamp if recent_metrics else None
        }

class RequestQueue:
    """Priority-based request queue with resource management."""
    
    def __init__(self, max_concurrent: int = None):
        self.max_concurrent = max_concurrent or min(os.cpu_count() or 4, 4)
        self.queue = PriorityQueue()
        self.active_requests: Dict[str, RequestMetrics] = {}
        self.completed_requests: List[RequestMetrics] = []
        self.executor = ThreadPoolExecutor(max_workers=self.max_concurrent)
        self.lock = threading.RLock()
        
        logger.info(f"Request queue initialized with max_concurrent={self.max_concurrent}")
    
    def submit_request(self, 
                      func: Callable, 
                      args: tuple = (), 
                      kwargs: dict = None, 
                      priority: int = 1,
                      request_id: str = None) -> Future:
        """Submit a request to the queue."""
        if kwargs is None:
            kwargs = {}
        
        if request_id is None:
            request_id = f"req_{int(time.time() * 1000)}"
        
        # Create request metrics
        request_metrics = RequestMetrics(
            request_id=request_id,
            start_time=time.time(),
            priority=priority
        )
        
        with self.lock:
            self.active_requests[request_id] = request_metrics
        
        # Wrap function to track completion
        def wrapped_func(*args, **kwargs):
            try:
                result = func(*args, **kwargs)
                
                # Update metrics
                with self.lock:
                    if request_id in self.active_requests:
                        metrics = self.active_requests[request_id]
                        metrics.end_time = time.time()
                        
                        # Try to extract token count from result
                        if hasattr(result, 'content'):
                            metrics.tokens_generated = len(str(result.content).split())
                        elif isinstance(result, str):
                            metrics.tokens_generated = len(result.split())
                        
                        # Move to completed
                        self.completed_requests.append(metrics)
                        del self.active_requests[request_id]
                        
                        # Keep only recent completed requests
                        if len(self.completed_requests) > 100:
                            self.completed_requests = self.completed_requests[-100:]
                
                return result
            except Exception as e:
                # Handle error
                with self.lock:
                    if request_id in self.active_requests:
                        metrics = self.active_requests[request_id]
                        metrics.end_time = time.time()
                        self.completed_requests.append(metrics)
                        del self.active_requests[request_id]
                raise
        
        # Submit to executor
        future = self.executor.submit(wrapped_func, *args, **kwargs)
        return future
    
    def get_queue_status(self) -> Dict[str, Any]:
        """Get current queue status."""
        with self.lock:
            active_count = len(self.active_requests)
            completed_count = len(self.completed_requests)
            
            # Calculate average response time
            avg_response_time = 0.0
            if self.completed_requests:
                total_time = sum(
                    (req.end_time or req.start_time) - req.start_time 
                    for req in self.completed_requests[-20:]  # Last 20 requests
                )
                avg_response_time = total_time / min(len(self.completed_requests), 20)
            
            return {
                "active_requests": active_count,
                "completed_requests": completed_count,
                "max_concurrent": self.max_concurrent,
                "avg_response_time": avg_response_time,
                "queue_utilization": active_count / self.max_concurrent
            }

class MemoryManager:
    """Manage memory usage and garbage collection."""
    
    def __init__(self, max_memory_gb: float = None):
        self.max_memory_gb = max_memory_gb or (psutil.virtual_memory().total / (1024**3) * 0.8)
        self.gc_threshold = 0.85  # Trigger GC at 85% of max memory
        self.last_gc_time = time.time()
        self.gc_interval = 30  # Minimum seconds between GC
        
        logger.info(f"Memory manager initialized with max_memory={self.max_memory_gb:.2f} GB")
    
    def check_memory_usage(self) -> Dict[str, Any]:
        """Check current memory usage and trigger GC if needed."""
        memory = psutil.virtual_memory()
        current_usage_gb = (memory.total - memory.available) / (1024**3)
        usage_ratio = current_usage_gb / self.max_memory_gb
        
        status = {
            "current_usage_gb": current_usage_gb,
            "max_memory_gb": self.max_memory_gb,
            "usage_ratio": usage_ratio,
            "gc_triggered": False
        }
        
        # Trigger garbage collection if needed
        if (usage_ratio > self.gc_threshold and 
            time.time() - self.last_gc_time > self.gc_interval):
            
            logger.info(f"Memory usage high ({usage_ratio:.1%}), triggering garbage collection")
            
            # Force garbage collection
            collected = gc.collect()
            self.last_gc_time = time.time()
            
            status["gc_triggered"] = True
            status["objects_collected"] = collected
            
            # Check memory after GC
            memory_after = psutil.virtual_memory()
            usage_after_gb = (memory_after.total - memory_after.available) / (1024**3)
            status["usage_after_gc_gb"] = usage_after_gb
            status["memory_freed_gb"] = current_usage_gb - usage_after_gb
        
        return status
    
    def optimize_memory(self):
        """Perform memory optimization."""
        # Force garbage collection
        gc.collect()
        
        # Try to reduce memory fragmentation (Python-specific)
        try:
            import ctypes
            libc = ctypes.CDLL("libc.so.6")
            libc.malloc_trim(0)
        except:
            pass  # Not available on all systems

class CPUOptimizer:
    """Optimize CPU usage for local LLM inference."""

    def __init__(self):
        self.cpu_count = os.cpu_count() or 4
        self.optimal_threads = self._calculate_optimal_threads()
        self.process = psutil.Process()

        logger.info(f"CPU optimizer initialized: {self.cpu_count} cores, {self.optimal_threads} optimal threads")

    def _calculate_optimal_threads(self) -> int:
        """Calculate optimal thread count for LLM inference."""
        # For CPU-only inference, use 75% of available cores
        # Leave some cores for system processes
        optimal = max(1, int(self.cpu_count * 0.75))
        return min(optimal, 8)  # Cap at 8 threads for most models

    def set_cpu_affinity(self, core_list: List[int] = None):
        """Set CPU affinity for the current process."""
        try:
            if core_list is None:
                # Use all available cores
                core_list = list(range(self.cpu_count))

            self.process.cpu_affinity(core_list)
            logger.info(f"CPU affinity set to cores: {core_list}")
        except Exception as e:
            logger.warning(f"Could not set CPU affinity: {e}")

    def optimize_process_priority(self):
        """Optimize process priority for better performance."""
        try:
            # Set higher priority for better responsiveness
            if os.name == 'nt':  # Windows
                self.process.nice(psutil.HIGH_PRIORITY_CLASS)
            else:  # Unix-like
                self.process.nice(-5)  # Higher priority

            logger.info("Process priority optimized")
        except Exception as e:
            logger.warning(f"Could not optimize process priority: {e}")

    def get_cpu_metrics(self) -> Dict[str, Any]:
        """Get CPU performance metrics."""
        return {
            "cpu_count": self.cpu_count,
            "optimal_threads": self.optimal_threads,
            "current_cpu_percent": psutil.cpu_percent(interval=0.1),
            "per_cpu_percent": psutil.cpu_percent(interval=0.1, percpu=True),
            "load_average": os.getloadavg() if hasattr(os, 'getloadavg') else None,
            "process_cpu_percent": self.process.cpu_percent(),
            "process_memory_mb": self.process.memory_info().rss / (1024**2)
        }

class ResponseCache:
    """Cache responses to improve performance."""

    def __init__(self, max_size: int = 1000, ttl_seconds: int = 3600):
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.access_times: Dict[str, float] = {}
        self.lock = threading.RLock()

        logger.info(f"Response cache initialized: max_size={max_size}, ttl={ttl_seconds}s")

    def _generate_cache_key(self, prompt: str, model: str, temperature: float) -> str:
        """Generate cache key for a request."""
        import hashlib
        key_data = f"{prompt}|{model}|{temperature}"
        return hashlib.md5(key_data.encode()).hexdigest()

    def get(self, prompt: str, model: str = "", temperature: float = 0.7) -> Optional[str]:
        """Get cached response if available."""
        cache_key = self._generate_cache_key(prompt, model, temperature)

        with self.lock:
            if cache_key in self.cache:
                entry = self.cache[cache_key]

                # Check TTL
                if time.time() - entry['timestamp'] < self.ttl_seconds:
                    self.access_times[cache_key] = time.time()
                    logger.debug(f"Cache hit for key: {cache_key[:16]}...")
                    return entry['response']
                else:
                    # Expired, remove
                    del self.cache[cache_key]
                    del self.access_times[cache_key]

        return None

    def put(self, prompt: str, response: str, model: str = "", temperature: float = 0.7):
        """Cache a response."""
        cache_key = self._generate_cache_key(prompt, model, temperature)

        with self.lock:
            # Clean up if at max size
            if len(self.cache) >= self.max_size:
                self._evict_oldest()

            self.cache[cache_key] = {
                'response': response,
                'timestamp': time.time(),
                'model': model,
                'temperature': temperature
            }
            self.access_times[cache_key] = time.time()

            logger.debug(f"Cached response for key: {cache_key[:16]}...")

    def _evict_oldest(self):
        """Evict the oldest cache entry."""
        if not self.access_times:
            return

        oldest_key = min(self.access_times.keys(), key=lambda k: self.access_times[k])
        del self.cache[oldest_key]
        del self.access_times[oldest_key]
        logger.debug(f"Evicted cache entry: {oldest_key[:16]}...")

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        with self.lock:
            return {
                "size": len(self.cache),
                "max_size": self.max_size,
                "utilization": len(self.cache) / self.max_size,
                "ttl_seconds": self.ttl_seconds
            }

    def clear(self):
        """Clear the cache."""
        with self.lock:
            self.cache.clear()
            self.access_times.clear()
            logger.info("Response cache cleared")

class PerformanceOptimizer:
    """Main performance optimization coordinator."""

    def __init__(self):
        self.resource_monitor = ResourceMonitor()
        self.request_queue = RequestQueue()
        self.memory_manager = MemoryManager()
        self.cpu_optimizer = CPUOptimizer()
        self.response_cache = ResponseCache()

        self.is_initialized = False
        self.optimization_enabled = True

        logger.info("Performance optimizer initialized")

    def initialize(self):
        """Initialize all optimization components."""
        if self.is_initialized:
            return

        try:
            # Start monitoring
            self.resource_monitor.start_monitoring()

            # Optimize CPU settings
            self.cpu_optimizer.optimize_process_priority()

            self.is_initialized = True
            logger.info("✅ Performance optimization initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize performance optimization: {e}")

    def shutdown(self):
        """Shutdown optimization components."""
        self.resource_monitor.stop_monitoring()
        self.request_queue.executor.shutdown(wait=True)
        logger.info("Performance optimizer shutdown complete")

    def optimize_request(self, func: Callable, *args, **kwargs) -> Future:
        """Optimize and execute a request."""
        if not self.optimization_enabled:
            # Direct execution without optimization
            future = Future()
            try:
                result = func(*args, **kwargs)
                future.set_result(result)
            except Exception as e:
                future.set_exception(e)
            return future

        # Check memory before processing
        memory_status = self.memory_manager.check_memory_usage()
        if memory_status.get('gc_triggered'):
            logger.info("Memory optimization triggered during request")

        # Submit to optimized queue
        return self.request_queue.submit_request(func, args, kwargs)

    def get_current_metrics(self) -> Dict[str, Any]:
        """Get current performance metrics."""
        queue_status = self.request_queue.get_queue_status()
        memory_status = self.memory_manager.check_memory_usage()
        cpu_metrics = self.cpu_optimizer.get_cpu_metrics()
        cache_stats = self.response_cache.get_cache_stats()

        return {
            "active_requests": queue_status["active_requests"],
            "queue_size": 0,  # PriorityQueue doesn't expose size easily
            "avg_response_time": queue_status["avg_response_time"],
            "tokens_per_second": 0.0,  # Would need to be calculated from request metrics
            "cache_hit_rate": 0.0,  # Would need hit/miss tracking
            "model_load_time": 0.0,  # Would need to be tracked separately
            "memory_usage_gb": memory_status["current_usage_gb"],
            "cpu_usage_percent": cpu_metrics["current_cpu_percent"],
            "cache_utilization": cache_stats["utilization"]
        }

    def get_performance_report(self) -> Dict[str, Any]:
        """Get comprehensive performance report."""
        return {
            "status": "active" if self.is_initialized else "inactive",
            "optimization_enabled": self.optimization_enabled,
            "resource_monitor": self.resource_monitor.get_performance_summary(),
            "request_queue": self.request_queue.get_queue_status(),
            "memory_manager": self.memory_manager.check_memory_usage(),
            "cpu_optimizer": self.cpu_optimizer.get_cpu_metrics(),
            "response_cache": self.response_cache.get_cache_stats(),
            "timestamp": datetime.now().isoformat()
        }

# Global performance optimizer instance
performance_optimizer = PerformanceOptimizer()
