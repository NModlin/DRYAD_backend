"""
Dryad Error Classes

Structured error handling for Dryad services.
Ported from TypeScript services/errors.ts
"""

from enum import Enum
from typing import Dict, Any, Optional
from datetime import datetime, timezone


class DryadErrorCode(str, Enum):
    """Error codes for Dryad operations."""
    
    # Grove errors
    GROVE_NOT_FOUND = "GROVE_NOT_FOUND"
    GROVE_CREATE_FAILED = "GROVE_CREATE_FAILED"
    GROVE_UPDATE_FAILED = "GROVE_UPDATE_FAILED"
    GROVE_DELETE_FAILED = "GROVE_DELETE_FAILED"
    GROVE_INVALID_PARAMS = "GROVE_INVALID_PARAMS"
    
    # Branch errors
    BRANCH_NOT_FOUND = "BRANCH_NOT_FOUND"
    BRANCH_CREATE_FAILED = "BRANCH_CREATE_FAILED"
    BRANCH_UPDATE_FAILED = "BRANCH_UPDATE_FAILED"
    BRANCH_DELETE_FAILED = "BRANCH_DELETE_FAILED"
    BRANCH_INVALID_PARAMS = "BRANCH_INVALID_PARAMS"
    BRANCH_INVALID_PARENT = "BRANCH_INVALID_PARENT"
    
    # Vessel errors
    VESSEL_NOT_FOUND = "VESSEL_NOT_FOUND"
    VESSEL_CREATE_FAILED = "VESSEL_CREATE_FAILED"
    VESSEL_UPDATE_FAILED = "VESSEL_UPDATE_FAILED"
    VESSEL_LOAD_FAILED = "VESSEL_LOAD_FAILED"
    VESSEL_SAVE_FAILED = "VESSEL_SAVE_FAILED"
    
    # Oracle errors
    ORACLE_PROVIDER_NOT_FOUND = "ORACLE_PROVIDER_NOT_FOUND"
    ORACLE_CONSULTATION_FAILED = "ORACLE_CONSULTATION_FAILED"
    ORACLE_INVALID_CONFIG = "ORACLE_INVALID_CONFIG"
    
    # Validation errors
    VALIDATION_FAILED = "VALIDATION_FAILED"
    INVALID_INPUT = "INVALID_INPUT"
    
    # Database errors
    DATABASE_ERROR = "DATABASE_ERROR"
    TRANSACTION_FAILED = "TRANSACTION_FAILED"
    
    # General errors
    INTERNAL_ERROR = "INTERNAL_ERROR"
    NOT_IMPLEMENTED = "NOT_IMPLEMENTED"


class DryadError(Exception):
    """Base error class for Dryad services."""
    
    def __init__(
        self,
        code: DryadErrorCode,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None
    ):
        super().__init__(message)
        self.code = code
        self.message = message
        self.details = details or {}
        self.cause = cause
        self.timestamp = datetime.now(timezone.utc)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert error to dictionary representation."""
        return {
            "code": self.code.value,
            "message": self.message,
            "details": self.details,
            "timestamp": self.timestamp.isoformat(),
            "cause": str(self.cause) if self.cause else None
        }


class ValidationError(DryadError):
    """Validation error for invalid input parameters."""
    
    def __init__(
        self,
        message: str,
        validation_errors: list[str],
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(DryadErrorCode.VALIDATION_FAILED, message, details)
        self.validation_errors = validation_errors


class NotFoundError(DryadError):
    """Not found error for missing resources."""

    def __init__(self, resource_type: str, resource_id: str):
        # Map resource types to error codes
        resource_type_normalized = resource_type.upper().replace(" ", "_")
        code_str = f"{resource_type_normalized}_NOT_FOUND"

        # Try to get the error code, fall back to generic NOT_FOUND
        try:
            code = DryadErrorCode(code_str)
        except ValueError:
            # If the specific error code doesn't exist, use a generic one based on resource type
            if "BRANCH" in resource_type_normalized:
                code = DryadErrorCode.BRANCH_NOT_FOUND
            elif "GROVE" in resource_type_normalized:
                code = DryadErrorCode.GROVE_NOT_FOUND
            elif "VESSEL" in resource_type_normalized:
                code = DryadErrorCode.VESSEL_NOT_FOUND
            else:
                code = DryadErrorCode.INTERNAL_ERROR

        message = f"{resource_type} with ID {resource_id} not found"
        details = {"resource_type": resource_type, "resource_id": resource_id}
        super().__init__(code, message, details)
        self.resource_type = resource_type
        self.resource_id = resource_id


class DatabaseError(DryadError):
    """Database error for database operations."""
    
    def __init__(
        self,
        message: str,
        cause: Optional[Exception] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(DryadErrorCode.DATABASE_ERROR, message, details, cause)


def wrap_error(
    error: Exception,
    code: DryadErrorCode,
    message: str,
    details: Optional[Dict[str, Any]] = None
) -> DryadError:
    """Helper function to wrap unknown errors."""
    if isinstance(error, DryadError):
        return error
    
    return DryadError(code, message, details, error)


def is_dryad_error(error: Exception) -> bool:
    """Helper function to check if error is a Dryad error."""
    return isinstance(error, DryadError)


def get_error_message(error: Exception) -> str:
    """Helper function to get error message safely."""
    return str(error)
