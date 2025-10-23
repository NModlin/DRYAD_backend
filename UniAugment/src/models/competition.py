"""
Competition and Arena models for the Agentic Research University System.

This module defines the competition framework including:
- Individual combat
- Team competitions
- Tournaments
- Leaderboards and rankings
- Training data collection
"""

import uuid
from datetime import datetime
from typing import Optional, Dict, Any, List
from enum import Enum

from sqlalchemy import Column, String, Text, Integer, Float, Boolean, DateTime, JSON, ForeignKey, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from pydantic import BaseModel, Field, validator

from app.database.models import Base


# Enums
class CompetitionType(str, Enum):
    """Type of competition"""
    INDIVIDUAL = "individual"  # Head-to-head agent battles
    TEAM = "team"  # Multi-agent team competitions
    TOURNAMENT = "tournament"  # Bracket-style tournaments
    CHALLENGE = "challenge"  # Open challenge for all agents
    RANKED = "ranked"  # Elo-based ranked matches


class CompetitionStatus(str, Enum):
    """Competition status"""
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    PAUSED = "paused"


class ChallengeCategory(str, Enum):
    """Challenge category"""
    REASONING = "reasoning"
    TOOL_USE = "tool_use"
    MEMORY = "memory"
    COLLABORATION = "collaboration"
    CREATIVITY = "creativity"
    SPEED = "speed"
    ACCURACY = "accuracy"
    EFFICIENCY = "efficiency"


class LeaderboardType(str, Enum):
    """Leaderboard type"""
    ELO = "elo"  # Elo rating system
    POINTS = "points"  # Points-based ranking
    WINS = "wins"  # Win count ranking
    CUSTOM = "custom"  # Custom ranking algorithm


# SQLAlchemy Models
class Competition(Base):
    """
    Competition instance in the Arena/Dojo.
    
    Represents a competitive event where agents test their capabilities
    and generate training data.
    """
    __tablename__ = "competitions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    university_id = Column(String, ForeignKey("universities.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Basic info
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    
    # Competition configuration
    competition_type = Column(String(50), nullable=False, index=True)
    challenge_category = Column(String(50), nullable=False, index=True)
    
    # Participants
    participant_ids = Column(JSON, nullable=False, default=list)  # Array of agent IDs
    team_1_ids = Column(JSON, nullable=True)  # For team competitions
    team_2_ids = Column(JSON, nullable=True)  # For team competitions
    max_participants = Column(Integer, nullable=True)
    
    # Rules and configuration
    rules = Column(JSON, nullable=False, default=dict)  # Competition-specific rules
    scoring_config = Column(JSON, nullable=False, default=dict)  # Scoring configuration
    time_limit_seconds = Column(Integer, nullable=True)
    max_rounds = Column(Integer, nullable=True)
    
    # Scheduling
    scheduled_start = Column(DateTime(timezone=True), nullable=True)
    scheduled_end = Column(DateTime(timezone=True), nullable=True)
    actual_start = Column(DateTime(timezone=True), nullable=True)
    actual_end = Column(DateTime(timezone=True), nullable=True)
    
    # Status
    status = Column(String(50), nullable=False, default=CompetitionStatus.SCHEDULED.value, index=True)
    
    # Results
    winner_id = Column(String, nullable=True)  # Agent ID of winner
    winner_team_ids = Column(JSON, nullable=True)  # For team competitions
    final_scores = Column(JSON, nullable=False, default=dict)  # {agent_id: score}
    rankings = Column(JSON, nullable=False, default=list)  # Ordered list of agent IDs
    
    # Training data
    training_data_collected = Column(Integer, nullable=False, default=0)
    data_quality_score = Column(Float, nullable=True)  # 0.0-1.0
    
    # Metadata
    tags = Column(JSON, nullable=False, default=list)
    custom_metadata = Column(JSON, nullable=False, default=dict)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    # university = relationship("University", back_populates="competitions")
    rounds = relationship("CompetitionRound", back_populates="competition", cascade="all, delete-orphan", order_by="CompetitionRound.round_number")
    # training_data = relationship("TrainingDataPoint", back_populates="competition", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Competition(id={self.id}, name={self.name}, type={self.competition_type}, status={self.status})>"


