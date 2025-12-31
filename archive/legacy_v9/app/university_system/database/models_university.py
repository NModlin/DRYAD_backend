"""
University System Database Models

Defines the database schema for the university system including:
- University entities and agent management
- Training data collection and validation
- Improvement proposals and implementation tracking
- Achievement and gamification system
- Curriculum and progression tracking
"""

from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, Text, JSON, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.university_system.database.database import Base

class University(Base):
    """University entity representing an educational institution"""
    __tablename__ = "universities"
    
    id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)
    description = Column(Text)
    owner_user_id = Column(String, nullable=False)
    client_app_id = Column(String)
    tenant_id = Column(String)
    organization_id = Column(String)
    settings = Column(JSON, default=dict)
    isolation_level = Column(String, default="standard")
    max_agents = Column(Integer, default=100)
    max_concurrent_competitions = Column(Integer, default=10)
    storage_quota_mb = Column(Integer, default=1024)
    primary_specialization = Column(String)
    secondary_specializations = Column(JSON, default=list)
    status = Column(String, default="active")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    last_activity_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    total_agents = Column(Integer, default=0)
    active_agents = Column(Integer, default=0)
    total_competitions = Column(Integer, default=0)
    total_training_data_points = Column(Integer, default=0)
    tags = Column(JSON, default=list)
    custom_metadata = Column(JSON, default=dict)

class UniversityAgent(Base):
    """University agent with detailed metrics and tracking"""
    __tablename__ = "university_agents"
    
    id = Column(String, primary_key=True, index=True)
    university_id = Column(String, ForeignKey("universities.id"), nullable=False, index=True)
    name = Column(String, nullable=False, index=True)
    agent_type = Column(String, default="student")  # student, professor, researcher, administrator
    status = Column(String, default="active")  # active, inactive, suspended
    specialization = Column(String)
    competency_score = Column(Float, default=0.0)
    training_hours = Column(Float, default=0.0)
    training_data_collected = Column(Integer, default=0)
    competition_wins = Column(Integer, default=0)
    competition_losses = Column(Integer, default=0)
    competition_draws = Column(Integer, default=0)
    average_score = Column(Float, default=0.0)
    highest_score = Column(Float, default=0.0)
    elo_rating = Column(Integer, default=1000)
    configuration = Column(JSON, default=dict)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    last_competed_at = Column(DateTime)
    current_curriculum_id = Column(String, ForeignKey("curriculum_paths.id"))
    
    # Relationships
    university = relationship("University", backref="agents")
    current_curriculum = relationship("CurriculumPath", backref="current_agents")

class CurriculumPath(Base):
    """Curriculum path for agent progression"""
    __tablename__ = "curriculum_paths"
    
    id = Column(String, primary_key=True, index=True)
    university_id = Column(String, ForeignKey("universities.id"), nullable=False, index=True)
    name = Column(String, nullable=False, index=True)
    description = Column(Text)
    difficulty_level = Column(String, default="beginner")  # beginner, intermediate, advanced, expert
    prerequisites = Column(JSON, default=list)
    specialization = Column(String)
    skill_tree_id = Column(String)
    version = Column(String, default="1.0.0")
    status = Column(String, default="active")  # active, draft, archived
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    total_enrollments = Column(Integer, default=0)
    total_completions = Column(Integer, default=0)
    average_completion_time_hours = Column(Float, default=0.0)
    average_score = Column(Float, default=0.0)
    tags = Column(JSON, default=list)
    custom_metadata = Column(JSON, default=dict)
    
    # Relationships
    university = relationship("University", backref="curriculum_paths")

class CurriculumLevel(Base):
    """Individual level within a curriculum path"""
    __tablename__ = "curriculum_levels"
    
    id = Column(String, primary_key=True, index=True)
    curriculum_path_id = Column(String, ForeignKey("curriculum_paths.id"), nullable=False, index=True)
    level_number = Column(Integer, nullable=False)
    name = Column(String, nullable=False, index=True)
    description = Column(Text)
    learning_objectives = Column(JSON, default=list)
    challenges = Column(JSON, default=list)
    estimated_duration_hours = Column(Float, default=1.0)
    prerequisites = Column(JSON, default=list)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Relationships
    curriculum_path = relationship("CurriculumPath", backref="levels")

