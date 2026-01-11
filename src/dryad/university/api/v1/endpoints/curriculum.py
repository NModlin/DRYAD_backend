"""
Curriculum management endpoints for Uni0
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel

from dryad.university.database.database import get_db
from dryad.university.database.models_university import CurriculumPath, University, UniversityAgent
from dryad.university.services.curriculum_engine import CurriculumEngine

router = APIRouter()

class CurriculumCreate(BaseModel):
    university_id: int
    name: str
    description: Optional[str] = None
    difficulty_level: str = "beginner"
    estimated_duration_hours: int = 40
    prerequisites: Optional[List[str]] = None
    learning_objectives: Optional[List[str]] = None
    settings: Optional[dict] = None

class CurriculumUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    difficulty_level: Optional[str] = None
    estimated_duration_hours: Optional[int] = None
    prerequisites: Optional[List[str]] = None
    learning_objectives: Optional[List[str]] = None
    settings: Optional[dict] = None
    status: Optional[str] = None

class CurriculumResponse(BaseModel):
    id: int
    university_id: int
    name: str
    description: Optional[str]
    difficulty_level: str
    estimated_duration_hours: int
    prerequisites: List[str]
    learning_objectives: List[str]
    status: str
    settings: dict
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True

@router.get("/", response_model=List[CurriculumResponse])
async def list_curricula(
    university_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """List curricula, optionally filtered by university"""
    query = db.query(CurriculumPath)
    
    if university_id:
        query = query.filter(CurriculumPath.university_id == university_id)
    
    curricula = query.offset(skip).limit(limit).all()
    
    return [
        CurriculumResponse(
            id=curriculum.id,
            university_id=curriculum.university_id,
            name=curriculum.name,
            description=curriculum.description,
            difficulty_level=curriculum.difficulty_level,
            estimated_duration_hours=curriculum.estimated_duration_hours,
            prerequisites=curriculum.prerequisites or [],
            learning_objectives=curriculum.learning_objectives or [],
            status=curriculum.status,
            settings=curriculum.settings or {},
            created_at=curriculum.created_at.isoformat(),
            updated_at=curriculum.updated_at.isoformat()
        )
        for curriculum in curricula
    ]

@router.post("/", response_model=CurriculumResponse)
async def create_curriculum(
    curriculum_data: CurriculumCreate,
    db: Session = Depends(get_db)
):
    """Create a new curriculum"""
    # Verify university exists
    university = db.query(University).filter(University.id == curriculum_data.university_id).first()
    if not university:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="University not found"
        )
    
    # Check if curriculum with same name already exists in this university
    existing_curriculum = db.query(CurriculumPath).filter(
        CurriculumPath.university_id == curriculum_data.university_id,
        CurriculumPath.name == curriculum_data.name
    ).first()
    if existing_curriculum:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Curriculum with this name already exists in this university"
        )
    
    # Create new curriculum
    curriculum = CurriculumPath(
        university_id=curriculum_data.university_id,
        name=curriculum_data.name,
        description=curriculum_data.description,
        difficulty_level=curriculum_data.difficulty_level,
        estimated_duration_hours=curriculum_data.estimated_duration_hours,
        prerequisites=curriculum_data.prerequisites or [],
        learning_objectives=curriculum_data.learning_objectives or [],
        settings=curriculum_data.settings or {}
    )
    
    db.add(curriculum)
    db.commit()
    db.refresh(curriculum)
    
    return CurriculumResponse(
        id=curriculum.id,
        university_id=curriculum.university_id,
        name=curriculum.name,
        description=curriculum.description,
        difficulty_level=curriculum.difficulty_level,
        estimated_duration_hours=curriculum.estimated_duration_hours,
        prerequisites=curriculum.prerequisites or [],
        learning_objectives=curriculum.learning_objectives or [],
        status=curriculum.status,
        settings=curriculum.settings or {},
        created_at=curriculum.created_at.isoformat(),
        updated_at=curriculum.updated_at.isoformat()
    )

@router.get("/{curriculum_id}", response_model=CurriculumResponse)
async def get_curriculum(curriculum_id: int, db: Session = Depends(get_db)):
    """Get a specific curriculum"""
    curriculum = db.query(CurriculumPath).filter(CurriculumPath.id == curriculum_id).first()
    if not curriculum:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Curriculum not found"
        )
    
    return CurriculumResponse(
        id=curriculum.id,
        university_id=curriculum.university_id,
        name=curriculum.name,
        description=curriculum.description,
        difficulty_level=curriculum.difficulty_level,
        estimated_duration_hours=curriculum.estimated_duration_hours,
        prerequisites=curriculum.prerequisites or [],
        learning_objectives=curriculum.learning_objectives or [],
        status=curriculum.status,
        settings=curriculum.settings or {},
        created_at=curriculum.created_at.isoformat(),
        updated_at=curriculum.updated_at.isoformat()
    )

@router.put("/{curriculum_id}", response_model=CurriculumResponse)
async def update_curriculum(
    curriculum_id: int,
    curriculum_data: CurriculumUpdate,
    db: Session = Depends(get_db)
):
    """Update a curriculum"""
    curriculum = db.query(CurriculumPath).filter(CurriculumPath.id == curriculum_id).first()
    if not curriculum:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Curriculum not found"
        )
    
    # Update fields if provided
    if curriculum_data.name is not None:
        # Check if new name conflicts with existing curriculum in same university
        existing = db.query(CurriculumPath).filter(
            CurriculumPath.university_id == curriculum.university_id,
            CurriculumPath.name == curriculum_data.name,
            CurriculumPath.id != curriculum_id
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Curriculum with this name already exists in this university"
            )
        curriculum.name = curriculum_data.name
    
    if curriculum_data.description is not None:
        curriculum.description = curriculum_data.description
    
    if curriculum_data.difficulty_level is not None:
        curriculum.difficulty_level = curriculum_data.difficulty_level
    
    if curriculum_data.estimated_duration_hours is not None:
        curriculum.estimated_duration_hours = curriculum_data.estimated_duration_hours
    
    if curriculum_data.prerequisites is not None:
        curriculum.prerequisites = curriculum_data.prerequisites
    
    if curriculum_data.learning_objectives is not None:
        curriculum.learning_objectives = curriculum_data.learning_objectives
    
    if curriculum_data.settings is not None:
        curriculum.settings = curriculum_data.settings
    
    if curriculum_data.status is not None:
        curriculum.status = curriculum_data.status
    
    db.commit()
    db.refresh(curriculum)
    
    return CurriculumResponse(
        id=curriculum.id,
        university_id=curriculum.university_id,
        name=curriculum.name,
        description=curriculum.description,
        difficulty_level=curriculum.difficulty_level,
        estimated_duration_hours=curriculum.estimated_duration_hours,
        prerequisites=curriculum.prerequisites or [],
        learning_objectives=curriculum.learning_objectives or [],
        status=curriculum.status,
        settings=curriculum.settings or {},
        created_at=curriculum.created_at.isoformat(),
        updated_at=curriculum.updated_at.isoformat()
    )

@router.delete("/{curriculum_id}")
async def delete_curriculum(curriculum_id: int, db: Session = Depends(get_db)):
    """Delete a curriculum"""
    curriculum = db.query(CurriculumPath).filter(CurriculumPath.id == curriculum_id).first()
    if not curriculum:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Curriculum not found"
        )
    
    # Check if curriculum is in use by any agents
    agents_using_curriculum = db.query(UniversityAgent).filter(
        UniversityAgent.current_curriculum_id == curriculum_id
    ).count()
    
    if agents_using_curriculum > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete curriculum that is currently assigned to agents"
        )
    
    db.delete(curriculum)
    db.commit()
    
    return {"message": "Curriculum deleted successfully"}

@router.get("/{curriculum_id}/stats")
async def get_curriculum_stats(curriculum_id: int, db: Session = Depends(get_db)):
    """Get statistics for a curriculum"""
    curriculum = db.query(CurriculumPath).filter(CurriculumPath.id == curriculum_id).first()
    if not curriculum:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Curriculum not found"
        )
    
    # Get agent statistics
    total_agents = db.query(UniversityAgent).filter(
        UniversityAgent.current_curriculum_id == curriculum_id
    ).count()
    
    active_agents = db.query(UniversityAgent).filter(
        UniversityAgent.current_curriculum_id == curriculum_id,
        UniversityAgent.status == "active"
    ).count()
    
    # Get completion statistics (this would need more detailed tracking)
    completed_agents = db.query(UniversityAgent).filter(
        UniversityAgent.current_curriculum_id == curriculum_id,
        UniversityAgent.status == "completed"
    ).count()
    
    return {
        "curriculum_id": curriculum_id,
        "name": curriculum.name,
        "statistics": {
            "agents": {
                "total_enrolled": total_agents,
                "active": active_agents,
                "completed": completed_agents,
                "dropout_rate": f"{((total_agents - active_agents - completed_agents) / total_agents * 100):.1f}%" if total_agents > 0 else "0%"
            },
            "curriculum": {
                "difficulty_level": curriculum.difficulty_level,
                "estimated_duration": f"{curriculum.estimated_duration_hours} hours",
                "prerequisites_count": len(curriculum.prerequisites or []),
                "learning_objectives_count": len(curriculum.learning_objectives or [])
            }
        }
    }

@router.post("/{curriculum_id}/assign/{agent_id}")
async def assign_curriculum_to_agent(
    curriculum_id: int,
    agent_id: int,
    db: Session = Depends(get_db)
):
    """Assign a curriculum to an agent"""
    curriculum = db.query(CurriculumPath).filter(CurriculumPath.id == curriculum_id).first()
    if not curriculum:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Curriculum not found"
        )
    
    agent = db.query(UniversityAgent).filter(UniversityAgent.id == agent_id).first()
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent not found"
        )
    
    # Verify agent belongs to the same university as curriculum
    if agent.university_id != curriculum.university_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Agent and curriculum must belong to the same university"
        )
    
    # Assign curriculum to agent
    agent.current_curriculum_id = curriculum_id
    db.commit()
    
    return {"message": f"Curriculum '{curriculum.name}' assigned to agent '{agent.name}'"}