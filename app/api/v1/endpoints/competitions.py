"""
Competition API Endpoints

Provides REST API endpoints for competition management including:
- CRUD operations for competitions
- Round management
- Leaderboard management
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from app.database.database import get_db
from app.models.competition import (
    Competition,
    CompetitionRound,
    Leaderboard,
    LeaderboardRanking,
    CompetitionType,
    CompetitionStatus,
    ChallengeCategory,
    LeaderboardType,
    CompetitionCreate,
    CompetitionUpdate,
    CompetitionResponse
)
from app.services.competition_service import CompetitionService

router = APIRouter(prefix="/competitions", tags=["competitions"])


# ==================== Pydantic Schemas ====================

class RoundCreate(BaseModel):
    """Schema for creating a competition round"""
    round_number: int = Field(..., ge=1)
    agent_actions: Dict[str, Any]
    agent_scores: Dict[str, float]


class RoundComplete(BaseModel):
    """Schema for completing a competition round"""
    winner_id: Optional[str] = None
    training_data_points: int = Field(default=0, ge=0)


class CompetitionComplete(BaseModel):
    """Schema for completing a competition"""
    winner_id: Optional[str] = None
    final_scores: Dict[str, float]


class LeaderboardCreate(BaseModel):
    """Schema for creating a leaderboard"""
    name: str = Field(..., min_length=1, max_length=255)
    university_id: Optional[str] = None
    leaderboard_type: LeaderboardType = LeaderboardType.ELO
    challenge_category: Optional[ChallengeCategory] = None
    time_period: Optional[str] = None


class RankingUpdate(BaseModel):
    """Schema for updating a ranking"""
    score_change: float
    won: bool = False
    lost: bool = False
    draw: bool = False


# ==================== Competition Endpoints ====================

@router.post("/", response_model=CompetitionResponse, status_code=201)
def create_competition(
    competition_data: CompetitionCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new competition.
    
    - **university_id**: University ID (required)
    - **name**: Competition name (required)
    - **competition_type**: Type (INDIVIDUAL, TEAM, TOURNAMENT, CHALLENGE, RANKED)
    - **challenge_category**: Category (REASONING, TOOL_USE, MEMORY, etc.)
    - **participant_ids**: List of participant agent IDs
    """
    try:
        competition = CompetitionService.create_competition(db, competition_data)
        return competition
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{competition_id}", response_model=CompetitionResponse)
def get_competition(
    competition_id: str,
    db: Session = Depends(get_db)
):
    """
    Get a competition by ID.
    
    - **competition_id**: Competition ID
    """
    competition = CompetitionService.get_competition(db, competition_id)
    
    if not competition:
        raise HTTPException(status_code=404, detail="Competition not found")
    
    return competition