class AgentProgress(Base):
    """Agent progress through curriculum levels"""
    __tablename__ = "agent_progress"
    
    id = Column(String, primary_key=True, index=True)
    agent_id = Column(String, ForeignKey("university_agents.id"), nullable=False, index=True)
    curriculum_level_id = Column(String, ForeignKey("curriculum_levels.id"), nullable=False, index=True)
    status = Column(String, default="not_started")  # not_started, in_progress, completed
    current_challenge_index = Column(Integer, default=0)
    total_challenges = Column(Integer, default=0)
    challenges_completed = Column(Integer, default=0)
    current_score = Column(Float, default=0.0)
    best_score = Column(Float, default=0.0)
    average_score = Column(Float, default=0.0)
    time_spent_minutes = Column(Integer, default=0)
    challenge_results = Column(JSON, default=list)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    last_activity_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Relationships
    agent = relationship("UniversityAgent", backref="progress_records")
    curriculum_level = relationship("CurriculumLevel", backref="agent_progress")

class TrainingDataCollection(Base):
    """Training data collected from agent activities"""
    __tablename__ = "training_data_collections"
    
    id = Column(String, primary_key=True, index=True)
    university_id = Column(String, ForeignKey("universities.id"), nullable=False, index=True)
    agent_id = Column(String, ForeignKey("university_agents.id"), nullable=False, index=True)
    source_type = Column(String, nullable=False)  # competition, curriculum, manual, external
    source_id = Column(String)  # ID of the source (competition_id, curriculum_level_id, etc.)
    data_type = Column(String, nullable=False)  # text, image, audio, video, multimodal
    raw_data = Column(JSON, nullable=False)
    data_metadata = Column(JSON, default=dict)
    validation_status = Column(String, default="pending")  # pending, validated, rejected
    quality_score = Column(Float, default=0.0)
    completeness_score = Column(Float, default=0.0)
    consistency_score = Column(Float, default=0.0)
    validity_score = Column(Float, default=0.0)
    validation_results = Column(JSON, default=dict)
    validated_by = Column(String)
    validated_at = Column(DateTime)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Relationships
    university = relationship("University", backref="training_data_collections")
    agent = relationship("UniversityAgent", backref="training_data_collections")

class ImprovementProposal(Base):
    """Improvement proposals generated from training data analysis"""
    __tablename__ = "improvement_proposals"
    
    id = Column(String, primary_key=True, index=True)
    university_id = Column(String, ForeignKey("universities.id"), nullable=False, index=True)
    title = Column(String, nullable=False, index=True)
    description = Column(Text, nullable=False)
    generated_by = Column(String, default="professor_agent")  # professor_agent, system, human
    source_data_collection_id = Column(String, ForeignKey("training_data_collections.id"))
    implementation_details = Column(Text)
    expected_improvement = Column(Float)  # Expected improvement percentage (0.0 - 1.0)
    validation_status = Column(String, default="pending")  # pending, approved, rejected, needs_revision
    validation_results = Column(JSON, default=dict)
    validated_by = Column(String)
    validated_at = Column(DateTime)
    implementation_status = Column(String, default="not_started")  # not_started, in_progress, completed, failed, cancelled
    implemented_by = Column(String)
    implemented_at = Column(DateTime)
    actual_improvement = Column(Float)  # Actual improvement percentage after implementation
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Relationships
    university = relationship("University", backref="improvement_proposals")
    source_data_collection = relationship("TrainingDataCollection", backref="improvement_proposals")

class Achievement(Base):
    """Achievements for gamification and progression tracking"""
    __tablename__ = "achievements"
    
    id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)
    description = Column(Text, nullable=False)
    category = Column(String)  # curriculum, competition, training, special
    difficulty = Column(String, default="easy")  # easy, medium, hard, expert
    points = Column(Integer, default=10)
    criteria = Column(JSON, nullable=False)  # Criteria for earning the achievement
    required_count = Column(Integer, default=1)  # Number of times criteria must be met
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

class AgentAchievement(Base):
    """Association between agents and achievements with progress tracking"""
    __tablename__ = "agent_achievements"
    
    id = Column(String, primary_key=True, index=True)
    agent_id = Column(String, ForeignKey("university_agents.id"), nullable=False, index=True)
    achievement_id = Column(String, ForeignKey("achievements.id"), nullable=False, index=True)
    progress = Column(Integer, default=0)  # Current progress toward achievement
    is_completed = Column(Boolean, default=False)
    awarded_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Relationships
    agent = relationship("UniversityAgent", backref="achievements")
    achievement = relationship("Achievement", backref="agent_achievements")

