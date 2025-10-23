"""
Advanced Security Features for DRYAD.AI Backend
Provides API key management, request signing, audit logging, and data encryption.
"""

import asyncio
import time
import hashlib
import hmac
import secrets
import json
import uuid
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
import os

from app.core.logging_config import get_logger
from app.core.caching import cache
from app.database.database import AsyncSessionLocal

logger = get_logger(__name__)

@dataclass
class APIKey:
    """API key with metadata."""
    key_id: str
    key_hash: str
    name: str
    permissions: List[str]
    created_at: float
    expires_at: Optional[float] = None
    last_used_at: Optional[float] = None
    usage_count: int = 0
    rate_limit: int = 1000  # requests per hour
    is_active: bool = True

@dataclass
class AuditLogEntry:
    """Audit log entry for security events."""
    id: str
    timestamp: float
    user_id: Optional[str]
    api_key_id: Optional[str]
    action: str
    resource: str
    details: Dict[str, Any]
    ip_address: str
    user_agent: str
    success: bool
    risk_score: float = 0.0

class APIKeyManager:
    """Advanced API key management system."""
    
    def __init__(self):
        self.api_keys: Dict[str, APIKey] = {}
        self.key_cache_ttl = 3600  # 1 hour
        self.rotation_schedule: Dict[str, float] = {}
        self.rate_limit_storage: Dict[str, List[float]] = {}
        
    async def create_api_key(self, name: str, permissions: List[str], 
                           expires_in_days: Optional[int] = None,
                           rate_limit: int = 1000) -> Tuple[str, str]:
        """Create a new API key."""
        key_id = str(uuid.uuid4())
        raw_key = secrets.token_urlsafe(32)
        key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
        
        expires_at = None
        if expires_in_days:
            expires_at = time.time() + (expires_in_days * 24 * 3600)
        
        api_key = APIKey(
            key_id=key_id,
            key_hash=key_hash,
            name=name,
            permissions=permissions,
            created_at=time.time(),
            expires_at=expires_at,
            rate_limit=rate_limit
        )
        
        self.api_keys[key_id] = api_key
        
        # Cache the key
        cache_key = f"api_key:{key_hash}"
        cache.set(cache_key, api_key, ttl=self.key_cache_ttl)
        
        logger.info(f"Created API key: {name} (ID: {key_id})")
        return f"{key_id}:{raw_key}", key_id
    
    async def validate_api_key(self, api_key_string: str) -> Optional[APIKey]:
        """Validate an API key."""
        try:
            if ':' not in api_key_string:
                return None
                
            key_id, raw_key = api_key_string.split(':', 1)
            key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
            
            # Try cache first
            cache_key = f"api_key:{key_hash}"
            cached_key = cache.get(cache_key)
            if cached_key and isinstance(cached_key, APIKey):
                if cached_key.key_id == key_id and cached_key.is_active:
                    if not cached_key.expires_at or cached_key.expires_at > time.time():
                        # Update usage
                        cached_key.last_used_at = time.time()
                        cached_key.usage_count += 1
                        return cached_key
            
            # Check stored keys
            if key_id in self.api_keys:
                stored_key = self.api_keys[key_id]
                if (stored_key.key_hash == key_hash and 
                    stored_key.is_active and
                    (not stored_key.expires_at or stored_key.expires_at > time.time())):
                    
                    # Update usage
                    stored_key.last_used_at = time.time()
                    stored_key.usage_count += 1
                    
                    # Update cache
                    cache.set(cache_key, stored_key, ttl=self.key_cache_ttl)
                    return stored_key
            
            return None
            
        except Exception as e:
            logger.error(f"Error validating API key: {e}")
            return None
    
    async def revoke_api_key(self, key_id: str) -> bool:
        """Revoke an API key."""
        if key_id in self.api_keys:
            self.api_keys[key_id].is_active = False
            
            # Remove from cache
            key_hash = self.api_keys[key_id].key_hash
            cache_key = f"api_key:{key_hash}"
            cache.delete(cache_key)
            
            logger.info(f"Revoked API key: {key_id}")
            return True
        return False
    
    async def rotate_api_key(self, key_id: str) -> Optional[Tuple[str, str]]:
        """Rotate an API key (create new, mark old for deprecation)."""
        if key_id not in self.api_keys:
            return None
        
        old_key = self.api_keys[key_id]
        
        # Create new key with same permissions
        new_key_string, new_key_id = await self.create_api_key(
            name=f"{old_key.name} (rotated)",
            permissions=old_key.permissions,
            rate_limit=old_key.rate_limit
        )
        
        # Schedule old key for deprecation (30 days)
        self.rotation_schedule[key_id] = time.time() + (30 * 24 * 3600)
        
        logger.info(f"Rotated API key: {key_id} -> {new_key_id}")
        return new_key_string, new_key_id
    
    async def check_rate_limit(self, key_id: str) -> bool:
        """Check if API key is within rate limits."""
        if key_id not in self.api_keys:
            return False

        api_key = self.api_keys[key_id]
        current_time = time.time()

        # Initialize rate limit storage for this key if not exists
        if key_id not in self.rate_limit_storage:
            self.rate_limit_storage[key_id] = []

        # Clean old requests (older than 1 hour)
        self.rate_limit_storage[key_id] = [
            req_time for req_time in self.rate_limit_storage[key_id]
            if current_time - req_time < 3600
        ]

        # Check if under rate limit
        if len(self.rate_limit_storage[key_id]) >= api_key.rate_limit:
            return False

        # Add current request
        self.rate_limit_storage[key_id].append(current_time)
        return True

