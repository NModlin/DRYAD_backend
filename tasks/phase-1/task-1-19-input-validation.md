# Task 1-19: Comprehensive Input Validation

**Phase:** 1 - Foundation & Beta Readiness  
**Week:** 3  
**Estimated Hours:** 4 hours  
**Priority:** HIGH  
**Dependencies:** None

---

## 🎯 OBJECTIVE

Implement comprehensive input validation across all API endpoints using Pydantic models with custom validators.

---

## 📋 REQUIREMENTS

### Functional Requirements
- Validate all request inputs
- Type validation
- Range validation
- Format validation
- Custom business logic validation
- Clear error messages

### Technical Requirements
- Pydantic v2 models
- Custom validators
- Field constraints
- Error response formatting

---

## 🔧 IMPLEMENTATION

**File:** `app/api/validators.py`

```python
"""
Input Validators
Pydantic models with comprehensive validation.
"""

from __future__ import annotations

import re
from uuid import UUID

from pydantic import BaseModel, Field, field_validator, model_validator


class AgentExecutionRequest(BaseModel):
    """Agent execution request with validation."""
    
    agent_id: UUID
    prompt: str = Field(..., min_length=1, max_length=10000)
    temperature: float = Field(0.7, ge=0.0, le=2.0)
    max_tokens: int = Field(1000, ge=1, le=100000)
    
    @field_validator("prompt")
    @classmethod
    def validate_prompt(cls, v: str) -> str:
        """Validate prompt content."""
        # Remove excessive whitespace
        v = " ".join(v.split())
        
        # Check for minimum meaningful content
        if len(v.strip()) < 3:
            raise ValueError("Prompt too short")
        
        return v
    
    @model_validator(mode="after")
    def validate_model(self):
        """Cross-field validation."""
        # Example: if temperature is high, limit max_tokens
        if self.temperature > 1.5 and self.max_tokens > 50000:
            raise ValueError(
                "High temperature requires lower max_tokens"
            )
        
        return self


class SearchRequest(BaseModel):
    """Search request with validation."""
    
    query: str = Field(..., min_length=1, max_length=500)
    limit: int = Field(10, ge=1, le=100)
    offset: int = Field(0, ge=0)
    
    @field_validator("query")
    @classmethod
    def validate_query(cls, v: str) -> str:
        """Validate search query."""
        # Remove special characters that could cause issues
        v = re.sub(r'[<>{}]', '', v)
        
        # Ensure not empty after cleaning
        if not v.strip():
            raise ValueError("Query cannot be empty")
        
        return v.strip()


class PaginationParams(BaseModel):
    """Reusable pagination parameters."""
    
    limit: int = Field(50, ge=1, le=1000)
    offset: int = Field(0, ge=0)
    sort_by: str | None = Field(None, pattern="^[a-z_]+$")
    sort_order: str = Field("desc", pattern="^(asc|desc)$")
```

**File:** `tests/test_input_validation.py`

```python
"""Input Validation Tests"""

import pytest
from uuid import uuid4

from app.api.validators import AgentExecutionRequest, SearchRequest


def test_valid_execution_request():
    """Test valid execution request."""
    request = AgentExecutionRequest(
        agent_id=uuid4(),
        prompt="Test prompt",
        temperature=0.7,
        max_tokens=1000,
    )
    
    assert request.prompt == "Test prompt"


def test_invalid_prompt_too_short():
    """Test prompt validation."""
    with pytest.raises(ValueError, match="too short"):
        AgentExecutionRequest(
            agent_id=uuid4(),
            prompt="ab",
            temperature=0.7,
        )


def test_temperature_out_of_range():
    """Test temperature range validation."""
    with pytest.raises(ValueError):
        AgentExecutionRequest(
            agent_id=uuid4(),
            prompt="Test",
            temperature=3.0,  # Too high
        )


def test_search_query_sanitization():
    """Test search query sanitization."""
    request = SearchRequest(
        query="test <script>alert(1)</script>",
    )
    
    # Should remove dangerous characters
    assert "<script>" not in request.query
```

---

## ✅ DEFINITION OF DONE

- [ ] All endpoints have validation
- [ ] Pydantic models created
- [ ] Custom validators implemented
- [ ] Error messages clear
- [ ] Tests passing

---

## 📊 SUCCESS METRICS

- Validation coverage: 100%
- Invalid requests blocked: 100%
- Clear error messages: 100%

---

**Estimated Completion:** 4 hours  
**Status:** NOT STARTED