# Additional models for competition system
class Competition(Base):
    """Competition entity for agent competitions"""
    __tablename__ = "competitions"
    
    id = Column(String, primary_key=True, index=True)
    university_id = Column(String, ForeignKey("universities.id"), nullable=False, index=True)
    name = Column(String, nullable=False, index=True)
    description = Column(Text)
    competition_type = Column(String, default="individual")  # individual, team, tournament
    challenge_category = Column(String, default="general")  # general, specific_skill, curriculum_based
    participant_ids = Column(JSON, default=list)
    team_1_ids = Column(JSON, default=list)
    team_2_ids = Column(JSON, default=list)
    max_participants = Column(Integer, default=10)
    rules = Column(JSON, default=dict)
    scoring_config = Column(JSON, default=dict)
    time_limit_seconds = Column(Integer, default=3600)
    max_rounds = Column(Integer, default=3)
    scheduled_start = Column(DateTime)
    scheduled_end = Column(DateTime)
    actual_start = Column(DateTime)
    actual_end = Column(DateTime)
    status = Column(String, default="scheduled")  # scheduled, in_progress, completed, cancelled
    winner_id = Column(String)
    final_scores = Column(JSON, default=dict)
    rankings = Column(JSON, default=list)
    training_data_collected = Column(Integer, default=0)
    tags = Column(JSON, default=list)
    custom_metadata = Column(JSON, default=dict)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Relationships
    university = relationship("University", backref="competitions")

class CompetitionRound(Base):
    """Individual round within a competition"""
    __tablename__ = "competition_rounds"
    
    id = Column(String, primary_key=True, index=True)
    competition_id = Column(String, ForeignKey("competitions.id"), nullable=False, index=True)
    round_number = Column(Integer, nullable=False)
    round_type = Column(String, default="standard")  # standard, elimination, final
    participants = Column(JSON, default=list)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    duration_seconds = Column(Integer)
    round_winner_id = Column(String)
    training_data_points = Column(Integer, default=0)
    round_results = Column(JSON, default=dict)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Relationships
    competition = relationship("Competition", backref="rounds")

class Leaderboard(Base):
    """Leaderboard for tracking agent rankings"""
    __tablename__ = "leaderboards"
    
    id = Column(String, primary_key=True, index=True)
    university_id = Column(String, ForeignKey("universities.id"), nullable=False, index=True)
    name = Column(String, nullable=False, index=True)
    leaderboard_type = Column(String, default="elo")  # elo, points, win_rate
    challenge_category = Column(String, default="general")
    rankings = Column(JSON, default=list)
    is_active = Column(Boolean, default=True)
    season_start = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    season_end = Column(DateTime)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Relationships
    university = relationship("University", backref="leaderboards")

# Skill Tree Models for Curriculum System
class SkillTree(Base):
    """Skill tree for organizing curriculum skills hierarchically"""
    __tablename__ = "skill_trees"
    
    id = Column(String, primary_key=True, index=True)
    university_id = Column(String, ForeignKey("universities.id"), nullable=False, index=True)
    name = Column(String, nullable=False, index=True)
    description = Column(Text)
    root_node_id = Column(String)  # ID of the root skill node
    status = Column(String, default="draft")  # draft, active, archived
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    total_nodes = Column(Integer, default=0)
    total_skills = Column(Integer, default=0)
    average_difficulty = Column(Float, default=0.0)
    tags = Column(JSON, default=list)
    custom_metadata = Column(JSON, default=dict)
    
    # Relationships
    university = relationship("University", backref="skill_trees")

class SkillNode(Base):
    """Individual skill node within a skill tree"""
    __tablename__ = "skill_nodes"
    
    id = Column(String, primary_key=True, index=True)
    skill_tree_id = Column(String, ForeignKey("skill_trees.id"), nullable=False, index=True)
    name = Column(String, nullable=False, index=True)
    description = Column(Text)
    parent_node_id = Column(String, ForeignKey("skill_nodes.id"))  # Self-referencing for hierarchy
    difficulty = Column(Integer, default=1)  # 1-10 scale
    prerequisites = Column(JSON, default=list)  # List of prerequisite skill node IDs
    learning_objectives = Column(JSON, default=list)
    estimated_duration_hours = Column(Float, default=1.0)
    order_index = Column(Integer, default=0)  # Order within parent
    skill_type = Column(String, default="conceptual")  # conceptual, practical, assessment
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Relationships
    skill_tree = relationship("SkillTree", backref="skill_nodes")
    parent = relationship("SkillNode", remote_side=[id], backref="children")