class RequestSigner:
    """Request signing and validation system."""
    
    def __init__(self, secret_key: Optional[str] = None):
        self.secret_key = secret_key or os.getenv("REQUEST_SIGNING_SECRET", secrets.token_urlsafe(32))
        
    def sign_request(self, method: str, path: str, body: str, timestamp: int) -> str:
        """Sign a request."""
        message = f"{method}|{path}|{body}|{timestamp}"
        signature = hmac.new(
            self.secret_key.encode(),
            message.encode(),
            hashlib.sha256
        ).hexdigest()
        return signature
    
    def validate_signature(self, method: str, path: str, body: str, 
                         timestamp: int, signature: str, max_age: int = 300) -> bool:
        """Validate a request signature."""
        # Check timestamp (prevent replay attacks)
        current_time = int(time.time())
        if abs(current_time - timestamp) > max_age:
            return False
        
        # Verify signature
        expected_signature = self.sign_request(method, path, body, timestamp)
        return hmac.compare_digest(signature, expected_signature)

class DataEncryption:
    """Advanced data encryption at rest and in transit with key management."""

    def __init__(self, encryption_key: Optional[bytes] = None):
        self._initialize_encryption(encryption_key)
        self.key_rotation_interval = 86400 * 30  # 30 days
        self.last_key_rotation = time.time()

    def _initialize_encryption(self, encryption_key: Optional[bytes] = None):
        """Initialize encryption with secure key derivation."""
        if encryption_key:
            self.fernet = Fernet(encryption_key)
        else:
            # Use secure environment-based key derivation
            password = os.getenv("ENCRYPTION_PASSWORD")
            salt = os.getenv("ENCRYPTION_SALT")

            if not password or not salt:
                if os.getenv("ENVIRONMENT") == "production":
                    raise ValueError(
                        "ENCRYPTION_PASSWORD and ENCRYPTION_SALT must be set in production. "
                        "Generate secure values with: python -c 'import secrets; print(secrets.token_urlsafe(32))'"
                    )
                else:
                    # Development defaults - silent in development
                    password = "dev-encryption-password-change-in-production"
                    salt = "dev-salt-change-in-production"
                    # Silent in development - only warn in production
                    logger.debug("Using development encryption keys. Set ENCRYPTION_PASSWORD and ENCRYPTION_SALT for production.")

            # Derive encryption key using PBKDF2
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt.encode(),
                iterations=100000,  # OWASP recommended minimum
            )
            key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
            self.fernet = Fernet(key)

    def encrypt(self, data: str) -> str:
        """Encrypt string data with timestamp."""
        if not data:
            return ""

        # Add timestamp for key rotation tracking
        timestamped_data = {
            "data": data,
            "timestamp": time.time(),
            "version": "1.0"
        }
        json_data = json.dumps(timestamped_data)
        return self.fernet.encrypt(json_data.encode()).decode()

    def decrypt(self, encrypted_data: str) -> str:
        """Decrypt string data with version handling."""
        if not encrypted_data:
            return ""

        try:
            decrypted_bytes = self.fernet.decrypt(encrypted_data.encode())
            decrypted_json = decrypted_bytes.decode()

            # Handle versioned data
            try:
                data_obj = json.loads(decrypted_json)
                if isinstance(data_obj, dict) and "data" in data_obj:
                    return data_obj["data"]
                else:
                    # Legacy format
                    return decrypted_json
            except json.JSONDecodeError:
                # Legacy format
                return decrypted_json

        except Exception as e:
            logger.error(f"Decryption failed: {e}")
            raise ValueError("Failed to decrypt data")

    def encrypt_dict(self, data: Dict[str, Any]) -> str:
        """Encrypt a dictionary with metadata."""
        if not data:
            return ""

        # Add encryption metadata
        encrypted_data = {
            "payload": data,
            "encrypted_at": time.time(),
            "encryption_version": "1.0",
            "checksum": hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()
        }
        json_data = json.dumps(encrypted_data)
        return self.fernet.encrypt(json_data.encode()).decode()

    def decrypt_dict(self, encrypted_data: str) -> Dict[str, Any]:
        """Decrypt to dictionary with integrity verification."""
        if not encrypted_data:
            return {}

        try:
            decrypted_bytes = self.fernet.decrypt(encrypted_data.encode())
            decrypted_json = decrypted_bytes.decode()
            data_obj = json.loads(decrypted_json)

            # Handle versioned data
            if isinstance(data_obj, dict) and "payload" in data_obj:
                payload = data_obj["payload"]

                # Verify checksum if available
                if "checksum" in data_obj:
                    expected_checksum = data_obj["checksum"]
                    actual_checksum = hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()
                    if expected_checksum != actual_checksum:
                        logger.error("Data integrity check failed during decryption")
                        raise ValueError("Data integrity verification failed")

                return payload
            else:
                # Legacy format
                return data_obj

        except Exception as e:
            logger.error(f"Dictionary decryption failed: {e}")
            raise ValueError("Failed to decrypt dictionary data")

    def encrypt_file_content(self, file_content: bytes, filename: str) -> bytes:
        """Encrypt file content with metadata."""
        if not file_content:
            return b""

        # Create file encryption metadata
        file_metadata = {
            "filename": filename,
            "size": len(file_content),
            "encrypted_at": time.time(),
            "content_hash": hashlib.sha256(file_content).hexdigest()
        }

        # Encrypt metadata and content separately
        metadata_encrypted = self.encrypt(json.dumps(file_metadata))
        content_encrypted = self.fernet.encrypt(file_content)

        # Combine with length prefixes
        metadata_bytes = metadata_encrypted.encode()
        metadata_length = len(metadata_bytes).to_bytes(4, byteorder='big')

        return metadata_length + metadata_bytes + content_encrypted

    def decrypt_file_content(self, encrypted_file_content: bytes) -> Tuple[bytes, Dict[str, Any]]:
        """Decrypt file content and return content with metadata."""
        if not encrypted_file_content:
            return b"", {}

        try:
            # Extract metadata length
            metadata_length = int.from_bytes(encrypted_file_content[:4], byteorder='big')

            # Extract and decrypt metadata
            metadata_bytes = encrypted_file_content[4:4+metadata_length]
            metadata_json = self.decrypt(metadata_bytes.decode())
            metadata = json.loads(metadata_json)

            # Extract and decrypt content
            content_encrypted = encrypted_file_content[4+metadata_length:]
            content = self.fernet.decrypt(content_encrypted)

            # Verify content integrity
            if "content_hash" in metadata:
                expected_hash = metadata["content_hash"]
                actual_hash = hashlib.sha256(content).hexdigest()
                if expected_hash != actual_hash:
                    logger.error("File content integrity check failed")
                    raise ValueError("File content integrity verification failed")

            return content, metadata

        except Exception as e:
            logger.error(f"File decryption failed: {e}")
            raise ValueError("Failed to decrypt file content")

    def should_rotate_key(self) -> bool:
        """Check if encryption key should be rotated."""
        return time.time() - self.last_key_rotation > self.key_rotation_interval

    def generate_new_key(self) -> bytes:
        """Generate a new encryption key."""
        return Fernet.generate_key()


