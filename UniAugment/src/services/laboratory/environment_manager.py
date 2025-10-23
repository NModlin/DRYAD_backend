"""
Environment Manager
The Laboratory - Level 5

Manages isolated sandbox environments for safe experimentation.
Creates, configures, and destroys experimental environments.
"""

import uuid
import shutil
import os
from typing import Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel

from app.services.logging.logger import StructuredLogger

logger = StructuredLogger("dryad.laboratory.environment_manager")


class EnvironmentConfig(BaseModel):
    """Configuration for experimental environment."""
    environment_id: str
    experiment_id: str
    database_path: str
    isolated: bool = True
    created_at: str


class EnvironmentManager:
    """
    Level 5 Component: Environment Manager
    
    Manages lifecycle of isolated experimental environments.
    Ensures experiments run safely without affecting production.
    """
    
    def __init__(self, base_path: str = "data/laboratory"):
        self.base_path = base_path
        self.environments: Dict[str, EnvironmentConfig] = {}
        
        # Ensure laboratory directory exists
        os.makedirs(base_path, exist_ok=True)
        
        logger.log_info("environment_manager_initialized", {"base_path": base_path})
    
    def create_environment(
        self,
        experiment_id: str,
        clone_production: bool = True
    ) -> EnvironmentConfig:
        """
        Create isolated experimental environment.
        
        Args:
            experiment_id: Experiment identifier
            clone_production: Whether to clone production data
            
        Returns:
            Environment configuration
        """
        try:
            environment_id = f"env_{uuid.uuid4().hex[:12]}"
            env_path = os.path.join(self.base_path, environment_id)
            
            # Create environment directory
            os.makedirs(env_path, exist_ok=True)
            
            # Create isolated database
            db_path = os.path.join(env_path, "experiment.db")
            
            if clone_production:
                # Clone production database (simplified for Level 5)
                production_db = "data/DRYAD.AI.db"
                if os.path.exists(production_db):
                    shutil.copy2(production_db, db_path)
                    logger.log_info(
                        "production_data_cloned",
                        {"environment_id": environment_id, "source": production_db}
                    )
            
            # Create environment config
            config = EnvironmentConfig(
                environment_id=environment_id,
                experiment_id=experiment_id,
                database_path=db_path,
                isolated=True,
                created_at=datetime.now().isoformat()
            )
            
            self.environments[environment_id] = config
            
            logger.log_info(
                "environment_created",
                {
                    "environment_id": environment_id,
                    "experiment_id": experiment_id,
                    "isolated": True
                }
            )
            
            return config
            
        except Exception as e:
            logger.log_error("environment_creation_failed", {"error": str(e)})
            raise
    
    def get_environment(
        self,
        environment_id: str
    ) -> Optional[EnvironmentConfig]:
        """
        Retrieve environment configuration.
        
        Args:
            environment_id: Environment identifier
            
        Returns:
            Environment config if found
        """
        return self.environments.get(environment_id)
    
    def destroy_environment(
        self,
        environment_id: str
    ) -> bool:
        """
        Destroy experimental environment and clean up resources.
        
        Args:
            environment_id: Environment identifier
            
        Returns:
            True if successful
        """
        try:
            config = self.environments.get(environment_id)
            if not config:
                return False
            
            # Remove environment directory
            env_path = os.path.join(self.base_path, environment_id)
            if os.path.exists(env_path):
                shutil.rmtree(env_path)
            
            # Remove from tracking
            del self.environments[environment_id]
            
            logger.log_info(
                "environment_destroyed",
                {"environment_id": environment_id}
            )
            
            return True
            
        except Exception as e:
            logger.log_error("environment_destruction_failed", {"error": str(e)})
            return False
    
    def list_environments(self) -> list[EnvironmentConfig]:
        """
        List all active experimental environments.
        
        Returns:
            List of environment configurations
        """
        return list(self.environments.values())
    
    def is_isolated(
        self,
        environment_id: str
    ) -> bool:
        """
        Check if environment is properly isolated.
        
        Args:
            environment_id: Environment identifier
            
        Returns:
            True if isolated
        """
        config = self.environments.get(environment_id)
        if not config:
            return False
        
        # Verify isolation
        # 1. Database is in laboratory directory
        if not config.database_path.startswith(self.base_path):
            logger.log_error(
                "isolation_violation",
                {
                    "environment_id": environment_id,
                    "reason": "database_outside_laboratory"
                }
            )
            return False
        
        # 2. Environment is marked as isolated
        if not config.isolated:
            logger.log_error(
                "isolation_violation",
                {
                    "environment_id": environment_id,
                    "reason": "not_marked_isolated"
                }
            )
            return False
        
        return True