class SkillProgress(Base):
    """Agent progress tracking for individual skills"""
    __tablename__ = "skill_progress"
    
    id = Column(String, primary_key=True, index=True)
    agent_id = Column(String, ForeignKey("university_agents.id"), nullable=False, index=True)
    skill_node_id = Column(String, ForeignKey("skill_nodes.id"), nullable=False, index=True)
    status = Column(String, default="not_started")  # not_started, in_progress, completed, failed
    progress_percentage = Column(Float, default=0.0)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    score = Column(Float)  # Assessment score if applicable
    attempts = Column(Integer, default=0)
    time_spent_minutes = Column(Integer, default=0)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Relationships
    agent = relationship("UniversityAgent", backref="skill_progress")
    skill_node = relationship("SkillNode", backref="progress_records")

# Competition Participation Model
class CompetitionParticipant(Base):
    """Track agent participation in competitions"""
    __tablename__ = "competition_participants"
    
    id = Column(String, primary_key=True, index=True)
    competition_id = Column(String, ForeignKey("competitions.id"), nullable=False, index=True)
    agent_id = Column(String, ForeignKey("university_agents.id"), nullable=False, index=True)
    status = Column(String, default="active")  # active, withdrawn, disqualified
    score = Column(Float, default=0.0)
    rank = Column(Integer)  # Current rank in competition
    joined_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    last_updated = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    performance_metrics = Column(JSON, default=dict)
    training_data_generated = Column(Integer, default=0)
    
    # Relationships
    competition = relationship("Competition", backref="participants")
    agent = relationship("UniversityAgent", backref="competition_participations")

# ==================== Agent Memory Models ====================

class ConversationSession(Base):
    """Store conversational sessions and context for agent memory"""
    __tablename__ = "conversation_sessions"
    
    id = Column(String, primary_key=True, index=True)
    agent_id = Column(String, ForeignKey("university_agents.id"), nullable=False)
    session_type = Column(String, default="interaction")  # interaction, problem_solving, learning
    context_data = Column(JSON, default=dict)  # Persistent context
    conversation_history = Column(JSON, default=list)  # Chat messages
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Relationships
    agent = relationship("UniversityAgent", backref="conversation_sessions")

class LearningContext(Base):
    """Store agent learning experiences and insights for problem-solving memory"""
    __tablename__ = "learning_contexts"
    
    id = Column(String, primary_key=True, index=True)
    agent_id = Column(String, ForeignKey("university_agents.id"), nullable=False)
    context_type = Column(String)  # problem_solving, decision_making, skill_learning
    context_data = Column(JSON, nullable=False)  # Structured learning data
    success_patterns = Column(JSON, default=list)  # What worked
    failure_patterns = Column(JSON, default=list)  # What didn't work
    applicable_scenarios = Column(JSON, default=list)  # When to apply this learning
    confidence_score = Column(Float, default=0.0)  # How confident the agent is in this learning
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Relationships
    agent = relationship("UniversityAgent", backref="learning_contexts")

class KnowledgeEntity(Base):
    """Store semantic knowledge entities for agents"""
    __tablename__ = "knowledge_entities"
    
    id = Column(String, primary_key=True, index=True)
    agent_id = Column(String, ForeignKey("university_agents.id"), nullable=False)
    entity_type = Column(String)  # concept, fact, procedure, relationship
    entity_name = Column(String, nullable=False)
    entity_data = Column(JSON, nullable=False)
    connections = Column(JSON, default=list)  # Related entities
    confidence = Column(Float, default=0.0)  # Confidence in this knowledge
    source_context = Column(String)  # Where this knowledge came from
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Relationships
    agent = relationship("UniversityAgent", backref="knowledge_entities")

# ==================== Domain Expert Agent Models ====================

