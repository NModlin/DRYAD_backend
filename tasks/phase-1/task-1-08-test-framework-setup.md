# Task 1-08: Test Framework Setup

**Phase:** 1 - Foundation & Beta Readiness  
**Week:** 2  
**Estimated Hours:** 4 hours  
**Priority:** CRITICAL  
**Dependencies:** None

---

## 🎯 OBJECTIVE

Set up comprehensive testing framework with pytest, pytest-asyncio, coverage tools, and test fixtures for the DRYAD.AI backend.

---

## 📋 REQUIREMENTS

### Functional Requirements
- Pytest configuration with async support
- Test database setup and teardown
- Fixture factories for common models
- Coverage reporting (>85% target)
- Test categorization (unit, integration, e2e)

### Technical Requirements
- pytest >= 7.4.0
- pytest-asyncio for async tests
- pytest-cov for coverage
- Factory Boy for test data
- SQLAlchemy test fixtures

### Performance Requirements
- Test suite execution: <5 minutes
- Individual test: <2 seconds
- Database setup: <1 second

---

## 🔧 IMPLEMENTATION

### Step 1: Dependencies (30 minutes)

**File:** `requirements-test.txt`

```txt
pytest==7.4.3
pytest-asyncio==0.21.1
pytest-cov==4.1.0
pytest-mock==3.12.0
factory-boy==3.3.0
faker==20.1.0
httpx==0.25.2
```

### Step 2: Pytest Configuration (1 hour)

**File:** `pytest.ini`

```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
asyncio_mode = auto
markers =
    unit: Unit tests
    integration: Integration tests
    e2e: End-to-end tests
    slow: Slow running tests
    critical: Critical path tests
addopts =
    --strict-markers
    --cov=app
    --cov-report=html
    --cov-report=term-missing
    --cov-fail-under=85
    -v
```

### Step 3: Test Database Fixtures (1.5 hours)

**File:** `tests/conftest.py`

```python
"""
Pytest Configuration and Fixtures
Global test setup for DRYAD.AI backend.
"""

from __future__ import annotations

import asyncio
from typing import AsyncGenerator

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

from app.database.base import Base
from app.core.config import settings

# Test database URL
TEST_DATABASE_URL = "postgresql+asyncpg://test:test@localhost:5432/dryad_test"


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="function")
async def db_engine():
    """Create test database engine."""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        poolclass=NullPool,
        echo=False,
    )
    
    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    # Drop all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def db_session(db_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create test database session."""
    async_session = sessionmaker(
        db_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    
    async with async_session() as session:
        yield session
        await session.rollback()


@pytest.fixture
def client():
    """Create test HTTP client."""
    from fastapi.testclient import TestClient
    from app.main import app
    
    return TestClient(app)
```

### Step 4: Factory Fixtures (1 hour)

**File:** `tests/factories.py`

```python
"""
Test Data Factories
Factory Boy factories for creating test data.
"""

from __future__ import annotations

from datetime import datetime
from uuid import uuid4

import factory
from factory import Faker

from app.database.models.agent_execution import AgentExecution, ExecutionStatus


class AgentExecutionFactory(factory.Factory):
    """Factory for AgentExecution model."""
    
    class Meta:
        model = AgentExecution
    
    id = factory.LazyFunction(uuid4)
    agent_id = factory.LazyFunction(uuid4)
    user_id = factory.LazyFunction(uuid4)
    execution_start = factory.LazyFunction(datetime.utcnow)
    status = ExecutionStatus.COMPLETED.value
    input_data = factory.Dict({"prompt": Faker("sentence")})
    output_data = factory.Dict({"result": Faker("text")})
    execution_time_ms = Faker("random_int", min=100, max=5000)
```

---

## ✅ DEFINITION OF DONE

- [ ] Pytest installed and configured
- [ ] Test database fixtures working
- [ ] Factory fixtures created
- [ ] Coverage reporting enabled
- [ ] All tests passing
- [ ] Documentation complete

---

## 📊 SUCCESS METRICS

- Test framework setup: <1 hour
- Test execution time: <5 minutes
- Coverage reporting: Working
- All fixtures functional

---

**Estimated Completion:** 4 hours  
**Status:** NOT STARTED

