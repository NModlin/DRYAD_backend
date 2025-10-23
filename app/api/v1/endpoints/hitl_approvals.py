"""
HITL Approval API Endpoints

API endpoints for managing human-in-the-loop approval workflows.
"""

import logging
from typing import List, Optional
from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.database.database import SessionLocal
from app.services.hitl_approval_service import HITLApprovalService
from app.models.hitl_approval import (
    PendingApproval, ApprovalPolicy, ApprovalAuditLog,
    ApprovalStatus, RiskLevel, ActionType
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/approvals", tags=["HITL Approvals"])


# Dependency to get sync database session
def get_db():
    """Dependency to get sync database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ============================================================================
# APPROVAL REQUEST ENDPOINTS
# ============================================================================

@router.post("/request", status_code=status.HTTP_201_CREATED)
async def create_approval_request(
    request_data: dict,
    db: Session = Depends(get_db)
):
    """
    Create a new approval request for a high-risk operation.

    Request body:
    {
        "action_type": "data_deletion",
        "risk_level": "high",
        "agent_id": "agent_name",
        "execution_id": "exec_uuid",
        "action_description": "Delete 100 customer records",
        "action_payload": {...},
        "context": {...}
    }
    """
    try:
        service = HITLApprovalService(db)

        # Check if approval is required
        check_result = await service.check_approval_required(
            action_type=ActionType(request_data.get("action_type")),
            risk_level=RiskLevel(request_data.get("risk_level")),
            agent_id=request_data.get("agent_id"),
            context=request_data.get("context")
        )

        if not check_result["required"]:
            return {
                "approval_required": False,
                "message": "This action does not require approval"
            }

        # Create approval request
        approval = await service.create_approval_request(
            action_type=ActionType(request_data.get("action_type")),
            risk_level=RiskLevel(request_data.get("risk_level")),
            agent_id=request_data.get("agent_id"),
            execution_id=request_data.get("execution_id"),
            action_description=request_data.get("action_description"),
            action_payload=request_data.get("action_payload", {}),
            context=request_data.get("context", {})
        )

        logger.info(f"✅ Created approval request: {approval['id']}")

        return {
            "approval_required": True,
            "approval_id": approval["id"],
            "status": approval["status"],
            "message": "Approval request created successfully"
        }

    except Exception as e:
        logger.error(f"❌ Failed to create approval request: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create approval request: {str(e)}"
        )


@router.get("/pending")
async def get_pending_approvals(
    agent_id: Optional[str] = Query(None, description="Filter by agent ID"),
    risk_level: Optional[str] = Query(None, description="Filter by risk level"),
    action_type: Optional[str] = Query(None, description="Filter by action type"),
    limit: int = Query(50, description="Maximum number of records"),
    db: Session = Depends(get_db)
):
    """
    Get all pending approval requests with optional filters.
    """
    try:
        service = HITLApprovalService(db)

        approvals = await service.get_pending_approvals(
            agent_id=agent_id,
            risk_level=RiskLevel(risk_level) if risk_level else None,
            action_type=ActionType(action_type) if action_type else None,
            limit=limit
        )

        return {
            "pending_approvals": approvals,
            "total": len(approvals)
        }

    except Exception as e:
        logger.error(f"❌ Failed to get pending approvals: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get pending approvals: {str(e)}"
        )


@router.get("/{approval_id}")
async def get_approval(
    approval_id: str,
    db: Session = Depends(get_db)
):
    """
    Get detailed information about a specific approval request.
    """
    try:
        service = HITLApprovalService(db)

        approval = await service.get_approval_by_id(approval_id)

        if not approval:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Approval not found: {approval_id}"
            )

        return approval

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to get approval: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get approval: {str(e)}"
        )


# ============================================================================
# APPROVAL ACTION ENDPOINTS
# ============================================================================

@router.post("/{approval_id}/approve")
async def approve_request(
    approval_id: str,
    approval_data: dict,
    db: Session = Depends(get_db)
):
    """
    Approve a pending approval request.

    Request body:
    {
        "approver_id": "admin_user",
        "notes": "Approved after verification",
        "execute_immediately": true
    }
    """
    try:
        service = HITLApprovalService(db)

        result = await service.approve_request(
            approval_id=approval_id,
            approver_id=approval_data.get("approver_id"),
            notes=approval_data.get("notes")
        )

        # Execute if requested
        if approval_data.get("execute_immediately", False):
            execution_result = await service.execute_approved_action(approval_id)
            result["execution"] = execution_result

        logger.info(f"✅ Approved request: {approval_id}")

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to approve request: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to approve request: {str(e)}"
        )


@router.post("/{approval_id}/reject")
async def reject_request(
    approval_id: str,
    rejection_data: dict,
    db: Session = Depends(get_db)
):
    """
    Reject a pending approval request.

    Request body:
    {
        "approver_id": "admin_user",
        "reason": "Insufficient justification for data deletion"
    }
    """
    try:
        service = HITLApprovalService(db)

        result = await service.reject_request(
            approval_id=approval_id,
            approver_id=rejection_data.get("approver_id"),
            reason=rejection_data.get("reason")
        )

        logger.info(f"✅ Rejected request: {approval_id}")

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to reject request: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reject request: {str(e)}"
        )


# ============================================================================
# AUDIT AND HISTORY ENDPOINTS
# ============================================================================

@router.get("/{approval_id}/history")
async def get_approval_history(
    approval_id: str,
    db: Session = Depends(get_db)
):
    """
    Get the complete audit history for an approval request.
    """
    try:
        service = HITLApprovalService(db)

        history = await service.get_approval_history(approval_id)

        return {
            "approval_id": approval_id,
            "history": history,
            "total_events": len(history)
        }

    except Exception as e:
        logger.error(f"❌ Failed to get approval history: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get approval history: {str(e)}"
        )


# ============================================================================
# POLICY MANAGEMENT ENDPOINTS
# ============================================================================

@router.get("/policies/list")
async def list_approval_policies(
    enabled: Optional[bool] = Query(None, description="Filter by enabled status"),
    db: Session = Depends(get_db)
):
    """
    List all approval policies.
    """
    try:
        query = db.query(ApprovalPolicy)

        if enabled is not None:
            query = query.filter(ApprovalPolicy.enabled == enabled)

        policies = query.all()

        return {
            "policies": [
                {
                    "policy_id": str(policy.policy_id),
                    "name": policy.name,
                    "description": policy.description,
                    "min_risk_level": policy.min_risk_level.value,
                    "action_types": policy.action_types,
                    "enabled": policy.enabled,
                    "created_at": policy.created_at.isoformat() if policy.created_at else None
                }
                for policy in policies
            ],
            "total": len(policies)
        }

    except Exception as e:
        logger.error(f"❌ Failed to list policies: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list policies: {str(e)}"
        )


@router.post("/policies", status_code=status.HTTP_201_CREATED)
async def create_approval_policy(
    policy_data: dict,
    db: Session = Depends(get_db)
):
    """
    Create a new approval policy.

    Request body:
    {
        "name": "High Risk Data Operations",
        "description": "Require approval for high-risk data operations",
        "min_risk_level": "high",
        "action_types": ["data_deletion", "data_modification"],
        "conditions": {...},
        "excluded_agents": []
    }
    """
    try:
        policy = ApprovalPolicy(
            name=policy_data.get("name"),
            description=policy_data.get("description"),
            min_risk_level=RiskLevel(policy_data.get("min_risk_level")),
            action_types=policy_data.get("action_types", []),
            conditions=policy_data.get("conditions", {}),
            excluded_agents=policy_data.get("excluded_agents", []),
            enabled=policy_data.get("enabled", True)
        )

        db.add(policy)
        db.commit()
        db.refresh(policy)

        logger.info(f"✅ Created approval policy: {policy.name}")

        return {
            "policy_id": str(policy.policy_id),
            "name": policy.name,
            "message": "Policy created successfully"
        }

    except Exception as e:
        db.rollback()
        logger.error(f"❌ Failed to create policy: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create policy: {str(e)}"
        )



# ============================================================================
# PHASE 5: INTERACTIVE CONSULTATION ENDPOINTS
# ============================================================================

@router.post("/{approval_id}/consultation/start")
async def start_consultation(
    approval_id: str,
    consultation_data: dict,
    db: Session = Depends(get_db)
):
    """
    Start an interactive consultation session for a pending approval.

    Request body:
    {
        "operator_id": "user_123"
    }
    """
    try:
        service = HITLApprovalService(db)

        result = await service.start_consultation(
            approval_id=approval_id,
            operator_id=consultation_data["operator_id"]
        )

        return result

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"❌ Failed to start consultation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start consultation: {str(e)}"
        )


@router.post("/{approval_id}/consultation/message")
async def send_consultation_message(
    approval_id: str,
    message_data: dict,
    db: Session = Depends(get_db)
):
    """
    Send a message in the consultation channel.

    Request body:
    {
        "sender_id": "user_123",
        "sender_type": "human",
        "message": "Can you clarify the impact?"
    }
    """
    try:
        service = HITLApprovalService(db)

        result = await service.send_consultation_message(
            approval_id=approval_id,
            sender_id=message_data["sender_id"],
            sender_type=message_data["sender_type"],
            message=message_data["message"]
        )

        return result

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"❌ Failed to send consultation message: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send consultation message: {str(e)}"
        )


@router.get("/{approval_id}/consultation/history")
async def get_consultation_history(
    approval_id: str,
    db: Session = Depends(get_db)
):
    """Retrieve the full consultation conversation history."""
    try:
        service = HITLApprovalService(db)
        conversation = await service.get_consultation_history(approval_id)

        return {
            "approval_id": approval_id,
            "messages": conversation,
            "total": len(conversation)
        }

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"❌ Failed to get consultation history: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get consultation history: {str(e)}"
        )


@router.post("/{approval_id}/consultation/end")
async def end_consultation(
    approval_id: str,
    end_data: dict,
    db: Session = Depends(get_db)
):
    """
    End the consultation session and finalize the approval decision.

    Request body:
    {
        "outcome": "approved",
        "final_notes": "Approved after clarification"
    }
    """
    try:
        service = HITLApprovalService(db)

        result = await service.end_consultation(
            approval_id=approval_id,
            outcome=end_data["outcome"],
            final_notes=end_data.get("final_notes")
        )

        return result

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"❌ Failed to end consultation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to end consultation: {str(e)}"
        )


# ============================================================================
# CLOUD PROXY TEST ENDPOINT
# ============================================================================

@router.post("/test-cloud-proxy")
async def test_cloud_proxy():
    """
    Test endpoint for cloud approval proxy integration.

    Sends a test approval request to the cloud proxy to verify
    end-to-end functionality including Pushover notifications.
    """
    import os
    import httpx
    import uuid
    from datetime import datetime

    # Check if cloud proxy is enabled
    if not os.getenv("CLOUD_PROXY_ENABLED", "false").lower() == "true":
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Cloud proxy is not enabled. Set CLOUD_PROXY_ENABLED=true in .env"
        )

    cloud_proxy_url = os.getenv("CLOUD_PROXY_URL")
    cloud_proxy_secret = os.getenv("CLOUD_PROXY_SECRET")

    if not cloud_proxy_url or not cloud_proxy_secret:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Cloud proxy configuration missing. Check CLOUD_PROXY_URL and CLOUD_PROXY_SECRET in .env"
        )

    try:
        # Create test approval request
        test_approval = {
            "approval_id": str(uuid.uuid4()),
            "action_type": "Test Cloud Proxy",
            "action_description": "Testing end-to-end cloud approval proxy functionality",
            "risk_level": "medium",
            "requested_at": datetime.now().isoformat(),
            "callback_url": f"http://localhost:8000/api/v1/approvals/cloud-callback",
            "secret": cloud_proxy_secret
        }

        # Send to cloud proxy
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{cloud_proxy_url}/api/approval-request",
                json=test_approval
            )

            if response.status_code == 200:
                result = response.json()
                return {
                    "status": "success",
                    "message": "Test approval request sent to cloud proxy",
                    "approval_id": test_approval["approval_id"],
                    "cloud_response": result,
                    "instructions": [
                        "1. Check your phone for a Pushover notification",
                        "2. Click the notification to open the approval interface",
                        "3. Approve or reject the test request",
                        "4. The decision will be sent back to this local DRYAD instance"
                    ]
                }
            else:
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail=f"Cloud proxy returned status {response.status_code}: {response.text}"
                )

    except httpx.TimeoutException:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="Timeout connecting to cloud proxy. Check your internet connection and cloud proxy URL."
        )
    except Exception as e:
        logger.error(f"❌ Cloud proxy test failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Cloud proxy test failed: {str(e)}"
        )


@router.post("/cloud-callback")
async def cloud_callback(callback_data: dict):
    """
    Webhook endpoint for receiving approval decisions from cloud proxy.

    This endpoint receives the approval decision from the cloud proxy
    after the user approves/rejects via the mobile interface.
    """
    import os

    # Validate secret
    cloud_proxy_secret = os.getenv("CLOUD_PROXY_SECRET")
    if callback_data.get("secret") != cloud_proxy_secret:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid secret"
        )

    logger.info(f"📱 Received cloud approval decision: {callback_data}")

    return {
        "status": "received",
        "approval_id": callback_data.get("approval_id"),
        "decision": callback_data.get("decision"),
        "notes": callback_data.get("notes"),
        "message": f"Cloud approval decision '{callback_data.get('decision')}' received successfully"
    }

