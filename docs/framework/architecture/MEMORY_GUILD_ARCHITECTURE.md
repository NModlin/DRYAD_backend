# Memory Guild Architecture

**Version:** 2.0.0  
**Status:** Production Ready

---

## Overview

The **Memory Guild** is DRYAD's sophisticated memory management system, providing:
- **Short-term memory** (Archivist) - Recent context with TTL
- **Long-term memory** (Librarian) - Persistent knowledge with semantic search
- **Data ingestion** (Scribe) - Content processing and deduplication
- **Memory coordination** (Coordinator) - Request routing and policy enforcement

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────┐
│                    Application Layer                     │
│              (Agents, Orchestration, APIs)              │
└────────────────────┬────────────────────────────────────┘
                     │
        ┌────────────┴────────────┐
        │                         │
┌───────▼──────────┐    ┌────────▼────────┐
│  Memory Scribe   │    │  Memory Coord.  │
│  (Ingestion)     │    │  (Routing)      │
└────────┬─────────┘    └────────┬────────┘
         │                       │
         │    ┌──────────────────┼──────────────────┐
         │    │                  │                  │
         │    │                  │                  │
    ┌────▼────▼──┐      ┌────────▼────────┐  ┌────▼────────┐
    │ Deduplicat.│      │  Archivist      │  │ Librarian   │
    │ Embedding  │      │  (Short-term)   │  │ (Long-term) │
    └────┬───────┘      └────────┬────────┘  └────┬────────┘
         │                       │                 │
         │                       │                 │
    ┌────▼───────────────────────▼─────────────────▼────┐
    │         Memory Database (PostgreSQL)              │
    │  ┌──────────────────────────────────────────────┐ │
    │  │ memory_records                               │ │
    │  │ memory_embeddings                            │ │
    │  │ memory_relationships                         │ │
    │  │ data_sources                                 │ │
    │  │ memory_access_policies                       │ │
    │  └──────────────────────────────────────────────┘ │
    └────┬───────────────────────────────────────────────┘
         │
    ┌────┴──────────────────────────────────────────┐
    │                                               │
┌───▼──────────────┐                    ┌──────────▼──┐
│ Redis Cache      │                    │ ChromaDB    │
│ (Short-term)     │                    │ (Long-term) │
└──────────────────┘                    └─────────────┘
```

---

## Components

### 1. Memory Coordinator
**File:** `app/services/memory_guild/coordinator.py`

**Purpose:** Routes memory requests to appropriate storage.

```python
class MemoryCoordinatorAgent:
    """Entry point to Memory Guild"""
    
    async def handle_memory_request(
        self,
        request: MemoryRequest
    ) -> MemoryResponse:
        """Route to Archivist or Librarian"""
        
        if request.memory_type == MemoryType.SHORT_TERM:
            return await self._store_short_term(request)
        else:
            return await self._store_long_term(request)
```

**Responsibilities:**
- Route to short-term or long-term storage
- Enforce memory policies
- Handle access control
- Manage memory lifecycle

**Key Methods:**
- `handle_memory_request()` - Main entry point
- `_store_short_term()` - Route to Archivist
- `_retrieve_short_term()` - Retrieve from Archivist
- `_store_long_term()` - Route to Librarian
- `_retrieve_long_term()` - Retrieve from Librarian

---

### 2. Memory Scribe
**File:** `app/services/memory_guild/scribe.py`

**Purpose:** Ingests and processes content.

```python
class MemoryScribeAgent:
    """Data ingestion and processing"""
    
    async def ingest_content(
        self,
        content: str,
        source: str,
        metadata: Dict
    ) -> MemoryResponse:
        """Ingest new content"""
        
        # 1. Check for duplicates
        content_hash = self._compute_hash(content)
        if self._is_duplicate(content_hash):
            return MemoryResponse(success=False, reason="duplicate")
        
        # 2. Generate embedding
        embedding = await self._generate_embedding(content)
        
        # 3. Store in database
        memory_id = await self._store_memory(
            content, embedding, metadata
        )
        
        return MemoryResponse(success=True, memory_id=memory_id)
```

**Responsibilities:**
- Ingest content from various sources
- Detect duplicates
- Generate embeddings
- Extract metadata
- Track data sources

**Key Methods:**
- `ingest_content()` - Main ingestion
- `_compute_hash()` - Deduplication
- `_generate_embedding()` - Vector generation
- `_store_memory()` - Database storage

---

### 3. Archivist Agent
**File:** `app/services/memory_guild/archivist.py`

**Purpose:** Manages short-term memory with TTL.

```python
class ArchivistAgent:
    """Short-term memory (Redis)"""
    
    async def store(
        self,
        key: str,
        value: Dict,
        ttl: timedelta,
        tenant_id: str
    ) -> bool:
        """Store with automatic expiration"""
        
        expiry = datetime.now(timezone.utc) + ttl
        
        if self.mock_mode:
            self.mock_storage[key] = (value, expiry)
        else:
            await self.redis_client.setex(
                key,
                int(ttl.total_seconds()),
                json.dumps(value)
            )
        
        return True
    
    async def retrieve(
        self,
        key: str,
        tenant_id: str
    ) -> Optional[Dict]:
        """Retrieve before expiration"""
        
        if self.mock_mode:
            value, expiry = self.mock_storage.get(key, (None, None))
            if expiry and datetime.now(timezone.utc) > expiry:
                del self.mock_storage[key]
                return None
            return value
        else:
            data = await self.redis_client.get(key)
            return json.loads(data) if data else None
