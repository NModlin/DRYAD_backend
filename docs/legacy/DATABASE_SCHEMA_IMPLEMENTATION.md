# University System Database Schema Implementation
## Detailed Database Design for Level 6 Agentic University

**Date**: October 22, 2025  
**Status**: Ready for Implementation  
**Target**: SQLAlchemy models with Alembic migrations

---

## Complete Database Schema

### Core University Tables

#### 1. University Instance Management
```sql
-- University instances with multi-tenant isolation
CREATE TABLE universities (
    id VARCHAR(36) PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    owner_user_id VARCHAR(255) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- Multi-tenant context (reusing existing DRYAD architecture)
    client_app_id VARCHAR(255) REFERENCES client_applications(id),
    tenant_id VARCHAR(255),
    organization_id VARCHAR(255) REFERENCES organizations(id),
    
    -- Configuration and limits
    settings JSON DEFAULT '{
        "max_agents": 100,
        "max_concurrent_competitions": 10,
        "data_retention_days": 365,
        "privacy_level": "strict"
    }',
    isolation_level VARCHAR(50) DEFAULT 'strict' CHECK (isolation_level IN ('strict', 'shared', 'collaborative')),
    
    -- Resource quotas
    max_agents INTEGER DEFAULT 100 CHECK (max_agents > 0),
    max_concurrent_competitions INTEGER DEFAULT 10 CHECK (max_concurrent_competitions > 0),
    storage_quota_mb INTEGER DEFAULT 1024 CHECK (storage_quota_mb > 0),
    
    -- Status and timestamps
    status VARCHAR(50) DEFAULT 'active' CHECK (status IN ('active', 'suspended', 'archived')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_activity_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Indexes for performance
    INDEX idx_universities_owner (owner_user_id),
    INDEX idx_universities_tenant (tenant_id),
    INDEX idx_universities_org (organization_id),
    INDEX idx_universities_status (status)
);
```

#### 2. University Agents
```sql
-- AI agents within university instances
CREATE TABLE university_agents (
    id VARCHAR(36) PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    university_id VARCHAR(36) NOT NULL REFERENCES universities(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    
    -- Agent configuration and type
    agent_type VARCHAR(100) NOT NULL CHECK (agent_type IN ('student', 'instructor', 'researcher', 'specialist')),
    configuration JSON NOT NULL, -- LLM config, tools, memory settings
    specialization VARCHAR(100), -- Optional specialization field
    
    -- Training state and progression
    current_curriculum_path_id VARCHAR(36) REFERENCES curriculum_paths(id),
    current_curriculum_level_id VARCHAR(36) REFERENCES curriculum_levels(id),
    current_challenge_index INTEGER DEFAULT 0,
    
    -- Competency metrics
    competency_score FLOAT DEFAULT 0.0 CHECK (competency_score >= 0.0 AND competency_score <= 1.0),
    training_hours FLOAT DEFAULT 0.0,
    training_data_collected INTEGER DEFAULT 0,
    
    -- Competition performance
    competition_wins INTEGER DEFAULT 0,
    competition_losses INTEGER DEFAULT 0,
    competition_draws INTEGER DEFAULT 0,
    average_score FLOAT DEFAULT 0.0,
    highest_score FLOAT DEFAULT 0.0,
    
    -- Status and timestamps
    status VARCHAR(50) DEFAULT 'active' CHECK (status IN ('active', 'training', 'competing', 'idle', 'archived')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_trained_at TIMESTAMP,
    last_competed_at TIMESTAMP,
    
    -- Indexes
    INDEX idx_agents_university (university_id),
    INDEX idx_agents_type (agent_type),
    INDEX idx_agents_competency (competency_score),
    INDEX idx_agents_status (status)
);
```

### Curriculum Engine Tables

#### 3. Curriculum Paths
```sql
-- Structured learning paths
CREATE TABLE curriculum_paths (
    id VARCHAR(36) PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    university_id VARCHAR(36) NOT NULL REFERENCES universities(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    
    -- Path configuration
    difficulty_level VARCHAR(50) DEFAULT 'beginner' CHECK (difficulty_level IN ('beginner', 'intermediate', 'advanced', 'expert')),
    estimated_duration_hours INTEGER DEFAULT 40 CHECK (estimated_duration_hours > 0),
    prerequisites JSON DEFAULT '[]', -- Array of required path IDs or competency scores
    
    -- Metadata
    version VARCHAR(20) DEFAULT '1.0.0',
    tags JSON DEFAULT '[]',
    is_public BOOLEAN DEFAULT FALSE,
    
    -- Status
    status VARCHAR(50) DEFAULT 'active' CHECK (status IN ('active', 'draft', 'archived')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_paths_university (university_id),
    INDEX idx_paths_difficulty (difficulty_level)
);
```