class DomainExpertProfile(Base):
    """Define specialized knowledge domains for agents"""
    __tablename__ = "domain_expert_profiles"
    
    id = Column(String, primary_key=True, index=True)
    agent_id = Column(String, ForeignKey("university_agents.id"), nullable=False)
    domain_name = Column(String, nullable=False, index=True)  # mathematics, physics, literature, etc.
    expertise_level = Column(String, default="intermediate")  # beginner, intermediate, advanced, expert
    specializations = Column(JSON, default=list)
    credentials = Column(JSON, default=list)
    knowledge_base = Column(JSON, default=dict)  # Structured knowledge
    teaching_style = Column(String, default="adaptive")  # Socratic, practical, theoretical, interactive, adaptive
    available_capabilities = Column(JSON, default=list)  # What they can teach/solve
    success_rate = Column(Float, default=0.0)  # Student success rate
    total_students_taught = Column(Integer, default=0)
    student_improvement_rate = Column(Float, default=0.0)  # Average improvement in student performance
    preferred_difficulty_levels = Column(JSON, default=list)  # Difficulty levels they work best with
    adaptive_learning_style = Column(String, default="mixed")  # visual, auditory, kinesthetic, mixed
    response_time_seconds = Column(Float, default=5.0)  # Average response time
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Relationships
    agent = relationship("UniversityAgent", backref="domain_expert_profiles")

class ExpertSession(Base):
    """Track tutoring sessions with expert agents"""
    __tablename__ = "expert_sessions"
    
    id = Column(String, primary_key=True, index=True)
    expert_agent_id = Column(String, ForeignKey("university_agents.id"), nullable=False)
    student_agent_id = Column(String, ForeignKey("university_agents.id"), nullable=False)
    domain = Column(String, nullable=False, index=True)
    topic = Column(String, nullable=False)
    session_type = Column(String, default="tutoring")  # tutoring, problem_solving, assessment, discussion
    learning_objectives = Column(JSON, default=list)
    methods_used = Column(JSON, default=list)  # Teaching methods employed
    student_outcomes = Column(JSON, default=dict)  # Results achieved
    difficulty_adaptations = Column(JSON, default=list)  # How difficulty was adjusted
    session_duration_minutes = Column(Integer)
    effectiveness_score = Column(Float, default=0.0)  # Session effectiveness rating
    student_satisfaction = Column(Float, default=0.0)  # Student satisfaction score
    concepts_mastered = Column(JSON, default=list)  # Concepts the student mastered
    areas_for_improvement = Column(JSON, default=list)  # Areas needing more work
    next_recommended_topics = Column(JSON, default=list)  # Suggested follow-up topics
    status = Column(String, default="active")  # active, completed, paused, cancelled
    started_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    completed_at = Column(DateTime)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Relationships
    expert_agent = relationship("UniversityAgent", foreign_keys=[expert_agent_id], backref="expert_sessions_as_expert")
    student_agent = relationship("UniversityAgent", foreign_keys=[student_agent_id], backref="expert_sessions_as_student")

class KnowledgeNode(Base):
    """Structured knowledge for domain experts"""
    __tablename__ = "knowledge_nodes"
    
    id = Column(String, primary_key=True, index=True)
    domain = Column(String, nullable=False, index=True)
    topic = Column(String, nullable=False, index=True)
    concept_name = Column(String, nullable=False)
    concept_data = Column(JSON, nullable=False)  # Detailed concept information
    status = Column(String, default="active", index=True)
    confidence_level = Column(Float, default=0.5)
    prerequisites = Column(JSON, default=list)  # Required prior knowledge
    learning_objectives = Column(JSON, default=list)
    examples = Column(JSON, default=list)
    common_misconceptions = Column(JSON, default=list)
    practice_problems = Column(JSON, default=list)
    difficulty_level = Column(String, default="intermediate")  # beginner, intermediate, advanced, expert
    estimated_learning_time_minutes = Column(Integer, default=30)
    difficulty_score = Column(Float, default=0.5)
    teaching_strategies = Column(JSON, default=list)  # Effective teaching methods for this concept
    assessment_criteria = Column(JSON, default=list)
    resources = Column(JSON, default=list)
    connections = Column(JSON, default=list)
    relationships = Column(JSON, default=list)
    related_concepts = Column(JSON, default=list)  # Connected concepts
    real_world_applications = Column(JSON, default=list)  # Practical applications
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Relationships


