# DRYAD.AI Prioritized Action Plan

**Date:** 2025-10-13  
**Purpose:** Prioritized steps to close all gaps and reach production readiness  
**Timeline:** 2 weeks to production ready

---

## Phase 1: Critical Fixes (2-4 hours) - DO IMMEDIATELY

### Action 1.1: Remove All CrewAI References
**Priority:** CRITICAL  
**Estimated Time:** 1 hour  
**Owner:** Development Team

**Files to Modify:**
1. `app/core/multi_agent.py`
   - Remove `CREWAI_AVAILABLE` flag
   - Remove `use_crewai` instance variable
   - Remove `_execute_crewai_simple_query()` method
   - Remove `_execute_crewai_complex_workflow()` method
   - Update all comments referencing CrewAI
   - Keep only built-in implementation

2. `scripts/validate_complete_system.py`
   - Remove all CrewAI validation checks
   - Remove Priority 1 "Complete CrewAI Integration Implementation"
   - Update to validate Level-based architecture

3. Search all files for "crew", "Crew", "CREW" and remove

**Validation:**
```bash
# Should return zero results
grep -r "crew" --include="*.py" --include="*.md" .
```

---

### Action 1.2: Fix Level 0 Pytest Configuration
**Priority:** CRITICAL  
**Estimated Time:** 1 hour  
**Owner:** Development Team

**Root Cause:** Pytest cannot discover/execute Level 0 tests

**Steps:**
1. Check `pytest.ini` configuration
2. Verify test discovery patterns
3. Check `conftest.py` fixtures
4. Ensure database fixtures are properly scoped
5. Run tests individually to isolate issues

**Files to Check:**
- `pytest.ini`
- `tests/conftest.py`
- `tests/services/tool_registry/conftest.py`
- `tests/services/memory_guild/conftest.py`
- `tests/services/structured_logging/conftest.py`

**Validation:**
```bash
pytest tests/services/tool_registry/ -v
pytest tests/services/memory_guild/ -v
pytest tests/services/structured_logging/ -v
```

**Success Criteria:** All Level 0 tests execute and pass

---

### Action 1.3: Fix Level 1 Memory Retrieval Bug
**Priority:** CRITICAL  
**Estimated Time:** 1 hour  
**Owner:** Development Team

**Root Cause:** Key mismatch between storage and retrieval

**File:** `app/services/memory_guild/coordinator.py`

**Issue:** 
- Storage uses key: `mem_bdc2ad0c4939`
- Retrieval looks for different key format

**Fix:**
1. Review `_store_short_term()` method - how keys are generated
2. Review `_retrieve_short_term()` method - how keys are looked up
3. Ensure consistent key format
4. Add logging to track key generation/lookup

**Validation:**
```bash
python scripts/validate_level_1.py
# Should show Memory Coordinator: 4/4 tests passing
```

---

### Action 1.4: Fix Level 1 Content Ingestion Bug
**Priority:** CRITICAL  
**Estimated Time:** 30 minutes  
**Owner:** Development Team

**Root Cause:** Duplicate detection returning None incorrectly

**File:** `app/services/memory_guild/scribe.py`

**Issue:**
- Content ingestion returning `memory_id: None`
- Duplicate detection triggering on first ingestion

**Fix:**
1. Review duplicate detection logic
2. Check hash generation
3. Verify database lookup for existing content
4. Ensure new content is stored, not rejected

**Validation:**
```bash
python scripts/validate_level_1.py
# Should show Memory Scribe: 5/5 tests passing
```

---

## Phase 2: High Priority (1-2 days) - THIS WEEK

### Action 2.1: Fix Agent Registry Duplicate Error
**Priority:** HIGH  
**Estimated Time:** 30 minutes

**File:** `tests/services/agent_registry/`

**Issue:** Test not cleaning up previous runs

**Fix:**
1. Add test isolation
2. Use unique agent IDs per test run
3. Add cleanup in teardown

---

### Action 2.2: Complete Production Dockerfile
**Priority:** HIGH  
**Estimated Time:** 3 hours

**File:** `Dockerfile.production`

**Requirements:**
- Multi-stage build (builder + runtime)
- Security hardening (non-root user)
- Optimized layers (minimize image size)
- Health checks
- Environment variable configuration

