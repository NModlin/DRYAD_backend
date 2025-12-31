# System Overview

## System Identity
**DRYAD.AI Backend v9.0.0** is a sophisticated, self-contained, multi-modal AI system. It is designed to be a comprehensive platform for building and orchestrating AI agents that can reason, collaborate, and interact with the world through various interfaces.

The key philosophy of the system is **"Self-Contained AI"**, capable of running with local LLMs (like Llama 3) for privacy and offline capability, while offering "Hybrid" routing to cloud models (OpenAI, Anthropic) for complex tasks.

## Core Technology Stack
*   **Language:** Python 3.11+
*   **Web Framework:** FastAPI (Async, REST, GraphQL, WebSocket)
*   **Database:** 
    *   **Relational:** SQLite (primary data storage)
    *   **Vector:** Weaviate (semantic search & RAG)
    *   **ORM:** SQLAlchemy (AsyncIO)
    *   **Migrations:** Alembic
*   **AI/ML:**
    *   **Local Inference:** specialized local model support (llama-cpp-python)
    *   **Cloud Inference:** OpenAI-compatible API client
    *   **Orchestration:** LangGraph / Custom Multi-Agent System
*   **Asynchronous Processing:**
    *   **Task Queue:** Redis (optional/configurable)
    *   **Worker:** Custom worker scripts
*   **Environment:** Docker & Docker Compose support

## Key Capabilities

### 1. Hybrid LLM Processing
The system features an intelligent router that selects the optimal model for a given task.
*   **Cloud Routing:** Uses high-end models (e.g., GPT-4o, Claude 3.5 Sonnet) for reasoning-heavy, complex planning, or creative tasks.
*   **Local Routing:** Uses efficient local models for routine tasks, summarization, and sensitive data processing, ensuring privacy and reducing costs.

### 2. Multi-Agent System
DRYAD implements a swarm of specialized agents (20+ defined roles) that can work together.
*   **Roles:** Researcher, Analyst, Coder, Reviewer, etc.
*   **Collaboration:** Agents share a common "Memory Guild" context.
*   **Tools:** Agents have access to a secure "Tool Registry" to execute safe code, query databases, or search the web.

### 3. Model Context Protocol (MCP) Server
Fully implements the **Model Context Protocol (MCP)** (2025 Standard), allowing the backend to serve as a standardized AI context provider for compatible clients. This includes:
*   Resources (documents, chat history)
*   Prompts
*   Tools (for the client to invoke)

### 4. "The Dryad" Knowledge System
A unique, tree-structured knowledge management system.
*   **Groves:** Top-level project containers.
*   **Branches:** Divergent paths of exploration or conversation.
*   **Vessels:** Context containers that hold data, state, and inherited knowledge.
*   **Oracles:** AI entities that "live" on branches to guide exploration.

### 5. Secure Execution Sandbox
A robust, Docker-based sandbox environment (Level 1 Component) that allows agents to execute generated code (Python, Shell) safely.
*   Resource limits (CPU, Memory).
*   Network isolation.
*   Timeouts and self-healing mechanisms.

### 6. Multi-Modal Interactions
Support for processing various input types beyond text:
*   **Audio/Voice:** Transcription and synthesis.
*   **Visual:** Image analysis and OCR.
