# Incomplete Features & Implementation Gaps

This document tracks features that are partially implemented, rely on mocks, or have known gaps based on the code analysis.

## 1. Memory Guild (Librarian Agent)
**Status:** ⚠️ Partially Implemented / Mock-Heavy
**Location:** `app/services/memory_guild/librarian.py`
**Gaps:**
*   **Embeddings:** The `_generate_embedding` method currently uses a **mock implementation** (deterministic hash) instead of a real AI embedding model.
    *   *TODO:* Integrate with Oracle service or external provider for real embeddings.
*   **ChromaDB Dependency:** The service falls back to an in-memory dictionary mock if `chromadb` is not installed or fails to initialize.
*   **Search**: In mock mode, search is a simple text match rather than semantic similarity.

## 2. Agent Factory & Creation Studio
**Status:** ⚠️ Incomplete
**Location:** `app/services/agent_factory.py`
**Gaps:**
*   **Tool Creation:** The `_create_tools` method is a placeholder that currently returns an empty list (`[]`).
    *   *Effect:* Agents created via the factory cannot actually have tools assigned to them yet.
*   **Configuration Validation:** Validation of specific tool configurations against their schemas is marked as `TODO`.

## 3. Tool Registry Migration
**Status:** ⚠️ Deprecation Warning
**Location:** `app/services/tool_registry_service.py`
**Gaps:**
*   **Legacy Code:** The file `app/services/tool_registry_service.py` is deprecated and contains a warning to use the new service in `app/services/tool_registry/service.py`.
*   **Cleanup:** The codebase currently contains both the old and new implementations, requiring cleanup to avoid confusion.

## 4. Dryad Services (Knowledge Tree)
**Status:** 🚧 Under Construction
**Location:** `app/dryad/services/`
**Gaps:**
*   **Vessel Inheritance:** Logic for inheriting context from parent vessels is marked with TODOs in `vessel_inheritance.py`.
*   **Import/Export:** Services for importing/exporting Groves (`import_service.py`, `export_service.py`) contain TODO placeholders for complex data structures.

## 5. Security & Auth
**Status:** 🟡 Functional but needs hardening
**Location:** `app/core/security.py`
**Gaps:**
*   Specific granular permission checks for some advanced admin endpoints may still be in TODO state (based on grep analysis of `admin.py`).

## 6. MCP Server Integration
**Status:** 🚧 In Progress
**Location:** `app/mcp/server.py`
**Gaps:**
*   The integration with the 2025 Model Context Protocol standards has TODO markers for advanced resource subscription and tool dynamic updates.
