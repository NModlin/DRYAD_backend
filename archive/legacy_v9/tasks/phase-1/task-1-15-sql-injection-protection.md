# Task 1-15: SQL Injection Protection

**Phase:** 1 - Foundation & Beta Readiness  
**Week:** 3  
**Estimated Hours:** 6 hours  
**Priority:** CRITICAL  
**Dependencies:** None

---

## 🎯 OBJECTIVE

Implement comprehensive SQL injection protection across all database queries using SQLAlchemy ORM, parameterized queries, and input validation.

---

## 📋 REQUIREMENTS

### Functional Requirements
- All queries use SQLAlchemy ORM or parameterized statements
- No raw SQL string concatenation
- Input validation on all user inputs
- Query parameter sanitization
- SQL injection testing

### Technical Requirements
- SQLAlchemy ORM for all queries
- Pydantic validation for inputs
- Bandit security scanning
- SQL injection test suite

### Performance Requirements
- No performance degradation from security measures
- Query execution time: <100ms

---

## 🔧 IMPLEMENTATION

### Step 1: Audit Existing Queries (2 hours)

**File:** `scripts/audit_sql_queries.py`

```python
"""
SQL Query Security Audit
Scans codebase for potential SQL injection vulnerabilities.
"""

from __future__ import annotations

import ast
import re
from pathlib import Path

from structlog import get_logger

logger = get_logger(__name__)


class SQLInjectionAuditor:
    """Audit code for SQL injection vulnerabilities."""
    
    DANGEROUS_PATTERNS = [
        r'execute\(["\'].*\+.*["\']',  # String concatenation in execute
        r'execute\(f["\']',  # F-string in execute
        r'execute\(.*\.format\(',  # .format() in execute
        r'raw\(',  # Raw SQL
    ]
    
    def audit_file(self, file_path: Path) -> list[dict]:
        """Audit single file for SQL injection risks."""
        issues = []
        
        content = file_path.read_text()
        
        for pattern in self.DANGEROUS_PATTERNS:
            matches = re.finditer(pattern, content)
            for match in matches:
                issues.append({
                    "file": str(file_path),
                    "line": content[:match.start()].count("\n") + 1,
                    "pattern": pattern,
                    "code": match.group(),
                })
        
        return issues
    
    def audit_codebase(self, root_dir: Path = Path("app")) -> dict:
        """Audit entire codebase."""
        all_issues = []
        
        for py_file in root_dir.rglob("*.py"):
            issues = self.audit_file(py_file)
            all_issues.extend(issues)
        
        return {
            "total_issues": len(all_issues),
            "issues": all_issues,
        }


if __name__ == "__main__":
    auditor = SQLInjectionAuditor()
    results = auditor.audit_codebase()
    
    print(f"Found {results['total_issues']} potential SQL injection risks")
    
    for issue in results["issues"]:
        print(f"{issue['file']}:{issue['line']} - {issue['code']}")
```

### Step 2: Safe Query Patterns (2 hours)

**File:** `app/database/safe_queries.py`

```python
"""
Safe Query Patterns
Examples of secure database queries.
"""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from structlog import get_logger

from app.database.models.agent_execution import AgentExecution

logger = get_logger(__name__)


class SafeQueryExamples:
    """Examples of SQL injection-safe queries."""
    
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
    
    async def safe_select_by_id(self, agent_id: UUID) -> list[AgentExecution]:
        """
        ✅ SAFE: Using SQLAlchemy ORM with parameters.
        
        Args:
            agent_id: Agent identifier (validated as UUID)
            
        Returns:
            List of executions
        """
        query = select(AgentExecution).where(
            AgentExecution.agent_id == agent_id  # Parameterized
        )
        
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def unsafe_select_example(self, agent_id: str):
        """
        ❌ UNSAFE: String concatenation (DO NOT USE).
        
        This is an example of what NOT to do.
        """
        # NEVER DO THIS:
        # query = f"SELECT * FROM agent_executions WHERE agent_id = '{agent_id}'"
        # await self.db.execute(query)
        
        raise NotImplementedError("This is an unsafe pattern - do not use")
    
    async def safe_search_with_like(self, search_term: str) -> list:
        """
        ✅ SAFE: LIKE query with parameter binding.
        
        Args:
            search_term: Search term (sanitized)
            
        Returns:
            Matching records
        """
        # Sanitize search term
        sanitized = search_term.replace("%", "\\%").replace("_", "\\_")
        
        query = select(AgentExecution).where(
            AgentExecution.error_message.like(f"%{sanitized}%")
        )
        
        result = await self.db.execute(query)
        return result.scalars().all()
```

### Step 3: Input Validation (1 hour)

**File:** `app/api/validators.py`

```python
"""
Input Validators
Pydantic validators for SQL injection prevention.
"""

from __future__ import annotations

import re
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class SafeSearchRequest(BaseModel):
    """Safe search request with validation."""
    
    query: str = Field(..., min_length=1, max_length=500)
    agent_id: UUID | None = None
    
    @field_validator("query")
    @classmethod
    def validate_query(cls, v: str) -> str:
        """Validate search query for safety."""
        # Remove potentially dangerous characters
        dangerous_chars = [";", "--", "/*", "*/", "xp_", "sp_"]
        
        for char in dangerous_chars:
            if char in v.lower():
                raise ValueError(f"Invalid character sequence: {char}")
        
        return v.strip()
```

### Step 4: Security Tests (1 hour)

**File:** `tests/security/test_sql_injection.py`

```python
"""
SQL Injection Security Tests
Tests for SQL injection vulnerabilities.
"""

import pytest
from uuid import uuid4

from app.database.safe_queries import SafeQueryExamples


@pytest.mark.asyncio
async def test_safe_query_with_malicious_input(db_session):
    """Test that malicious input is safely handled."""
    service = SafeQueryExamples(db_session)
    
    # Malicious UUID attempt (will fail UUID validation)
    with pytest.raises(ValueError):
        malicious_id = "1' OR '1'='1"
        UUID(malicious_id)  # UUID validation prevents injection
    
    # Valid UUID is safe
    safe_id = uuid4()
    results = await service.safe_select_by_id(safe_id)
    assert isinstance(results, list)


@pytest.mark.asyncio
async def test_search_with_sql_injection_attempt(db_session):
    """Test search with SQL injection attempt."""
    service = SafeQueryExamples(db_session)
    
    # Attempt SQL injection in search
    malicious_search = "test'; DROP TABLE agent_executions; --"
    
    # Should be safely escaped
    results = await service.safe_search_with_like(malicious_search)
    
    # No SQL injection occurred (table still exists)
    assert isinstance(results, list)


@pytest.mark.asyncio
async def test_input_validation_blocks_injection(db_session):
    """Test that input validation blocks SQL injection."""
    from app.api.validators import SafeSearchRequest
    
    # Should raise validation error
    with pytest.raises(ValueError):
        SafeSearchRequest(query="test; DROP TABLE users;")
```

---

## ✅ DEFINITION OF DONE

- [ ] All queries use SQLAlchemy ORM
- [ ] No raw SQL string concatenation
- [ ] Input validation implemented
- [ ] Security tests passing
- [ ] Bandit scan clean
- [ ] Code audit complete

---

## 📊 SUCCESS METRICS

- SQL injection vulnerabilities: 0
- Bandit security score: A
- Test coverage: >90%
- All security tests passing

---

**Estimated Completion:** 6 hours  
**Status:** NOT STARTED

