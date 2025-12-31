"""
Collaboration Service

Service for managing multi-agent collaboration workflows and patterns.
Handles workflow creation, execution, and pattern management.
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.models.agent_collaboration import (
    CollaborationWorkflow, CollaborationStep, CollaborationPattern,
    CollaborationWorkflowCreate, CollaborationStepCreate, CollaborationPatternCreate,
    CollaborationWorkflowResponse, CollaborationPatternResponse
)

logger = logging.getLogger(__name__)


class CollaborationService:
    """Service for managing multi-agent collaboration."""

    def __init__(self, db: Session):
        self.db = db

    async def create_workflow(
        self,
        pattern_id: str,
        initiator_agent_id: str,
        task_description: str,
        context: Optional[Dict[str, Any]] = None,
        custom_steps: Optional[List[Dict[str, Any]]] = None
    ) -> CollaborationWorkflow:
        """
        Create a new collaboration workflow from a pattern.

        Args:
            pattern_id: ID of the collaboration pattern to use
            initiator_agent_id: ID of the agent initiating the workflow
            task_description: Description of the task
            context: Additional context for the workflow
            custom_steps: Optional custom steps (overrides pattern steps)

        Returns:
            Created CollaborationWorkflow object
        """
        try:
            # Get the pattern
            pattern = self.db.query(CollaborationPattern).filter(
                CollaborationPattern.pattern_id == pattern_id
            ).first()

            if not pattern:
                raise ValueError(f"Collaboration pattern '{pattern_id}' not found")

            if not pattern.enabled:
                raise ValueError(f"Collaboration pattern '{pattern_id}' is disabled")

            # Create workflow
            workflow = CollaborationWorkflow(
                pattern_id=pattern.id,
                initiator_agent_id=initiator_agent_id,
                task_description=task_description,
                context=context or {},
                status="pending",
                current_step=0,
                total_steps=len(custom_steps) if custom_steps else len(pattern.workflow_steps)
            )

            self.db.add(workflow)
            self.db.flush()  # Get workflow ID

            # Create workflow steps
            steps_to_create = custom_steps if custom_steps else pattern.workflow_steps

            for idx, step_data in enumerate(steps_to_create, start=1):
                step = CollaborationStep(
                    workflow_id=workflow.id,
                    step_number=idx,
                    agent_id=step_data.get("agent"),
                    action=step_data.get("action"),
                    input_data=step_data.get("input", {}),
                    status="pending",
                    can_run_parallel=step_data.get("parallel", False)
                )
                self.db.add(step)

            self.db.commit()
            self.db.refresh(workflow)

            logger.info(f"✅ Created workflow: {workflow.id} using pattern {pattern_id}")
            return workflow

        except Exception as e:
            self.db.rollback()
            logger.error(f"❌ Failed to create workflow: {e}")
            raise

    async def execute_workflow(
        self,
        workflow_id: str,
        max_steps: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Execute a collaboration workflow.

        Args:
            workflow_id: ID of the workflow to execute
            max_steps: Maximum number of steps to execute (None = all)

        Returns:
            Dict with execution results
        """
        try:
            workflow = self.db.query(CollaborationWorkflow).filter(
                CollaborationWorkflow.id == workflow_id
            ).first()

            if not workflow:
                raise ValueError(f"Workflow '{workflow_id}' not found")

            if workflow.status == "completed":
                raise ValueError(f"Workflow '{workflow_id}' is already completed")

            # Update workflow status
            workflow.status = "running"
            workflow.started_at = datetime.utcnow()
            self.db.commit()

            # Get pending steps
            steps = self.db.query(CollaborationStep).filter(
                and_(
                    CollaborationStep.workflow_id == workflow_id,
                    CollaborationStep.status == "pending"
                )
            ).order_by(CollaborationStep.step_number).all()

            if max_steps:
                steps = steps[:max_steps]

            executed_steps = []
            failed_steps = []

            # Execute steps
            for step in steps:
                try:
                    result = await self._execute_step(step)
                    executed_steps.append({
                        "step_number": step.step_number,
                        "agent_id": step.agent_id,
                        "action": step.action,
                        "status": "completed",
                        "result": result
                    })

                    workflow.current_step = step.step_number

                except Exception as step_error:
                    logger.error(f"❌ Step {step.step_number} failed: {step_error}")
                    failed_steps.append({
                        "step_number": step.step_number,
                        "agent_id": step.agent_id,
                        "error": str(step_error)
                    })

                    # Mark workflow as failed
                    workflow.status = "failed"
                    workflow.completed_at = datetime.utcnow()
                    self.db.commit()

                    return {
                        "workflow_id": workflow_id,
                        "status": "failed",
                        "executed_steps": executed_steps,
                        "failed_step": failed_steps[-1],
                        "error": f"Workflow failed at step {step.step_number}"
                    }

            # Check if workflow is complete
            remaining_steps = self.db.query(CollaborationStep).filter(
                and_(
                    CollaborationStep.workflow_id == workflow_id,
                    CollaborationStep.status == "pending"
                )
            ).count()

            if remaining_steps == 0:
                workflow.status = "completed"
                workflow.completed_at = datetime.utcnow()

            self.db.commit()

            logger.info(f"✅ Executed {len(executed_steps)} steps for workflow {workflow_id}")

            return {
                "workflow_id": workflow_id,
                "status": workflow.status,
                "executed_steps": executed_steps,
                "current_step": workflow.current_step,
                "total_steps": workflow.total_steps,
                "remaining_steps": remaining_steps
            }

        except Exception as e:
            self.db.rollback()
            logger.error(f"❌ Failed to execute workflow: {e}")
            raise

    async def get_workflow_status(self, workflow_id: str) -> Dict[str, Any]:
        """
        Get current status of a workflow.

        Args:
            workflow_id: ID of the workflow

        Returns:
            Dict with workflow status and progress
        """
        try:
            workflow = self.db.query(CollaborationWorkflow).filter(
                CollaborationWorkflow.id == workflow_id
            ).first()

            if not workflow:
                raise ValueError(f"Workflow '{workflow_id}' not found")

            # Get step statuses
            steps = self.db.query(CollaborationStep).filter(
                CollaborationStep.workflow_id == workflow_id
            ).order_by(CollaborationStep.step_number).all()

            step_statuses = [
                {
                    "step_number": step.step_number,
                    "agent_id": step.agent_id,
                    "action": step.action,
                    "status": step.status,
                    "started_at": step.started_at.isoformat() if step.started_at else None,
                    "completed_at": step.completed_at.isoformat() if step.completed_at else None
                }
                for step in steps
            ]

            return {
                "workflow_id": workflow_id,
                "status": workflow.status,
                "current_step": workflow.current_step,
                "total_steps": workflow.total_steps,
                "progress_percentage": (workflow.current_step / workflow.total_steps * 100) if workflow.total_steps > 0 else 0,
                "started_at": workflow.started_at.isoformat() if workflow.started_at else None,
                "completed_at": workflow.completed_at.isoformat() if workflow.completed_at else None,
                "steps": step_statuses
            }

        except Exception as e:
            logger.error(f"❌ Failed to get workflow status: {e}")
            raise

    async def register_pattern(
        self,
        pattern_data: CollaborationPatternCreate
    ) -> CollaborationPattern:
        """
        Register a new collaboration pattern.

        Args:
            pattern_data: Pattern data to register

        Returns:
            Created CollaborationPattern object
        """
        try:
            # Check if pattern already exists
            existing = self.db.query(CollaborationPattern).filter(
                CollaborationPattern.pattern_id == pattern_data.pattern_id
            ).first()

            if existing:
                raise ValueError(f"Pattern '{pattern_data.pattern_id}' already exists")

            pattern = CollaborationPattern(
                pattern_id=pattern_data.pattern_id,
                name=pattern_data.name,
                description=pattern_data.description,
                pattern_type=pattern_data.pattern_type,
                required_agents=pattern_data.required_agents,
                optional_agents=pattern_data.optional_agents,
                workflow_steps=pattern_data.workflow_steps,
                decision_points=pattern_data.decision_points,
                max_steps=pattern_data.max_steps,
                max_execution_time=pattern_data.max_execution_time,
                enabled=pattern_data.enabled
            )

            self.db.add(pattern)
            self.db.commit()
            self.db.refresh(pattern)

            logger.info(f"✅ Registered collaboration pattern: {pattern.pattern_id}")
            return pattern

        except Exception as e:
            self.db.rollback()
            logger.error(f"❌ Failed to register pattern: {e}")
            raise

    async def get_available_patterns(
        self,
        pattern_type: Optional[str] = None,
        enabled_only: bool = True
    ) -> List[CollaborationPattern]:
        """
        List available collaboration patterns.

        Args:
            pattern_type: Filter by pattern type (hierarchical, peer_to_peer, hybrid)
            enabled_only: Only return enabled patterns

        Returns:
            List of collaboration patterns
        """
        try:
            query = self.db.query(CollaborationPattern)

            if enabled_only:
                query = query.filter(CollaborationPattern.enabled == True)

            if pattern_type:
                query = query.filter(CollaborationPattern.pattern_type == pattern_type)

            patterns = query.order_by(CollaborationPattern.name).all()

            logger.info(f"✅ Retrieved {len(patterns)} collaboration patterns")
            return patterns

        except Exception as e:
            logger.error(f"❌ Failed to retrieve patterns: {e}")
            raise

    async def get_pattern_by_id(self, pattern_id: str) -> Optional[CollaborationPattern]:
        """Get a collaboration pattern by ID."""
        return self.db.query(CollaborationPattern).filter(
            CollaborationPattern.pattern_id == pattern_id
        ).first()

    async def update_pattern_stats(
        self,
        pattern_id: str,
        success: bool
    ) -> None:
        """
        Update usage statistics for a pattern.

        Args:
            pattern_id: ID of the pattern
            success: Whether the workflow was successful
        """
        try:
            pattern = await self.get_pattern_by_id(pattern_id)
            if pattern:
                pattern.usage_count += 1
                if success:
                    pattern.success_count += 1
                self.db.commit()

        except Exception as e:
            logger.error(f"❌ Failed to update pattern stats: {e}")
            # Don't raise - stats update failure shouldn't break workflow

    async def _execute_step(self, step: CollaborationStep) -> Dict[str, Any]:
        """
        Execute a single workflow step.

        This is a placeholder implementation. In production, this would:
        1. Call the appropriate agent service
        2. Pass input data and context
        3. Wait for agent response
        4. Store output data

        Args:
            step: The step to execute

        Returns:
            Dict with step execution result
        """
        try:
            # Mark step as running
            step.status = "running"
            step.started_at = datetime.utcnow()
            self.db.commit()

            # Simulate step execution
            logger.info(f"🚀 Executing step {step.step_number}: {step.action} (Agent: {step.agent_id})")

            # In real implementation, this would call the agent service
            # For now, we'll simulate a successful execution
            result = {
                "success": True,
                "agent_id": step.agent_id,
                "action": step.action,
                "output": f"Simulated output for {step.action}",
                "execution_time_ms": 100
            }

            # Update step with result
            step.status = "completed"
            step.completed_at = datetime.utcnow()
            step.output_data = result
            self.db.commit()

            logger.info(f"✅ Completed step {step.step_number}")

            return result

        except Exception as e:
            step.status = "failed"
            step.completed_at = datetime.utcnow()
            step.output_data = {"error": str(e)}
            self.db.commit()

            logger.error(f"❌ Step {step.step_number} failed: {e}")
            raise

    async def cancel_workflow(self, workflow_id: str, reason: Optional[str] = None) -> Dict[str, Any]:
        """
        Cancel a running workflow.

        Args:
            workflow_id: ID of the workflow to cancel
            reason: Optional reason for cancellation

        Returns:
            Dict with cancellation result
        """
        try:
            workflow = self.db.query(CollaborationWorkflow).filter(
                CollaborationWorkflow.id == workflow_id
            ).first()

            if not workflow:
                raise ValueError(f"Workflow '{workflow_id}' not found")

            if workflow.status in ["completed", "failed", "cancelled"]:
                raise ValueError(f"Cannot cancel workflow with status: {workflow.status}")

            # Cancel pending steps
            pending_steps = self.db.query(CollaborationStep).filter(
                and_(
                    CollaborationStep.workflow_id == workflow_id,
                    CollaborationStep.status == "pending"
                )
            ).all()

            for step in pending_steps:
                step.status = "cancelled"

            # Update workflow
            workflow.status = "cancelled"
            workflow.completed_at = datetime.utcnow()

            self.db.commit()

            logger.info(f"✅ Cancelled workflow: {workflow_id}")

            return {
                "workflow_id": workflow_id,
                "status": "cancelled",
                "reason": reason,
                "cancelled_steps": len(pending_steps)
            }

        except Exception as e:
            self.db.rollback()
            logger.error(f"❌ Failed to cancel workflow: {e}")
            raise


    # ========================================================================
    # Phase 5: Task Force Collaboration
    # ========================================================================

    async def create_task_force(
        self,
        specialist_agent_ids: List[str],
        task_description: str,
        initiator_agent_id: str,
        context: Optional[Dict[str, Any]] = None
    ) -> CollaborationWorkflow:
        """
        Create a temporary Task Force for collaborative problem-solving.

        This creates a special workflow type where agents engage in
        conversational collaboration until reaching a terminal state.

        Args:
            specialist_agent_ids: List of agent IDs to participate
            task_description: Description of the problem to solve
            initiator_agent_id: ID of the agent initiating the task force
            context: Additional context for the task force

        Returns:
            Created CollaborationWorkflow object with workflow_type='task_force'
        """
        try:
            import uuid
            from app.models.agent_collaboration import CollaborationStatus

            # Create a task force workflow (using peer-to-peer pattern)
            workflow_id = f"taskforce_{uuid.uuid4().hex[:12]}"

            workflow = CollaborationWorkflow(
                workflow_id=workflow_id,
                task_description=task_description,
                orchestration_pattern="peer_to_peer",
                initiator_agent_id=initiator_agent_id,
                participating_agents=specialist_agent_ids,
                collaboration_graph={
                    "type": "task_force",
                    "specialists": specialist_agent_ids,
                    "context": context or {}
                },
                status=CollaborationStatus.INITIATED,
                workflow_type="task_force",  # Phase 5 field
                terminal_state=None
            )

            self.db.add(workflow)
            self.db.commit()
            self.db.refresh(workflow)

            logger.info(f"✅ Created task force: {workflow_id} with {len(specialist_agent_ids)} specialists")

            return workflow

        except Exception as e:
            self.db.rollback()
            logger.error(f"❌ Failed to create task force: {e}")
            raise

    async def add_task_force_message(
        self,
        workflow_id: str,
        agent_id: str,
        message: str,
        message_type: str = "response"
    ) -> Dict[str, Any]:
        """
        Add a message to the task force conversation.

        Args:
            workflow_id: ID of the task force workflow
            agent_id: ID of the agent sending the message
            message: The message content
            message_type: Type of message (response, question, proposal, agreement)

        Returns:
            Dictionary with message details
        """
        try:
            import uuid
            from app.models.agent_collaboration import TaskForceMessage

            # Verify workflow exists and is a task force
            workflow = self.db.query(CollaborationWorkflow).filter(
                CollaborationWorkflow.workflow_id == workflow_id
            ).first()

            if not workflow:
                raise ValueError(f"Workflow not found: {workflow_id}")

            if workflow.workflow_type != "task_force":
                raise ValueError(f"Workflow {workflow_id} is not a task force")

            # Create message
            task_force_message = TaskForceMessage(
                workflow_id=workflow.id,
                agent_id=agent_id,
                message=message,
                message_type=message_type,
                metadata={"timestamp": datetime.utcnow().isoformat()}
            )

            self.db.add(task_force_message)
            self.db.commit()
            self.db.refresh(task_force_message)

            logger.info(f"✅ Added task force message from {agent_id} to {workflow_id}")

            return {
                "message_id": str(task_force_message.id),
                "workflow_id": workflow_id,
                "agent_id": agent_id,
                "message": message,
                "message_type": message_type,
                "timestamp": task_force_message.timestamp.isoformat()
            }

        except Exception as e:
            self.db.rollback()
            logger.error(f"❌ Failed to add task force message: {e}")
            raise

    async def get_task_force_conversation(
        self,
        workflow_id: str
    ) -> List[Dict[str, Any]]:
        """
        Retrieve the full conversation history of a task force.

        Args:
            workflow_id: ID of the task force workflow

        Returns:
            List of messages in chronological order
        """
        try:
            from app.models.agent_collaboration import TaskForceMessage

            # Verify workflow exists
            workflow = self.db.query(CollaborationWorkflow).filter(
                CollaborationWorkflow.workflow_id == workflow_id
            ).first()

            if not workflow:
                raise ValueError(f"Workflow not found: {workflow_id}")

            # Get all messages
            messages = self.db.query(TaskForceMessage).filter(
                TaskForceMessage.workflow_id == workflow.id
            ).order_by(TaskForceMessage.timestamp).all()

            conversation = [
                {
                    "message_id": str(msg.id),
                    "agent_id": msg.agent_id,
                    "message": msg.message,
                    "message_type": msg.message_type,
                    "timestamp": msg.timestamp.isoformat(),
                    "metadata": msg.metadata
                }
                for msg in messages
            ]

            logger.info(f"✅ Retrieved {len(conversation)} messages for task force {workflow_id}")

            return conversation

        except Exception as e:
            logger.error(f"❌ Failed to get task force conversation: {e}")
            raise

    async def evaluate_task_force_completion(
        self,
        workflow_id: str
    ) -> Dict[str, Any]:
        """
        Evaluate if the task force has reached a terminal state
        (solution found or failure declared).

        Args:
            workflow_id: ID of the task force workflow

        Returns:
            Dictionary with completion status and terminal state
        """
        try:
            from app.models.agent_collaboration import TaskForceMessage, CollaborationStatus

            # Get workflow
            workflow = self.db.query(CollaborationWorkflow).filter(
                CollaborationWorkflow.workflow_id == workflow_id
            ).first()

            if not workflow:
                raise ValueError(f"Workflow not found: {workflow_id}")

            # Get recent messages
            messages = self.db.query(TaskForceMessage).filter(
                TaskForceMessage.workflow_id == workflow.id
            ).order_by(TaskForceMessage.timestamp.desc()).limit(10).all()

            # Simple heuristic: check for agreement or failure keywords
            terminal_keywords = {
                "solution_found": ["agreed", "solution", "consensus", "resolved", "complete"],
                "failed": ["failed", "impossible", "cannot", "deadlock", "timeout"],
                "timeout": ["timeout", "expired", "too long"]
            }

            terminal_state = None
            for msg in messages:
                msg_lower = msg.message.lower()
                for state, keywords in terminal_keywords.items():
                    if any(keyword in msg_lower for keyword in keywords):
                        terminal_state = state
                        break
                if terminal_state:
                    break

            # Update workflow if terminal state reached
            if terminal_state:
                workflow.terminal_state = terminal_state
                workflow.status = CollaborationStatus.COMPLETED if terminal_state == "solution_found" else CollaborationStatus.FAILED
                workflow.completed_at = datetime.utcnow()
                self.db.commit()

                logger.info(f"✅ Task force {workflow_id} reached terminal state: {terminal_state}")

            return {
                "workflow_id": workflow_id,
                "is_complete": terminal_state is not None,
                "terminal_state": terminal_state,
                "status": workflow.status.value if hasattr(workflow.status, 'value') else str(workflow.status),
                "message_count": len(messages)
            }

        except Exception as e:
            logger.error(f"❌ Failed to evaluate task force completion: {e}")
            raise


