"""
Test fixtures for Structured Logging tests.
"""

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool

from app.database.database import Base


@pytest_asyncio.fixture
async def async_db():
    """Create an async in-memory SQLite database for testing."""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async_session = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with async_session() as session:
        yield session
    
    await engine.dispose()


@pytest.fixture
def sample_log_data():
    """Sample log entry data for testing."""
    return {
        "level": "INFO",
        "component": "test_component",
        "event_type": "test_event",
        "message": "Test log message",
        "log_metadata": {
            "key1": "value1",
            "key2": 123,
        },
        "trace_id": "trace_abc123",
        "span_id": "span_def456",
        "agent_id": "agent_789",
        "task_id": "task_012",
    }