@dataclass
class PIIDetectionResult:
    """Result of PII detection scan."""
    has_pii: bool
    pii_types: List[str]
    confidence_score: float
    redacted_content: str
    original_length: int
    redacted_length: int


class PIIDetector:
    """Advanced PII detection and redaction system."""

    def __init__(self):
        # PII patterns with confidence scores
        self.pii_patterns = {
            'email': {
                'pattern': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
                'confidence': 0.95,
                'replacement': '[EMAIL_REDACTED]'
            },
            'phone': {
                'pattern': r'(\+?1[-.\s]?)?\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})',
                'confidence': 0.90,
                'replacement': '[PHONE_REDACTED]'
            },
            'ssn': {
                'pattern': r'\b\d{3}-?\d{2}-?\d{4}\b',
                'confidence': 0.85,
                'replacement': '[SSN_REDACTED]'
            },
            'credit_card': {
                'pattern': r'\b(?:\d{4}[-\s]?){3}\d{4}\b',
                'confidence': 0.80,
                'replacement': '[CREDIT_CARD_REDACTED]'
            },
            'ip_address': {
                'pattern': r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b',
                'confidence': 0.75,
                'replacement': '[IP_ADDRESS_REDACTED]'
            },
            'url': {
                'pattern': r'https?://(?:[-\w.])+(?:[:\d]+)?(?:/(?:[\w/_.])*(?:\?(?:[\w&=%.])*)?(?:#(?:[\w.])*)?)?',
                'confidence': 0.70,
                'replacement': '[URL_REDACTED]'
            },
            'address': {
                'pattern': r'\d+\s+[A-Za-z\s]+(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Lane|Ln|Drive|Dr|Court|Ct|Place|Pl)',
                'confidence': 0.65,
                'replacement': '[ADDRESS_REDACTED]'
            },
            'date_of_birth': {
                'pattern': r'\b(?:0[1-9]|1[0-2])[/-](?:0[1-9]|[12]\d|3[01])[/-](?:19|20)\d{2}\b',
                'confidence': 0.60,
                'replacement': '[DOB_REDACTED]'
            }
        }

        # Sensitive keywords that might indicate PII context
        self.sensitive_keywords = [
            'password', 'secret', 'token', 'key', 'credential', 'auth',
            'personal', 'private', 'confidential', 'sensitive', 'classified'
        ]

    def detect_pii(self, content: str, confidence_threshold: float = 0.7) -> PIIDetectionResult:
        """Detect PII in content and return detection results."""
        import re

        if not content:
            return PIIDetectionResult(
                has_pii=False,
                pii_types=[],
                confidence_score=0.0,
                redacted_content=content,
                original_length=0,
                redacted_length=0
            )

        detected_pii = []
        redacted_content = content
        max_confidence = 0.0

        # Check each PII pattern
        for pii_type, pattern_info in self.pii_patterns.items():
            pattern = pattern_info['pattern']
            confidence = pattern_info['confidence']
            replacement = pattern_info['replacement']

            matches = re.findall(pattern, content, re.IGNORECASE)
            if matches:
                detected_pii.append(pii_type)
                max_confidence = max(max_confidence, confidence)

                # Redact the content
                redacted_content = re.sub(pattern, replacement, redacted_content, flags=re.IGNORECASE)

        # Check for sensitive keywords (lower confidence)
        content_lower = content.lower()
        for keyword in self.sensitive_keywords:
            if keyword in content_lower:
                if 'sensitive_keyword' not in detected_pii:
                    detected_pii.append('sensitive_keyword')
                max_confidence = max(max_confidence, 0.3)

        has_pii = len(detected_pii) > 0 and max_confidence >= confidence_threshold

        return PIIDetectionResult(
            has_pii=has_pii,
            pii_types=detected_pii,
            confidence_score=max_confidence,
            redacted_content=redacted_content if has_pii else content,
            original_length=len(content),
            redacted_length=len(redacted_content)
        )

    def sanitize_for_logging(self, content: str) -> str:
        """Sanitize content for safe logging by removing PII."""
        result = self.detect_pii(content, confidence_threshold=0.5)
        return result.redacted_content

    def is_safe_for_storage(self, content: str, max_pii_confidence: float = 0.8) -> bool:
        """Check if content is safe for storage without encryption."""
        result = self.detect_pii(content)
        return not result.has_pii or result.confidence_score < max_pii_confidence


