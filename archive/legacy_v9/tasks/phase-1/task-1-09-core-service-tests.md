# Task 1-09: Core Service Tests

**Phase:** 1 - Foundation & Beta Readiness  
**Week:** 2  
**Estimated Hours:** 12 hours  
**Priority:** CRITICAL  
**Dependencies:** Task 1-08 (Test Framework Setup)

---

## 🎯 OBJECTIVE

Create comprehensive test suite for all core services including Agent Studio, Sandbox, Oracle, and Guardian services with >85% code coverage.

---

## 📋 REQUIREMENTS

### Functional Requirements
- Unit tests for all service methods
- Mock external dependencies
- Test error handling
- Test edge cases
- Async test support

### Technical Requirements
- pytest-asyncio for async tests
- pytest-mock for mocking
- Factory Boy for test data
- Coverage >85%

### Performance Requirements
- Test suite execution: <3 minutes
- Individual test: <1 second

---

## 🔧 IMPLEMENTATION

### Agent Studio Service Tests

**File:** `tests/services/test_agent_studio_service.py`

```python
"""
Agent Studio Service Tests
Comprehensive tests for agent management.
"""

import pytest
from uuid import uuid4

from app.services.agent_studio_service import AgentStudioService
from app.database.models.agent_execution import ExecutionStatus


@pytest.mark.asyncio
async def test_create_execution_record(db_session):
    """Test creating execution record."""
    service = AgentStudioService(db_session)
    
    agent_id = uuid4()
    user_id = uuid4()
    input_data = {"prompt": "Test"}
    
    execution_id = await service.create_execution_record(
        agent_id=agent_id,
        user_id=user_id,
        input_data=input_data,
    )
    
    assert execution_id is not None


@pytest.mark.asyncio
async def test_get_execution_history(db_session):
    """Test fetching execution history."""
    service = AgentStudioService(db_session)
    
    agent_id = uuid4()
    user_id = uuid4()
    
    # Create test executions
    for i in range(5):
        await service.create_execution_record(
            agent_id=agent_id,
            user_id=user_id,
            input_data={"test": i},
        )
    
    history = await service.get_agent_execution_history(agent_id)
    
    assert len(history) == 5


@pytest.mark.asyncio
async def test_update_execution_status(db_session):
    """Test updating execution status."""
    service = AgentStudioService(db_session)
    
    agent_id = uuid4()
    user_id = uuid4()
    
    execution_id = await service.create_execution_record(
        agent_id=agent_id,
        user_id=user_id,
        input_data={},
    )
    
    await service.update_execution_status(
        execution_id=execution_id,
        status=ExecutionStatus.COMPLETED,
        output_data={"result": "success"},
    )
    
    history = await service.get_agent_execution_history(agent_id)
    assert history[0]["status"] == ExecutionStatus.COMPLETED.value


@pytest.mark.asyncio
async def test_get_performance_metrics(db_session):
    """Test performance metrics calculation."""
    service = AgentStudioService(db_session)
    
    agent_id = uuid4()
    user_id = uuid4()
    
    # Create executions
    for i in range(10):
        exec_id = await service.create_execution_record(
            agent_id=agent_id,
            user_id=user_id,
            input_data={},
        )
        
        status = ExecutionStatus.COMPLETED if i < 8 else ExecutionStatus.FAILED
        await service.update_execution_status(
            execution_id=exec_id,
            status=status,
        )
    
    metrics = await service.get_agent_performance_metrics(agent_id, "7d")
    
    assert metrics["total_executions"] == 10
    assert metrics["successful_executions"] == 8
    assert metrics["success_rate"] == 80.0
```

### Sandbox Service Tests

**File:** `tests/services/test_sandbox_service.py`

```python
"""
Sandbox Service Tests
"""

import pytest
from datetime import datetime, timedelta
from uuid import uuid4

from app.services.sandbox_service import SandboxCleanupService
from app.database.models.sandbox import Sandbox, SandboxStatus


@pytest.mark.asyncio
async def test_get_expired_sandboxes(db_session):
    """Test finding expired sandboxes."""
    service = SandboxCleanupService(db_session)
    
    user_id = uuid4()
    
    # Create expired sandbox
    expired = Sandbox(
        user_id=user_id,
        expires_at=datetime.utcnow() - timedelta(hours=1),
        status=SandboxStatus.ACTIVE.value,
    )
    db_session.add(expired)
    await db_session.commit()
    
    expired_list = await service.get_expired_sandboxes(100)
    
    assert len(expired_list) >= 1


@pytest.mark.asyncio
async def test_cleanup_sandbox(db_session, mocker):
    """Test sandbox cleanup."""
    service = SandboxCleanupService(db_session)
    
    # Mock Docker client
    mocker.patch.object(service, 'delete_docker_resources')
    
    user_id = uuid4()
    sandbox = Sandbox(
        user_id=user_id,
        expires_at=datetime.utcnow() - timedelta(hours=1),
        status=SandboxStatus.ACTIVE.value,
    )
    db_session.add(sandbox)
    await db_session.commit()
    
    await service.cleanup_sandbox(sandbox.id)
    
    await db_session.refresh(sandbox)
    assert sandbox.status == SandboxStatus.CLEANED.value
```

---

## ✅ DEFINITION OF DONE

- [ ] All core services have test coverage
- [ ] All tests passing
- [ ] Coverage >85%
- [ ] Edge cases tested
- [ ] Error handling tested
- [ ] Mocks properly configured

---

## 📊 SUCCESS METRICS

- Test coverage: >85%
- Test execution time: <3 minutes
- All tests passing
- No flaky tests

---

**Estimated Completion:** 12 hours  
**Status:** NOT STARTED

