"""
Scalability Architecture for DRYAD.AI Backend
Implements horizontal scaling, load balancing, and distributed architecture patterns.
"""

import asyncio
import hashlib
import json
import time
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass
from enum import Enum
import uuid

from app.core.logging_config import get_logger
from app.core.caching import cache
from app.core.monitoring import metrics_collector

logger = get_logger(__name__)


class ServiceType(str, Enum):
    """Types of scalable services."""
    API_GATEWAY = "api_gateway"
    WORKER = "worker"
    DATABASE = "database"
    CACHE = "cache"
    LLM_PROCESSOR = "llm_processor"
    DOCUMENT_PROCESSOR = "document_processor"
    WEBSOCKET_HANDLER = "websocket_handler"


@dataclass
class ServiceInstance:
    """Represents a service instance in the cluster."""
    id: str
    service_type: ServiceType
    host: str
    port: int
    status: str
    load: float
    last_heartbeat: float
    metadata: Dict[str, Any]


class LoadBalancer:
    """Intelligent load balancer with multiple strategies."""
    
    def __init__(self):
        self.instances: Dict[str, List[ServiceInstance]] = {}
        self.strategies = {
            "round_robin": self._round_robin,
            "least_connections": self._least_connections,
            "weighted_round_robin": self._weighted_round_robin,
            "consistent_hash": self._consistent_hash,
            "health_aware": self._health_aware
        }
        self.current_strategy = "health_aware"
        self.round_robin_counters: Dict[str, int] = {}
    
    def register_instance(self, instance: ServiceInstance):
        """Register a service instance."""
        service_type = instance.service_type
        if service_type not in self.instances:
            self.instances[service_type] = []
        
        # Remove existing instance with same ID
        self.instances[service_type] = [
            inst for inst in self.instances[service_type] 
            if inst.id != instance.id
        ]
        
        # Add new instance
        self.instances[service_type].append(instance)
        logger.info(f"Registered {service_type} instance: {instance.id}")
        
        # Record metric
        metrics_collector.record_gauge(
            f"cluster.{service_type}.instances", 
            len(self.instances[service_type])
        )
    
    def unregister_instance(self, service_type: ServiceType, instance_id: str):
        """Unregister a service instance."""
        if service_type in self.instances:
            self.instances[service_type] = [
                inst for inst in self.instances[service_type] 
                if inst.id != instance_id
            ]
            logger.info(f"Unregistered {service_type} instance: {instance_id}")
            
            # Record metric
            metrics_collector.record_gauge(
                f"cluster.{service_type}.instances", 
                len(self.instances[service_type])
            )
    
    def get_instance(self, service_type: ServiceType, request_context: Optional[Dict] = None) -> Optional[ServiceInstance]:
        """Get an instance using the current load balancing strategy."""
        if service_type not in self.instances or not self.instances[service_type]:
            return None
        
        # Filter healthy instances
        healthy_instances = [
            inst for inst in self.instances[service_type]
            if inst.status == "healthy" and time.time() - inst.last_heartbeat < 30
        ]
        
        if not healthy_instances:
            logger.warning(f"No healthy instances available for {service_type}")
            return None
        
        # Apply load balancing strategy
        strategy_func = self.strategies.get(self.current_strategy, self._round_robin)
        selected_instance = strategy_func(service_type, healthy_instances, request_context)
        
        # Record selection metric
        metrics_collector.record_counter(f"load_balancer.{service_type}.requests")
        
        return selected_instance
    
    def _round_robin(self, service_type: ServiceType, instances: List[ServiceInstance], context: Optional[Dict]) -> ServiceInstance:
        """Round-robin load balancing."""
        if service_type not in self.round_robin_counters:
            self.round_robin_counters[service_type] = 0
        
        index = self.round_robin_counters[service_type] % len(instances)
        self.round_robin_counters[service_type] += 1
        
        return instances[index]
    
    def _least_connections(self, service_type: ServiceType, instances: List[ServiceInstance], context: Optional[Dict]) -> ServiceInstance:
        """Least connections load balancing."""
        return min(instances, key=lambda inst: inst.load)
    
    def _weighted_round_robin(self, service_type: ServiceType, instances: List[ServiceInstance], context: Optional[Dict]) -> ServiceInstance:
        """Weighted round-robin based on instance capacity."""
        # Simple implementation - in production, use actual weights
        return self._round_robin(service_type, instances, context)
    
    def _consistent_hash(self, service_type: ServiceType, instances: List[ServiceInstance], context: Optional[Dict]) -> ServiceInstance:
        """Consistent hashing for sticky sessions."""
        if not context or "session_id" not in context:
            return self._round_robin(service_type, instances, context)
        
        session_id = context["session_id"]
        hash_value = int(hashlib.md5(session_id.encode()).hexdigest(), 16)
        index = hash_value % len(instances)
        
        return instances[index]
    
    def _health_aware(self, service_type: ServiceType, instances: List[ServiceInstance], context: Optional[Dict]) -> ServiceInstance:
        """Health-aware load balancing considering load and response time."""
        # Score instances based on load (lower is better)
        scored_instances = []
        for instance in instances:
            # Simple scoring: lower load = higher score
            score = max(0, 100 - instance.load)
            scored_instances.append((score, instance))
        
        # Sort by score (highest first)
        scored_instances.sort(key=lambda x: x[0], reverse=True)
        
        # Return best instance
        return scored_instances[0][1]
    
    def get_cluster_status(self) -> Dict[str, Any]:
        """Get cluster status information."""
        status = {}
        total_instances = 0
        healthy_instances = 0
        
        for service_type, instances in self.instances.items():
            service_healthy = sum(
                1 for inst in instances 
                if inst.status == "healthy" and time.time() - inst.last_heartbeat < 30
            )
            
            status[service_type] = {
                "total_instances": len(instances),
                "healthy_instances": service_healthy,
                "unhealthy_instances": len(instances) - service_healthy,
                "average_load": sum(inst.load for inst in instances) / len(instances) if instances else 0
            }
            
            total_instances += len(instances)
            healthy_instances += service_healthy
        
        return {
            "services": status,
            "cluster_summary": {
                "total_instances": total_instances,
                "healthy_instances": healthy_instances,
                "unhealthy_instances": total_instances - healthy_instances,
                "health_percentage": (healthy_instances / total_instances * 100) if total_instances > 0 else 0
            },
            "load_balancing_strategy": self.current_strategy,
            "timestamp": time.time()
        }


