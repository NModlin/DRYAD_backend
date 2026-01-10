"""
Dryad Core Module

Contains core functionality for vessel generation, inheritance,
persistence, and other fundamental Dryad operations.
"""

from .errors import (
    DryadError, DryadErrorCode, ValidationError, NotFoundError,
    DatabaseError, wrap_error, is_dryad_error, get_error_message
)
from .vessel_generator import VesselGenerator, VesselContent, VesselCreationOptions
from .vessel_inheritance import VesselInheritanceManager
from .vessel_persistence import VesselPersistenceService

__all__ = [
    # Error handling
    "DryadError", "DryadErrorCode", "ValidationError", "NotFoundError",
    "DatabaseError", "wrap_error", "is_dryad_error", "get_error_message",

    # Vessel system
    "VesselGenerator", "VesselContent", "VesselCreationOptions",
    "VesselInheritanceManager", "VesselPersistenceService"
]

from .errors import DryadError, DryadErrorCode, ValidationError, NotFoundError, DatabaseError
from .vessel_generator import VesselGenerator
from .vessel_inheritance import VesselInheritanceManager
from .vessel_persistence import VesselPersistenceService

__all__ = [
    "DryadError",
    "DryadErrorCode", 
    "ValidationError",
    "NotFoundError",
    "DatabaseError",
    "VesselGenerator",
    "VesselInheritanceManager", 
    "VesselPersistenceService",
]