class DataPrivacyManager:
    """Comprehensive data privacy and protection manager."""

    def __init__(self):
        self.encryption = DataEncryption()
        self.pii_detector = PIIDetector()
        self.data_classification_cache = {}

    def classify_data_sensitivity(self, content: str) -> str:
        """Classify data sensitivity level."""
        if not content:
            return "public"

        # Check cache first
        content_hash = hashlib.sha256(content.encode()).hexdigest()
        if content_hash in self.data_classification_cache:
            return self.data_classification_cache[content_hash]

        pii_result = self.pii_detector.detect_pii(content)

        if pii_result.has_pii:
            if pii_result.confidence_score >= 0.9:
                classification = "highly_sensitive"
            elif pii_result.confidence_score >= 0.7:
                classification = "sensitive"
            else:
                classification = "restricted"
        else:
            classification = "public"

        # Cache the result
        self.data_classification_cache[content_hash] = classification
        return classification

    def secure_store_data(self, data: str, data_type: str = "general") -> Dict[str, Any]:
        """Securely store data with appropriate protection level."""
        if not data:
            return {"encrypted": False, "data": "", "classification": "public"}

        classification = self.classify_data_sensitivity(data)

        if classification in ["highly_sensitive", "sensitive"]:
            # Encrypt sensitive data
            encrypted_data = self.encryption.encrypt(data)
            return {
                "encrypted": True,
                "data": encrypted_data,
                "classification": classification,
                "data_type": data_type,
                "stored_at": time.time()
            }
        elif classification == "restricted":
            # Redact PII but don't encrypt
            pii_result = self.pii_detector.detect_pii(data)
            return {
                "encrypted": False,
                "data": pii_result.redacted_content,
                "classification": classification,
                "data_type": data_type,
                "pii_redacted": True,
                "stored_at": time.time()
            }
        else:
            # Store as-is for public data
            return {
                "encrypted": False,
                "data": data,
                "classification": classification,
                "data_type": data_type,
                "stored_at": time.time()
            }

    def secure_retrieve_data(self, stored_data: Dict[str, Any]) -> str:
        """Securely retrieve data with appropriate decryption."""
        if not stored_data or "data" not in stored_data:
            return ""

        if stored_data.get("encrypted", False):
            return self.encryption.decrypt(stored_data["data"])
        else:
            return stored_data["data"]

    def anonymize_for_analytics(self, data: str) -> str:
        """Anonymize data for analytics while preserving utility."""
        pii_result = self.pii_detector.detect_pii(data, confidence_threshold=0.5)

        # Replace specific PII with generic tokens
        anonymized = pii_result.redacted_content

        # Additional anonymization for analytics
        import re

        # Replace numbers with generic tokens
        anonymized = re.sub(r'\b\d{4,}\b', '[NUMBER]', anonymized)

        # Replace proper nouns (capitalized words) with generic tokens
        anonymized = re.sub(r'\b[A-Z][a-z]+\b', '[NAME]', anonymized)

        return anonymized

    def generate_privacy_report(self, content: str) -> Dict[str, Any]:
        """Generate a comprehensive privacy analysis report."""
        pii_result = self.pii_detector.detect_pii(content)
        classification = self.classify_data_sensitivity(content)

        return {
            "content_length": len(content),
            "classification": classification,
            "has_pii": pii_result.has_pii,
            "pii_types": pii_result.pii_types,
            "confidence_score": pii_result.confidence_score,
            "redaction_ratio": (pii_result.original_length - pii_result.redacted_length) / pii_result.original_length if pii_result.original_length > 0 else 0,
            "recommended_action": self._get_recommended_action(classification, pii_result),
            "analysis_timestamp": time.time()
        }

    def _get_recommended_action(self, classification: str, pii_result: PIIDetectionResult) -> str:
        """Get recommended action based on data analysis."""
        if classification == "highly_sensitive":
            return "encrypt_and_restrict_access"
        elif classification == "sensitive":
            return "encrypt_or_redact"
        elif classification == "restricted":
            return "redact_pii"
        else:
            return "store_as_is"

