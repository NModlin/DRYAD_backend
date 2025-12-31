"""
Advanced Monitoring and Observability System for DRYAD.AI Backend
Provides comprehensive metrics collection, distributed tracing, alerting, and observability features.
"""

import asyncio
import time
import psutil
import threading
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Callable, Union
from collections import defaultdict, deque
from dataclasses import dataclass, asdict, field
from enum import Enum
from contextlib import asynccontextmanager
import json
import hashlib

from app.core.logging_config import get_logger, metrics_logger
from app.core.error_handling import error_handler
from app.core.caching import cache

logger = get_logger(__name__)

@dataclass
class PerformanceBaseline:
    """Performance baseline for comparison."""
    metric_name: str
    baseline_value: float
    threshold_warning: float
    threshold_critical: float
    unit: str
    created_at: float = field(default_factory=time.time)

@dataclass
class AlertRule:
    """Alert rule definition."""
    id: str
    name: str
    metric_name: str
    condition: str  # gt, lt, eq, gte, lte
    threshold: float
    severity: str  # critical, warning, info
    duration_seconds: int = 300  # Alert after condition persists for this duration
    cooldown_seconds: int = 900  # Cooldown period before re-alerting
    enabled: bool = True
    last_triggered: Optional[float] = None
    last_resolved: Optional[float] = None

@dataclass
class TraceSpan:
    """Distributed tracing span."""
    trace_id: str
    span_id: str
    parent_span_id: Optional[str]
    operation_name: str
    start_time: float
    end_time: Optional[float] = None
    duration: Optional[float] = None
    tags: Dict[str, Any] = field(default_factory=dict)
    logs: List[Dict[str, Any]] = field(default_factory=list)
    status: str = "active"  # active, completed, error

class DistributedTracer:
    """Advanced distributed tracing system."""

    def __init__(self, max_spans: int = 10000):
        self.max_spans = max_spans
        self.spans: Dict[str, TraceSpan] = {}
        self.active_traces: Dict[str, List[str]] = defaultdict(list)
        self.span_lock = threading.RLock()

    def start_trace(self, operation_name: str, tags: Optional[Dict[str, Any]] = None) -> str:
        """Start a new trace."""
        trace_id = str(uuid.uuid4())
        span_id = str(uuid.uuid4())

        span = TraceSpan(
            trace_id=trace_id,
            span_id=span_id,
            parent_span_id=None,
            operation_name=operation_name,
            start_time=time.time(),
            tags=tags or {}
        )

        with self.span_lock:
            self.spans[span_id] = span
            self.active_traces[trace_id].append(span_id)

        return span_id

    def finish_span(self, span_id: str, status: str = "completed", tags: Optional[Dict[str, Any]] = None):
        """Finish a span."""
        with self.span_lock:
            if span_id not in self.spans:
                return

            span = self.spans[span_id]
            span.end_time = time.time()
            span.duration = span.end_time - span.start_time
            span.status = status

            if tags:
                span.tags.update(tags)

class AlertingSystem:
    """Advanced alerting system with rules and notifications."""

    def __init__(self):
        self.alert_rules: Dict[str, AlertRule] = {}
        self.active_alerts: Dict[str, Dict[str, Any]] = {}
        self.alert_history: deque = deque(maxlen=1000)
        self.notification_handlers: List[Callable] = []
        self.is_monitoring = False
        self.monitor_thread = None

    def add_alert_rule(self, rule: AlertRule):
        """Add an alert rule."""
        self.alert_rules[rule.id] = rule
        logger.info(f"Added alert rule: {rule.name}")

    def start_monitoring(self):
        """Start alert monitoring."""
        if self.is_monitoring:
            return

        self.is_monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self.monitor_thread.start()
        logger.info("Alert monitoring started")

    def _monitoring_loop(self):
        """Main alert monitoring loop."""
        while self.is_monitoring:
            try:
                self._check_alert_conditions()
                time.sleep(30)  # Check every 30 seconds
            except Exception as e:
                logger.error(f"Error in alert monitoring: {e}")
                time.sleep(30)

