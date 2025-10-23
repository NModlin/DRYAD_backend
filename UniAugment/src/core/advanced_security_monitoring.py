"""
Advanced Security Monitoring and Alerting System for DRYAD.AI Backend
Provides comprehensive security event detection, threat analysis, and automated alerting.
"""

import asyncio
import time
import json
import hashlib
import smtplib
import threading
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Callable, Union, Set
from collections import defaultdict, deque
from dataclasses import dataclass, field, asdict
from enum import Enum
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os

from app.core.logging_config import get_logger, metrics_logger
from app.core.monitoring import AISystemMonitor, AlertRule
from app.core.security_hardening import SecurityMonitor

logger = get_logger(__name__)


class ThreatLevel(Enum):
    """Security threat severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AlertChannel(Enum):
    """Alert notification channels."""
    EMAIL = "email"
    WEBHOOK = "webhook"
    LOG = "log"
    SLACK = "slack"
    TEAMS = "teams"


@dataclass
class SecurityAlert:
    """Security alert data structure."""
    id: str
    title: str
    description: str
    threat_level: ThreatLevel
    event_type: str
    source_ip: Optional[str] = None
    user_id: Optional[str] = None
    timestamp: float = field(default_factory=time.time)
    details: Dict[str, Any] = field(default_factory=dict)
    resolved: bool = False
    resolved_at: Optional[float] = None
    resolution_notes: Optional[str] = None


@dataclass
class ThreatPattern:
    """Security threat pattern definition."""
    name: str
    description: str
    pattern_type: str  # frequency, sequence, anomaly, correlation
    conditions: Dict[str, Any]
    threat_level: ThreatLevel
    enabled: bool = True
    detection_window_seconds: int = 300
    threshold_count: int = 5


class AdvancedSecurityMonitor:
    """Advanced security monitoring with threat detection and alerting."""
    
    def __init__(self):
        self.base_monitor = SecurityMonitor()
        self.ai_monitor = AISystemMonitor()
        
        # Security state tracking
        self.active_alerts: Dict[str, SecurityAlert] = {}
        self.alert_history: deque = deque(maxlen=10000)
        self.threat_patterns: Dict[str, ThreatPattern] = {}
        self.security_metrics: Dict[str, Any] = defaultdict(int)

        # Enhanced monitoring features
        self.ip_reputation_cache: Dict[str, Dict[str, Any]] = {}
        self.user_behavior_profiles: Dict[str, Dict[str, Any]] = {}
        self.attack_signatures: Dict[str, Dict[str, Any]] = {}
        self.geolocation_cache: Dict[str, Dict[str, Any]] = {}

        # Machine learning features for anomaly detection
        self.baseline_metrics: Dict[str, Dict[str, float]] = defaultdict(lambda: defaultdict(float))
        self.anomaly_thresholds: Dict[str, float] = {
            'request_rate': 2.0,  # Standard deviations
            'error_rate': 2.5,
            'response_time': 2.0,
            'unique_ips': 3.0,
            'failed_auth': 1.5
        }

        # Event correlation
        self.event_correlation_window = 300  # 5 minutes
        self.correlated_events: deque = deque(maxlen=1000)

        # Notification channels
        self.alert_channels: Dict[AlertChannel, Dict[str, Any]] = {}

        # Enhanced configuration
        self.behavioral_analysis_enabled = True
        self.ip_reputation_enabled = True
        self.geolocation_analysis_enabled = True
        self.ml_anomaly_detection_enabled = True
        
        # Initialize default threat patterns
        self._initialize_threat_patterns()
        
        # Start background monitoring
        self._start_monitoring_tasks()
    
    def _initialize_threat_patterns(self):
        """Initialize default security threat patterns."""
        patterns = [
            ThreatPattern(
                name="brute_force_attack",
                description="Multiple failed login attempts from same IP",
                pattern_type="frequency",
                conditions={"event_type": "failed_login", "threshold": 10, "window": 300},
                threat_level=ThreatLevel.HIGH,
                threshold_count=10
            ),
            ThreatPattern(
                name="credential_stuffing",
                description="Failed logins across multiple accounts from same IP",
                pattern_type="correlation",
                conditions={"event_type": "failed_login", "unique_users": 5, "window": 600},
                threat_level=ThreatLevel.HIGH,
                threshold_count=5
            ),
            ThreatPattern(
                name="suspicious_api_usage",
                description="Unusual API access patterns",
                pattern_type="anomaly",
                conditions={"event_type": "api_access", "rate_threshold": 100, "window": 60},
                threat_level=ThreatLevel.MEDIUM,
                threshold_count=100
            ),
            ThreatPattern(
                name="privilege_escalation",
                description="Attempts to access unauthorized resources",
                pattern_type="sequence",
                conditions={"event_type": "authorization_failure", "threshold": 5, "window": 300},
                threat_level=ThreatLevel.CRITICAL,
                threshold_count=5
            ),
            ThreatPattern(
                name="data_exfiltration",
                description="Large volume data access patterns",
                pattern_type="anomaly",
                conditions={"event_type": "data_access", "volume_threshold": 1000000, "window": 300},
                threat_level=ThreatLevel.CRITICAL,
                threshold_count=1
            ),
            ThreatPattern(
                name="malicious_file_upload",
                description="Suspicious file upload attempts",
                pattern_type="frequency",
                conditions={"event_type": "file_upload_blocked", "threshold": 3, "window": 300},
                threat_level=ThreatLevel.HIGH,
                threshold_count=3
            )
        ]
        
        for pattern in patterns:
            self.threat_patterns[pattern.name] = pattern
    
    def configure_alert_channel(self, channel: AlertChannel, config: Dict[str, Any]):
        """Configure alert notification channel."""
        self.alert_channels[channel] = config
        logger.info(f"Configured alert channel: {channel.value}")
    
    def record_security_event(self, event_type: str, details: Dict[str, Any], 
                            source_ip: Optional[str] = None, user_id: Optional[str] = None):
        """Record and analyze security event."""
        # Record in base monitor
        self.base_monitor.record_security_event(event_type, details)
        
        # Create enhanced event record
        event = {
            "id": hashlib.md5(f"{event_type}_{time.time()}_{source_ip}".encode()).hexdigest()[:16],
            "timestamp": time.time(),
            "event_type": event_type,
            "source_ip": source_ip,
            "user_id": user_id,
            "details": details
        }
        
        # Add to correlation window
        self.correlated_events.append(event)
        
        # Update security metrics
        self.security_metrics[f"events_{event_type}"] += 1
        self.security_metrics["total_events"] += 1
        
        # Analyze for threat patterns
        self._analyze_threat_patterns(event)
        
        # Log enhanced event
        logger.info(f"Security event recorded: {event_type}", extra={
            "security_event": event,
            "correlation_id": event["id"]
        })
    
    def _analyze_threat_patterns(self, event: Dict[str, Any]):
        """Analyze event against known threat patterns."""
        current_time = time.time()
        
        for pattern_name, pattern in self.threat_patterns.items():
            if not pattern.enabled:
                continue
            
            try:
                if self._matches_pattern(event, pattern, current_time):
                    self._trigger_security_alert(pattern_name, pattern, event)
            except Exception as e:
                logger.error(f"Error analyzing threat pattern {pattern_name}: {e}")
    
    def _matches_pattern(self, event: Dict[str, Any], pattern: ThreatPattern, current_time: float) -> bool:
        """Check if event matches threat pattern."""
        conditions = pattern.conditions
        window_start = current_time - pattern.detection_window_seconds
        
        # Get relevant events in time window
        relevant_events = [
            e for e in self.correlated_events
            if e["timestamp"] >= window_start and e["event_type"] == conditions.get("event_type", event["event_type"])
        ]
        
        if pattern.pattern_type == "frequency":
            # Check if event frequency exceeds threshold
            if event["event_type"] == conditions.get("event_type"):
                same_ip_events = [e for e in relevant_events if e.get("source_ip") == event.get("source_ip")]
                return len(same_ip_events) >= conditions.get("threshold", pattern.threshold_count)
        
        elif pattern.pattern_type == "correlation":
            # Check for correlated events across multiple entities
            if event["event_type"] == conditions.get("event_type"):
                same_ip_events = [e for e in relevant_events if e.get("source_ip") == event.get("source_ip")]
                unique_users = len(set(e.get("user_id") for e in same_ip_events if e.get("user_id")))
                return unique_users >= conditions.get("unique_users", 5)
        
        elif pattern.pattern_type == "anomaly":
            # Check for anomalous behavior
            if event["event_type"] == conditions.get("event_type"):
                if "rate_threshold" in conditions:
                    return len(relevant_events) >= conditions["rate_threshold"]
                elif "volume_threshold" in conditions:
                    total_volume = sum(e.get("details", {}).get("volume", 0) for e in relevant_events)
                    return total_volume >= conditions["volume_threshold"]
        
        elif pattern.pattern_type == "sequence":
            # Check for sequential patterns
            if event["event_type"] == conditions.get("event_type"):
                same_user_events = [e for e in relevant_events if e.get("user_id") == event.get("user_id")]
                return len(same_user_events) >= conditions.get("threshold", pattern.threshold_count)
        
        return False
    
    def _trigger_security_alert(self, pattern_name: str, pattern: ThreatPattern, triggering_event: Dict[str, Any]):
        """Trigger security alert for detected threat pattern."""
        alert_id = hashlib.md5(f"{pattern_name}_{triggering_event['id']}_{time.time()}".encode()).hexdigest()[:16]
        
        # Check if similar alert is already active
        existing_alert = self._find_similar_active_alert(pattern_name, triggering_event)
        if existing_alert:
            logger.debug(f"Similar alert already active: {existing_alert.id}")
            return
        
        alert = SecurityAlert(
            id=alert_id,
            title=f"Security Threat Detected: {pattern.name.replace('_', ' ').title()}",
            description=pattern.description,
            threat_level=pattern.threat_level,
            event_type=pattern_name,
            source_ip=triggering_event.get("source_ip"),
            user_id=triggering_event.get("user_id"),
            details={
                "pattern": pattern_name,
                "triggering_event": triggering_event,
                "detection_time": time.time(),
                "threat_score": self._calculate_threat_score(pattern, triggering_event)
            }
        )
        
        # Store alert
        self.active_alerts[alert_id] = alert
        self.alert_history.append(alert)
        
        # Update metrics
        self.security_metrics[f"alerts_{pattern.threat_level.value}"] += 1
        self.security_metrics["total_alerts"] += 1
        
        # Send notifications
        try:
            asyncio.create_task(self._send_alert_notifications(alert))
        except RuntimeError:
            # No event loop running, skip async notifications in test environment
            logger.debug("No event loop available for alert notifications")
        
        # Log alert
        logger.warning(f"Security alert triggered: {alert.title}", extra={
            "security_alert": asdict(alert),
            "alert_id": alert_id,
            "threat_level": pattern.threat_level.value
        })
    
    def _find_similar_active_alert(self, pattern_name: str, event: Dict[str, Any]) -> Optional[SecurityAlert]:
        """Find similar active alert to avoid duplicates."""
        for alert in self.active_alerts.values():
            if (alert.event_type == pattern_name and 
                alert.source_ip == event.get("source_ip") and
                not alert.resolved and
                time.time() - alert.timestamp < 3600):  # Within last hour
                return alert
        return None
    
    def _calculate_threat_score(self, pattern: ThreatPattern, event: Dict[str, Any]) -> float:
        """Calculate threat score based on pattern and event context."""
        base_score = {
            ThreatLevel.LOW: 25,
            ThreatLevel.MEDIUM: 50,
            ThreatLevel.HIGH: 75,
            ThreatLevel.CRITICAL: 100
        }[pattern.threat_level]
        
        # Adjust based on event context
        score_modifiers = 0
        
        # Source IP reputation (simplified)
        if event.get("source_ip"):
            if self._is_known_malicious_ip(event["source_ip"]):
                score_modifiers += 20
        
        # User context
        if event.get("user_id"):
            if self._is_privileged_user(event["user_id"]):
                score_modifiers += 15
        
        # Time-based factors
        current_hour = datetime.now().hour
        if current_hour < 6 or current_hour > 22:  # Off-hours
            score_modifiers += 10
        
        return min(100, base_score + score_modifiers)
    
    def _is_known_malicious_ip(self, ip: str) -> bool:
        """Check if IP is known to be malicious (simplified implementation)."""
        # In production, this would check against threat intelligence feeds
        malicious_patterns = ["192.168.", "10.", "172.16."]  # Private IPs for demo
        return any(ip.startswith(pattern) for pattern in malicious_patterns)
    
    def _is_privileged_user(self, user_id: str) -> bool:
        """Check if user has privileged access."""
        # In production, this would check user roles/permissions
        privileged_indicators = ["admin", "root", "system"]
        return any(indicator in user_id.lower() for indicator in privileged_indicators)
    
    async def _send_alert_notifications(self, alert: SecurityAlert):
        """Send alert notifications through configured channels."""
        for channel, config in self.alert_channels.items():
            try:
                if channel == AlertChannel.EMAIL:
                    await self._send_email_alert(alert, config)
                elif channel == AlertChannel.WEBHOOK:
                    await self._send_webhook_alert(alert, config)
                elif channel == AlertChannel.LOG:
                    await self._send_log_alert(alert, config)
                # Add more channels as needed
            except Exception as e:
                logger.error(f"Failed to send alert via {channel.value}: {e}")
    
    async def _send_email_alert(self, alert: SecurityAlert, config: Dict[str, Any]):
        """Send email alert notification."""
        if not all(k in config for k in ["smtp_server", "smtp_port", "username", "password", "recipients"]):
            logger.warning("Email alert configuration incomplete")
            return
        
        try:
            msg = MIMEMultipart()
            msg["From"] = config["username"]
            msg["To"] = ", ".join(config["recipients"])
            msg["Subject"] = f"[SECURITY ALERT] {alert.title}"
            
            body = f"""
