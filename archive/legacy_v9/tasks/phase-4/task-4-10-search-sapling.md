# Task 4-10: Search Sapling (Discovery-Only Deployment) Configuration

**Phase:** 4 - Forest Ecosystem Architecture  
**Week:** 20  
**Estimated Hours:** 8 hours  
**Priority:** MEDIUM  
**Dependencies:** Task 4-07 (Search Mycelium)

---

## 🎯 OBJECTIVE

Create Search Sapling - a lightweight discovery-only deployment for searching and discovering agents, workflows, and knowledge without full DRYAD ecosystem.

---

## 📋 REQUIREMENTS

### Functional Requirements
- Standalone search service
- Agent discovery
- Knowledge search
- Minimal dependencies

### Technical Requirements
- Docker Compose configuration
- Embedded search engine (Meilisearch)
- Read-only data access

### Performance Requirements
- Startup time: <30 seconds
- Memory footprint: <512MB
- Search latency: <500ms

---

## 🔧 IMPLEMENTATION

**File:** `deployments/search-sapling/docker-compose.yml`

```yaml
version: '3.8'

services:
  meilisearch:
    image: getmeili/meilisearch:latest
    environment:
      MEILI_ENV: development
    volumes:
      - meili_data:/meili_data
    ports:
      - "7700:7700"

  search-mycelium:
    build: ../../services/search-mycelium
    environment:
      SEARCH_ENGINE_URL: http://meilisearch:7700
    ports:
      - "8090:8000"
    depends_on:
      - meilisearch

volumes:
  meili_data:
```

---

## ✅ DEFINITION OF DONE

- [ ] Docker Compose configuration created
- [ ] Documentation complete
- [ ] Tested search functionality
- [ ] Resource usage verified

---

## 📊 SUCCESS METRICS

- Startup time: <30s
- Memory footprint: <512MB
- Search latency: <500ms

---

**Estimated Completion:** 8 hours  
**Status:** NOT STARTED