@router.get("/", response_model=List[CompetitionResponse])
def list_competitions(
    university_id: str = Query(..., description="University ID"),
    competition_type: Optional[CompetitionType] = Query(None, description="Filter by type"),
    category: Optional[ChallengeCategory] = Query(None, description="Filter by category"),
    status: Optional[CompetitionStatus] = Query(None, description="Filter by status"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    db: Session = Depends(get_db)
):
    """
    List competitions for a university with optional filters.
    
    - **university_id**: University ID (required)
    - **competition_type**: Filter by type
    - **category**: Filter by category
    - **status**: Filter by status
    """
    competitions = CompetitionService.get_competitions_by_university(
        db, university_id, competition_type, category, status, skip, limit
    )
    
    return competitions


@router.put("/{competition_id}", response_model=CompetitionResponse)
def update_competition(
    competition_id: str,
    update_data: CompetitionUpdate,
    db: Session = Depends(get_db)
):
    """
    Update a competition.
    
    - **competition_id**: Competition ID
    - **update_data**: Fields to update
    """
    competition = CompetitionService.update_competition(db, competition_id, update_data)
    
    if not competition:
        raise HTTPException(status_code=404, detail="Competition not found")
    
    return competition


@router.post("/{competition_id}/start", response_model=CompetitionResponse)
def start_competition(
    competition_id: str,
    db: Session = Depends(get_db)
):
    """
    Start a competition.
    
    - **competition_id**: Competition ID
    """
    competition = CompetitionService.start_competition(db, competition_id)
    
    if not competition:
        raise HTTPException(status_code=404, detail="Competition not found")
    
    return competition


@router.post("/{competition_id}/complete", response_model=CompetitionResponse)
def complete_competition(
    competition_id: str,
    completion_data: CompetitionComplete,
    db: Session = Depends(get_db)
):
    """
    Complete a competition and update leaderboards.
    
    - **competition_id**: Competition ID
    - **winner_id**: Winner agent ID
    - **final_scores**: Final scores for all participants
    """
    competition = CompetitionService.complete_competition(
        db, competition_id, completion_data.winner_id, completion_data.final_scores
    )
    
    if not competition:
        raise HTTPException(status_code=404, detail="Competition not found")
    
    return competition


@router.post("/{competition_id}/cancel", response_model=CompetitionResponse)
def cancel_competition(
    competition_id: str,
    db: Session = Depends(get_db)
):
    """
    Cancel a competition.
    
    - **competition_id**: Competition ID
    """
    competition = CompetitionService.cancel_competition(db, competition_id)
    
    if not competition:
        raise HTTPException(status_code=404, detail="Competition not found")
    
    return competition


# ==================== Round Endpoints ====================

@router.post("/{competition_id}/rounds", status_code=201)
def create_round(
    competition_id: str,
    round_data: RoundCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new competition round.
    
    - **competition_id**: Competition ID
    - **round_number**: Round number
    - **agent_actions**: Actions taken by agents
    - **agent_scores**: Scores for agents in this round
    """
    try:
        competition_round = CompetitionService.create_round(
            db, competition_id, round_data.round_number,
            round_data.agent_actions, round_data.agent_scores
        )
        return competition_round
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/rounds/{round_id}/complete")
def complete_round(
    round_id: str,
    completion_data: RoundComplete,
    db: Session = Depends(get_db)
):
    """
    Complete a competition round.
    
    - **round_id**: Round ID
    - **winner_id**: Winner agent ID for this round
    - **training_data_points**: Number of training data points collected
    """
    competition_round = CompetitionService.complete_round(
        db, round_id, completion_data.winner_id, completion_data.training_data_points
    )
    
    if not competition_round:
        raise HTTPException(status_code=404, detail="Round not found")
    
    return competition_round


@router.get("/{competition_id}/rounds")
def list_rounds(
    competition_id: str,
    db: Session = Depends(get_db)
):
    """
    Get all rounds for a competition.
    
    - **competition_id**: Competition ID
    """
    rounds = CompetitionService.get_rounds_by_competition(db, competition_id)
    
    return rounds


# ==================== Leaderboard Endpoints ====================

@router.post("/leaderboards", status_code=201)
def create_leaderboard(
    leaderboard_data: LeaderboardCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new leaderboard.
    
    - **name**: Leaderboard name (required)
    - **university_id**: University ID (optional, null for global)
    - **leaderboard_type**: Type (ELO, POINTS, WINS, CUSTOM)
    - **challenge_category**: Category filter (optional)
    - **time_period**: Time period (all_time, monthly, weekly, daily)
    """
    try:
        leaderboard = CompetitionService.create_leaderboard(
            db,
            leaderboard_data.name,
            leaderboard_data.university_id,
            leaderboard_data.leaderboard_type,
            leaderboard_data.challenge_category,
            leaderboard_data.time_period
        )
        return leaderboard
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/leaderboards/{leaderboard_id}")
def get_leaderboard(
    leaderboard_id: str,
    db: Session = Depends(get_db)
):
    """
    Get a leaderboard by ID.
    
    - **leaderboard_id**: Leaderboard ID
    """
    leaderboard = CompetitionService.get_leaderboard(db, leaderboard_id)
    
    if not leaderboard:
        raise HTTPException(status_code=404, detail="Leaderboard not found")
    
    return leaderboard


@router.get("/leaderboards")
def list_leaderboards(
    university_id: str = Query(..., description="University ID"),
    active_only: bool = Query(True, description="Only return active leaderboards"),
    db: Session = Depends(get_db)
):
    """
    Get leaderboards for a university.
    
    - **university_id**: University ID
    - **active_only**: Only return active leaderboards
    """
    leaderboards = CompetitionService.get_leaderboards_by_university(
        db, university_id, active_only
    )
    
    return leaderboards


@router.get("/leaderboards/{leaderboard_id}/rankings")
def get_rankings(
    leaderboard_id: str,
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of rankings to return"),
    db: Session = Depends(get_db)
):
    """
    Get rankings for a leaderboard.
    
    - **leaderboard_id**: Leaderboard ID
    - **limit**: Maximum number of rankings to return
    """
    rankings = CompetitionService.get_rankings(db, leaderboard_id, limit)
    
    return rankings


@router.post("/leaderboards/{leaderboard_id}/rankings/{agent_id}")
def update_ranking(
    leaderboard_id: str,
    agent_id: str,
    ranking_data: RankingUpdate,
    db: Session = Depends(get_db)
):
    """
    Update or create a ranking for an agent.
    
    - **leaderboard_id**: Leaderboard ID
    - **agent_id**: Agent ID
    - **score_change**: Score change to apply
    - **won**: Whether the agent won
    - **lost**: Whether the agent lost
    - **draw**: Whether it was a draw
    """
    try:
        ranking = CompetitionService.update_ranking(
            db, leaderboard_id, agent_id, ranking_data.score_change,
            ranking_data.won, ranking_data.lost, ranking_data.draw
        )
        return ranking
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

