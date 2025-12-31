"""
Database configuration and connection management for Uni0
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./uni0.db")

# Create engine with appropriate configuration
if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool
    )
else:
    engine = create_engine(DATABASE_URL)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base for declarative models
Base = declarative_base()

def get_db():
    """Dependency for getting database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def ensure_data_directory():
    """Ensure data directory exists for SQLite database"""
    if DATABASE_URL.startswith("sqlite"):
        data_dir = os.path.dirname(DATABASE_URL.replace("sqlite:///", ""))
        if data_dir and not os.path.exists(data_dir):
            os.makedirs(data_dir, exist_ok=True)

def create_tables():
    """Create all database tables"""
    from .models_university import Base as UniversityBase
    
    # Create all tables
    UniversityBase.metadata.create_all(bind=engine)
    
    print("✅ Database tables created successfully")

def drop_tables():
    """Drop all database tables (for testing/development)"""
    from .models_university import Base as UniversityBase
    
    # Drop all tables
    UniversityBase.metadata.drop_all(bind=engine)
    
    print("✅ Database tables dropped successfully")

def reset_database():
    """Reset database by dropping and recreating tables"""
    drop_tables()
    create_tables()
    
    print("✅ Database reset completed")

# Import models to ensure they're registered with Base
# from .models_university import (
#     University, UniversityAgent, CurriculumPath, CurriculumLevel,
#     AgentProgress, TrainingDataCollection, ImprovementProposal,
#     Achievement, AgentAchievement, Competition, CompetitionRound, Leaderboard,
#     SkillTree, SkillNode, SkillProgress, CompetitionParticipant
# )