#### 4. Curriculum Levels
```sql
-- Individual levels within curriculum paths
CREATE TABLE curriculum_levels (
    id VARCHAR(36) PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    curriculum_path_id VARCHAR(36) NOT NULL REFERENCES curriculum_paths(id) ON DELETE CASCADE,
    level_number INTEGER NOT NULL CHECK (level_number > 0),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    
    -- Learning objectives and content
    learning_objectives JSON NOT NULL, -- Array of objectives
    theoretical_content TEXT, -- Textual learning material
    practical_exercises JSON, -- Array of exercise definitions
    
    -- Challenge definitions
    challenges JSON NOT NULL, -- Array of challenge configurations
    challenge_count INTEGER DEFAULT 0,
    passing_score FLOAT DEFAULT 0.7 CHECK (passing_score >= 0.0 AND passing_score <= 1.0),
    time_limit_minutes INTEGER DEFAULT 60 CHECK (time_limit_minutes > 0),
    
    -- Prerequisites
    required_competency_score FLOAT DEFAULT 0.0,
    prerequisite_level_ids JSON DEFAULT '[]',
    
    -- Metadata
    tags JSON DEFAULT '[]',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE (curriculum_path_id, level_number),
    INDEX idx_levels_path (curriculum_path_id),
    INDEX idx_levels_number (level_number)
);
```

#### 5. Agent Progress Tracking
```sql
-- Detailed progress tracking for each agent
CREATE TABLE agent_progress (
    id VARCHAR(36) PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    agent_id VARCHAR(36) NOT NULL REFERENCES university_agents(id) ON DELETE CASCADE,
    curriculum_level_id VARCHAR(36) NOT NULL REFERENCES curriculum_levels(id),
    
    -- Progress state
    current_challenge_index INTEGER DEFAULT 0,
    challenges_completed INTEGER DEFAULT 0,
    total_challenges INTEGER NOT NULL,
    
    -- Performance metrics
    current_score FLOAT DEFAULT 0.0,
    best_score FLOAT DEFAULT 0.0,
    average_score FLOAT DEFAULT 0.0,
    time_spent_minutes INTEGER DEFAULT 0,
    
    -- Status and completion
    status VARCHAR(50) DEFAULT 'not_started' CHECK (status IN ('not_started', 'in_progress', 'completed', 'failed')),
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    last_activity_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Detailed challenge results
    challenge_results JSON DEFAULT '[]', -- Array of individual challenge results
    
    UNIQUE (agent_id, curriculum_level_id),
    INDEX idx_progress_agent (agent_id),
    INDEX idx_progress_level (curriculum_level_id),
    INDEX idx_progress_status (status)
);
```

### Competition Framework Tables

#### 6. Competitions
```sql
-- Competition instances
CREATE TABLE competitions (
    id VARCHAR(36) PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    university_id VARCHAR(36) NOT NULL REFERENCES universities(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    
    -- Competition configuration
    competition_type VARCHAR(100) NOT NULL CHECK (competition_type IN ('solo', 'head_to_head', 'tournament', 'challenge')),
    rules JSON NOT NULL, -- Scoring rules, time limits, etc.
    benchmark_id VARCHAR(255), -- Reference to Level 4 benchmark
    evaluation_config JSON NOT NULL,
    
    -- Scheduling
    scheduled_start TIMESTAMP,
    scheduled_end TIMESTAMP,
    actual_start TIMESTAMP,
    actual_end TIMESTAMP,
    
    -- Status
    status VARCHAR(50) DEFAULT 'scheduled' CHECK (status IN ('scheduled', 'active', 'completed', 'cancelled')),
    max_participants INTEGER DEFAULT 10 CHECK (max_participants > 0),
    
    -- Results
    winner_agent_id VARCHAR(36) REFERENCES university_agents(id),
    results_published BOOLEAN DEFAULT FALSE,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_competitions_university (university_id),
    INDEX idx_competitions_status (status),
    INDEX idx_competitions_schedule (scheduled_start)
);
```

