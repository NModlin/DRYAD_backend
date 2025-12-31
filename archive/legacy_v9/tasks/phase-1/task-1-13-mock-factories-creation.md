# Task 1-13: Mock Factories Creation

**Phase:** 1 - Foundation & Beta Readiness  
**Week:** 2  
**Estimated Hours:** 6 hours  
**Priority:** MEDIUM  
**Dependencies:** Task 1-08 (Test Framework Setup)

---

## 🎯 OBJECTIVE

Create comprehensive mock factories using Factory Boy for all database models to simplify test data creation.

---

## 📋 REQUIREMENTS

### Functional Requirements
- Factory for each database model
- Realistic test data generation
- Relationship handling
- Customizable attributes
- Sequence generation

### Technical Requirements
- Factory Boy library
- Faker for realistic data
- SQLAlchemy integration
- Async support

---

## 🔧 IMPLEMENTATION

**File:** `tests/factories.py`

```python
"""
Test Data Factories
Factory Boy factories for all models.
"""

from __future__ import annotations

from datetime import datetime
from uuid import uuid4

import factory
from factory import Faker

from app.database.models.agent_execution import AgentExecution, ExecutionStatus
from app.database.models.sandbox import Sandbox, SandboxStatus


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


class SandboxFactory(factory.Factory):
    """Factory for Sandbox model."""
    
    class Meta:
        model = Sandbox
    
    id = factory.LazyFunction(uuid4)
    user_id = factory.LazyFunction(uuid4)
    status = SandboxStatus.ACTIVE.value
    created_at = factory.LazyFunction(datetime.utcnow)
    expires_at = factory.LazyFunction(
        lambda: datetime.utcnow() + timedelta(hours=24)
    )


# Usage in tests:
# execution = AgentExecutionFactory()
# execution_with_custom = AgentExecutionFactory(status=ExecutionStatus.FAILED.value)
```

---

## ✅ DEFINITION OF DONE

- [ ] Factories for all models
- [ ] Realistic data generation
- [ ] Relationships handled
- [ ] Documentation complete
- [ ] Tests using factories

---

## 📊 SUCCESS METRICS

- All models have factories
- Test data creation: <100ms
- Factories used in >80% of tests

---

**Estimated Completion:** 6 hours  
**Status:** NOT STARTED

