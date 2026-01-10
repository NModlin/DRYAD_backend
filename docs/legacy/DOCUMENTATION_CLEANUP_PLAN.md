# Documentation Cleanup Plan

**Date:** 2025-10-13  
**Purpose:** Remove all outdated documentation, keep only what's needed to finish the project

---

## Files to KEEP

### New Unified Documentation (Created Today)
- ✅ `UNIFIED_MASTER_PLAN.md` - Single source of truth
- ✅ `PHASE_TO_LEVEL_MAPPING.md` - Task mapping
- ✅ `GAP_ANALYSIS_REPORT.md` - Current gaps
- ✅ `ACTION_PLAN_PRIORITY.md` - Prioritized actions
- ✅ `CREWAI_REMOVAL_PLAN.md` - CrewAI cleanup
- ✅ `CONSOLIDATION_COMPLETE_SUMMARY.md` - Summary

### Level Completion Reports (Still Valid)
- ✅ `LEVEL_2_COMPLETION_REPORT.md`
- ✅ `LEVEL_3_COMPLETION_REPORT.md`
- ✅ `LEVEL_4_COMPLETION_REPORT.md`
- ✅ `LEVEL_5_COMPLETION_REPORT.md`

### Essential Technical Guides
- ✅ `DATABASE_SCHEMA_GUIDE.md` - Database reference
- ✅ `HYBRID_LLM_GUIDE.md` - LLM configuration
- ✅ `API.md` - API documentation
- ✅ `DRYAD_BRAND_GUIDE.md` - Branding (if needed)

### Essential Directories
- ✅ `docs/api/` - API reference
- ✅ `docs/getting-started/` - Setup guides
- ✅ `docs/reference/` - Technical reference

---

## Files/Directories to REMOVE

### Old Planning Documents (Superseded by Unified Plan)
- ❌ `docs/FInalRoadmap/` - **ENTIRE DIRECTORY** (old planning, superseded)
  - Contains: MASTER_IMPLEMENTATION_PLAN.md (old version)
  - Contains: Multiple gap analysis docs (superseded)
  - Contains: Old task documentation (superseded)
  - Contains: Legacy plans subdirectory

### Frontend Handoff (Not Relevant to Backend Completion)
- ❌ `docs/FrontendDrop/` - **ENTIRE DIRECTORY**
  - Frontend requirements (not backend work)

### Duplicate/Old Deployment Guides
- ❌ `DEPLOYMENT.md` - Duplicate
- ❌ `DEPLOYMENT_GUIDE.md` - Duplicate
- ❌ `DEPLOYMENT_RUNBOOK.md` - Duplicate
- ❌ `PRODUCTION_DEPLOYMENT_GUIDE.md` - Duplicate
- ❌ `PRODUCTION_DOCKER_SETUP.md` - Duplicate
- ❌ `PHASE_4_PRODUCTION_DEPLOYMENT.md` - Old phase doc
- ❌ `docs/deployment/` - **ENTIRE DIRECTORY** (old deployment docs)

### Old Infrastructure Docs (Will be recreated)
- ❌ `CICD_PIPELINE.md` - Old version
- ❌ `MONITORING_ALERTING.md` - Old version
- ❌ `LOAD_BALANCING.md` - Old version
- ❌ `LOGGING_INFRASTRUCTURE.md` - Old version
- ❌ `DISASTER_RECOVERY.md` - Incomplete/old
- ❌ `ROLLBACK_RUNBOOK.md` - Old version
- ❌ `TROUBLESHOOTING_GUIDE.md` - Old version

### Old Security Docs (Will be consolidated)
- ❌ `OAUTH2_SETUP_GUIDE.md` - Old version
- ❌ `SECRETS_MANAGEMENT.md` - Duplicate
- ❌ `SECRETS_MANAGEMENT_STRATEGY.md` - Duplicate
- ❌ `SSL_TLS_CONFIGURATION.md` - Old version
- ❌ `SERVICE_DEPENDENCIES.md` - Old version

### Old Agent/Architecture Docs (Superseded by Level Architecture)
- ❌ `docs/agent-enhancements/` - **ENTIRE DIRECTORY** (old agent docs)
- ❌ `docs/agent-studio/` - **ENTIRE DIRECTORY** (old agent studio)
- ❌ `docs/system-agents/` - **ENTIRE DIRECTORY** (superseded by Levels)
- ❌ `docs/architecture/` - **ENTIRE DIRECTORY** (old architecture docs)

### Old DRYAD Concept Docs (Superseded)
- ❌ `docs/dryad/` - **ENTIRE DIRECTORY** (old concept docs)

### Old Integration Docs (Not Current Focus)
- ❌ `docs/integrations/` - **ENTIRE DIRECTORY** (radar, headhunter - not core)

### Old Templates (Not Needed)
- ❌ `docs/templates/` - **ENTIRE DIRECTORY** (frontend handoff templates)

### Old Developer Portal (Not Current Focus)
- ❌ `docs/developer-portal/` - **ENTIRE DIRECTORY** (old portal)

### Old Migration Docs
- ❌ `docs/migrations/` - **ENTIRE DIRECTORY** (old migration docs)
- ❌ `migrations.md` - Old migration doc

### Old Getting Started Docs (Keep directory, remove old files)
- ❌ `getting_started.md` - Old version (keep directory)

### Old Reference Docs
- ❌ `api_reference.md` - Old version
- ❌ `enhanced_error_handling.md` - Old version
- ❌ `multi_language_examples.md` - Old version

### Old README
- ❌ `README.md` - Old version (will create new one)

---

## Summary

**KEEP:** 10 files + 3 directories (api, getting-started, reference)
**REMOVE:** ~100+ files across 15+ directories

**Rationale:**
- New unified plan supersedes all old planning docs
- Level architecture supersedes old agent/architecture docs
- Infrastructure docs will be recreated based on action plan
- Integration/frontend docs not relevant to backend completion
- Duplicate deployment guides causing confusion

---

## Execution Plan

1. Create backup of entire docs/ directory (just in case)
2. Remove directories first (bulk cleanup)
3. Remove individual files
4. Verify essential files remain
5. Create new README.md pointing to unified plan

---

**After cleanup, docs/ will contain:**
```
docs/
├── UNIFIED_MASTER_PLAN.md              # Single source of truth
├── PHASE_TO_LEVEL_MAPPING.md           # Task mapping
├── GAP_ANALYSIS_REPORT.md              # Gap analysis
├── ACTION_PLAN_PRIORITY.md             # Action plan
├── CREWAI_REMOVAL_PLAN.md              # CrewAI cleanup
├── CONSOLIDATION_COMPLETE_SUMMARY.md   # Summary
├── LEVEL_2_COMPLETION_REPORT.md        # Level 2 status
├── LEVEL_3_COMPLETION_REPORT.md        # Level 3 status
├── LEVEL_4_COMPLETION_REPORT.md        # Level 4 status
├── LEVEL_5_COMPLETION_REPORT.md        # Level 5 status
├── DATABASE_SCHEMA_GUIDE.md            # Database reference
├── HYBRID_LLM_GUIDE.md                 # LLM configuration
├── API.md                              # API docs
├── DRYAD_BRAND_GUIDE.md                # Branding
├── api/                                # API reference
├── getting-started/                    # Setup guides
└── reference/                          # Technical reference
```

Clean, focused, and ready to finish the project.

