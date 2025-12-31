# Task 1-11: Database Integration Tests

**Phase:** 1 - Foundation & Beta Readiness  
**Week:** 2  
**Estimated Hours:** 4 hours  
**Priority:** HIGH  
**Dependencies:** Task 1-08 (Test Framework Setup)

---

## 🎯 OBJECTIVE

Create comprehensive database integration tests covering models, relationships, queries, and transactions.

---

## 📋 REQUIREMENTS

### Functional Requirements
- Test all database models
- Test relationships and foreign keys
- Test complex queries
- Test transactions and rollbacks
- Test database constraints

### Technical Requirements
- pytest-asyncio for async tests
- Test database fixtures
- SQLAlchemy test utilities
- Transaction isolation

### Performance Requirements
- Test suite execution: <2 minutes
- Database setup/teardown: <1 second

---

## 🔧 IMPLEMENTATION

**File:** `tests/integration/test_database.py`

```python
"""
Database Integration Tests
"""

import pytest
from uuid import uuid4
from datetime import datetime, timedelta

from app.database.models.agent_execution import AgentExecution, ExecutionStatus
from app.database.models.sandbox import Sandbox, SandboxStatus


@pytest.mark.asyncio
async def test_create_agent_execution(db_session):
    """Test creating agent execution record."""
    execution = AgentExecution(
        agent_id=uuid4(),
        user_id=uuid4(),
        input_data={"test": "data"},
        status=ExecutionStatus.PENDING.value,
    )
    
    db_session.add(execution)
    await db_session.commit()
    await db_session.refresh(execution)
    
    assert execution.id is not None
    assert execution.created_at is not None


@pytest.mark.asyncio
async def test_agent_execution_relationships(db_session):
    """Test model relationships."""
    # Test would verify agent and user relationships
    pass


@pytest.mark.asyncio
async def test_query_with_filters(db_session):
    """Test complex queries with filters."""
    from sqlalchemy import select
    
    agent_id = uuid4()
    
    # Create test data
    for i in range(5):
        execution = AgentExecution(
            agent_id=agent_id,
            user_id=uuid4(),
            input_data={"index": i},
            status=ExecutionStatus.COMPLETED.value,
        )
        db_session.add(execution)
    
    await db_session.commit()
    
    # Query with filter
    query = select(AgentExecution).where(
        AgentExecution.agent_id == agent_id,
        AgentExecution.status == ExecutionStatus.COMPLETED.value,
    )
    
    result = await db_session.execute(query)
    executions = result.scalars().all()
    
    assert len(executions) == 5


@pytest.mark.asyncio
async def test_transaction_rollback(db_session):
    """Test transaction rollback."""
    execution = AgentExecution(
        agent_id=uuid4(),
        user_id=uuid4(),
        input_data={},
        status=ExecutionStatus.PENDING.value,
    )
    
    db_session.add(execution)
    await db_session.rollback()
    
    # Should not be in database
    from sqlalchemy import select
    result = await db_session.execute(
        select(AgentExecution).where(AgentExecution.id == execution.id)
    )
    assert result.scalar_one_or_none() is None


@pytest.mark.asyncio
async def test_cascade_delete(db_session):
    """Test cascade delete behavior."""
    # Test cascade relationships
    pass
```

---

## ✅ DEFINITION OF DONE

- [ ] All models tested
- [ ] Relationships verified
- [ ] Complex queries tested
- [ ] Transactions tested
- [ ] Constraints validated
- [ ] All tests passing

---

## 📊 SUCCESS METRICS

- Test coverage: >85%
- Test execution: <2 minutes
- All database operations tested

---

**Estimated Completion:** 4 hours  
**Status:** NOT STARTED

