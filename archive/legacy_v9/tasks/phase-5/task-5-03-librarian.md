# Task 5-03: Librarian (Long-Term Memory) Implementation

**Phase:** 5 - Cognitive Architecture & Self-Improvement  
**Week:** 21  
**Estimated Hours:** 16 hours  
**Priority:** HIGH  
**Dependencies:** Task 5-01 (Memory Coordinator)

---

## 🎯 OBJECTIVE

Implement Librarian agent for managing long-term memory using vector database (ChromaDB/Weaviate). Handles persistent knowledge, execution patterns, and semantic search.

---

## 📋 REQUIREMENTS

### Functional Requirements
- Store/retrieve long-term memory with embeddings
- Semantic search capabilities
- Knowledge categorization
- Memory consolidation
- Pattern recognition

### Technical Requirements
- Vector database integration (ChromaDB)
- Embedding generation via Oracle
- Metadata filtering
- Similarity search

### Performance Requirements
- Store operation: <1 second
- Search query: <2 seconds
- Storage capacity: Unlimited

---

## 🔧 IMPLEMENTATION

**File:** `app/agents/librarian.py`

```python
"""
Librarian - Long-Term Memory Specialist
Manages persistent knowledge in vector database.
"""

from __future__ import annotations

from typing import Any
from uuid import UUID, uuid4

import chromadb
from pydantic import BaseModel, Field
from structlog import get_logger

logger = get_logger(__name__)


class MemoryEntry(BaseModel):
    """Long-term memory entry."""
    
    entry_id: UUID = Field(default_factory=uuid4)
    content: str
    category: str
    metadata: dict[str, Any] = Field(default_factory=dict)
    embedding: list[float] | None = None


class LibrarianAgent:
    """
    Librarian Agent - Long-Term Memory (Vector DB)
    
    Manages persistent knowledge with semantic search.
    """
    
    def __init__(self, persist_directory: str = "./data/librarian") -> None:
        self.client = chromadb.Client(chromadb.Settings(
            persist_directory=persist_directory,
        ))
        self.collection = self.client.get_or_create_collection("long_term_memory")
        self.logger = logger.bind(agent="librarian")
    
    async def store(
        self,
        content: str,
        category: str,
        metadata: dict[str, Any] | None = None,
        embedding: list[float] | None = None,
    ) -> UUID:
        """Store in long-term memory."""
        entry_id = uuid4()
        
        # Generate embedding if not provided
        if embedding is None:
            embedding = await self._generate_embedding(content)
        
        self.collection.add(
            ids=[str(entry_id)],
            embeddings=[embedding],
            documents=[content],
            metadatas=[{
                "category": category,
                **(metadata or {}),
            }],
        )
        
        self.logger.info("memory_stored", entry_id=str(entry_id), category=category)
        return entry_id
    
    async def search(
        self,
        query: str,
        category: str | None = None,
        limit: int = 5,
    ) -> list[MemoryEntry]:
        """Search long-term memory."""
        query_embedding = await self._generate_embedding(query)
        
        where_filter = {"category": category} if category else None
        
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=limit,
            where=where_filter,
        )
        
        entries = []
        if results["ids"] and results["ids"][0]:
            for i, entry_id in enumerate(results["ids"][0]):
                entries.append(MemoryEntry(
                    entry_id=UUID(entry_id),
                    content=results["documents"][0][i],
                    category=results["metadatas"][0][i]["category"],
                    metadata=results["metadatas"][0][i],
                ))
        
        return entries
    
    async def _generate_embedding(self, text: str) -> list[float]:
        """Generate embedding for text."""
        # Call Oracle service for embedding
        # For now, return mock embedding
        return [0.1] * 384
```

---

## ✅ DEFINITION OF DONE

- [ ] Librarian agent implemented
- [ ] Vector DB integration working
- [ ] Semantic search functional
- [ ] Tests passing (>85% coverage)

---

## 📊 SUCCESS METRICS

- Store operation: <1s
- Search query: <2s
- Test coverage: >85%

---

**Estimated Completion:** 16 hours  
**Status:** NOT STARTED

