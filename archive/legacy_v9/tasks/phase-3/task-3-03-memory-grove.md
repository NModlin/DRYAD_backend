# Task 3-03: Memory Grove (Knowledge Storage) Implementation

**Phase:** 3 - Advanced Collaboration & Governance  
**Week:** 13  
**Estimated Hours:** 12 hours  
**Priority:** HIGH  
**Dependencies:** Task 3-01 (Path Finder)

---

## 🎯 OBJECTIVE

Implement Memory Grove - a vector database-backed knowledge storage system that stores execution patterns, successful solutions, and learned knowledge for retrieval by Path Finder and other agents.

---

## 📋 REQUIREMENTS

### Functional Requirements
- Store execution plans and results as embeddings
- Enable semantic search for similar past solutions
- Track success/failure patterns
- Support knowledge generalization
- Provide relevance scoring for retrieved patterns
- Enable knowledge pruning and archival

### Technical Requirements
- ChromaDB or Weaviate integration
- Async/await patterns for database operations
- Embedding generation via Oracle/LLM
- Metadata filtering capabilities
- Comprehensive logging

### Performance Requirements
- Query response time: <2 seconds
- Embedding generation: <5 seconds
- Storage operation: <1 second
- Concurrent queries: Up to 20

---

## 🔧 IMPLEMENTATION STEPS

### Step 1: Create Memory Grove Service (10 hours)

**File:** `app/services/memory_grove.py`