# AI-specific monitoring components
class AISystemMonitor:
    """Enhanced AI system monitoring with advanced metrics and tracing."""

    def __init__(self):
        self.llm_metrics = {
            "requests_total": 0,
            "requests_success": 0,
            "requests_error": 0,
            "total_tokens_generated": 0,
            "avg_response_time": 0.0,
            "active_requests": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "model_switches": 0
        }
        self.agent_metrics = {
            "workflows_total": 0,
            "workflows_success": 0,
            "workflows_error": 0,
            "active_workflows": 0,
            "avg_workflow_time": 0.0,
            "multi_agent_executions": 0,
            "fallback_activations": 0
        }
        self.model_metrics = {
            "models_loaded": 0,
            "model_load_time": 0.0,
            "model_memory_usage": 0.0,
            "inference_speed": 0.0,
            "context_length_avg": 0.0
        }
        self.performance_baselines: Dict[str, PerformanceBaseline] = {}
        self.lock = threading.RLock()
        self.tracer = DistributedTracer()
        self.alerting = AlertingSystem()

    def set_performance_baseline(self, metric_name: str, baseline_value: float,
                               warning_threshold: float, critical_threshold: float, unit: str = ""):
        """Set performance baseline for a metric."""
        baseline = PerformanceBaseline(
            metric_name=metric_name,
            baseline_value=baseline_value,
            threshold_warning=warning_threshold,
            threshold_critical=critical_threshold,
            unit=unit
        )
        self.performance_baselines[metric_name] = baseline
        logger.info(f"Set performance baseline for {metric_name}: {baseline_value} {unit}")

    def check_performance_deviation(self, metric_name: str, current_value: float) -> Optional[str]:
        """Check if current value deviates from baseline."""
        if metric_name not in self.performance_baselines:
            return None

        baseline = self.performance_baselines[metric_name]
        deviation = abs(current_value - baseline.baseline_value) / baseline.baseline_value * 100

        if deviation >= baseline.threshold_critical:
            return "critical"
        elif deviation >= baseline.threshold_warning:
            return "warning"

        return None

    def record_llm_request(self, success: bool, response_time: float, tokens: int = 0, model: str = ""):
        """Record LLM request metrics."""
        with self.lock:
            self.llm_metrics["requests_total"] += 1
            if success:
                self.llm_metrics["requests_success"] += 1
                self.llm_metrics["total_tokens_generated"] += tokens
            else:
                self.llm_metrics["requests_error"] += 1

            # Update average response time
            total_requests = self.llm_metrics["requests_total"]
            current_avg = self.llm_metrics["avg_response_time"]
            self.llm_metrics["avg_response_time"] = (
                (current_avg * (total_requests - 1) + response_time) / total_requests
            )

    def record_agent_workflow(self, success: bool, workflow_time: float, workflow_type: str = ""):
        """Record agent workflow metrics."""
        with self.lock:
            self.agent_metrics["workflows_total"] += 1
            if success:
                self.agent_metrics["workflows_success"] += 1
            else:
                self.agent_metrics["workflows_error"] += 1

            # Update average workflow time
            total_workflows = self.agent_metrics["workflows_total"]
            current_avg = self.agent_metrics["avg_workflow_time"]
            self.agent_metrics["avg_workflow_time"] = (
                (current_avg * (total_workflows - 1) + workflow_time) / total_workflows
            )

    def record_model_load(self, load_time: float, memory_usage: float, model_name: str = ""):
        """Record model loading metrics."""
        with self.lock:
            self.model_metrics["models_loaded"] += 1
            self.model_metrics["model_load_time"] = load_time
            self.model_metrics["model_memory_usage"] = memory_usage

    def get_ai_metrics(self) -> Dict[str, Any]:
        """Get all AI system metrics."""
        with self.lock:
            return {
                "llm": dict(self.llm_metrics),
                "agents": dict(self.agent_metrics),
                "models": dict(self.model_metrics),
                "timestamp": time.time()
            }


