"""
Enhanced University API Endpoints

Provides RESTful API endpoints for the enhanced university system including:
- University agent management with detailed metrics
- Training data collection and quality assessment
- Improvement proposal generation and validation
- Achievement and gamification system
- Advanced analytics and reporting
"""

from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.services.enhanced_university_service import EnhancedUniversityService
from app.database.models_university import (
    UniversityAgent, TrainingDataCollection, ImprovementProposal, 
    Achievement, AgentAchievement, AgentProgress
)

router = APIRouter()

# ==================== University Agent Endpoints ====================

@router.post("/universities/{university_id}/agents", response_model=Dict[str, Any])
def create_agent(
    university_id: str,
    name: str,
    agent_type: str = Query("student", regex="^(student|professor|researcher|administrator)$"),
    configuration: Optional[Dict[str, Any]] = None,
    specialization: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Create a new university agent"""
    try:
        agent = EnhancedUniversityService.create_agent(
            db=db,
            university_id=university_id,
            name=name,
            agent_type=agent_type,
            configuration=configuration or {},
            specialization=specialization
        )
        
        return {
            "message": "Agent created successfully",
            "agent": {
                "id": agent.id,
                "name": agent.name,
                "agent_type": agent.agent_type,
                "status": agent.status,
                "created_at": agent.created_at.isoformat()
            }
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create agent: {str(e)}"
        )

@router.get("/universities/{university_id}/agents", response_model=Dict[str, Any])
def get_agents(
    university_id: str,
    agent_type: Optional[str] = Query(None, regex="^(student|professor|researcher|administrator)$"),
    status: Optional[str] = Query(None, regex="^(active|inactive|suspended)$"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """Get agents for a university"""
    agents = EnhancedUniversityService.get_agents_by_university(
        db=db,
        university_id=university_id,
        agent_type=agent_type,
        status=status,
        skip=skip,
        limit=limit
    )
    
    return {
        "university_id": university_id,
        "agents": [
            {
                "id": agent.id,
                "name": agent.name,
                "agent_type": agent.agent_type,
                "status": agent.status,
                "competency_score": agent.competency_score,
                "training_hours": agent.training_hours,
                "created_at": agent.created_at.isoformat()
            }
            for agent in agents
        ],
        "total_count": len(agents)
    }

@router.get("/agents/{agent_id}", response_model=Dict[str, Any])
def get_agent(agent_id: str, db: Session = Depends(get_db)):
    """Get detailed information about an agent"""
    agent = EnhancedUniversityService.get_agent(db=db, agent_id=agent_id)
    
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent not found"
        )
    
    return {
        "agent": {
            "id": agent.id,
            "university_id": agent.university_id,
            "name": agent.name,
            "agent_type": agent.agent_type,
            "status": agent.status,
            "specialization": agent.specialization,
            "competency_score": agent.competency_score,
            "training_hours": agent.training_hours,
            "training_data_collected": agent.training_data_collected,
            "competition_wins": agent.competition_wins,
            "competition_losses": agent.competition_losses,
            "competition_draws": agent.competition_draws,
            "average_score": agent.average_score,
            "highest_score": agent.highest_score,
            "elo_rating": agent.elo_rating,
            "configuration": agent.configuration,
            "created_at": agent.created_at.isoformat(),
            "updated_at": agent.updated_at.isoformat() if agent.updated_at else None,
            "last_competed_at": agent.last_competed_at.isoformat() if agent.last_competed_at else None
        }
    }

@router.put("/agents/{agent_id}/competency", response_model=Dict[str, Any])
def update_agent_competency(
    agent_id: str,
    competency_score: float = Query(..., ge=0.0, le=1.0),
    training_hours: Optional[float] = Query(None, ge=0.0),
    db: Session = Depends(get_db)
):
    """Update agent competency metrics"""
    agent = EnhancedUniversityService.update_agent_competency(
        db=db,
        agent_id=agent_id,
        competency_score=competency_score,
        training_hours=training_hours
    )
    
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent not found"
        )
    
    return {
        "message": "Agent competency updated successfully",
        "agent": {
            "id": agent.id,
            "competency_score": agent.competency_score,
            "training_hours": agent.training_hours,
            "updated_at": agent.updated_at.isoformat()
        }
    }

@router.put("/agents/{agent_id}/competition", response_model=Dict[str, Any])
def update_agent_competition_stats(
    agent_id: str,
    won: bool = Query(False),
    lost: bool = Query(False),
    draw: bool = Query(False),
    score: Optional[float] = Query(None, ge=0.0),
    db: Session = Depends(get_db)
):
    """Update agent competition statistics"""
    agent = EnhancedUniversityService.update_agent_competition_stats(
        db=db,
        agent_id=agent_id,
        won=won,
        lost=lost,
        draw=draw,
        score=score
    )
    
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent not found"
        )
    
    return {
        "message": "Agent competition stats updated successfully",
        "agent": {
            "id": agent.id,
            "competition_wins": agent.competition_wins,
            "competition_losses": agent.competition_losses,
            "competition_draws": agent.competition_draws,
            "average_score": agent.average_score,
            "highest_score": agent.highest_score,
            "elo_rating": agent.elo_rating,
            "last_competed_at": agent.last_competed_at.isoformat() if agent.last_competed_at else None
        }
    }

# ==================== Training Data Endpoints ====================

@router.post("/universities/{university_id}/training-data", response_model=Dict[str, Any])
def collect_training_data(
    university_id: str,
    agent_id: str,
    source_type: str,
    data_type: str,
    raw_data: Dict[str, Any],
    source_id: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
    db: Session = Depends(get_db)
):
    """Collect training data from agent activities"""
    try:
        collection = EnhancedUniversityService.collect_training_data(
            db=db,
            university_id=university_id,
            agent_id=agent_id,
            source_type=source_type,
            source_id=source_id,
            data_type=data_type,
            raw_data=raw_data,
            metadata=metadata or {}
        )
        
        return {
            "message": "Training data collected successfully",
            "collection": {
                "id": collection.id,
                "university_id": collection.university_id,
                "agent_id": collection.agent_id,
                "source_type": collection.source_type,
                "data_type": collection.data_type,
                "validation_status": collection.validation_status,
                "created_at": collection.created_at.isoformat()
            }
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to collect training data: {str(e)}"
        )

@router.put("/training-data/{collection_id}/validate", response_model=Dict[str, Any])
def validate_training_data(
    collection_id: str,
    quality_score: float = Query(..., ge=0.0, le=1.0),
    completeness_score: float = Query(..., ge=0.0, le=1.0),
    consistency_score: float = Query(..., ge=0.0, le=1.0),
    validity_score: float = Query(..., ge=0.0, le=1.0),
    validation_results: Dict[str, Any] = None,
    validated_by: str = Query(...),
    db: Session = Depends(get_db)
):
    """Validate training data collection"""
    if validation_results is None:
        validation_results = {}
        
    collection = EnhancedUniversityService.validate_training_data(
        db=db,
        collection_id=collection_id,
        quality_score=quality_score,
        completeness_score=completeness_score,
        consistency_score=consistency_score,
        validity_score=validity_score,
        validation_results=validation_results,
        validated_by=validated_by
    )
    
    if not collection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Training data collection not found"
        )
    
    return {
        "message": "Training data validated successfully",
        "collection": {
            "id": collection.id,
            "validation_status": collection.validation_status,
            "quality_score": collection.quality_score,
            "completeness_score": collection.completeness_score,
            "consistency_score": collection.consistency_score,
            "validity_score": collection.validity_score,
            "validated_by": collection.validated_by,
            "validated_at": collection.validated_at.isoformat() if collection.validated_at else None
        }
    }

@router.get("/universities/{university_id}/training-data", response_model=Dict[str, Any])
def get_training_data(
    university_id: str,
    validation_status: Optional[str] = Query(None, regex="^(pending|validated|rejected)$"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """Get training data collections for a university"""
    # This would require a new method in the service, but for now we'll query directly
    query = db.query(TrainingDataCollection).filter(
        TrainingDataCollection.university_id == university_id
    )
    
    if validation_status:
        query = query.filter(TrainingDataCollection.validation_status == validation_status)
        
    collections = query.order_by(TrainingDataCollection.created_at.desc()).offset(skip).limit(limit).all()
    
    return {
        "university_id": university_id,
        "collections": [
            {
                "id": collection.id,
                "agent_id": collection.agent_id,
                "source_type": collection.source_type,
                "data_type": collection.data_type,
                "validation_status": collection.validation_status,
                "quality_score": collection.quality_score,
                "created_at": collection.created_at.isoformat()
            }
            for collection in collections
        ],
        "total_count": len(collections)
    }

# ==================== Improvement Proposal Endpoints ====================

@router.post("/universities/{university_id}/improvement-proposals", response_model=Dict[str, Any])
def create_improvement_proposal(
    university_id: str,
    title: str,
    description: str,
    generated_by: str = Query("professor_agent"),
    source_data_collection_id: Optional[str] = None,
    implementation_details: Optional[str] = None,
    expected_improvement: Optional[float] = Query(None, ge=0.0),
    db: Session = Depends(get_db)
):
    """Create an improvement proposal"""
    try:
        proposal = EnhancedUniversityService.create_improvement_proposal(
            db=db,
            university_id=university_id,
            title=title,
            description=description,
            generated_by=generated_by,
            source_data_collection_id=source_data_collection_id,
            implementation_details=implementation_details,
            expected_improvement=expected_improvement
        )
        
        return {
            "message": "Improvement proposal created successfully",
            "proposal": {
                "id": proposal.id,
                "title": proposal.title,
                "validation_status": proposal.validation_status,
                "implementation_status": proposal.implementation_status,
                "created_at": proposal.created_at.isoformat()
            }
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create improvement proposal: {str(e)}"
        )

@router.put("/improvement-proposals/{proposal_id}/validate", response_model=Dict[str, Any])
def validate_improvement_proposal(
    proposal_id: str,
    validation_status: str = Query(..., regex="^(approved|rejected|needs_revision)$"),
    validation_results: Dict[str, Any] = None,
    validated_by: str = Query(...),
    db: Session = Depends(get_db)
):
    """Validate an improvement proposal"""
    if validation_results is None:
        validation_results = {}
        
    proposal = EnhancedUniversityService.validate_improvement_proposal(
        db=db,
        proposal_id=proposal_id,
        validation_status=validation_status,
        validation_results=validation_results,
        validated_by=validated_by
    )
    
    if not proposal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Improvement proposal not found"
        )
    
    return {
        "message": "Improvement proposal validated successfully",
        "proposal": {
            "id": proposal.id,
            "validation_status": proposal.validation_status,
            "validated_by": proposal.validated_by,
            "validated_at": proposal.validated_at.isoformat() if proposal.validated_at else None
        }
    }

@router.put("/improvement-proposals/{proposal_id}/implement", response_model=Dict[str, Any])
def implement_improvement_proposal(
    proposal_id: str,
    implementation_status: str = Query(..., regex="^(in_progress|completed|failed|cancelled)$"),
    db: Session = Depends(get_db)
):
    """Update implementation status of a proposal"""
    proposal = EnhancedUniversityService.implement_improvement_proposal(
        db=db,
        proposal_id=proposal_id,
        implementation_status=implementation_status
    )
    
    if not proposal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Improvement proposal not found"
        )
    
    return {
        "message": "Improvement proposal implementation status updated successfully",
        "proposal": {
            "id": proposal.id,
            "implementation_status": proposal.implementation_status,
            "implemented_at": proposal.implemented_at.isoformat() if proposal.implemented_at else None
        }
    }

# ==================== Achievement Endpoints ====================

@router.post("/achievements", response_model=Dict[str, Any])
def create_achievement(
    name: str,
    description: str,
    criteria: Dict[str, Any],
    category: Optional[str] = None,
    difficulty: str = Query("easy", regex="^(easy|medium|hard|expert)$"),
    points: int = Query(10, ge=1),
    required_count: int = Query(1, ge=1),
    db: Session = Depends(get_db)
):
    """Create a new achievement"""
    try:
        achievement = EnhancedUniversityService.create_achievement(
            db=db,
            name=name,
            description=description,
            criteria=criteria,
            category=category,
            difficulty=difficulty,
            points=points,
            required_count=required_count
        )
        
        return {
            "message": "Achievement created successfully",
            "achievement": {
                "id": achievement.id,
                "name": achievement.name,
                "description": achievement.description,
                "category": achievement.category,
                "difficulty": achievement.difficulty,
                "points": achievement.points
            }
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create achievement: {str(e)}"
        )

@router.post("/agents/{agent_id}/achievements/{achievement_id}", response_model=Dict[str, Any])
def award_achievement(
    agent_id: str,
    achievement_id: str,
    progress: Optional[int] = Query(None, ge=0),
    db: Session = Depends(get_db)
):
    """Award an achievement to an agent"""
    try:
        agent_achievement = EnhancedUniversityService.award_achievement(
            db=db,
            agent_id=agent_id,
            achievement_id=achievement_id,
            progress=progress
        )
        
        return {
            "message": "Achievement awarded successfully",
            "agent_achievement": {
                "id": agent_achievement.id,
                "agent_id": agent_achievement.agent_id,
                "achievement_id": agent_achievement.achievement_id,
                "progress": agent_achievement.progress,
                "is_completed": agent_achievement.is_completed,
                "awarded_at": agent_achievement.awarded_at.isoformat() if agent_achievement.awarded_at else None
            }
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to award achievement: {str(e)}"
        )

@router.get("/agents/{agent_id}/achievements", response_model=Dict[str, Any])
def get_agent_achievements(
    agent_id: str,
    completed_only: bool = Query(False),
    db: Session = Depends(get_db)
):
    """Get achievements for an agent"""
    agent_achievements = EnhancedUniversityService.get_agent_achievements(
        db=db,
        agent_id=agent_id,
        completed_only=completed_only
    )
    
    return {
        "agent_id": agent_id,
        "achievements": [
            {
                "id": aa.id,
                "achievement_id": aa.achievement_id,
                "achievement_name": aa.achievement.name,
                "achievement_description": aa.achievement.description,
                "progress": aa.progress,
                "required_count": aa.achievement.required_count,
                "is_completed": aa.is_completed,
                "awarded_at": aa.awarded_at.isoformat() if aa.awarded_at else None
            }
            for aa in agent_achievements
        ],
        "total_count": len(agent_achievements),
        "completed_count": len([aa for aa in agent_achievements if aa.is_completed])
    }

# ==================== Analytics Endpoints ====================

@router.get("/universities/{university_id}/analytics", response_model=Dict[str, Any])
def get_university_analytics(university_id: str, db: Session = Depends(get_db)):
    """Get comprehensive analytics for a university"""
    analytics = EnhancedUniversityService.get_university_analytics(
        db=db,
        university_id=university_id
    )
    
    return analytics