"""
Security Dashboard API Endpoints
Provides security monitoring, alerting, and dashboard functionality.
"""

from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Body
from pydantic import BaseModel, Field
from datetime import datetime

from app.core.security import get_current_user
from app.core.advanced_security_monitoring import (
    get_advanced_security_monitor, SecurityAlert, ThreatLevel, AlertChannel, ThreatPattern
)
from app.database.models import User

router = APIRouter()


class AlertResponse(BaseModel):
    """Security alert response model."""
    id: str
    title: str
    description: str
    threat_level: str
    event_type: str
    source_ip: Optional[str] = None
    user_id: Optional[str] = None
    timestamp: float
    resolved: bool
    resolved_at: Optional[float] = None
    resolution_notes: Optional[str] = None
    threat_score: Optional[float] = None


class DashboardResponse(BaseModel):
    """Security dashboard response model."""
    active_alerts: Dict[str, int]
    total_active_alerts: int
    recent_events_24h: int
    event_types_24h: Dict[str, int]
    security_metrics: Dict[str, Any]
    threat_patterns_enabled: int
    last_updated: float


class AlertChannelConfig(BaseModel):
    """Alert channel configuration model."""
    channel: str = Field(..., description="Alert channel type (email, webhook, log)")
    config: Dict[str, Any] = Field(..., description="Channel-specific configuration")


class ResolveAlertRequest(BaseModel):
    """Resolve alert request model."""
    resolution_notes: str = Field("", description="Notes about alert resolution")


class ThreatPatternResponse(BaseModel):
    """Threat pattern response model."""
    name: str
    description: str
    pattern_type: str
    threat_level: str
    enabled: bool
    detection_window_seconds: int
    threshold_count: int


