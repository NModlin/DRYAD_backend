# Task 3-05: Protected Clearing (Hardened Sandbox) Implementation

**Phase:** 3 - Advanced Collaboration & Governance  
**Week:** 14  
**Estimated Hours:** 20 hours  
**Priority:** CRITICAL  
**Dependencies:** Task 3-04 (GAD Workflow)

---

## 🎯 OBJECTIVE

Implement the Protected Clearing - a hardened, isolated sandbox environment using Docker and gVisor for secure execution of agent-generated code. This is the core security component of the GAD Execute phase.

---

## 📋 REQUIREMENTS

### Functional Requirements
- Create isolated Docker containers for code execution
- Implement gVisor for enhanced kernel-level isolation
- Manage Git branch creation for changes
- Execute validation gauntlet (tests, linting, security scans)
- Implement resource limiting (CPU, memory, network)
- Support stateful execution sessions
- Automatic cleanup of expired sandboxes

### Technical Requirements
- Docker SDK for Python integration
- gVisor runtime configuration
- Async/await patterns for container management
- Network isolation and egress controls
- File system isolation
- Comprehensive audit logging

### Performance Requirements
- Container creation: <5 seconds
- Code execution: Variable (based on task)
- Container cleanup: <2 seconds
- Resource overhead: <10% of host

---

## 🔧 IMPLEMENTATION STEPS

### Step 1: Create Protected Clearing Service (16 hours)

**File:** `app/services/protected_clearing.py`