class CompetitionRound(Base):
    """
    Individual round within a competition.
    
    Tracks actions, scores, and outcomes for each round.
    """
    __tablename__ = "competition_rounds"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    competition_id = Column(String, ForeignKey("competitions.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Round info
    round_number = Column(Integer, nullable=False)
    round_name = Column(String(255), nullable=True)
    
    # Actions
    agent_actions = Column(JSON, nullable=False, default=dict)  # {agent_id: action_data}
    
    # Scores
    agent_scores = Column(JSON, nullable=False, default=dict)  # {agent_id: score}
    score_breakdown = Column(JSON, nullable=False, default=dict)  # Detailed scoring
    
    # Results
    round_winner_id = Column(String, nullable=True)
    
    # Timing
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    duration_seconds = Column(Float, nullable=True)
    
    # Training data
    training_data_points = Column(Integer, nullable=False, default=0)
    
    # Metadata
    custom_metadata = Column(JSON, nullable=False, default=dict)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    competition = relationship("Competition", back_populates="rounds")

    def __repr__(self):
        return f"<CompetitionRound(id={self.id}, competition={self.competition_id}, round={self.round_number})>"


class Leaderboard(Base):
    """
    Leaderboard for tracking agent rankings.
    
    Can be university-specific or global.
    """
    __tablename__ = "leaderboards"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    university_id = Column(String, ForeignKey("universities.id", ondelete="CASCADE"), nullable=True, index=True)  # NULL for global
    
    # Leaderboard info
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    
    # Configuration
    leaderboard_type = Column(String(50), nullable=False)  # "elo", "points", "wins", "custom"
    challenge_category = Column(String(50), nullable=True, index=True)  # Filter by category
    time_period = Column(String(50), nullable=True)  # "all_time", "monthly", "weekly", "daily"
    
    # Status
    is_active = Column(Boolean, nullable=False, default=True)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    rankings = relationship("LeaderboardRanking", back_populates="leaderboard", cascade="all, delete-orphan", order_by="LeaderboardRanking.rank")

    def __repr__(self):
        return f"<Leaderboard(id={self.id}, name={self.name}, type={self.leaderboard_type})>"


class LeaderboardRanking(Base):
    """
    Individual agent ranking on a leaderboard.
    """
    __tablename__ = "leaderboard_rankings"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    leaderboard_id = Column(String, ForeignKey("leaderboards.id", ondelete="CASCADE"), nullable=False, index=True)
    agent_id = Column(String, nullable=False, index=True)
    
    # Ranking
    rank = Column(Integer, nullable=False)
    previous_rank = Column(Integer, nullable=True)
    
    # Scores
    score = Column(Float, nullable=False)  # Elo rating, points, etc.
    wins = Column(Integer, nullable=False, default=0)
    losses = Column(Integer, nullable=False, default=0)
    draws = Column(Integer, nullable=False, default=0)
    total_matches = Column(Integer, nullable=False, default=0)
    
    # Performance metrics
    win_rate = Column(Float, nullable=True)  # 0.0-1.0
    average_score = Column(Float, nullable=True)
    peak_score = Column(Float, nullable=True)
    
    # Metadata
    last_match_at = Column(DateTime(timezone=True), nullable=True)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    leaderboard = relationship("Leaderboard", back_populates="rankings")

    def __repr__(self):
        return f"<LeaderboardRanking(agent={self.agent_id}, rank={self.rank}, score={self.score})>"


# Indexes
Index("idx_competition_university_status", Competition.university_id, Competition.status)
Index("idx_competition_type_category", Competition.competition_type, Competition.challenge_category)
Index("idx_competition_scheduled", Competition.scheduled_start, Competition.status)
Index("idx_round_competition", CompetitionRound.competition_id, CompetitionRound.round_number)
Index("idx_leaderboard_university_active", Leaderboard.university_id, Leaderboard.is_active)
Index("idx_ranking_leaderboard_rank", LeaderboardRanking.leaderboard_id, LeaderboardRanking.rank)
Index("idx_ranking_agent", LeaderboardRanking.agent_id, LeaderboardRanking.leaderboard_id, unique=True)


# Pydantic Schemas
class CompetitionCreate(BaseModel):
    """Schema for creating a competition"""
    university_id: str
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    competition_type: CompetitionType
    challenge_category: ChallengeCategory
    participant_ids: List[str] = Field(default_factory=list)
    team_1_ids: Optional[List[str]] = None
    team_2_ids: Optional[List[str]] = None
    max_participants: Optional[int] = Field(None, ge=2, le=100)
    rules: Dict[str, Any] = Field(default_factory=dict)
    scoring_config: Dict[str, Any] = Field(default_factory=dict)
    time_limit_seconds: Optional[int] = Field(None, ge=1)
    max_rounds: Optional[int] = Field(None, ge=1, le=100)
    scheduled_start: Optional[datetime] = None
    scheduled_end: Optional[datetime] = None
    tags: List[str] = Field(default_factory=list)
    custom_metadata: Dict[str, Any] = Field(default_factory=dict)


class CompetitionUpdate(BaseModel):
    """Schema for updating a competition"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    status: Optional[CompetitionStatus] = None
    participant_ids: Optional[List[str]] = None
    scheduled_start: Optional[datetime] = None
    scheduled_end: Optional[datetime] = None
    tags: Optional[List[str]] = None
    custom_metadata: Optional[Dict[str, Any]] = None


class CompetitionResponse(BaseModel):
    """Schema for competition response"""
    id: str
    university_id: str
    name: str
    description: Optional[str]
    competition_type: str
    challenge_category: str
    participant_ids: List[str]
    team_1_ids: Optional[List[str]]
    team_2_ids: Optional[List[str]]
    max_participants: Optional[int]
    rules: Dict[str, Any]
    scoring_config: Dict[str, Any]
    time_limit_seconds: Optional[int]
    max_rounds: Optional[int]
    scheduled_start: Optional[datetime]
    scheduled_end: Optional[datetime]
    actual_start: Optional[datetime]
    actual_end: Optional[datetime]
    status: str
    winner_id: Optional[str]
    winner_team_ids: Optional[List[str]]
    final_scores: Dict[str, float]
    rankings: List[str]
    training_data_collected: int
    data_quality_score: Optional[float]
    tags: List[str]
    custom_metadata: Dict[str, Any]
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True

