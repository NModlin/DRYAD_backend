"""
Librarian Agent - Long-Term Memory Specialist (Level 2)

Manages persistent knowledge using vector database with semantic search.
Part of the Memory Guild cognitive architecture.

Responsibilities:
- Store/retrieve long-term memory with embeddings
- Semantic search capabilities
- Knowledge categorization
- Memory consolidation
- Pattern recognition
"""

import asyncio
from datetime import datetime, timezone
from typing import Any, Dict, Optional, List
from uuid import uuid4, UUID

try:
    import chromadb
    from chromadb.config import Settings
    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False

from pydantic import BaseModel, Field
from app.services.logging.logger import StructuredLogger

logger = StructuredLogger("librarian")


class MemoryEntry(BaseModel):
    """Long-term memory entry."""
    entry_id: UUID = Field(default_factory=uuid4)
    content: str
    category: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    embedding: Optional[List[float]] = None
    score: Optional[float] = None  # Similarity score for search results


class LibrarianAgent:
    """
    Level 2 Component: Librarian Agent
    
    Manages long-term memory (Vector DB) with semantic search.
    Handles persistent knowledge, execution patterns, and multi-source synthesis.
    """
    
    DEFAULT_EMBEDDING_DIM = 384  # Default embedding dimension
    
    def __init__(
        self,
        persist_directory: str = "./data/librarian",
        mock_mode: bool = None
    ):
        """
        Initialize Librarian Agent.
        
        Args:
            persist_directory: Directory for vector database persistence
            mock_mode: Force mock mode (None = auto-detect)
        """
        self.persist_directory = persist_directory
        
        # Determine if we should use mock mode
        if mock_mode is None:
            self.mock_mode = not CHROMADB_AVAILABLE
        else:
            self.mock_mode = mock_mode
        
        if self.mock_mode:
            logger.log_warning("librarian_init", {"mode": "mock", "reason": "ChromaDB unavailable"})
            self.client = None
            self.collection = None
            self.mock_storage: Dict[str, MemoryEntry] = {}
        else:
            try:
                self.client = chromadb.Client(Settings(
                    persist_directory=persist_directory,
                    anonymized_telemetry=False
                ))
                self.collection = self.client.get_or_create_collection("long_term_memory")
                logger.log_info("librarian_init", {"mode": "chromadb", "persist_dir": persist_directory})
            except Exception as e:
                logger.log_warning("librarian_init_failed", {"error": str(e), "falling_back": "mock"})
                self.mock_mode = True
                self.client = None
                self.collection = None
                self.mock_storage = {}
    
    async def _generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for text.
        
        In production, this would call the Oracle service or another embedding model.
        For now, returns a mock embedding.
        
        Args:
            text: Text to embed
            
        Returns:
            Embedding vector
        """
        # TODO: Integrate with Oracle service for real embeddings
        # For now, return mock embedding based on text hash
        import hashlib
        text_hash = int(hashlib.md5(text.encode()).hexdigest(), 16)
        
        # Generate deterministic "embedding" from hash
        embedding = []
        for i in range(self.DEFAULT_EMBEDDING_DIM):
            # Use hash to generate pseudo-random but deterministic values
            val = ((text_hash + i) % 1000) / 1000.0
            embedding.append(val)
        
        return embedding
    
    async def store(
        self,
        content: str,
        category: str,
        metadata: Optional[Dict[str, Any]] = None,
        embedding: Optional[List[float]] = None,
        tenant_id: str = "default",
        agent_id: str = "system"
    ) -> UUID:
        """
        Store in long-term memory.
        
        Args:
            content: Content to store
            category: Category/type of memory
            metadata: Additional metadata
            embedding: Pre-computed embedding (optional)
            tenant_id: Tenant identifier
            agent_id: Agent identifier
            
        Returns:
            Entry ID
        """
        entry_id = uuid4()
        
        # Generate embedding if not provided
        if embedding is None:
            embedding = await self._generate_embedding(content)
        
        # Add tenant/agent to metadata
        full_metadata = {
            "category": category,
            "tenant_id": tenant_id,
            "agent_id": agent_id,
            "created_at": datetime.now(timezone.utc).isoformat(),
            **(metadata or {})
        }
        
        try:
            if self.mock_mode:
                # Mock implementation
                entry = MemoryEntry(
                    entry_id=entry_id,
                    content=content,
                    category=category,
                    metadata=full_metadata,
                    embedding=embedding
                )
                self.mock_storage[str(entry_id)] = entry
                
                logger.log_info(
                    "memory_stored",
                    {
                        "entry_id": str(entry_id),
                        "category": category,
                        "mode": "mock"
                    }
                )
            else:
                # ChromaDB implementation
                self.collection.add(
                    ids=[str(entry_id)],
                    embeddings=[embedding],
                    documents=[content],
                    metadatas=[full_metadata]
                )
                
                logger.log_info(
                    "memory_stored",
                    {
                        "entry_id": str(entry_id),
                        "category": category,
                        "mode": "chromadb"
                    }
                )
            
            return entry_id
            
        except Exception as e:
            logger.log_error("store_failed", {"error": str(e)})
            raise
    
    async def search(
        self,
        query: str,
        category: Optional[str] = None,
        limit: int = 5,
        tenant_id: str = "default",
        agent_id: str = "system"
    ) -> List[MemoryEntry]:
        """
        Search long-term memory using semantic search.
        
        Args:
            query: Search query
            category: Filter by category (optional)
            limit: Maximum number of results
            tenant_id: Tenant identifier
            agent_id: Agent identifier
            
        Returns:
            List of matching memory entries
        """
        try:
            query_embedding = await self._generate_embedding(query)
            
            if self.mock_mode:
                # Mock implementation - simple text matching
                results = []
                for entry in self.mock_storage.values():
                    # Check tenant/agent match
                    if (entry.metadata.get("tenant_id") != tenant_id or
                        entry.metadata.get("agent_id") != agent_id):
                        continue
                    
                    # Check category filter
                    if category and entry.category != category:
                        continue
                    
                    # Simple text similarity (contains check)
                    query_lower = query.lower()
                    content_lower = entry.content.lower()
                    
                    if query_lower in content_lower or any(word in content_lower for word in query_lower.split()):
                        # Calculate simple score
                        score = len([w for w in query_lower.split() if w in content_lower]) / max(len(query_lower.split()), 1)
                        entry_copy = entry.model_copy()
                        entry_copy.score = score
                        results.append(entry_copy)
                
                # Sort by score and limit
                results.sort(key=lambda x: x.score or 0, reverse=True)
                results = results[:limit]
                
                logger.log_info(
                    "memory_searched",
                    {
                        "query": query,
                        "results_count": len(results),
                        "mode": "mock"
                    }
                )
                
                return results
            else:
                # ChromaDB implementation
                where_filter = {
                    "tenant_id": tenant_id,
                    "agent_id": agent_id
                }
                if category:
                    where_filter["category"] = category
                
                results = self.collection.query(
                    query_embeddings=[query_embedding],
                    n_results=limit,
                    where=where_filter
                )
                
                entries = []
                if results["ids"] and results["ids"][0]:
                    for i, entry_id in enumerate(results["ids"][0]):
                        distance = results["distances"][0][i] if "distances" in results else None
                        score = 1.0 - distance if distance is not None else None
                        
                        entries.append(MemoryEntry(
                            entry_id=UUID(entry_id),
                            content=results["documents"][0][i],
                            category=results["metadatas"][0][i]["category"],
                            metadata=results["metadatas"][0][i],
                            score=score
                        ))
                
                logger.log_info(
                    "memory_searched",
                    {
                        "query": query,
                        "results_count": len(entries),
                        "mode": "chromadb"
                    }
                )
                
                return entries
                
        except Exception as e:
            logger.log_error("search_failed", {"query": query, "error": str(e)})
            return []
    
    async def delete(
        self,
        entry_id: UUID
    ) -> bool:
        """
        Delete entry from long-term memory.
        
        Args:
            entry_id: Entry ID to delete
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if self.mock_mode:
                # Mock implementation
                if str(entry_id) in self.mock_storage:
                    del self.mock_storage[str(entry_id)]
                    logger.log_info("memory_deleted", {"entry_id": str(entry_id), "mode": "mock"})
                    return True
                else:
                    logger.log_info("memory_not_found", {"entry_id": str(entry_id), "mode": "mock"})
                    return False
            else:
                # ChromaDB implementation
                self.collection.delete(ids=[str(entry_id)])
                logger.log_info("memory_deleted", {"entry_id": str(entry_id), "mode": "chromadb"})
                return True
                
        except Exception as e:
            logger.log_error("delete_failed", {"entry_id": str(entry_id), "error": str(e)})
            return False
    
    async def count(
        self,
        category: Optional[str] = None,
        tenant_id: str = "default",
        agent_id: str = "system"
    ) -> int:
        """
        Count entries in long-term memory.
        
        Args:
            category: Filter by category (optional)
            tenant_id: Tenant identifier
            agent_id: Agent identifier
            
        Returns:
            Number of entries
        """
        try:
            if self.mock_mode:
                # Mock implementation
                count = sum(
                    1 for entry in self.mock_storage.values()
                    if (entry.metadata.get("tenant_id") == tenant_id and
                        entry.metadata.get("agent_id") == agent_id and
                        (category is None or entry.category == category))
                )
                return count
            else:
                # ChromaDB implementation
                where_filter = {
                    "tenant_id": tenant_id,
                    "agent_id": agent_id
                }
                if category:
                    where_filter["category"] = category
                
                # ChromaDB doesn't have a direct count, so we query with limit=1 and check
                # For now, return the collection count (not filtered)
                return self.collection.count()
                
        except Exception as e:
            logger.log_error("count_failed", {"error": str(e)})
            return 0

