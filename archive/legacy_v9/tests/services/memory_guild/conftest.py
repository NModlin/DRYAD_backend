"""
Test fixtures for Memory Guild tests.
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
def sample_memory_data():
    """Sample memory record data for testing."""
    return {
        "agent_id": "agent_123",
        "tenant_id": "tenant_456",
        "source_type": "conversation",
        "content_text": "User prefers dark mode for all interfaces",
        "content_hash": "a1b2c3d4e5f6789012345678901234567890123456789012345678901234",
        "memory_metadata": {
            "conversation_id": "conv_789",
            "timestamp": "2025-01-10T10:30:00Z",
            "confidence": 0.95,
        },
    }


@pytest.fixture
def sample_embedding_data():
    """Sample embedding data for testing."""
    return {
        "vector_id": "vec_123456",
        "embedding_model": "text-embedding-ada-002",
    }


@pytest.fixture
def sample_relationship_data():
    """Sample relationship data for testing."""
    return {
        "relationship_type": "supports",
        "confidence_score": 0.87,
    }


@pytest.fixture
def sample_data_source_data():
    """Sample data source data for testing."""
    return {
        "source_name": "confluence_wiki",
        "source_type": "api",
        "source_uri": "https://wiki.example.com/api",
        "source_metadata": {
            "api_version": "v2",
            "auth_type": "oauth2",
        },
    }


@pytest.fixture
def sample_policy_data():
    """Sample access policy data for testing."""
    return {
        "policy_name": "tenant_isolation_policy",
        "policy_rules": {
            "allow": [
                {
                    "effect": "allow",
                    "actions": ["read", "write"],
                    "resources": ["memory:*"],
                    "conditions": {
                        "tenant_match": True,
                    },
                }
            ],
        },
    }