class TaskQueue:
    """Distributed task queue for horizontal scaling."""
    
    def __init__(self):
        self.queues: Dict[str, List[Dict[str, Any]]] = {}
        self.processing: Dict[str, Dict[str, Any]] = {}
        self.completed: Dict[str, Dict[str, Any]] = {}
        self.failed: Dict[str, Dict[str, Any]] = {}
        self.workers: Dict[str, Dict[str, Any]] = {}
    
    def enqueue_task(self, queue_name: str, task_data: Dict[str, Any], priority: int = 0) -> str:
        """Enqueue a task for processing."""
        task_id = str(uuid.uuid4())
        
        task = {
            "id": task_id,
            "queue": queue_name,
            "data": task_data,
            "priority": priority,
            "created_at": time.time(),
            "attempts": 0,
            "max_attempts": 3
        }
        
        if queue_name not in self.queues:
            self.queues[queue_name] = []
        
        # Insert based on priority (higher priority first)
        self.queues[queue_name].append(task)
        self.queues[queue_name].sort(key=lambda t: t["priority"], reverse=True)
        
        logger.info(f"Enqueued task {task_id} to queue {queue_name}")
        metrics_collector.record_counter(f"task_queue.{queue_name}.enqueued")
        
        return task_id
    
    def dequeue_task(self, queue_name: str, worker_id: str) -> Optional[Dict[str, Any]]:
        """Dequeue a task for processing."""
        if queue_name not in self.queues or not self.queues[queue_name]:
            return None
        
        task = self.queues[queue_name].pop(0)
        task["worker_id"] = worker_id
        task["started_at"] = time.time()
        
        self.processing[task["id"]] = task
        
        logger.info(f"Dequeued task {task['id']} by worker {worker_id}")
        metrics_collector.record_counter(f"task_queue.{queue_name}.dequeued")
        
        return task
    
    def complete_task(self, task_id: str, result: Any = None):
        """Mark a task as completed."""
        if task_id in self.processing:
            task = self.processing.pop(task_id)
            task["completed_at"] = time.time()
            task["result"] = result
            task["duration"] = task["completed_at"] - task["started_at"]
            
            self.completed[task_id] = task
            
            logger.info(f"Task {task_id} completed in {task['duration']:.2f}s")
            metrics_collector.record_counter(f"task_queue.{task['queue']}.completed")
            metrics_collector.record_timer(f"task_queue.{task['queue']}.duration", task["duration"] * 1000)
    
    def fail_task(self, task_id: str, error: str):
        """Mark a task as failed."""
        if task_id in self.processing:
            task = self.processing.pop(task_id)
            task["failed_at"] = time.time()
            task["error"] = error
            task["attempts"] += 1
            
            # Retry if under max attempts
            if task["attempts"] < task["max_attempts"]:
                # Re-queue with delay
                task["retry_after"] = time.time() + (2 ** task["attempts"])  # Exponential backoff
                self.queues[task["queue"]].append(task)
                logger.warning(f"Task {task_id} failed, retrying (attempt {task['attempts']})")
            else:
                self.failed[task_id] = task
                logger.error(f"Task {task_id} failed permanently: {error}")
                metrics_collector.record_counter(f"task_queue.{task['queue']}.failed")
    
    def register_worker(self, worker_id: str, capabilities: List[str]):
        """Register a worker."""
        self.workers[worker_id] = {
            "id": worker_id,
            "capabilities": capabilities,
            "registered_at": time.time(),
            "last_heartbeat": time.time(),
            "tasks_processed": 0
        }
        
        logger.info(f"Registered worker {worker_id} with capabilities: {capabilities}")
        metrics_collector.record_gauge("task_queue.workers.active", len(self.workers))
    
    def worker_heartbeat(self, worker_id: str):
        """Update worker heartbeat."""
        if worker_id in self.workers:
            self.workers[worker_id]["last_heartbeat"] = time.time()
    
    def get_queue_status(self) -> Dict[str, Any]:
        """Get queue status information."""
        status = {}
        
        for queue_name, tasks in self.queues.items():
            status[queue_name] = {
                "pending": len(tasks),
                "processing": len([t for t in self.processing.values() if t["queue"] == queue_name]),
                "completed": len([t for t in self.completed.values() if t["queue"] == queue_name]),
                "failed": len([t for t in self.failed.values() if t["queue"] == queue_name])
            }
        
        active_workers = sum(
            1 for worker in self.workers.values()
            if time.time() - worker["last_heartbeat"] < 60
        )
        
        return {
            "queues": status,
            "workers": {
                "total": len(self.workers),
                "active": active_workers,
                "inactive": len(self.workers) - active_workers
            },
            "timestamp": time.time()
        }


