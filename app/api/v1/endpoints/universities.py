"""
University API Endpoints

Provides REST API endpoints for university management including:
- CRUD operations for universities
- Statistics retrieval
- Search and filtering
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.models.university import (
    University,
    UniversityCreate,
    UniversityUpdate,
    UniversityResponse,
    UniversityStatistics,
    UniversityListResponse,
    UniversityStatus
)
from app.services.university_service import UniversityService

router = APIRouter(prefix="/universities", tags=["universities"])


@router.post("/", response_model=UniversityResponse, status_code=201)
def create_university(
    university_data: UniversityCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new university instance.
    
    - **name**: University name (required)
    - **owner_user_id**: Owner user ID (required)
    - **settings**: University configuration settings
    - **max_agents**: Maximum number of agents (default: 100)
    - **max_concurrent_competitions**: Maximum concurrent competitions (default: 10)
    - **storage_quota_mb**: Storage quota in MB (default: 1024)
    """
    try:
        university = UniversityService.create_university(db, university_data)
        return university
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{university_id}", response_model=UniversityResponse)
def get_university(
    university_id: str,
    db: Session = Depends(get_db)
):
    """
    Get a university by ID.
    
    - **university_id**: University ID
    """
    university = UniversityService.get_university(db, university_id)
    
    if not university:
        raise HTTPException(status_code=404, detail="University not found")
    
    return university


@router.get("/", response_model=UniversityListResponse)
def list_universities(
    owner_user_id: Optional[str] = Query(None, description="Filter by owner user ID"),
    tenant_id: Optional[str] = Query(None, description="Filter by tenant ID"),
    status: Optional[UniversityStatus] = Query(None, description="Filter by status"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    db: Session = Depends(get_db)
):
    """
    List universities with optional filters.
    
    - **owner_user_id**: Filter by owner user ID
    - **tenant_id**: Filter by tenant ID
    - **status**: Filter by status (ACTIVE, PAUSED, ARCHIVED, MAINTENANCE)
    - **skip**: Number of records to skip (pagination)
    - **limit**: Maximum number of records to return
    """
    if owner_user_id:
        universities = UniversityService.get_universities_by_owner(
            db, owner_user_id, status, skip, limit
        )
    elif tenant_id:
        universities = UniversityService.get_universities_by_tenant(
            db, tenant_id, status, skip, limit
        )
    else:
        # If no filter, return empty list or require authentication
        universities = []
    
    total = len(universities)
    
    return UniversityListResponse(
        universities=universities,
        total=total,
        skip=skip,
        limit=limit
    )


@router.put("/{university_id}", response_model=UniversityResponse)
def update_university(
    university_id: str,
    update_data: UniversityUpdate,
    db: Session = Depends(get_db)
):
    """
    Update a university.
    
    - **university_id**: University ID
    - **update_data**: Fields to update
    """
    university = UniversityService.update_university(db, university_id, update_data)
    
    if not university:
        raise HTTPException(status_code=404, detail="University not found")
    
    return university


@router.delete("/{university_id}", status_code=204)
def delete_university(
    university_id: str,
    db: Session = Depends(get_db)
):
    """
    Delete (archive) a university.
    
    - **university_id**: University ID
    """
    success = UniversityService.delete_university(db, university_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="University not found")
    
    return None


@router.get("/{university_id}/statistics", response_model=UniversityStatistics)
def get_university_statistics(
    university_id: str,
    db: Session = Depends(get_db)
):
    """
    Get detailed statistics for a university.
    
    - **university_id**: University ID
    """
    university = UniversityService.get_university(db, university_id)
    
    if not university:
        raise HTTPException(status_code=404, detail="University not found")
    
    return UniversityStatistics(
        university_id=university.id,
        university_name=university.name,
        total_agents=university.total_agents,
        active_agents=university.active_agents,
        total_competitions=university.total_competitions,
        total_training_data_points=university.total_training_data_points,
        agent_utilization=university.active_agents / university.max_agents if university.max_agents > 0 else 0.0,
        storage_used_mb=0,  # TODO: Calculate actual storage usage
        storage_quota_mb=university.storage_quota_mb,
        created_at=university.created_at,
        last_activity_at=university.last_activity_at
    )


@router.post("/{university_id}/agents/increment", response_model=UniversityResponse)
def increment_agent_count(
    university_id: str,
    active: bool = Query(True, description="Whether the agent is active"),
    db: Session = Depends(get_db)
):
    """
    Increment agent count for a university.
    
    - **university_id**: University ID
    - **active**: Whether the agent is active
    """
    university = UniversityService.increment_agent_count(db, university_id, active)
    
    if not university:
        raise HTTPException(status_code=404, detail="University not found")
    
    return university


@router.post("/{university_id}/competitions/increment", response_model=UniversityResponse)
def increment_competition_count(
    university_id: str,
    db: Session = Depends(get_db)
):
    """
    Increment competition count for a university.
    
    - **university_id**: University ID
    """
    university = UniversityService.increment_competition_count(db, university_id)
    
    if not university:
        raise HTTPException(status_code=404, detail="University not found")
    
    return university


@router.get("/search/", response_model=UniversityListResponse)
def search_universities(
    query: Optional[str] = Query(None, description="Search query for name/description"),
    specialization: Optional[str] = Query(None, description="Filter by specialization"),
    status: Optional[UniversityStatus] = Query(None, description="Filter by status"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    db: Session = Depends(get_db)
):
    """
    Search universities with filters.
    
    - **query**: Search query for name/description
    - **specialization**: Filter by specialization
    - **status**: Filter by status
    - **skip**: Number of records to skip (pagination)
    - **limit**: Maximum number of records to return
    """
    universities = UniversityService.search_universities(
        db, query, specialization, status, False, skip, limit
    )
    
    total = len(universities)
    
    return UniversityListResponse(
        universities=universities,
        total=total,
        skip=skip,
        limit=limit
    )

