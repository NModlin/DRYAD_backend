# Architecture & Directory Structure

## High-Level Architecture
DRYAD is built as a **Modular Monolith** with clear separation of concerns, designed to support a multi-agent system.

```mermaid
graph TD
    Client[Clients (Web/App/MCP)] --> API[FastAPI Gateway]
    API --> Services[Service Layer]
    Services --> DB[(SQLite / Weaviate)]
    
    subgraph "Core Agent System"
        Services --> Orch[Orchestrator]
        Orch --> Registry[Tool Registry]
        Orch --> Memory[Memory Guild]
        Orch --> Sandbox[Execution Sandbox]
    end
    
    subgraph "The Dryad"
        Services --> Grove[Grove Manager]
        Grove --> Branch[Branch Logic]
        Branch --> Vessel[Vessel Storage]
    end
```

## Directory Structure
The repository is organized into the following key areas. Note that some cleanup is recommended (see `DEEP_DIRECTORY_ANALYSIS.md`).

### Source Code (`app/`)
*   **`api/`**: API endpoints (v1 REST, GraphQL).
*   **`core/`**: Core configuration, security, and exception handling.
*   **`database/`**: SQLAlchemy models and database connection logic.
*   **`services/`**: Business logic layer.
    *   `tool_registry/`: The new, consolidated tool registry service.
    *   `sandbox_service.py`: Docker-based execution environment.
    *   `memory_guild/`: Long-term memory and librarian agents.
    *   `multimodal_service.py`: Audio/Video/Image processing.
    *   `agent_factory.py`: Logic for creating new agents.
*   **`dryad/`**: Specific logic for the "Dryad" knowledge tree system (Groves, Branches, Vessels).
*   **`mcp/`**: Model Context Protocol server implementation.

### Infrastructure
*   **`alembic/`**: Database migrations.
*   **`docker/`**: Dockerfiles and Compose configurations for various environments.
*   **`scripts/`**: Utility scripts for startup, testing, and maintenance.

### Documentation (`docs/` & `info/`)
*   **`docs/`**: Detailed legacy documentation.
*   **`info/`**: (This directory) High-level system summaries for the rebuild.

## Key Design Patterns
*   **Service Repository Pattern:** Business logic is encapsulated in Services, which interact with the Database (Repositories).
*   **Dependency Injection:** Services are injected into API endpoints.
*   **Agentic Pattern:** Agents are autonomous entities with access to a shared Tool Registry and Memory store.
*   **Hybrid AI:** Router pattern to switch between Local (Llama) and Cloud (accessible via API) models.
