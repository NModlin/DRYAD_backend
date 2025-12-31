"""
Test fixtures for Tool Registry Service tests.
"""

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import StaticPool

from app.database.database import Base
from app.services.tool_registry.service import ToolRegistryService


@pytest_asyncio.fixture
async def async_db_engine():
    """Create an async in-memory SQLite database engine for testing."""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    await engine.dispose()


@pytest_asyncio.fixture
async def async_db_session(async_db_engine):
    """Create an async database session for testing."""
    async_session_maker = async_sessionmaker(
        async_db_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    
    async with async_session_maker() as session:
        yield session


@pytest_asyncio.fixture
async def tool_registry_service(async_db_session):
    """Create a ToolRegistryService instance for testing."""
    return ToolRegistryService(async_db_session)


@pytest.fixture
def sample_tool_data():
    """Sample tool data for testing."""
    return {
        "name": "code_executor",
        "version": "1.0.0",
        "description": "Executes Python code in isolated environment",
        "configuration_schema": {
            "openapi": "3.0.0",
            "info": {
                "title": "Code Executor",
                "version": "1.0.0"
            },
            "paths": {
                "/execute": {
                    "post": {
                        "requestBody": {
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "code": {"type": "string"},
                                            "language": {
                                                "type": "string",
                                                "enum": ["python", "javascript"]
                                            }
                                        },
                                        "required": ["code"]
                                    }
                                }
                            }
                        },
                        "responses": {
                            "200": {
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "type": "object",
                                            "properties": {
                                                "output": {"type": "string"},
                                                "exit_code": {"type": "integer"}
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        },
        "docker_image_uri": "registry.example.com/tools/code-executor:1.0.0"
    }


@pytest.fixture
def sample_permission_data():
    """Sample permission data for testing."""
    return {
        "principal_id": "agent_123",
        "principal_type": "agent",
        "allow_stateful_execution": True,
        "created_by": "admin_user"
    }

