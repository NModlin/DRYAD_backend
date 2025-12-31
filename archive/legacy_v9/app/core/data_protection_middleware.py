"""
Data Protection Middleware for DRYAD.AI Backend
Provides automatic data encryption, PII detection, and privacy protection for requests and responses.
"""

import json
import time
from typing import Dict, Any, Optional
from fastapi import Request, Response
from fastapi.responses import JSONResponse

from app.core.logging_config import get_logger
from app.core.advanced_security import get_data_privacy_manager, get_pii_detector

logger = get_logger(__name__)


class DataProtectionMiddleware:
    """Middleware for automatic data protection and privacy enforcement."""
    
    def __init__(self):
        self.privacy_manager = get_data_privacy_manager()
        self.pii_detector = get_pii_detector()
        
        # Endpoints that require special data protection
        self.protected_endpoints = {
            '/api/v1/documents/upload',
            '/api/v1/agent/invoke',
            '/api/v1/multi-agent/invoke',
            '/api/v1/chat',
            '/api/v1/history'
        }
        
        # Response fields that should be checked for PII
        self.sensitive_response_fields = {
            'message', 'content', 'text', 'description', 'summary',
            'analysis', 'result', 'output', 'response'
        }
    
    async def __call__(self, request: Request, call_next):
        """Process request and response with data protection."""
        start_time = time.time()
        
        # Check if this endpoint needs protection
        needs_protection = any(
            protected_path in str(request.url.path) 
            for protected_path in self.protected_endpoints
        )
        
        if needs_protection:
            # Process request data
            await self._protect_request_data(request)
        
        # Call the next middleware/endpoint
        response = await call_next(request)
        
        if needs_protection and isinstance(response, JSONResponse):
            # Process response data
            response = await self._protect_response_data(response, request)
        
        # Add privacy headers
        self._add_privacy_headers(response)
        
        # Log data protection metrics
        processing_time = time.time() - start_time
        if needs_protection:
            logger.info(f"Data protection applied to {request.url.path} in {processing_time:.3f}s")
        
        return response
    
    async def _protect_request_data(self, request: Request):
        """Protect sensitive data in request."""
        try:
            # Check if request has body
            if hasattr(request, '_body'):
                return
            
            # Read and analyze request body
            body = await request.body()
            if not body:
                return
            
            try:
                # Parse JSON body
                json_body = json.loads(body.decode('utf-8'))
                
                # Check for PII in request data
                pii_found = False
                for key, value in json_body.items():
                    if isinstance(value, str):
                        pii_result = self.pii_detector.detect_pii(value)
                        if pii_result.has_pii:
                            pii_found = True
                            logger.warning(f"PII detected in request field '{key}': {pii_result.pii_types}")
                
                if pii_found:
                    # Add PII detection flag to request state
                    request.state.pii_detected = True
                    request.state.requires_encryption = True
                
            except json.JSONDecodeError:
                # Not JSON, check raw body for PII
                body_str = body.decode('utf-8', errors='ignore')
                pii_result = self.pii_detector.detect_pii(body_str)
                if pii_result.has_pii:
                    request.state.pii_detected = True
                    logger.warning(f"PII detected in request body: {pii_result.pii_types}")
        
        except Exception as e:
            logger.error(f"Error protecting request data: {e}")
    
    async def _protect_response_data(self, response: JSONResponse, request: Request) -> JSONResponse:
        """Protect sensitive data in response."""
        try:
            # Get response content
            if not hasattr(response, 'body'):
                return response
            
            # Parse response body
            response_body = response.body.decode('utf-8')
            response_data = json.loads(response_body)
            
            # Check and protect sensitive fields
            protected_data = self._protect_response_fields(response_data, request)
            
            # Create new response with protected data
            new_response = JSONResponse(
                content=protected_data,
                status_code=response.status_code,
                headers=dict(response.headers)
            )
            
            return new_response
        
        except Exception as e:
            logger.error(f"Error protecting response data: {e}")
            return response
    
    def _protect_response_fields(self, data: Any, request: Request) -> Any:
        """Recursively protect sensitive fields in response data."""
        if isinstance(data, dict):
            protected_dict = {}
            for key, value in data.items():
                if key.lower() in self.sensitive_response_fields:
                    # Check if this field contains PII
                    if isinstance(value, str):
                        pii_result = self.pii_detector.detect_pii(value)
                        if pii_result.has_pii:
                            # Log PII detection
                            logger.warning(f"PII detected in response field '{key}': {pii_result.pii_types}")
                            
                            # Add privacy notice to response
                            protected_dict[key] = pii_result.redacted_content
                            protected_dict[f"{key}_privacy_notice"] = "Content has been automatically redacted for privacy protection"
                        else:
                            protected_dict[key] = value
                    else:
                        protected_dict[key] = self._protect_response_fields(value, request)
                else:
                    protected_dict[key] = self._protect_response_fields(value, request)
            return protected_dict
        
        elif isinstance(data, list):
            return [self._protect_response_fields(item, request) for item in data]
        
        else:
            return data
    
    def _add_privacy_headers(self, response: Response):
        """Add privacy-related headers to response."""
        response.headers["X-Content-Privacy"] = "protected"
        response.headers["X-PII-Detection"] = "enabled"
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, private"
        response.headers["Pragma"] = "no-cache"


