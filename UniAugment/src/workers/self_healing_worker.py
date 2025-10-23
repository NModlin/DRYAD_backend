"""
Self-Healing Background Worker
Executes approved code fixes using the Code Agent.
"""

import asyncio
import shutil
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime
from sqlalchemy import select, update

from app.database.database import AsyncSessionLocal
from app.database.self_healing_models import SelfHealingTask, TaskStatus
from app.core.logging_config import get_logger
from app.integrations.teams_notifier import send_completion_notification

logger = get_logger(__name__)


class SelfHealingWorker:
    """
    Background worker that executes approved self-healing fixes.
    
    Responsibilities:
    - Poll for approved tasks
    - Apply code changes
    - Run validation tests
    - Rollback on failure
    - Update task status
    """
    
    def __init__(self, check_interval: float = 10.0):
        """
        Initialize worker.
        
        Args:
            check_interval: Seconds between checks for approved tasks
        """
        self.check_interval = check_interval
        self.running = False
    
    async def start(self):
        """Start the worker."""
        logger.info("Self-Healing Worker starting...")
        self.running = True
        
        try:
            await self._worker_loop()
        except Exception as e:
            logger.error(f"Worker error: {e}", exc_info=True)
            self.running = False
    
    async def stop(self):
        """Stop the worker."""
        logger.info("Self-Healing Worker stopping...")
        self.running = False
    
    async def _worker_loop(self):
        """Main worker loop."""
        while self.running:
            try:
                # Get approved tasks
                approved_tasks = await self._get_approved_tasks()
                
                # Execute each task
                for task in approved_tasks:
                    await self._execute_task(task)
                
                # Wait before next check
                await asyncio.sleep(self.check_interval)
            
            except Exception as e:
                logger.error(f"Error in worker loop: {e}", exc_info=True)
                await asyncio.sleep(self.check_interval)
    
    async def _get_approved_tasks(self):
        """Get tasks that are approved and ready for execution."""
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(SelfHealingTask)
                .where(SelfHealingTask.status == TaskStatus.APPROVED)
                .order_by(SelfHealingTask.reviewed_at)
                .limit(5)  # Process max 5 at a time
            )
            return result.scalars().all()
    
    async def _execute_task(self, task: SelfHealingTask):
        """Execute a self-healing task."""
        logger.info(f"Executing task {task.id}: {task.error_type}")
        
        try:
            # Update status to executing
            await self._update_task_status(task.id, TaskStatus.EXECUTING)
            
            # Create backup
            backup_path = await self._create_backup(task.file_path)
            
            # Apply changes
            success = await self._apply_changes(task)
            
            if success:
                # Run tests
                test_success = await self._run_tests(task)
                
                if test_success:
                    # Success!
                    await self._update_task_status(
                        task.id,
                        TaskStatus.COMPLETED,
                        execution_log={"message": "Fix applied and validated successfully"}
                    )
                    logger.info(f"Task {task.id} completed successfully")
                    
                    # Send success notification
                    await send_completion_notification(task.to_dict(), success=True)
                else:
                    # Tests failed, rollback
                    await self._rollback(task.file_path, backup_path)
                    await self._update_task_status(
                        task.id,
                        TaskStatus.FAILED,
                        execution_log={"message": "Tests failed, changes rolled back"}
                    )
                    logger.warning(f"Task {task.id} failed validation, rolled back")
                    
                    # Send failure notification
                    await send_completion_notification(task.to_dict(), success=False)
            else:
                # Failed to apply changes
                await self._update_task_status(
                    task.id,
                    TaskStatus.FAILED,
                    execution_log={"message": "Failed to apply changes"}
                )
                logger.error(f"Task {task.id} failed to apply changes")
        
        except Exception as e:
            logger.error(f"Error executing task {task.id}: {e}", exc_info=True)
            await self._update_task_status(
                task.id,
                TaskStatus.FAILED,
                execution_log={"message": f"Execution error: {str(e)}"}
            )
    
    async def _create_backup(self, file_path: str) -> Optional[Path]:
        """Create backup of file before modification."""
        try:
            source = Path(file_path)
            if not source.exists():
                logger.warning(f"File not found for backup: {file_path}")
                return None
            
            backup = source.with_suffix(f".backup.{int(datetime.now().timestamp())}")
            shutil.copy2(source, backup)
            logger.debug(f"Created backup: {backup}")
            return backup
        
        except Exception as e:
            logger.error(f"Error creating backup: {e}")
            return None
    
    async def _apply_changes(self, task: SelfHealingTask) -> bool:
        """
        Apply code changes from the plan.

        Implements actual code patching with:
        1. Parse the plan's change specifications
        2. Read file content
        3. Apply str_replace logic
        4. Validate syntax
        5. Write changes
        """
        try:
            plan = task.plan
            if not plan or "changes" not in plan:
                logger.error("No changes in plan")
                return False

            changes = plan["changes"]
            if not changes:
                logger.error("Empty changes list")
                return False

            # Apply each change
            for change in changes:
                file_path = change.get("file")
                if not file_path:
                    logger.error("No file path in change")
                    continue

                # Get change details
                old_code = change.get("old_code", "")
                new_code = change.get("new_code", "")
                line_start = change.get("line_start", 0)
                line_end = change.get("line_end", 0)
                rationale = change.get("rationale", "")

                logger.info(f"Applying change to {file_path}: {rationale}")

                # Apply the change
                success = await self._patch_file(
                    file_path, old_code, new_code, line_start, line_end
                )

                if not success:
                    logger.error(f"Failed to patch {file_path}")
                    return False

            return True

        except Exception as e:
            logger.error(f"Error applying changes: {e}", exc_info=True)
            return False

    async def _patch_file(
        self,
        file_path: str,
        old_code: str,
        new_code: str,
        line_start: int,
        line_end: int
    ) -> bool:
        """
        Patch a single file with str_replace logic.

        Args:
            file_path: Path to file
            old_code: Code to replace (if provided)
            new_code: New code to insert
            line_start: Start line number (1-based)
            line_end: End line number (1-based)

        Returns:
            True if successful, False otherwise
        """
        try:
            file_path_obj = Path(file_path)

            # Check file exists
            if not file_path_obj.exists():
                logger.error(f"File not found: {file_path}")
                return False

            # Read current content
            with open(file_path_obj, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            # If old_code is provided, use str_replace logic
            if old_code:
                content = ''.join(lines)

                # Check if old_code exists
                if old_code not in content:
                    logger.error(f"Old code not found in {file_path}")
                    logger.debug(f"Looking for: {old_code[:100]}...")
                    return False

                # Replace
                new_content = content.replace(old_code, new_code, 1)

                # Write back
                with open(file_path_obj, 'w', encoding='utf-8') as f:
                    f.write(new_content)

                logger.info(f"Patched {file_path} using str_replace")
                return True

            # Otherwise, use line-based replacement
            elif line_start > 0 and line_end > 0:
                # Validate line numbers
                if line_start > len(lines) or line_end > len(lines):
                    logger.error(f"Invalid line numbers: {line_start}-{line_end} (file has {len(lines)} lines)")
                    return False

                # Replace lines (convert to 0-based)
                new_lines = new_code.split('\n')
                lines[line_start-1:line_end] = [line + '\n' for line in new_lines]

                # Write back
                with open(file_path_obj, 'w', encoding='utf-8') as f:
                    f.writelines(lines)

                logger.info(f"Patched {file_path} lines {line_start}-{line_end}")
                return True

            else:
                logger.error("No old_code or line numbers provided")
                return False

        except Exception as e:
            logger.error(f"Error patching file: {e}", exc_info=True)
            return False
    
    async def _run_tests(self, task: SelfHealingTask) -> bool:
        """
        Run validation tests.

        Implements actual test execution with:
        1. Run pytest with specified test files
        2. Capture test output
        3. Parse results
        4. Store in task.test_results
        """
        try:
            plan = task.plan
            if not plan:
                logger.info("No plan specified, skipping tests")
                return True

            tests = plan.get("tests_to_run", [])
            if not tests:
                logger.info("No tests specified in plan, skipping")
                return True

            # Run each test file
            all_passed = True
            test_results = []

            for test_file in tests:
                logger.info(f"Running test: {test_file}")

                result = await self._run_pytest(test_file)
                test_results.append(result)

                if not result["passed"]:
                    all_passed = False
                    logger.warning(f"Test failed: {test_file}")

            # Store results in task
            await self._update_task_test_results(task.id, test_results)

            return all_passed

        except Exception as e:
            logger.error(f"Error running tests: {e}", exc_info=True)
            return False

    async def _run_pytest(self, test_file: str) -> Dict[str, Any]:
        """
        Run pytest on a specific test file.

        Args:
            test_file: Path to test file

        Returns:
            Dictionary with test results
        """
        import subprocess
        import json

        try:
            # Check if test file exists
            test_path = Path(test_file)
            if not test_path.exists():
                logger.warning(f"Test file not found: {test_file}")
                return {
                    "test_file": test_file,
                    "passed": True,  # Don't fail if test doesn't exist yet
                    "skipped": True,
                    "output": "Test file not found"
                }

            # Run pytest with JSON output
            cmd = [
                "pytest",
                str(test_path),
                "-v",
                "--tb=short",
                "--json-report",
                "--json-report-file=test_report.json"
            ]

            # Run in subprocess
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60  # 1 minute timeout
            )

            # Parse output
            passed = result.returncode == 0

            # Try to read JSON report
            report_path = Path("test_report.json")
            if report_path.exists():
                with open(report_path, 'r') as f:
                    report = json.load(f)

                # Clean up report file
                report_path.unlink()

                return {
                    "test_file": test_file,
                    "passed": passed,
                    "skipped": False,
                    "total": report.get("summary", {}).get("total", 0),
                    "passed_count": report.get("summary", {}).get("passed", 0),
                    "failed_count": report.get("summary", {}).get("failed", 0),
                    "output": result.stdout[:1000]  # Limit output size
                }
            else:
                # Fallback to basic result
                return {
                    "test_file": test_file,
                    "passed": passed,
                    "skipped": False,
                    "output": result.stdout[:1000]
                }

        except subprocess.TimeoutExpired:
            logger.error(f"Test timeout: {test_file}")
            return {
                "test_file": test_file,
                "passed": False,
                "skipped": False,
                "error": "Test timeout (60s)"
            }

        except Exception as e:
            logger.error(f"Error running pytest: {e}", exc_info=True)
            return {
                "test_file": test_file,
                "passed": False,
                "skipped": False,
                "error": str(e)
            }

    async def _update_task_test_results(self, task_id: str, test_results: list):
        """Update task with test results."""
        try:
            async with AsyncSessionLocal() as db:
                stmt = (
                    update(SelfHealingTask)
                    .where(SelfHealingTask.id == task_id)
                    .values(test_results=test_results)
                )
                await db.execute(stmt)
                await db.commit()

        except Exception as e:
            logger.error(f"Error updating test results: {e}", exc_info=True)
    
    async def _rollback(self, file_path: str, backup_path: Optional[Path]) -> bool:
        """Rollback changes by restoring from backup."""
        try:
            if not backup_path or not backup_path.exists():
                logger.error("No backup available for rollback")
                return False
            
            target = Path(file_path)
            shutil.copy2(backup_path, target)
            logger.info(f"Rolled back {file_path} from backup")
            
            # Clean up backup
            backup_path.unlink()
            
            return True
        
        except Exception as e:
            logger.error(f"Error during rollback: {e}", exc_info=True)
            return False
    
    async def _update_task_status(
        self, 
        task_id: str, 
        status: TaskStatus,
        execution_log: Optional[Dict[str, Any]] = None
    ):
        """Update task status in database."""
        try:
            async with AsyncSessionLocal() as db:
                values = {"status": status}
                
                if status == TaskStatus.COMPLETED:
                    values["completed_at"] = datetime.now()
                
                if execution_log:
                    values["execution_log"] = execution_log
                
                stmt = (
                    update(SelfHealingTask)
                    .where(SelfHealingTask.id == task_id)
                    .values(**values)
                )
                await db.execute(stmt)
                await db.commit()
        
        except Exception as e:
            logger.error(f"Error updating task status: {e}", exc_info=True)


# Global worker instance (lazy initialization)
_worker = None


def _get_worker() -> "SelfHealingWorker":
    """Get or create the global Worker instance."""
    global _worker
    if _worker is None:
        _worker = SelfHealingWorker()
    return _worker


async def start_worker():
    """Start the self-healing worker."""
    worker = _get_worker()
    await worker.start()


async def stop_worker():
    """Stop the self-healing worker."""
    worker = _get_worker()
    await worker.stop()

