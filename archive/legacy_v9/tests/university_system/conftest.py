"""
Pytest configuration and fixtures for Uni0 tests
"""

import pytest
import os
import sys
import uuid
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

# Added app.university_system imports directly

# Set test environment BEFORE importing anything else
os.environ["ENVIRONMENT"] = "test"
os.environ["DATABASE_URL"] = "sqlite:///:memory:"

# Create test database - use in-memory SQLite for tests
TEST_DATABASE_URL = "sqlite:///:memory:"

# Create engine with StaticPool to keep in-memory DB alive
engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
    echo=False
)

# Create session factory
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Override database module BEFORE importing app
import app.university_system.database.database as db_module
db_module.engine = engine
db_module.SessionLocal = TestingSessionLocal

# NOW import the app (which will use the overridden engine)
from app.university_system.main import app
from app.university_system.database.database import Base, get_db
from app.university_system.database.models_university import (
    University, UniversityAgent, CurriculumPath, CurriculumLevel,
    AgentProgress, TrainingDataCollection, ImprovementProposal,
    Achievement, AgentAchievement, Competition, CompetitionRound, Leaderboard,
    SkillTree, SkillNode, SkillProgress, CompetitionParticipant
)


@pytest.fixture(scope="session", autouse=True)
def setup_database():
    """Create test database tables once per session"""
    # Create all tables at the start of the session
    Base.metadata.create_all(bind=engine)
    yield
    # Tables are automatically cleaned up when in-memory DB is destroyed


@pytest.fixture
def db_session(setup_database) -> Session:
    """Create a fresh database session for each test"""
    session = TestingSessionLocal()

    yield session

    # Clean up after each test - delete all data to avoid constraint violations
    try:
        # Delete all data from tables in reverse order of dependencies
        session.query(CompetitionParticipant).delete()
        session.query(SkillProgress).delete()
        session.query(SkillNode).delete()
        session.query(SkillTree).delete()
        session.query(Leaderboard).delete()
        session.query(CompetitionRound).delete()
        session.query(Competition).delete()
        session.query(AgentAchievement).delete()
        session.query(Achievement).delete()
        session.query(ImprovementProposal).delete()
        session.query(TrainingDataCollection).delete()
        session.query(AgentProgress).delete()
        session.query(CurriculumLevel).delete()
        session.query(CurriculumPath).delete()
        session.query(UniversityAgent).delete()
        session.query(University).delete()
        session.commit()
    except Exception:
        session.rollback()
    finally:
        session.close()


@pytest.fixture
def override_get_db(db_session):
    """Override the get_db dependency"""
    def _override_get_db():
        return db_session

    app.dependency_overrides[get_db] = _override_get_db
    yield
    app.dependency_overrides.clear()


@pytest.fixture
def disable_rate_limit():
    """Disable rate limiting for tests"""
    from app.university_system.middleware.rate_limit import limiter
    limiter.enabled = False
    yield
    limiter.enabled = True


@pytest.fixture
def client(override_get_db, disable_rate_limit) -> TestClient:
    """Create a test client"""
    return TestClient(app)


@pytest.fixture
def test_university(db_session: Session) -> University:
    """Create a test university with unique ID"""
    unique_id = f"test-uni-{uuid.uuid4().hex[:8]}"
    university = University(
        id=unique_id,
        name="Test University",
        description="A test university for unit tests",
        owner_user_id="test-owner",
        status="active"
    )
    db_session.add(university)
    db_session.commit()
    db_session.refresh(university)
    return university


@pytest.fixture
def test_agent(db_session: Session, test_university: University) -> UniversityAgent:
    """Create a test agent with unique ID"""
    unique_id = f"test-agent-{uuid.uuid4().hex[:8]}"
    agent = UniversityAgent(
        id=unique_id,
        university_id=test_university.id,
        name="Test Agent",
        agent_type="student",
        status="active",
        specialization="AI",
        competency_score=0.5
    )
    db_session.add(agent)
    db_session.commit()
    db_session.refresh(agent)
    return agent


@pytest.fixture
def test_curriculum(db_session: Session, test_university: University) -> CurriculumPath:
    """Create a test curriculum path with unique ID"""
    unique_id = f"test-curriculum-{uuid.uuid4().hex[:8]}"
    curriculum = CurriculumPath(
        id=unique_id,
        university_id=test_university.id,
        name="Test Curriculum",
        description="A test curriculum path",
        difficulty_level="beginner",
        status="active"
    )
    db_session.add(curriculum)
    db_session.commit()
    db_session.refresh(curriculum)
    return curriculum


@pytest.fixture
def test_achievement(db_session: Session) -> Achievement:
    """Create a test achievement with unique ID"""
    unique_id = f"test-achievement-{uuid.uuid4().hex[:8]}"
    achievement = Achievement(
        id=unique_id,
        name="Test Achievement",
        description="A test achievement for unit tests",
        category="testing",
        difficulty="easy",
        points=10,
        criteria={"tests": 1},
        required_count=1
    )
    db_session.add(achievement)
    db_session.commit()
    db_session.refresh(achievement)
    return achievement


@pytest.fixture
def test_competition(db_session: Session, test_university: University) -> Competition:
    """Create a test competition with unique ID"""
    unique_id = f"test-competition-{uuid.uuid4().hex[:8]}"
    competition = Competition(
        id=unique_id,
        university_id=test_university.id,
        name="Test Competition",
        description="A test competition for unit tests",
        competition_type="ai_battle",
        status="active"
    )
    db_session.add(competition)
    db_session.commit()
    db_session.refresh(competition)
    return competition


@pytest.fixture
def auth_token(client: TestClient, test_university: University) -> str:
    """Get an authentication token for testing"""
    response = client.post(
        "/api/v1/auth/login",
        json={
            "university_id": test_university.id,
            "api_key": f"uni0_{test_university.id}_key"
        }
    )
    assert response.status_code == 200
    return response.json()["access_token"]


@pytest.fixture
def auth_headers(auth_token: str) -> dict:
    """Get authorization headers for testing"""
    return {"Authorization": f"Bearer {auth_token}"}

