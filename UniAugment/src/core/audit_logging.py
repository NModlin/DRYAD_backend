"""
Comprehensive Audit Logging System for DRYAD.AI Backend
Provides security audit logging, compliance logging, and security event tracking.
"""

import json
import time
import hashlib
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Union
from enum import Enum
from dataclasses import dataclass, asdict
from pathlib import Path
import asyncio
import threading
from queue import Queue, Empty
import os

from app.core.logging_config import get_logger

logger = get_logger(__name__)


class AuditEventType(Enum):
    """Types of audit events."""
    # Authentication Events
    LOGIN_SUCCESS = "login_success"
    LOGIN_FAILURE = "login_failure"
    LOGOUT = "logout"
    TOKEN_REFRESH = "token_refresh"
    TOKEN_REVOKED = "token_revoked"
    
    # Authorization Events
    ACCESS_GRANTED = "access_granted"
    ACCESS_DENIED = "access_denied"
    PERMISSION_ESCALATION = "permission_escalation"
    
    # Data Access Events
    DATA_READ = "data_read"
    DATA_WRITE = "data_write"
    DATA_DELETE = "data_delete"
    DATA_EXPORT = "data_export"
    PII_ACCESS = "pii_access"
    
    # Security Events
    SECURITY_VIOLATION = "security_violation"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    IP_BLOCKED = "ip_blocked"
    ENCRYPTION_FAILURE = "encryption_failure"
    
    # System Events
    SYSTEM_START = "system_start"
    SYSTEM_SHUTDOWN = "system_shutdown"
    CONFIG_CHANGE = "config_change"
    
    # API Events
    API_KEY_CREATED = "api_key_created"
    API_KEY_REVOKED = "api_key_revoked"
    API_REQUEST = "api_request"
    
    # Compliance Events
    GDPR_REQUEST = "gdpr_request"
    DATA_RETENTION_ACTION = "data_retention_action"
    COMPLIANCE_VIOLATION = "compliance_violation"


