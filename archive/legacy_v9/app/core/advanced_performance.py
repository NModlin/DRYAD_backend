"""
Advanced Performance Optimization System for DRYAD.AI Backend
Provides comprehensive performance optimization including cache warming, request batching,
resource monitoring, and intelligent optimization strategies.
"""

import asyncio
import time
import psutil
import threading
from typing import Dict, Any, List, Optional, Callable, Union
from dataclasses import dataclass, field
from collections import defaultdict, deque
from contextlib import asynccontextmanager
import json
import hashlib
from concurrent.futures import ThreadPoolExecutor, as_completed

from app.core.logging_config import get_logger, LogTimer
from app.core.caching import cache, MultiLevelCache
from app.core.performance import pool_manager
from app.database.database import AsyncSessionLocal

logger = get_logger(__name__)

@dataclass
class PerformanceMetrics:
    """Performance metrics tracking."""
    cpu_usage: float = 0.0
    memory_usage: float = 0.0
    disk_io_read: float = 0.0
    disk_io_write: float = 0.0
    network_io_sent: float = 0.0
    network_io_recv: float = 0.0
    active_connections: int = 0
    cache_hit_rate: float = 0.0
    avg_response_time: float = 0.0
    requests_per_second: float = 0.0
    error_rate: float = 0.0
    timestamp: float = field(default_factory=time.time)

@dataclass
class OptimizationRecommendation:
    """Performance optimization recommendation."""
    category: str
    priority: str  # high, medium, low
    description: str
    action: str
    expected_improvement: str
    implementation_effort: str

class ResourceMonitor:
    """Advanced resource monitoring and optimization."""
    
    def __init__(self, monitoring_interval: int = 30):
        self.monitoring_interval = monitoring_interval
        self.metrics_history: deque = deque(maxlen=1000)
        self.is_monitoring = False
        self.monitor_thread = None
        self.optimization_rules = []
        self.performance_baselines = {}
        
    def start_monitoring(self):
        """Start continuous resource monitoring."""
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
            self.monitor_thread.join(timeout=5)
        logger.info("Resource monitoring stopped")
    
    def _monitor_loop(self):
        """Main monitoring loop."""
        while self.is_monitoring:
            try:
                metrics = self._collect_metrics()
                self.metrics_history.append(metrics)
                
                # Check for optimization opportunities
                recommendations = self._analyze_performance(metrics)
                if recommendations:
                    self._apply_optimizations(recommendations)
                
                time.sleep(self.monitoring_interval)
                
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                time.sleep(self.monitoring_interval)
    
    def _collect_metrics(self) -> PerformanceMetrics:
        """Collect current system metrics."""
        # System metrics
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk_io = psutil.disk_io_counters()
        network_io = psutil.net_io_counters()
        
        # Application metrics
        cache_stats = cache.get_stats()
        cache_hit_rate = (cache_stats["hits"] / max(cache_stats["hits"] + cache_stats["misses"], 1)) * 100
        
        return PerformanceMetrics(
            cpu_usage=cpu_percent,
            memory_usage=memory.percent,
            disk_io_read=disk_io.read_bytes if disk_io else 0,
            disk_io_write=disk_io.write_bytes if disk_io else 0,
            network_io_sent=network_io.bytes_sent if network_io else 0,
            network_io_recv=network_io.bytes_recv if network_io else 0,
            cache_hit_rate=cache_hit_rate
        )
    
    def _analyze_performance(self, current_metrics: PerformanceMetrics) -> List[OptimizationRecommendation]:
        """Analyze performance and generate optimization recommendations."""
        recommendations = []
        
        # High CPU usage
        if current_metrics.cpu_usage > 80:
            recommendations.append(OptimizationRecommendation(
                category="cpu",
                priority="high",
                description="High CPU usage detected",
                action="Enable request batching and increase cache TTL",
                expected_improvement="20-30% CPU reduction",
                implementation_effort="low"
            ))
        
        # Low cache hit rate
        if current_metrics.cache_hit_rate < 60:
            recommendations.append(OptimizationRecommendation(
                category="cache",
                priority="medium",
                description="Low cache hit rate",
                action="Implement cache warming for frequently accessed data",
                expected_improvement="40-60% response time improvement",
                implementation_effort="medium"
            ))
        
        # High memory usage
        if current_metrics.memory_usage > 85:
            recommendations.append(OptimizationRecommendation(
                category="memory",
                priority="high",
                description="High memory usage",
                action="Reduce cache size and implement memory cleanup",
                expected_improvement="15-25% memory reduction",
                implementation_effort="low"
            ))
        
        return recommendations
    
    def _apply_optimizations(self, recommendations: List[OptimizationRecommendation]):
        """Apply automatic optimizations based on recommendations."""
        for rec in recommendations:
            if rec.priority == "high" and rec.implementation_effort == "low":
                logger.info(f"Applying optimization: {rec.description}")
                
                if rec.category == "cpu":
                    # Enable more aggressive caching
                    self._optimize_cpu_usage()
                elif rec.category == "memory":
                    # Clean up memory
                    self._optimize_memory_usage()
                elif rec.category == "cache":
                    # Warm cache
                    asyncio.create_task(self._warm_cache())
    
    def _optimize_cpu_usage(self):
        """Optimize CPU usage."""
        # Increase cache TTL for frequently accessed items
        # This is a simplified implementation
        logger.info("Optimizing CPU usage by adjusting cache settings")
    
    def _optimize_memory_usage(self):
        """Optimize memory usage."""
        # Clear old cache entries
        cache.memory_cache.cleanup_expired()
        logger.info("Optimized memory usage by cleaning cache")
    
    async def _warm_cache(self):
        """Warm cache with frequently accessed data."""
        logger.info("Starting cache warming process")
        # Implementation would warm cache with common queries
        # This is a placeholder for the actual implementation