Security Alert Details:
- Alert ID: {alert.id}
- Threat Level: {alert.threat_level.value.upper()}
- Description: {alert.description}
- Source IP: {alert.source_ip or 'Unknown'}
- User ID: {alert.user_id or 'Unknown'}
- Timestamp: {datetime.fromtimestamp(alert.timestamp)}
- Threat Score: {alert.details.get('threat_score', 'N/A')}

Event Details:
{json.dumps(alert.details, indent=2)}

Please investigate immediately if threat level is HIGH or CRITICAL.
            """
            
            msg.attach(MIMEText(body, "plain"))
            
            server = smtplib.SMTP(config["smtp_server"], config["smtp_port"])
            server.starttls()
            server.login(config["username"], config["password"])
            server.send_message(msg)
            server.quit()
            
            logger.info(f"Email alert sent for {alert.id}")
        except Exception as e:
            logger.error(f"Failed to send email alert: {e}")
    
    async def _send_webhook_alert(self, alert: SecurityAlert, config: Dict[str, Any]):
        """Send webhook alert notification."""
        import aiohttp
        
        if "url" not in config:
            logger.warning("Webhook alert configuration incomplete")
            return
        
        try:
            payload = {
                "alert_id": alert.id,
                "title": alert.title,
                "description": alert.description,
                "threat_level": alert.threat_level.value,
                "timestamp": alert.timestamp,
                "source_ip": alert.source_ip,
                "user_id": alert.user_id,
                "details": alert.details
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    config["url"],
                    json=payload,
                    headers=config.get("headers", {}),
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    if response.status == 200:
                        logger.info(f"Webhook alert sent for {alert.id}")
                    else:
                        logger.error(f"Webhook alert failed with status {response.status}")
        except Exception as e:
            logger.error(f"Failed to send webhook alert: {e}")
    
    async def _send_log_alert(self, alert: SecurityAlert, config: Dict[str, Any]):
        """Send log-based alert notification."""
        log_level = config.get("level", "warning").lower()
        
        alert_message = f"SECURITY ALERT: {alert.title} | Level: {alert.threat_level.value} | ID: {alert.id}"
        
        if log_level == "critical":
            logger.critical(alert_message, extra={"security_alert": asdict(alert)})
        elif log_level == "error":
            logger.error(alert_message, extra={"security_alert": asdict(alert)})
        else:
            logger.warning(alert_message, extra={"security_alert": asdict(alert)})
    
    def _start_monitoring_tasks(self):
        """Start background monitoring tasks."""
        # Start alert cleanup task
        threading.Thread(target=self._alert_cleanup_worker, daemon=True).start()
        
        # Start metrics collection task
        threading.Thread(target=self._metrics_collection_worker, daemon=True).start()
    
    def _alert_cleanup_worker(self):
        """Background worker to clean up old resolved alerts."""
        while True:
            try:
                current_time = time.time()
                cleanup_threshold = current_time - (24 * 3600)  # 24 hours
                
                # Remove old resolved alerts
                alerts_to_remove = [
                    alert_id for alert_id, alert in self.active_alerts.items()
                    if alert.resolved and alert.resolved_at and alert.resolved_at < cleanup_threshold
                ]
                
                for alert_id in alerts_to_remove:
                    del self.active_alerts[alert_id]
                
                if alerts_to_remove:
                    logger.info(f"Cleaned up {len(alerts_to_remove)} old resolved alerts")
                
                time.sleep(3600)  # Run every hour
            except Exception as e:
                logger.error(f"Error in alert cleanup worker: {e}")
                time.sleep(300)  # Wait 5 minutes on error
    
    def _metrics_collection_worker(self):
        """Background worker to collect and report security metrics."""
        while True:
            try:
                # Report security metrics
                for metric_name, value in self.security_metrics.items():
                    metrics_logger.record_gauge(f"security.{metric_name}", value)
                
                # Report active alerts by threat level
                for threat_level in ThreatLevel:
                    active_count = sum(
                        1 for alert in self.active_alerts.values()
                        if not alert.resolved and alert.threat_level == threat_level
                    )
                    metrics_logger.record_gauge(f"security.active_alerts.{threat_level.value}", active_count)
                
                time.sleep(60)  # Report every minute
            except Exception as e:
                logger.error(f"Error in metrics collection worker: {e}")
                time.sleep(60)

    def create_alert(self, title: str, description: str, threat_level: ThreatLevel,
                    source_event: Dict[str, Any], affected_resources: list = None) -> str:
        """Create a new security alert."""
        alert_id = hashlib.md5(f"{title}_{time.time()}".encode()).hexdigest()[:16]

        alert = SecurityAlert(
            id=alert_id,
            title=title,
            description=description,
            threat_level=threat_level,
            event_type=source_event.get("event_type", "manual"),
            source_ip=source_event.get("ip_address", "unknown"),
            user_id=source_event.get("user_id"),
            timestamp=time.time(),
            details=source_event,
            resolved=False
        )

        self.active_alerts[alert_id] = alert

        # Send notifications asynchronously
        try:
            import asyncio
            asyncio.create_task(self._send_alert_notifications(alert))
        except Exception as e:
            logger.error(f"Failed to send alert notifications: {e}")

        logger.info(f"Created security alert {alert_id}: {title}")
        return alert_id

    def resolve_alert(self, alert_id: str, resolution_notes: str = ""):
        """Resolve a security alert."""
        if alert_id in self.active_alerts:
            alert = self.active_alerts[alert_id]
            alert.resolved = True
            alert.resolved_at = time.time()
            alert.resolution_notes = resolution_notes
            
            logger.info(f"Security alert resolved: {alert_id}", extra={
                "alert_id": alert_id,
                "resolution_notes": resolution_notes
            })
            
            return True
        return False
    
    def get_security_dashboard_data(self) -> Dict[str, Any]:
        """Get security dashboard data."""
        current_time = time.time()
        last_24h = current_time - (24 * 3600)
        
        # Active alerts by threat level
        active_alerts_by_level = defaultdict(int)
        for alert in self.active_alerts.values():
            if not alert.resolved:
                active_alerts_by_level[alert.threat_level.value] += 1
        
        # Recent events (last 24 hours)
        recent_events = [
            event for event in self.correlated_events
            if event["timestamp"] >= last_24h
        ]
        
        # Event types distribution
        event_types = defaultdict(int)
        for event in recent_events:
            event_types[event["event_type"]] += 1
        
        return {
            "active_alerts": dict(active_alerts_by_level),
            "total_active_alerts": len([a for a in self.active_alerts.values() if not a.resolved]),
            "recent_events_24h": len(recent_events),
            "event_types_24h": dict(event_types),
            "security_metrics": dict(self.security_metrics),
            "threat_patterns_enabled": len([p for p in self.threat_patterns.values() if p.enabled]),
            "last_updated": current_time
        }

    def analyze_user_behavior(self, user_id: str, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze user behavior for anomaly detection."""
        if not self.behavioral_analysis_enabled:
            return {"anomaly_score": 0, "anomalies": []}

        profile = self.user_behavior_profiles.get(user_id, {
            "login_times": [],
            "ip_addresses": set(),
            "user_agents": set(),
            "request_patterns": defaultdict(int),
            "last_activity": None,
            "baseline_established": False
        })

        anomalies = []
        anomaly_score = 0

        # Analyze login time patterns
        current_hour = datetime.now().hour
        if profile["baseline_established"]:
            typical_hours = set(profile.get("typical_login_hours", []))
            if current_hour not in typical_hours:
                anomalies.append("unusual_login_time")
                anomaly_score += 20

        # Analyze IP address patterns
        current_ip = event_data.get("ip_address")
        if current_ip and profile["baseline_established"]:
            if current_ip not in profile["ip_addresses"]:
                anomalies.append("new_ip_address")
                anomaly_score += 30

        # Analyze user agent patterns
        current_ua = event_data.get("user_agent")
        if current_ua and profile["baseline_established"]:
            if current_ua not in profile["user_agents"]:
                anomalies.append("new_user_agent")
                anomaly_score += 25

        # Update profile
        profile["login_times"].append(current_hour)
        if current_ip:
            profile["ip_addresses"].add(current_ip)
        if current_ua:
            profile["user_agents"].add(current_ua)
        profile["last_activity"] = datetime.now()

        # Establish baseline after sufficient data
        if len(profile["login_times"]) >= 10:
            profile["baseline_established"] = True
            profile["typical_login_hours"] = list(set(profile["login_times"]))

        self.user_behavior_profiles[user_id] = profile

        return {
            "anomaly_score": anomaly_score,
            "anomalies": anomalies,
            "profile_established": profile["baseline_established"]
        }

    def check_ip_reputation(self, ip_address: str) -> Dict[str, Any]:
        """Check IP address reputation and threat intelligence."""
        if not self.ip_reputation_enabled:
            return {"reputation_score": 50, "threat_indicators": []}

        # Check cache first
        if ip_address in self.ip_reputation_cache:
            cached_data = self.ip_reputation_cache[ip_address]
            if (datetime.now() - cached_data["timestamp"]).seconds < 3600:  # 1 hour cache
                return cached_data["data"]

        threat_indicators = []
        reputation_score = 50  # Neutral score

        # Check for known malicious patterns
        if self._is_tor_exit_node(ip_address):
            threat_indicators.append("tor_exit_node")
            reputation_score -= 30

        if self._is_vpn_ip(ip_address):
            threat_indicators.append("vpn_service")
            reputation_score -= 10

        if self._is_cloud_provider(ip_address):
            threat_indicators.append("cloud_provider")
            reputation_score -= 5

        # Check against internal blacklist
        if self._is_blacklisted_ip(ip_address):
            threat_indicators.append("internal_blacklist")
            reputation_score -= 50

        result = {
            "reputation_score": max(0, reputation_score),
            "threat_indicators": threat_indicators,
            "risk_level": "high" if reputation_score < 20 else "medium" if reputation_score < 40 else "low"
        }

        # Cache result
        self.ip_reputation_cache[ip_address] = {
            "timestamp": datetime.now(),
            "data": result
        }

        return result

    def detect_attack_patterns(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Detect known attack patterns in event data."""
        detected_attacks = []
        confidence_scores = {}

        # SQL Injection detection
        if self._detect_sql_injection(event_data):
            detected_attacks.append("sql_injection")
            confidence_scores["sql_injection"] = 85

        # XSS detection
        if self._detect_xss_attack(event_data):
            detected_attacks.append("xss_attack")
            confidence_scores["xss_attack"] = 80

        # Command injection detection
        if self._detect_command_injection(event_data):
            detected_attacks.append("command_injection")
            confidence_scores["command_injection"] = 90

        # Directory traversal detection
        if self._detect_directory_traversal(event_data):
            detected_attacks.append("directory_traversal")
            confidence_scores["directory_traversal"] = 75

        # Brute force detection
        if self._detect_brute_force(event_data):
            detected_attacks.append("brute_force")
            confidence_scores["brute_force"] = 70

        return {
            "detected_attacks": detected_attacks,
            "confidence_scores": confidence_scores,
            "overall_threat_level": "high" if any(score > 80 for score in confidence_scores.values()) else "medium" if detected_attacks else "low"
        }

    def _is_tor_exit_node(self, ip_address: str) -> bool:
        """Check if IP is a known Tor exit node."""
        # Simplified check - in production, use actual Tor exit node list
        tor_patterns = ["tor", "exit", "relay"]
        return any(pattern in ip_address.lower() for pattern in tor_patterns)

    def _is_vpn_ip(self, ip_address: str) -> bool:
        """Check if IP belongs to a VPN service."""
        # Simplified check - in production, use VPN IP databases
        vpn_ranges = ["10.", "172.", "192.168."]
        return any(ip_address.startswith(range_) for range_ in vpn_ranges)

    def _is_cloud_provider(self, ip_address: str) -> bool:
        """Check if IP belongs to a cloud provider."""
        # Simplified check - in production, use cloud provider IP ranges
        return False  # Placeholder

    def _is_blacklisted_ip(self, ip_address: str) -> bool:
        """Check if IP is in internal blacklist."""
        blacklisted_ips = getattr(self, '_blacklisted_ips', set())
        return ip_address in blacklisted_ips

    def _detect_sql_injection(self, event_data: Dict[str, Any]) -> bool:
        """Detect SQL injection patterns."""
        sql_patterns = ["union select", "drop table", "'; --", "or 1=1"]
        content = str(event_data.get("request_body", "")).lower()
        return any(pattern in content for pattern in sql_patterns)

    def _detect_xss_attack(self, event_data: Dict[str, Any]) -> bool:
        """Detect XSS attack patterns."""
        xss_patterns = ["<script>", "javascript:", "onerror=", "onload="]
        content = str(event_data.get("request_body", "")).lower()
        return any(pattern in content for pattern in xss_patterns)

    def _detect_command_injection(self, event_data: Dict[str, Any]) -> bool:
        """Detect command injection patterns."""
        cmd_patterns = ["; rm -rf", "&& cat", "| nc ", "`whoami`"]
        content = str(event_data.get("request_body", "")).lower()
        return any(pattern in content for pattern in cmd_patterns)

    def _detect_directory_traversal(self, event_data: Dict[str, Any]) -> bool:
        """Detect directory traversal patterns."""
        traversal_patterns = ["../", "..\\", "%2e%2e%2f", "....//"]
        content = str(event_data.get("request_path", "")).lower()
        return any(pattern in content for pattern in traversal_patterns)

    def _detect_brute_force(self, event_data: Dict[str, Any]) -> bool:
        """Detect brute force attack patterns."""
        ip_address = event_data.get("ip_address")
        if not ip_address:
            return False

        # Count failed attempts from this IP in the last 5 minutes
        recent_failures = 0
        current_time = datetime.now()

        for event in self.correlated_events:
            if (event.get("ip_address") == ip_address and
                event.get("event_type") == "failed_login" and
                (current_time - event.get("timestamp", current_time)).seconds < 300):
                recent_failures += 1

        return recent_failures >= 5


# Global instance
advanced_security_monitor = AdvancedSecurityMonitor()

def get_advanced_security_monitor() -> AdvancedSecurityMonitor:
    """Get the global advanced security monitor instance."""
    return advanced_security_monitor