class AuditSeverity(Enum):
    """Severity levels for audit events."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class AuditEvent:
    """Audit event data structure."""
    event_id: str
    event_type: AuditEventType
    severity: AuditSeverity
    timestamp: datetime
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    resource: Optional[str] = None
    action: Optional[str] = None
    outcome: str = "success"  # success, failure, error
    details: Dict[str, Any] = None
    risk_score: int = 0  # 0-100
    compliance_tags: List[str] = None
    
    def __post_init__(self):
        if self.details is None:
            self.details = {}
        if self.compliance_tags is None:
            self.compliance_tags = []


class AuditLogger:
    """Comprehensive audit logging system."""
    
    def __init__(self, log_directory: str = "logs/audit"):
        self.log_directory = Path(log_directory)
        self.log_directory.mkdir(parents=True, exist_ok=True)
        
        # Event queue for async processing
        self.event_queue = Queue()
        self.processing_thread = None
        self.shutdown_event = threading.Event()
        
        # Configuration
        self.max_log_file_size = 100 * 1024 * 1024  # 100MB
        self.max_log_files = 10
        self.batch_size = 100
        self.flush_interval = 30  # seconds
        
        # Start background processing
        self.start_processing()
        
        logger.info("Audit logging system initialized")
    
    def start_processing(self):
        """Start background thread for processing audit events."""
        if self.processing_thread is None or not self.processing_thread.is_alive():
            self.processing_thread = threading.Thread(
                target=self._process_events,
                daemon=True
            )
            self.processing_thread.start()
    
    def _process_events(self):
        """Background thread to process audit events."""
        events_batch = []
        last_flush = time.time()
        
        while not self.shutdown_event.is_set():
            try:
                # Get events from queue with timeout
                try:
                    event = self.event_queue.get(timeout=1.0)
                    events_batch.append(event)
                except Empty:
                    pass
                
                # Flush batch if it's full or enough time has passed
                current_time = time.time()
                should_flush = (
                    len(events_batch) >= self.batch_size or
                    (events_batch and current_time - last_flush >= self.flush_interval)
                )
                
                if should_flush:
                    self._write_events_batch(events_batch)
                    events_batch.clear()
                    last_flush = current_time
                    
            except Exception as e:
                logger.error(f"Error processing audit events: {e}")
        
        # Flush remaining events on shutdown
        if events_batch:
            self._write_events_batch(events_batch)
    
    def _write_events_batch(self, events: List[AuditEvent]):
        """Write a batch of events to log files."""
        if not events:
            return
        
        try:
            # Group events by date for daily log files
            events_by_date = {}
            for event in events:
                date_str = event.timestamp.strftime("%Y-%m-%d")
                if date_str not in events_by_date:
                    events_by_date[date_str] = []
                events_by_date[date_str].append(event)
            
            # Write each date's events to its log file
            for date_str, date_events in events_by_date.items():
                log_file = self.log_directory / f"audit_{date_str}.jsonl"
                
                with open(log_file, 'a', encoding='utf-8') as f:
                    for event in date_events:
                        event_dict = asdict(event)
                        # Convert enum values to strings
                        event_dict['event_type'] = event.event_type.value
                        event_dict['severity'] = event.severity.value
                        event_dict['timestamp'] = event.timestamp.isoformat()
                        
                        f.write(json.dumps(event_dict) + '\n')
                
                # Rotate log file if it's too large
                self._rotate_log_file_if_needed(log_file)
                
        except Exception as e:
            logger.error(f"Error writing audit events: {e}")
    
    def _rotate_log_file_if_needed(self, log_file: Path):
        """Rotate log file if it exceeds size limit."""
        try:
            if log_file.exists() and log_file.stat().st_size > self.max_log_file_size:
                # Find next rotation number
                rotation_num = 1
                while True:
                    rotated_file = log_file.with_suffix(f'.{rotation_num}.jsonl')
                    if not rotated_file.exists():
                        break
                    rotation_num += 1
                
                # Rotate the file
                log_file.rename(rotated_file)
                
                # Clean up old rotated files
                self._cleanup_old_log_files(log_file.stem)
                
        except Exception as e:
            logger.error(f"Error rotating log file {log_file}: {e}")
    
    def _cleanup_old_log_files(self, base_name: str):
        """Clean up old rotated log files."""
        try:
            # Find all rotated files for this base name
            rotated_files = []
            for file_path in self.log_directory.glob(f"{base_name}.*.jsonl"):
                try:
                    rotation_num = int(file_path.suffix[1:-6])  # Extract number from .N.jsonl
                    rotated_files.append((rotation_num, file_path))
                except ValueError:
                    continue
            
            # Sort by rotation number and remove oldest files
            rotated_files.sort(key=lambda x: x[0], reverse=True)
            for rotation_num, file_path in rotated_files[self.max_log_files:]:
                file_path.unlink()
                logger.info(f"Removed old audit log file: {file_path}")
                
        except Exception as e:
            logger.error(f"Error cleaning up old log files: {e}")
    
    def log_event(self, event: AuditEvent):
        """Log an audit event."""
        try:
            # Add event to queue for async processing
            self.event_queue.put(event)
        except Exception as e:
            logger.error(f"Error queuing audit event: {e}")
    
    def log_authentication_event(self, event_type: AuditEventType, user_id: str = None,
                                ip_address: str = None, user_agent: str = None,
                                outcome: str = "success", details: Dict[str, Any] = None):
        """Log authentication-related events."""
        severity = AuditSeverity.MEDIUM if outcome == "success" else AuditSeverity.HIGH
        
        event = AuditEvent(
            event_id=str(uuid.uuid4()),
            event_type=event_type,
            severity=severity,
            timestamp=datetime.now(timezone.utc),
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            outcome=outcome,
            details=details or {},
            compliance_tags=["authentication", "access_control"]
        )
        
        self.log_event(event)
    
    def log_data_access_event(self, event_type: AuditEventType, user_id: str,
                            resource: str, action: str, ip_address: str = None,
                            outcome: str = "success", details: Dict[str, Any] = None):
        """Log data access events."""
        severity = AuditSeverity.MEDIUM
        if event_type == AuditEventType.PII_ACCESS:
            severity = AuditSeverity.HIGH
        
        event = AuditEvent(
            event_id=str(uuid.uuid4()),
            event_type=event_type,
            severity=severity,
            timestamp=datetime.now(timezone.utc),
            user_id=user_id,
            ip_address=ip_address,
            resource=resource,
            action=action,
            outcome=outcome,
            details=details or {},
            compliance_tags=["data_access", "privacy"]
        )
        
        self.log_event(event)
    
    def log_security_event(self, event_type: AuditEventType, severity: AuditSeverity,
                          ip_address: str = None, user_id: str = None,
                          details: Dict[str, Any] = None, risk_score: int = 0):
        """Log security-related events."""
        event = AuditEvent(
            event_id=str(uuid.uuid4()),
            event_type=event_type,
            severity=severity,
            timestamp=datetime.now(timezone.utc),
            user_id=user_id,
            ip_address=ip_address,
            outcome="detected",
            details=details or {},
            risk_score=risk_score,
            compliance_tags=["security", "threat_detection"]
        )
        
        self.log_event(event)
    
    def shutdown(self):
        """Shutdown the audit logging system."""
        logger.info("Shutting down audit logging system...")
        self.shutdown_event.set()
        
        if self.processing_thread and self.processing_thread.is_alive():
            self.processing_thread.join(timeout=5.0)
        
        logger.info("Audit logging system shutdown complete")


# Global audit logger instance
_audit_logger: Optional[AuditLogger] = None


def get_audit_logger() -> AuditLogger:
    """Get the global audit logger instance."""
    global _audit_logger
    if _audit_logger is None:
        _audit_logger = AuditLogger()
    return _audit_logger


def shutdown_audit_logging():
    """Shutdown the global audit logger."""
    global _audit_logger
    if _audit_logger:
        _audit_logger.shutdown()
        _audit_logger = None