```python
"""
Protected Clearing - Hardened Sandbox for Secure Code Execution
Provides isolated Docker containers with gVisor for agent code execution.
"""

from __future__ import annotations

import asyncio
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any
from uuid import UUID, uuid4

import docker
from docker.models.containers import Container
from pydantic import BaseModel, Field
from structlog import get_logger

logger = get_logger(__name__)


class SandboxConfig(BaseModel):
    """Configuration for sandbox environment."""
    
    sandbox_id: UUID = Field(default_factory=uuid4)
    runtime: str = "runsc"  # gVisor runtime
    cpu_limit: float = Field(default=1.0, ge=0.1, le=4.0)  # CPU cores
    memory_limit: str = "512m"  # Memory limit
    network_mode: str = "none"  # Isolated network
    timeout_seconds: int = Field(default=300, ge=10, le=3600)
    auto_cleanup: bool = True
    working_dir: Path = Field(default_factory=lambda: Path("/workspace"))


class ExecutionResult(BaseModel):
    """Result of code execution in sandbox."""
    
    sandbox_id: UUID
    success: bool
    exit_code: int
    stdout: str
    stderr: str
    execution_time_seconds: float
    validation_results: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ProtectedClearingService:
    """
    Protected Clearing Service
    
    Manages isolated sandbox environments for secure code execution
    using Docker with gVisor runtime.
    """
    
    def __init__(self, base_image: str = "python:3.11-slim") -> None:
        self.docker_client = docker.from_env()
        self.base_image = base_image
        self.logger = logger.bind(service="protected_clearing")
        
        # Active sandboxes
        self._active_sandboxes: dict[UUID, Container] = {}
        
        # Ensure gVisor runtime is available
        self._verify_gvisor_runtime()
    
    def _verify_gvisor_runtime(self) -> None:
        """Verify gVisor (runsc) runtime is available."""
        try:
            info = self.docker_client.info()
            runtimes = info.get('Runtimes', {})
            
            if 'runsc' not in runtimes:
                self.logger.warning(
                    "gvisor_not_available",
                    message="gVisor runtime not found, falling back to runc",
                )
        except Exception as e:
            self.logger.error("runtime_verification_failed", error=str(e))
    
    async def create_sandbox(
        self,
        config: SandboxConfig | None = None,
    ) -> UUID:
        """
        Create new isolated sandbox environment.
        
        Args:
            config: Optional sandbox configuration
            
        Returns:
            Sandbox ID
        """
        config = config or SandboxConfig()
        
        self.logger.info("creating_sandbox", sandbox_id=str(config.sandbox_id))
        
        try:
            # Create container with gVisor runtime
            container = await asyncio.to_thread(
                self.docker_client.containers.create,
                image=self.base_image,
                command="sleep infinity",  # Keep container running
                runtime=config.runtime,
                cpu_period=100000,
                cpu_quota=int(config.cpu_limit * 100000),
                mem_limit=config.memory_limit,
                network_mode=config.network_mode,
                working_dir=str(config.working_dir),
                detach=True,
                remove=config.auto_cleanup,
                labels={
                    "sandbox_id": str(config.sandbox_id),
                    "created_at": datetime.utcnow().isoformat(),
                    "managed_by": "protected_clearing",
                },
                security_opt=["no-new-privileges:true"],
                cap_drop=["ALL"],  # Drop all capabilities
                read_only=True,  # Read-only root filesystem
                tmpfs={"/tmp": "rw,noexec,nosuid,size=100m"},
            )
            
            # Start container
            await asyncio.to_thread(container.start)
            
            self._active_sandboxes[config.sandbox_id] = container
            
            self.logger.info(
                "sandbox_created",
                sandbox_id=str(config.sandbox_id),
                container_id=container.short_id,
            )
            
            return config.sandbox_id
            
        except Exception as e:
            self.logger.error(
                "sandbox_creation_failed",
                sandbox_id=str(config.sandbox_id),
                error=str(e),
            )
            raise
    
    async def execute_in_sandbox(
        self,
        sandbox_id: UUID,
        command: str | list[str],
        timeout: int = 300,
    ) -> ExecutionResult:
        """
        Execute command in sandbox environment.
        
        Args:
            sandbox_id: Sandbox identifier
            command: Command to execute
            timeout: Execution timeout in seconds
            
        Returns:
            Execution result with stdout/stderr
        """
        container = self._active_sandboxes.get(sandbox_id)
        if not container:
            raise ValueError(f"Sandbox {sandbox_id} not found")
        
        self.logger.info(
            "executing_command",
            sandbox_id=str(sandbox_id),
            command=str(command)[:100],
        )
        
        start_time = datetime.utcnow()
        
        try:
            # Execute command
            exec_result = await asyncio.wait_for(
                asyncio.to_thread(
                    container.exec_run,
                    cmd=command,
                    demux=True,  # Separate stdout/stderr
                ),
                timeout=timeout,
            )
            
            exit_code = exec_result.exit_code
            stdout_bytes, stderr_bytes = exec_result.output
            
            stdout = stdout_bytes.decode('utf-8') if stdout_bytes else ""
            stderr = stderr_bytes.decode('utf-8') if stderr_bytes else ""
            
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            
            result = ExecutionResult(
                sandbox_id=sandbox_id,
                success=exit_code == 0,
                exit_code=exit_code,
                stdout=stdout,
                stderr=stderr,
                execution_time_seconds=execution_time,
            )
            
            self.logger.info(
                "command_executed",
                sandbox_id=str(sandbox_id),
                exit_code=exit_code,
                execution_time=execution_time,
            )
            
            return result
            
        except asyncio.TimeoutError:
            self.logger.error(
                "execution_timeout",
                sandbox_id=str(sandbox_id),
                timeout=timeout,
            )
            
            return ExecutionResult(
                sandbox_id=sandbox_id,
                success=False,
                exit_code=-1,
                stdout="",
                stderr=f"Execution timeout after {timeout} seconds",
                execution_time_seconds=timeout,
            )
        
        except Exception as e:
            self.logger.error(
                "execution_failed",
                sandbox_id=str(sandbox_id),
                error=str(e),
            )
            raise
    
    async def execute_plan(
        self,
        plan: Any,  # ExecutionPlanModel
        config: SandboxConfig | None = None,
    ) -> dict[str, Any]:
        """
        Execute complete plan in sandbox with validation gauntlet.
        
        Args:
            plan: Execution plan to run
            config: Optional sandbox configuration
            
        Returns:
            Execution results with validation
        """
        sandbox_id = await self.create_sandbox(config)
        
        try:
            results: dict[str, Any] = {
                "sandbox_id": str(sandbox_id),
                "success": True,
                "steps": [],
                "validation": {},
            }
            
            # Execute each step
            for step in plan.steps:
                step_result = await self._execute_step(sandbox_id, step)
                results["steps"].append(step_result)
                
                if not step_result.get("success"):
                    results["success"] = False
                    break
            
            # Run validation gauntlet if all steps succeeded
            if results["success"]:
                validation = await self._run_validation_gauntlet(sandbox_id)
                results["validation"] = validation
                results["success"] = validation.get("all_passed", False)
            
            return results
            
        finally:
            # Cleanup sandbox
            await self.destroy_sandbox(sandbox_id)
    
    async def _execute_step(
        self,
        sandbox_id: UUID,
        step: Any,  # PlanStep
    ) -> dict[str, Any]:
        """Execute individual plan step."""
        # Implementation would execute the specific step
        # This is a simplified version
        return {
            "step_number": step.step_number,
            "success": True,
            "output": "Step executed successfully",
        }
    
    async def _run_validation_gauntlet(
        self,
        sandbox_id: UUID,
    ) -> dict[str, Any]:
        """
        Run comprehensive validation gauntlet.
        
        Includes:
        - Static analysis (ruff, bandit)
        - Type checking (mypy)
        - Unit tests (pytest)
        - Code coverage analysis
        - Security scanning
        """
        validation_results: dict[str, Any] = {
            "all_passed": True,
            "checks": {},
        }
        
        # Run ruff (linting)
        ruff_result = await self.execute_in_sandbox(
            sandbox_id,
            ["ruff", "check", "."],
            timeout=60,
        )
        validation_results["checks"]["ruff"] = {
            "passed": ruff_result.success,
            "output": ruff_result.stdout,
        }
        if not ruff_result.success:
            validation_results["all_passed"] = False
        
        # Run bandit (security)
        bandit_result = await self.execute_in_sandbox(
            sandbox_id,
            ["bandit", "-r", ".", "-f", "json"],
            timeout=60,
        )
        validation_results["checks"]["bandit"] = {
            "passed": bandit_result.success,
            "output": bandit_result.stdout,
        }
        if not bandit_result.success:
            validation_results["all_passed"] = False
        
        # Run mypy (type checking)
        mypy_result = await self.execute_in_sandbox(
            sandbox_id,
            ["mypy", "."],
            timeout=120,
        )
        validation_results["checks"]["mypy"] = {
            "passed": mypy_result.success,
            "output": mypy_result.stdout,
        }
        if not mypy_result.success:
            validation_results["all_passed"] = False
        
        # Run pytest
        pytest_result = await self.execute_in_sandbox(
            sandbox_id,
            ["pytest", "-v", "--cov=.", "--cov-report=json"],
            timeout=300,
        )
        validation_results["checks"]["pytest"] = {
            "passed": pytest_result.success,
            "output": pytest_result.stdout,
        }
        if not pytest_result.success:
            validation_results["all_passed"] = False
        
        return validation_results
    
    async def destroy_sandbox(self, sandbox_id: UUID) -> None:
        """Destroy sandbox and cleanup resources."""
        container = self._active_sandboxes.get(sandbox_id)
        if not container:
            return
        
        self.logger.info("destroying_sandbox", sandbox_id=str(sandbox_id))
        
        try:
            await asyncio.to_thread(container.stop, timeout=10)
            await asyncio.to_thread(container.remove, force=True)
            
            del self._active_sandboxes[sandbox_id]
            
            self.logger.info("sandbox_destroyed", sandbox_id=str(sandbox_id))
            
        except Exception as e:
            self.logger.error(
                "sandbox_destruction_failed",
                sandbox_id=str(sandbox_id),
                error=str(e),
            )
    
    async def cleanup_expired_sandboxes(self, max_age_hours: int = 24) -> int:
        """Cleanup sandboxes older than max_age_hours."""
        cleaned = 0
        cutoff = datetime.utcnow() - timedelta(hours=max_age_hours)
        
        for sandbox_id, container in list(self._active_sandboxes.items()):
            try:
                labels = container.labels
                created_at_str = labels.get("created_at")
                
                if created_at_str:
                    created_at = datetime.fromisoformat(created_at_str)
                    
                    if created_at < cutoff:
                        await self.destroy_sandbox(sandbox_id)
                        cleaned += 1
                        
            except Exception as e:
                self.logger.error(
                    "cleanup_failed",
                    sandbox_id=str(sandbox_id),
                    error=str(e),
                )
        
        self.logger.info("cleanup_completed", sandboxes_cleaned=cleaned)
        return cleaned
```

---

## ✅ DEFINITION OF DONE

- [ ] Protected Clearing service implemented
- [ ] Docker integration working
- [ ] gVisor runtime configured
- [ ] Resource limiting functional
- [ ] Validation gauntlet operational
- [ ] Sandbox cleanup working
- [ ] All tests passing (>85% coverage)
- [ ] Security audit complete
- [ ] Documentation complete

---

## 📊 SUCCESS METRICS

- Sandbox creation time: <5 seconds
- Execution isolation: 100%
- Resource limit enforcement: 100%
- Cleanup success rate: >99%
- Security scan pass rate: >95%
- Test coverage: >85%

---

**Estimated Completion:** 20 hours  
**Assigned To:** DevOps Engineer + Backend Developer  
**Status:** NOT STARTED