#### 7. Competition Participants
```sql
-- Agent participation in competitions
CREATE TABLE competition_participants (
    id VARCHAR(36) PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    competition_id VARCHAR(36) NOT NULL REFERENCES competitions(id) ON DELETE CASCADE,
    agent_id VARCHAR(36) NOT NULL REFERENCES university_agents(id) ON DELETE CASCADE,
    
    -- Participation details
    participant_type VARCHAR(50) DEFAULT 'competitor' CHECK (participant_type IN ('competitor', 'observer', 'judge')),
    seed_ranking INTEGER, -- For tournament brackets
    
    -- Performance metrics
    final_score FLOAT,
    ranking INTEGER,
    execution_time_ms INTEGER,
    
    -- Status
    status VARCHAR(50) DEFAULT 'registered' CHECK (status IN ('registered', 'active', 'completed', 'disqualified')),
    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    
    UNIQUE (competition_id, agent_id),
    INDEX idx_participants_competition (competition_id),
    INDEX idx_participants_agent (agent_id)
);
```

#### 8. Competition Matches
```sql
-- Individual matches within competitions
CREATE TABLE competition_matches (
    id VARCHAR(36) PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    competition_id VARCHAR(36) NOT NULL REFERENCES competitions(id) ON DELETE CASCADE,
    match_number INTEGER NOT NULL,
    
    -- Participants
    participant1_id VARCHAR(36) NOT NULL REFERENCES competition_participants(id),
    participant2_id VARCHAR(36) REFERENCES competition_participants(id), -- NULL for solo competitions
    
    -- Match details
    match_config JSON NOT NULL,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    
    -- Results
    participant1_score FLOAT,
    participant2_score FLOAT,
    winner_participant_id VARCHAR(36) REFERENCES competition_participants(id),
    
    -- Status
    status VARCHAR(50) DEFAULT 'scheduled' CHECK (status IN ('scheduled', 'active', 'completed', 'cancelled')),
    
    -- Evaluation data
    evaluation_run_id VARCHAR(255), -- Reference to Level 4 evaluation run
    detailed_results JSON,
    
    INDEX idx_matches_competition (competition_id),
    INDEX idx_matches_participants (participant1_id, participant2_id),
    INDEX idx_matches_status (status)
);
```

### Training Data Pipeline Tables

#### 9. Training Data Collection
```sql
-- Collection of training data from agent activities
CREATE TABLE training_data_collections (
    id VARCHAR(36) PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    university_id VARCHAR(36) NOT NULL REFERENCES universities(id) ON DELETE CASCADE,
    agent_id VARCHAR(36) NOT NULL REFERENCES university_agents(id) ON DELETE CASCADE,
    
    -- Data source
    source_type VARCHAR(100) NOT NULL CHECK (source_type IN ('competition', 'training', 'evaluation', 'interaction')),
    source_id VARCHAR(36), -- Reference to competition, match, etc.
    
    -- Data content
    data_type VARCHAR(100) NOT NULL CHECK (data_type IN ('conversation', 'reasoning', 'tool_use', 'problem_solving')),
    raw_data JSON NOT NULL,
    processed_data JSON,
    metadata JSON,
    
    -- Quality metrics
    quality_score FLOAT DEFAULT 0.0,
    validation_status VARCHAR(50) DEFAULT 'pending' CHECK (validation_status IN ('pending', 'validated', 'rejected', 'anonymized')),
    
    -- Privacy and sharing
    privacy_level VARCHAR(50) DEFAULT 'private' CHECK (privacy_level IN ('private', 'shared', 'public')),
    anonymized BOOLEAN DEFAULT FALSE,
    
    collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    validated_at TIMESTAMP,
    
    INDEX idx_training_university (university_id),
    INDEX idx_training_agent (agent_id),
    INDEX idx_training_source (source_type, source_id),
    INDEX idx_training_validation (validation_status)
);
```

#### 10. Improvement Proposals (Lyceum Integration)
```sql
-- Improvement proposals generated from training data
CREATE TABLE improvement_proposals (
    id VARCHAR(36) PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    university_id VARCHAR(36) NOT NULL REFERENCES universities(id) ON DELETE CASCADE,
    
    -- Proposal source
    generated_by VARCHAR(100) DEFAULT 'professor_agent' CHECK (generated_by IN ('professor_agent', 'human', 'system')),
    source_data_collection_id VARCHAR(36) REFERENCES training_data_collections(id),
    
    -- Proposal content
    title VARCHAR(255) NOT NULL,
    description TEXT NOT NULL,
    implementation_details TEXT,
    expected_improvement FLOAT, -- Expected competency score improvement
    
    -- Validation
    validation_results JSON,
    validation_status VARCHAR(50) DEFAULT 'pending' CHECK (validation_status IN ('pending', 'approved', 'rejected', 'implemented')),
    validated_by VARCHAR(255), -- User ID or system
    validated_at TIMESTAMP,
    
    -- Implementation
    implementation_status VARCHAR(50) DEFAULT 'not_started' CHECK (implementation_status IN ('not_started', 'in_progress', 'completed', 'failed')),
    implemented_at TIMESTAMP,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_proposals_university (university_id),
    INDEX idx_proposals_status (validation_status),
    INDEX idx_proposals_implementation (implementation_status)
);
```