class AuditLogger:
    """Advanced audit logging system."""
    
    def __init__(self):
        self.audit_log: List[AuditLogEntry] = []
        self.max_log_size = 10000
        self.risk_calculator = SecurityRiskCalculator()
        
    async def log_action(self, action: str, resource: str, details: Dict[str, Any],
                        user_id: Optional[str] = None, api_key_id: Optional[str] = None,
                        ip_address: str = "", user_agent: str = "", success: bool = True):
        """Log a security-relevant action."""
        
        # Calculate risk score
        risk_score = self.risk_calculator.calculate_risk(
            action, resource, details, ip_address, user_agent
        )
        
        entry = AuditLogEntry(
            id=str(uuid.uuid4()),
            timestamp=time.time(),
            user_id=user_id,
            api_key_id=api_key_id,
            action=action,
            resource=resource,
            details=details,
            ip_address=ip_address,
            user_agent=user_agent,
            success=success,
            risk_score=risk_score
        )
        
        self.audit_log.append(entry)
        
        # Trim log if too large
        if len(self.audit_log) > self.max_log_size:
            self.audit_log = self.audit_log[-self.max_log_size:]
        
        # Log high-risk actions immediately
        if risk_score > 0.7:
            logger.warning(f"High-risk action detected: {action} on {resource} (risk: {risk_score:.2f})")
        
        # Store in persistent storage (simplified)
        await self._persist_audit_entry(entry)
    
    async def _persist_audit_entry(self, entry: AuditLogEntry):
        """Persist audit entry to database."""
        # This would store in a dedicated audit table
        # For now, just log it
        logger.info(f"AUDIT: {entry.action} on {entry.resource} by {entry.user_id or entry.api_key_id}")
    
    def get_audit_trail(self, resource: str, hours: int = 24) -> List[AuditLogEntry]:
        """Get audit trail for a resource."""
        cutoff_time = time.time() - (hours * 3600)
        return [
            entry for entry in self.audit_log
            if entry.resource == resource and entry.timestamp >= cutoff_time
        ]

