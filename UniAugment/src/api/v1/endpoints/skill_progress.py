"""
Skill Progress Endpoints - Phase 2

REST API endpoints for tracking agent progress through skill trees.
"""

from fastapi import APIRouter, HTTPException, Depends, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
import logging

from app.database.database import get_db
from app.models.skill_progress import (
    AgentSkillProgress,
    AgentSkillProgressCreate,
    AgentSkillProgressUpdate,
    AgentSkillProgressResponse,
    GainExperienceResponse,
    UnlockSkillResponse,
)
from app.services.skill_progress_service import SkillProgressService

logger = logging.getLogger(__name__)
router = APIRouter()


# ============================================================================
# Request Models
# ============================================================================

class GainExperienceRequest(BaseModel):
    """Request model for gaining experience."""
    experience_amount: int
    reason: Optional[str] = None


class UnlockSkillRequest(BaseModel):
    """Request model for unlocking a skill."""
    force: bool = False


# ============================================================================
# Skill Progress CRUD Endpoints
# ============================================================================

@router.post("/agents/{agent_id}/skills/{skill_node_id}/progress", response_model=AgentSkillProgressResponse, tags=["Skill Progress"])
async def create_skill_progress(
    agent_id: str,
    skill_node_id: str,
    progress: AgentSkillProgressCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new skill progress record for an agent.
    
    **Parameters:**
    - `agent_id`: The ID of the agent
    - `skill_node_id`: The ID of the skill node
    - `progress`: Skill progress configuration
    
    **Returns:** Created skill progress
    """
    try:
        result = SkillProgressService.create_skill_progress(db, agent_id, progress)
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error creating skill progress: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create skill progress: {str(e)}"
        )


@router.get("/agents/{agent_id}/skills/{skill_node_id}/progress", response_model=AgentSkillProgressResponse, tags=["Skill Progress"])
async def get_skill_progress(
    agent_id: str,
    skill_node_id: str,
    db: Session = Depends(get_db)
):
    """
    Get skill progress for an agent and skill.
    
    **Parameters:**
    - `agent_id`: The ID of the agent
    - `skill_node_id`: The ID of the skill node
    
    **Returns:** Skill progress or 404 if not found
    """
    progress = SkillProgressService.get_skill_progress(db, agent_id, skill_node_id)
    if not progress:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Skill progress not found for agent {agent_id} and skill {skill_node_id}"
        )
    return progress


@router.get("/agents/{agent_id}/skills/progress", response_model=List[AgentSkillProgressResponse], tags=["Skill Progress"])
async def get_all_agent_progress(
    agent_id: str,
    db: Session = Depends(get_db)
):
    """
    Get all skill progress for an agent.
    
    **Parameters:**
    - `agent_id`: The ID of the agent
    
    **Returns:** List of skill progress records
    """
    progress_list = SkillProgressService.get_all_agent_progress(db, agent_id)
    return progress_list


@router.delete("/agents/{agent_id}/skills/{skill_node_id}/progress", status_code=status.HTTP_204_NO_CONTENT, tags=["Skill Progress"])
async def delete_skill_progress(
    agent_id: str,
    skill_node_id: str,
    db: Session = Depends(get_db)
):
    """
    Delete skill progress for an agent.
    
    **Parameters:**
    - `agent_id`: The ID of the agent
    - `skill_node_id`: The ID of the skill node
    
    **Returns:** 204 No Content on success, 404 if not found
    """
    success = SkillProgressService.delete_skill_progress(db, agent_id, skill_node_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Skill progress not found for agent {agent_id} and skill {skill_node_id}"
        )


# ============================================================================
# Skill Progress Actions
# ============================================================================

@router.post("/agents/{agent_id}/skills/{skill_node_id}/gain-experience", response_model=GainExperienceResponse, tags=["Skill Progress"])
async def gain_experience(
    agent_id: str,
    skill_node_id: str,
    request: GainExperienceRequest,
    db: Session = Depends(get_db)
):
    """
    Add experience to a skill and handle leveling up.
    
    **Parameters:**
    - `agent_id`: The ID of the agent
    - `skill_node_id`: The ID of the skill node
    - `request`: Experience gain request with amount and optional reason
    
    **Returns:** Experience gain response with level up information
    """
    try:
        result = SkillProgressService.gain_experience(
            db, agent_id, skill_node_id, request.experience_amount, request.reason
        )
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error gaining experience: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to gain experience: {str(e)}"
        )


@router.post("/agents/{agent_id}/skills/{skill_node_id}/unlock", response_model=UnlockSkillResponse, tags=["Skill Progress"])
async def unlock_skill(
    agent_id: str,
    skill_node_id: str,
    request: UnlockSkillRequest = UnlockSkillRequest(),
    db: Session = Depends(get_db)
):
    """
    Unlock a skill for an agent (if prerequisites met).
    
    **Parameters:**
    - `agent_id`: The ID of the agent
    - `skill_node_id`: The ID of the skill node
    - `request`: Unlock request with optional force flag
    
    **Returns:** Unlock response with status and prerequisite information
    """
    try:
        result = SkillProgressService.unlock_skill(db, agent_id, skill_node_id, request.force)
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error unlocking skill: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to unlock skill: {str(e)}"
        )

