"""
Guardrail API Endpoints

API endpoints for managing runtime guardrails and monitoring agent behavior.
"""

import logging
from typing import List, Optional
from datetime import datetime, timedelta
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.database.database import SessionLocal
from app.services.guardrail_service import GuardrailService
from app.models.execution_guardrails import (
    ExecutionGuardrail, GuardrailConfiguration, GuardrailMetrics,
    GuardrailType, GuardrailAction, SeverityLevel
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/guardrails", tags=["Guardrails"])


# Dependency to get sync database session
def get_db():
    """Dependency to get sync database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ============================================================================
# CONFIGURATION ENDPOINTS
# ============================================================================

@router.get("/configurations")
async def list_configurations(
    guardrail_type: Optional[str] = Query(None, description="Filter by guardrail type"),
    enabled: Optional[bool] = Query(None, description="Filter by enabled status"),
    db: Session = Depends(get_db)
):
    """
    List all guardrail configurations.
    """
    try:
        query = db.query(GuardrailConfiguration)
        
        if guardrail_type:
            query = query.filter(GuardrailConfiguration.guardrail_type == GuardrailType(guardrail_type))
        
        if enabled is not None:
            query = query.filter(GuardrailConfiguration.enabled == enabled)
        
        configs = query.all()
        
        return {
            "configurations": [
                {
                    "id": str(config.id),
                    "guardrail_type": config.guardrail_type.value,
                    "name": config.name,
                    "description": config.description,
                    "action": config.action.value,
                    "threshold": config.threshold,
                    "enabled": config.enabled,
                    "created_at": config.created_at.isoformat() if config.created_at else None
                }
                for config in configs
            ],
            "total": len(configs)
        }
    
    except Exception as e:
        logger.error(f"❌ Failed to list configurations: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list configurations: {str(e)}"
        )


@router.get("/configurations/{config_id}")
async def get_configuration(
    config_id: str,
    db: Session = Depends(get_db)
):
    """
    Get detailed information about a specific guardrail configuration.
    """
    try:
        config = db.query(GuardrailConfiguration).filter(
            GuardrailConfiguration.id == config_id
        ).first()
        
        if not config:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Configuration not found: {config_id}"
            )
        
        return {
            "id": str(config.id),
            "guardrail_type": config.guardrail_type.value,
            "name": config.name,
            "description": config.description,
            "action": config.action.value,
            "threshold": config.threshold,
            "parameters": config.parameters,
            "enabled": config.enabled,
            "created_at": config.created_at.isoformat() if config.created_at else None,
            "updated_at": config.updated_at.isoformat() if config.updated_at else None
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to get configuration: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get configuration: {str(e)}"
        )


@router.post("/configurations", status_code=status.HTTP_201_CREATED)
async def create_configuration(
    config_data: dict,
    db: Session = Depends(get_db)
):
    """
    Create a new guardrail configuration.
    
    Request body:
    {
        "guardrail_type": "content_filter",
        "name": "PII Detection",
        "description": "Detect and redact PII in agent outputs",
        "action": "modify",
        "threshold": 0.8,
        "parameters": {...},
        "enabled": true
    }
    """
    try:
        config = GuardrailConfiguration(
            guardrail_type=GuardrailType(config_data.get("guardrail_type")),
            name=config_data.get("name"),
            description=config_data.get("description"),
            action=GuardrailAction(config_data.get("action")),
            threshold=config_data.get("threshold"),
            parameters=config_data.get("parameters", {}),
            enabled=config_data.get("enabled", True)
        )
        
        db.add(config)
        db.commit()
        db.refresh(config)
        
        logger.info(f"✅ Created guardrail configuration: {config.name}")
        
        return {
            "id": str(config.id),
            "guardrail_type": config.guardrail_type.value,
            "name": config.name,
            "message": "Configuration created successfully"
        }
    
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Failed to create configuration: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create configuration: {str(e)}"
        )


@router.put("/configurations/{config_id}")
async def update_configuration(
    config_id: str,
    config_data: dict,
    db: Session = Depends(get_db)
):
    """
    Update an existing guardrail configuration.
    """
    try:
        config = db.query(GuardrailConfiguration).filter(
            GuardrailConfiguration.id == config_id
        ).first()
        
        if not config:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Configuration not found: {config_id}"
            )
        
        # Update fields
        if "name" in config_data:
            config.name = config_data["name"]
        if "description" in config_data:
            config.description = config_data["description"]
        if "action" in config_data:
            config.action = GuardrailAction(config_data["action"])
        if "threshold" in config_data:
            config.threshold = config_data["threshold"]
        if "parameters" in config_data:
            config.parameters = config_data["parameters"]
        if "enabled" in config_data:
            config.enabled = config_data["enabled"]
        
        config.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(config)
        
        logger.info(f"✅ Updated guardrail configuration: {config.name}")
        
        return {
            "id": str(config.id),
            "name": config.name,
            "message": "Configuration updated successfully"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Failed to update configuration: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update configuration: {str(e)}"
        )


# ============================================================================
# VIOLATION TRACKING ENDPOINTS
# ============================================================================

@router.get("/violations")
async def list_violations(
    execution_id: Optional[str] = Query(None, description="Filter by execution ID"),
    agent_id: Optional[str] = Query(None, description="Filter by agent ID"),
    guardrail_type: Optional[str] = Query(None, description="Filter by guardrail type"),
    severity: Optional[str] = Query(None, description="Filter by severity"),
    start_date: Optional[str] = Query(None, description="Start date (ISO format)"),
    end_date: Optional[str] = Query(None, description="End date (ISO format)"),
    limit: int = Query(100, description="Maximum number of records"),
    db: Session = Depends(get_db)
):
    """
    List guardrail violations with optional filters.
    """
    try:
        service = GuardrailService(db)
        
        violations = await service.get_violation_history(
            execution_id=execution_id,
            agent_id=agent_id,
            guardrail_type=GuardrailType(guardrail_type) if guardrail_type else None,
            severity=SeverityLevel(severity) if severity else None,
            start_date=datetime.fromisoformat(start_date) if start_date else None,
            end_date=datetime.fromisoformat(end_date) if end_date else None,
            limit=limit
        )
        
        return {
            "violations": violations,
            "total": len(violations)
        }
    
    except Exception as e:
        logger.error(f"❌ Failed to list violations: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list violations: {str(e)}"
        )


@router.get("/violations/{violation_id}")
async def get_violation(
    violation_id: str,
    db: Session = Depends(get_db)
):
    """
    Get detailed information about a specific violation.
    """
    try:
        violation = db.query(ExecutionGuardrail).filter(
            ExecutionGuardrail.id == violation_id
        ).first()
        
        if not violation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Violation not found: {violation_id}"
            )
        
        return {
            "id": str(violation.id),
            "execution_id": violation.execution_id,
            "agent_id": violation.agent_id,
            "guardrail_type": violation.guardrail_type.value,
            "severity": violation.severity.value,
            "action_taken": violation.action_taken.value,
            "violation_details": violation.violation_details,
            "original_output": violation.original_output,
            "modified_output": violation.modified_output,
            "timestamp": violation.timestamp.isoformat() if violation.timestamp else None
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to get violation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get violation: {str(e)}"
        )


# ============================================================================
# METRICS ENDPOINTS
# ============================================================================

@router.get("/metrics")
async def get_metrics_summary(
    start_date: Optional[str] = Query(None, description="Start date (ISO format)"),
    end_date: Optional[str] = Query(None, description="End date (ISO format)"),
    guardrail_type: Optional[str] = Query(None, description="Filter by guardrail type"),
    db: Session = Depends(get_db)
):
    """
    Get aggregated metrics for guardrail performance.
    """
    try:
        service = GuardrailService(db)
        
        # Default to last 30 days if no dates provided
        if not start_date:
            start_date = (datetime.utcnow() - timedelta(days=30)).isoformat()
        if not end_date:
            end_date = datetime.utcnow().isoformat()
        
        metrics = await service.get_metrics_summary(
            start_date=datetime.fromisoformat(start_date),
            end_date=datetime.fromisoformat(end_date),
            guardrail_type=GuardrailType(guardrail_type) if guardrail_type else None
        )
        
        return metrics
    
    except Exception as e:
        logger.error(f"❌ Failed to get metrics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get metrics: {str(e)}"
        )

