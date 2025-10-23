"""
Dryad - Quantum-Inspired Knowledge Tree Module

This module provides the core Dryad functionality for DRYAD.AI,
enabling quantum-inspired knowledge exploration through branching paths
with context isolation.

Core Concepts:
- Grove: A project or workspace containing a knowledge tree
- Branch: A node in the tree representing an exploration path  
- Vessel: A context container storing the state of a branch
- Oracle: An AI provider that can be consulted for insights

Version: 2.0.0 (Python port from TypeScript 1.0.0)
"""

from .services.grove_service import GroveService
from .services.branch_service import BranchService  
from .services.vessel_service import VesselService
from .services.oracle_service import OracleService
from .models.grove import Grove
from .models.branch import Branch, BranchStatus, BranchPriority
from .models.vessel import Vessel
from .models.dialogue import Dialogue
from .schemas.grove_schemas import GroveCreate, GroveUpdate, GroveResponse
from .schemas.branch_schemas import BranchCreate, BranchUpdate, BranchResponse
from .schemas.vessel_schemas import VesselCreate, VesselResponse
from .core.errors import DryadError, DryadErrorCode

__version__ = "2.0.0"
__all__ = [
    # Services
    "GroveService",
    "BranchService", 
    "VesselService",
    "OracleService",
    
    # Models
    "Grove",
    "Branch",
    "BranchStatus", 
    "BranchPriority",
    "Vessel",
    "Dialogue",
    
    # Schemas
    "GroveCreate",
    "GroveUpdate", 
    "GroveResponse",
    "BranchCreate",
    "BranchUpdate",
    "BranchResponse", 
    "VesselCreate",
    "VesselResponse",
    
    # Errors
    "DryadError",
    "DryadErrorCode",
]
