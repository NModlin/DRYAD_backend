"""
Code Editor Agent - Tier 2 Specialist Agent
Handles code editing, validation, and rollback operations.
"""

import ast
import json
import shutil
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime

from app.core.logging_config import get_logger
from sqlalchemy.ext.asyncio import AsyncSession

logger = get_logger(__name__)


class CodeEditorAgent:
    """
    Tier 2 Specialist Agent for code editing operations.
    
    Capabilities:
    - code_editing: Apply code changes with validation
    - syntax_validation: Validate Python syntax
    - rollback: Rollback changes to previous state
    - formatting: Format code using standard tools
    - git_integration: Integrate with Git operations
    """
    
    def __init__(self):
        """Initialize Code Editor Agent."""
        self.agent_id = "code-editor"
        self.tier = 2
        self.capabilities = [
            "code_editing",
            "syntax_validation",
            "rollback",
            "formatting",
            "git_integration"
        ]
        logger.info("✅ Code Editor Agent initialized")
    
    def get_capabilities(self) -> Dict[str, Any]:
        """Get agent capabilities."""
        return {
            "agent_id": self.agent_id,
            "tier": self.tier,
            "capabilities": self.capabilities,
            "description": "Tier 2 Specialist Agent for code editing operations"
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """Check agent health."""
        return {
            "agent_id": self.agent_id,
            "status": "healthy",
            "capabilities_available": len(self.capabilities),
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def edit_code(
        self,
        db: AsyncSession,
        file_path: str,
        changes: List[Dict[str, Any]],
        validate: bool = True,
        create_backup: bool = True,
        branch_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Edit code with validation and rollback support.
        
        Args:
            db: Database session
            file_path: Path to file to edit
            changes: List of changes to apply
            validate: Whether to validate syntax after changes
            create_backup: Whether to create backup before changes
            branch_id: Optional DRYAD branch ID for context storage
            
        Returns:
            Dict with success status and details
        """
        logger.info(f"📝 Editing code: {file_path}")
        
        backup_path = None
        try:
            # Create backup if requested
            if create_backup:
                backup_path = await self._create_backup(file_path)
                logger.info(f"💾 Created backup: {backup_path}")
            
            # Apply changes
            for change in changes:
                success = await self._apply_change(file_path, change)
                if not success:
                    # Rollback on failure
                    if backup_path:
                        await self._rollback(file_path, backup_path)
                    return {
                        "success": False,
                        "error": f"Failed to apply change: {change.get('description', 'Unknown')}"
                    }
            
            # Validate syntax if requested
            if validate:
                validation_result = await self.validate_syntax(file_path)
                if not validation_result["valid"]:
                    # Rollback on validation failure
                    if backup_path:
                        await self._rollback(file_path, backup_path)
                    return {
                        "success": False,
                        "error": f"Syntax validation failed: {validation_result.get('error', 'Unknown')}"
                    }
            
            # Store in DRYAD if branch_id provided
            if branch_id:
                await self._store_in_dryad(db, file_path, changes, branch_id)
            
            # Clean up backup on success
            if backup_path:
                Path(backup_path).unlink(missing_ok=True)
            
            logger.info(f"✅ Code editing complete: {file_path}")
            return {
                "success": True,
                "file_path": file_path,
                "changes_applied": len(changes),
                "validated": validate
            }
        
        except Exception as e:
            logger.error(f"❌ Code editing failed: {e}", exc_info=True)
            # Rollback on exception
            if backup_path:
                await self._rollback(file_path, backup_path)
            return {
                "success": False,
                "error": str(e)
            }
    
    async def validate_syntax(self, file_path: str) -> Dict[str, Any]:
        """
        Validate Python syntax.
        
        Args:
            file_path: Path to file to validate
            
        Returns:
            Dict with validation result
        """
        try:
            file_path_obj = Path(file_path)
            
            # Only validate Python files
            if not file_path_obj.suffix == '.py':
                return {
                    "valid": True,
                    "message": "Non-Python file, skipping syntax validation"
                }
            
            # Read file content
            with open(file_path_obj, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Parse with AST
            ast.parse(content)
            
            logger.info(f"✅ Syntax validation passed: {file_path}")
            return {
                "valid": True,
                "file_path": file_path
            }
        
        except SyntaxError as e:
            logger.error(f"❌ Syntax error in {file_path}: {e}")
            return {
                "valid": False,
                "error": str(e),
                "line": e.lineno,
                "offset": e.offset
            }
        
        except Exception as e:
            logger.error(f"❌ Validation error: {e}", exc_info=True)
            return {
                "valid": False,
                "error": str(e)
            }
    
    async def _create_backup(self, file_path: str) -> str:
        """Create backup of file."""
        try:
            file_path_obj = Path(file_path)
            if not file_path_obj.exists():
                raise FileNotFoundError(f"File not found: {file_path}")
            
            # Create backup with timestamp
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            backup_path = f"{file_path}.backup_{timestamp}"
            
            shutil.copy2(file_path_obj, backup_path)
            return backup_path
        
        except Exception as e:
            logger.error(f"❌ Backup creation failed: {e}", exc_info=True)
            raise
    
    async def _rollback(self, file_path: str, backup_path: str) -> bool:
        """Rollback changes by restoring from backup."""
        try:
            backup_path_obj = Path(backup_path)
            if not backup_path_obj.exists():
                logger.error(f"Backup not found: {backup_path}")
                return False
            
            shutil.copy2(backup_path_obj, file_path)
            logger.info(f"🔄 Rolled back {file_path} from backup")
            
            # Clean up backup
            backup_path_obj.unlink()
            
            return True
        
        except Exception as e:
            logger.error(f"❌ Rollback failed: {e}", exc_info=True)
            return False
    
    async def _apply_change(self, file_path: str, change: Dict[str, Any]) -> bool:
        """Apply a single change to a file."""
        try:
            file_path_obj = Path(file_path)
            
            # Check file exists
            if not file_path_obj.exists():
                logger.error(f"File not found: {file_path}")
                return False
            
            # Read current content
            with open(file_path_obj, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Get change details
            old_code = change.get("old_code", "")
            new_code = change.get("new_code", "")
            
            # Apply str_replace logic
            if old_code and old_code in content:
                new_content = content.replace(old_code, new_code, 1)
                
                # Write back
                with open(file_path_obj, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                
                logger.info(f"✅ Applied change to {file_path}")
                return True
            else:
                logger.error(f"Old code not found in {file_path}")
                return False
        
        except Exception as e:
            logger.error(f"❌ Change application failed: {e}", exc_info=True)
            return False
    
    async def _store_in_dryad(
        self,
        db: AsyncSession,
        file_path: str,
        changes: List[Dict[str, Any]],
        branch_id: str
    ) -> Optional[str]:
        """Store code editing context in DRYAD vessel."""
        try:
            # Lazy import to avoid circular dependencies
            from app.dryad.services.vessel_service import VesselService
            from app.dryad.schemas.vessel_schemas import VesselCreate
            
            vessel_service = VesselService()
            
            # Create context data
            context_data = {
                "agent_id": self.agent_id,
                "file_path": file_path,
                "changes": changes,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Create vessel
            vessel_create = VesselCreate(
                branch_id=branch_id,
                initial_context=json.dumps(context_data)
            )
            
            vessel = await vessel_service.create_vessel(db, vessel_create)
            logger.info(f"✅ Stored code editing in DRYAD vessel: {vessel.id}")
            
            return vessel.id
        
        except Exception as e:
            logger.error(f"❌ DRYAD storage failed: {e}", exc_info=True)
            return None