**Template:**
```dockerfile
# Stage 1: Builder
FROM python:3.11-slim as builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Stage 2: Runtime
FROM python:3.11-slim
RUN useradd -m -u 1000 dryad
WORKDIR /app
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY . .
USER dryad
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD python -c "import requests; requests.get('http://localhost:8000/health')"
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

### Action 2.3: Create Nginx Configuration
**Priority:** HIGH  
**Estimated Time:** 2 hours

**File:** `nginx/nginx.conf`

**Requirements:**
- Reverse proxy to FastAPI (port 8000)
- SSL/TLS termination
- Rate limiting
- Static file serving
- WebSocket support
- Security headers

---

### Action 2.4: Create Operations Runbook
**Priority:** HIGH  
**Estimated Time:** 4 hours

**File:** `docs/operations/RUNBOOK.md`

**Sections:**
1. System Architecture Overview
2. Deployment Procedures
3. Monitoring and Alerting
4. Troubleshooting Guide
5. Backup and Recovery
6. Scaling Procedures
7. Security Incident Response
8. Common Issues and Solutions

---

## Phase 3: Medium Priority (1 week) - THIS MONTH

### Action 3.1: Complete Monitoring Stack
**Priority:** MEDIUM  
**Estimated Time:** 8 hours

**Files:**
- `monitoring/prometheus.yml`
- `monitoring/grafana/dashboards/dryad-overview.json`
- `monitoring/grafana/datasources/prometheus.yml`
- `docker-compose.monitoring.yml`

**Components:**
1. Prometheus for metrics collection
2. Grafana for visualization
3. Custom dashboards for DRYAD metrics
4. Alerting rules

---

### Action 3.2: Create CI/CD Pipeline
**Priority:** MEDIUM  
**Estimated Time:** 6 hours

**File:** `.github/workflows/ci-cd.yml`

**Stages:**
1. Lint and type checking
2. Unit tests
3. Integration tests
4. Security scanning
5. Docker build
6. Deploy to staging
7. Deploy to production (manual approval)

---

### Action 3.3: Complete API Documentation
**Priority:** MEDIUM  
**Estimated Time:** 8 hours

**Location:** `docs/api/`

**Files:**
- `authentication.md` - Auth guide
- `endpoints.md` - All endpoints documented
- `examples.md` - Code examples
- `errors.md` - Error handling
- `rate-limiting.md` - Rate limit guide
- `versioning.md` - API versioning

---

### Action 3.4: Add Test Coverage Reporting
**Priority:** MEDIUM  
**Estimated Time:** 2 hours

**Files:**
- `pytest.ini` - Add coverage configuration
- `.coveragerc` - Coverage settings
- `.github/workflows/ci-cd.yml` - Add coverage reporting

**Configuration:**
```ini
[tool:pytest]
addopts = --cov=app --cov-report=html --cov-report=term-missing --cov-fail-under=90
```

---

### Action 3.5: Create Developer Onboarding Guide
**Priority:** MEDIUM  
**Estimated Time:** 4 hours

**File:** `docs/getting-started/DEVELOPER_GUIDE.md`

**Sections:**
1. Prerequisites
2. Local Development Setup
3. Architecture Overview
4. Code Structure
5. Testing Strategy
6. Contribution Guidelines
7. Common Development Tasks

---

## Phase 4: Low Priority (2 weeks) - FUTURE

### Action 4.1: Create Architecture Decision Records
**Priority:** LOW  
**Estimated Time:** 8 hours

**Location:** `docs/architecture/decisions/`

**ADRs to Create:**
- 001-level-based-architecture.md
- 002-memory-guild-design.md
- 003-hybrid-orchestration.md
- 004-self-improvement-engine.md
- 005-no-crewai-decision.md

---

### Action 4.2: Complete Test Documentation
**Priority:** LOW  
**Estimated Time:** 4 hours

**File:** `docs/testing/TESTING_GUIDE.md`

---

### Action 4.3: Update Disaster Recovery Plan
**Priority:** LOW  
**Estimated Time:** 3 hours

**File:** `docs/DISASTER_RECOVERY.md`

---

## Timeline Summary

### Week 1
- **Day 1:** Phase 1 (Critical Fixes) - 2-4 hours
- **Day 2-3:** Phase 2 Actions 2.1-2.2 (Dockerfile, Agent Registry)
- **Day 4-5:** Phase 2 Actions 2.3-2.4 (Nginx, Runbook)

### Week 2
- **Day 1-2:** Phase 3 Action 3.1 (Monitoring Stack)
- **Day 3:** Phase 3 Action 3.2 (CI/CD Pipeline)
- **Day 4-5:** Phase 3 Actions 3.3-3.5 (Docs, Coverage, Onboarding)

### Weeks 3-4 (Optional)
- Phase 4 (Low Priority Items)

---

## Success Metrics

### End of Week 1
- [ ] All Level validation scripts pass 100%
- [ ] Zero CrewAI references
- [ ] Production Dockerfile complete
- [ ] Nginx configuration deployed
- [ ] Operations runbook complete

### End of Week 2
- [ ] Monitoring stack operational
- [ ] CI/CD pipeline functional
- [ ] API documentation complete
- [ ] Test coverage >90%
- [ ] Developer guide complete

### Production Ready Checklist
- [ ] All validation scripts pass
- [ ] All tests pass
- [ ] Test coverage >90%
- [ ] Security scan clean
- [ ] Performance benchmarks met
- [ ] Documentation complete
- [ ] Monitoring operational
- [ ] Runbook complete
- [ ] Disaster recovery plan complete

---

## Daily Standup Template

**What was completed yesterday:**
- List completed actions

**What will be completed today:**
- List planned actions

**Blockers:**
- List any blockers

**Metrics:**
- Level 0 validation: X%
- Level 1 validation: X%
- Overall test coverage: X%
- Documentation coverage: X%

---

**Start with Phase 1 immediately. All critical fixes should be complete within 4 hours.**