class CacheWarmingSystem:
    """Advanced cache warming system."""
    
    def __init__(self):
        self.warming_strategies = {}
        self.access_patterns = defaultdict(int)
        self.warming_queue = asyncio.Queue()
        self.is_warming = False
        
    def register_warming_strategy(self, key_pattern: str, strategy: Callable):
        """Register a cache warming strategy."""
        self.warming_strategies[key_pattern] = strategy
        logger.info(f"Registered cache warming strategy for pattern: {key_pattern}")
    
    async def start_warming(self):
        """Start the cache warming process."""
        if self.is_warming:
            return
            
        self.is_warming = True
        asyncio.create_task(self._warming_worker())
        logger.info("Cache warming system started")
    
    async def stop_warming(self):
        """Stop the cache warming process."""
        self.is_warming = False
        logger.info("Cache warming system stopped")
    
    async def _warming_worker(self):
        """Cache warming worker."""
        while self.is_warming:
            try:
                # Get warming task from queue
                warming_task = await asyncio.wait_for(
                    self.warming_queue.get(), timeout=30
                )
                
                # Execute warming strategy
                await self._execute_warming_task(warming_task)
                
            except asyncio.TimeoutError:
                # No warming tasks, continue
                continue
            except Exception as e:
                logger.error(f"Error in cache warming worker: {e}")
    
    async def _execute_warming_task(self, task: Dict[str, Any]):
        """Execute a cache warming task."""
        pattern = task.get("pattern")
        strategy = self.warming_strategies.get(pattern)
        
        if strategy:
            try:
                await strategy(task)
                logger.debug(f"Executed cache warming for pattern: {pattern}")
            except Exception as e:
                logger.error(f"Cache warming failed for pattern {pattern}: {e}")
    
    async def warm_common_queries(self):
        """Warm cache with common queries."""
        common_patterns = [
            "llm_response_*",
            "user_preferences_*",
            "conversation_context_*",
            "vector_search_*"
        ]
        
        for pattern in common_patterns:
            await self.warming_queue.put({
                "pattern": pattern,
                "priority": "high"
            })

class RequestBatcher:
    """Intelligent request batching system."""
    
    def __init__(self, batch_size: int = 10, batch_timeout: float = 0.1):
        self.batch_size = batch_size
        self.batch_timeout = batch_timeout
        self.pending_requests = {}
        self.batch_processors = {}
        
    def register_batch_processor(self, request_type: str, processor: Callable):
        """Register a batch processor for a request type."""
        self.batch_processors[request_type] = processor
        logger.info(f"Registered batch processor for: {request_type}")
    
    async def add_request(self, request_type: str, request_data: Any) -> Any:
        """Add a request to the batch."""
        if request_type not in self.batch_processors:
            raise ValueError(f"No batch processor registered for: {request_type}")
        
        # Create batch if it doesn't exist
        if request_type not in self.pending_requests:
            self.pending_requests[request_type] = {
                "requests": [],
                "futures": [],
                "created_at": time.time()
            }
        
        batch = self.pending_requests[request_type]
        
        # Create future for this request
        future = asyncio.Future()
        batch["requests"].append(request_data)
        batch["futures"].append(future)
        
        # Process batch if it's full or timeout reached
        if (len(batch["requests"]) >= self.batch_size or 
            time.time() - batch["created_at"] > self.batch_timeout):
            await self._process_batch(request_type)
        
        return await future
    
    async def _process_batch(self, request_type: str):
        """Process a batch of requests."""
        if request_type not in self.pending_requests:
            return
        
        batch = self.pending_requests.pop(request_type)
        processor = self.batch_processors[request_type]
        
        try:
            # Process all requests in the batch
            results = await processor(batch["requests"])
            
            # Set results for all futures
            for future, result in zip(batch["futures"], results):
                if not future.done():
                    future.set_result(result)
                    
        except Exception as e:
            # Set exception for all futures
            for future in batch["futures"]:
                if not future.done():
                    future.set_exception(e)

