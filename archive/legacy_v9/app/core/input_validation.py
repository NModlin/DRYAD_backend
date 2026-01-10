"""
Enhanced Input Validation and Sanitization for DRYAD.AI Backend
Provides comprehensive protection against injection attacks and malicious input.
"""

import re
import html
import urllib.parse
import json
import base64
from typing import Any, Dict, List, Optional, Union, Tuple
from enum import Enum
import unicodedata

from app.core.logging_config import get_logger
from app.core.audit_logging import get_audit_logger, AuditEventType, AuditSeverity

logger = get_logger(__name__)


class ValidationResult:
    """Result of input validation."""
    
    def __init__(self, is_valid: bool, sanitized_value: Any = None, 
                 violations: List[str] = None, risk_score: int = 0):
        self.is_valid = is_valid
        self.sanitized_value = sanitized_value
        self.violations = violations or []
        self.risk_score = risk_score


class InputType(Enum):
    """Types of input for validation."""
    TEXT = "text"
    EMAIL = "email"
    URL = "url"
    FILENAME = "filename"
    JSON = "json"
    SQL_QUERY = "sql_query"
    HTML = "html"
    JAVASCRIPT = "javascript"
    COMMAND = "command"
    PATH = "path"
    API_KEY = "api_key"
    PASSWORD = "password"


