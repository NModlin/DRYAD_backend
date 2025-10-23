"""
HITL (Human-in-the-Loop) Approval Service

Service for managing human approval workflows for high-risk agent operations.
Handles approval requests, policy checks, and action execution.
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from app.models.hitl_approval import (
    PendingApproval, ApprovalPolicy, ApprovalAuditLog,
    ApprovalStatus, RiskLevel, ActionType,
    PendingApprovalCreate, ApprovalPolicyCreate,
    PendingApprovalResponse, ApprovalPolicyResponse
)

logger = logging.getLogger(__name__)


class HITLApprovalService:
    """Service for managing human-in-the-loop approval workflows."""

    def __init__(self, db: Session):
        self.db = db

    async def check_approval_required(
        self,
        action_type: ActionType,
        risk_level: RiskLevel,
        agent_id: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Check if an operation requires human approval based on policies.

        Args:
            action_type: Type of action being performed
            risk_level: Risk level of the operation
            agent_id: ID of the agent requesting the action
            context: Additional context for policy evaluation

        Returns:
            Dict with 'required', 'policy_id', and 'reason'
        """
        try:
            # Query applicable policies
            policies = self.db.query(ApprovalPolicy).filter(
                and_(
                    ApprovalPolicy.enabled == True,
                    ApprovalPolicy.action_types.contains([action_type.value])
                )
            ).all()

            # Check each policy
            for policy in policies:
                # Check risk level threshold
                risk_levels = [RiskLevel.LOW, RiskLevel.MEDIUM, RiskLevel.HIGH, RiskLevel.CRITICAL]
                min_risk_index = risk_levels.index(policy.min_risk_level)
                current_risk_index = risk_levels.index(risk_level)

                if current_risk_index >= min_risk_index:
                    # Check if agent is in excluded list
                    if policy.excluded_agents and agent_id in policy.excluded_agents:
                        continue

                    # Check conditions if specified
                    if policy.conditions and context:
                        if not self._evaluate_conditions(policy.conditions, context):
                            continue

                    logger.info(f"✅ Approval required for {action_type.value} (Policy: {policy.policy_id})")
                    return {
                        "required": True,
                        "policy_id": policy.policy_id,
                        "policy_name": policy.name,
                        "reason": policy.description,
                        "auto_approve_timeout": policy.auto_approve_timeout
                    }

            logger.info(f"✅ No approval required for {action_type.value}")
            return {
                "required": False,
                "policy_id": None,
                "reason": "No matching approval policy found"
            }

        except Exception as e:
            logger.error(f"❌ Failed to check approval requirement: {e}")
            raise

    async def create_approval_request(
        self,
        execution_id: str,
        agent_id: str,
        action_type: ActionType,
        action_description: str,
        risk_level: RiskLevel,
        action_payload: Dict[str, Any],
        policy_id: Optional[str] = None,
        requested_by: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> PendingApproval:
        """
        Create a new approval request for a high-risk operation.

        Args:
            execution_id: ID of the agent execution
            agent_id: ID of the agent requesting approval
            action_type: Type of action requiring approval
            action_description: Human-readable description
            risk_level: Risk level of the operation
            action_payload: Data needed to execute the action
            policy_id: ID of the policy triggering approval
            requested_by: User who initiated the request
            context: Additional context

        Returns:
            Created PendingApproval object
        """
        try:
            approval = PendingApproval(
                execution_id=execution_id,
                agent_id=agent_id,
                action_type=action_type,
                action_description=action_description,
                risk_level=risk_level,
                action_payload=action_payload,
                policy_id=policy_id,
                requested_by=requested_by,
                context=context,
                status=ApprovalStatus.PENDING
            )

            self.db.add(approval)
            self.db.commit()
            self.db.refresh(approval)

            logger.info(f"✅ Created approval request: {approval.id} for {action_type.value}")
            return approval

        except Exception as e:
            self.db.rollback()
            logger.error(f"❌ Failed to create approval request: {e}")
            raise

    async def approve_request(
        self,
        approval_id: str,
        approved_by: str,
        approval_notes: Optional[str] = None,
        execute_immediately: bool = True
    ) -> Dict[str, Any]:
        """
        Approve a pending request and optionally execute the action.

        Args:
            approval_id: ID of the approval request
            approved_by: User approving the request
            approval_notes: Optional notes from approver
            execute_immediately: Whether to execute the action immediately

        Returns:
            Dict with approval result and execution status
        """
        try:
            approval = self.db.query(PendingApproval).filter(
                PendingApproval.id == approval_id
            ).first()

            if not approval:
                raise ValueError(f"Approval request '{approval_id}' not found")

            if approval.status != ApprovalStatus.PENDING:
                raise ValueError(f"Approval request is not pending (status: {approval.status.value})")

            # Update approval
            approval.status = ApprovalStatus.APPROVED
            approval.approved_by = approved_by
            approval.approved_at = datetime.utcnow()
            approval.approval_notes = approval_notes

            # Create audit log
            audit_log = ApprovalAuditLog(
                approval_id=approval.id,
                action="APPROVED",
                performed_by=approved_by,
                notes=approval_notes,
                previous_status=ApprovalStatus.PENDING.value,
                new_status=ApprovalStatus.APPROVED.value
            )
            self.db.add(audit_log)

            self.db.commit()
            self.db.refresh(approval)

            logger.info(f"✅ Approved request: {approval_id} by {approved_by}")

            result = {
                "approval_id": approval_id,
                "status": "approved",
                "approved_by": approved_by,
                "approved_at": approval.approved_at.isoformat()
            }

            # Execute action if requested
            if execute_immediately:
                execution_result = await self.execute_approved_action(approval_id)
                result["execution"] = execution_result

            return result

        except Exception as e:
            self.db.rollback()
            logger.error(f"❌ Failed to approve request: {e}")
            raise

    async def reject_request(
        self,
        approval_id: str,
        rejected_by: str,
        rejection_reason: str
    ) -> Dict[str, Any]:
        """
        Reject a pending approval request.

        Args:
            approval_id: ID of the approval request
            rejected_by: User rejecting the request
            rejection_reason: Reason for rejection

        Returns:
            Dict with rejection result
        """
        try:
            approval = self.db.query(PendingApproval).filter(
                PendingApproval.id == approval_id
            ).first()

            if not approval:
                raise ValueError(f"Approval request '{approval_id}' not found")

            if approval.status != ApprovalStatus.PENDING:
                raise ValueError(f"Approval request is not pending (status: {approval.status.value})")

            # Update approval
            approval.status = ApprovalStatus.REJECTED
            approval.rejected_by = rejected_by
            approval.rejected_at = datetime.utcnow()
            approval.rejection_reason = rejection_reason

            # Create audit log
            audit_log = ApprovalAuditLog(
                approval_id=approval.id,
                action="REJECTED",
                performed_by=rejected_by,
                notes=rejection_reason,
                previous_status=ApprovalStatus.PENDING.value,
                new_status=ApprovalStatus.REJECTED.value
            )
            self.db.add(audit_log)

            self.db.commit()

            logger.info(f"✅ Rejected request: {approval_id} by {rejected_by}")

            return {
                "approval_id": approval_id,
                "status": "rejected",
                "rejected_by": rejected_by,
                "rejected_at": approval.rejected_at.isoformat(),
                "reason": rejection_reason
            }

        except Exception as e:
            self.db.rollback()
            logger.error(f"❌ Failed to reject request: {e}")
            raise

    async def execute_approved_action(self, approval_id: str) -> Dict[str, Any]:
        """
        Execute the action after approval.

        Args:
            approval_id: ID of the approved request

        Returns:
            Dict with execution result
        """
        try:
            approval = self.db.query(PendingApproval).filter(
                PendingApproval.id == approval_id
            ).first()

            if not approval:
                raise ValueError(f"Approval request '{approval_id}' not found")

            if approval.status != ApprovalStatus.APPROVED:
                raise ValueError(f"Approval request is not approved (status: {approval.status.value})")

            if approval.executed_at:
                raise ValueError(f"Action already executed at {approval.executed_at}")

            # Mark as executing
            approval.status = ApprovalStatus.EXECUTING
            self.db.commit()

            # Execute the action based on action_type
            # This is a placeholder - actual execution would be handled by the appropriate service
            logger.info(f"🚀 Executing approved action: {approval.action_type.value}")

            # Simulate execution (in real implementation, this would call the appropriate service)
            execution_result = {
                "success": True,
                "action_type": approval.action_type.value,
                "payload": approval.action_payload,
                "message": "Action executed successfully (placeholder)"
            }

            # Update approval with execution result
            approval.status = ApprovalStatus.EXECUTED
            approval.executed_at = datetime.utcnow()
            approval.execution_result = execution_result

            # Create audit log
            audit_log = ApprovalAuditLog(
                approval_id=approval.id,
                action="EXECUTED",
                performed_by=approval.approved_by,
                notes="Action executed successfully",
                previous_status=ApprovalStatus.EXECUTING.value,
                new_status=ApprovalStatus.EXECUTED.value,
                metadata=execution_result
            )
            self.db.add(audit_log)

            self.db.commit()

            logger.info(f"✅ Executed approved action: {approval_id}")

            return execution_result

        except Exception as e:
            self.db.rollback()
            logger.error(f"❌ Failed to execute approved action: {e}")

            # Mark as failed
            if approval:
                approval.status = ApprovalStatus.FAILED
                approval.execution_result = {"error": str(e)}
                self.db.commit()

            raise

    async def get_pending_approvals(
        self,
        user_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        action_type: Optional[ActionType] = None,
        risk_level: Optional[RiskLevel] = None,
        limit: int = 50
    ) -> List[PendingApproval]:
        """
        Retrieve pending approval requests with optional filters.

        Args:
            user_id: Filter by user who requested
            agent_id: Filter by agent ID
            action_type: Filter by action type
            risk_level: Filter by risk level
            limit: Maximum number of results

        Returns:
            List of pending approvals
        """
        try:
            query = self.db.query(PendingApproval).filter(
                PendingApproval.status == ApprovalStatus.PENDING
            )

            if user_id:
                query = query.filter(PendingApproval.requested_by == user_id)

            if agent_id:
                query = query.filter(PendingApproval.agent_id == agent_id)

            if action_type:
                query = query.filter(PendingApproval.action_type == action_type)

            if risk_level:
                query = query.filter(PendingApproval.risk_level == risk_level)

            approvals = query.order_by(
                PendingApproval.created_at.desc()
            ).limit(limit).all()

            logger.info(f"✅ Retrieved {len(approvals)} pending approvals")
            return approvals

        except Exception as e:
            logger.error(f"❌ Failed to retrieve pending approvals: {e}")
            raise

    async def get_approval_by_id(self, approval_id: str) -> Optional[PendingApproval]:
        """Get an approval request by ID."""
        return self.db.query(PendingApproval).filter(
            PendingApproval.id == approval_id
        ).first()

    async def get_approval_history(
        self,
        approval_id: str
    ) -> List[ApprovalAuditLog]:
        """Get audit history for an approval request."""
        return self.db.query(ApprovalAuditLog).filter(
            ApprovalAuditLog.approval_id == approval_id
        ).order_by(ApprovalAuditLog.timestamp.asc()).all()

    def _evaluate_conditions(
        self,
        conditions: Dict[str, Any],
        context: Dict[str, Any]
    ) -> bool:
        """
        Evaluate policy conditions against context.

        Simple condition evaluation - can be extended for complex logic.
        """
        for key, expected_value in conditions.items():
            if key not in context:
                return False
            if context[key] != expected_value:
                return False
        return True


    # ========================================================================
    # Phase 5: Interactive HITL Consultation
    # ========================================================================

    async def start_consultation(
        self,
        approval_id: str,
        operator_id: str
    ) -> Dict[str, Any]:
        """
        Start an interactive consultation session for a pending approval.
        Opens a dialogue channel between operator and paused agent.

        Args:
            approval_id: ID of the pending approval
            operator_id: ID of the human operator starting consultation

        Returns:
            Dictionary with consultation session details
        """
        try:
            # Get approval
            approval = self.db.query(PendingApproval).filter(
                PendingApproval.approval_id == approval_id
            ).first()

            if not approval:
                raise ValueError(f"Approval not found: {approval_id}")

            if approval.status != ApprovalStatus.PENDING:
                raise ValueError(f"Approval {approval_id} is not pending (status: {approval.status})")

            # Start consultation
            approval.consultation_active = True
            approval.consultation_started_at = datetime.utcnow()

            self.db.commit()

            # Log event
            await self._log_approval_event(
                approval_id=str(approval.id),
                event_type="consultation_started",
                event_description=f"Consultation started by operator {operator_id}",
                actor_id=operator_id
            )

            logger.info(f"✅ Started consultation for approval {approval_id}")

            return {
                "approval_id": approval_id,
                "consultation_active": True,
                "started_at": approval.consultation_started_at.isoformat(),
                "operator_id": operator_id
            }

        except Exception as e:
            self.db.rollback()
            logger.error(f"❌ Failed to start consultation: {e}")
            raise

    async def send_consultation_message(
        self,
        approval_id: str,
        sender_id: str,
        sender_type: str,  # "human" or "agent"
        message: str
    ) -> Dict[str, Any]:
        """
        Send a message in the consultation channel.

        Args:
            approval_id: ID of the pending approval
            sender_id: ID of the sender (human or agent)
            sender_type: Type of sender ("human" or "agent")
            message: The message content

        Returns:
            Dictionary with message details
        """
        try:
            from app.models.hitl_approval import ConsultationMessage
            import uuid

            # Get approval
            approval = self.db.query(PendingApproval).filter(
                PendingApproval.approval_id == approval_id
            ).first()

            if not approval:
                raise ValueError(f"Approval not found: {approval_id}")

            if not approval.consultation_active:
                raise ValueError(f"Consultation not active for approval {approval_id}")

            # Create message
            consultation_message = ConsultationMessage(
                approval_id=approval.id,
                sender_id=sender_id,
                sender_type=sender_type,
                message=message,
                metadata={"timestamp": datetime.utcnow().isoformat()}
            )

            self.db.add(consultation_message)
            self.db.commit()
            self.db.refresh(consultation_message)

            logger.info(f"✅ Added consultation message from {sender_type} {sender_id} to {approval_id}")

            return {
                "message_id": str(consultation_message.id),
                "approval_id": approval_id,
                "sender_id": sender_id,
                "sender_type": sender_type,
                "message": message,
                "timestamp": consultation_message.timestamp.isoformat()
            }

        except Exception as e:
            self.db.rollback()
            logger.error(f"❌ Failed to send consultation message: {e}")
            raise

    async def get_consultation_history(
        self,
        approval_id: str
    ) -> List[Dict[str, Any]]:
        """
        Retrieve the full consultation conversation history.

        Args:
            approval_id: ID of the pending approval

        Returns:
            List of messages in chronological order
        """
        try:
            from app.models.hitl_approval import ConsultationMessage

            # Get approval
            approval = self.db.query(PendingApproval).filter(
                PendingApproval.approval_id == approval_id
            ).first()

            if not approval:
                raise ValueError(f"Approval not found: {approval_id}")

            # Get all messages
            messages = self.db.query(ConsultationMessage).filter(
                ConsultationMessage.approval_id == approval.id
            ).order_by(ConsultationMessage.timestamp).all()

            conversation = [
                {
                    "message_id": str(msg.id),
                    "sender_id": msg.sender_id,
                    "sender_type": msg.sender_type,
                    "message": msg.message,
                    "timestamp": msg.timestamp.isoformat(),
                    "metadata": msg.metadata
                }
                for msg in messages
            ]

            logger.info(f"✅ Retrieved {len(conversation)} consultation messages for {approval_id}")

            return conversation

        except Exception as e:
            logger.error(f"❌ Failed to get consultation history: {e}")
            raise

    async def end_consultation(
        self,
        approval_id: str,
        outcome: str,  # "approved", "rejected", "modified"
        final_notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        End the consultation session and finalize the approval decision.
        The existing approve/reject methods will call this internally.

        Args:
            approval_id: ID of the pending approval
            outcome: Final outcome ("approved", "rejected", "modified")
            final_notes: Optional final notes from the consultation

        Returns:
            Dictionary with consultation end details
        """
        try:
            # Get approval
            approval = self.db.query(PendingApproval).filter(
                PendingApproval.approval_id == approval_id
            ).first()

            if not approval:
                raise ValueError(f"Approval not found: {approval_id}")

            if not approval.consultation_active:
                raise ValueError(f"Consultation not active for approval {approval_id}")

            # End consultation
            approval.consultation_active = False
            approval.consultation_ended_at = datetime.utcnow()

            if final_notes:
                approval.reviewer_notes = (approval.reviewer_notes or "") + f"\n\nConsultation notes: {final_notes}"

            self.db.commit()

            # Log event
            await self._log_approval_event(
                approval_id=str(approval.id),
                event_type="consultation_ended",
                event_description=f"Consultation ended with outcome: {outcome}",
                actor_id=None,
                event_data={"outcome": outcome, "final_notes": final_notes}
            )

            logger.info(f"✅ Ended consultation for approval {approval_id} with outcome: {outcome}")

            return {
                "approval_id": approval_id,
                "consultation_active": False,
                "ended_at": approval.consultation_ended_at.isoformat(),
                "outcome": outcome,
                "duration_seconds": (approval.consultation_ended_at - approval.consultation_started_at).total_seconds() if approval.consultation_started_at else None
            }

        except Exception as e:
            self.db.rollback()
            logger.error(f"❌ Failed to end consultation: {e}")
            raise