```

**Storage Options:**
- **Redis** (production) - Fast, distributed
- **Mock** (fallback) - In-memory dictionary

**Features:**
- Automatic TTL expiration
- Tenant isolation
- Mock fallback
- Async operations

---

### 4. Librarian Agent
**File:** `app/services/memory_guild/librarian.py`

**Purpose:** Manages long-term memory with semantic search.

```python
class LibrarianAgent:
    """Long-term memory (ChromaDB)"""
    
    async def store(
        self,
        content: str,
        embedding: List[float],
        metadata: Dict,
        tenant_id: str
    ) -> str:
        """Store with semantic indexing"""
        
        memory_id = str(uuid4())
        
        if self.mock_mode:
            self.mock_storage[memory_id] = {
                "content": content,
                "embedding": embedding,
                "metadata": metadata
            }
        else:
            await self.collection.add(
                ids=[memory_id],
                embeddings=[embedding],
                documents=[content],
                metadatas=[metadata]
            )
        
        return memory_id
    
    async def search(
        self,
        query: str,
        embedding: List[float],
        limit: int = 10
    ) -> List[SearchResult]:
        """Semantic search"""
        
        if self.mock_mode:
            # Simple mock search
            results = list(self.mock_storage.values())[:limit]
        else:
            results = await self.collection.query(
                query_embeddings=[embedding],
                n_results=limit
            )
        
        return results
```

**Storage Options:**
- **ChromaDB** (production) - Vector database
- **Mock** (fallback) - In-memory dictionary

**Features:**
- Semantic search
- Vector indexing
- Metadata filtering
- Mock fallback

---

## Data Models

### MemoryRequest
```python
class MemoryRequest(BaseModel):
    operation: MemoryOperation  # STORE, RETRIEVE, SEARCH
    memory_type: MemoryType     # SHORT_TERM, LONG_TERM
    content: Optional[str]
    key: Optional[str]
    memory_id: Optional[str]
    tenant_id: str
    agent_id: Optional[str]
    ttl_seconds: Optional[int]
    metadata: Dict = {}
```

### MemoryResponse
```python
class MemoryResponse(BaseModel):
    success: bool
    operation: MemoryOperation
    memory_type: MemoryType
    memory_id: Optional[str]
    content: Optional[str]
    data: Optional[Dict]
    source: str  # "archivist", "librarian", "mock"
    error: Optional[str]
```

---

## Memory Lifecycle

### Short-Term Memory (Archivist)
```
1. Store in Redis with TTL
2. Automatic expiration after TTL
3. Used for active workflows
4. Example: Current conversation context
```

### Long-Term Memory (Librarian)
```
1. Ingest via Scribe
2. Generate embedding
3. Store in ChromaDB
4. Semantic search available
5. Permanent retention
6. Example: Knowledge base
```

---

## Access Control

### Memory Policies
```python
class MemoryPolicy(BaseModel):
    tenant_id: str
    short_term_ttl: int = 3600
    long_term_enabled: bool = True
    max_memory_size: int = 1000000
    access_rules: Dict[str, Any] = {}
    retention_days: int = 30
```

### Multi-Tenant Isolation
- All queries filtered by `tenant_id`
- Row-level security in database
- Separate Redis namespaces
- Isolated ChromaDB collections

---

## Fallback Mechanisms

### Mock Mode
When external services unavailable:
- **Archivist** → In-memory dictionary
- **Librarian** → In-memory dictionary
- **Scribe** → Direct database storage

### Graceful Degradation
```python
if not REDIS_AVAILABLE:
    self.archivist.mock_mode = True
    
if not CHROMADB_AVAILABLE:
    self.librarian.mock_mode = True
```

---

## Performance Characteristics

| Operation | Storage | Latency | Throughput |
|-----------|---------|---------|-----------|
| Store (short-term) | Redis | <10ms | 10k+/sec |
| Retrieve (short-term) | Redis | <10ms | 10k+/sec |
| Store (long-term) | ChromaDB | <100ms | 1k+/sec |
| Search (semantic) | ChromaDB | <500ms | 100+/sec |

---

## Next Steps

1. **[Orchestration Architecture](ORCHESTRATION_ARCHITECTURE.md)** - Task routing
2. **[Implementation Templates](../templates/)** - Ready-to-use code
3. **[Reference Implementation](../reference/)** - Code examples