class EnhancedInputValidator:
    """Comprehensive input validation and sanitization system."""
    
    def __init__(self):
        self.audit_logger = get_audit_logger()
        
        # SQL injection patterns
        self.sql_injection_patterns = [
            r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|EXECUTE)\b)",
            r"(\b(UNION|OR|AND)\s+\d+\s*=\s*\d+)",
            r"(--|#|/\*|\*/)",
            r"(\b(SCRIPT|JAVASCRIPT|VBSCRIPT|ONLOAD|ONERROR)\b)",
            r"([\'\";].*[\'\";])",
            r"(\bxp_cmdshell\b)",
            r"(\bsp_executesql\b)",
            r"(\bINTO\s+OUTFILE\b)",
            r"(\bLOAD_FILE\b)"
        ]
        
        # XSS patterns
        self.xss_patterns = [
            r"<script[^>]*>.*?</script>",
            r"javascript:",
            r"vbscript:",
            r"on\w+\s*=",
            r"<iframe[^>]*>.*?</iframe>",
            r"<object[^>]*>.*?</object>",
            r"<embed[^>]*>.*?</embed>",
            r"<link[^>]*>",
            r"<meta[^>]*>",
            r"<style[^>]*>.*?</style>",
            r"expression\s*\(",
            r"url\s*\(",
            r"@import"
        ]
        
        # Command injection patterns
        self.command_injection_patterns = [
            r"[;&|`$(){}[\]<>]",
            r"\b(cat|ls|dir|type|copy|move|del|rm|mkdir|rmdir|cd|pwd)\b",
            r"\b(wget|curl|nc|netcat|telnet|ssh|ftp)\b",
            r"\b(python|perl|ruby|php|bash|sh|cmd|powershell)\b",
            r"(\.\./|\.\.\\)",
            r"(/etc/passwd|/etc/shadow|/proc/)",
            r"(\\windows\\|\\system32\\)"
        ]
        
        # Path traversal patterns
        self.path_traversal_patterns = [
            r"(\.\./|\.\.\\)",
            r"(%2e%2e%2f|%2e%2e%5c)",
            r"(\.\.%2f|\.\.%5c)",
            r"(%252e%252e%252f|%252e%252e%255c)",
            r"(\\\.\.\\|/\.\./)",
            r"(\x2e\x2e\x2f|\x2e\x2e\x5c)",
            r"(\.\.\/|\.\.\\)",
            r"(%2e%2e/|%2e%2e\\)",
            r"(\.\.%252f|\.\.%255c)"
        ]
        
        # LDAP injection patterns
        self.ldap_injection_patterns = [
            r"[()&|!*]",
            r"(\x00|\x01|\x02|\x03|\x04|\x05|\x06|\x07|\x08|\x09|\x0a|\x0b|\x0c|\x0d|\x0e|\x0f)",
            r"(\\[0-9a-fA-F]{2})"
        ]
        
        # Compile patterns for performance
        self._compile_patterns()
    
    def _compile_patterns(self):
        """Compile regex patterns for better performance."""
        self.sql_injection_regex = [re.compile(pattern, re.IGNORECASE) for pattern in self.sql_injection_patterns]
        self.xss_regex = [re.compile(pattern, re.IGNORECASE) for pattern in self.xss_patterns]
        self.command_injection_regex = [re.compile(pattern, re.IGNORECASE) for pattern in self.command_injection_patterns]
        self.path_traversal_regex = [re.compile(pattern, re.IGNORECASE) for pattern in self.path_traversal_patterns]
        self.ldap_injection_regex = [re.compile(pattern, re.IGNORECASE) for pattern in self.ldap_injection_patterns]
    
    def validate_input(self, value: Any, input_type: InputType, 
                      max_length: int = 1000, allow_empty: bool = True,
                      user_id: str = None, ip_address: str = None) -> ValidationResult:
        """Comprehensive input validation."""
        if value is None:
            return ValidationResult(allow_empty, None if allow_empty else "", [], 0)
        
        # Convert to string for validation
        str_value = str(value)
        
        # Check length
        if len(str_value) > max_length:
            return ValidationResult(False, str_value[:max_length], 
                                  [f"Input exceeds maximum length of {max_length}"], 30)
        
        # Empty check
        if not str_value.strip() and not allow_empty:
            return ValidationResult(False, "", ["Empty input not allowed"], 10)
        
        violations = []
        risk_score = 0
        
        # Perform type-specific validation
        if input_type == InputType.TEXT:
            violations, risk_score = self._validate_text(str_value)
        elif input_type == InputType.EMAIL:
            violations, risk_score = self._validate_email(str_value)
        elif input_type == InputType.URL:
            violations, risk_score = self._validate_url(str_value)
        elif input_type == InputType.FILENAME:
            violations, risk_score = self._validate_filename(str_value)
        elif input_type == InputType.JSON:
            violations, risk_score = self._validate_json(str_value)
        elif input_type == InputType.SQL_QUERY:
            violations, risk_score = self._validate_sql_query(str_value)
        elif input_type == InputType.HTML:
            violations, risk_score = self._validate_html(str_value)
        elif input_type == InputType.JAVASCRIPT:
            violations, risk_score = self._validate_javascript(str_value)
        elif input_type == InputType.COMMAND:
            violations, risk_score = self._validate_command(str_value)
        elif input_type == InputType.PATH:
            violations, risk_score = self._validate_path(str_value)
        elif input_type == InputType.API_KEY:
            violations, risk_score = self._validate_api_key(str_value)
        elif input_type == InputType.PASSWORD:
            violations, risk_score = self._validate_password(str_value)
        
        # Log security violations
        if violations and risk_score >= 70:
            self._log_security_violation(str_value, input_type, violations, 
                                       risk_score, user_id, ip_address)
        
        # Sanitize the input
        sanitized_value = self._sanitize_input(str_value, input_type)

        # For certain input types, any violation makes it invalid
        strict_types = [InputType.EMAIL, InputType.URL, InputType.API_KEY]
        if input_type in strict_types:
            is_valid = len(violations) == 0
        else:
            is_valid = len(violations) == 0 or risk_score < 50

        return ValidationResult(is_valid, sanitized_value, violations, risk_score)
    
    def _validate_text(self, value: str) -> Tuple[List[str], int]:
        """Validate general text input."""
        violations = []
        risk_score = 0
        
        # Check for SQL injection
        for pattern in self.sql_injection_regex:
            if pattern.search(value):
                violations.append("Potential SQL injection detected")
                risk_score = max(risk_score, 90)
                break
        
        # Check for XSS
        for pattern in self.xss_regex:
            if pattern.search(value):
                violations.append("Potential XSS attack detected")
                risk_score = max(risk_score, 85)
                break
        
        # Check for command injection
        for pattern in self.command_injection_regex:
            if pattern.search(value):
                violations.append("Potential command injection detected")
                risk_score = max(risk_score, 80)
                break
        
        # Check for path traversal
        for pattern in self.path_traversal_regex:
            if pattern.search(value):
                violations.append("Potential path traversal detected")
                risk_score = max(risk_score, 75)
                break
        
        # Check for control characters
        if any(ord(c) < 32 and c not in '\t\n\r' for c in value):
            violations.append("Control characters detected")
            risk_score = max(risk_score, 40)
        
        # Check for excessive special characters
        special_char_ratio = sum(1 for c in value if not c.isalnum() and c not in ' .,!?-_@') / max(len(value), 1)
        if special_char_ratio > 0.3:
            violations.append("Excessive special characters")
            risk_score = max(risk_score, 30)
        
        return violations, risk_score
    
    def _validate_email(self, value: str) -> Tuple[List[str], int]:
        """Validate email input."""
        violations = []
        risk_score = 0

        # Basic email format validation - allow common valid patterns
        email_pattern = r'^[a-zA-Z0-9]([a-zA-Z0-9._+%-]*[a-zA-Z0-9])?@[a-zA-Z0-9]([a-zA-Z0-9.-]*[a-zA-Z0-9])?\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, value):
            violations.append("Invalid email format")
            risk_score = 50

        # Check for consecutive dots
        if '..' in value:
            violations.append("Consecutive dots in email")
            risk_score = max(risk_score, 40)

        # Check for invalid characters at start/end
        if value.startswith('.') or value.startswith('@') or value.endswith('.') or value.endswith('@'):
            violations.append("Invalid email start/end characters")
            risk_score = max(risk_score, 40)

        # Check length
        if len(value) > 254:
            violations.append("Email too long")
            risk_score = max(risk_score, 30)

        # Check for injection attempts in email
        text_violations, text_risk = self._validate_text(value)
        violations.extend(text_violations)
        risk_score = max(risk_score, text_risk)

        return violations, risk_score
    
    def _validate_url(self, value: str) -> Tuple[List[str], int]:
        """Validate URL input."""
        violations = []
        risk_score = 0
        
        # Basic URL format validation
        url_pattern = r'^https?://[^\s/$.?#].[^\s]*$'
        if not re.match(url_pattern, value, re.IGNORECASE):
            violations.append("Invalid URL format")
            risk_score = 20
        
        # Check for dangerous schemes
        dangerous_schemes = ['javascript:', 'data:', 'vbscript:', 'file:', 'ftp:']
        for scheme in dangerous_schemes:
            if value.lower().startswith(scheme):
                violations.append(f"Dangerous URL scheme: {scheme}")
                risk_score = max(risk_score, 80)
        
        # Check for suspicious patterns
        if re.search(r'[<>"\']', value):
            violations.append("Suspicious characters in URL")
            risk_score = max(risk_score, 60)
        
        return violations, risk_score
    
    def _validate_filename(self, value: str) -> Tuple[List[str], int]:
        """Validate filename input."""
        violations = []
        risk_score = 0
        
        # Check for path traversal
        for pattern in self.path_traversal_regex:
            if pattern.search(value):
                violations.append("Path traversal in filename")
                risk_score = max(risk_score, 90)
        
        # Check for dangerous characters
        dangerous_chars = ['<', '>', ':', '"', '|', '?', '*', '\x00']
        for char in dangerous_chars:
            if char in value:
                violations.append(f"Dangerous character in filename: {char}")
                risk_score = max(risk_score, 70)
        
        # Check for reserved names (Windows)
        reserved_names = ['CON', 'PRN', 'AUX', 'NUL', 'COM1', 'COM2', 'COM3', 'COM4', 
                         'COM5', 'COM6', 'COM7', 'COM8', 'COM9', 'LPT1', 'LPT2', 
                         'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9']
        if value.upper().split('.')[0] in reserved_names:
            violations.append("Reserved filename")
            risk_score = max(risk_score, 50)
        
        return violations, risk_score

    def _validate_sql_query(self, value: str) -> Tuple[List[str], int]:
        """Validate SQL query input (for admin/debug purposes only)."""
        violations = []
        risk_score = 0

        # Check for dangerous SQL operations
        dangerous_operations = ['DROP', 'DELETE', 'TRUNCATE', 'ALTER', 'CREATE', 'EXEC', 'EXECUTE']
        for op in dangerous_operations:
            if re.search(rf'\b{op}\b', value, re.IGNORECASE):
                violations.append(f"Dangerous SQL operation: {op}")
                risk_score = max(risk_score, 95)

        # Check for SQL injection patterns
        for pattern in self.sql_injection_regex:
            if pattern.search(value):
                violations.append("SQL injection pattern detected")
                risk_score = max(risk_score, 90)
                break

        return violations, risk_score

    def _validate_html(self, value: str) -> Tuple[List[str], int]:
        """Validate HTML input."""
        violations = []
        risk_score = 0

        # Check for XSS patterns
        for pattern in self.xss_regex:
            if pattern.search(value):
                violations.append("XSS pattern in HTML detected")
                risk_score = max(risk_score, 85)
                break

        # Check for dangerous HTML tags
        dangerous_tags = ['script', 'iframe', 'object', 'embed', 'form', 'input', 'meta', 'link']
        for tag in dangerous_tags:
            if re.search(rf'<{tag}[^>]*>', value, re.IGNORECASE):
                violations.append(f"Dangerous HTML tag: {tag}")
                risk_score = max(risk_score, 80)

        return violations, risk_score

    def _validate_javascript(self, value: str) -> Tuple[List[str], int]:
        """Validate JavaScript input."""
        violations = []
        risk_score = 0

        # Check for dangerous JavaScript functions
        dangerous_functions = ['eval', 'Function', 'setTimeout', 'setInterval', 'document.write',
                             'innerHTML', 'outerHTML', 'document.cookie', 'localStorage', 'sessionStorage']
        for func in dangerous_functions:
            if func in value:
                violations.append(f"Dangerous JavaScript function: {func}")
                risk_score = max(risk_score, 90)

        # Check for XSS patterns
        for pattern in self.xss_regex:
            if pattern.search(value):
                violations.append("XSS pattern in JavaScript detected")
                risk_score = max(risk_score, 85)
                break

        return violations, risk_score

    def _validate_command(self, value: str) -> Tuple[List[str], int]:
        """Validate command input."""
        violations = []
        risk_score = 0

        # Check for command injection patterns
        for pattern in self.command_injection_regex:
            if pattern.search(value):
                violations.append("Command injection pattern detected")
                risk_score = max(risk_score, 95)
                break

        # Check for dangerous commands
        dangerous_commands = ['rm', 'del', 'format', 'fdisk', 'mkfs', 'dd', 'wget', 'curl', 'nc', 'netcat']
        for cmd in dangerous_commands:
            if re.search(rf'\b{cmd}\b', value, re.IGNORECASE):
                violations.append(f"Dangerous command: {cmd}")
                risk_score = max(risk_score, 90)

        return violations, risk_score

    def _validate_path(self, value: str) -> Tuple[List[str], int]:
        """Validate file path input."""
        violations = []
        risk_score = 0

        # URL decode the value to catch encoded traversal attempts
        try:
            decoded_value = urllib.parse.unquote(value)
            # Double decode to catch double-encoded attempts
            double_decoded = urllib.parse.unquote(decoded_value)
        except Exception:
            decoded_value = value
            double_decoded = value

        # Check for path traversal in original, decoded, and double-decoded values
        for test_value in [value, decoded_value, double_decoded]:
            for pattern in self.path_traversal_regex:
                if pattern.search(test_value):
                    violations.append("Path traversal detected")
                    risk_score = max(risk_score, 90)
                    break
            if violations:  # Break outer loop if violation found
                break

        # Check for absolute paths to sensitive directories
        sensitive_paths = ['/etc/', '/proc/', '/sys/', '/dev/', 'C:\\Windows\\', 'C:\\System32\\']
        for test_value in [value, decoded_value, double_decoded]:
            for path in sensitive_paths:
                if test_value.startswith(path):
                    violations.append(f"Access to sensitive path: {path}")
                    risk_score = max(risk_score, 80)
                    break
            if violations:  # Break if violation found
                break

        return violations, risk_score

    def _validate_api_key(self, value: str) -> Tuple[List[str], int]:
        """Validate API key input."""
        violations = []
        risk_score = 0

        # Check format (should be alphanumeric with possible underscores/hyphens)
        if not re.match(r'^[a-zA-Z0-9_-]+$', value):
            violations.append("Invalid API key format")
            risk_score = 30

        # Check length (should be reasonable)
        if len(value) < 16 or len(value) > 128:
            violations.append("API key length suspicious")
            risk_score = max(risk_score, 40)

        return violations, risk_score

    def _validate_password(self, value: str) -> Tuple[List[str], int]:
        """Validate password input."""
        violations = []
        risk_score = 0

        # Check for common weak passwords
        weak_passwords = ['password', '123456', 'admin', 'root', 'guest', 'test']
        if value.lower() in weak_passwords:
            violations.append("Weak password detected")
            risk_score = 60

        # Check minimum strength requirements
        if len(value) < 8:
            violations.append("Password too short")
            risk_score = max(risk_score, 40)

        return violations, risk_score

    def _sanitize_input(self, value: str, input_type: InputType) -> str:
        """Sanitize input based on type."""
        if input_type == InputType.HTML:
            # HTML escape
            return html.escape(value)
        elif input_type == InputType.URL:
            # URL encode
            return urllib.parse.quote(value, safe=':/?#[]@!$&\'()*+,;=')
        elif input_type == InputType.FILENAME:
            # Remove dangerous characters
            sanitized = re.sub(r'[<>:"|?*\x00-\x1f]', '', value)
            return sanitized.strip()
        elif input_type == InputType.PATH:
            # Normalize path and remove traversal attempts
            sanitized = value.replace('..', '').replace('//', '/').replace('\\\\', '\\')
            return sanitized.strip()
        else:
            # General sanitization
            # Remove null bytes and control characters
            sanitized = ''.join(c for c in value if ord(c) >= 32 or c in '\t\n\r')
            # Normalize unicode
            sanitized = unicodedata.normalize('NFKC', sanitized)
            return sanitized.strip()

    def _log_security_violation(self, value: str, input_type: InputType,
                              violations: List[str], risk_score: int,
                              user_id: str = None, ip_address: str = None):
        """Log security violations for monitoring."""
        try:
            details = {
                "input_type": input_type.value,
                "violations": violations,
                "risk_score": risk_score,
                "input_length": len(value),
                "input_preview": value[:100] + "..." if len(value) > 100 else value
            }

            self.audit_logger.log_security_event(
                event_type=AuditEventType.SECURITY_VIOLATION,
                severity=AuditSeverity.HIGH if risk_score >= 80 else AuditSeverity.MEDIUM,
                ip_address=ip_address,
                user_id=user_id,
                details=details,
                risk_score=risk_score
            )

        except Exception as e:
            logger.error(f"Error logging security violation: {e}")


# Global validator instance
_input_validator: Optional[EnhancedInputValidator] = None


def get_input_validator() -> EnhancedInputValidator:
    """Get the global input validator instance."""
    global _input_validator
    if _input_validator is None:
        _input_validator = EnhancedInputValidator()
    return _input_validator


def validate_input(value: Any, input_type: InputType, **kwargs) -> ValidationResult:
    """Convenience function for input validation."""
    validator = get_input_validator()
    return validator.validate_input(value, input_type, **kwargs)
