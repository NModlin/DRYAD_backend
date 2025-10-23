"""
Curriculum API Endpoints

Provides REST API endpoints for curriculum management including:
- CRUD operations for curriculum paths and levels
- Agent enrollment and progress tracking
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.models.curriculum import (
    CurriculumPath,
    CurriculumLevel,
    AgentCurriculumProgress,
    DifficultyLevel,
    CurriculumStatus,
    AgentProgressStatus,
    CurriculumPathCreate,
    CurriculumPathUpdate,
    CurriculumPathResponse,
    CurriculumLevelCreate,
    CurriculumLevelResponse,
    AgentProgressCreate,
    AgentProgressUpdate,
    AgentProgressResponse
)
from app.services.curriculum_service import CurriculumService

router = APIRouter(prefix="/curriculum", tags=["curriculum"])


# ==================== Curriculum Path Endpoints ====================

@router.post("/paths", response_model=CurriculumPathResponse, status_code=201)
def create_curriculum_path(
    path_data: CurriculumPathCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new curriculum path.
    
    - **university_id**: University ID (required)
    - **name**: Path name (required)
    - **difficulty_level**: Difficulty level (BEGINNER, INTERMEDIATE, ADVANCED, EXPERT, MASTER)
    - **estimated_duration_hours**: Estimated completion time in hours
    """
    try:
        curriculum_path = CurriculumService.create_curriculum_path(db, path_data)
        return curriculum_path
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/paths/{path_id}", response_model=CurriculumPathResponse)
def get_curriculum_path(
    path_id: str,
    db: Session = Depends(get_db)
):
    """
    Get a curriculum path by ID.
    
    - **path_id**: Curriculum path ID
    """
    curriculum_path = CurriculumService.get_curriculum_path(db, path_id)
    
    if not curriculum_path:
        raise HTTPException(status_code=404, detail="Curriculum path not found")
    
    return curriculum_path


