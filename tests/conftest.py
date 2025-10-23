"""
Security-focused test configuration for DRYAD.AI Backend
"""
import pytest
import os
import tempfile
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from unittest.mock import patch

from app.database.database import Base

# Set test environment variables
os.environ["ENVIRONMENT"] = "development"
os.environ["DATABASE_URL"] = "sqlite:///./test_DRYAD.AI.db"
os.environ["JWT_SECRET_KEY"] = "test-jwt-secret-key-for-testing-only"
os.environ["CORS_ALLOWED_ORIGINS"] = "http://localhost:3000,http://127.0.0.1:3000"
os.environ["LOG_LEVEL"] = "DEBUG"
os.environ["DISABLE_RATE_LIMITING"] = "true"  # Disable rate limiting for tests

@pytest.fixture(scope="session")
def test_client():
    """Create test client for security testing."""
    from app.main import app
    return TestClient(app)

@pytest.fixture(scope="function")
def temp_file():
    """Create temporary file for upload testing."""
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp.write(b"Test file content")
        tmp.flush()
        yield tmp.name
    os.unlink(tmp.name)

@pytest.fixture(scope="function")
def malicious_file():
    """Create malicious file for security testing."""
    with tempfile.NamedTemporaryFile(delete=False, suffix=".exe") as tmp:
        # Create a fake executable file
        tmp.write(b"MZ\x90\x00")  # PE header signature
        tmp.write(b"This is a fake executable for testing")
        tmp.flush()
        yield tmp.name
    os.unlink(tmp.name)

@pytest.fixture(scope="function")
def oversized_file():
    """Create oversized file for testing file size limits."""
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        # Create 60MB file (over 50MB limit)
        tmp.write(b"X" * (60 * 1024 * 1024))
        tmp.flush()
        yield tmp.name
    os.unlink(tmp.name)

@pytest.fixture(scope="function")
def db() -> Session:
    """Create test database session."""
    from sqlalchemy import Column, String, Table

    # Create in-memory SQLite database
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})

    # Create a simple agents table for foreign key references
    # This is a minimal table just for testing - not the full system_agents table
    agents_table = Table(
        'agents',
        Base.metadata,
        Column('id', String, primary_key=True),
        extend_existing=True
    )

    # Create all tables
    Base.metadata.create_all(bind=engine)

    # Create session
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSessionLocal()

    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)