```python
"""
Memory Grove - Vector Database Knowledge Storage
Stores and retrieves execution patterns using semantic search.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

import chromadb
from chromadb.config import Settings
from pydantic import BaseModel, Field
from structlog import get_logger

from app.core.oracle import OracleService

logger = get_logger(__name__)


class ExecutionPattern(BaseModel):
    """Stored execution pattern with metadata."""
    
    pattern_id: UUID = Field(default_factory=uuid4)
    request: str
    plan_summary: str
    result_summary: str
    success: bool
    execution_time_hours: float
    tags: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class RetrievedPattern(BaseModel):
    """Retrieved pattern with relevance score."""
    
    pattern: ExecutionPattern
    relevance_score: float = Field(ge=0.0, le=1.0)
    distance: float


class MemoryGroveService:
    """
    Memory Grove Service
    
    Vector database for storing and retrieving execution patterns
    using semantic search.
    """
    
    def __init__(
        self,
        oracle_service: OracleService,
        collection_name: str = "execution_patterns",
        persist_directory: str = "./data/memory_grove",
    ) -> None:
        self.oracle = oracle_service
        self.logger = logger.bind(service="memory_grove")
        
        # Initialize ChromaDB
        self.client = chromadb.Client(Settings(
            persist_directory=persist_directory,
            anonymized_telemetry=False,
        ))
        
        # Get or create collection
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"description": "Execution patterns and learned knowledge"},
        )
    
    async def store_execution_pattern(
        self,
        request: str,
        plan: Any,  # ExecutionPlanModel
        result: dict[str, Any],
        success: bool,
    ) -> UUID:
        """
        Store execution pattern in Memory Grove.
        
        Args:
            request: Original natural language request
            plan: Execution plan that was used
            result: Execution result
            success: Whether execution succeeded
            
        Returns:
            Pattern ID
        """
        pattern_id = uuid4()
        
        self.logger.info(
            "storing_pattern",
            pattern_id=str(pattern_id),
            success=success,
        )
        
        try:
            # Create pattern summary
            plan_summary = self._summarize_plan(plan)
            result_summary = self._summarize_result(result)
            
            # Generate embedding
            embedding_text = f"""
Request: {request}
Plan: {plan_summary}
Result: {result_summary}
Success: {success}
"""
            
            embedding = await self._generate_embedding(embedding_text)
            
            # Create pattern
            pattern = ExecutionPattern(
                pattern_id=pattern_id,
                request=request,
                plan_summary=plan_summary,
                result_summary=result_summary,
                success=success,
                execution_time_hours=plan.total_estimated_hours,
                tags=self._extract_tags(request, plan),
                metadata={
                    "plan_id": str(plan.plan_id),
                    "step_count": len(plan.steps),
                    "risk_level": plan.overall_risk_level,
                },
            )
            
            # Store in ChromaDB
            self.collection.add(
                ids=[str(pattern_id)],
                embeddings=[embedding],
                documents=[embedding_text],
                metadatas=[{
                    "request": request,
                    "success": success,
                    "execution_time_hours": pattern.execution_time_hours,
                    "created_at": pattern.created_at.isoformat(),
                    **pattern.metadata,
                }],
            )
            
            self.logger.info(
                "pattern_stored",
                pattern_id=str(pattern_id),
            )
            
            return pattern_id
            
        except Exception as e:
            self.logger.error(
                "pattern_storage_failed",
                pattern_id=str(pattern_id),
                error=str(e),
            )
            raise
    
    async def query_similar_patterns(
        self,
        request: str,
        limit: int = 5,
        success_only: bool = True,
    ) -> list[RetrievedPattern]:
        """
        Query for similar execution patterns.
        
        Args:
            request: Natural language request to match
            limit: Maximum number of results
            success_only: Only return successful patterns
            
        Returns:
            List of similar patterns with relevance scores
        """
        self.logger.info(
            "querying_patterns",
            request=request[:100],
            limit=limit,
        )
        
        try:
            # Generate query embedding
            embedding = await self._generate_embedding(request)
            
            # Build where filter
            where_filter = {"success": True} if success_only else None
            
            # Query ChromaDB
            results = self.collection.query(
                query_embeddings=[embedding],
                n_results=limit,
                where=where_filter,
            )
            
            # Parse results
            patterns: list[RetrievedPattern] = []
            
            if results["ids"] and results["ids"][0]:
                for i, pattern_id in enumerate(results["ids"][0]):
                    metadata = results["metadatas"][0][i]
                    distance = results["distances"][0][i]
                    
                    # Convert distance to relevance score (0-1)
                    relevance_score = max(0.0, 1.0 - distance)
                    
                    pattern = ExecutionPattern(
                        pattern_id=UUID(pattern_id),
                        request=metadata["request"],
                        plan_summary=metadata.get("plan_summary", ""),
                        result_summary=metadata.get("result_summary", ""),
                        success=metadata["success"],
                        execution_time_hours=metadata["execution_time_hours"],
                        created_at=datetime.fromisoformat(metadata["created_at"]),
                        metadata={
                            k: v for k, v in metadata.items()
                            if k not in ["request", "success", "execution_time_hours", "created_at"]
                        },
                    )
                    
                    patterns.append(RetrievedPattern(
                        pattern=pattern,
                        relevance_score=relevance_score,
                        distance=distance,
                    ))
            
            self.logger.info(
                "patterns_retrieved",
                count=len(patterns),
            )
            
            return patterns
            
        except Exception as e:
            self.logger.error(
                "pattern_query_failed",
                error=str(e),
            )
            raise
    
    async def _generate_embedding(self, text: str) -> list[float]:
        """Generate embedding vector for text."""
        # Use Oracle to generate embeddings
        # In production, use dedicated embedding model
        response = await self.oracle.generate_embedding(text)
        return response
    
    def _summarize_plan(self, plan: Any) -> str:
        """Create concise plan summary."""
        steps_summary = "; ".join([
            f"{step.step_number}. {step.action}"
            for step in plan.steps[:5]  # First 5 steps
        ])
        
        if len(plan.steps) > 5:
            steps_summary += f" ... ({len(plan.steps) - 5} more steps)"
        
        return steps_summary
    
    def _summarize_result(self, result: dict[str, Any]) -> str:
        """Create concise result summary."""
        success = result.get("success", False)
        status = "SUCCESS" if success else "FAILED"
        
        summary = f"{status}"
        
        if "validation" in result:
            validation = result["validation"]
            if "all_passed" in validation:
                summary += f" - Validation: {'PASSED' if validation['all_passed'] else 'FAILED'}"
        
        return summary
    
    def _extract_tags(self, request: str, plan: Any) -> list[str]:
        """Extract relevant tags from request and plan."""
        tags: set[str] = set()
        
        # Add risk level tag
        tags.add(f"risk:{plan.overall_risk_level.lower()}")
        
        # Add complexity tag
        if plan.total_estimated_hours < 4:
            tags.add("complexity:simple")
        elif plan.total_estimated_hours < 16:
            tags.add("complexity:moderate")
        else:
            tags.add("complexity:complex")
        
        # Extract keywords from request
        keywords = ["api", "database", "auth", "test", "deploy", "security"]
        for keyword in keywords:
            if keyword in request.lower():
                tags.add(f"domain:{keyword}")
        
        return sorted(list(tags))
    
    async def get_pattern_by_id(self, pattern_id: UUID) -> ExecutionPattern | None:
        """Retrieve specific pattern by ID."""
        try:
            result = self.collection.get(
                ids=[str(pattern_id)],
                include=["metadatas"],
            )
            
            if result["ids"]:
                metadata = result["metadatas"][0]
                
                return ExecutionPattern(
                    pattern_id=pattern_id,
                    request=metadata["request"],
                    plan_summary=metadata.get("plan_summary", ""),
                    result_summary=metadata.get("result_summary", ""),
                    success=metadata["success"],
                    execution_time_hours=metadata["execution_time_hours"],
                    created_at=datetime.fromisoformat(metadata["created_at"]),
                )
            
            return None
            
        except Exception as e:
            self.logger.error(
                "pattern_retrieval_failed",
                pattern_id=str(pattern_id),
                error=str(e),
            )
            return None
    
    def get_collection_stats(self) -> dict[str, Any]:
        """Get Memory Grove statistics."""
        count = self.collection.count()
        
        return {
            "total_patterns": count,
            "collection_name": self.collection.name,
        }
```