## SQLAlchemy Model Implementation

### Base University Models
```python
# app/database/models_university.py
from sqlalchemy import Column, String, Text, Integer, Float, Boolean, JSON, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database.database import Base
import uuid

class University(Base):
    __tablename__ = "universities"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False)
    description = Column(Text)
    owner_user_id = Column(String, ForeignKey("users.id"), nullable=False)
    
    # Multi-tenant context
    client_app_id = Column(String, ForeignKey("client_applications.id"))
    tenant_id = Column(String)
    organization_id = Column(String, ForeignKey("organizations.id"))
    
    # Configuration
    settings = Column(JSON, default=lambda: {})
    isolation_level = Column(String(50), default="strict")
    max_agents = Column(Integer, default=100)
    max_concurrent_competitions = Column(Integer, default=10)
    storage_quota_mb = Column(Integer, default=1024)
    
    # Status
    status = Column(String(50), default="active")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    agents = relationship("UniversityAgent", back_populates="university", cascade="all, delete-orphan")
    curriculum_paths = relationship("CurriculumPath", back_populates="university", cascade="all, delete-orphan")
    competitions = relationship("Competition", back_populates="university", cascade="all, delete-orphan")

class UniversityAgent(Base):
    __tablename__ = "university_agents"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    university_id = Column(String, ForeignKey("universities.id"), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    
    # Agent configuration
    agent_type = Column(String(100), nullable=False)
    configuration = Column(JSON, nullable=False)
    specialization = Column(String(100))
    
    # Training state
    current_curriculum_path_id = Column(String, ForeignKey("curriculum_paths.id"))
    current_curriculum_level_id = Column(String, ForeignKey("curriculum_levels.id"))
    current_challenge_index = Column(Integer, default=0)
    
    # Performance metrics
    competency_score = Column(Float, default=0.0)
    training_hours = Column(Float, default=0.0)
    training_data_collected = Column(Integer, default=0)
    
    # Competition performance
    competition_wins = Column(Integer, default=0)
    competition_losses = Column(Integer, default=0)
    competition_draws = Column(Integer, default=0)
    average_score = Column(Float, default=0.0)
    highest_score = Column(Float, default=0.0)
    
    # Status
    status = Column(String(50), default="active")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    university = relationship("University", back_populates="agents")
    progress_records = relationship("AgentProgress", back_populates="agent", cascade="all, delete-orphan")
    competition_participations = relationship("CompetitionParticipant", back_populates="agent", cascade="all, delete-orphan")
```

## Alembic Migration Strategy

### Initial Migration
```python
# migrations/versions/001_create_university_tables.py
from alembic import op
import sqlalchemy as sa

def upgrade():
    # Create all university tables
    op.create_table('universities', ...)
    op.create_table('university_agents', ...)
    # ... all other tables
    
    # Create indexes
    op.create_index('idx_universities_owner', 'universities', ['owner_user_id'])
    op.create_index('idx_agents_university', 'university_agents', ['university_id'])
    # ... all other indexes

def downgrade():
    # Drop tables in reverse order (respecting foreign keys)
    op.drop_table('improvement_proposals')
    op.drop_table('training_data_collections')
    # ... all other tables
```

## Data Retention and Archiving

### Archiving Strategy
```sql
-- Archive old data while maintaining performance
CREATE TABLE universities_archive AS SELECT * FROM universities WHERE 1=0;
CREATE TABLE university_agents_archive AS SELECT * FROM university_agents WHERE 1=0;

-- Monthly archiving procedure
CREATE PROCEDURE archive_old_university_data()
BEGIN
    -- Archive universities inactive for > 1 year
    INSERT INTO universities_archive 
    SELECT * FROM universities 
    WHERE status = 'archived' AND last_activity_at < DATE_SUB(NOW(), INTERVAL 1 YEAR);
    
    DELETE FROM universities 
    WHERE status = 'archived' AND last_activity_at < DATE_SUB(NOW(), INTERVAL 1 YEAR);
    
    -- Similar procedures for other tables
END;
```

This comprehensive database schema provides the foundation for the Agentic University System while maintaining compatibility with DRYAD's existing multi-tenant architecture.