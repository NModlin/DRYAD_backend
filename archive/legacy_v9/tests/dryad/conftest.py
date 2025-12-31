"""
Dryad Test Configuration

Pytest fixtures and configuration for Dryad tests.
"""

import pytest
import asyncio
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database.database import Base
from app.dryad.models import *  # Import all Dryad models
from app.dryad.services.grove_service import GroveService
from app.dryad.services.branch_service import BranchService
from app.dryad.services.vessel_service import VesselService
from app.dryad.services.oracle_service import OracleService


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def test_db() -> AsyncGenerator[AsyncSession, None]:
    """Create a test database session."""
    # Use in-memory SQLite for testing
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
        echo=False
    )
    
    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Create session
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with async_session() as session:
        yield session
    
    await engine.dispose()


@pytest.fixture
async def grove_service(test_db: AsyncSession) -> GroveService:
    """Create a GroveService instance for testing."""
    return GroveService(test_db)


@pytest.fixture
async def branch_service(test_db: AsyncSession) -> BranchService:
    """Create a BranchService instance for testing."""
    return BranchService(test_db)


@pytest.fixture
async def vessel_service(test_db: AsyncSession) -> VesselService:
    """Create a VesselService instance for testing."""
    return VesselService(test_db)


@pytest.fixture
async def oracle_service(test_db: AsyncSession) -> OracleService:
    """Create an OracleService instance for testing."""
    return OracleService(test_db)


@pytest.fixture
async def sample_grove(grove_service: GroveService):
    """Create a sample grove for testing."""
    from app.dryad.schemas.grove_schemas import GroveCreate
    
    grove_data = GroveCreate(
        name="Test Grove",
        description="A test grove for unit testing",
        template_metadata={"test": True}
    )
    
    return await grove_service.create_grove(grove_data)


@pytest.fixture
async def sample_branch(branch_service: BranchService, sample_grove):
    """Create a sample branch for testing."""
    from app.dryad.schemas.branch_schemas import BranchCreate
    from app.dryad.models.branch import BranchPriority
    
    # Get the root branch first
    branches = await branch_service.get_branches_by_grove(sample_grove.id)
    root_branch = next((b for b in branches if b.parent_id is None), None)
    
    if not root_branch:
        raise ValueError("No root branch found in sample grove")
    
    branch_data = BranchCreate(
        grove_id=sample_grove.id,
        parent_id=root_branch.id,
        name="Test Branch",
        description="A test branch for unit testing",
        priority=BranchPriority.MEDIUM
    )
    
    return await branch_service.create_branch(branch_data)


@pytest.fixture
async def sample_vessel(vessel_service: VesselService, sample_branch):
    """Create a sample vessel for testing."""
    from app.dryad.schemas.vessel_schemas import VesselCreate
    
    vessel_data = VesselCreate(
        branch_id=sample_branch.id,
        initial_context="Test context for vessel"
    )
    
    return await vessel_service.create_vessel(vessel_data)
