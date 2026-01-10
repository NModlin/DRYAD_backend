"""
Tool Registry Service

Service for managing the agent tool catalog, permissions, and usage.
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import and_, select
from sqlalchemy.exc import IntegrityError

from app.models.agent_tools import (
    AgentToolCatalog, ToolPermission, ToolUsageLog,
    ToolCategory, ToolSecurityLevel,
    ToolCatalogCreate, ToolPermissionCreate,
    ToolUsageRequest, ToolUsageResponse
)

logger = logging.getLogger(__name__)


class ToolRegistryService:
    """
    (DEPRECATED) Service for managing agent tools.
    
    .. warning::
        This service is deprecated and will be removed in a future version.
        Please use `app.services.tool_registry.service.ToolRegistryService` instead.
    """

    def __init__(self, db: AsyncSession):
        import warnings
        warnings.warn(
            "app.services.tool_registry_service.ToolRegistryService is deprecated. "
            "Use app.services.tool_registry.service.ToolRegistryService instead.",
            DeprecationWarning,
            stacklevel=2
        )
        self.db = db

    async def register_tool(self, tool_data: ToolCatalogCreate) -> AgentToolCatalog:
        """Register a new tool in the catalog."""
        try:
            # Check if tool already exists
            query = select(AgentToolCatalog).where(AgentToolCatalog.tool_id == tool_data.tool_id)
            result = await self.db.execute(query)
            existing = result.scalar_one_or_none()

            if existing:
                raise ValueError(f"Tool with ID '{tool_data.tool_id}' already exists")

            # Create tool
            tool = AgentToolCatalog(
                tool_id=tool_data.tool_id,
                name=tool_data.name,
                display_name=tool_data.display_name,
                description=tool_data.description,
                category=tool_data.category,
                security_level=tool_data.security_level,
                configuration_schema=tool_data.configuration_schema,
                default_configuration=tool_data.default_configuration,
                required_permissions=tool_data.required_permissions,
                implementation_class=tool_data.implementation_class,
                implementation_function=tool_data.implementation_function,
                max_execution_time=tool_data.max_execution_time,
                rate_limit=tool_data.rate_limit,
                requires_human_approval=tool_data.requires_human_approval,
                enabled=tool_data.enabled,
                version=tool_data.version,
                documentation_url=tool_data.documentation_url,
                examples=tool_data.examples
            )

            self.db.add(tool)
            await self.db.commit()
            await self.db.refresh(tool)

            logger.info(f"✅ Registered tool: {tool.tool_id} ({tool.security_level.value})")
            return tool

        except Exception as e:
            await self.db.rollback()
            logger.error(f"❌ Failed to register tool: {e}")
            raise

    async def get_tool(self, tool_id: str) -> Optional[AgentToolCatalog]:
        """Get a tool by ID."""
        query = select(AgentToolCatalog).where(AgentToolCatalog.tool_id == tool_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def list_tools(
        self,
        category: Optional[ToolCategory] = None,
        security_level: Optional[ToolSecurityLevel] = None,
        enabled_only: bool = True
    ) -> List[AgentToolCatalog]:
        """List tools with optional filters."""
        query = select(AgentToolCatalog)

        if enabled_only:
            query = query.where(AgentToolCatalog.enabled == True)

        if category:
            query = query.where(AgentToolCatalog.category == category)

        if security_level:
            query = query.where(AgentToolCatalog.security_level == security_level)

        query = query.order_by(AgentToolCatalog.name)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def validate_tool_request(
        self,
        tool_id: str,
        agent_category: str,
        agent_tier: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Validate if an agent can use a specific tool.

        Returns:
            Dict with 'allowed', 'reason', and 'constraints'
        """
        # Get tool
        tool = await self.get_tool(tool_id)
        if not tool:
            return {
                "allowed": False,
                "reason": f"Tool '{tool_id}' not found in catalog",
                "constraints": {}
            }

        if not tool.enabled:
            return {
                "allowed": False,
                "reason": f"Tool '{tool_id}' is disabled",
                "constraints": {}
            }

        if tool.deprecated:
            return {
                "allowed": False,
                "reason": f"Tool '{tool_id}' is deprecated: {tool.deprecation_message}",
                "constraints": {}
            }

        # Check permissions
        query = select(ToolPermission).where(
            and_(
                ToolPermission.tool_id == tool.id,
                ToolPermission.agent_category == agent_category
            )
        )
        result = await self.db.execute(query)
        permission = result.scalar_one_or_none()

        # If no specific permission, check if tool is generally safe
        if not permission:
            if tool.security_level in [ToolSecurityLevel.SAFE, ToolSecurityLevel.LOW_RISK]:
                return {
                    "allowed": True,
                    "reason": "Tool is safe for general use",
                    "constraints": {
                        "max_execution_time": tool.max_execution_time,
                        "rate_limit": tool.rate_limit,
                        "requires_approval": tool.requires_human_approval
                    }
                }
            else:
                return {
                    "allowed": False,
                    "reason": f"Tool requires explicit permission for category '{agent_category}'",
                    "constraints": {}
                }

        if not permission.allowed:
            return {
                "allowed": False,
                "reason": f"Tool is not allowed for category '{agent_category}'",
                "constraints": {}
            }

        # Build constraints
        constraints = {
            "max_execution_time": tool.max_execution_time,
            "rate_limit": tool.rate_limit,
            "requires_approval": tool.requires_human_approval or permission.requires_approval_override,
            "max_calls_per_execution": permission.max_calls_per_execution
        }

        if permission.additional_constraints:
            constraints.update(permission.additional_constraints)

        return {
            "allowed": True,
            "reason": "Tool is allowed",
            "constraints": constraints
        }

    async def log_tool_usage(
        self,
        execution_id: str,
        tool_id: str,
        agent_id: str,
        input_parameters: Dict[str, Any],
        output_result: Optional[Dict[str, Any]] = None,
        execution_time: Optional[int] = None,
        success: bool = True,
        error_message: Optional[str] = None,
        approved_by: Optional[str] = None
    ) -> ToolUsageLog:
        """Log tool usage."""
        try:
            # Get tool
            tool = await self.get_tool(tool_id)
            if not tool:
                raise ValueError(f"Tool '{tool_id}' not found")

            log = ToolUsageLog(
                execution_id=execution_id,
                tool_id=tool.id,
                agent_id=agent_id,
                input_parameters=input_parameters,
                output_result=output_result,
                execution_time=execution_time,
                success=success,
                error_message=error_message,
                approved_by=approved_by,
                approval_timestamp=datetime.utcnow() if approved_by else None
            )

            self.db.add(log)
            await self.db.commit()
            await self.db.refresh(log)

            return log

        except Exception as e:
            await self.db.rollback()
            logger.error(f"❌ Failed to log tool usage: {e}")
            raise

    async def get_tool_usage_stats(self, tool_id: str) -> Dict[str, Any]:
        """Get usage statistics for a tool."""
        tool = await self.get_tool(tool_id)
        if not tool:
            raise ValueError(f"Tool '{tool_id}' not found")

        query = select(ToolUsageLog).where(ToolUsageLog.tool_id == tool.id)
        result = await self.db.execute(query)
        logs = result.scalars().all()

        total_uses = len(logs)
        successful_uses = sum(1 for log in logs if log.success)
        failed_uses = total_uses - successful_uses
        avg_execution_time = sum(log.execution_time or 0 for log in logs) / total_uses if total_uses > 0 else 0

        return {
            "tool_id": tool_id,
            "total_uses": total_uses,
            "successful_uses": successful_uses,
            "failed_uses": failed_uses,
            "success_rate": successful_uses / total_uses if total_uses > 0 else 0,
            "avg_execution_time_ms": avg_execution_time
        }


