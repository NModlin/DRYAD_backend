"""
Competition management endpoints for Uni0
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime, timezone
import uuid

from dryad.university.database.database import get_db
from dryad.university.database.models_university import Competition, University, UniversityAgent, CompetitionParticipant
from dryad.university.services.competition_engine import CompetitionEngine

router = APIRouter()

class CompetitionCreate(BaseModel):
    university_id: str
    name: str
    description: Optional[str] = None
    competition_type: str = "skill_challenge"
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    max_participants: int = 50
    rules: Optional[dict] = None
    rewards: Optional[dict] = None
    settings: Optional[dict] = None

class CompetitionUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    competition_type: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    max_participants: Optional[int] = None
    rules: Optional[dict] = None
    rewards: Optional[dict] = None
    settings: Optional[dict] = None
    status: Optional[str] = None

class CompetitionResponse(BaseModel):
    id: str
    university_id: str
    name: str
    description: Optional[str]
    competition_type: str
    start_date: Optional[str]
    end_date: Optional[str]
    max_participants: int
    current_participants: int
    rules: dict
    rewards: dict
    status: str
    settings: dict
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True

class CompetitionParticipantResponse(BaseModel):
    id: str
    competition_id: str
    agent_id: str
    agent_name: str
    score: Optional[float]
    rank: Optional[int]
    status: str
    joined_at: str
    last_updated: str

    class Config:
        from_attributes = True

@router.get("/", response_model=List[CompetitionResponse])
async def list_competitions(
    university_id: Optional[str] = None,
    status: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """List competitions, optionally filtered by university and status"""
    query = db.query(Competition)
    
    if university_id:
        query = query.filter(Competition.university_id == university_id)
    
    if status:
        query = query.filter(Competition.status == status)
    
    competitions = query.offset(skip).limit(limit).all()
    
    # Calculate current participant counts
    competition_responses = []
    for competition in competitions:
        current_participants = db.query(CompetitionParticipant).filter(
            CompetitionParticipant.competition_id == competition.id,
            CompetitionParticipant.status == "active"
        ).count()
        
        competition_responses.append(CompetitionResponse(
            id=competition.id,
            university_id=competition.university_id,
            name=competition.name,
            description=competition.description,
            competition_type=competition.competition_type,
            start_date=competition.scheduled_start.isoformat() if competition.scheduled_start else None,
            end_date=competition.scheduled_end.isoformat() if competition.scheduled_end else None,
            max_participants=competition.max_participants,
            current_participants=current_participants,
            rules=competition.rules or {},
            rewards=competition.rewards or {},
            status=competition.status,
            settings=competition.settings or {},
            created_at=competition.created_at.isoformat(),
            updated_at=competition.updated_at.isoformat()
        ))
    
    return competition_responses

@router.post("/", response_model=CompetitionResponse)
async def create_competition(
    competition_data: CompetitionCreate,
    db: Session = Depends(get_db)
):
    """Create a new competition"""
    # Verify university exists
    university = db.query(University).filter(University.id == competition_data.university_id).first()
    if not university:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="University not found"
        )
    
    # Check if competition with same name already exists in this university
    existing_competition = db.query(Competition).filter(
        Competition.university_id == competition_data.university_id,
        Competition.name == competition_data.name
    ).first()
    if existing_competition:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Competition with this name already exists in this university"
        )
    
    # Set default start date to now if not provided
    start_date = competition_data.start_date or datetime.now(timezone.utc)
    
    # Create new competition
    competition = Competition(
        id=str(uuid.uuid4()),
        university_id=competition_data.university_id,
        name=competition_data.name,
        description=competition_data.description,
        competition_type=competition_data.competition_type,
        scheduled_start=start_date,
        scheduled_end=competition_data.end_date,
        max_participants=competition_data.max_participants,
        rules=competition_data.rules or {},
        rewards=competition_data.rewards or {},
        settings=competition_data.settings or {}
    )
    
    db.add(competition)
    db.commit()
    db.refresh(competition)
    
    return CompetitionResponse(
        id=competition.id,
        university_id=competition.university_id,
        name=competition.name,
        description=competition.description,
        competition_type=competition.competition_type,
        start_date=competition.scheduled_start.isoformat() if competition.scheduled_start else None,
        end_date=competition.scheduled_end.isoformat() if competition.scheduled_end else None,
        max_participants=competition.max_participants,
        current_participants=0,  # New competition has no participants
        rules=competition.rules or {},
        rewards=competition.rewards or {},
        status=competition.status,
        settings=competition.settings or {},
        created_at=competition.created_at.isoformat(),
        updated_at=competition.updated_at.isoformat()
    )

@router.get("/{competition_id}", response_model=CompetitionResponse)
async def get_competition(competition_id: str, db: Session = Depends(get_db)):
    """Get a specific competition"""
    competition = db.query(Competition).filter(Competition.id == competition_id).first()
    if not competition:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Competition not found"
        )
    
    current_participants = db.query(CompetitionParticipant).filter(
        CompetitionParticipant.competition_id == competition_id,
        CompetitionParticipant.status == "active"
    ).count()
    
    return CompetitionResponse(
        id=competition.id,
        university_id=competition.university_id,
        name=competition.name,
        description=competition.description,
        competition_type=competition.competition_type,
        start_date=competition.scheduled_start.isoformat() if competition.scheduled_start else None,
        end_date=competition.scheduled_end.isoformat() if competition.scheduled_end else None,
        max_participants=competition.max_participants,
        current_participants=current_participants,
        rules=competition.rules or {},
        rewards=competition.rewards or {},
        status=competition.status,
        settings=competition.settings or {},
        created_at=competition.created_at.isoformat(),
        updated_at=competition.updated_at.isoformat()
    )

@router.put("/{competition_id}", response_model=CompetitionResponse)
async def update_competition(
    competition_id: str,
    competition_data: CompetitionUpdate,
    db: Session = Depends(get_db)
):
    """Update a competition"""
    competition = db.query(Competition).filter(Competition.id == competition_id).first()
    if not competition:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Competition not found"
        )
    
    # Update fields if provided
    if competition_data.name is not None:
        # Check if new name conflicts with existing competition in same university
        existing = db.query(Competition).filter(
            Competition.university_id == competition.university_id,
            Competition.name == competition_data.name,
            Competition.id != competition_id
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Competition with this name already exists in this university"
            )
        competition.name = competition_data.name
    
    if competition_data.description is not None:
        competition.description = competition_data.description
    
    if competition_data.competition_type is not None:
        competition.competition_type = competition_data.competition_type
    
    if competition_data.start_date is not None:
        competition.scheduled_start = competition_data.start_date
    
    if competition_data.end_date is not None:
        competition.scheduled_end = competition_data.end_date
    
    if competition_data.max_participants is not None:
        competition.max_participants = competition_data.max_participants
    
    if competition_data.rules is not None:
        competition.rules = competition_data.rules
    
    if competition_data.rewards is not None:
        competition.rewards = competition_data.rewards
    
    if competition_data.settings is not None:
        competition.settings = competition_data.settings
    
    if competition_data.status is not None:
        competition.status = competition_data.status
    
    db.commit()
    db.refresh(competition)
    
    current_participants = db.query(CompetitionParticipant).filter(
        CompetitionParticipant.competition_id == competition_id,
        CompetitionParticipant.status == "active"
    ).count()
    
    return CompetitionResponse(
        id=competition.id,
        university_id=competition.university_id,
        name=competition.name,
        description=competition.description,
        competition_type=competition.competition_type,
        start_date=competition.scheduled_start.isoformat() if competition.scheduled_start else None,
        end_date=competition.scheduled_end.isoformat() if competition.scheduled_end else None,
        max_participants=competition.max_participants,
        current_participants=current_participants,
        rules=competition.rules or {},
        rewards=competition.rewards or {},
        status=competition.status,
        settings=competition.settings or {},
        created_at=competition.created_at.isoformat(),
        updated_at=competition.updated_at.isoformat()
    )

@router.delete("/{competition_id}")
async def delete_competition(competition_id: str, db: Session = Depends(get_db)):
    """Delete a competition"""
    competition = db.query(Competition).filter(Competition.id == competition_id).first()
    if not competition:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Competition not found"
        )
    
    # Check if competition has active participants
    active_participants = db.query(CompetitionParticipant).filter(
        CompetitionParticipant.competition_id == competition_id,
        CompetitionParticipant.status == "active"
    ).count()
    
    if active_participants > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete competition with active participants"
        )
    
    db.delete(competition)
    db.commit()
    
    return {"message": "Competition deleted successfully"}

@router.get("/{competition_id}/participants", response_model=List[CompetitionParticipantResponse])
async def list_competition_participants(
    competition_id: str,
    db: Session = Depends(get_db)
):
    """List participants in a competition"""
    competition = db.query(Competition).filter(Competition.id == competition_id).first()
    if not competition:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Competition not found"
        )
    
    participants = db.query(CompetitionParticipant).filter(
        CompetitionParticipant.competition_id == competition_id
    ).all()
    
    participant_responses = []
    for participant in participants:
        agent = db.query(UniversityAgent).filter(UniversityAgent.id == participant.agent_id).first()
        if agent:
            participant_responses.append(CompetitionParticipantResponse(
                id=participant.id,
                competition_id=participant.competition_id,
                agent_id=participant.agent_id,
                agent_name=agent.name,
                score=participant.score,
                rank=participant.rank,
                status=participant.status,
                joined_at=participant.joined_at.isoformat(),
                last_updated=participant.last_updated.isoformat()
            ))
    
    return participant_responses

@router.post("/{competition_id}/join/{agent_id}")
async def join_competition(
    competition_id: str,
    agent_id: str,
    db: Session = Depends(get_db)
):
    """Join an agent to a competition"""
    competition = db.query(Competition).filter(Competition.id == competition_id).first()
    if not competition:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Competition not found"
        )
    
    agent = db.query(UniversityAgent).filter(UniversityAgent.id == agent_id).first()
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent not found"
        )
    
    # Verify agent belongs to the same university as competition
    if agent.university_id != competition.university_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Agent and competition must belong to the same university"
        )
    
    # Check if competition is open for participation
    if competition.status != "active":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Competition is not currently active"
        )
    
    # Check if agent is already participating
    existing_participation = db.query(CompetitionParticipant).filter(
        CompetitionParticipant.competition_id == competition_id,
        CompetitionParticipant.agent_id == agent_id
    ).first()
    
    if existing_participation:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Agent is already participating in this competition"
        )
    
    # Check if competition has reached maximum participants
    current_participants = db.query(CompetitionParticipant).filter(
        CompetitionParticipant.competition_id == competition_id,
        CompetitionParticipant.status == "active"
    ).count()
    
    if current_participants >= competition.max_participants:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Competition has reached maximum participants"
        )
    
    # Create participation record
    participation = CompetitionParticipant(
        id=str(uuid.uuid4()),
        competition_id=competition_id,
        agent_id=agent_id,
        status="active"
    )
    
    db.add(participation)
    db.commit()
    
    return {"message": f"Agent '{agent.name}' joined competition '{competition.name}'"}

@router.get("/{competition_id}/leaderboard")
async def get_competition_leaderboard(competition_id: str, db: Session = Depends(get_db)):
    """Get competition leaderboard"""
    competition = db.query(Competition).filter(Competition.id == competition_id).first()
    if not competition:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Competition not found"
        )
    
    # Get participants ordered by score (descending)
    participants = db.query(CompetitionParticipant).filter(
        CompetitionParticipant.competition_id == competition_id,
        CompetitionParticipant.status == "active"
    ).order_by(CompetitionParticipant.score.desc()).all()
    
    leaderboard = []
    for rank, participant in enumerate(participants, 1):
        agent = db.query(UniversityAgent).filter(UniversityAgent.id == participant.agent_id).first()
        if agent:
            leaderboard.append({
                "rank": rank,
                "agent_id": agent.id,
                "agent_name": agent.name,
                "score": participant.score,
                "joined_at": participant.joined_at.isoformat(),
                "last_updated": participant.last_updated.isoformat()
            })
    
    return {
        "competition_id": competition_id,
        "competition_name": competition.name,
        "leaderboard": leaderboard,
        "total_participants": len(leaderboard)
    }