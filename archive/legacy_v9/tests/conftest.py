"""
Security-focused test configuration for DRYAD.AI Backend
"""
import pytest
import pytest_asyncio
import os
import tempfile
import asyncio
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text, Column, String
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from unittest.mock import patch

from app.database.database import Base
# Import all models to ensure they are registered with Base.metadata
# Removed legacy university model imports
from app.models.agent_registry import SystemAgent, AgentCapabilityMatch

# Import Tool Registry and Memory Guild models to ensure they are registered
from app.database.models.tool_registry import ToolRegistry, ToolPermission, ToolSession, ToolExecution
from app.services.memory_guild.models import MemoryRecord, MemoryRelationship, MemoryEmbedding

# Set test environment variables
os.environ["ENVIRONMENT"] = "development"
os.environ["DATABASE_URL"] = "sqlite:///./test_DRYAD.AI.db"
os.environ["JWT_SECRET_KEY"] = "test-jwt-secret-key-for-testing-only"
os.environ["CORS_ALLOWED_ORIGINS"] = "http://localhost:3000,http://127.0.0.1:3000"
os.environ["LOG_LEVEL"] = "DEBUG"
os.environ["DISABLE_RATE_LIMITING"] = "true"  # Disable rate limiting for tests

class Agent(Base):
    """Dummy Agent model to satisfy Foreign Keys in tests."""
    __tablename__ = "agents"
    id = Column(String, primary_key=True)


@pytest.fixture(scope="session")
def test_client():
    """Create test client for security testing."""
    from app.main import app
    return TestClient(app)

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for each test case."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

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
    """Create test database session (Sync)."""
    from sqlalchemy import Column, String, Table

    # Create in-memory SQLite database
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})

    # Create a simple agents table for foreign key references if needed
    # (Leaving this pattern from original file, but logic might be better handled by just creating all models)
    
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

@pytest_asyncio.fixture(scope="function")
async def async_db() -> AsyncSession:
    """Create test database session (Async)."""
    # Use aiosqlite for async testing
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:", 
        connect_args={"check_same_thread": False},
        echo=False
    )

    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Create session maker
    AsyncTestingSessionLocal = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False, autoflush=False
    )
    
    async with AsyncTestingSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
    
    # Drop tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    await engine.dispose()