class DatabaseEncryptionHelper:
    """Helper for database field encryption and decryption."""

    def __init__(self):
        self.privacy_manager = get_data_privacy_manager()
        self.pii_detector = get_pii_detector()
    
    def encrypt_sensitive_field(self, field_name: str, value: str) -> Dict[str, Any]:
        """Encrypt a database field if it contains sensitive data."""
        if not value:
            return {"value": value, "encrypted": False}
        
        # Classify data sensitivity
        classification = self.privacy_manager.classify_data_sensitivity(value)
        
        if classification in ["highly_sensitive", "sensitive"]:
            # Encrypt the value
            encrypted_value = self.privacy_manager.encryption.encrypt(value)
            return {
                "value": encrypted_value,
                "encrypted": True,
                "classification": classification,
                "field_name": field_name,
                "encrypted_at": time.time()
            }
        else:
            return {"value": value, "encrypted": False, "classification": classification}
    
    def decrypt_sensitive_field(self, encrypted_data: Dict[str, Any]) -> str:
        """Decrypt a database field."""
        if not encrypted_data or not encrypted_data.get("encrypted", False):
            return encrypted_data.get("value", "") if encrypted_data else ""
        
        try:
            return self.privacy_manager.encryption.decrypt(encrypted_data["value"])
        except Exception as e:
            logger.error(f"Failed to decrypt field: {e}")
            return "[DECRYPTION_FAILED]"
    
    def should_encrypt_field(self, field_name: str, value: str) -> bool:
        """Determine if a field should be encrypted based on name and content."""
        # Field names that typically contain sensitive data
        sensitive_field_names = {
            'email', 'phone', 'address', 'ssn', 'credit_card',
            'password', 'secret', 'token', 'key', 'personal_info',
            'medical_info', 'financial_info', 'private_notes'
        }
        
        # Check field name
        field_lower = field_name.lower()
        if any(sensitive_name in field_lower for sensitive_name in sensitive_field_names):
            return True
        
        # Check content for PII
        if value:
            pii_result = self.pii_detector.detect_pii(value)
            return pii_result.has_pii and pii_result.confidence_score >= 0.7
        
        return False


class FileEncryptionHelper:
    """Helper for file encryption and decryption."""

    def __init__(self):
        self.privacy_manager = get_data_privacy_manager()
        self.pii_detector = get_pii_detector()
    
    def encrypt_file_if_needed(self, file_content: bytes, filename: str, 
                              content_type: str = None) -> Dict[str, Any]:
        """Encrypt file if it contains sensitive data."""
        if not file_content:
            return {"content": file_content, "encrypted": False}
        
        # Check if file type typically contains sensitive data
        sensitive_types = {
            'application/pdf', 'text/plain', 'application/msword',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        }
        
        should_check_content = (
            content_type in sensitive_types or
            any(ext in filename.lower() for ext in ['.pdf', '.doc', '.docx', '.txt'])
        )
        
        if should_check_content:
            # Check content for PII (for text-based files)
            try:
                if content_type == 'text/plain' or filename.lower().endswith('.txt'):
                    text_content = file_content.decode('utf-8', errors='ignore')
                    pii_result = self.pii_detector.detect_pii(text_content)
                    
                    if pii_result.has_pii and pii_result.confidence_score >= 0.7:
                        # Encrypt the file
                        encrypted_content = self.privacy_manager.encryption.encrypt_file_content(
                            file_content, filename
                        )
                        return {
                            "content": encrypted_content,
                            "encrypted": True,
                            "pii_detected": True,
                            "pii_types": pii_result.pii_types,
                            "original_size": len(file_content),
                            "encrypted_size": len(encrypted_content)
                        }
            except Exception as e:
                logger.warning(f"Could not analyze file content for PII: {e}")
        
        return {"content": file_content, "encrypted": False}
    
    def decrypt_file_if_needed(self, file_data: Dict[str, Any]) -> bytes:
        """Decrypt file if it was encrypted."""
        if not file_data.get("encrypted", False):
            return file_data.get("content", b"")
        
        try:
            encrypted_content = file_data["content"]
            decrypted_content, metadata = self.privacy_manager.encryption.decrypt_file_content(
                encrypted_content
            )
            return decrypted_content
        except Exception as e:
            logger.error(f"Failed to decrypt file: {e}")
            return b""


# Global instances
data_protection_middleware = DataProtectionMiddleware()
db_encryption_helper = DatabaseEncryptionHelper()
file_encryption_helper = FileEncryptionHelper()

def get_data_protection_middleware() -> DataProtectionMiddleware:
    """Get the global data protection middleware instance."""
    return data_protection_middleware

def get_db_encryption_helper() -> DatabaseEncryptionHelper:
    """Get the global database encryption helper instance."""
    return db_encryption_helper

def get_file_encryption_helper() -> FileEncryptionHelper:
    """Get the global file encryption helper instance."""
    return file_encryption_helper
