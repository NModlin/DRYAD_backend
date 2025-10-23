# app/database/models_university.py
# Unified University System Database Models
# Combines comprehensive plan's structure with UniAugment's quality metrics

from sqlalchemy import Column, String, Text, Integer, Float, Boolean, JSON, DateTime, ForeignKey, CheckConstraint
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database.database import Base
import uuid


class University(Base):
    """University instances with multi-tenant isolation"""
    __tablename__ = "universities"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False)
    description = Column(Text)
    
    # Multi-tenant context (reusing existing DRYAD architecture)
    owner_user_id = Column(String, ForeignKey("users.id"), nullable=False)
    client_app_id = Column(String, ForeignKey("client_applications.id"))
    tenant_id = Column(String)
    organization_id = Column(String, ForeignKey("organizations.id"))
    
    # Configuration and limits (comprehensive plan + UniAugment enhancements)
    settings = Column(JSON, default=lambda: {
        "max_agents": 100,
        "max_concurrent_competitions": 10,
        "data_retention_days": 365,
        "privacy_level": "strict",
        "training_data_sharing": False,  # UniAugment feature
        "isolation_level": "strict"
    })
    
    # Resource quotas (comprehensive plan)
    max_agents = Column(Integer, default=100)
    max_concurrent_competitions = Column(Integer, default=10)
    storage_quota_mb = Column(Integer, default=1024)
    
    # Status and timestamps
    status = Column(String(50), default="active")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    last_activity_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    agents = relationship("UniversityAgent", back_populates="university", cascade="all, delete-orphan")
    curriculum_paths = relationship("CurriculumPath", back_populates="university", cascade="all, delete-orphan")
    competitions = relationship("Competition", back_populates="university", cascade="all, delete-orphan")
    training_data_collections = relationship("TrainingDataCollection", back_populates="university", cascade="all, delete-orphan")
    improvement_proposals = relationship("ImprovementProposal", back_populates="university", cascade="all, delete-orphan")
    
    # Constraints
    __table_args__ = (
        CheckConstraint("status IN ('active', 'suspended', 'archived')", name="ck_university_status"),
        CheckConstraint("max_agents > 0", name="ck_university_max_agents"),
        CheckConstraint("max_concurrent_competitions > 0", name="ck_university_max_competitions"),
    )