def get_default_tool_catalog() -> List[Dict[str, Any]]:
    """
    Get default tool catalog with common tools.

    This should be called during system initialization to populate the tool catalog.
    """
    return [
        {
            "tool_id": "database_query",
            "name": "Database Query",
            "display_name": "Database Query Tool",
            "description": "Execute read-only database queries",
            "category": ToolCategory.DATABASE,
            "security_level": ToolSecurityLevel.SAFE,
            "required_permissions": ["database.read"],
            "max_execution_time": 30,
            "rate_limit": 20,
            "requires_human_approval": False,
            "examples": [
                {
                    "title": "Query users",
                    "code": "SELECT * FROM users WHERE active = true LIMIT 10",
                    "description": "Fetch active users"
                }
            ]
        },
        {
            "tool_id": "powershell_ad_query",
            "name": "PowerShell AD Query",
            "display_name": "Active Directory Query (PowerShell)",
            "description": "Execute read-only Active Directory queries via PowerShell",
            "category": ToolCategory.POWERSHELL,
            "security_level": ToolSecurityLevel.LOW_RISK,
            "required_permissions": ["ad.read", "powershell.execute"],
            "max_execution_time": 60,
            "rate_limit": 10,
            "requires_human_approval": False,
            "examples": [
                {
                    "title": "Get AD User",
                    "code": "Get-ADUser -Identity 'jdoe' -Properties *",
                    "description": "Retrieve user details from Active Directory"
                }
            ]
        },
        {
            "tool_id": "powershell_ad_modify",
            "name": "PowerShell AD Modify",
            "display_name": "Active Directory Modification (PowerShell)",
            "description": "Execute Active Directory modifications via PowerShell",
            "category": ToolCategory.POWERSHELL,
            "security_level": ToolSecurityLevel.HIGH_RISK,
            "required_permissions": ["ad.write", "powershell.execute"],
            "max_execution_time": 60,
            "rate_limit": 5,
            "requires_human_approval": True,
            "examples": [
                {
                    "title": "Reset Password",
                    "code": "Set-ADAccountPassword -Identity 'jdoe' -Reset",
                    "description": "Reset user password (requires approval)"
                }
            ]
        }
    ]


    # ========================================================================
    # Phase 5: Stateful Tool Execution
    # ========================================================================

    async def create_stateful_session(
        self,
        tool_id: str,
        agent_id: str,
        execution_id: str
    ) -> str:
        """
        Create a stateful execution session for a tool.

        Args:
            tool_id: ID of the tool
            agent_id: ID of the agent requesting the session
            execution_id: ID of the execution context

        Returns:
            session_id: Unique identifier for the session
        """
        try:
            from app.services.sandbox_service import SandboxService

            # Get tool
            query = select(AgentToolCatalog).where(AgentToolCatalog.tool_id == tool_id)
            result = await self.db.execute(query)
            tool = result.scalar_one_or_none()

            if not tool:
                raise ValueError(f"Tool not found: {tool_id}")

            if not tool.stateful:
                raise ValueError(f"Tool {tool_id} does not support stateful execution")

            # Create sandbox session if required
            if tool.requires_sandbox:
                sandbox_service = SandboxService(self.db)
                session_id = await sandbox_service.create_sandbox_session(
                    agent_id=agent_id,
                    tool_id=tool_id,
                    timeout_seconds=tool.max_session_duration or 300
                )
            else:
                # Create simple stateful session without sandbox
                import uuid
                from app.models.agent_tools import ToolSession
                from datetime import timedelta

                session_id = f"session_{uuid.uuid4().hex[:16]}"

                session = ToolSession(
                    session_id=session_id,
                    tool_id=tool.id,
                    agent_id=agent_id,
                    execution_id=execution_id,
                    sandbox_id=None,
                    sandbox_status="not_required",
                    status="active",
                    expires_at=datetime.utcnow() + timedelta(seconds=tool.max_session_duration or 300)
                )

                self.db.add(session)
                await self.db.commit()

            logger.info(f"✅ Created stateful session {session_id} for tool {tool_id}")

            return session_id

        except Exception as e:
            await self.db.rollback()
            logger.error(f"❌ Failed to create stateful session: {e}")
            raise

    async def execute_stateful_tool(
        self,
        session_id: str,
        tool_id: str,
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute a tool within a stateful session.

        Args:
            session_id: ID of the stateful session
            tool_id: ID of the tool to execute
            parameters: Tool execution parameters

        Returns:
            Dictionary with execution results
        """
        try:
            from app.models.agent_tools import ToolSession
            from app.services.sandbox_service import SandboxService

            # Get session
            query = select(ToolSession).where(ToolSession.session_id == session_id)
            result = await self.db.execute(query)
            session = result.scalar_one_or_none()

            if not session:
                raise ValueError(f"Session not found: {session_id}")

            if session.status != "active":
                raise ValueError(f"Session {session_id} is not active")

            # Get tool
            tool_query = select(AgentToolCatalog).where(AgentToolCatalog.tool_id == tool_id)
            tool_result = await self.db.execute(tool_query)
            tool = tool_result.scalar_one_or_none()

            if not tool:
                raise ValueError(f"Tool not found: {tool_id}")

            # Execute in sandbox if required
            if tool.requires_sandbox and session.sandbox_id:
                sandbox_service = SandboxService(self.db)

                # Build command from parameters
                command = self._build_command(tool, parameters)

                result = await sandbox_service.execute_in_sandbox(
                    session_id=session_id,
                    command=command
                )
            else:
                # Mock execution for non-sandboxed tools
                result = {
                    "success": True,
                    "output": f"Executed {tool.name} with parameters: {parameters}",
                    "execution_time_ms": 50
                }

            # Log usage
            await self.log_tool_usage(
                tool_id=tool_id,
                agent_id=session.agent_id,
                execution_id=session.execution_id,
                parameters=parameters,
                success=result.get("exit_code", 0) == 0 if "exit_code" in result else result.get("success", True),
                execution_time_ms=result.get("execution_time_ms", 0)
            )

            logger.info(f"✅ Executed tool {tool_id} in session {session_id}")

            return result

        except Exception as e:
            logger.error(f"❌ Failed to execute stateful tool: {e}")
            raise

    async def close_stateful_session(
        self,
        session_id: str
    ) -> None:
        """
        Close and clean up a stateful session.

        Args:
            session_id: ID of the session to close
        """
        try:
            from app.models.agent_tools import ToolSession
            from app.services.sandbox_service import SandboxService

            # Get session
            query = select(ToolSession).where(ToolSession.session_id == session_id)
            result = await self.db.execute(query)
            session = result.scalar_one_or_none()

            if not session:
                raise ValueError(f"Session not found: {session_id}")

            # Destroy sandbox if exists
            if session.sandbox_id:
                sandbox_service = SandboxService(self.db)
                await sandbox_service.destroy_sandbox_session(session_id)
            else:
                # Just update session status
                session.status = "closed"
                session.closed_at = datetime.utcnow()
                await self.db.commit()

            logger.info(f"✅ Closed stateful session: {session_id}")

        except Exception as e:
            await self.db.rollback()
            logger.error(f"❌ Failed to close stateful session: {e}")
            raise

    def _build_command(self, tool: AgentToolCatalog, parameters: Dict[str, Any]) -> str:
        """Build a command string from tool and parameters."""
        # Simple command builder - can be enhanced based on tool type
        if tool.category == ToolCategory.POWERSHELL:
            # Build PowerShell command
            cmd_parts = [tool.implementation_function or "Invoke-Command"]
            for key, value in parameters.items():
                cmd_parts.append(f"-{key} '{value}'")
            return " ".join(cmd_parts)
        else:
            # Generic command
            return f"{tool.implementation_function or 'execute'} {' '.join(f'--{k}={v}' for k, v in parameters.items())}"

