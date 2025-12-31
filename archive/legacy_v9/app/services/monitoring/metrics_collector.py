"""
Metrics Collector
DRYAD.AI Agent Evolution Architecture

Collects and exposes metrics for monitoring system performance.
Tracks agent execution, memory operations, orchestration decisions, etc.
"""

import time
from typing import Dict, Any, Optional
from datetime import datetime
from collections import defaultdict
import threading


class MetricsCollector:
    """Collects and aggregates system metrics."""
    
    def __init__(self):
        """Initialize metrics collector."""
        self.metrics = defaultdict(lambda: defaultdict(int))
        self.timings = defaultdict(list)
        self.gauges = {}
        self.lock = threading.Lock()
        self.start_time = time.time()
    
    def increment(self, metric_name: str, value: int = 1, labels: Optional[Dict[str, str]] = None):
        """Increment a counter metric."""
        with self.lock:
            key = self._make_key(metric_name, labels)
            self.metrics["counters"][key] += value
    
    def record_timing(self, metric_name: str, duration: float, labels: Optional[Dict[str, str]] = None):
        """Record a timing metric."""
        with self.lock:
            key = self._make_key(metric_name, labels)
            self.timings[key].append(duration)
            
            # Keep only last 1000 timings
            if len(self.timings[key]) > 1000:
                self.timings[key] = self.timings[key][-1000:]
    
    def set_gauge(self, metric_name: str, value: float, labels: Optional[Dict[str, str]] = None):
        """Set a gauge metric."""
        with self.lock:
            key = self._make_key(metric_name, labels)
            self.gauges[key] = value
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get all metrics."""
        with self.lock:
            return {
                "counters": dict(self.metrics["counters"]),
                "timings": self._calculate_timing_stats(),
                "gauges": dict(self.gauges),
                "uptime_seconds": time.time() - self.start_time,
                "timestamp": datetime.utcnow().isoformat()
            }
    
    def get_prometheus_format(self) -> str:
        """Export metrics in Prometheus format."""
        lines = []
        
        with self.lock:
            # Counters
            for key, value in self.metrics["counters"].items():
                metric_name, labels = self._parse_key(key)
                labels_str = self._format_labels(labels) if labels else ""
                lines.append(f"# TYPE {metric_name} counter")
                lines.append(f"{metric_name}{labels_str} {value}")
            
            # Gauges
            for key, value in self.gauges.items():
                metric_name, labels = self._parse_key(key)
                labels_str = self._format_labels(labels) if labels else ""
                lines.append(f"# TYPE {metric_name} gauge")
                lines.append(f"{metric_name}{labels_str} {value}")
            
            # Timing summaries
            timing_stats = self._calculate_timing_stats()
            for key, stats in timing_stats.items():
                metric_name, labels = self._parse_key(key)
                labels_str = self._format_labels(labels) if labels else ""
                
                lines.append(f"# TYPE {metric_name}_duration_seconds summary")
                lines.append(f"{metric_name}_duration_seconds_sum{labels_str} {stats['sum']}")
                lines.append(f"{metric_name}_duration_seconds_count{labels_str} {stats['count']}")
                lines.append(f"{metric_name}_duration_seconds{{quantile=\"0.5\"}}{labels_str} {stats['p50']}")
                lines.append(f"{metric_name}_duration_seconds{{quantile=\"0.95\"}}{labels_str} {stats['p95']}")
                lines.append(f"{metric_name}_duration_seconds{{quantile=\"0.99\"}}{labels_str} {stats['p99']}")
            
            # Uptime
            lines.append(f"# TYPE dryad_uptime_seconds gauge")
            lines.append(f"dryad_uptime_seconds {time.time() - self.start_time}")
        
        return "\n".join(lines)
    
    def _make_key(self, metric_name: str, labels: Optional[Dict[str, str]]) -> str:
        """Create a key from metric name and labels."""
        if not labels:
            return metric_name
        label_str = ",".join(f"{k}={v}" for k, v in sorted(labels.items()))
        return f"{metric_name}{{{label_str}}}"
    
    def _parse_key(self, key: str) -> tuple[str, Optional[Dict[str, str]]]:
        """Parse a key into metric name and labels."""
        if "{" not in key:
            return key, None
        
        metric_name, labels_str = key.split("{", 1)
        labels_str = labels_str.rstrip("}")
        
        labels = {}
        for pair in labels_str.split(","):
            k, v = pair.split("=", 1)
            labels[k] = v
        
        return metric_name, labels
    
    def _format_labels(self, labels: Dict[str, str]) -> str:
        """Format labels for Prometheus."""
        label_pairs = [f'{k}="{v}"' for k, v in sorted(labels.items())]
        return "{" + ",".join(label_pairs) + "}"
    
    def _calculate_timing_stats(self) -> Dict[str, Dict[str, float]]:
        """Calculate statistics for timing metrics."""
        stats = {}
        
        for key, timings in self.timings.items():
            if not timings:
                continue
            
            sorted_timings = sorted(timings)
            count = len(sorted_timings)
            
            stats[key] = {
                "count": count,
                "sum": sum(sorted_timings),
                "min": sorted_timings[0],
                "max": sorted_timings[-1],
                "mean": sum(sorted_timings) / count,
                "p50": sorted_timings[int(count * 0.5)],
                "p95": sorted_timings[int(count * 0.95)],
                "p99": sorted_timings[int(count * 0.99)],
            }
        
        return stats
    
    def reset(self):
        """Reset all metrics."""
        with self.lock:
            self.metrics.clear()
            self.timings.clear()
            self.gauges.clear()


class MetricsTimer:
    """Context manager for timing operations."""
    
    def __init__(self, collector: MetricsCollector, metric_name: str, labels: Optional[Dict[str, str]] = None):
        """Initialize timer."""
        self.collector = collector
        self.metric_name = metric_name
        self.labels = labels
        self.start_time = None
    
    def __enter__(self):
        """Start timing."""
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Stop timing and record."""
        duration = time.time() - self.start_time
        self.collector.record_timing(self.metric_name, duration, self.labels)
        
        # Also increment counter
        status = "error" if exc_type else "success"
        labels = dict(self.labels) if self.labels else {}
        labels["status"] = status
        self.collector.increment(f"{self.metric_name}_total", labels=labels)


# Global metrics collector instance
metrics_collector = MetricsCollector()


# Convenience functions
def increment(metric_name: str, value: int = 1, **labels):
    """Increment a counter metric."""
    metrics_collector.increment(metric_name, value, labels or None)


def record_timing(metric_name: str, duration: float, **labels):
    """Record a timing metric."""
    metrics_collector.record_timing(metric_name, duration, labels or None)


def set_gauge(metric_name: str, value: float, **labels):
    """Set a gauge metric."""
    metrics_collector.set_gauge(metric_name, value, labels or None)


def timer(metric_name: str, **labels):
    """Create a timing context manager."""
    return MetricsTimer(metrics_collector, metric_name, labels or None)


def get_metrics() -> Dict[str, Any]:
    """Get all metrics."""
    return metrics_collector.get_metrics()


def get_prometheus_metrics() -> str:
    """Get metrics in Prometheus format."""
    return metrics_collector.get_prometheus_format()