class CircuitBreaker:
    """Circuit breaker pattern for fault tolerance."""
    
    def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time = 0
        self.state = "closed"  # closed, open, half_open
    
    def call(self, func: Callable, *args, **kwargs):
        """Execute function with circuit breaker protection."""
        if self.state == "open":
            if time.time() - self.last_failure_time > self.recovery_timeout:
                self.state = "half_open"
                logger.info("Circuit breaker transitioning to half-open")
            else:
                raise Exception("Circuit breaker is open")
        
        try:
            result = func(*args, **kwargs)
            
            if self.state == "half_open":
                self.state = "closed"
                self.failure_count = 0
                logger.info("Circuit breaker closed - service recovered")
            
            return result
            
        except Exception as e:
            self.failure_count += 1
            self.last_failure_time = time.time()
            
            if self.failure_count >= self.failure_threshold:
                self.state = "open"
                logger.warning(f"Circuit breaker opened after {self.failure_count} failures")
            
            raise e
    
    def get_status(self) -> Dict[str, Any]:
        """Get circuit breaker status."""
        return {
            "state": self.state,
            "failure_count": self.failure_count,
            "failure_threshold": self.failure_threshold,
            "last_failure_time": self.last_failure_time,
            "recovery_timeout": self.recovery_timeout
        }


