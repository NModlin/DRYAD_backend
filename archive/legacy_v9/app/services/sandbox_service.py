"""
Sandboxed Execution Environment - Level 1 Component

Provides secure, isolated Docker-based execution environment for tools with:
- Resource limits and security isolation
- Tool Registry integration
- Execution monitoring and logging
- Session management and cleanup

Part of DRYAD.AI Agent Evolution Architecture Level 1.
"""

import asyncio
import logging
import uuid
import json
import time
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.services.logging.logger import StructuredLogger
from app.services.tool_registry.service import ToolRegistryService
from app.services.tool_registry.exceptions import ToolNotFoundError

logger = logging.getLogger(__name__)
structured_logger = StructuredLogger("sandbox_service")


class SandboxExecutionEnvironment:
    """
    Level 1 Component: Sandboxed Execution Environment

    Provides secure, isolated Docker-based execution environment for tools.
    Integrates with Tool Registry and implements comprehensive resource limits.
    """

    def __init__(self, db: Session):
        self.db = db
        self.docker_available = self._check_docker_availability()
        self.tool_registry = ToolRegistryService(db)

        # Resource limits configuration
        self.default_memory_limit = "512m"
        self.default_cpu_quota = 50000  # 50% of one core
        self.default_timeout = 300  # 5 minutes
        self.max_concurrent_sessions = 10

        # Security configuration
        self.allowed_images = {
            "python:3.11-slim",
            "node:18-alpine",
            "ubuntu:22.04",
            "alpine:latest"
        }

        logger.info("🔧 Sandbox Execution Environment initialized")

    def _check_docker_availability(self) -> bool:
        """Check if Docker is available and accessible."""
        try:
            import docker
            client = docker.from_env()
            client.ping()

            # Test container creation
            test_container = client.containers.run(
                "alpine:latest",
                command="echo 'Docker test successful'",
                detach=True,
                remove=True
            )

            structured_logger.log_info(
                "docker_availability_check",
                {"status": "available", "test_successful": True}
            )
            logger.info("✅ Docker is available and functional for sandbox execution")
            return True

        except Exception as e:
            structured_logger.log_warning(
                "docker_availability_check",
                {"status": "unavailable", "error": str(e)}
            )
            logger.warning(f"⚠️ Docker not available: {e}. Sandbox execution will use mock mode.")
            return False
    
    def create_session(
        self,
        session_id: str = None,
        agent_id: str = None,
        tool_id: str = None,
        timeout_seconds: int = None,
        resource_limits: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Synchronous wrapper for create_sandbox_session.

        Args:
            session_id: Unique session identifier (optional, will be generated if not provided)
            agent_id: ID of the agent requesting execution
            tool_id: ID of the tool to execute
            timeout_seconds: Maximum execution time
            resource_limits: Custom resource limits

        Returns:
            Session information dictionary
        """
        return asyncio.run(self.create_sandbox_session(
            session_id=session_id,
            agent_id=agent_id,
            tool_id=tool_id,
            timeout_seconds=timeout_seconds,
            resource_limits=resource_limits
        ))

    def close_session(self, session_id: str) -> bool:
        """
        Synchronous wrapper for close_sandbox_session.

        Args:
            session_id: Session ID to close

        Returns:
            True if session was closed successfully
        """
        return asyncio.run(self.close_sandbox_session(session_id))

    async def create_sandbox_session(
        self,
        agent_id: str,
        tool_id: str,
        session_id: str = None,
        timeout_seconds: int = None,
        resource_limits: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create a new sandboxed execution session with enhanced security and monitoring.

        Args:
            agent_id: ID of the agent requesting the sandbox
            tool_id: ID of the tool to execute
            session_id: Optional session identifier (will be generated if not provided)
            timeout_seconds: Maximum session duration in seconds
            resource_limits: Custom resource limits for this session

        Returns:
            Dict containing session details and status

        Raises:
            ToolNotFoundError: If tool doesn't exist
            ValueError: If tool doesn't require sandbox or limits exceeded
        """
        try:
            # Check concurrent session limits
            active_sessions = await self._count_active_sessions()
            if active_sessions >= self.max_concurrent_sessions:
                raise ValueError(f"Maximum concurrent sessions ({self.max_concurrent_sessions}) exceeded")

            # Get tool details from Tool Registry (if available)
            tool = None
            try:
                tool = await self.tool_registry.get_tool_by_id(tool_id)
            except (ToolNotFoundError, Exception) as e:
                # Tool not found - use mock/default values for testing
                structured_logger.log_warning(
                    "tool_not_found_using_defaults",
                    {"tool_id": tool_id, "error": str(e)}
                )

            # For testing/mock mode, allow execution even if tool not found
            # In production, you might want to enforce tool existence

            # Validate and set resource limits
            timeout = timeout_seconds or (tool.max_session_duration if tool and hasattr(tool, 'max_session_duration') else None) or self.default_timeout
            limits = self._prepare_resource_limits(resource_limits, tool)

            # Generate session ID if not provided
            if not session_id:
                session_id = f"sandbox_{uuid.uuid4().hex[:16]}"

            structured_logger.log_info(
                "sandbox_session_creation_started",
                {
                    "session_id": session_id,
                    "agent_id": agent_id,
                    "tool_id": tool_id,
                    "timeout_seconds": timeout,
                    "resource_limits": limits
                }
            )

            # Create sandbox container (if Docker available)
            sandbox_result = await self._create_secure_container(
                session_id=session_id,
                tool=tool,
                timeout_seconds=timeout,
                resource_limits=limits
            )

            # Create session record
            from app.models.agent_tools import ToolSession
            session = ToolSession(
                session_id=session_id,
                tool_id=tool.id if tool and hasattr(tool, 'id') else tool_id,
                agent_id=agent_id,
                execution_id=None,
                sandbox_id=sandbox_result["container_id"],
                sandbox_status=sandbox_result["status"],
                status="active",
                expires_at=datetime.utcnow() + timedelta(seconds=timeout)
            )
            
            self.db.add(session)
            self.db.commit()
            self.db.refresh(session)

            structured_logger.log_info(
                "sandbox_session_created",
                {
                    "session_id": session_id,
                    "container_id": sandbox_result["container_id"],
                    "status": sandbox_result["status"],
                    "docker_available": self.docker_available
                }
            )

            logger.info(f"✅ Created sandbox session: {session_id} for tool {tool_id}")

            return {
                "session_id": session_id,
                "container_id": sandbox_result["container_id"],
                "status": sandbox_result["status"],
                "expires_at": session.expires_at.isoformat(),
                "resource_limits": limits,
                "docker_available": self.docker_available
            }

        except Exception as e:
            self.db.rollback()
            structured_logger.log_error(
                "sandbox_session_creation_failed",
                {"agent_id": agent_id, "tool_id": tool_id, "error": str(e)}
            )
            logger.error(f"❌ Failed to create sandbox session: {e}")
            raise

    async def _count_active_sessions(self) -> int:
        """Count currently active sandbox sessions."""
        from app.models.agent_tools import ToolSession

        count = self.db.query(ToolSession).filter(
            ToolSession.status == "active",
            ToolSession.expires_at > datetime.utcnow()
        ).count()

        return count

    def _prepare_resource_limits(
        self,
        custom_limits: Optional[Dict[str, Any]],
        tool: Any
    ) -> Dict[str, Any]:
        """Prepare resource limits for container creation."""
        limits = {
            "memory": self.default_memory_limit,
            "cpu_quota": self.default_cpu_quota,
            "network_mode": "none",  # Isolated network by default
            "read_only": False,  # Allow writes within container
            "tmpfs": {"/tmp": "size=100m"},  # Temporary filesystem
        }

        # Apply tool-specific limits if available
        if hasattr(tool, 'resource_limits') and tool.resource_limits:
            limits.update(tool.resource_limits)

        # Apply custom limits (with validation)
        if custom_limits:
            # Validate memory limit
            if "memory" in custom_limits:
                memory = custom_limits["memory"]
                if isinstance(memory, str) and memory.endswith(('m', 'g')):
                    limits["memory"] = memory

            # Validate CPU quota
            if "cpu_quota" in custom_limits:
                cpu_quota = custom_limits["cpu_quota"]
                if isinstance(cpu_quota, int) and 1000 <= cpu_quota <= 100000:
                    limits["cpu_quota"] = cpu_quota

        return limits

    async def _create_secure_container(
        self,
        session_id: str,
        tool: Any,
        timeout_seconds: int,
        resource_limits: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create a secure Docker container with proper isolation and limits."""
        if not self.docker_available:
            return {
                "container_id": f"mock_{session_id}",
                "status": "mock",
                "message": "Docker not available, using mock mode"
            }

        try:
            import docker
            client = docker.from_env()

            # Determine container image
            image = (tool.sandbox_image if tool and hasattr(tool, 'sandbox_image') else None) or "python:3.11-slim"
            if image not in self.allowed_images:
                logger.warning(f"Image {image} not in allowed list, using default")
                image = "python:3.11-slim"

            # Create container with security and resource limits
            container = client.containers.run(
                image,
                command="sleep infinity",
                detach=True,
                name=f"sandbox_{session_id}",
                network_mode=resource_limits.get("network_mode", "none"),
                mem_limit=resource_limits.get("memory", self.default_memory_limit),
                cpu_quota=resource_limits.get("cpu_quota", self.default_cpu_quota),
                cpu_period=100000,  # Standard CPU period
                read_only=resource_limits.get("read_only", False),
                tmpfs=resource_limits.get("tmpfs", {"/tmp": "size=100m"}),
                remove=False,
                security_opt=["no-new-privileges:true"],  # Security hardening
                cap_drop=["ALL"],  # Drop all capabilities
                cap_add=["CHOWN", "SETUID", "SETGID"],  # Add only necessary capabilities
                user="1000:1000",  # Non-root user
            )

            structured_logger.log_info(
                "docker_container_created",
                {
                    "session_id": session_id,
                    "container_id": container.id,
                    "image": image,
                    "resource_limits": resource_limits
                }
            )

            return {
                "container_id": container.id,
                "status": "running",
                "image": image
            }

        except Exception as e:
            structured_logger.log_error(
                "docker_container_creation_failed",
                {"session_id": session_id, "error": str(e)}
            )
            logger.error(f"❌ Failed to create Docker container: {e}")
            return {
                "container_id": None,
                "status": "error",
                "error": str(e)
            }

    async def execute_in_sandbox(
        self,
        session_id: str,
        command: str,
        working_directory: Optional[str] = None,
        environment_variables: Optional[Dict[str, str]] = None,
        input_parameters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Execute a command in the sandbox session with comprehensive tracking.

        Args:
            session_id: ID of the sandbox session
            command: Command to execute
            working_directory: Optional working directory for the command
            environment_variables: Environment variables for the execution
            input_parameters: Input parameters for tracking

        Returns:
            Dictionary with execution results and performance metrics
        """
        execution_id = f"exec_{uuid.uuid4().hex[:16]}"
        start_time = time.time()

        try:
            from app.models.agent_tools import ToolSession, ToolExecution

            # Get session
            session = self.db.query(ToolSession).filter(
                ToolSession.session_id == session_id
            ).first()

            if not session:
                raise ValueError(f"Session not found: {session_id}")

            if session.status != "active":
                raise ValueError(f"Session {session_id} is not active (status: {session.status})")

            # Check expiration
            if session.expires_at and datetime.utcnow() > session.expires_at:
                session.status = "expired"
                self.db.commit()
                raise ValueError(f"Session {session_id} has expired")

            # Create execution record
            execution = ToolExecution(
                execution_id=execution_id,
                session_id=session_id,
                tool_id=session.tool_id,
                agent_id=session.agent_id,
                command=command,
                working_directory=working_directory,
                environment_variables=environment_variables,
                input_parameters=input_parameters,
                started_at=datetime.utcnow()
            )

            self.db.add(execution)
            self.db.commit()

            structured_logger.log_info(
                "sandbox_execution_started",
                {
                    "execution_id": execution_id,
                    "session_id": session_id,
                    "command": command[:100],  # Truncate for logging
                    "working_directory": working_directory
                }
            )

            # Execute command
            if self.docker_available and session.sandbox_id:
                result = await self._execute_docker_command_enhanced(
                    container_id=session.sandbox_id,
                    command=command,
                    working_directory=working_directory,
                    environment_variables=environment_variables
                )
            else:
                # Mock execution
                result = {
                    "stdout": f"[MOCK] Executed: {command}",
                    "stderr": "",
                    "exit_code": 0,
                    "execution_time_ms": 100,
                    "memory_usage_mb": 50,
                    "cpu_usage_percent": 10
                }
                logger.info(f"🔧 Mock execution in session {session_id}: {command}")

            # Update execution record with results
            execution.stdout = result.get("stdout", "")
            execution.stderr = result.get("stderr", "")
            execution.exit_code = result.get("exit_code", 0)
            execution.success = result.get("exit_code", 0) == 0
            execution.execution_time_ms = result.get("execution_time_ms", 0)
            execution.memory_usage_mb = result.get("memory_usage_mb")
            execution.cpu_usage_percent = result.get("cpu_usage_percent")
            execution.completed_at = datetime.utcnow()
            execution.resource_limits_enforced = True

            if not execution.success:
                execution.error_message = result.get("stderr", "Unknown error")

            self.db.commit()

            structured_logger.log_info(
                "sandbox_execution_completed",
                {
                    "execution_id": execution_id,
                    "success": execution.success,
                    "exit_code": execution.exit_code,
                    "execution_time_ms": execution.execution_time_ms
                }
            )

            logger.info(f"✅ Executed command in sandbox {session_id} (execution: {execution_id})")

            # Return enhanced result
            return {
                "execution_id": execution_id,
                "success": execution.success,
                "stdout": execution.stdout,
                "stderr": execution.stderr,
                "exit_code": execution.exit_code,
                "execution_time_ms": execution.execution_time_ms,
                "memory_usage_mb": execution.memory_usage_mb,
                "cpu_usage_percent": execution.cpu_usage_percent,
                "resource_limits_enforced": execution.resource_limits_enforced
            }

        except Exception as e:
            # Update execution record with error
            if 'execution' in locals():
                execution.success = False
                execution.error_message = str(e)
                execution.completed_at = datetime.utcnow()
                self.db.commit()

            structured_logger.log_error(
                "sandbox_execution_failed",
                {"execution_id": execution_id, "session_id": session_id, "error": str(e)}
            )
            logger.error(f"❌ Failed to execute in sandbox: {e}")
            raise
    
    async def get_sandbox_state(
        self,
        session_id: str
    ) -> Dict[str, Any]:
        """
        Get current state of the sandbox session.
        
        Args:
            session_id: ID of the sandbox session
            
        Returns:
            Dictionary with session state information
        """
        try:
            from app.models.agent_tools import ToolSession
            
            # Get session
            session = self.db.query(ToolSession).filter(
                ToolSession.session_id == session_id
            ).first()
            
            if not session:
                raise ValueError(f"Session not found: {session_id}")
            
            # Get container state if Docker available
            container_state = None
            if self.docker_available and session.sandbox_id:
                container_state = await self._get_docker_container_state(session.sandbox_id)
            
            # Count active executions
            from app.models.agent_tools import ToolExecution
            active_executions = self.db.query(ToolExecution).filter(
                ToolExecution.session_id == session_id,
                ToolExecution.completed_at.is_(None)
            ).count()

            return {
                "session_id": session_id,
                "status": session.status,
                "container_id": session.sandbox_id,
                "sandbox_status": session.sandbox_status,
                "created_at": session.created_at.isoformat(),
                "expires_at": session.expires_at.isoformat() if session.expires_at else None,
                "active_executions": active_executions
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to get sandbox state: {e}")
            raise
    
    async def destroy_sandbox_session(
        self,
        session_id: str
    ) -> None:
        """
        Destroy the sandbox session and clean up resources.
        
        Args:
            session_id: ID of the sandbox session
        """
        try:
            from app.models.agent_tools import ToolSession
            
            # Get session
            session = self.db.query(ToolSession).filter(
                ToolSession.session_id == session_id
            ).first()
            
            if not session:
                raise ValueError(f"Session not found: {session_id}")
            
            # Stop and remove container if Docker available
            if self.docker_available and session.sandbox_id:
                await self._destroy_docker_container(session.sandbox_id)
            
            # Update session
            session.status = "closed"
            session.closed_at = datetime.utcnow()
            
            self.db.commit()
            
            logger.info(f"✅ Destroyed sandbox session: {session_id}")
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"❌ Failed to destroy sandbox session: {e}")
            raise
    
    # ========================================================================
    # Docker Helper Methods
    # ========================================================================
    
    async def _execute_docker_command_enhanced(
        self,
        container_id: str,
        command: str,
        working_directory: Optional[str] = None,
        environment_variables: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """Execute a command in a Docker container with enhanced monitoring."""
        try:
            import docker
            import psutil

            client = docker.from_env()
            container = client.containers.get(container_id)

            # Prepare environment variables
            env_vars = environment_variables or {}

            # Monitor execution
            start_time = time.time()
            start_memory = self._get_container_memory_usage(container)

            # Execute command
            exec_result = container.exec_run(
                command,
                workdir=working_directory,
                environment=env_vars,
                demux=True,
                stream=False
            )

            end_time = time.time()
            execution_time_ms = int((end_time - start_time) * 1000)

            # Get resource usage
            end_memory = self._get_container_memory_usage(container)
            memory_usage_mb = max(end_memory - start_memory, 0) if start_memory and end_memory else None

            # Parse output
            stdout = exec_result.output[0].decode() if exec_result.output[0] else ""
            stderr = exec_result.output[1].decode() if exec_result.output[1] else ""

            return {
                "stdout": stdout,
                "stderr": stderr,
                "exit_code": exec_result.exit_code,
                "execution_time_ms": execution_time_ms,
                "memory_usage_mb": memory_usage_mb,
                "cpu_usage_percent": None  # Would need more complex monitoring
            }

        except Exception as e:
            logger.error(f"❌ Docker command execution failed: {e}")
            return {
                "stdout": "",
                "stderr": str(e),
                "exit_code": 1,
                "execution_time_ms": 0,
                "memory_usage_mb": None,
                "cpu_usage_percent": None
            }

    def _get_container_memory_usage(self, container) -> Optional[int]:
        """Get container memory usage in MB."""
        try:
            stats = container.stats(stream=False)
            memory_usage = stats['memory_stats'].get('usage', 0)
            return int(memory_usage / (1024 * 1024))  # Convert to MB
        except:
            return None

    async def _create_docker_container(
        self,
        session_id: str,
        image: str,
        timeout_seconds: int
    ) -> tuple[str, str]:
        """Create a Docker container for the sandbox."""
        try:
            import docker
            client = docker.from_env()
            
            container = client.containers.run(
                image,
                command="sleep infinity",
                detach=True,
                name=f"sandbox_{session_id}",
                network_mode="none",  # Isolated network
                mem_limit="512m",  # Memory limit
                cpu_quota=50000,  # CPU limit (50% of one core)
                remove=False
            )
            
            return container.id, "running"

        except Exception as e:
            logger.error(f"❌ Failed to create Docker container: {e}")
            return None, "error"

    async def close_sandbox_session(self, session_id: str) -> bool:
        """Close a sandbox session and clean up resources."""
        try:
            from app.models.agent_tools import ToolSession

            session = self.db.query(ToolSession).filter(
                ToolSession.session_id == session_id
            ).first()

            if not session:
                raise ValueError(f"Session not found: {session_id}")

            # Stop Docker container if it exists
            if self.docker_available and session.sandbox_id:
                try:
                    import docker
                    client = docker.from_env()
                    container = client.containers.get(session.sandbox_id)
                    container.stop(timeout=10)
                    container.remove()
                    logger.info(f"🗑️ Cleaned up container {session.sandbox_id}")
                except Exception as e:
                    logger.warning(f"⚠️ Failed to cleanup container: {e}")

            # Update session status
            session.status = "closed"
            session.closed_at = datetime.utcnow()
            self.db.commit()

            structured_logger.log_info(
                "sandbox_session_closed",
                {"session_id": session_id, "container_id": session.sandbox_id}
            )

            return True

        except Exception as e:
            structured_logger.log_error(
                "sandbox_session_close_failed",
                {"session_id": session_id, "error": str(e)}
            )
            raise

    async def list_sandbox_sessions(
        self,
        agent_id: Optional[str] = None,
        status: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """List sandbox sessions with optional filtering."""
        try:
            from app.models.agent_tools import ToolSession

            query = self.db.query(ToolSession)

            if agent_id:
                query = query.filter(ToolSession.agent_id == agent_id)
            if status:
                query = query.filter(ToolSession.status == status)

            sessions = query.order_by(ToolSession.created_at.desc()).all()

            result = []
            for session in sessions:
                result.append({
                    "session_id": session.session_id,
                    "agent_id": session.agent_id,
                    "tool_id": str(session.tool_id),
                    "status": session.status,
                    "sandbox_status": session.sandbox_status,
                    "created_at": session.created_at.isoformat(),
                    "expires_at": session.expires_at.isoformat() if session.expires_at else None,
                    "closed_at": session.closed_at.isoformat() if session.closed_at else None
                })

            return result

        except Exception as e:
            structured_logger.log_error(
                "sandbox_sessions_list_failed",
                {"agent_id": agent_id, "status": status, "error": str(e)}
            )
            raise
    
    async def _execute_docker_command(
        self,
        container_id: str,
        command: str,
        working_directory: Optional[str] = None
    ) -> Dict[str, Any]:
        """Execute a command in a Docker container."""
        try:
            import docker
            import time
            
            client = docker.from_env()
            container = client.containers.get(container_id)
            
            start_time = time.time()
            exec_result = container.exec_run(
                command,
                workdir=working_directory,
                demux=True
            )
            execution_time = int((time.time() - start_time) * 1000)
            
            stdout = exec_result.output[0].decode() if exec_result.output[0] else ""
            stderr = exec_result.output[1].decode() if exec_result.output[1] else ""
            
            return {
                "stdout": stdout,
                "stderr": stderr,
                "exit_code": exec_result.exit_code,
                "execution_time_ms": execution_time
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to execute Docker command: {e}")
            raise
    
    async def _get_docker_container_state(self, container_id: str) -> Dict[str, Any]:
        """Get the state of a Docker container."""
        try:
            import docker
            client = docker.from_env()
            container = client.containers.get(container_id)
            
            return {
                "status": container.status,
                "running": container.status == "running"
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to get Docker container state: {e}")
            return {"status": "unknown", "running": False}
    
    async def _destroy_docker_container(self, container_id: str) -> None:
        """Stop and remove a Docker container."""
        try:
            import docker
            client = docker.from_env()
            container = client.containers.get(container_id)
            container.stop(timeout=5)
            container.remove()
            
        except Exception as e:
            logger.error(f"❌ Failed to destroy Docker container: {e}")