class TeachingMethod(Base):
    """Teaching methods and strategies for domain experts"""
    __tablename__ = "teaching_methods"
    
    id = Column(String, primary_key=True, index=True)
    domain = Column(String, nullable=False, index=True)
    method_name = Column(String, nullable=False)
    description = Column(Text)
    effectiveness_scores = Column(JSON, default=dict)  # Effectiveness for different learning styles
    difficulty_levels = Column(JSON, default=list)  # Difficulty levels this method works best for
    requirements = Column(JSON, default=dict)  # Required resources or conditions
    prerequisites = Column(JSON, default=list)  # Required prior knowledge
    estimated_time_minutes = Column(Integer, default=30)
    success_indicators = Column(JSON, default=list)  # How to measure success
    common_failures = Column(JSON, default=list)  # Common issues and how to handle them
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

class StudentLearningProfile(Base):
    """Detailed learning profiles for students"""
    __tablename__ = "student_learning_profiles"
    
    id = Column(String, primary_key=True, index=True)
    agent_id = Column(String, ForeignKey("university_agents.id"), nullable=False)
    domain = Column(String, nullable=False, index=True)
    learning_style = Column(String, default="visual")  # visual, auditory, kinesthetic, reading, mixed
    preferred_pace = Column(String, default="moderate")  # slow, moderate, fast
    attention_span_minutes = Column(Integer, default=45)
    motivation_factors = Column(JSON, default=list)  # What motivates this student
    learning_obstacles = Column(JSON, default=list)  # Known learning difficulties
    strengths = Column(JSON, default=list)  # Student strengths
    weaknesses = Column(JSON, default=list)  # Areas needing focus
    previous_methods_used = Column(JSON, default=list)  # Teaching methods that have worked/failed
    success_patterns = Column(JSON, default=list)  # What consistently works for this student
    failure_patterns = Column(JSON, default=list)  # What consistently doesn't work
    personality_factors = Column(JSON, default=dict)  # Learning personality traits
    environmental_preferences = Column(JSON, default=dict)  # Preferred learning environment
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Relationships
    agent = relationship("UniversityAgent", backref="learning_profiles")

class AdaptiveLearningPath(Base):
    """Adaptive learning paths based on student performance"""
    __tablename__ = "adaptive_learning_paths"
    
    id = Column(String, primary_key=True, index=True)
    student_agent_id = Column(String, ForeignKey("university_agents.id"), nullable=False)
    domain = Column(String, nullable=False, index=True)
    path_name = Column(String, nullable=False)
    current_position = Column(Integer, default=0)
    path_segments = Column(JSON, default=list)  # Ordered list of concepts/topics
    adaptation_history = Column(JSON, default=list)  # How the path has been adapted
    performance_milestones = Column(JSON, default=list)  # Key performance indicators
    difficulty_adjustments = Column(JSON, default=list)  # Historical difficulty changes
    alternative_routes = Column(JSON, default=list)  # Alternative paths tried
    success_rate = Column(Float, default=0.0)
    total_time_spent_hours = Column(Float, default=0.0)
    estimated_completion_hours = Column(Float, default=10.0)
    status = Column(String, default="active")  # active, paused, completed, failed
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Relationships
    student_agent = relationship("UniversityAgent", backref="adaptive_learning_paths")

# ==================== Multimodal Capability Models ====================

class MediaAsset(Base):
    """Store multimedia assets and their analysis"""
    __tablename__ = "media_assets"
    
    id = Column(String, primary_key=True, index=True)
    agent_id = Column(String, ForeignKey("university_agents.id"), nullable=False)
    asset_type = Column(String)  # image, audio, video, document, interactive
    asset_name = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    file_size = Column(Integer)
    content_type = Column(String, nullable=False)
    asset_metadata = Column(JSON, default=dict)
    analysis_results = Column(JSON, default=dict)  # AI analysis results
    accessibility_info = Column(JSON, default=dict)  # Alt text, captions, etc.
    usage_rights = Column(String, default="university")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    # Relationships
    agent = relationship("UniversityAgent", backref="media_assets")