class AutoScaler:
    """Auto-scaling manager for dynamic resource allocation."""
    
    def __init__(self):
        self.scaling_policies: Dict[str, Dict[str, Any]] = {}
        self.scaling_history: List[Dict[str, Any]] = []
        self.cooldown_period = 300  # 5 minutes
    
    def register_scaling_policy(self, service_type: str, policy: Dict[str, Any]):
        """Register an auto-scaling policy."""
        self.scaling_policies[service_type] = policy
        logger.info(f"Registered scaling policy for {service_type}")
    
    def evaluate_scaling(self, service_type: str, metrics: Dict[str, Any]) -> Optional[str]:
        """Evaluate if scaling is needed."""
        if service_type not in self.scaling_policies:
            return None
        
        policy = self.scaling_policies[service_type]
        current_instances = metrics.get("current_instances", 0)
        
        # Check if in cooldown period
        recent_scaling = [
            event for event in self.scaling_history
            if event["service_type"] == service_type and 
               time.time() - event["timestamp"] < self.cooldown_period
        ]
        
        if recent_scaling:
            return None
        
        # Scale up conditions
        if (metrics.get("cpu_usage", 0) > policy.get("scale_up_cpu_threshold", 80) or
            metrics.get("memory_usage", 0) > policy.get("scale_up_memory_threshold", 80) or
            metrics.get("queue_length", 0) > policy.get("scale_up_queue_threshold", 100)):
            
            if current_instances < policy.get("max_instances", 10):
                self._record_scaling_event(service_type, "scale_up", current_instances, current_instances + 1)
                return "scale_up"
        
        # Scale down conditions
        elif (metrics.get("cpu_usage", 0) < policy.get("scale_down_cpu_threshold", 20) and
              metrics.get("memory_usage", 0) < policy.get("scale_down_memory_threshold", 30) and
              metrics.get("queue_length", 0) < policy.get("scale_down_queue_threshold", 10)):
            
            if current_instances > policy.get("min_instances", 1):
                self._record_scaling_event(service_type, "scale_down", current_instances, current_instances - 1)
                return "scale_down"
        
        return None
    
    def _record_scaling_event(self, service_type: str, action: str, from_instances: int, to_instances: int):
        """Record a scaling event."""
        event = {
            "service_type": service_type,
            "action": action,
            "from_instances": from_instances,
            "to_instances": to_instances,
            "timestamp": time.time()
        }
        
        self.scaling_history.append(event)
        
        # Keep only recent history
        cutoff_time = time.time() - 86400  # 24 hours
        self.scaling_history = [
            event for event in self.scaling_history
            if event["timestamp"] > cutoff_time
        ]
        
        logger.info(f"Scaling event: {action} {service_type} from {from_instances} to {to_instances}")
        metrics_collector.record_counter(f"autoscaler.{service_type}.{action}")
    
    def get_scaling_status(self) -> Dict[str, Any]:
        """Get auto-scaling status."""
        return {
            "policies": self.scaling_policies,
            "recent_events": self.scaling_history[-10:],  # Last 10 events
            "cooldown_period": self.cooldown_period,
            "timestamp": time.time()
        }


# Global instances
load_balancer = LoadBalancer()
task_queue = TaskQueue()
auto_scaler = AutoScaler()


def get_scalability_status() -> Dict[str, Any]:
    """Get comprehensive scalability status."""
    return {
        "load_balancer": load_balancer.get_cluster_status(),
        "task_queue": task_queue.get_queue_status(),
        "auto_scaler": auto_scaler.get_scaling_status(),
        "timestamp": time.time()
    }
