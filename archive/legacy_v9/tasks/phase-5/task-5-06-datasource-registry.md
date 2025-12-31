# Task 5-06: Data Source Registry Implementation

**Phase:** 5 - Cognitive Architecture & Self-Improvement  
**Week:** 22  
**Estimated Hours:** 12 hours  
**Priority:** MEDIUM  
**Dependencies:** Task 5-04 (Ingestion Scribe)

---

## 🎯 OBJECTIVE

Implement Data Source Registry for managing external knowledge sources (documentation sites, APIs, databases) that can be ingested into the memory system.

---

## 📋 REQUIREMENTS

### Functional Requirements
- Register external data sources
- Schedule periodic ingestion
- Track ingestion status
- Support multiple source types (web, API, database)
- Handle authentication for sources

### Technical Requirements
- FastAPI service or database model
- Celery for scheduled tasks
- Source connectors (web scraper, API client)
- Integration with Ingestion Scribe

### Performance Requirements
- Source registration: <1 second
- Ingestion scheduling: <500ms
- Concurrent sources: Up to 50

---

## 🔧 IMPLEMENTATION

**File:** `app/services/datasource_registry.py`

```python
"""
Data Source Registry
Manages external knowledge sources for ingestion.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, HttpUrl
from structlog import get_logger

logger = get_logger(__name__)


class SourceType(str, Enum):
    """Type of data source."""
    
    WEB = "WEB"  # Web scraping
    API = "API"  # REST API
    DATABASE = "DATABASE"  # Database query
    FILE = "FILE"  # File upload


class DataSource(BaseModel):
    """External data source."""
    
    source_id: UUID = Field(default_factory=uuid4)
    name: str
    source_type: SourceType
    url: HttpUrl | None = None
    config: dict[str, any] = Field(default_factory=dict)
    schedule: str | None = None  # Cron expression
    last_ingestion: datetime | None = None
    status: str = "ACTIVE"  # ACTIVE, PAUSED, ERROR


class DataSourceRegistry:
    """
    Data Source Registry
    
    Manages external knowledge sources.
    """
    
    def __init__(self) -> None:
        self.logger = logger.bind(service="datasource_registry")
        self._sources: dict[UUID, DataSource] = {}
    
    async def register_source(self, source: DataSource) -> UUID:
        """Register new data source."""
        self.logger.info(
            "registering_source",
            source_id=str(source.source_id),
            name=source.name,
            type=source.source_type.value,
        )
        
        self._sources[source.source_id] = source
        
        # Schedule ingestion if schedule provided
        if source.schedule:
            await self._schedule_ingestion(source)
        
        return source.source_id
    
    async def ingest_source(self, source_id: UUID) -> None:
        """Trigger ingestion from source."""
        source = self._sources.get(source_id)
        if not source:
            raise ValueError(f"Source not found: {source_id}")
        
        self.logger.info("ingesting_source", source_id=str(source_id))
        
        # Fetch data from source
        data = await self._fetch_data(source)
        
        # Send to Ingestion Scribe
        # await ingestion_scribe.ingest_batch(data)
        
        # Update last ingestion time
        source.last_ingestion = datetime.utcnow()
    
    async def _fetch_data(self, source: DataSource) -> list[dict]:
        """Fetch data from source."""
        match source.source_type:
            case SourceType.WEB:
                return await self._scrape_web(source)
            case SourceType.API:
                return await self._fetch_api(source)
            case SourceType.DATABASE:
                return await self._query_database(source)
            case _:
                return []
    
    async def _scrape_web(self, source: DataSource) -> list[dict]:
        """Scrape web source."""
        # Implementation would use BeautifulSoup or similar
        return []
    
    async def _fetch_api(self, source: DataSource) -> list[dict]:
        """Fetch from API."""
        # Implementation would use httpx
        return []
    
    async def _query_database(self, source: DataSource) -> list[dict]:
        """Query database."""
        # Implementation would use SQLAlchemy
        return []
    
    async def _schedule_ingestion(self, source: DataSource) -> None:
        """Schedule periodic ingestion."""
        # Implementation would use Celery or similar
        pass
```

---

## ✅ DEFINITION OF DONE

- [ ] Data Source Registry implemented
- [ ] Source registration working
- [ ] Ingestion scheduling functional
- [ ] Multiple source types supported
- [ ] Tests passing (>80% coverage)

---

## 📊 SUCCESS METRICS

- Source registration: <1s
- Concurrent sources: 50+
- Test coverage: >80%

---

**Estimated Completion:** 12 hours  
**Status:** NOT STARTED