class SecurityRiskCalculator:
    """Calculate security risk scores for actions."""
    
    def __init__(self):
        self.risk_weights = {
            "failed_login": 0.8,
            "api_key_creation": 0.6,
            "data_export": 0.7,
            "admin_action": 0.9,
            "bulk_operation": 0.5,
            "unusual_ip": 0.4,
            "off_hours": 0.3
        }
    
    def calculate_risk(self, action: str, resource: str, details: Dict[str, Any],
                      ip_address: str, user_agent: str) -> float:
        """Calculate risk score for an action."""
        risk_score = 0.0
        
        # Base risk by action type
        for risk_type, weight in self.risk_weights.items():
            if risk_type in action.lower():
                risk_score += weight
        
        # Additional risk factors
        if self._is_unusual_ip(ip_address):
            risk_score += self.risk_weights.get("unusual_ip", 0.4)
        
        if self._is_off_hours():
            risk_score += self.risk_weights.get("off_hours", 0.3)
        
        # Normalize to 0-1 range
        return min(risk_score, 1.0)
    
    def _is_unusual_ip(self, ip_address: str) -> bool:
        """Check if IP address is unusual."""
        # Simplified check - in production, this would check against known IPs
        return not ip_address.startswith(("127.", "192.168.", "10."))
    
    def _is_off_hours(self) -> bool:
        """Check if current time is off-hours."""
        current_hour = datetime.now().hour
        return current_hour < 6 or current_hour > 22

# Global instances
api_key_manager = APIKeyManager()
request_signer = RequestSigner()
data_encryption = DataEncryption()
pii_detector = PIIDetector()
data_privacy_manager = DataPrivacyManager()
audit_logger = AuditLogger()

def get_api_key_manager() -> APIKeyManager:
    """Get the global API key manager instance."""
    return api_key_manager

def get_data_encryption() -> DataEncryption:
    """Get the global data encryption instance."""
    return data_encryption

def get_pii_detector() -> PIIDetector:
    """Get the global PII detector instance."""
    return pii_detector

def get_data_privacy_manager() -> DataPrivacyManager:
    """Get the global data privacy manager instance."""
    return data_privacy_manager

async def initialize_security():
    """Initialize security systems."""
    logger.info("Initializing advanced security systems")
    
    # Set up default API keys if needed
    await _setup_default_security()
    
    logger.info("Advanced security systems initialized")

async def _setup_default_security():
    """Set up default security configuration."""
    # This would set up initial API keys, encryption, etc.
    logger.info("Security systems configured")

async def shutdown_security():
    """Shutdown security systems."""
    logger.info("Shutting down security systems")
    # Clean up any resources
    logger.info("Security systems shutdown complete")
