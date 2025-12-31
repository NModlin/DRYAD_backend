"""
Agent Creation Studio Enhancement Endpoints - Phase 1

REST API endpoints for visual and behavioral customization of agents.
"""

from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session
from typing import Optional
import logging

from app.database.database import get_db
from app.models.agent_enhancements import (
    VisualProfile,
    BehavioralProfile,
    VisualProfileSchema,
    BehavioralProfileSchema,
    EnhancedAgentProfileSchema,
)

logger = logging.getLogger(__name__)
router = APIRouter()


# ============================================================================
# Visual Customization Endpoints
# ============================================================================

@router.post("/agents/{agent_id}/visual", response_model=VisualProfileSchema, tags=["Agent Enhancements"])
async def create_or_update_visual_profile(
    agent_id: str,
    profile: VisualProfileSchema,
    db: Session = Depends(get_db)
):
    """
    Create or update visual customization profile for an agent.
    
    **Parameters:**
    - `agent_id`: The ID of the agent
    - `profile`: Visual profile configuration
    
    **Returns:** Updated visual profile
    """
    try:
        # Check if profile exists
        existing = db.query(VisualProfile).filter(VisualProfile.agent_id == agent_id).first()
        
        if existing:
            # Update existing profile
            for key, value in profile.dict().items():
                setattr(existing, key, value)
            db.commit()
            db.refresh(existing)
            return existing
        else:
            # Create new profile
            new_profile = VisualProfile(
                agent_id=agent_id,
                **profile.dict()
            )
            db.add(new_profile)
            db.commit()
            db.refresh(new_profile)
            return new_profile
    except Exception as e:
        logger.error(f"Error creating/updating visual profile: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create/update visual profile: {str(e)}"
        )


@router.get("/agents/{agent_id}/visual", response_model=VisualProfileSchema, tags=["Agent Enhancements"])
async def get_visual_profile(
    agent_id: str,
    db: Session = Depends(get_db)
):
    """
    Get visual customization profile for an agent.
    
    **Parameters:**
    - `agent_id`: The ID of the agent
    
    **Returns:** Visual profile or 404 if not found
    """
    profile = db.query(VisualProfile).filter(VisualProfile.agent_id == agent_id).first()
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Visual profile not found for agent {agent_id}"
        )
    return profile


@router.patch("/agents/{agent_id}/visual", response_model=VisualProfileSchema, tags=["Agent Enhancements"])
async def patch_visual_profile(
    agent_id: str,
    updates: dict,
    db: Session = Depends(get_db)
):
    """
    Partially update visual customization profile for an agent.
    
    **Parameters:**
    - `agent_id`: The ID of the agent
    - `updates`: Fields to update
    
    **Returns:** Updated visual profile
    """
    profile = db.query(VisualProfile).filter(VisualProfile.agent_id == agent_id).first()
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Visual profile not found for agent {agent_id}"
        )
    
    try:
        for key, value in updates.items():
            if hasattr(profile, key):
                setattr(profile, key, value)
        db.commit()
        db.refresh(profile)
        return profile
    except Exception as e:
        logger.error(f"Error patching visual profile: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to patch visual profile: {str(e)}"
        )


# ============================================================================
# Behavioral Customization Endpoints
# ============================================================================

@router.post("/agents/{agent_id}/behavior", response_model=BehavioralProfileSchema, tags=["Agent Enhancements"])
async def create_or_update_behavioral_profile(
    agent_id: str,
    profile: BehavioralProfileSchema,
    db: Session = Depends(get_db)
):
    """
    Create or update behavioral customization profile for an agent.
    
    **Parameters:**
    - `agent_id`: The ID of the agent
    - `profile`: Behavioral profile configuration
    
    **Returns:** Updated behavioral profile
    """
    try:
        # Check if profile exists
        existing = db.query(BehavioralProfile).filter(BehavioralProfile.agent_id == agent_id).first()
        
        if existing:
            # Update existing profile
            for key, value in profile.dict().items():
                setattr(existing, key, value)
            db.commit()
            db.refresh(existing)
            return existing
        else:
            # Create new profile
            new_profile = BehavioralProfile(
                agent_id=agent_id,
                **profile.dict()
            )
            db.add(new_profile)
            db.commit()
            db.refresh(new_profile)
            return new_profile
    except Exception as e:
        logger.error(f"Error creating/updating behavioral profile: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create/update behavioral profile: {str(e)}"
        )


@router.get("/agents/{agent_id}/behavior", response_model=BehavioralProfileSchema, tags=["Agent Enhancements"])
async def get_behavioral_profile(
    agent_id: str,
    db: Session = Depends(get_db)
):
    """
    Get behavioral customization profile for an agent.
    
    **Parameters:**
    - `agent_id`: The ID of the agent
    
    **Returns:** Behavioral profile or 404 if not found
    """
    profile = db.query(BehavioralProfile).filter(BehavioralProfile.agent_id == agent_id).first()
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Behavioral profile not found for agent {agent_id}"
        )
    return profile


@router.patch("/agents/{agent_id}/behavior", response_model=BehavioralProfileSchema, tags=["Agent Enhancements"])
async def patch_behavioral_profile(
    agent_id: str,
    updates: dict,
    db: Session = Depends(get_db)
):
    """
    Partially update behavioral customization profile for an agent.
    
    **Parameters:**
    - `agent_id`: The ID of the agent
    - `updates`: Fields to update
    
    **Returns:** Updated behavioral profile
    """
    profile = db.query(BehavioralProfile).filter(BehavioralProfile.agent_id == agent_id).first()
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Behavioral profile not found for agent {agent_id}"
        )
    
    try:
        for key, value in updates.items():
            if hasattr(profile, key):
                setattr(profile, key, value)
        db.commit()
        db.refresh(profile)
        return profile
    except Exception as e:
        logger.error(f"Error patching behavioral profile: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to patch behavioral profile: {str(e)}"
        )


# ============================================================================
# Combined Profile Endpoints
# ============================================================================

@router.get("/agents/{agent_id}/profile", response_model=EnhancedAgentProfileSchema, tags=["Agent Enhancements"])
async def get_enhanced_agent_profile(
    agent_id: str,
    db: Session = Depends(get_db)
):
    """
    Get complete enhanced profile (visual + behavioral) for an agent.
    
    **Parameters:**
    - `agent_id`: The ID of the agent
    
    **Returns:** Combined visual and behavioral profiles
    """
    visual = db.query(VisualProfile).filter(VisualProfile.agent_id == agent_id).first()
    behavioral = db.query(BehavioralProfile).filter(BehavioralProfile.agent_id == agent_id).first()
    
    if not visual or not behavioral:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Enhanced profile not found for agent {agent_id}"
        )
    
    return {
        "agent_id": agent_id,
        "visual_profile": visual,
        "behavioral_profile": behavioral,
        "created_at": visual.created_at,
        "updated_at": max(visual.updated_at, behavioral.updated_at)
    }