class UniversityAgent(Base):
    """AI agents within university instances"""
    __tablename__ = "university_agents"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    university_id = Column(String, ForeignKey("universities.id"), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    
    # Agent configuration and type
    agent_type = Column(String(100), nullable=False)
    configuration = Column(JSON, nullable=False)
    specialization = Column(String(100))
    
    # Training state and progression
    current_curriculum_path_id = Column(String, ForeignKey("curriculum_paths.id"))
    current_curriculum_level_id = Column(String, ForeignKey("curriculum_levels.id"))
    current_challenge_index = Column(Integer, default=0)
    
    # Competency metrics
    competency_score = Column(Float, default=0.0)
    training_hours = Column(Float, default=0.0)
    training_data_collected = Column(Integer, default=0)
    
    # Competition performance (comprehensive plan + UniAugment enhancements)
    competition_wins = Column(Integer, default=0)
    competition_losses = Column(Integer, default=0)
    competition_draws = Column(Integer, default=0)
    average_score = Column(Float, default=0.0)
    highest_score = Column(Float, default=0.0)
    elo_rating = Column(Float, default=1000.0)  # UniAugment Elo system
    
    # Status and timestamps
    status = Column(String(50), default="active")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    last_trained_at = Column(DateTime(timezone=True))
    last_competed_at = Column(DateTime(timezone=True))
    
    # Relationships
    university = relationship("University", back_populates="agents")
    current_curriculum_path = relationship("CurriculumPath", foreign_keys=[current_curriculum_path_id])
    current_curriculum_level = relationship("CurriculumLevel", foreign_keys=[current_curriculum_level_id])
    progress_records = relationship("AgentProgress", back_populates="agent", cascade="all, delete-orphan")
    competition_participations = relationship("CompetitionParticipant", back_populates="agent", cascade="all, delete-orphan")
    training_data = relationship("TrainingDataCollection", back_populates="agent", cascade="all, delete-orphan")
    
    # Constraints
    __table_args__ = (
        CheckConstraint("agent_type IN ('student', 'instructor', 'researcher', 'specialist')", name="ck_agent_type"),
        CheckConstraint("status IN ('active', 'training', 'competing', 'idle', 'archived')", name="ck_agent_status"),
        CheckConstraint("competency_score >= 0.0 AND competency_score <= 1.0", name="ck_agent_competency"),
    )


class CurriculumPath(Base):
    """Structured learning paths"""
    __tablename__ = "curriculum_paths"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    university_id = Column(String, ForeignKey("universities.id"), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    
    # Path configuration
    difficulty_level = Column(String(50), default="beginner")
    estimated_duration_hours = Column(Integer, default=40)
    prerequisites = Column(JSON, default=lambda: [])
    
    # Metadata
    version = Column(String(20), default="1.0.0")
    tags = Column(JSON, default=lambda: [])
    is_public = Column(Boolean, default=False)
    
    # Status
    status = Column(String(50), default="active")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    university = relationship("University", back_populates="curriculum_paths")
    levels = relationship("CurriculumLevel", back_populates="curriculum_path", cascade="all, delete-orphan")
    agents = relationship("UniversityAgent", back_populates="current_curriculum_path", foreign_keys="UniversityAgent.current_curriculum_path_id")
    
    # Constraints
    __table_args__ = (
        CheckConstraint("difficulty_level IN ('beginner', 'intermediate', 'advanced', 'expert')", name="ck_path_difficulty"),
        CheckConstraint("status IN ('active', 'draft', 'archived')", name="ck_path_status"),
        CheckConstraint("estimated_duration_hours > 0", name="ck_path_duration"),
    )


class CurriculumLevel(Base):
    """Individual levels within curriculum paths"""
    __tablename__ = "curriculum_levels"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    curriculum_path_id = Column(String, ForeignKey("curriculum_paths.id"), nullable=False)
    level_number = Column(Integer, nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    
    # Learning objectives and content
    learning_objectives = Column(JSON, nullable=False)
    theoretical_content = Column(Text)
    practical_exercises = Column(JSON)
    
    # Challenge definitions
    challenges = Column(JSON, nullable=False)
    challenge_count = Column(Integer, default=0)
    passing_score = Column(Float, default=0.7)
    time_limit_minutes = Column(Integer, default=60)
    
    # Prerequisites
    required_competency_score = Column(Float, default=0.0)
    prerequisite_level_ids = Column(JSON, default=lambda: [])
    
    # Metadata
    tags = Column(JSON, default=lambda: [])
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    curriculum_path = relationship("CurriculumPath", back_populates="levels")
    agents = relationship("UniversityAgent", back_populates="current_curriculum_level", foreign_keys="UniversityAgent.current_curriculum_level_id")
    progress_records = relationship("AgentProgress", back_populates="curriculum_level", cascade="all, delete-orphan")
    
    # Constraints
    __table_args__ = (
        CheckConstraint("level_number > 0", name="ck_level_number"),
        CheckConstraint("passing_score >= 0.0 AND passing_score <= 1.0", name="ck_level_passing_score"),
        CheckConstraint("time_limit_minutes > 0", name="ck_level_time_limit"),
        CheckConstraint("challenge_count >= 0", name="ck_level_challenge_count"),
    )


class AgentProgress(Base):
    """Detailed progress tracking for each agent"""
    __tablename__ = "agent_progress"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    agent_id = Column(String, ForeignKey("university_agents.id"), nullable=False)
    curriculum_level_id = Column(String, ForeignKey("curriculum_levels.id"), nullable=False)
    
    # Progress state
    current_challenge_index = Column(Integer, default=0)
    challenges_completed = Column(Integer, default=0)
    total_challenges = Column(Integer, nullable=False)
    
    # Performance metrics
    current_score = Column(Float, default=0.0)
    best_score = Column(Float, default=0.0)
    average_score = Column(Float, default=0.0)
    time_spent_minutes = Column(Integer, default=0)
    
    # Status and completion
    status = Column(String(50), default="not_started")
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    last_activity_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Detailed challenge results
    challenge_results = Column(JSON, default=lambda: [])
    
    # Relationships
    agent = relationship("UniversityAgent", back_populates="progress_records")
    curriculum_level = relationship("CurriculumLevel", back_populates="progress_records")
    
    # Constraints
    __table_args__ = (
        CheckConstraint("status IN ('not_started', 'in_progress', 'completed', 'failed')", name="ck_progress_status"),
        CheckConstraint("current_challenge_index >= 0", name="ck_progress_challenge_index"),
        CheckConstraint("challenges_completed >= 0", name="ck_progress_completed"),
        CheckConstraint("total_challenges > 0", name="ck_progress_total_challenges"),
    )


class Competition(Base):
    """Competition instances"""
    __tablename__ = "competitions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    university_id = Column(String, ForeignKey("universities.id"), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    
    # Competition configuration
    competition_type = Column(String(100), nullable=False)
    rules = Column(JSON, nullable=False)
    benchmark_id = Column(String(255))
    evaluation_config = Column(JSON, nullable=False)
    
    # Scheduling
    scheduled_start = Column(DateTime(timezone=True))
    scheduled_end = Column(DateTime(timezone=True))
    actual_start = Column(DateTime(timezone=True))
    actual_end = Column(DateTime(timezone=True))
    
    # Status
    status = Column(String(50), default="scheduled")
    max_participants = Column(Integer, default=10)
    
    # Results
    winner_agent_id = Column(String, ForeignKey("university_agents.id"))
    results_published = Column(Boolean, default=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    university = relationship("University", back_populates="competitions")
    winner_agent = relationship("UniversityAgent", foreign_keys=[winner_agent_id])
    participants = relationship("CompetitionParticipant", back_populates="competition", cascade="all, delete-orphan")
    matches = relationship("CompetitionMatch", back_populates="competition", cascade="all, delete-orphan")
    
    # Constraints
    __table_args__ = (
        CheckConstraint("competition_type IN ('solo', 'head_to_head', 'tournament', 'challenge')", name="ck_competition_type"),
        CheckConstraint("status IN ('scheduled', 'active', 'completed', 'cancelled')", name="ck_competition_status"),
        CheckConstraint("max_participants > 0", name="ck_competition_max_participants"),
    )


class CompetitionParticipant(Base):
    """Agent participation in competitions"""
    __tablename__ = "competition_participants"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    competition_id = Column(String, ForeignKey("competitions.id"), nullable=False)
    agent_id = Column(String, ForeignKey("university_agents.id"), nullable=False)
    
    # Participation details
    participant_type = Column(String(50), default="competitor")
    seed_ranking = Column(Integer)
    
    # Performance metrics
    final_score = Column(Float)
    ranking = Column(Integer)
    execution_time_ms = Column(Integer)
    
    # Status
    status = Column(String(50), default="registered")
    joined_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True))
    
    # Relationships
    competition = relationship("Competition", back_populates="participants")
    agent = relationship("UniversityAgent", back_populates="competition_participations")
    matches_as_participant1 = relationship("CompetitionMatch", foreign_keys="CompetitionMatch.participant1_id", back_populates="participant1")
    matches_as_participant2 = relationship("CompetitionMatch", foreign_keys="CompetitionMatch.participant2_id", back_populates="participant2")
    
    # Constraints
    __table_args__ = (
        CheckConstraint("participant_type IN ('competitor', 'observer', 'judge')", name="ck_participant_type"),
        CheckConstraint("status IN ('registered', 'active', 'completed', 'disqualified')", name="ck_participant_status"),
    )


class CompetitionMatch(Base):
    """Individual matches within competitions"""
    __tablename__ = "competition_matches"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    competition_id = Column(String, ForeignKey("competitions.id"), nullable=False)
    match_number = Column(Integer, nullable=False)
    
    # Participants
    participant1_id = Column(String, ForeignKey("competition_participants.id"), nullable=False)
    participant2_id = Column(String, ForeignKey("competition_participants.id"))
    
    # Match details
    match_config = Column(JSON, nullable=False)
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    
    # Results
    participant1_score = Column(Float)
    participant2_score = Column(Float)
    winner_participant_id = Column(String, ForeignKey("competition_participants.id"))
    
    # Status
    status = Column(String(50), default="scheduled")
    
    # Evaluation data
    evaluation_run_id = Column(String(255))
    detailed_results = Column(JSON)
    
    # Relationships
    competition = relationship("Competition", back_populates="matches")
    participant1 = relationship("CompetitionParticipant", foreign_keys=[participant1_id], back_populates="matches_as_participant1")
    participant2 = relationship("CompetitionParticipant", foreign_keys=[participant2_id], back_populates="matches_as_participant2")
    winner = relationship("CompetitionParticipant", foreign_keys=[winner_participant_id])
    
    # Constraints
    __table_args__ = (
        CheckConstraint("status IN ('scheduled', 'active', 'completed', 'cancelled')", name="ck_match_status"),
        CheckConstraint("match_number > 0", name="ck_match_number"),
    )


class TrainingDataCollection(Base):
    """Collection of training data from agent activities"""
    __tablename__ = "training_data_collections"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    university_id = Column(String, ForeignKey("universities.id"), nullable=False)
    agent_id = Column(String, ForeignKey("university_agents.id"), nullable=False)
    
    # Data source
    source_type = Column(String(100), nullable=False)
    source_id = Column(String(36))
    
    # Data content
    data_type = Column(String(100), nullable=False)
    raw_data = Column(JSON, nullable=False)
    processed_data = Column(JSON)
    metadata = Column(JSON)
    
    # Quality metrics (UniAugment enhancements)
    quality_score = Column(Float, default=0.0)
    completeness_score = Column(Float, default=0.0)
    consistency_score = Column(Float, default=0.0)
    validity_score = Column(Float, default=0.0)
    validation_status = Column(String(50), default="pending")
    
    # Privacy and sharing
    privacy_level = Column(String(50), default="private")
    anonymized = Column(Boolean, default=False)
    
    collected_at = Column(DateTime(timezone=True), server_default=func.now())
    validated_at = Column(DateTime(timezone=True))
    
    # Relationships
    university = relationship("University", back_populates="training_data_collections")
    agent = relationship("UniversityAgent", back_populates="training_data")
    improvement_proposals = relationship("ImprovementProposal", back_populates="source_data_collection")
    
    # Constraints
    __table_args__ = (
        CheckConstraint("source_type IN ('competition', 'training', 'evaluation', 'interaction')", name="ck_training_source_type"),
        CheckConstraint("data_type IN ('conversation', 'reasoning', 'tool_use', 'problem_solving')", name="ck_training_data_type"),
        CheckConstraint("validation_status IN ('pending', 'validated', 'rejected', 'anonymized')", name="ck_training_validation_status"),
        CheckConstraint("privacy_level IN ('private', 'shared', 'public')", name="ck_training_privacy_level"),
        CheckConstraint("quality_score >= 0.0 AND quality_score <= 1.0", name="ck_training_quality"),
    )


class ImprovementProposal(Base):
    """Improvement proposals generated from training data"""
    __tablename__ = "improvement_proposals"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    university_id = Column(String, ForeignKey("universities.id"), nullable=False)
    
    # Proposal source
    generated_by = Column(String(100), default="professor_agent")
    source_data_collection_id = Column(String, ForeignKey("training_data_collections.id"))
    
    # Proposal content
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    implementation_details = Column(Text)
    expected_improvement = Column(Float)
    
    # Validation
    validation_results = Column(JSON)
    validation_status = Column(String(50), default="pending")
    validated_by = Column(String(255))
    validated_at = Column(DateTime(timezone=True))
    
    # Implementation
    implementation_status = Column(String(50), default="not_started")
    implemented_at = Column(DateTime(timezone=True))
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    university = relationship("University", back_populates="improvement_proposals")
    source_data_collection = relationship("TrainingDataCollection", back_populates="improvement_proposals")
    
    # Constraints
    __table_args__ = (
        CheckConstraint("generated_by IN ('professor_agent', 'human', 'system')", name="ck_proposal_generated_by"),
        CheckConstraint("validation_status IN ('pending', 'approved', 'rejected', 'implemented')", name="ck_proposal_validation_status"),
        CheckConstraint("implementation_status IN ('not_started', 'in_progress', 'completed', 'failed')", name="ck_proposal_implementation_status"),
    )


# Achievement and gamification models (UniAugment enhancements)
class Achievement(Base):
    """Gamification achievements for agents"""
    __tablename__ = "achievements"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False)
    description = Column(Text)
    category = Column(String(100))
    difficulty = Column(String(50), default="easy")
    points = Column(Integer, default=10)
    
    # Achievement criteria
    criteria = Column(JSON, nullable=False)
    required_count = Column(Integer, default=1)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Constraints
    __table_args__ = (
        CheckConstraint("difficulty IN ('easy', 'medium', 'hard', 'expert')", name="ck_achievement_difficulty"),
        CheckConstraint("points > 0", name="ck_achievement_points"),
        CheckConstraint("required_count > 0", name="ck_achievement_required_count"),
    )


class AgentAchievement(Base):
    """Agent achievement tracking"""
    __tablename__ = "agent_achievements"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    agent_id = Column(String, ForeignKey("university_agents.id"), nullable=False)
    achievement_id = Column(String, ForeignKey("achievements.id"), nullable=False)
    
    earned_at = Column(DateTime(timezone=True), server_default=func.now())
    progress = Column(Integer, default=0)
    is_completed = Column(Boolean, default=False)
    
    # Relationships
    agent = relationship("UniversityAgent")
    achievement = relationship("Achievement")
    
    # Constraints
    __table_args__ = (
        CheckConstraint("progress >= 0", name="ck_agent_achievement_progress"),
    )