@router.get("/paths", response_model=List[CurriculumPathResponse])
def list_curriculum_paths(
    university_id: str = Query(..., description="University ID"),
    difficulty: Optional[DifficultyLevel] = Query(None, description="Filter by difficulty level"),
    specialization: Optional[str] = Query(None, description="Filter by specialization"),
    status: Optional[CurriculumStatus] = Query(None, description="Filter by status"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    db: Session = Depends(get_db)
):
    """
    List curriculum paths for a university with optional filters.
    
    - **university_id**: University ID (required)
    - **difficulty**: Filter by difficulty level
    - **specialization**: Filter by specialization
    - **status**: Filter by status
    """
    curriculum_paths = CurriculumService.get_curriculum_paths_by_university(
        db, university_id, difficulty, specialization, status, skip, limit
    )
    
    return curriculum_paths


@router.put("/paths/{path_id}", response_model=CurriculumPathResponse)
def update_curriculum_path(
    path_id: str,
    update_data: CurriculumPathUpdate,
    db: Session = Depends(get_db)
):
    """
    Update a curriculum path.
    
    - **path_id**: Curriculum path ID
    - **update_data**: Fields to update
    """
    curriculum_path = CurriculumService.update_curriculum_path(db, path_id, update_data)
    
    if not curriculum_path:
        raise HTTPException(status_code=404, detail="Curriculum path not found")
    
    return curriculum_path


@router.delete("/paths/{path_id}", status_code=204)
def delete_curriculum_path(
    path_id: str,
    db: Session = Depends(get_db)
):
    """
    Delete (archive) a curriculum path.
    
    - **path_id**: Curriculum path ID
    """
    success = CurriculumService.delete_curriculum_path(db, path_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Curriculum path not found")
    
    return None


# ==================== Curriculum Level Endpoints ====================

@router.post("/levels", response_model=CurriculumLevelResponse, status_code=201)
def create_curriculum_level(
    level_data: CurriculumLevelCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new curriculum level.
    
    - **curriculum_path_id**: Curriculum path ID (required)
    - **level_number**: Level number (required)
    - **name**: Level name (required)
    - **objectives**: Learning objectives
    - **challenges**: Challenges and tasks
    """
    try:
        curriculum_level = CurriculumService.create_curriculum_level(db, level_data)
        return curriculum_level
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/levels/{level_id}", response_model=CurriculumLevelResponse)
def get_curriculum_level(
    level_id: str,
    db: Session = Depends(get_db)
):
    """
    Get a curriculum level by ID.
    
    - **level_id**: Curriculum level ID
    """
    curriculum_level = CurriculumService.get_curriculum_level(db, level_id)
    
    if not curriculum_level:
        raise HTTPException(status_code=404, detail="Curriculum level not found")
    
    return curriculum_level


@router.get("/paths/{path_id}/levels", response_model=List[CurriculumLevelResponse])
def list_curriculum_levels(
    path_id: str,
    db: Session = Depends(get_db)
):
    """
    Get all levels for a curriculum path, ordered by level number.
    
    - **path_id**: Curriculum path ID
    """
    curriculum_levels = CurriculumService.get_levels_by_path(db, path_id)
    
    return curriculum_levels


@router.delete("/levels/{level_id}", status_code=204)
def delete_curriculum_level(
    level_id: str,
    db: Session = Depends(get_db)
):
    """
    Delete a curriculum level.
    
    - **level_id**: Curriculum level ID
    """
    success = CurriculumService.delete_curriculum_level(db, level_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Curriculum level not found")
    
    return None


# ==================== Agent Progress Endpoints ====================

@router.post("/enroll", response_model=AgentProgressResponse, status_code=201)
def enroll_agent(
    enrollment_data: AgentProgressCreate,
    db: Session = Depends(get_db)
):
    """
    Enroll an agent in a curriculum path.
    
    - **agent_id**: Agent ID (required)
    - **curriculum_path_id**: Curriculum path ID (required)
    """
    try:
        progress = CurriculumService.enroll_agent(db, enrollment_data)
        return progress
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/progress/{agent_id}/{path_id}", response_model=AgentProgressResponse)
def get_agent_progress(
    agent_id: str,
    path_id: str,
    db: Session = Depends(get_db)
):
    """
    Get agent's progress on a curriculum path.
    
    - **agent_id**: Agent ID
    - **path_id**: Curriculum path ID
    """
    progress = CurriculumService.get_agent_progress(db, agent_id, path_id)
    
    if not progress:
        raise HTTPException(status_code=404, detail="Progress record not found")
    
    return progress


@router.get("/progress/{agent_id}", response_model=List[AgentProgressResponse])
def get_agent_all_progress(
    agent_id: str,
    status: Optional[AgentProgressStatus] = Query(None, description="Filter by status"),
    db: Session = Depends(get_db)
):
    """
    Get all curriculum progress for an agent.
    
    - **agent_id**: Agent ID
    - **status**: Filter by status (NOT_STARTED, IN_PROGRESS, COMPLETED, FAILED, PAUSED)
    """
    progress_list = CurriculumService.get_agent_all_progress(db, agent_id, status)
    
    return progress_list


@router.post("/progress/{agent_id}/{path_id}/start", response_model=AgentProgressResponse)
def start_curriculum(
    agent_id: str,
    path_id: str,
    db: Session = Depends(get_db)
):
    """
    Mark curriculum as started for an agent.
    
    - **agent_id**: Agent ID
    - **path_id**: Curriculum path ID
    """
    progress = CurriculumService.start_curriculum(db, agent_id, path_id)
    
    if not progress:
        raise HTTPException(status_code=404, detail="Progress record not found")
    
    return progress


@router.post("/progress/{agent_id}/{path_id}/complete-level", response_model=AgentProgressResponse)
def complete_level(
    agent_id: str,
    path_id: str,
    level_number: int = Query(..., ge=1, description="Level number to complete"),
    score: float = Query(..., ge=0.0, le=1.0, description="Score achieved (0.0-1.0)"),
    db: Session = Depends(get_db)
):
    """
    Mark a level as completed and update progress.
    
    - **agent_id**: Agent ID
    - **path_id**: Curriculum path ID
    - **level_number**: Level number completed
    - **score**: Score achieved (0.0-1.0)
    """
    progress = CurriculumService.complete_level(db, agent_id, path_id, level_number, score)
    
    if not progress:
        raise HTTPException(status_code=404, detail="Progress record not found")
    
    return progress

