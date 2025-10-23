"""
Specialization Endpoints - Phase 2

REST API endpoints for agent specialization management.
"""

from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session
from typing import List, Optional
import logging

from app.database.database import get_db
from app.models.specialization import (
    SpecializationProfile,
    SpecializationType,
    SpecializationProfileCreate,
    SpecializationProfileUpdate,
    SpecializationProfileResponse,
    SpecializationTypeInfo,
)
from app.services.specialization_service import SpecializationService

logger = logging.getLogger(__name__)
router = APIRouter()


# ============================================================================
# Specialization Profile Endpoints
# ============================================================================

@router.post("/agents/{agent_id}/specialization", response_model=SpecializationProfileResponse, tags=["Specializations"])
async def create_specialization_profile(
    agent_id: str,
    profile: SpecializationProfileCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new specialization profile for an agent.
    
    **Parameters:**
    - `agent_id`: The ID of the agent
    - `profile`: Specialization profile configuration
    
    **Returns:** Created specialization profile
    """
    try:
        result = SpecializationService.create_specialization_profile(db, agent_id, profile)
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error creating specialization profile: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create specialization profile: {str(e)}"
        )


@router.get("/agents/{agent_id}/specialization", response_model=SpecializationProfileResponse, tags=["Specializations"])
async def get_specialization_profile(
    agent_id: str,
    db: Session = Depends(get_db)
):
    """
    Get specialization profile for an agent.
    
    **Parameters:**
    - `agent_id`: The ID of the agent
    
    **Returns:** Specialization profile or 404 if not found
    """
    profile = SpecializationService.get_specialization_profile(db, agent_id)
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Specialization profile not found for agent {agent_id}"
        )
    return profile


@router.put("/agents/{agent_id}/specialization", response_model=SpecializationProfileResponse, tags=["Specializations"])
async def update_specialization_profile(
    agent_id: str,
    profile: SpecializationProfileUpdate,
    db: Session = Depends(get_db)
):
    """
    Update specialization profile for an agent.
    
    **Parameters:**
    - `agent_id`: The ID of the agent
    - `profile`: Updated specialization profile data
    
    **Returns:** Updated specialization profile
    """
    try:
        result = SpecializationService.update_specialization_profile(db, agent_id, profile)
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error updating specialization profile: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update specialization profile: {str(e)}"
        )


@router.delete("/agents/{agent_id}/specialization", status_code=status.HTTP_204_NO_CONTENT, tags=["Specializations"])
async def delete_specialization_profile(
    agent_id: str,
    db: Session = Depends(get_db)
):
    """
    Delete specialization profile for an agent.
    
    **Parameters:**
    - `agent_id`: The ID of the agent
    
    **Returns:** 204 No Content on success, 404 if not found
    """
    success = SpecializationService.delete_specialization_profile(db, agent_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Specialization profile not found for agent {agent_id}"
        )


# ============================================================================
# Specialization Actions
# ============================================================================

@router.post("/agents/{agent_id}/specialization/level-up", response_model=SpecializationProfileResponse, tags=["Specializations"])
async def level_up_specialization(
    agent_id: str,
    db: Session = Depends(get_db)
):
    """
    Increase agent's specialization level by 1 (max 10).
    
    **Parameters:**
    - `agent_id`: The ID of the agent
    
    **Returns:** Updated specialization profile
    """
    try:
        result = SpecializationService.level_up_specialization(db, agent_id)
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error leveling up specialization: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to level up specialization: {str(e)}"
        )


@router.post("/agents/{agent_id}/specialization/add-secondary", response_model=SpecializationProfileResponse, tags=["Specializations"])
async def add_secondary_specialization(
    agent_id: str,
    specialization: SpecializationType,
    db: Session = Depends(get_db)
):
    """
    Add a secondary specialization to an agent.
    
    **Parameters:**
    - `agent_id`: The ID of the agent
    - `specialization`: Specialization type to add
    
    **Returns:** Updated specialization profile
    """
    try:
        result = SpecializationService.add_secondary_specialization(db, agent_id, specialization)
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error adding secondary specialization: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to add secondary specialization: {str(e)}"
        )


# ============================================================================
# Specialization Type Information
# ============================================================================

@router.get("/specializations/types", response_model=List[SpecializationTypeInfo], tags=["Specializations"])
async def get_all_specialization_types():
    """
    Get information about all available specialization types.
    
    **Returns:** List of specialization type information
    """
    return SpecializationService.get_all_specialization_types()


@router.get("/specializations/types/{spec_type}", response_model=SpecializationTypeInfo, tags=["Specializations"])
async def get_specialization_type_info(spec_type: SpecializationType):
    """
    Get information about a specific specialization type.
    
    **Parameters:**
    - `spec_type`: Specialization type
    
    **Returns:** Specialization type information
    """
    return SpecializationService.get_specialization_type_info(spec_type)

