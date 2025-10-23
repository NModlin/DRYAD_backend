#!/usr/bin/env python3
"""
DRYAD.AI Monitoring Integration

Integrates monitoring with LLM and agent systems to provide comprehensive
observability and performance tracking.
"""

import time
import logging
import functools
from typing import Dict, Any, Optional, Callable
from contextlib import contextmanager
import threading

from app.core.monitoring import metrics_collector

logger = logging.getLogger(__name__)

class MonitoringIntegration:
    """Integration layer for monitoring AI system components."""
    
    def __init__(self):
        self.active_operations: Dict[str, Dict[str, Any]] = {}
        self.lock = threading.RLock()
        
        logger.info("Monitoring integration initialized")
    
    @contextmanager
    def monitor_llm_request(self, model_name: str = "", prompt_length: int = 0):
        """Context manager for monitoring LLM requests."""
        request_id = f"llm_{int(time.time() * 1000000)}"
        start_time = time.time()
        
        # Record request start
        metrics_collector.ai_monitor.record_llm_request(True, 0, 0, model_name)
        
        with self.lock:
            self.active_operations[request_id] = {
                "type": "llm_request",
                "model": model_name,
                "start_time": start_time,
                "prompt_length": prompt_length
            }
        
        try:
            yield request_id
            # Success case
            duration = time.time() - start_time
            metrics_collector.ai_monitor.record_llm_request(True, duration, 0, model_name)
            
        except Exception as e:
            # Error case
            duration = time.time() - start_time
            metrics_collector.ai_monitor.record_llm_request(False, duration, 0, model_name)
            raise
        finally:
            with self.lock:
                self.active_operations.pop(request_id, None)
    
    @contextmanager
    def monitor_agent_workflow(self, workflow_type: str = "", agents: list = None):
        """Context manager for monitoring agent workflows."""
        workflow_id = f"workflow_{int(time.time() * 1000000)}"
        start_time = time.time()
        
        with self.lock:
            self.active_operations[workflow_id] = {
                "type": "agent_workflow",
                "workflow_type": workflow_type,
                "agents": agents or [],
                "start_time": start_time
            }
        
        try:
            yield workflow_id
            # Success case
            duration = time.time() - start_time
            metrics_collector.ai_monitor.record_agent_workflow(True, duration, workflow_type)
            
        except Exception as e:
            # Error case
            duration = time.time() - start_time
            metrics_collector.ai_monitor.record_agent_workflow(False, duration, workflow_type)
            raise
        finally:
            with self.lock:
                self.active_operations.pop(workflow_id, None)
    
    def record_model_load(self, model_name: str, load_time: float, memory_usage: float):
        """Record model loading metrics."""
        metrics_collector.ai_monitor.record_model_load(load_time, memory_usage, model_name)
        logger.info(f"Model {model_name} loaded in {load_time:.2f}s, using {memory_usage:.2f}MB")
    
    def get_active_operations(self) -> Dict[str, Any]:
        """Get currently active operations."""
        with self.lock:
            return {
                "total_active": len(self.active_operations),
                "by_type": {
                    "llm_requests": len([op for op in self.active_operations.values() 
                                       if op["type"] == "llm_request"]),
                    "agent_workflows": len([op for op in self.active_operations.values() 
                                          if op["type"] == "agent_workflow"])
                },
                "operations": dict(self.active_operations)
            }

# Global monitoring integration instance
monitoring_integration = MonitoringIntegration()

def monitor_llm_call(model_name: str = ""):
    """Decorator for monitoring LLM function calls."""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Try to extract prompt length from arguments
            prompt_length = 0
            if args and isinstance(args[0], str):
                prompt_length = len(args[0])
            elif 'prompt' in kwargs and isinstance(kwargs['prompt'], str):
                prompt_length = len(kwargs['prompt'])
            
            with monitoring_integration.monitor_llm_request(model_name, prompt_length):
                return func(*args, **kwargs)
        
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            # Try to extract prompt length from arguments
            prompt_length = 0
            if args and isinstance(args[0], str):
                prompt_length = len(args[0])
            elif 'prompt' in kwargs and isinstance(kwargs['prompt'], str):
                prompt_length = len(kwargs['prompt'])
            
            with monitoring_integration.monitor_llm_request(model_name, prompt_length):
                return await func(*args, **kwargs)
        
        # Return appropriate wrapper based on function type
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return wrapper
    
    return decorator

def monitor_agent_workflow(workflow_type: str = "", agents: list = None):
    """Decorator for monitoring agent workflow function calls."""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            with monitoring_integration.monitor_agent_workflow(workflow_type, agents):
                return func(*args, **kwargs)
        
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            with monitoring_integration.monitor_agent_workflow(workflow_type, agents):
                return await func(*args, **kwargs)
        
        # Return appropriate wrapper based on function type
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return wrapper
    
    return decorator

class PerformanceTracker:
    """Track performance metrics for AI operations."""
    
    def __init__(self):
        self.operation_times: Dict[str, list] = {}
        self.lock = threading.RLock()
    
    def record_operation_time(self, operation_name: str, duration: float):
        """Record the duration of an operation."""
        with self.lock:
            if operation_name not in self.operation_times:
                self.operation_times[operation_name] = []
            
            self.operation_times[operation_name].append(duration)
            
            # Keep only recent measurements (last 100)
            if len(self.operation_times[operation_name]) > 100:
                self.operation_times[operation_name] = self.operation_times[operation_name][-100:]
    
    def get_operation_stats(self, operation_name: str) -> Dict[str, float]:
        """Get statistics for an operation."""
        with self.lock:
            times = self.operation_times.get(operation_name, [])
            
            if not times:
                return {"count": 0, "avg": 0.0, "min": 0.0, "max": 0.0}
            
            return {
                "count": len(times),
                "avg": sum(times) / len(times),
                "min": min(times),
                "max": max(times),
                "latest": times[-1] if times else 0.0
            }
    
    def get_all_stats(self) -> Dict[str, Dict[str, float]]:
        """Get statistics for all operations."""
        with self.lock:
            return {op_name: self.get_operation_stats(op_name) 
                   for op_name in self.operation_times.keys()}

# Global performance tracker
performance_tracker = PerformanceTracker()

def track_performance(operation_name: str):
    """Decorator to track performance of operations."""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                performance_tracker.record_operation_time(operation_name, duration)
                return result
            except Exception as e:
                duration = time.time() - start_time
                performance_tracker.record_operation_time(f"{operation_name}_error", duration)
                raise
        
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                duration = time.time() - start_time
                performance_tracker.record_operation_time(operation_name, duration)
                return result
            except Exception as e:
                duration = time.time() - start_time
                performance_tracker.record_operation_time(f"{operation_name}_error", duration)
                raise
        
        # Return appropriate wrapper based on function type
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return wrapper
    
    return decorator
