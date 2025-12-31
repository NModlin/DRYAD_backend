"""
University management endpoints for Uni0
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel

from app.university_system.database.database import get_db
from app.university_system.database.models_university import University, UniversityAgent, CurriculumPath, Competition

router = APIRouter()

class UniversityCreate(BaseModel):
    name: str
    description: Optional[str] = None
    owner_user_id: str
    max_agents: int = 100
    settings: Optional[dict] = None

class UniversityUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    max_agents: Optional[int] = None
    settings: Optional[dict] = None
    status: Optional[str] = None

class UniversityResponse(BaseModel):
    id: str
    name: str
    description: Optional[str]
    max_agents: int
    current_agents: int
    status: str
    settings: dict
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True

@router.get("/")
async def list_universities(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """List all universities"""
    universities = db.query(University).offset(skip).limit(limit).all()
    
    # Calculate current agent counts
    university_responses = []
    for university in universities:
        current_agents = db.query(UniversityAgent).filter(
            UniversityAgent.university_id == university.id,
            UniversityAgent.status == "active"
        ).count()
        
        university_responses.append(UniversityResponse(
            id=university.id,
            name=university.name,
            description=university.description,
            max_agents=university.max_agents,
            current_agents=current_agents,
            status=university.status,
            settings=university.settings or {},
            created_at=university.created_at.isoformat(),
            updated_at=university.updated_at.isoformat()
        ))
    
    return university_responses

@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_university(
    university_data: UniversityCreate,
    db: Session = Depends(get_db)
):
    """Create a new university"""
    # Check if university with same name already exists
    existing_university = db.query(University).filter(University.name == university_data.name).first()
    if existing_university:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="University with this name already exists"
        )
    
    # Create new university with generated ID
    import uuid
    university = University(
        id=str(uuid.uuid4()),
        name=university_data.name,
        description=university_data.description,
        owner_user_id=university_data.owner_user_id,
        max_agents=university_data.max_agents,
        settings=university_data.settings or {},
        status="active"
    )

    db.add(university)
    db.commit()
    db.refresh(university)

    return {
        "id": university.id,
        "name": university.name,
        "description": university.description,
        "max_agents": university.max_agents,
        "current_agents": 0,  # New university has no agents
        "status": university.status,
        "settings": university.settings or {},
        "created_at": university.created_at.isoformat(),
        "updated_at": university.updated_at.isoformat()
    }

@router.get("/{university_id}")
async def get_university(university_id: str, db: Session = Depends(get_db)):
    """Get a specific university"""
    university = db.query(University).filter(University.id == university_id).first()
    if not university:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="University not found"
        )

    current_agents = db.query(UniversityAgent).filter(
        UniversityAgent.university_id == university_id,
        UniversityAgent.status == "active"
    ).count()

    return {
        "id": university.id,
        "name": university.name,
        "description": university.description,
        "max_agents": university.max_agents,
        "current_agents": current_agents,
        "status": university.status,
        "settings": university.settings or {},
        "created_at": university.created_at.isoformat(),
        "updated_at": university.updated_at.isoformat()
    }

@router.put("/{university_id}")
async def update_university(
    university_id: str,
    university_data: UniversityUpdate,
    db: Session = Depends(get_db)
):
    """Update a university"""
    university = db.query(University).filter(University.id == university_id).first()
    if not university:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="University not found"
        )
    
    # Update fields if provided
    if university_data.name is not None:
        # Check if new name conflicts with existing university
        existing = db.query(University).filter(
            University.name == university_data.name,
            University.id != university_id
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="University with this name already exists"
            )
        university.name = university_data.name
    
    if university_data.description is not None:
        university.description = university_data.description

    if university_data.max_agents is not None:
        university.max_agents = university_data.max_agents

    if university_data.settings is not None:
        university.settings = university_data.settings

    if university_data.status is not None:
        university.status = university_data.status

    db.commit()
    db.refresh(university)

    current_agents = db.query(UniversityAgent).filter(
        UniversityAgent.university_id == university_id,
        UniversityAgent.status == "active"
    ).count()

    return {
        "id": university.id,
        "name": university.name,
        "description": university.description,
        "max_agents": university.max_agents,
        "current_agents": current_agents,
        "status": university.status,
        "settings": university.settings or {},
        "created_at": university.created_at.isoformat(),
        "updated_at": university.updated_at.isoformat()
    }

@router.delete("/{university_id}", status_code=status.HTTP_200_OK)
async def delete_university(university_id: str, db: Session = Depends(get_db)):
    """Delete a university"""
    university = db.query(University).filter(University.id == university_id).first()
    if not university:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="University not found"
        )

    # Check if university has active agents
    active_agents = db.query(UniversityAgent).filter(
        UniversityAgent.university_id == university_id,
        UniversityAgent.status == "active"
    ).count()

    if active_agents > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete university with active agents"
        )

    db.delete(university)
    db.commit()

    return {"message": "University deleted successfully"}

@router.get("/{university_id}/agents")
async def get_university_agents(university_id: str, db: Session = Depends(get_db)):
    """Get agents for a university"""
    university = db.query(University).filter(University.id == university_id).first()
    if not university:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="University not found"
        )

    agents = db.query(UniversityAgent).filter(UniversityAgent.university_id == university_id).all()

    return [
        {
            "id": agent.id,
            "name": agent.name,
            "agent_type": agent.agent_type,
            "status": agent.status,
            "specialization": agent.specialization,
            "competency_score": agent.competency_score,
            "training_hours": agent.training_hours
        }
        for agent in agents
    ]

@router.get("/{university_id}/stats")
async def get_university_stats(university_id: str, db: Session = Depends(get_db)):
    """Get detailed statistics for a university"""
    university = db.query(University).filter(University.id == university_id).first()
    if not university:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="University not found"
        )
    
    # Get agent statistics
    total_agents = db.query(UniversityAgent).filter(UniversityAgent.university_id == university_id).count()
    active_agents = db.query(UniversityAgent).filter(
        UniversityAgent.university_id == university_id,
        UniversityAgent.status == "active"
    ).count()
    inactive_agents = total_agents - active_agents
    
    # Get curriculum statistics
    total_curricula = db.query(CurriculumPath).filter(CurriculumPath.university_id == university_id).count()
    active_curricula = db.query(CurriculumPath).filter(
        CurriculumPath.university_id == university_id,
        CurriculumPath.status == "active"
    ).count()
    
    # Get competition statistics
    total_competitions = db.query(Competition).filter(Competition.university_id == university_id).count()
    active_competitions = db.query(Competition).filter(
        Competition.university_id == university_id,
        Competition.status == "active"
    ).count()
    
    return {
        "total_agents": total_agents,
        "active_agents": active_agents,
        "inactive_agents": inactive_agents,
        "total_competitions": total_competitions,
        "active_competitions": active_competitions,
        "total_curricula": total_curricula,
        "active_curricula": active_curricula,
        "capacity_usage": f"{(active_agents / university.max_agents * 100):.1f}%",
        "max_agents": university.max_agents,
        "available_agents": university.max_agents - active_agents
    }