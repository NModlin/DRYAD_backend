"""
Tool Security and Compliance System

Comprehensive security, access control, and compliance management for tools.
Part of DRYAD.AI Armory System for comprehensive educational tool security.
"""

import logging
import asyncio
import json
import uuid
import hashlib
import time
from typing import Dict, Any, List, Optional, Union, Set, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict, deque
import re
import secrets
import jwt
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from .content_creation import ToolCategory, ToolSecurityLevel

logger = logging.getLogger(__name__)


class SecurityPolicyType(str, Enum):
    """Types of security policies"""
    ACCESS_CONTROL = "access_control"
    DATA_PROTECTION = "data_protection"
    AUDIT_LOGGING = "audit_logging"
    ENCRYPTION = "encryption"
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    COMPLIANCE = "compliance"
    INCIDENT_RESPONSE = "incident_response"


class ComplianceStandard(str, Enum):
    """Compliance standards"""
    GDPR = "gdpr"
    FERPA = "ferpa"
    COPPA = "coppa"
    SOX = "sox"
    HIPAA = "hipaa"
    ISO27001 = "iso27001"
    NIST = "nist"
    CCPA = "ccpa"
    WCAG = "wcag"


class ThreatLevel(str, Enum):
    """Threat levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"
    EMERGENCY = "emergency"


class IncidentStatus(str, Enum):
    """Incident status"""
    DETECTED = "detected"
    INVESTIGATING = "investigating"
    CONTAINED = "contained"
    RESOLVED = "resolved"
    CLOSED = "closed"


class AccessLevel(str, Enum):
    """Access levels"""
    READ = "read"
    WRITE = "write"
    EXECUTE = "execute"
    ADMIN = "admin"
    OWNER = "owner"


class RiskCategory(str, Enum):
    """Risk categories"""
    DATA_BREACH = "data_breach"
    UNAUTHORIZED_ACCESS = "unauthorized_access"
    MALWARE = "malware"
    SOCIAL_ENGINEERING = "social_engineering"
    INSIDER_THREAT = "insider_threat"
    SYSTEM_FAILURE = "system_failure"
    COMPLIANCE_VIOLATION = "compliance_violation"


@dataclass
class SecurityPolicy:
    """Security policy definition"""
    policy_id: str
    name: str
    description: str
    policy_type: SecurityPolicyType
    compliance_standards: List[ComplianceStandard] = field(default_factory=list)
    rules: Dict[str, Any] = field(default_factory=dict)
    enforcement_level: str = "mandatory"  # optional, recommended, mandatory
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    
    def __post_init__(self):
        if not self.policy_id:
            self.policy_id = f"policy_{uuid.uuid4().hex[:8]}"


@dataclass
class AccessControlRule:
    """Access control rule"""
    rule_id: str
    tool_id: str
    principal_id: str
    principal_type: str  # user, role, group
    access_level: AccessLevel
    conditions: Dict[str, Any] = field(default_factory=dict)
    expires_at: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    def __post_init__(self):
        if not self.rule_id:
            self.rule_id = f"rule_{uuid.uuid4().hex[:8]}"


@dataclass
class SecurityIncident:
    """Security incident report"""
    incident_id: str
    title: str
    description: str
    threat_level: ThreatLevel
    category: str
    status: IncidentStatus
    affected_tools: List[str] = field(default_factory=list)
    affected_users: List[str] = field(default_factory=list)
    detected_at: datetime = field(default_factory=datetime.utcnow)
    resolved_at: Optional[datetime] = None
    assigned_to: Optional[str] = None
    resolution_notes: str = ""
    audit_trail: List[Dict[str, Any]] = field(default_factory=list)
    
    def __post_init__(self):
        if not self.incident_id:
            self.incident_id = f"incident_{uuid.uuid4().hex[:8]}"


@dataclass
class AuditLogEntry:
    """Audit log entry"""
    log_id: str
    timestamp: datetime
    user_id: str
    action: str
    resource: str
    resource_id: str
    details: Dict[str, Any] = field(default_factory=dict)
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    result: str = "success"  # success, failure, error
    risk_score: float = 0.0
    
    def __post_init__(self):
        if not self.log_id:
            self.log_id = f"audit_{uuid.uuid4().hex[:8]}"


@dataclass
class RiskAssessment:
    """Risk assessment result"""
    assessment_id: str
    tool_id: str
    risk_level: ThreatLevel
    risk_score: float  # 0.0 to 1.0
    risk_categories: List[RiskCategory] = field(default_factory=list)
    mitigation_strategies: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    assessed_at: datetime = field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None
    
    def __post_init__(self):
        if not self.assessment_id:
            self.assessment_id = f"risk_{uuid.uuid4().hex[:8]}"


@dataclass
class ComplianceReport:
    """Compliance report"""
    report_id: str
    standard: ComplianceStandard
    tool_id: str
    compliance_status: str  # compliant, non_compliant, partial
    compliance_score: float  # 0.0 to 1.0
    violations: List[str] = field(default_factory=list)
    remediation_steps: List[str] = field(default_factory=list)
    assessed_at: datetime = field(default_factory=datetime.utcnow)
    next_review: Optional[datetime] = None
    
    def __post_init__(self):
        if not self.report_id:
            self.report_id = f"compliance_{uuid.uuid4().hex[:8]}"


class SecurityManager:
    """Central security manager for all tool security operations"""
    
    def __init__(self, db_session=None):
        self.access_control_engine = AccessControlEngine()
        self.audit_engine = AuditEngine()
        self.compliance_engine = ComplianceEngine()
        self.incident_engine = IncidentResponseEngine()
        self.risk_engine = RiskAssessmentEngine()
        self.encryption_engine = EncryptionEngine()
        
        # Security management
        self.policies: Dict[str, SecurityPolicy] = {}
        self.access_rules: Dict[str, AccessControlRule] = {}
        self.incidents: Dict[str, SecurityIncident] = {}
        self.risk_assessments: Dict[str, RiskAssessment] = {}
        
        # Note: Async initialization will be done separately to avoid event loop issues
        # asyncio.create_task(self._initialize_security_tools())
    
    async def initialize(self):
        """Initialize the security manager (must be called from async context)"""
        await self._initialize_security_tools()
    
    async def _initialize_security_tools(self):
        """Initialize security tools in the tool registry"""
        security_tools = [
            {
                "name": "Access Controller",
                "description": "Manage tool access control and permissions",
                "category": ToolCategory.CONTENT_CREATION,
                "security_level": ToolSecurityLevel.HIGH_RISK,
                "schema_json": {
                    "openapi": "3.0.0",
                    "info": {"title": "Access Controller", "version": "1.0.0"},
                    "paths": {
                        "/check_access": {
                            "post": {
                                "summary": "Check user access to tool",
                                "parameters": [
                                    {"name": "tool_id", "in": "query", "schema": {"type": "string"}},
                                    {"name": "user_id", "in": "query", "schema": {"type": "string"}},
                                    {"name": "action", "in": "query", "schema": {"type": "string"}}
                                ]
                            }
                        }
                    }
                }
            },
            {
                "name": "Security Monitor",
                "description": "Monitor and analyze security events",
                "category": ToolCategory.CONTENT_CREATION,
                "security_level": ToolSecurityLevel.HIGH_RISK,
                "schema_json": {
                    "openapi": "3.0.0",
                    "info": {"title": "Security Monitor", "version": "1.0.0"},
                    "paths": {
                        "/monitor": {
                            "post": {
                                "summary": "Monitor security events",
                                "parameters": [
                                    {"name": "event_type", "in": "query", "schema": {"type": "string"}},
                                    {"name": "tool_id", "in": "query", "schema": {"type": "string"}}
                                ]
                            }
                        }
                    }
                }
            }
        ]
        
        # Note: In a real implementation, these would be registered with the tool registry
        logger.info("Security tools initialized")
    
    async def check_tool_access(self, tool_id: str, user_id: str, action: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Check if user has access to perform action on tool"""
        try:
            logger.info(f"Checking access: {user_id} -> {action} on {tool_id}")
            
            # Perform access control check
            access_result = await self.access_control_engine.check_access(
                tool_id, user_id, action, context or {}
            )
            
            # Log access attempt
            await self.audit_engine.log_access_attempt(
                user_id, tool_id, action, access_result["allowed"], context
            )
            
            # Check for security violations
            security_check = await self._perform_security_check(tool_id, user_id, action, context)
            
            return {
                "success": True,
                "allowed": access_result["allowed"] and security_check["clear"],
                "access_result": access_result,
                "security_check": security_check,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Access check failed: {e}")
            return {
                "success": False,
                "allowed": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def grant_tool_access(self, rule: AccessControlRule) -> Dict[str, Any]:
        """Grant access to tool"""
        try:
            logger.info(f"Granting access: {rule.principal_id} -> {rule.access_level.value} on {rule.tool_id}")
            
            # Validate rule
            validation_result = await self._validate_access_rule(rule)
            if not validation_result["valid"]:
                return {
                    "success": False,
                    "error": "Invalid access rule",
                    "validation_errors": validation_result["errors"]
                }
            
            # Store rule
            self.access_rules[rule.rule_id] = rule
            
            # Log access grant
            await self.audit_engine.log_access_change(
                rule.principal_id, rule.tool_id, "grant", rule.access_level.value
            )
            
            # Apply security policies
            policy_result = await self._apply_security_policies(rule)
            
            return {
                "success": True,
                "rule_id": rule.rule_id,
                "policy_result": policy_result,
                "granted_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Access grant failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "rule": rule.__dict__ if hasattr(rule, '__dict__') else {}
            }
    
    async def revoke_tool_access(self, rule_id: str, reason: str = "") -> Dict[str, Any]:
        """Revoke tool access"""
        try:
            if rule_id not in self.access_rules:
                return {
                    "success": False,
                    "error": "Access rule not found"
                }
            
            rule = self.access_rules[rule_id]
            
            # Remove rule
            del self.access_rules[rule_id]
            
            # Log access revocation
            await self.audit_engine.log_access_change(
                rule.principal_id, rule.tool_id, "revoke", reason
            )
            
            return {
                "success": True,
                "revoked_rule": rule.__dict__ if hasattr(rule, '__dict__') else {},
                "reason": reason,
                "revoked_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Access revocation failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "rule_id": rule_id
            }
    
    async def assess_tool_risk(self, tool_id: str, context: Dict[str, Any] = None) -> RiskAssessment:
        """Perform comprehensive risk assessment for tool"""
        try:
            logger.info(f"Performing risk assessment for tool: {tool_id}")
            
            # Generate new assessment
            assessment = await self.risk_engine.assess_tool(tool_id, context or {})
            
            # Store assessment
            self.risk_assessments[assessment.assessment_id] = assessment
            
            # Apply mitigation strategies
            await self._apply_mitigation_strategies(assessment)
            
            return assessment
            
        except Exception as e:
            logger.error(f"Risk assessment failed: {e}")
            # Return default assessment
            return RiskAssessment(
                assessment_id=f"error_{uuid.uuid4().hex[:8]}",
                tool_id=tool_id,
                risk_level=ThreatLevel.HIGH,
                risk_score=0.8,
                risk_categories=[RiskCategory.SYSTEM_FAILURE],
                recommendations=["Manual review required due to assessment error"]
            )
    
    async def report_security_incident(self, incident: SecurityIncident) -> Dict[str, Any]:
        """Report and handle security incident"""
        try:
            logger.info(f"Reporting security incident: {incident.title}")
            
            # Validate incident
            validation_result = await self._validate_incident(incident)
            if not validation_result["valid"]:
                return {
                    "success": False,
                    "error": "Invalid incident report",
                    "validation_errors": validation_result["errors"]
                }
            
            # Store incident
            self.incidents[incident.incident_id] = incident
            
            # Handle incident response
            response_result = await self.incident_engine.handle_incident(incident)
            
            # Apply immediate containment measures
            containment_result = await self._apply_containment_measures(incident)
            
            # Notify relevant stakeholders
            await self._notify_incident_stakeholders(incident)
            
            return {
                "success": True,
                "incident_id": incident.incident_id,
                "response_result": response_result,
                "containment_result": containment_result,
                "reported_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Incident reporting failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "incident": incident.__dict__ if hasattr(incident, '__dict__') else {}
            }
    
    async def check_compliance(self, tool_id: str, standards: List[ComplianceStandard]) -> List[ComplianceReport]:
        """Check compliance with specified standards"""
        try:
            logger.info(f"Checking compliance for tool: {tool_id}")
            
            reports = []
            
            for standard in standards:
                # Perform compliance check
                report = await self.compliance_engine.check_compliance(tool_id, standard)
                reports.append(report)
            
            # Store reports
            for report in reports:
                await self._store_compliance_report(report)
            
            return reports
            
        except Exception as e:
            logger.error(f"Compliance check failed: {e}")
            # Return error reports
            return [
                ComplianceReport(
                    report_id=f"error_{uuid.uuid4().hex[:8]}",
                    standard=standard,
                    tool_id=tool_id,
                    compliance_status="error",
                    compliance_score=0.0,
                    violations=["Compliance check failed"]
                ) for standard in standards
            ]
    
    async def encrypt_sensitive_data(self, data: str, encryption_type: str = "standard") -> Dict[str, Any]:
        """Encrypt sensitive data"""
        try:
            logger.info(f"Encrypting sensitive data with {encryption_type} encryption")
            
            # Encrypt data
            encrypted_result = await self.encryption_engine.encrypt_data(data, encryption_type)
            
            # Log encryption event
            await self.audit_engine.log_encryption_event("encrypt", encryption_type, len(data))
            
            return {
                "success": True,
                "encrypted_data": encrypted_result["encrypted"],
                "encryption_metadata": encrypted_result["metadata"],
                "encryption_timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Data encryption failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "original_data_size": len(data)
            }
    
    async def decrypt_sensitive_data(self, encrypted_data: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Decrypt sensitive data"""
        try:
            logger.info("Decrypting sensitive data")
            
            # Decrypt data
            decrypted_result = await self.encryption_engine.decrypt_data(encrypted_data, metadata)
            
            # Log decryption event
            await self.audit_engine.log_encryption_event("decrypt", metadata.get("type", "unknown"), len(decrypted_result["decrypted"]))
            
            return {
                "success": True,
                "decrypted_data": decrypted_result["decrypted"],
                "decryption_timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Data decryption failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _perform_security_check(self, tool_id: str, user_id: str, action: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Perform additional security checks"""
        # Check for suspicious patterns
        risk_indicators = 0
        
        # Check IP reputation (simplified)
        ip_address = context.get("ip_address")
        if ip_address and await self._is_suspicious_ip(ip_address):
            risk_indicators += 1
        
        # Check access patterns
        recent_attempts = await self.audit_engine.get_recent_attempts(user_id, tool_id, minutes=5)
        if len(recent_attempts) > 10:
            risk_indicators += 1
        
        # Check time patterns (access outside normal hours)
        current_hour = datetime.utcnow().hour
        if current_hour < 6 or current_hour > 22:  # Outside 6 AM - 10 PM
            risk_indicators += 0.5
        
        risk_score = min(1.0, risk_indicators / 3.0)
        
        return {
            "clear": risk_score < 0.5,
            "risk_score": risk_score,
            "risk_indicators": risk_indicators,
            "requires_approval": risk_score > 0.7
        }
    
    async def _validate_access_rule(self, rule: AccessControlRule) -> Dict[str, Any]:
        """Validate access control rule"""
        errors = []
        
        if not rule.tool_id.strip():
            errors.append("Tool ID is required")
        
        if not rule.principal_id.strip():
            errors.append("Principal ID is required")
        
        if not rule.principal_type.strip():
            errors.append("Principal type is required")
        
        if not rule.access_level:
            errors.append("Access level is required")
        
        # Check for conflicting rules
        conflicting_rules = [
            r for r in self.access_rules.values()
            if (r.tool_id == rule.tool_id and 
                r.principal_id == rule.principal_id and 
                r.rule_id != rule.rule_id)
        ]
        
        if conflicting_rules:
            errors.append("Conflicting access rule exists")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors
        }
    
    async def _validate_incident(self, incident: SecurityIncident) -> Dict[str, Any]:
        """Validate security incident"""
        errors = []
        
        if not incident.title.strip():
            errors.append("Incident title is required")
        
        if not incident.description.strip():
            errors.append("Incident description is required")
        
        if not incident.threat_level:
            errors.append("Threat level is required")
        
        if not incident.category.strip():
            errors.append("Incident category is required")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors
        }
    
    async def _apply_security_policies(self, rule: AccessControlRule) -> Dict[str, Any]:
        """Apply relevant security policies to access rule"""
        applicable_policies = [
            policy for policy in self.policies.values()
            if policy.policy_type == SecurityPolicyType.ACCESS_CONTROL
        ]
        
        policy_results = []
        
        for policy in applicable_policies:
            # Check if policy applies to this rule
            if await self._policy_applies_to_rule(policy, rule):
                result = await self._enforce_policy(policy, rule)
                policy_results.append(result)
        
        return {
            "applicable_policies": len(applicable_policies),
            "policy_results": policy_results,
            "enforcement_status": "applied"
        }
    
    async def _apply_mitigation_strategies(self, assessment: RiskAssessment):
        """Apply risk mitigation strategies"""
        for strategy in assessment.mitigation_strategies:
            # Apply specific mitigation based on strategy type
            if "access_control" in strategy.lower():
                await self._tighten_access_controls(assessment.tool_id)
            elif "monitoring" in strategy.lower():
                await self._enhance_monitoring(assessment.tool_id)
            elif "encryption" in strategy.lower():
                await self._require_encryption(assessment.tool_id)
    
    async def _apply_containment_measures(self, incident: SecurityIncident) -> Dict[str, Any]:
        """Apply immediate containment measures for incident"""
        containment_actions = []
        
        if incident.threat_level in [ThreatLevel.HIGH, ThreatLevel.CRITICAL, ThreatLevel.EMERGENCY]:
            # Isolate affected tools
            for tool_id in incident.affected_tools:
                await self.access_control_engine.isolate_tool(tool_id)
                containment_actions.append(f"Isolated tool: {tool_id}")
            
            # Disable suspicious accounts
            for user_id in incident.affected_users:
                await self.access_control_engine.suspend_user(user_id)
                containment_actions.append(f"Suspended user: {user_id}")
        
        return {
            "containment_actions": containment_actions,
            "incident_severity": incident.threat_level.value,
            "containment_timestamp": datetime.utcnow().isoformat()
        }
    
    async def _notify_incident_stakeholders(self, incident: SecurityIncident):
        """Notify relevant stakeholders about incident"""
        # In a real implementation, this would send notifications to:
        # - Security team
        # - Management
        # - Affected users
        # - Compliance officers
        # - Legal team (if required)
        
        logger.info(f"Notifying stakeholders about incident: {incident.incident_id}")
    
    async def _store_compliance_report(self, report: ComplianceReport):
        """Store compliance report"""
        # In a real implementation, this would store in database
        # For now, just log the report
        logger.info(f"Stored compliance report: {report.report_id}")
    
    async def _policy_applies_to_rule(self, policy: SecurityPolicy, rule: AccessControlRule) -> bool:
        """Check if policy applies to access rule"""
        # Simplified policy applicability check
        # In reality, this would check policy conditions and rule attributes
        return True
    
    async def _enforce_policy(self, policy: SecurityPolicy, rule: AccessControlRule) -> Dict[str, Any]:
        """Enforce security policy on access rule"""
        return {
            "policy_id": policy.policy_id,
            "enforced": True,
            "action": "allow",  # or "deny" based on policy evaluation
            "reason": "Policy enforcement completed"
        }
    
    async def _tighten_access_controls(self, tool_id: str):
        """Tighten access controls for tool"""
        logger.info(f"Tightening access controls for tool: {tool_id}")
    
    async def _enhance_monitoring(self, tool_id: str):
        """Enhance monitoring for tool"""
        logger.info(f"Enhancing monitoring for tool: {tool_id}")
    
    async def _require_encryption(self, tool_id: str):
        """Require encryption for tool"""
        logger.info(f"Requiring encryption for tool: {tool_id}")
    
    async def _is_suspicious_ip(self, ip_address: str) -> bool:
        """Check if IP address is suspicious"""
        # Simplified suspicious IP detection
        # In reality, this would check against threat intelligence feeds
        return ip_address.startswith("192.168.1.")  # Example suspicious pattern


class AccessControlEngine:
    """Engine for managing access control"""
    
    def __init__(self):
        self.access_cache = {}
        self.suspended_users = set()
        self.isolated_tools = set()
    
    async def check_access(self, tool_id: str, user_id: str, action: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Check if user has access to perform action on tool"""
        # Check if user is suspended
        if user_id in self.suspended_users:
            return {
                "allowed": False,
                "reason": "User account is suspended",
                "requires_approval": False
            }
        
        # Check if tool is isolated
        if tool_id in self.isolated_tools:
            return {
                "allowed": False,
                "reason": "Tool is temporarily isolated",
                "requires_approval": False
            }
        
        # Check access rules
        applicable_rules = await self._find_applicable_rules(tool_id, user_id, action)
        
        if not applicable_rules:
            return {
                "allowed": False,
                "reason": "No access rules found",
                "requires_approval": True
            }
        
        # Evaluate rules
        rule_evaluation = await self._evaluate_rules(applicable_rules, context)
        
        return {
            "allowed": rule_evaluation["allowed"],
            "reason": rule_evaluation["reason"],
            "requires_approval": rule_evaluation.get("requires_approval", False),
            "applied_rules": [rule.rule_id for rule in applicable_rules]
        }
    
    async def isolate_tool(self, tool_id: str):
        """Isolate tool from access"""
        self.isolated_tools.add(tool_id)
        logger.info(f"Tool {tool_id} isolated")
    
    async def suspend_user(self, user_id: str):
        """Suspend user access"""
        self.suspended_users.add(user_id)
        logger.info(f"User {user_id} suspended")
    
    async def _find_applicable_rules(self, tool_id: str, user_id: str, action: str) -> List[AccessControlRule]:
        """Find access rules applicable to the request"""
        # This would query the database in a real implementation
        # For now, return empty list (no rules configured)
        return []
    
    async def _evaluate_rules(self, rules: List[AccessControlRule], context: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate access rules"""
        if not rules:
            return {"allowed": False, "reason": "No applicable rules"}
        
        # Evaluate each rule
        for rule in rules:
            if await self._rule_matches_context(rule, context):
                if rule.access_level in [AccessLevel.OWNER, AccessLevel.ADMIN]:
                    return {"allowed": True, "reason": "Administrative access granted"}
                elif rule.access_level == AccessLevel.READ and action.lower() in ["read", "view"]:
                    return {"allowed": True, "reason": "Read access granted"}
                elif rule.access_level == AccessLevel.WRITE and action.lower() in ["write", "edit", "update"]:
                    return {"allowed": True, "reason": "Write access granted"}
                elif rule.access_level == AccessLevel.EXECUTE and action.lower() in ["execute", "run", "use"]:
                    return {"allowed": True, "reason": "Execute access granted"}
        
        return {"allowed": False, "reason": "Access level insufficient"}
    
    async def _rule_matches_context(self, rule: AccessControlRule, context: Dict[str, Any]) -> bool:
        """Check if rule matches current context"""
        # Check expiration
        if rule.expires_at and datetime.utcnow() > rule.expires_at:
            return False
        
        # Check conditions
        for condition_key, condition_value in rule.conditions.items():
            if condition_key in context:
                if context[condition_key] != condition_value:
                    return False
        
        return True


class AuditEngine:
    """Engine for audit logging and monitoring"""
    
    def __init__(self):
        self.audit_log = deque(maxlen=10000)
        self.suspicious_patterns = []
    
    async def log_access_attempt(self, user_id: str, tool_id: str, action: str, granted: bool, context: Dict[str, Any]):
        """Log access attempt"""
        log_entry = AuditLogEntry(
            timestamp=datetime.utcnow(),
            user_id=user_id,
            action=f"access_{action}",
            resource="tool",
            resource_id=tool_id,
            details={
                "granted": granted,
                "context": context
            },
            ip_address=context.get("ip_address"),
            user_agent=context.get("user_agent"),
            result="success" if granted else "denied"
        )
        
        self.audit_log.append(log_entry)
    
    async def log_access_change(self, principal_id: str, tool_id: str, change_type: str, details: str):
        """Log access control change"""
        log_entry = AuditLogEntry(
            timestamp=datetime.utcnow(),
            user_id="system",
            action=f"access_change_{change_type}",
            resource="tool",
            resource_id=tool_id,
            details={
                "principal_id": principal_id,
                "change_type": change_type,
                "details": details
            },
            result="success"
        )
        
        self.audit_log.append(log_entry)
    
    async def log_encryption_event(self, action: str, encryption_type: str, data_size: int):
        """Log encryption/decryption event"""
        log_entry = AuditLogEntry(
            timestamp=datetime.utcnow(),
            user_id="system",
            action=f"encryption_{action}",
            resource="data",
            resource_id=f"{encryption_type}_{data_size}",
            details={
                "encryption_type": encryption_type,
                "data_size": data_size
            },
            result="success"
        )
        
        self.audit_log.append(log_entry)
    
    async def get_recent_attempts(self, user_id: str, tool_id: str, minutes: int = 5) -> List[AuditLogEntry]:
        """Get recent access attempts for user/tool"""
        cutoff_time = datetime.utcnow() - timedelta(minutes=minutes)
        
        return [
            entry for entry in self.audit_log
            if (entry.user_id == user_id and 
                entry.resource_id == tool_id and 
                entry.timestamp > cutoff_time)
        ]
    
    async def analyze_access_patterns(self, user_id: str, timeframe_hours: int = 24) -> Dict[str, Any]:
        """Analyze access patterns for user"""
        cutoff_time = datetime.utcnow() - timedelta(hours=timeframe_hours)
        
        user_entries = [
            entry for entry in self.audit_log
            if entry.user_id == user_id and entry.timestamp > cutoff_time
        ]
        
        if not user_entries:
            return {"pattern": "no_activity", "risk_score": 0.0}
        
        # Analyze patterns
        access_counts = defaultdict(int)
        failure_count = sum(1 for entry in user_entries if entry.result == "denied")
        total_count = len(user_entries)
        
        for entry in user_entries:
            access_counts[entry.action] += 1
        
        failure_rate = failure_count / total_count if total_count > 0 else 0
        
        # Calculate risk score
        risk_score = min(1.0, failure_rate * 2)  # Higher failure rate = higher risk
        
        return {
            "total_attempts": total_count,
            "failure_count": failure_count,
            "failure_rate": failure_rate,
            "access_patterns": dict(access_counts),
            "risk_score": risk_score,
            "timeframe_hours": timeframe_hours
        }


class ComplianceEngine:
    """Engine for compliance checking"""
    
    def __init__(self):
        self.compliance_rules = self._load_compliance_rules()
    
    def _load_compliance_rules(self) -> Dict[ComplianceStandard, Dict[str, Any]]:
        """Load compliance rules for different standards"""
        return {
            ComplianceStandard.GDPR: {
                "data_protection_required": True,
                "consent_required": True,
                "data_retention_limit_days": 365,
                "breach_notification_hours": 72
            },
            ComplianceStandard.FERPA: {
                "student_data_protection": True,
                "parental_consent_required": True,
                "access_logging_required": True
            },
            ComplianceStandard.HIPAA: {
                "phi_protection": True,
                "audit_trail_required": True,
                "access_controls_required": True
            },
            ComplianceStandard.ISO27001: {
                "information_security_management": True,
                "risk_assessment_required": True,
                "incident_response_required": True
            }
        }
    
    async def check_compliance(self, tool_id: str, standard: ComplianceStandard) -> ComplianceReport:
        """Check compliance with specified standard"""
        rules = self.compliance_rules.get(standard, {})
        
        # Perform compliance checks
        violations = []
        compliance_score = 1.0
        
        for rule_name, requirement in rules.items():
            check_result = await self._check_compliance_rule(tool_id, rule_name, requirement, standard)
            
            if not check_result["compliant"]:
                violations.append(check_result["violation"])
                compliance_score -= 0.1
        
        compliance_score = max(0.0, compliance_score)
        compliance_status = "compliant" if compliance_score >= 0.8 else "non_compliant" if compliance_score < 0.5 else "partial"
        
        # Generate remediation steps
        remediation_steps = await self._generate_remediation_steps(violations, standard)
        
        # Calculate next review date
        next_review = datetime.utcnow() + timedelta(days=90)  # 90 days default
        
        return ComplianceReport(
            report_id=f"compliance_{uuid.uuid4().hex[:8]}",
            standard=standard,
            tool_id=tool_id,
            compliance_status=compliance_status,
            compliance_score=compliance_score,
            violations=violations,
            remediation_steps=remediation_steps,
            assessed_at=datetime.utcnow(),
            next_review=next_review
        )
    
    async def _check_compliance_rule(self, tool_id: str, rule_name: str, requirement: Any, standard: ComplianceStandard) -> Dict[str, Any]:
        """Check individual compliance rule"""
        # Simplified compliance checking
        # In reality, this would check actual tool configuration
        
        if rule_name == "data_protection_required":
            return {"compliant": True, "violation": None}
        elif rule_name == "consent_required":
            return {"compliant": True, "violation": None}
        elif rule_name == "audit_trail_required":
            return {"compliant": True, "violation": None}
        else:
            return {"compliant": True, "violation": None}
    
    async def _generate_remediation_steps(self, violations: List[str], standard: ComplianceStandard) -> List[str]:
        """Generate remediation steps for violations"""
        steps = []
        
        for violation in violations:
            if "data_protection" in violation:
                steps.append("Implement data protection measures")
            elif "consent" in violation:
                steps.append("Obtain proper consent from users")
            elif "audit" in violation:
                steps.append("Enable audit logging and monitoring")
            else:
                steps.append(f"Address compliance issue: {violation}")
        
        if not steps:
            steps.append("Maintain current compliance standards")
        
        return steps


class IncidentResponseEngine:
    """Engine for incident response management"""
    
    def __init__(self):
        self.incident_templates = self._load_incident_templates()
        self.response_playbooks = self._load_response_playbooks()
    
    def _load_incident_templates(self) -> Dict[str, Dict[str, Any]]:
        """Load incident response templates"""
        return {
            "data_breach": {
                "response_time_target": 15,  # minutes
                "escalation_required": True,
                "notification_requirements": ["management", "legal", "affected_users"]
            },
            "unauthorized_access": {
                "response_time_target": 30,  # minutes
                "escalation_required": False,
                "notification_requirements": ["security_team"]
            },
            "malware": {
                "response_time_target": 10,  # minutes
                "escalation_required": True,
                "notification_requirements": ["security_team", "it_team"]
            }
        }
    
    def _load_response_playbooks(self) -> Dict[str, List[str]]:
        """Load incident response playbooks"""
        return {
            "data_breach": [
                "Immediately isolate affected systems",
                "Preserve evidence and logs",
                "Assess scope of breach",
                "Notify relevant stakeholders",
                "Implement remediation measures",
                "Conduct post-incident review"
            ],
            "unauthorized_access": [
                "Block suspicious user accounts",
                "Review access logs",
                "Implement additional authentication",
                "Monitor for additional suspicious activity",
                "Document incident and lessons learned"
            ],
            "malware": [
                "Isolate infected systems immediately",
                "Stop malware spread",
                "Clean infected systems",
                "Update security patches",
                "Review and strengthen defenses",
                "Conduct forensic analysis"
            ]
        }
    
    async def handle_incident(self, incident: SecurityIncident) -> Dict[str, Any]:
        """Handle security incident according to response procedures"""
        template = self.incident_templates.get(incident.category, {})
        playbook = self.response_playbooks.get(incident.category, [])
        
        # Update incident status
        incident.status = IncidentStatus.INVESTIGATING
        
        # Execute response procedures
        response_actions = []
        
        for step in playbook:
            action_result = await self._execute_response_step(incident, step)
            response_actions.append(action_result)
            
            # Log each action
            incident.audit_trail.append({
                "timestamp": datetime.utcnow().isoformat(),
                "action": step,
                "result": action_result
            })
        
        # Check if escalation is required
        escalation_required = template.get("escalation_required", False)
        
        return {
            "incident_id": incident.incident_id,
            "response_actions": response_actions,
            "escalation_required": escalation_required,
            "response_status": "initiated",
            "estimated_resolution_time": template.get("response_time_target", 60)  # minutes
        }
    
    async def _execute_response_step(self, incident: SecurityIncident, step: str) -> Dict[str, Any]:
        """Execute individual response step"""
        # Simulate response action execution
        await asyncio.sleep(0.1)  # Simulate processing time
        
        return {
            "step": step,
            "status": "completed",
            "timestamp": datetime.utcnow().isoformat(),
            "notes": f"Executed: {step}"
        }


class RiskAssessmentEngine:
    """Engine for risk assessment"""
    
    def __init__(self):
        self.risk_factors = self._load_risk_factors()
        self.mitigation_strategies = self._load_mitigation_strategies()
    
    def _load_risk_factors(self) -> Dict[str, Dict[str, Any]]:
        """Load risk assessment factors"""
        return {
            "data_sensitivity": {
                "weight": 0.3,
                "factors": ["personal_data", "financial_data", "health_data", "academic_records"]
            },
            "access_scope": {
                "weight": 0.25,
                "factors": ["number_of_users", "external_access", "admin_privileges"]
            },
            "system_complexity": {
                "weight": 0.2,
                "factors": ["integration_points", "third_party_dependencies", "custom_code"]
            },
            "security_controls": {
                "weight": 0.25,
                "factors": ["encryption", "authentication", "monitoring", "audit_logging"]
            }
        }
    
    def _load_mitigation_strategies(self) -> Dict[str, List[str]]:
        """Load risk mitigation strategies"""
        return {
            "data_breach": [
                "Implement strong encryption",
                "Enable access logging",
                "Regular security audits",
                "Staff training on data handling"
            ],
            "unauthorized_access": [
                "Multi-factor authentication",
                "Role-based access controls",
                "Regular access reviews",
                "Session management"
            ],
            "malware": [
                "Antivirus protection",
                "Regular security updates",
                "Network segmentation",
                "User awareness training"
            ],
            "system_failure": [
                "Backup and recovery procedures",
                "Redundancy planning",
                "Performance monitoring",
                "Disaster recovery planning"
            ]
        }
    
    async def assess_tool(self, tool_id: str, context: Dict[str, Any]) -> RiskAssessment:
        """Perform comprehensive risk assessment for tool"""
        # Calculate risk factors
        risk_scores = {}
        
        for factor_name, factor_config in self.risk_factors.items():
            score = await self._calculate_factor_score(tool_id, factor_name, context)
            risk_scores[factor_name] = score
        
        # Calculate overall risk score
        overall_score = sum(
            risk_scores[factor] * config["weight"]
            for factor, config in self.risk_factors.items()
        )
        
        # Determine risk level
        risk_level = self._determine_risk_level(overall_score)
        
        # Identify risk categories
        risk_categories = await self._identify_risk_categories(risk_scores, context)
        
        # Generate mitigation strategies
        mitigation_strategies = []
        for category in risk_categories:
            if category.value in self.mitigation_strategies:
                mitigation_strategies.extend(self.mitigation_strategies[category.value])
        
        # Generate recommendations
        recommendations = await self._generate_recommendations(risk_scores, risk_level)
        
        # Set expiration date
        expires_at = datetime.utcnow() + timedelta(days=180)  # 6 months
        
        return RiskAssessment(
            assessment_id=f"risk_{uuid.uuid4().hex[:8]}",
            tool_id=tool_id,
            risk_level=risk_level,
            risk_categories=risk_categories,
            risk_score=overall_score,
            mitigation_strategies=list(set(mitigation_strategies)),  # Remove duplicates
            recommendations=recommendations,
            assessed_at=datetime.utcnow(),
            expires_at=expires_at
        )
    
    async def _calculate_factor_score(self, tool_id: str, factor_name: str, context: Dict[str, Any]) -> float:
        """Calculate score for specific risk factor"""
        if factor_name == "data_sensitivity":
            # Check if tool handles sensitive data
            sensitive_data_types = context.get("sensitive_data_types", [])
            score = min(1.0, len(sensitive_data_types) * 0.25)
        elif factor_name == "access_scope":
            # Assess access scope
            num_users = context.get("user_count", 0)
            external_access = context.get("external_access", False)
            score = min(1.0, (num_users / 100) * 0.5 + (0.5 if external_access else 0))
        elif factor_name == "system_complexity":
            # Assess system complexity
            integrations = context.get("integrations", [])
            score = min(1.0, len(integrations) * 0.2)
        elif factor_name == "security_controls":
            # Assess security controls
            security_features = context.get("security_features", [])
            score = 1.0 - (len(security_features) * 0.15)  # More features = lower risk
        else:
            score = 0.5  # Default moderate risk
        
        return max(0.0, min(1.0, score))
    
    def _determine_risk_level(self, risk_score: float) -> ThreatLevel:
        """Determine risk level from score"""
        if risk_score >= 0.8:
            return ThreatLevel.CRITICAL
        elif risk_score >= 0.6:
            return ThreatLevel.HIGH
        elif risk_score >= 0.4:
            return ThreatLevel.MEDIUM
        else:
            return ThreatLevel.LOW
    
    async def _identify_risk_categories(self, risk_scores: Dict[str, float], context: Dict[str, Any]) -> List[RiskCategory]:
        """Identify relevant risk categories"""
        categories = []
        
        if risk_scores.get("data_sensitivity", 0) > 0.5:
            categories.append(RiskCategory.DATA_BREACH)
        
        if risk_scores.get("access_scope", 0) > 0.5:
            categories.append(RiskCategory.UNAUTHORIZED_ACCESS)
        
        if risk_scores.get("system_complexity", 0) > 0.6:
            categories.append(RiskCategory.SYSTEM_FAILURE)
        
        if risk_scores.get("security_controls", 0) > 0.5:  # Low security controls = high risk
            categories.append(RiskCategory.COMPLIANCE_VIOLATION)
        
        return categories if categories else [RiskCategory.SYSTEM_FAILURE]  # Default category
    
    async def _generate_recommendations(self, risk_scores: Dict[str, float], risk_level: ThreatLevel) -> List[str]:
        """Generate risk mitigation recommendations"""
        recommendations = []
        
        if risk_scores.get("data_sensitivity", 0) > 0.5:
            recommendations.append("Implement data classification and protection measures")
            recommendations.append("Enable data loss prevention")
        
        if risk_scores.get("access_scope", 0) > 0.5:
            recommendations.append("Review and tighten access controls")
            recommendations.append("Implement least privilege principle")
        
        if risk_scores.get("system_complexity", 0) > 0.5:
            recommendations.append("Simplify system architecture where possible")
            recommendations.append("Increase monitoring and observability")
        
        if risk_scores.get("security_controls", 0) > 0.5:
            recommendations.append("Strengthen authentication mechanisms")
            recommendations.append("Enhance security monitoring")
        
        if risk_level in [ThreatLevel.HIGH, ThreatLevel.CRITICAL]:
            recommendations.append("Conduct regular security assessments")
            recommendations.append("Develop incident response plan")
        
        return recommendations if recommendations else ["Monitor system security regularly"]


class EncryptionEngine:
    """Engine for data encryption and decryption"""
    
    def __init__(self):
        self.encryption_keys = {}
        self.algorithm_configs = {
            "standard": {"algorithm": "AES-256", "key_derivation": "PBKDF2"},
            "high_security": {"algorithm": "AES-256-GCM", "key_derivation": "PBKDF2", "iterations": 100000},
            "legacy": {"algorithm": "AES-128", "key_derivation": "PBKDF2"}
        }
    
    async def encrypt_data(self, data: str, encryption_type: str = "standard") -> Dict[str, Any]:
        """Encrypt sensitive data"""
        try:
            config = self.encryption_configs.get(encryption_type, self.encryption_configs["standard"])
            
            # Generate or retrieve encryption key
            key = await self._get_or_generate_key(encryption_type)
            
            # Create cipher
            fernet = Fernet(key)
            
            # Encrypt data
            encrypted_data = fernet.encrypt(data.encode())
            
            return {
                "encrypted": encrypted_data.decode(),
                "metadata": {
                    "type": encryption_type,
                    "algorithm": config["algorithm"],
                    "timestamp": datetime.utcnow().isoformat(),
                    "version": "1.0"
                }
            }
            
        except Exception as e:
            logger.error(f"Encryption failed: {e}")
            raise
    
    async def decrypt_data(self, encrypted_data: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Decrypt sensitive data"""
        try:
            encryption_type = metadata.get("type", "standard")
            
            # Get appropriate key
            key = await self._get_or_generate_key(encryption_type)
            
            # Create cipher
            fernet = Fernet(key)
            
            # Decrypt data
            decrypted_data = fernet.decrypt(encrypted_data.encode())
            
            return {
                "decrypted": decrypted_data.decode(),
                "metadata": metadata
            }
            
        except Exception as e:
            logger.error(f"Decryption failed: {e}")
            raise
    
    async def _get_or_generate_key(self, encryption_type: str) -> bytes:
        """Get or generate encryption key"""
        if encryption_type not in self.encryption_keys:
            # Generate new key
            password = f"dryad_{encryption_type}_{secrets.token_hex(16)}".encode()
            salt = secrets.token_bytes(16)
            
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
            )
            key = base64.urlsafe_b64encode(kdf.derive(password))
            
            # Store key with metadata
            self.encryption_keys[encryption_type] = {
                "key": key,
                "salt": base64.urlsafe_b64encode(salt),
                "created_at": datetime.utcnow()
            }
        
        return self.encryption_keys[encryption_type]["key"]