# CrewAI Removal Plan

**Date:** 2025-10-13  
**Status:** IN PROGRESS  
**Priority:** CRITICAL

---

## Executive Summary

DRYAD.AI has moved away from CrewAI in favor of a superior built-in multi-agent architecture based on the Level 0-5 dependency-driven implementation. All references to CrewAI must be removed from:

1. Code files (Python, TypeScript, JavaScript)
2. Documentation (Markdown files)
3. Configuration files
4. Test files
5. Validation scripts

---

## Files Requiring CrewAI Removal

### 1. Core Code Files

**app/core/multi_agent.py**
- Remove: `CREWAI_AVAILABLE` flag
- Remove: `use_crewai` instance variable
- Remove: `_execute_crewai_simple_query()` method
- Remove: `_execute_crewai_complex_workflow()` method
- Remove: All CrewAI fallback logic
- Keep: Built-in agent implementation
- Update: Comments referencing CrewAI

**scripts/validate_complete_system.py**
- Remove: All CrewAI validation checks
- Remove: Priority 1 "Complete CrewAI Integration Implementation"
- Update: Validation to focus on Level-based architecture

### 2. Documentation Files

**README.md** (if exists)
- Remove: Any CrewAI mentions
- Update: Architecture description to Level-based

**docs/** (various)
- Search and remove all CrewAI references

### 3. Configuration Files

**requirements.txt / requirements-dev.txt**
- Remove: `crewai` package (if present)
- Remove: Any CrewAI dependencies

---

## Replacement Strategy

### What CrewAI Provided
- Multi-agent orchestration
- Task delegation
- Agent collaboration

### What DRYAD Provides (Superior)
- **Level 3: Hybrid Orchestration** - Intelligent task routing
- **Level 3: Task Force Management** - Multi-agent collaboration
- **Level 3: HITL System** - Human oversight
- **Level 1-2: Memory Guild** - Persistent agent memory
- **Level 4-5: Self-Improvement** - Autonomous optimization

---

## Action Items

- [ ] Remove CrewAI from app/core/multi_agent.py
- [ ] Remove CrewAI from scripts/validate_complete_system.py
- [ ] Search all .py files for "crew" references
- [ ] Search all .md files for "crew" references
- [ ] Update requirements.txt
- [ ] Update all documentation
- [ ] Run validation to ensure no breakage

---

## Completion Criteria

1. Zero mentions of "CrewAI", "crew", or "Crew" in codebase
2. All tests passing without CrewAI
3. Documentation updated to reflect Level-based architecture
4. Validation scripts updated

---

**Next Steps:** Execute removal systematically, starting with core files.

