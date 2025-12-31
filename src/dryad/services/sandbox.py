import logging
import asyncio
from typing import Dict, Any, Optional
import docker
from docker.errors import DockerException, APIError

logger = logging.getLogger(__name__)

class SandboxService:
    """
    Service for executing code in isolated Docker environments.
    """
    
    def __init__(self, docker_enabled: bool = True):
        self.docker_enabled = docker_enabled
        self.client = None
        if self.docker_enabled:
            try:
                self.client = docker.from_env()
                self.client.ping()
                logger.info("✅ Docker client connected successfully.")
            except (DockerException, APIError) as e:
                logger.warning(f"⚠️ Docker connection failed: {e}. Falling back to MOCK mode.")
                self.docker_enabled = False
        
    async def execute_command(
        self, 
        image: str, 
        command: str, 
        timeout: int = 30
    ) -> Dict[str, Any]:
        """
        Execute a command in a sandboxed container.
        """
        if not self.docker_enabled:
            return await self._mock_execution(image, command)
            
        return await self._docker_execution(image, command, timeout)

    async def _docker_execution(self, image: str, command: str, timeout: int) -> Dict[str, Any]:
        """
        Run command in a real ephemeral container.
        """
        try:
            # We run the blocking docker call in an executor to avoid blocking the async loop
            loop = asyncio.get_running_loop()
            
            def run_container():
                return self.client.containers.run(
                    image=image,
                    command=command,
                    remove=True, # Ephemeral
                    stdout=True,
                    stderr=True,
                    mem_limit="512m", # Hardening: Limit RAM
                    network_mode="none", # Hardening: No network access by default
                    read_only=True, # Hardening: Read-only FS generally
                    # We might need a working dir that is writable, or mount a volume?
                    # For simple "python -c", read-only root is usually fine if /tmp is usable.
                )

            output = await loop.run_in_executor(None, run_container)
            
            return {
                "status": "success",
                "exit_code": 0,
                "stdout": output.decode('utf-8'),
                "stderr": "",
            }
            
        except docker.errors.ContainerError as e:
             return {
                "status": "error",
                "exit_code": e.exit_status,
                "stdout": e.stderr.decode('utf-8') if e.stderr else "", # Container error often logs to stderr
                "stderr": str(e)
            }
        except Exception as e:
            logger.error(f"Docker execution failed: {e}")
            return {
                "status": "system_error",
                "error": str(e)
            }

    async def _mock_execution(self, image: str, command: str) -> Dict[str, Any]:
        """
        Simulate execution for testing.
        """
        logger.info(f"Mock executing in {image}: {command}")
        await asyncio.sleep(0.5)
        return {
            "status": "success",
            "exit_code": 0,
            "stdout": f"Mock output for command: {command}",
            "stderr": "",
            "execution_time_ms": 500
        }