### Step 2: Create Tests (2 hours)

**File:** `tests/test_memory_grove.py`

```python
"""Tests for Memory Grove service."""

import pytest
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from app.services.memory_grove import MemoryGroveService, ExecutionPattern
from app.services.architect_agent import ExecutionPlanModel, PlanStep


@pytest.fixture
def mock_oracle():
    """Mock Oracle service."""
    oracle = AsyncMock()
    oracle.generate_embedding.return_value = [0.1] * 384  # Mock embedding
    return oracle


@pytest.fixture
def memory_grove(mock_oracle, tmp_path):
    """Create Memory Grove instance."""
    return MemoryGroveService(
        oracle_service=mock_oracle,
        persist_directory=str(tmp_path / "test_grove"),
    )


@pytest.fixture
def sample_plan():
    """Create sample execution plan."""
    return ExecutionPlanModel(
        plan_id=uuid4(),
        request="Add logging to API endpoints",
        steps=[
            PlanStep(
                step_number=1,
                action="Add logging middleware",
                estimated_hours=2.0,
                risk_level="LOW",
            )
        ],
        total_estimated_hours=2.0,
        overall_risk_level="LOW",
    )


@pytest.mark.asyncio
async def test_store_execution_pattern(memory_grove, sample_plan):
    """Test storing execution pattern."""
    pattern_id = await memory_grove.store_execution_pattern(
        request="Add logging to API endpoints",
        plan=sample_plan,
        result={"success": True},
        success=True,
    )
    
    assert pattern_id is not None
    
    # Verify pattern can be retrieved
    pattern = await memory_grove.get_pattern_by_id(pattern_id)
    assert pattern is not None
    assert pattern.success is True


@pytest.mark.asyncio
async def test_query_similar_patterns(memory_grove, sample_plan):
    """Test querying similar patterns."""
    # Store a pattern first
    await memory_grove.store_execution_pattern(
        request="Add logging to API endpoints",
        plan=sample_plan,
        result={"success": True},
        success=True,
    )
    
    # Query for similar patterns
    results = await memory_grove.query_similar_patterns(
        request="Add logging to endpoints",
        limit=5,
    )
    
    assert len(results) > 0
    assert results[0].pattern.success is True
    assert 0.0 <= results[0].relevance_score <= 1.0
```

---

## ✅ DEFINITION OF DONE

- [ ] Memory Grove service implemented
- [ ] ChromaDB integration working
- [ ] Embedding generation functional
- [ ] Pattern storage operational
- [ ] Semantic search working
- [ ] All tests passing (>85% coverage)
- [ ] Documentation complete

---

## 📊 SUCCESS METRICS

- Query response time: <2 seconds
- Storage success rate: >99%
- Retrieval accuracy: >85%
- Test coverage: >85%

---

**Estimated Completion:** 12 hours  
**Assigned To:** Backend Developer  
**Status:** NOT STARTED

