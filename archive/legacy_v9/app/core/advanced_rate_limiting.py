"""
Advanced Rate Limiting and DDoS Protection System

This module provides sophisticated rate limiting, DDoS protection, and traffic analysis
capabilities for the DRYAD.AI Backend system.
"""

import asyncio
import hashlib
import json
import logging
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple
from threading import Lock, Thread

from fastapi import HTTPException, Request, status
from starlette.responses import JSONResponse

logger = logging.getLogger(__name__)


class RateLimitStrategy(Enum):
    """Rate limiting strategies."""
    TOKEN_BUCKET = "token_bucket"
    SLIDING_WINDOW = "sliding_window"
    FIXED_WINDOW = "fixed_window"
    ADAPTIVE = "adaptive"


class ThreatLevel(Enum):
    """DDoS threat levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class RateLimitRule:
    """Rate limiting rule configuration."""
    name: str
    requests_per_second: float
    burst_size: int
    window_size: int
    strategy: RateLimitStrategy = RateLimitStrategy.TOKEN_BUCKET
    enabled: bool = True
    priority: int = 1  # Higher priority rules are checked first


@dataclass
class TrafficPattern:
    """Traffic pattern analysis data."""
    ip_address: str
    request_count: int
    unique_endpoints: Set[str] = field(default_factory=set)
    user_agents: Set[str] = field(default_factory=set)
    request_intervals: List[float] = field(default_factory=list)
    first_seen: float = field(default_factory=time.time)
    last_seen: float = field(default_factory=time.time)
    threat_score: float = 0.0
    is_suspicious: bool = False


@dataclass
class DDoSAlert:
    """DDoS attack alert."""
    id: str
    alert_type: str
    threat_level: ThreatLevel
    source_ips: List[str]
    target_endpoints: List[str]
    attack_pattern: str
    start_time: float
    end_time: Optional[float] = None
    mitigation_actions: List[str] = field(default_factory=list)
    resolved: bool = False


class TokenBucket:
    """Token bucket rate limiter implementation."""
    
    def __init__(self, capacity: int, refill_rate: float):
        self.capacity = capacity
        self.tokens = capacity
        self.refill_rate = refill_rate
        self.last_refill = time.time()
        self.lock = Lock()
    
    def consume(self, tokens: int = 1) -> bool:
        """Try to consume tokens from the bucket."""
        with self.lock:
            now = time.time()
            # Add tokens based on time elapsed
            elapsed = now - self.last_refill
            self.tokens = min(self.capacity, self.tokens + elapsed * self.refill_rate)
            self.last_refill = now
            
            if self.tokens >= tokens:
                self.tokens -= tokens
                return True
            return False
    
    def get_wait_time(self, tokens: int = 1) -> float:
        """Get time to wait before tokens are available."""
        with self.lock:
            if self.tokens >= tokens:
                return 0.0
            needed_tokens = tokens - self.tokens
            return needed_tokens / self.refill_rate


class SlidingWindowCounter:
    """Sliding window rate limiter implementation."""
    
    def __init__(self, window_size: int, max_requests: int):
        self.window_size = window_size
        self.max_requests = max_requests
        self.requests = deque()
        self.lock = Lock()
    
    def is_allowed(self) -> bool:
        """Check if request is allowed."""
        with self.lock:
            now = time.time()
            # Remove old requests outside the window
            while self.requests and self.requests[0] < now - self.window_size:
                self.requests.popleft()
            
            if len(self.requests) < self.max_requests:
                self.requests.append(now)
                return True
            return False
    
    def get_current_count(self) -> int:
        """Get current request count in window."""
        with self.lock:
            now = time.time()
            while self.requests and self.requests[0] < now - self.window_size:
                self.requests.popleft()
            return len(self.requests)


class AdvancedRateLimiter:
    """Advanced rate limiting system with multiple strategies and DDoS protection."""
    
    def __init__(self):
        self.rules: Dict[str, RateLimitRule] = {}
        self.token_buckets: Dict[str, TokenBucket] = {}
        self.sliding_windows: Dict[str, SlidingWindowCounter] = {}
        self.blocked_ips: Dict[str, float] = {}  # IP -> unblock_time
        self.traffic_patterns: Dict[str, TrafficPattern] = {}
        self.ddos_alerts: Dict[str, DDoSAlert] = {}
        self.whitelist: Set[str] = set()
        self.blacklist: Set[str] = set()
        self.lock = Lock()
        
        # DDoS detection thresholds
        self.ddos_thresholds = {
            "requests_per_second": 100,
            "unique_ips_threshold": 50,
            "suspicious_score_threshold": 80.0,
            "burst_detection_window": 60,
        }
        
        # Initialize default rules
        self._initialize_default_rules()
        
        # Start background monitoring
        self.monitoring_thread = Thread(target=self._background_monitoring, daemon=True)
        self.monitoring_thread.start()
    
    def _initialize_default_rules(self):
        """Initialize default rate limiting rules."""
        default_rules = [
            RateLimitRule("api_general", 10.0, 20, 60, RateLimitStrategy.TOKEN_BUCKET, True, 1),
            RateLimitRule("api_auth", 5.0, 10, 60, RateLimitStrategy.SLIDING_WINDOW, True, 2),
            RateLimitRule("api_upload", 2.0, 5, 60, RateLimitStrategy.TOKEN_BUCKET, True, 3),
            RateLimitRule("api_ai", 1.0, 3, 60, RateLimitStrategy.ADAPTIVE, True, 4),
        ]
        
        for rule in default_rules:
            self.add_rule(rule)
    
    def add_rule(self, rule: RateLimitRule):
        """Add a rate limiting rule."""
        self.rules[rule.name] = rule
        logger.info(f"Added rate limiting rule: {rule.name}")
    
    def remove_rule(self, rule_name: str):
        """Remove a rate limiting rule."""
        if rule_name in self.rules:
            del self.rules[rule_name]
            logger.info(f"Removed rate limiting rule: {rule_name}")
    
    def check_rate_limit(self, identifier: str, rule_name: str) -> Tuple[bool, Dict[str, Any]]:
        """Check if request is within rate limits."""
        if identifier in self.whitelist:
            return True, {"status": "whitelisted"}
        
        if identifier in self.blacklist:
            return False, {"status": "blacklisted", "reason": "IP in blacklist"}
        
        # Check if IP is temporarily blocked
        if identifier in self.blocked_ips:
            if time.time() < self.blocked_ips[identifier]:
                return False, {"status": "blocked", "reason": "Temporarily blocked"}
            else:
                del self.blocked_ips[identifier]
        
        rule = self.rules.get(rule_name)
        if not rule or not rule.enabled:
            return True, {"status": "no_rule"}
        
        bucket_key = f"{identifier}:{rule_name}"
        
        if rule.strategy == RateLimitStrategy.TOKEN_BUCKET:
            return self._check_token_bucket(bucket_key, rule)
        elif rule.strategy == RateLimitStrategy.SLIDING_WINDOW:
            return self._check_sliding_window(bucket_key, rule)
        elif rule.strategy == RateLimitStrategy.ADAPTIVE:
            return self._check_adaptive_limit(identifier, rule)
        else:
            return True, {"status": "unknown_strategy"}
    
    def _check_token_bucket(self, bucket_key: str, rule: RateLimitRule) -> Tuple[bool, Dict[str, Any]]:
        """Check token bucket rate limit."""
        if bucket_key not in self.token_buckets:
            self.token_buckets[bucket_key] = TokenBucket(rule.burst_size, rule.requests_per_second)
        
        bucket = self.token_buckets[bucket_key]
        allowed = bucket.consume()
        
        return allowed, {
            "status": "allowed" if allowed else "rate_limited",
            "strategy": "token_bucket",
            "tokens_remaining": int(bucket.tokens),
            "wait_time": bucket.get_wait_time() if not allowed else 0
        }
    
    def _check_sliding_window(self, window_key: str, rule: RateLimitRule) -> Tuple[bool, Dict[str, Any]]:
        """Check sliding window rate limit."""
        if window_key not in self.sliding_windows:
            self.sliding_windows[window_key] = SlidingWindowCounter(rule.window_size, rule.burst_size)
        
        window = self.sliding_windows[window_key]
        allowed = window.is_allowed()
        
        return allowed, {
            "status": "allowed" if allowed else "rate_limited",
            "strategy": "sliding_window",
            "current_count": window.get_current_count(),
            "max_requests": rule.burst_size
        }
    
    def _check_adaptive_limit(self, identifier: str, rule: RateLimitRule) -> Tuple[bool, Dict[str, Any]]:
        """Check adaptive rate limit based on traffic patterns."""
        pattern = self.traffic_patterns.get(identifier)
        if not pattern:
            # First request, allow but start monitoring
            return True, {"status": "allowed", "strategy": "adaptive", "reason": "first_request"}
        
        # Adjust rate limit based on threat score
        adjusted_rate = rule.requests_per_second
        if pattern.threat_score > 50:
            adjusted_rate *= (100 - pattern.threat_score) / 100
        
        # Use token bucket with adjusted rate
        bucket_key = f"{identifier}:adaptive"
        if bucket_key not in self.token_buckets:
            self.token_buckets[bucket_key] = TokenBucket(rule.burst_size, adjusted_rate)
        else:
            # Update rate if it changed
            self.token_buckets[bucket_key].refill_rate = adjusted_rate
        
        bucket = self.token_buckets[bucket_key]
        allowed = bucket.consume()
        
        return allowed, {
            "status": "allowed" if allowed else "rate_limited",
            "strategy": "adaptive",
            "threat_score": pattern.threat_score,
            "adjusted_rate": adjusted_rate
        }

    def analyze_traffic_pattern(self, request: Request, identifier: str):
        """Analyze traffic patterns for DDoS detection."""
        now = time.time()

        with self.lock:
            if identifier not in self.traffic_patterns:
                self.traffic_patterns[identifier] = TrafficPattern(
                    ip_address=identifier,
                    request_count=0
                )

            pattern = self.traffic_patterns[identifier]
            pattern.request_count += 1
            pattern.last_seen = now
            pattern.unique_endpoints.add(str(request.url.path))

            # Add user agent if available
            user_agent = request.headers.get("user-agent", "unknown")
            pattern.user_agents.add(user_agent)

            # Calculate request interval
            if hasattr(pattern, '_last_request_time'):
                interval = now - pattern._last_request_time
                pattern.request_intervals.append(interval)
                # Keep only last 100 intervals
                if len(pattern.request_intervals) > 100:
                    pattern.request_intervals.pop(0)
            else:
                pattern.request_intervals.append(0)

            pattern._last_request_time = now

            # Calculate threat score
            pattern.threat_score = self._calculate_threat_score(pattern)
            pattern.is_suspicious = pattern.threat_score > 70.0

    def _calculate_threat_score(self, pattern: TrafficPattern) -> float:
        """Calculate threat score based on traffic patterns."""
        score = 0.0

        # High request frequency
        if len(pattern.request_intervals) > 10:
            avg_interval = sum(pattern.request_intervals[-10:]) / 10
            if avg_interval < 0.1:  # More than 10 requests per second
                score += 30.0
            elif avg_interval < 0.5:  # More than 2 requests per second
                score += 15.0

        # Low endpoint diversity (potential bot behavior)
        if pattern.request_count > 50:
            endpoint_diversity = len(pattern.unique_endpoints) / pattern.request_count
            if endpoint_diversity < 0.1:
                score += 25.0
            elif endpoint_diversity < 0.3:
                score += 10.0

        # Suspicious user agents
        suspicious_agents = ["bot", "crawler", "spider", "scraper", "curl", "wget"]
        for agent in pattern.user_agents:
            if any(sus in agent.lower() for sus in suspicious_agents):
                score += 20.0
                break

        # Very regular intervals (bot-like behavior)
        if len(pattern.request_intervals) > 20:
            intervals = pattern.request_intervals[-20:]
            variance = sum((x - sum(intervals)/len(intervals))**2 for x in intervals) / len(intervals)
            if variance < 0.01:  # Very regular timing
                score += 15.0

        return min(100.0, score)

    def detect_ddos_attack(self) -> List[DDoSAlert]:
        """Detect potential DDoS attacks."""
        alerts = []
        now = time.time()

        # Analyze overall traffic patterns
        recent_patterns = {
            ip: pattern for ip, pattern in self.traffic_patterns.items()
            if now - pattern.last_seen < 300  # Last 5 minutes
        }

        if not recent_patterns:
            return alerts

        # Check for volumetric attacks
        total_requests = sum(p.request_count for p in recent_patterns.values())
        if total_requests > self.ddos_thresholds["requests_per_second"] * 60:  # Per minute
            alert_id = hashlib.md5(f"volumetric_{now}".encode()).hexdigest()[:16]
            alerts.append(DDoSAlert(
                id=alert_id,
                alert_type="volumetric_attack",
                threat_level=ThreatLevel.HIGH,
                source_ips=list(recent_patterns.keys()),
                target_endpoints=[],
                attack_pattern="High volume of requests detected",
                start_time=now
            ))

        # Check for distributed attacks
        suspicious_ips = [ip for ip, pattern in recent_patterns.items() if pattern.is_suspicious]
        if len(suspicious_ips) > self.ddos_thresholds["unique_ips_threshold"]:
            alert_id = hashlib.md5(f"distributed_{now}".encode()).hexdigest()[:16]
            alerts.append(DDoSAlert(
                id=alert_id,
                alert_type="distributed_attack",
                threat_level=ThreatLevel.CRITICAL,
                source_ips=suspicious_ips,
                target_endpoints=[],
                attack_pattern="Distributed attack from multiple IPs",
                start_time=now
            ))

        # Check for application layer attacks
        endpoint_counts = defaultdict(int)
        for pattern in recent_patterns.values():
            for endpoint in pattern.unique_endpoints:
                endpoint_counts[endpoint] += pattern.request_count

        for endpoint, count in endpoint_counts.items():
            if count > 1000:  # High requests to specific endpoint
                alert_id = hashlib.md5(f"app_layer_{endpoint}_{now}".encode()).hexdigest()[:16]
                alerts.append(DDoSAlert(
                    id=alert_id,
                    alert_type="application_layer_attack",
                    threat_level=ThreatLevel.MEDIUM,
                    source_ips=[],
                    target_endpoints=[endpoint],
                    attack_pattern=f"High requests to endpoint: {endpoint}",
                    start_time=now
                ))

        # Store alerts
        for alert in alerts:
            self.ddos_alerts[alert.id] = alert
            logger.warning(f"DDoS attack detected: {alert.alert_type} - {alert.attack_pattern}")

        return alerts

    def apply_mitigation(self, alert: DDoSAlert) -> List[str]:
        """Apply DDoS mitigation measures."""
        actions = []

        if alert.alert_type == "volumetric_attack":
            # Block top offending IPs
            for ip in alert.source_ips[:10]:  # Block top 10
                self.block_ip(ip, 3600)  # Block for 1 hour
                actions.append(f"Blocked IP {ip}")

        elif alert.alert_type == "distributed_attack":
            # Apply stricter rate limiting
            for ip in alert.source_ips:
                self.block_ip(ip, 1800)  # Block for 30 minutes
                actions.append(f"Blocked suspicious IP {ip}")

        elif alert.alert_type == "application_layer_attack":
            # Apply endpoint-specific rate limiting
            for endpoint in alert.target_endpoints:
                # This would be implemented with endpoint-specific rules
                actions.append(f"Applied strict rate limiting to {endpoint}")

        alert.mitigation_actions.extend(actions)
        logger.info(f"Applied mitigation for alert {alert.id}: {actions}")

        return actions

    def block_ip(self, ip: str, duration: int):
        """Block IP address for specified duration."""
        self.blocked_ips[ip] = time.time() + duration
        logger.warning(f"Blocked IP {ip} for {duration} seconds")

    def unblock_ip(self, ip: str):
        """Unblock IP address."""
        if ip in self.blocked_ips:
            del self.blocked_ips[ip]
            logger.info(f"Unblocked IP {ip}")

    def add_to_whitelist(self, ip: str):
        """Add IP to whitelist."""
        self.whitelist.add(ip)
        logger.info(f"Added IP {ip} to whitelist")

    def add_to_blacklist(self, ip: str):
        """Add IP to blacklist."""
        self.blacklist.add(ip)
        logger.info(f"Added IP {ip} to blacklist")

    def get_traffic_statistics(self) -> Dict[str, Any]:
        """Get traffic statistics and metrics."""
        now = time.time()

        # Active patterns (last 5 minutes)
        active_patterns = {
            ip: pattern for ip, pattern in self.traffic_patterns.items()
            if now - pattern.last_seen < 300
        }

        total_requests = sum(p.request_count for p in active_patterns.values())
        suspicious_ips = [ip for ip, pattern in active_patterns.items() if pattern.is_suspicious]

        return {
            "active_ips": len(active_patterns),
            "total_requests_5min": total_requests,
            "suspicious_ips": len(suspicious_ips),
            "blocked_ips": len(self.blocked_ips),
            "whitelist_size": len(self.whitelist),
            "blacklist_size": len(self.blacklist),
            "active_alerts": len([a for a in self.ddos_alerts.values() if not a.resolved]),
            "rate_limit_rules": len(self.rules)
        }

    def reset_rate_limits(self):
        """Reset all rate limiting state (for development/testing)."""
        with self.lock:
            self.token_buckets.clear()
            self.sliding_windows.clear()
            self.blocked_ips.clear()
            self.traffic_patterns.clear()
            self.ddos_alerts.clear()
            logger.warning("Rate limiting state has been reset")

    def clear_ip_limits(self, ip: str):
        """Clear rate limits for a specific IP address."""
        with self.lock:
            # Clear token buckets for this IP
            keys_to_remove = [key for key in self.token_buckets.keys() if key.startswith(f"{ip}:")]
            for key in keys_to_remove:
                del self.token_buckets[key]

            # Clear sliding windows for this IP
            keys_to_remove = [key for key in self.sliding_windows.keys() if key.startswith(f"{ip}:")]
            for key in keys_to_remove:
                del self.sliding_windows[key]

            # Unblock IP if blocked
            if ip in self.blocked_ips:
                del self.blocked_ips[ip]

            # Clear traffic pattern
            if ip in self.traffic_patterns:
                del self.traffic_patterns[ip]

            logger.info(f"Cleared rate limits for IP: {ip}")

    def _background_monitoring(self):
        """Background thread for continuous monitoring."""
        while True:
            try:
                # Clean old traffic patterns
                now = time.time()
                old_patterns = [
                    ip for ip, pattern in self.traffic_patterns.items()
                    if now - pattern.last_seen > 3600  # 1 hour old
                ]
                for ip in old_patterns:
                    del self.traffic_patterns[ip]

                # Clean expired blocks
                expired_blocks = [
                    ip for ip, unblock_time in self.blocked_ips.items()
                    if now > unblock_time
                ]
                for ip in expired_blocks:
                    del self.blocked_ips[ip]

                # Detect DDoS attacks
                alerts = self.detect_ddos_attack()
                for alert in alerts:
                    self.apply_mitigation(alert)

                # Sleep for 30 seconds
                time.sleep(30)

            except Exception as e:
                logger.error(f"Error in background monitoring: {e}")
                time.sleep(60)


# Global instance
_advanced_rate_limiter: Optional[AdvancedRateLimiter] = None


def get_advanced_rate_limiter() -> AdvancedRateLimiter:
    """Get the global advanced rate limiter instance."""
    global _advanced_rate_limiter
    if _advanced_rate_limiter is None:
        _advanced_rate_limiter = AdvancedRateLimiter()
    return _advanced_rate_limiter