class MultimodalInteraction(Base):
    """Track agent interactions with multimedia content"""
    __tablename__ = "multimodal_interactions"
    
    id = Column(String, primary_key=True, index=True)
    agent_id = Column(String, ForeignKey("university_agents.id"), nullable=False)
    asset_id = Column(String, ForeignKey("media_assets.id"), nullable=False)
    interaction_type = Column(String)  # view, analyze, transcribe, describe, generate
    interaction_data = Column(JSON, default=dict)  # Specific interaction details
    processing_time_ms = Column(Integer)
    success = Column(Boolean, default=True)
    feedback_quality = Column(Float, default=0.0)  # Quality of analysis/generation
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    # Relationships
    agent = relationship("UniversityAgent", backref="multimodal_interactions")
    asset = relationship("MediaAsset", backref="interactions")

class ContentGeneration(Base):
    """Track AI-generated multimedia content"""
    __tablename__ = "content_generation"
    
    id = Column(String, primary_key=True, index=True)
    agent_id = Column(String, ForeignKey("university_agents.id"), nullable=False)
    generation_type = Column(String)  # image, audio, video, text_description
    prompt = Column(Text, nullable=False)
    generated_content = Column(String)  # File path or base64
    quality_score = Column(Float, default=0.0)
    human_feedback = Column(JSON, default=dict)
    iterations = Column(Integer, default=1)
    processing_time_seconds = Column(Integer)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    # Relationships
    agent = relationship("UniversityAgent", backref="content_generations")

# ==================== Collaborative Agents Models ====================

class AgentCollaboration(Base):
    """Track collaboration between agents"""
    __tablename__ = "agent_collaborations"
    
    id = Column(String, primary_key=True, index=True)
    collaboration_type = Column(String)  # peer_tutoring, group_project, research_team, debate
    participating_agents = Column(JSON, default=list)  # List of agent IDs
    collaboration_leader_id = Column(String, ForeignKey("university_agents.id"))
    collaboration_goal = Column(Text, nullable=False)
    collaboration_methods = Column(JSON, default=list)  # Brainstorming, debate, consensus, etc.
    task_distribution = Column(JSON, default=dict)  # Who does what
    shared_resources = Column(JSON, default=list)  # Shared files, knowledge, tools
    progress_tracking = Column(JSON, default=dict)  # Progress by agent/task
    collaboration_outcomes = Column(JSON, default=dict)  # Results achieved
    effectiveness_score = Column(Float, default=0.0)
    started_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    completed_at = Column(DateTime)
    
    # Relationships
    leader = relationship("UniversityAgent", foreign_keys=[collaboration_leader_id], backref="leading_collaborations")

class KnowledgeSharing(Base):
    """Track knowledge sharing between agents"""
    __tablename__ = "knowledge_sharing"
    
    id = Column(String, primary_key=True, index=True)
    sharing_agent_id = Column(String, ForeignKey("university_agents.id"), nullable=False)
    receiving_agent_id = Column(String, ForeignKey("university_agents.id"), nullable=False)
    knowledge_type = Column(String)  # concept, method, insight, resource, skill
    knowledge_content = Column(JSON, nullable=False)
    sharing_context = Column(String)  # tutoring, collaboration, assignment, spontaneous
    comprehension_verified = Column(Boolean, default=False)
    feedback_quality = Column(Float, default=0.0)
    adoption_success = Column(Float, default=0.0)  # How well receiver used the knowledge
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    # Relationships
    sharing_agent = relationship("UniversityAgent", foreign_keys=[sharing_agent_id], backref="knowledge_shared")
    receiving_agent = relationship("UniversityAgent", foreign_keys=[receiving_agent_id], backref="knowledge_received")

class CollaborativeProject(Base):
    """Manage complex multi-agent projects"""
    __tablename__ = "collaborative_projects"
    
    id = Column(String, primary_key=True, index=True)
    project_name = Column(String, nullable=False)
    project_type = Column(String)  # research, development, analysis, creative, presentation
    project_description = Column(Text, nullable=False)
    team_agents = Column(JSON, default=list)
    project_lead_id = Column(String, ForeignKey("university_agents.id"))
    required_expertise = Column(JSON, default=list)
    project_phases = Column(JSON, default=list)  # Planned phases
    current_phase = Column(String, default="planning")
    deliverables = Column(JSON, default=list)
    milestones = Column(JSON, default=list)
    collaboration_tools_used = Column(JSON, default=list)
    project_status = Column(String, default="active")
    quality_assessment = Column(JSON, default=dict)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    # Relationships
    project_lead = relationship("UniversityAgent", foreign_keys=[project_lead_id], backref="leading_projects")