"""
Isolation Enforcer
The Laboratory - Level 5

Ensures experimental environments have no access to production systems.
Validates isolation constraints and prevents accidental production access.
"""

from typing import Dict, Any, List, Optional
from pydantic import BaseModel

from dryad.services.logging.logger import StructuredLogger

logger = StructuredLogger("dryad.laboratory.isolation_enforcer")


class IsolationViolation(BaseModel):
    """Isolation violation record."""
    violation_type: str
    severity: str  # low, medium, high, critical
    description: str
    environment_id: str


class IsolationEnforcer:
    """
    Level 5 Component: Isolation Enforcer
    
    Enforces isolation constraints for experimental environments.
    Prevents production access and validates safety boundaries.
    """
    
    def __init__(self):
        self.violations: List[IsolationViolation] = []
        self.production_paths = [
            "data/DRYAD.AI.db",  # Production database
            "data/production",   # Production data directory
        ]
        logger.log_info("isolation_enforcer_initialized", {})
    
    def validate_database_access(
        self,
        environment_id: str,
        database_path: str
    ) -> bool:
        """
        Validate that database access is isolated.
        
        Args:
            environment_id: Environment identifier
            database_path: Path to database being accessed
            
        Returns:
            True if access is allowed
        """
        # Check if accessing production database
        for prod_path in self.production_paths:
            if database_path == prod_path:
                violation = IsolationViolation(
                    violation_type="production_database_access",
                    severity="critical",
                    description=f"Attempted to access production database: {database_path}",
                    environment_id=environment_id
                )
                self.violations.append(violation)
                
                logger.log_error(
                    "isolation_violation",
                    {
                        "environment_id": environment_id,
                        "violation_type": "production_database_access",
                        "database_path": database_path
                    }
                )
                
                return False
        
        # Check if database is in laboratory directory
        if not database_path.startswith("data/laboratory/"):
            violation = IsolationViolation(
                violation_type="database_outside_laboratory",
                severity="high",
                description=f"Database not in laboratory directory: {database_path}",
                environment_id=environment_id
            )
            self.violations.append(violation)
            
            logger.log_error(
                "isolation_violation",
                {
                    "environment_id": environment_id,
                    "violation_type": "database_outside_laboratory",
                    "database_path": database_path
                }
            )
            
            return False
        
        return True
    
    def validate_network_access(
        self,
        environment_id: str,
        target_host: str,
        target_port: int
    ) -> bool:
        """
        Validate that network access is isolated.
        
        Args:
            environment_id: Environment identifier
            target_host: Target host
            target_port: Target port
            
        Returns:
            True if access is allowed
        """
        # For Level 5, we allow localhost access for Redis/ChromaDB
        # but log it for monitoring
        if target_host in ["localhost", "127.0.0.1"]:
            logger.log_info(
                "network_access_allowed",
                {
                    "environment_id": environment_id,
                    "target": f"{target_host}:{target_port}"
                }
            )
            return True
        
        # Block external network access
        violation = IsolationViolation(
            violation_type="external_network_access",
            severity="high",
            description=f"Attempted external network access: {target_host}:{target_port}",
            environment_id=environment_id
        )
        self.violations.append(violation)
        
        logger.log_error(
            "isolation_violation",
            {
                "environment_id": environment_id,
                "violation_type": "external_network_access",
                "target": f"{target_host}:{target_port}"
            }
        )
        
        return False
    
    def validate_file_access(
        self,
        environment_id: str,
        file_path: str,
        access_type: str  # read, write, delete
    ) -> bool:
        """
        Validate that file access is isolated.
        
        Args:
            environment_id: Environment identifier
            file_path: Path to file
            access_type: Type of access (read, write, delete)
            
        Returns:
            True if access is allowed
        """
        # Block access to production paths
        for prod_path in self.production_paths:
            if file_path.startswith(prod_path):
                violation = IsolationViolation(
                    violation_type="production_file_access",
                    severity="critical",
                    description=f"Attempted {access_type} access to production file: {file_path}",
                    environment_id=environment_id
                )
                self.violations.append(violation)
                
                logger.log_error(
                    "isolation_violation",
                    {
                        "environment_id": environment_id,
                        "violation_type": "production_file_access",
                        "file_path": file_path,
                        "access_type": access_type
                    }
                )
                
                return False
        
        # Allow access to laboratory directory
        if file_path.startswith("data/laboratory/"):
            return True
        
        # Log other access for monitoring
        logger.log_info(
            "file_access",
            {
                "environment_id": environment_id,
                "file_path": file_path,
                "access_type": access_type
            }
        )
        
        return True
    
    def get_violations(
        self,
        environment_id: Optional[str] = None,
        severity: Optional[str] = None
    ) -> List[IsolationViolation]:
        """
        Get isolation violations.
        
        Args:
            environment_id: Filter by environment
            severity: Filter by severity
            
        Returns:
            List of violations
        """
        violations = self.violations
        
        if environment_id:
            violations = [v for v in violations if v.environment_id == environment_id]
        
        if severity:
            violations = [v for v in violations if v.severity == severity]
        
        return violations
    
    def clear_violations(self, environment_id: str):
        """Clear violations for an environment."""
        self.violations = [v for v in self.violations if v.environment_id != environment_id]

