"""
Progression Path Endpoints - Phase 2

REST API endpoints for managing progression paths through skill trees.
"""

from fastapi import APIRouter, HTTPException, Depends, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import logging

from app.database.database import get_db
from app.models.progression_path import (
    ProgressionPath,
    ProgressionPathCreate,
    ProgressionPathUpdate,
    ProgressionPathResponse,
    ProgressionPathWithDetails,
    AgentProgressionPathProgress,
)
from app.models.specialization import SpecializationType
from app.services.progression_path_service import ProgressionPathService

logger = logging.getLogger(__name__)
router = APIRouter()


# ============================================================================
# Progression Path CRUD Endpoints
# ============================================================================

@router.post("/progression-paths", response_model=ProgressionPathResponse, tags=["Progression Paths"])
async def create_progression_path(
    path: ProgressionPathCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new progression path.
    
    **Parameters:**
    - `path`: Progression path configuration
    
    **Returns:** Created progression path
    """
    try:
        result = ProgressionPathService.create_progression_path(db, path)
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error creating progression path: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create progression path: {str(e)}"
        )


@router.get("/progression-paths/{path_id}", response_model=ProgressionPathResponse, tags=["Progression Paths"])
async def get_progression_path(
    path_id: str,
    db: Session = Depends(get_db)
):
    """
    Get a progression path by ID.
    
    **Parameters:**
    - `path_id`: Progression path ID
    
    **Returns:** Progression path or 404 if not found
    """
    path = ProgressionPathService.get_progression_path(db, path_id)
    if not path:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Progression path not found: {path_id}"
        )
    return path


@router.get("/progression-paths", response_model=List[ProgressionPathResponse], tags=["Progression Paths"])
async def get_progression_paths_by_specialization(
    specialization: SpecializationType,
    public_only: bool = Query(False, description="Only return public paths"),
    db: Session = Depends(get_db)
):
    """
    Get all progression paths for a specialization.
    
    **Parameters:**
    - `specialization`: Specialization type
    - `public_only`: Only return public paths (default: false)
    
    **Returns:** List of progression paths
    """
    paths = ProgressionPathService.get_progression_paths_by_specialization(
        db, specialization, public_only
    )
    return paths


@router.get("/skill-trees/{tree_id}/progression-paths", response_model=List[ProgressionPathResponse], tags=["Progression Paths"])
async def get_progression_paths_by_tree(
    tree_id: str,
    db: Session = Depends(get_db)
):
    """
    Get all progression paths for a skill tree.
    
    **Parameters:**
    - `tree_id`: Skill tree ID
    
    **Returns:** List of progression paths
    """
    paths = ProgressionPathService.get_progression_paths_by_tree(db, tree_id)
    return paths


@router.put("/progression-paths/{path_id}", response_model=ProgressionPathResponse, tags=["Progression Paths"])
async def update_progression_path(
    path_id: str,
    path: ProgressionPathUpdate,
    db: Session = Depends(get_db)
):
    """
    Update a progression path.
    
    **Parameters:**
    - `path_id`: Progression path ID
    - `path`: Updated progression path data
    
    **Returns:** Updated progression path
    """
    try:
        result = ProgressionPathService.update_progression_path(db, path_id, path)
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error updating progression path: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update progression path: {str(e)}"
        )


@router.delete("/progression-paths/{path_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Progression Paths"])
async def delete_progression_path(
    path_id: str,
    db: Session = Depends(get_db)
):
    """
    Delete a progression path.
    
    **Parameters:**
    - `path_id`: Progression path ID
    
    **Returns:** 204 No Content on success, 404 if not found
    """
    success = ProgressionPathService.delete_progression_path(db, path_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Progression path not found: {path_id}"
        )


# ============================================================================
# Progression Path Details & Progress
# ============================================================================

@router.get("/progression-paths/{path_id}/details", response_model=ProgressionPathWithDetails, tags=["Progression Paths"])
async def get_path_with_details(
    path_id: str,
    db: Session = Depends(get_db)
):
    """
    Get a progression path with full skill details.
    
    **Parameters:**
    - `path_id`: Progression path ID
    
    **Returns:** Progression path with detailed skill information
    """
    try:
        result = ProgressionPathService.get_path_with_details(db, path_id)
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error getting path details: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get path details: {str(e)}"
        )


@router.get("/agents/{agent_id}/progression-paths/{path_id}/progress", response_model=AgentProgressionPathProgress, tags=["Progression Paths"])
async def get_agent_progress_on_path(
    agent_id: str,
    path_id: str,
    db: Session = Depends(get_db)
):
    """
    Get an agent's progress through a progression path.
    
    **Parameters:**
    - `agent_id`: The ID of the agent
    - `path_id`: Progression path ID
    
    **Returns:** Detailed progress information for the agent on this path
    """
    try:
        result = ProgressionPathService.get_agent_progress_on_path(db, agent_id, path_id)
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error getting agent progress on path: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get agent progress on path: {str(e)}"
        )