@router.get("/dashboard", response_model=DashboardResponse)
async def get_security_dashboard(
    current_user: User = Depends(get_current_user)
):
    """Get security dashboard overview data."""
    try:
        monitor = get_advanced_security_monitor()
        dashboard_data = monitor.get_security_dashboard_data()
        
        return DashboardResponse(**dashboard_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get dashboard data: {str(e)}")


@router.get("/alerts", response_model=List[AlertResponse])
async def get_security_alerts(
    resolved: Optional[bool] = Query(None, description="Filter by resolved status"),
    threat_level: Optional[str] = Query(None, description="Filter by threat level"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of alerts to return"),
    current_user: User = Depends(get_current_user)
):
    """Get security alerts with optional filtering."""
    try:
        monitor = get_advanced_security_monitor()
        alerts = list(monitor.active_alerts.values())
        
        # Apply filters
        if resolved is not None:
            alerts = [alert for alert in alerts if alert.resolved == resolved]
        
        if threat_level:
            try:
                level_filter = ThreatLevel(threat_level.lower())
                alerts = [alert for alert in alerts if alert.threat_level == level_filter]
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid threat level: {threat_level}")
        
        # Sort by timestamp (newest first) and limit
        alerts = sorted(alerts, key=lambda x: x.timestamp, reverse=True)[:limit]
        
        # Convert to response format
        alert_responses = []
        for alert in alerts:
            alert_responses.append(AlertResponse(
                id=alert.id,
                title=alert.title,
                description=alert.description,
                threat_level=alert.threat_level.value,
                event_type=alert.event_type,
                source_ip=alert.source_ip,
                user_id=alert.user_id,
                timestamp=alert.timestamp,
                resolved=alert.resolved,
                resolved_at=alert.resolved_at,
                resolution_notes=alert.resolution_notes,
                threat_score=alert.details.get('threat_score')
            ))
        
        return alert_responses
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get alerts: {str(e)}")


@router.get("/alerts/{alert_id}", response_model=AlertResponse)
async def get_security_alert(
    alert_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get specific security alert by ID."""
    try:
        monitor = get_advanced_security_monitor()
        
        if alert_id not in monitor.active_alerts:
            raise HTTPException(status_code=404, detail="Alert not found")
        
        alert = monitor.active_alerts[alert_id]
        
        return AlertResponse(
            id=alert.id,
            title=alert.title,
            description=alert.description,
            threat_level=alert.threat_level.value,
            event_type=alert.event_type,
            source_ip=alert.source_ip,
            user_id=alert.user_id,
            timestamp=alert.timestamp,
            resolved=alert.resolved,
            resolved_at=alert.resolved_at,
            resolution_notes=alert.resolution_notes,
            threat_score=alert.details.get('threat_score')
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get alert: {str(e)}")


@router.post("/alerts/{alert_id}/resolve")
async def resolve_security_alert(
    alert_id: str,
    request: ResolveAlertRequest,
    current_user: User = Depends(get_current_user)
):
    """Resolve a security alert."""
    try:
        monitor = get_advanced_security_monitor()
        
        if monitor.resolve_alert(alert_id, request.resolution_notes):
            return {"message": "Alert resolved successfully", "alert_id": alert_id}
        else:
            raise HTTPException(status_code=404, detail="Alert not found")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to resolve alert: {str(e)}")


@router.get("/threat-patterns", response_model=List[ThreatPatternResponse])
async def get_threat_patterns(
    current_user: User = Depends(get_current_user)
):
    """Get configured threat detection patterns."""
    try:
        monitor = get_advanced_security_monitor()
        patterns = []
        
        for pattern in monitor.threat_patterns.values():
            patterns.append(ThreatPatternResponse(
                name=pattern.name,
                description=pattern.description,
                pattern_type=pattern.pattern_type,
                threat_level=pattern.threat_level.value,
                enabled=pattern.enabled,
                detection_window_seconds=pattern.detection_window_seconds,
                threshold_count=pattern.threshold_count
            ))
        
        return patterns
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get threat patterns: {str(e)}")


@router.post("/threat-patterns/{pattern_name}/toggle")
async def toggle_threat_pattern(
    pattern_name: str,
    current_user: User = Depends(get_current_user)
):
    """Enable or disable a threat detection pattern."""
    try:
        monitor = get_advanced_security_monitor()
        
        if pattern_name not in monitor.threat_patterns:
            raise HTTPException(status_code=404, detail="Threat pattern not found")
        
        pattern = monitor.threat_patterns[pattern_name]
        pattern.enabled = not pattern.enabled
        
        return {
            "message": f"Threat pattern {'enabled' if pattern.enabled else 'disabled'}",
            "pattern_name": pattern_name,
            "enabled": pattern.enabled
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to toggle threat pattern: {str(e)}")


@router.post("/alert-channels")
async def configure_alert_channel(
    config: AlertChannelConfig,
    current_user: User = Depends(get_current_user)
):
    """Configure alert notification channel."""
    try:
        monitor = get_advanced_security_monitor()
        
        # Validate channel type
        try:
            channel = AlertChannel(config.channel.lower())
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid channel type: {config.channel}")
        
        # Configure the channel
        monitor.configure_alert_channel(channel, config.config)
        
        return {
            "message": "Alert channel configured successfully",
            "channel": config.channel,
            "configured": True
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to configure alert channel: {str(e)}")


@router.get("/metrics")
async def get_security_metrics(
    current_user: User = Depends(get_current_user)
):
    """Get detailed security metrics."""
    try:
        monitor = get_advanced_security_monitor()
        
        # Get current metrics
        metrics = dict(monitor.security_metrics)
        
        # Add real-time statistics
        current_time = datetime.now()
        metrics.update({
            "monitoring_uptime_hours": (current_time.timestamp() - monitor.ai_monitor.start_time) / 3600,
            "active_threat_patterns": len([p for p in monitor.threat_patterns.values() if p.enabled]),
            "configured_alert_channels": len(monitor.alert_channels),
            "correlation_window_events": len(monitor.correlated_events),
            "alert_history_size": len(monitor.alert_history)
        })
        
        return {
            "metrics": metrics,
            "timestamp": current_time.timestamp(),
            "status": "operational"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get security metrics: {str(e)}")


@router.post("/test-alert")
async def trigger_test_alert(
    threat_level: str = Query("medium", description="Test alert threat level"),
    current_user: User = Depends(get_current_user)
):
    """Trigger a test security alert for testing notification channels."""
    try:
        monitor = get_advanced_security_monitor()
        
        # Validate threat level
        try:
            level = ThreatLevel(threat_level.lower())
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid threat level: {threat_level}")
        
        # Create test event
        test_event = {
            "id": f"test_{int(datetime.now().timestamp())}",
            "timestamp": datetime.now().timestamp(),
            "event_type": "test_alert",
            "source_ip": "127.0.0.1",
            "user_id": current_user.email,
            "details": {
                "test": True,
                "triggered_by": current_user.email,
                "message": "This is a test security alert"
            }
        }
        
        # Record the test event
        monitor.record_security_event(
            "test_alert",
            test_event["details"],
            test_event["source_ip"],
            test_event["user_id"]
        )
        
        return {
            "message": "Test alert triggered successfully",
            "event_id": test_event["id"],
            "threat_level": threat_level
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to trigger test alert: {str(e)}")


@router.get("/health")
async def security_monitoring_health():
    """Get security monitoring system health status."""
    try:
        monitor = get_advanced_security_monitor()
        
        return {
            "status": "healthy",
            "monitoring_active": True,
            "threat_patterns_loaded": len(monitor.threat_patterns),
            "alert_channels_configured": len(monitor.alert_channels),
            "active_alerts": len([a for a in monitor.active_alerts.values() if not a.resolved]),
            "last_event_time": max([e["timestamp"] for e in monitor.correlated_events]) if monitor.correlated_events else None,
            "uptime_seconds": datetime.now().timestamp() - monitor.ai_monitor.start_time
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "monitoring_active": False
        }
