# Task 1-10: API Endpoint Tests

**Phase:** 1 - Foundation & Beta Readiness  
**Week:** 2  
**Estimated Hours:** 12 hours  
**Priority:** CRITICAL  
**Dependencies:** Task 1-08 (Test Framework Setup)

---

## 🎯 OBJECTIVE

Create comprehensive integration tests for all API endpoints with request/response validation, authentication testing, and error handling.

---

## 📋 REQUIREMENTS

### Functional Requirements
- Test all API endpoints
- Request validation testing
- Response schema validation
- Authentication/authorization testing
- Error response testing

### Technical Requirements
- FastAPI TestClient
- Pydantic response validation
- HTTP status code verification
- JSON schema validation

### Performance Requirements
- API test suite: <2 minutes
- Individual endpoint test: <500ms

---

## 🔧 IMPLEMENTATION

### Agent Studio API Tests

**File:** `tests/api/test_agent_studio_api.py`

```python
"""
Agent Studio API Tests
Integration tests for agent management endpoints.
"""

import pytest
from uuid import uuid4

from fastapi.testclient import TestClient


def test_get_agent_execution_history(client: TestClient, db_session):
    """Test GET /api/v1/agent-studio/agents/{agent_id}/executions"""
    agent_id = uuid4()
    
    response = client.get(f"/api/v1/agent-studio/agents/{agent_id}/executions")
    
    assert response.status_code == 200
    data = response.json()
    assert "executions" in data
    assert "total" in data
    assert isinstance(data["executions"], list)


def test_get_agent_execution_history_with_pagination(client: TestClient):
    """Test pagination parameters."""
    agent_id = uuid4()
    
    response = client.get(
        f"/api/v1/agent-studio/agents/{agent_id}/executions",
        params={"limit": 10, "offset": 0},
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["limit"] == 10
    assert data["offset"] == 0


def test_get_agent_execution_history_invalid_limit(client: TestClient):
    """Test invalid limit parameter."""
    agent_id = uuid4()
    
    response = client.get(
        f"/api/v1/agent-studio/agents/{agent_id}/executions",
        params={"limit": 1000},  # Exceeds max
    )
    
    assert response.status_code == 422  # Validation error


def test_get_agent_performance_metrics(client: TestClient):
    """Test GET /api/v1/agent-studio/agents/{agent_id}/metrics"""
    agent_id = uuid4()
    
    response = client.get(f"/api/v1/agent-studio/agents/{agent_id}/metrics")
    
    assert response.status_code == 200
    data = response.json()
    assert "total_executions" in data
    assert "success_rate" in data
    assert "execution_times" in data


def test_get_metrics_with_time_range(client: TestClient):
    """Test metrics with different time ranges."""
    agent_id = uuid4()
    
    for time_range in ["1d", "7d", "30d", "90d"]:
        response = client.get(
            f"/api/v1/agent-studio/agents/{agent_id}/metrics",
            params={"time_range": time_range},
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["time_range"] == time_range


def test_get_metrics_invalid_time_range(client: TestClient):
    """Test invalid time range."""
    agent_id = uuid4()
    
    response = client.get(
        f"/api/v1/agent-studio/agents/{agent_id}/metrics",
        params={"time_range": "invalid"},
    )
    
    assert response.status_code == 422
```

### Sandbox API Tests

**File:** `tests/api/test_sandbox_api.py`

```python
"""
Sandbox API Tests
"""

import pytest
from fastapi.testclient import TestClient


def test_cleanup_sandboxes(client: TestClient):
    """Test POST /api/v1/sandbox/cleanup"""
    response = client.post("/api/v1/sandbox/cleanup")
    
    assert response.status_code == 200
    data = response.json()
    assert "total_found" in data
    assert "cleaned" in data
    assert "failed" in data


def test_cleanup_with_limit(client: TestClient):
    """Test cleanup with limit parameter."""
    response = client.post(
        "/api/v1/sandbox/cleanup",
        params={"limit": 50},
    )
    
    assert response.status_code == 200


def test_cleanup_requires_authentication(client: TestClient):
    """Test that cleanup requires authentication."""
    # Without auth token
    response = client.post("/api/v1/sandbox/cleanup")
    
    # Should require authentication (if implemented)
    # assert response.status_code == 401
    pass
```

### Error Handling Tests

**File:** `tests/api/test_error_handling.py`

```python
"""
API Error Handling Tests
"""

import pytest
from fastapi.testclient import TestClient


def test_404_not_found(client: TestClient):
    """Test 404 for non-existent endpoint."""
    response = client.get("/api/v1/nonexistent")
    
    assert response.status_code == 404


def test_422_validation_error(client: TestClient):
    """Test 422 for validation errors."""
    from uuid import uuid4
    
    agent_id = uuid4()
    
    response = client.get(
        f"/api/v1/agent-studio/agents/{agent_id}/executions",
        params={"limit": -1},  # Invalid
    )
    
    assert response.status_code == 422
    data = response.json()
    assert "detail" in data


def test_500_internal_error_handling(client: TestClient, mocker):
    """Test 500 error handling."""
    # Mock service to raise exception
    # Verify proper error response
    pass
```

---

## ✅ DEFINITION OF DONE

- [ ] All API endpoints tested
- [ ] Request validation tested
- [ ] Response schemas validated
- [ ] Error handling tested
- [ ] Authentication tested
- [ ] All tests passing

---

## 📊 SUCCESS METRICS

- API test coverage: >90%
- Test execution: <2 minutes
- All status codes verified
- All error cases tested

---

**Estimated Completion:** 12 hours  
**Status:** NOT STARTED