class AlertSeverity(str, Enum):
    """Alert severity levels."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class MetricType(str, Enum):
    """Types of metrics."""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    TIMER = "timer"


@dataclass
class Metric:
    """Metric data structure."""
    name: str
    type: MetricType
    value: float
    timestamp: float
    tags: Dict[str, str]
    description: Optional[str] = None


@dataclass
class Alert:
    """Alert data structure."""
    id: str
    name: str
    severity: AlertSeverity
    message: str
    timestamp: float
    resolved: bool = False
    resolved_at: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None


class MetricsCollector:
    """Centralized metrics collection system."""
    
    def __init__(self):
        self.metrics: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        self.counters: Dict[str, float] = defaultdict(float)
        self.gauges: Dict[str, float] = {}
        self.histograms: Dict[str, List[float]] = defaultdict(list)
        self.timers: Dict[str, deque] = defaultdict(lambda: deque(maxlen=100))
        
        # System metrics
        self.system_metrics_enabled = True
        self.system_metrics_interval = 30  # seconds
        self._system_metrics_task = None
        
        # Custom metrics
        self.custom_metrics: Dict[str, Callable] = {}

        # AI system monitoring
        self.ai_monitor = AISystemMonitor()

        logger.info("Metrics collector initialized with AI monitoring")
    
    def start_system_metrics_collection(self):
        """Start automatic system metrics collection."""
        if self._system_metrics_task is None:
            self._system_metrics_task = threading.Thread(
                target=self._collect_system_metrics_loop,
                daemon=True
            )
            self._system_metrics_task.start()
            logger.info("System metrics collection started")
    
    def _collect_system_metrics_loop(self):
        """Background loop for system metrics collection."""
        while self.system_metrics_enabled:
            try:
                self._collect_system_metrics()
                time.sleep(self.system_metrics_interval)
            except Exception as e:
                logger.error(f"Error collecting system metrics: {e}")
                time.sleep(self.system_metrics_interval)
    
    def _collect_system_metrics(self):
        """Collect system-level metrics."""
        now = time.time()
        
        # CPU metrics
        cpu_percent = psutil.cpu_percent(interval=1)
        self.record_gauge("system.cpu.usage_percent", cpu_percent)
        
        # Memory metrics
        memory = psutil.virtual_memory()
        self.record_gauge("system.memory.usage_percent", memory.percent)
        self.record_gauge("system.memory.available_bytes", memory.available)
        self.record_gauge("system.memory.used_bytes", memory.used)
        
        # Disk metrics
        disk = psutil.disk_usage('/')
        self.record_gauge("system.disk.usage_percent", (disk.used / disk.total) * 100)
        self.record_gauge("system.disk.free_bytes", disk.free)
        self.record_gauge("system.disk.used_bytes", disk.used)
        
        # Network metrics
        network = psutil.net_io_counters()
        self.record_counter("system.network.bytes_sent", network.bytes_sent)
        self.record_counter("system.network.bytes_recv", network.bytes_recv)
        self.record_counter("system.network.packets_sent", network.packets_sent)
        self.record_counter("system.network.packets_recv", network.packets_recv)
        
        # Process metrics
        process = psutil.Process()
        self.record_gauge("process.cpu.usage_percent", process.cpu_percent())
        self.record_gauge("process.memory.rss_bytes", process.memory_info().rss)
        self.record_gauge("process.memory.vms_bytes", process.memory_info().vms)
        self.record_gauge("process.threads.count", process.num_threads())
        
        # File descriptors (Unix only)
        try:
            self.record_gauge("process.fd.count", process.num_fds())
        except AttributeError:
            pass  # Windows doesn't have num_fds
    
    def record_counter(self, name: str, value: float = 1, tags: Optional[Dict[str, str]] = None):
        """Record a counter metric."""
        self.counters[name] += value
        metric = Metric(
            name=name,
            type=MetricType.COUNTER,
            value=self.counters[name],
            timestamp=time.time(),
            tags=tags or {}
        )
        self.metrics[name].append(metric)
        metrics_logger.increment_counter(name, int(value), tags)
    
    def record_gauge(self, name: str, value: float, tags: Optional[Dict[str, str]] = None):
        """Record a gauge metric."""
        self.gauges[name] = value
        metric = Metric(
            name=name,
            type=MetricType.GAUGE,
            value=value,
            timestamp=time.time(),
            tags=tags or {}
        )
        self.metrics[name].append(metric)
        metrics_logger.record_gauge(name, value, tags)
    
    def record_histogram(self, name: str, value: float, tags: Optional[Dict[str, str]] = None):
        """Record a histogram metric."""
        self.histograms[name].append(value)
        # Keep only last 1000 values
        if len(self.histograms[name]) > 1000:
            self.histograms[name] = self.histograms[name][-1000:]
        
        metric = Metric(
            name=name,
            type=MetricType.HISTOGRAM,
            value=value,
            timestamp=time.time(),
            tags=tags or {}
        )
        self.metrics[name].append(metric)
        metrics_logger.record_histogram(name, value, tags)
    
    def record_timer(self, name: str, duration_ms: float, tags: Optional[Dict[str, str]] = None):
        """Record a timer metric."""
        self.timers[name].append(duration_ms)
        metric = Metric(
            name=name,
            type=MetricType.TIMER,
            value=duration_ms,
            timestamp=time.time(),
            tags=tags or {}
        )
        self.metrics[name].append(metric)
        metrics_logger.record_timing(name, duration_ms, tags)
    
    def get_metric_summary(self, name: str) -> Dict[str, Any]:
        """Get summary statistics for a metric."""
        if name not in self.metrics:
            return {}
        
        recent_metrics = list(self.metrics[name])
        if not recent_metrics:
            return {}
        
        values = [m.value for m in recent_metrics]
        
        summary = {
            "name": name,
            "type": recent_metrics[-1].type,
            "count": len(values),
            "latest_value": values[-1],
            "latest_timestamp": recent_metrics[-1].timestamp
        }
        
        if len(values) > 1:
            summary.update({
                "min": min(values),
                "max": max(values),
                "avg": sum(values) / len(values),
                "sum": sum(values)
            })
            
            # Percentiles for histograms and timers
            if recent_metrics[-1].type in [MetricType.HISTOGRAM, MetricType.TIMER]:
                sorted_values = sorted(values)
                summary.update({
                    "p50": sorted_values[int(len(sorted_values) * 0.5)],
                    "p90": sorted_values[int(len(sorted_values) * 0.9)],
                    "p95": sorted_values[int(len(sorted_values) * 0.95)],
                    "p99": sorted_values[int(len(sorted_values) * 0.99)]
                })
        
        return summary
    
    def get_all_metrics_summary(self) -> Dict[str, Any]:
        """Get summary of all metrics."""
        summaries = {}
        for name in self.metrics.keys():
            summaries[name] = self.get_metric_summary(name)
        
        return {
            "metrics": summaries,
            "ai_system": self.ai_monitor.get_ai_metrics(),
            "total_metrics": len(summaries),
            "timestamp": time.time()
        }
    
    def register_custom_metric(self, name: str, collector_func: Callable[[], float]):
        """Register a custom metric collector function."""
        self.custom_metrics[name] = collector_func
        logger.info(f"Registered custom metric: {name}")
    
    def collect_custom_metrics(self):
        """Collect all registered custom metrics."""
        for name, collector_func in self.custom_metrics.items():
            try:
                value = collector_func()
                self.record_gauge(f"custom.{name}", value)
            except Exception as e:
                logger.error(f"Error collecting custom metric {name}: {e}")


class HealthMonitor:
    """System health monitoring with configurable checks."""
    
    def __init__(self):
        self.health_checks: Dict[str, Callable] = {}
        self.health_status: Dict[str, Dict[str, Any]] = {}
        self.health_history: deque = deque(maxlen=100)
        
        # Register default health checks
        self._register_default_checks()
    
    def _register_default_checks(self):
        """Register default health checks."""
        self.register_health_check("system_resources", self._check_system_resources)
        self.register_health_check("database", self._check_database)
        self.register_health_check("llm_service", self._check_llm_service)
        self.register_health_check("error_rate", self._check_error_rate)
    
    def register_health_check(self, name: str, check_func: Callable[[], Dict[str, Any]]):
        """Register a health check function."""
        self.health_checks[name] = check_func
        logger.info(f"Registered health check: {name}")
    
    async def run_health_checks(self) -> Dict[str, Any]:
        """Run all health checks."""
        results = {}
        overall_status = "healthy"
        
        for name, check_func in self.health_checks.items():
            try:
                if asyncio.iscoroutinefunction(check_func):
                    result = await check_func()
                else:
                    result = check_func()
                
                results[name] = result
                
                # Update overall status
                if result.get("status") == "unhealthy":
                    overall_status = "unhealthy"
                elif result.get("status") == "degraded" and overall_status == "healthy":
                    overall_status = "degraded"
                    
            except Exception as e:
                logger.error(f"Health check {name} failed: {e}")
                results[name] = {
                    "status": "unhealthy",
                    "error": str(e),
                    "timestamp": time.time()
                }
                overall_status = "unhealthy"
        
        health_report = {
            "overall_status": overall_status,
            "checks": results,
            "timestamp": time.time()
        }
        
        # Store in history
        self.health_history.append(health_report)
        self.health_status = results
        
        return health_report
    
    def _check_system_resources(self) -> Dict[str, Any]:
        """Check system resource usage."""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            # Determine status based on thresholds
            if cpu_percent > 90 or memory.percent > 90 or (disk.used / disk.total) > 0.95:
                status = "unhealthy"
            elif cpu_percent > 70 or memory.percent > 70 or (disk.used / disk.total) > 0.85:
                status = "degraded"
            else:
                status = "healthy"
            
            return {
                "status": status,
                "cpu_percent": cpu_percent,
                "memory_percent": memory.percent,
                "disk_percent": (disk.used / disk.total) * 100,
                "timestamp": time.time()
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": time.time()
            }
    
    def _check_database(self) -> Dict[str, Any]:
        """Check database connectivity."""
        try:
            # This would be implemented with actual database check
            # For now, return healthy
            return {
                "status": "healthy",
                "response_time_ms": 10,
                "timestamp": time.time()
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": time.time()
            }
    
    def _check_llm_service(self) -> Dict[str, Any]:
        """Check LLM service availability."""
        try:
            from app.core.llm_config import get_llm_health_status
            llm_health = get_llm_health_status()
            
            return {
                "status": llm_health.get("status", "unknown"),
                "provider": llm_health.get("provider", "unknown"),
                "timestamp": time.time()
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": time.time()
            }
    
    def _check_error_rate(self) -> Dict[str, Any]:
        """Check system error rate."""
        try:
            error_stats = error_handler.get_error_stats()
            error_rate = error_stats.get("error_rate_1h", 0)
            
            if error_rate > 10:  # More than 10 errors per minute
                status = "unhealthy"
            elif error_rate > 5:  # More than 5 errors per minute
                status = "degraded"
            else:
                status = "healthy"
            
            return {
                "status": status,
                "error_rate_1h": error_rate,
                "total_errors": error_stats.get("total_errors", 0),
                "timestamp": time.time()
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": time.time()
            }


class AlertManager:
    """Alert management system."""
    
    def __init__(self):
        self.alerts: Dict[str, Alert] = {}
        self.alert_rules: Dict[str, Dict[str, Any]] = {}
        self.alert_history: deque = deque(maxlen=1000)
        self.notification_handlers: List[Callable] = []
        
        # Register default alert rules
        self._register_default_alert_rules()
    
    def _register_default_alert_rules(self):
        """Register default alert rules."""
        self.register_alert_rule(
            "high_cpu_usage",
            condition=lambda metrics: metrics.get("system.cpu.usage_percent", 0) > 80,
            severity=AlertSeverity.WARNING,
            message="High CPU usage detected"
        )
        
        self.register_alert_rule(
            "high_memory_usage",
            condition=lambda metrics: metrics.get("system.memory.usage_percent", 0) > 85,
            severity=AlertSeverity.WARNING,
            message="High memory usage detected"
        )
        
        self.register_alert_rule(
            "high_error_rate",
            condition=lambda metrics: metrics.get("error_rate_1h", 0) > 5,
            severity=AlertSeverity.ERROR,
            message="High error rate detected"
        )
    
    def register_alert_rule(self, name: str, condition: Callable, severity: AlertSeverity, message: str):
        """Register an alert rule."""
        self.alert_rules[name] = {
            "condition": condition,
            "severity": severity,
            "message": message
        }
        logger.info(f"Registered alert rule: {name}")
    
    def check_alert_conditions(self, metrics: Dict[str, Any]):
        """Check all alert conditions against current metrics."""
        for rule_name, rule in self.alert_rules.items():
            try:
                if rule["condition"](metrics):
                    self.trigger_alert(
                        rule_name,
                        rule["severity"],
                        rule["message"],
                        metadata={"metrics": metrics}
                    )
                else:
                    # Resolve alert if condition is no longer met
                    self.resolve_alert(rule_name)
                    
            except Exception as e:
                logger.error(f"Error checking alert rule {rule_name}: {e}")
    
    def trigger_alert(self, name: str, severity: AlertSeverity, message: str, metadata: Optional[Dict[str, Any]] = None):
        """Trigger an alert."""
        alert_id = f"{name}_{int(time.time())}"
        
        alert = Alert(
            id=alert_id,
            name=name,
            severity=severity,
            message=message,
            timestamp=time.time(),
            metadata=metadata
        )
        
        self.alerts[name] = alert
        self.alert_history.append(alert)
        
        # Log alert
        logger.warning(f"Alert triggered: {name} - {message}", extra={
            "alert": asdict(alert)
        })
        
        # Notify handlers
        for handler in self.notification_handlers:
            try:
                handler(alert)
            except Exception as e:
                logger.error(f"Error in alert notification handler: {e}")
    
    def resolve_alert(self, name: str):
        """Resolve an active alert."""
        if name in self.alerts and not self.alerts[name].resolved:
            self.alerts[name].resolved = True
            self.alerts[name].resolved_at = time.time()
            
            logger.info(f"Alert resolved: {name}")
    
    def get_active_alerts(self) -> List[Alert]:
        """Get all active alerts."""
        return [alert for alert in self.alerts.values() if not alert.resolved]
    
    def get_alert_summary(self) -> Dict[str, Any]:
        """Get alert summary."""
        active_alerts = self.get_active_alerts()
        
        severity_counts = defaultdict(int)
        for alert in active_alerts:
            severity_counts[alert.severity] += 1
        
        return {
            "active_alerts": len(active_alerts),
            "severity_breakdown": dict(severity_counts),
            "total_alerts_24h": len([a for a in self.alert_history if a.timestamp > time.time() - 86400]),
            "timestamp": time.time()
        }


# Global instances
metrics_collector = MetricsCollector()
health_monitor = HealthMonitor()
alert_manager = AlertManager()
ai_system_monitor = AISystemMonitor()
distributed_tracer = DistributedTracer()


def start_monitoring():
    """Start the monitoring system."""
    metrics_collector.start_system_metrics_collection()
    logger.info("Monitoring system started")


def get_monitoring_dashboard() -> Dict[str, Any]:
    """Get comprehensive monitoring dashboard data."""
    return {
        "metrics": metrics_collector.get_all_metrics_summary(),
        "health": health_monitor.health_status,
        "alerts": alert_manager.get_alert_summary(),
        "timestamp": time.time()
    }