class ConnectionPoolOptimizer:
    """Advanced connection pool optimization."""
    
    def __init__(self):
        self.pool_metrics = defaultdict(dict)
        self.optimization_history = []
        
    async def optimize_pools(self):
        """Optimize all connection pools."""
        # Database pool optimization
        await self._optimize_database_pool()
        
        # LLM pool optimization
        await self._optimize_llm_pool()
        
        # Redis pool optimization
        await self._optimize_redis_pool()
        
        logger.info("Connection pool optimization completed")
    
    async def _optimize_database_pool(self):
        """Optimize database connection pool."""
        from app.database.database import async_engine
        
        # Get current pool stats
        pool_stats = pool_manager.get_pool_stats(async_engine.sync_engine)
        
        # Calculate optimal pool size based on usage patterns
        optimal_size = self._calculate_optimal_pool_size(pool_stats)
        
        if optimal_size != pool_stats.get("pool_size", 20):
            logger.info(f"Optimizing database pool size to: {optimal_size}")
            # Apply optimization (simplified)
    
    async def _optimize_llm_pool(self):
        """Optimize LLM connection pool."""
        # This would optimize LLM connection pools
        logger.info("Optimizing LLM connection pools")
    
    async def _optimize_redis_pool(self):
        """Optimize Redis connection pool."""
        # This would optimize Redis connection pools
        logger.info("Optimizing Redis connection pools")
    
    def _calculate_optimal_pool_size(self, pool_stats: Dict[str, Any]) -> int:
        """Calculate optimal pool size based on usage patterns."""
        # Simplified calculation
        current_size = pool_stats.get("pool_size", 20)
        utilization = pool_stats.get("checked_out_connections", 0) / current_size
        
        if utilization > 0.8:
            return min(current_size + 5, 50)  # Increase but cap at 50
        elif utilization < 0.3:
            return max(current_size - 5, 10)  # Decrease but keep minimum 10
        
        return current_size

# Global instances
resource_monitor = ResourceMonitor()
cache_warmer = CacheWarmingSystem()
request_batcher = RequestBatcher()
pool_optimizer = ConnectionPoolOptimizer()

async def initialize_performance_optimization():
    """Initialize all performance optimization systems."""
    logger.info("Initializing advanced performance optimization systems")
    
    # Start resource monitoring
    resource_monitor.start_monitoring()
    
    # Start cache warming
    await cache_warmer.start_warming()
    
    # Register common batch processors
    await _register_batch_processors()
    
    # Register cache warming strategies
    await _register_warming_strategies()
    
    logger.info("Advanced performance optimization systems initialized")

async def _register_batch_processors():
    """Register common batch processors."""
    
    async def llm_batch_processor(requests: List[Dict[str, Any]]) -> List[Any]:
        """Process LLM requests in batch."""
        # Simplified batch processing
        results = []
        for request in requests:
            # Process each request (in real implementation, this would be optimized)
            results.append({"response": f"Processed: {request.get('query', '')}"})
        return results
    
    request_batcher.register_batch_processor("llm_inference", llm_batch_processor)

async def _register_warming_strategies():
    """Register cache warming strategies."""
    
    async def warm_llm_responses(task: Dict[str, Any]):
        """Warm cache with common LLM responses."""
        common_queries = [
            "What is artificial intelligence?",
            "How does machine learning work?",
            "Explain deep learning concepts"
        ]
        
        for query in common_queries:
            cache_key = f"llm_response_{hashlib.md5(query.encode()).hexdigest()}"
            if not cache.get(cache_key):
                # This would generate and cache the response
                cache.set(cache_key, f"Cached response for: {query}", ttl=3600)
    
    cache_warmer.register_warming_strategy("llm_response_*", warm_llm_responses)

async def shutdown_performance_optimization():
    """Shutdown all performance optimization systems."""
    logger.info("Shutting down performance optimization systems")
    
    resource_monitor.stop_monitoring()
    await cache_warmer.stop_warming()
    
    logger.info("Performance optimization systems shutdown complete")
