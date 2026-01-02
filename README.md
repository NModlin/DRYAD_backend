# DRYAD.AI Backend v9.0.0

A sophisticated, self-contained, multi-modal AI system built with FastAPI and Weaviate, featuring **hybrid cloud/local LLM processing** with intelligent routing, built-in multi-agent capabilities, semantic search, and RAG (Retrieval-Augmented Generation) that can reason across text, collaborate on complex tasks, and maintain conversation context through persistent chat history and document knowledge.

**Current Version:** 9.0.0 | **Status:** ✅ Production Ready | **Architecture:** Self-Contained AI + Multi-Client | **API Endpoints:** 100+ (conditional on service availability) + MCP Protocol

## 📚 Documentation

**Complete documentation is now organized in the [docs/](docs/) directory:**

- **[Documentation Index](docs/README.md)** - Complete documentation navigation
- **[Quick Start](QUICK_START.md)** - Get running in 5 minutes
- **[Agent Studio](docs/agent-studio/)** - Create custom AI agents
- **[Agent Enhancements](docs/agent-enhancements/)** - 43 API endpoints for agent capabilities
- **[System Agents](docs/system-agents/)** - Built-in 20-agent swarm system
- **[DRYAD](docs/dryad/)** - Knowledge tree & quantum branching
- **[Deployment](docs/deployment/)** - Production deployment guides
- **[Getting Started](docs/getting-started/)** - Setup and configuration
- **[Architecture](docs/architecture/)** - System design and architecture
- **[Integrations](docs/integrations/)** - External system integrations
- **[API Reference](docs/api_reference.md)** - Complete API documentation
- **[Hybrid LLM Guide](docs/HYBRID_LLM_GUIDE.md)** - Cloud/local LLM configuration and usage

**Recent Updates:**
- 🚀 **Hybrid LLM System** - Intelligent cloud/local routing with Ollama Cloud integration
- 🧹 **Repository Cleanup** - Removed test files, updated documentation with hybrid LLM information
- ✅ **Phase 5 Complete** - AutoGen-inspired enhancements (12 new endpoints)
- ✅ **Documentation Reorganized** - 168 files organized into logical structure
- ✅ **Archive Created** - 91 historical files preserved in archive/
- 📖 **[Documentation Audit Summary](DOCUMENTATION_AUDIT_SUMMARY.md)** - Complete reorganization report

## 🎯 Hybrid LLM System (**NEWLY IMPLEMENTED**)
- ✅ **Intelligent Cloud/Local Routing**: Automatically selects optimal models based on task complexity and agent type
- ✅ **Ollama Cloud Integration**: Access to powerful cloud models (gpt-oss:120b, deepseek-v3.1:671b, qwen3-coder:480b)
- ✅ **Graceful Fallback**: Seamless fallback from cloud to local models when needed
- ✅ **Agent-Specific Optimization**: Each agent type routes to optimal models for their tasks
- ✅ **Cost Optimization**: Use expensive cloud models only for complex tasks
- ✅ **Privacy Modes**: Force local-only mode for sensitive operations
- ✅ **Offline Capable**: Full functionality with local models when cloud unavailable
- ✅ **Multiple Local Models**: TinyLlama (669MB), Llama3.2 (3B), CodeLlama (7B)
- ✅ **Hybrid Database**: SQLite + Weaviate for optimal AI performance

## 🚀 Features

### 🏢 Multi-Client Architecture
- **Client Application Support**: Multiple client apps connect via standardized APIs
- **Tenant Isolation**: Strict data separation between clients and tenants
- **Cross-Client Learning**: Privacy-preserving knowledge sharing across clients
- **Model Context Protocol (MCP)**: Standardized interface for client integration
- **API Key Authentication**: Secure client application authentication
- **Federated Learning**: Aggregate insights while preserving privacy

### 🔌 **Model Context Protocol (MCP) Server** (**FULLY IMPLEMENTED**)
- **Complete MCP Implementation**: Full MCP 2025-06-18 protocol support
- **Real AI Integration**: Actual LLM responses, not mock data
- **Resource Access**: Documents, conversations, shared knowledge, analytics
- **Advanced Tools**: Semantic search, data extraction, pattern analysis
- **Standardized Interface**: Compatible with all MCP clients
- **Production Ready**: Comprehensive error handling and logging

### 🔧 AI-Powered Tools (**REAL FUNCTIONALITY**)
- **Semantic Search**: Vector-based document search with tenant isolation
- **AI Chat**: Context-aware conversations with conversation history
- **Data Extraction**: LLM-powered structured data extraction for any schema
- **Pattern Analysis**: AI-powered pattern detection with domain context
- **Content Classification**: Configurable taxonomies and risk assessment
- **Similarity Calculation**: Multi-factor similarity with custom weighting
- **Geographic Processing**: Location extraction and geocoding capabilities
- **Domain Contexts**: Pre-configured for GovCon, Legal, E-commerce, Research

### Core Agent Engine
- **LangGraph-based Agent**: Advanced agent workflow with tool integration
- **DuckDuckGo Search**: Web search capabilities for real-time information
- **FastAPI Framework**: Modern, fast API with automatic documentation
- **Tool Integration**: Extensible architecture for adding new tools

### Robust API Layer
- **Chat History**: Persistent conversation storage with SQLite database
- **Context Awareness**: Multi-turn conversations with memory
- **CRUD Operations**: Complete conversation and message management
- **Database Migrations**: Alembic-powered schema management

### Advanced Multi-Agent Architecture
- **Built-in Multi-Agent System**: Sophisticated multi-agent orchestration with no external dependencies
- **Specialized Agent Roles**: Researcher, Analyst, Writer, Coordinator
- **Complex Workflows**: Multi-step reasoning and task coordination
- **Agent Memory System**: Persistent context sharing between agents
- **Enhanced API Endpoints**: Multi-agent workflow capabilities
- **Performance Optimized**: Faster execution than external frameworks

### Data Infrastructure
- **Weaviate Vector Store**: High-performance semantic search capabilities with fallback support
- **Document Management**: Intelligent chunking and storage system
- **RAG System**: Retrieval-Augmented Generation for enhanced responses
- **Semantic Search**: Vector similarity search with metadata filtering
- **Document APIs**: Complete CRUD operations for knowledge management
- **Analytics & Monitoring**: Search analytics and system health monitoring

### Agent Orchestration & Scalability
- **Enhanced Orchestrator**: Central coordination system for all components
- **Asynchronous Task Execution**: Celery-based distributed task processing
- **Advanced Task Management**: 9 task types with priority and timeout handling
- **Scalable Architecture**: Horizontal scaling with multiple worker processes
- **Production Infrastructure**: Worker scripts, monitoring, and deployment tools
- **Comprehensive APIs**: Complete orchestration and task management endpoints

### API Modernization & Real-time Communication
- **GraphQL Integration**: Complete GraphQL API with queries, mutations, and subscriptions
- **Real-time Communication**: WebSocket infrastructure for live updates
- **Modern API Architecture**: Dual REST/GraphQL support with enhanced capabilities
- **Live Broadcasting**: Real-time message, task, and system event broadcasting
- **Enhanced Developer Experience**: GraphQL playground and comprehensive tooling
- **Backward Compatibility**: All existing APIs preserved and enhanced

### Multi-Modal Processing
- **Audio Processing**: Speech-to-text transcription, audio analysis, and text-to-speech conversion
- **Video Processing**: Frame extraction, video analysis, and audio transcription from video
- **Image Processing**: Computer vision analysis, object detection, and OCR capabilities
- **Multi-Modal Fusion**: Unified processing pipeline for combining multiple media types
- **Intelligent Storage**: Efficient content management with deduplication and metadata
- **Graceful Fallbacks**: System operates with partial capabilities when dependencies unavailable

### 🌳 Dryad Knowledge Tree System (**INTEGRATED**)
- **Quantum-Inspired Branching**: Non-linear knowledge exploration with parallel investigation paths
- **Grove Management**: Project workspaces for organizing knowledge trees
- **Branch Navigation**: Tree-based exploration with parent-child relationships and status tracking
- **Vessel Context System**: Isolated context containers with inheritance from parent branches
- **Oracle Integration**: AI consultation system with multiple LLM provider support
- **Observation Points**: Decision points where exploration paths can diverge
- **32 REST API Endpoints**: Complete CRUD operations for groves, branches, vessels, and dialogues
- **Database Integration**: 7 dedicated tables with proper foreign keys and cascade rules
- **Status Management**: Track branch states (ACTIVE, ARCHIVED, PRUNED) and priorities
- **Dialogue History**: Persistent conversation records with AI oracles per branch

### Developer Enablement & Documentation
- **Comprehensive Documentation**: Interactive API docs with live testing capabilities
- **Developer SDKs**: Full-featured Python SDK with async support and type safety
- **CLI Tools**: Rich command-line interface with interactive features and rich output
- **Interactive Documentation**: Live API testing, GraphQL playground, and WebSocket tester
- **Developer Portal**: Real-time monitoring dashboard with system metrics
- **Code Examples**: Extensive tutorials and best practices in multiple languages

## 📋 Requirements

### Minimum Requirements (Basic Mode)
- Python 3.11+
- SQLite (included with Python)
- Internet connection (for DuckDuckGo search)

### Full Feature Requirements (Optional)
- **LLM Provider**: OpenAI API key OR Ollama server (http://localhost:11434)
- **Vector Database**: Weaviate server (http://localhost:8081) for semantic search
- **Task Queue**: Redis server (redis://localhost:6379) for background processing
- **Multi-Modal**: Additional Python packages for audio/video/image processing

### **HONEST DEPENDENCY MATRIX**
| Feature | Status | Requirements | Fallback Behavior |
|---------|--------|--------------|-------------------|
| **REST/GraphQL APIs** | ✅ Ready | None | N/A - Core functionality |
| **Authentication** | ✅ Ready | None | N/A - Core functionality |
| **Database Operations** | ✅ Ready | SQLite (included) | N/A - Core functionality |
| **Basic AI Chat** | 🔧 Needs Setup | Local LLM or API keys | ❌ Error messages only |
| **Multi-Agent Workflows** | ✅ Ready | Local LLM setup | Built-in implementation |
| **Document Search/RAG** | ⚠️ Optional | Weaviate server | ⚠️ Basic database search |
| **Task Orchestration** | ⚠️ Optional | Redis server | ⚠️ Synchronous processing |
| **Multi-Modal Processing** | ⚠️ Optional | Additional packages | ❌ Feature unavailable |

**Legend**: ✅ = Works immediately | 🔧 = Needs configuration | ⚠️ = Optional enhancement | ❌ = Requires significant setup

## 🛠️ Installation

### **🌟 ENHANCED INTERACTIVE INSTALLER (NEW!)**

DRYAD.AI now features a **comprehensive, menu-driven installation system** with full component selection:

```bash
# Interactive installation with full customization
./install_dryad_enhanced.sh
```

**Features:**
- 🎯 7 deployment configurations (minimal to GPU-accelerated)
- 🎨 3 optional frontend applications
- 🔧 6 optional backend/monitoring components
- 🤖 4 LLM provider options (Mock, OpenAI, Anthropic, Ollama)
- 📊 Automatic resource checking and port conflict detection
- 🏥 Comprehensive health checks and status reporting

**For Remote Servers (SSH):**
```bash
# One-line remote installation
curl -fsSL https://raw.githubusercontent.com/NModlin/DRYAD_backend/main/quick_install.sh | bash

# Or manual clone
git clone https://github.com/NModlin/DRYAD_backend.git
cd DRYAD_backend
./install_dryad_enhanced.sh
```

📖 **See [INSTALL_ON_REMOTE_SERVER.md](INSTALL_ON_REMOTE_SERVER.md) for complete remote installation guide**

---

### **🚀 UNIFIED INSTALLATION (Alternative)**

For a simpler, non-interactive installation that automatically detects and utilizes your system's capabilities:

```bash
# Clone and setup
git clone <repository-url>
cd DRYAD_backend
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Single installation command - includes ALL features
pip install -r requirements.txt

# Start server (auto-detects optimal configuration)
python start.py
```

**✨ What you get automatically:**
- **🔥 GPU Acceleration**: Automatic CUDA detection and utilization for LLM inference
- **🤖 Local AI**: LlamaCpp with optimized performance (CPU fallback if no GPU)
- **🧠 Multi-Agent System**: Built-in multi-agent workflows (no external dependencies)
- **📊 Vector Search**: Weaviate integration for semantic search
- **🎵 Multimodal Processing**: Audio, video, and image processing with GPU acceleration
- **⚡ Task Orchestration**: Celery + Redis for background processing
- **🌐 Modern APIs**: REST, GraphQL, and WebSocket support
- **🔐 Authentication**: OAuth2 + JWT with Google SSO

### **🎛️ Environment Configuration**

The system automatically detects your hardware capabilities. Optional overrides:

```bash
# Force CPU-only mode (useful for testing or troubleshooting)
export FORCE_CPU=true

# Specify LLM model (optional - auto-selects optimal model)
export LLAMACPP_MODEL="tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf"

# Configure external services (optional - graceful fallbacks available)
export WEAVIATE_URL="http://localhost:8081"
export REDIS_URL="redis://localhost:6379"
```

### **🧪 Development Installation**

For development, testing, and code quality tools:

```bash
# Install production dependencies + development tools
pip install -r requirements.txt -r requirements-dev.txt
```

### **⚠️ IMPORTANT NOTES**
- **Profile 1** works immediately with no external dependencies
- **Profile 2** requires local LLM model to be properly loaded (not guaranteed)
- **Profile 3** requires external services (Weaviate, Redis) to be running
- **Profile 4** requires significant system resources for multi-modal processing
- **Always test each profile before proceeding to the next**

## 🎯 Development Status

**🔧 DEVELOPMENT/BETA** - API Platform with AI Integration Capabilities

The DRYAD.AI system provides a robust API platform with AI integration capabilities. **Current implementation status:**

### **✅ FULLY FUNCTIONAL (Out-of-the-Box)**
- **REST & GraphQL APIs**: Complete API framework with 71+ endpoints
- **Authentication System**: Production-ready OAuth2 with JWT tokens
- **Database Operations**: SQLite with Alembic migrations and chat history
- **WebSocket Support**: Real-time communication infrastructure
- **Developer Tools**: Interactive documentation, CLI tools, and SDKs
- **Health Monitoring**: Comprehensive system monitoring and metrics

### **⚠️ REQUIRES SETUP (External Dependencies)**
- **Multi-Agent Workflows**: Built-in system requires only local LLM configuration
- **Document Search & RAG**: Requires Weaviate vector database setup
- **Advanced Task Processing**: Requires Redis for distributed task queue
- **Multi-Modal Processing**: Requires additional Python packages for audio/video/image

### **🔧 IN DEVELOPMENT (Limited Functionality)**
- **Local LLM Integration**: TinyLlama model included but inference needs verification
- **Self-Contained AI**: Basic framework exists but depends on proper model loading

### **❌ KNOWN ISSUES**
- Local LLM model loading needs verification
- Some advanced features fall back to mock responses when dependencies unavailable
- Multi-agent system uses built-in implementation (no external dependencies required)

**Legend**: ✅ = Production Ready | ⚠️ = Requires External Setup | 🔧 = Needs Work | ❌ = Known Issues

## 🚀 Quick Start

**📖 For complete setup instructions, see [DRYAD.AI_COMPLETE_GUIDE.md](DRYAD.AI_COMPLETE_GUIDE.md)**

### **Recommended: Optimized Self-Contained AI Setup**
```bash
# Clone the repository
git clone <repository-url>
cd DRYAD_backend

# Install optimized dependencies for local AI
pip install -r requirements-minimal.txt

# Start with optimized local AI (no external services needed)
python start.py basic
```

### **Alternative: Quick Start**
```bash
# Using the provided script
./start.sh

# Or directly with uvicorn
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

### **Verify Optimized Setup**
```bash
# Test the optimized llama-cpp-python implementation
python verify_optimized_setup.py

# Test the complete MCP server functionality
python verify_mcp_fixed.py
```

### Access API Documentation
- **Interactive Docs**: http://127.0.0.1:8000/docs
- **ReDoc**: http://127.0.0.1:8000/redoc
- **GraphQL Playground**: http://127.0.0.1:8000/graphql
- **Complete Guide**: [DRYAD.AI_COMPLETE_GUIDE.md](DRYAD.AI_COMPLETE_GUIDE.md)
- **Tech Stack Reference**: [TECH_STACK.json](TECH_STACK.json)

## 📚 Documentation

### Core Documentation
- **[Installation & Setup](README.md#-installation)** - Unified installation guide
- **[Deployment Guide](DEPLOYMENT.md)** - Docker and production deployment
- **[Testing Guide](TESTING.md)** - Comprehensive testing instructions
- **[GPU Acceleration](GPU_ACCELERATION.md)** - Hardware optimization guide
- **[Dependency Guide](DEPENDENCY_GUIDE.md)** - Package management and dependencies

### Development & CI/CD
- **[CI/CD Pipeline](CI_CD_DOCUMENTATION.md)** - GitHub Actions workflows and testing
- **[Docker Configuration](docker/README.md)** - Container deployment options
- **[Security Deployment](SECURITY_DEPLOYMENT_CHECKLIST.md)** - Production security guide
- **[Troubleshooting](TROUBLESHOOTING.md)** - Common issues and solutions

### Project Status
- **[Repository Cleanup](REPOSITORY_CLEANUP_SUMMARY.md)** - Organization improvements
- **[Installation Consolidation](INSTALLATION_CONSOLIDATION_SUMMARY.md)** - Unified approach
- **[CI/CD Setup Complete](CI_CD_PIPELINE_SETUP_COMPLETE.md)** - Pipeline implementation

## 📚 API Usage

### Simple Agent Query
```bash
curl -X POST "http://127.0.0.1:8000/api/v1/agent/invoke" \
  -H "Content-Type: application/json" \
  -d '{"input": "What is artificial intelligence?"}'
```

### Context-Aware Chat
```bash
# Start a conversation
curl -X POST "http://127.0.0.1:8000/api/v1/agent/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "input": "What is machine learning?",
    "save_conversation": true
  }'

# Continue the conversation with context
curl -X POST "http://127.0.0.1:8000/api/v1/agent/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "input": "Can you explain that in simpler terms?",
    "conversation_id": "your-conversation-id",
    "save_conversation": true
  }'
```

### Modern API & Real-time Communication
```bash
# GraphQL API - Flexible queries
curl -X POST "http://127.0.0.1:8000/graphql" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "query { conversations(limit: 5) { id title messages { role content } } }"
  }'

# GraphQL Mutations with real-time updates
curl -X POST "http://127.0.0.1:8000/graphql" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "mutation { create_conversation(input: {title: \"New Chat\"}) { id title } }"
  }'

# WebSocket connection for real-time updates
# Connect to: ws://127.0.0.1:8000/api/v1/realtime-ws/ws
# Send: {"type": "subscribe", "subscription_type": "conversation", "conversation_id": "123"}

# Real-time API information
curl -X GET "http://127.0.0.1:8000/api/v1/realtime/info"

# System status with real-time metrics
curl -X GET "http://127.0.0.1:8000/api/v1/realtime/system/status"
```

### Developer Tools & Documentation
```bash
# Interactive documentation and developer portal
# Visit: http://127.0.0.1:8000/docs (Developer Portal)
# Visit: http://127.0.0.1:8000/graphql (GraphQL Playground)

# Python SDK usage
pip install gremlins-ai  # (when published)
python -c "
import asyncio
from gremlins_ai import DRYAD.AIClient

async def main():
    async with DRYAD.AIClient() as client:
        response = await client.invoke_agent('Hello, AI!')
        print(response['output'])

asyncio.run(main())
"

# CLI tool usage
python cli/gremlins_cli.py agent chat "What is machine learning?"
python cli/gremlins_cli.py interactive  # Interactive chat mode
python cli/gremlins_cli.py system health  # System status

# Developer portal endpoints
curl -X GET "http://127.0.0.1:8000/developer-portal/"  # Dashboard
curl -X GET "http://127.0.0.1:8000/developer-portal/metrics"  # Metrics
curl -X GET "http://127.0.0.1:8000/docs/system-status"  # System status
```

### Multi-Modal Processing
```bash
# Multi-modal processing endpoints
# Visit: http://127.0.0.1:8000/api/v1/multimodal/capabilities (Check capabilities)

# Process audio file
curl -X POST "http://127.0.0.1:8000/api/v1/multimodal/process/audio" \
  -F "file=@audio.wav" \
  -F "transcribe=true" \
  -F "analyze=true"

# Process video file
curl -X POST "http://127.0.0.1:8000/api/v1/multimodal/process/video" \
  -F "file=@video.mp4" \
  -F "extract_frames=true" \
  -F "transcribe_audio=true" \
  -F "frame_count=15"

# Process image file
curl -X POST "http://127.0.0.1:8000/api/v1/multimodal/process/image" \
  -F "file=@image.jpg" \
  -F "detect_objects=true" \
  -F "extract_text=true" \
  -F "analyze=true"

# Multi-modal batch processing
curl -X POST "http://127.0.0.1:8000/api/v1/multimodal/process/multimodal" \
  -F "files=@audio.wav" \
  -F "files=@video.mp4" \
  -F "files=@image.jpg" \
  -F "fusion_strategy=concatenate"

# Text-to-speech conversion
curl -X POST "http://127.0.0.1:8000/api/v1/multimodal/text-to-speech" \
  -F "text=Hello, this is a test of text-to-speech conversion" \
  -F "output_format=wav"
```

### Advanced Orchestration
```bash
# Execute task through orchestrator
curl -X POST "http://127.0.0.1:8000/api/v1/orchestrator/execute" \
  -H "Content-Type: application/json" \
  -d '{
    "task_type": "rag_query",
    "payload": {
      "query": "What are the latest AI developments?",
      "search_limit": 5,
      "use_multi_agent": true
    },
    "execution_mode": "async",
    "priority": 1
  }'

# Enhanced agent chat with orchestration
curl -X POST "http://127.0.0.1:8000/api/v1/orchestrator/agent/enhanced-chat" \
  -d "input=Analyze renewable energy trends" \
  -d "use_multi_agent=true" \
  -d "use_rag=true" \
  -d "async_mode=true"

# Check task status
curl -X GET "http://127.0.0.1:8000/api/v1/orchestrator/task/{task_id}"

# System health check
curl -X POST "http://127.0.0.1:8000/api/v1/orchestrator/health-check?async_mode=false"
```

### Document Management & RAG
```bash
# Create a document with automatic chunking
curl -X POST "http://127.0.0.1:8000/api/v1/documents/" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "AI Research Paper",
    "content": "Artificial intelligence research shows...",
    "tags": ["ai", "research"],
    "chunk_size": 1000
  }'

# Semantic search across documents
curl -X POST "http://127.0.0.1:8000/api/v1/documents/search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "machine learning algorithms",
    "limit": 5,
    "search_type": "chunks"
  }'

# RAG query with document context
curl -X POST "http://127.0.0.1:8000/api/v1/documents/rag" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Explain neural networks based on available documents",
    "use_multi_agent": true,
    "search_limit": 3
  }'
```

### Multi-Agent Workflows
```bash
# Execute multi-agent workflow
curl -X POST "http://127.0.0.1:8000/api/v1/multi-agent/workflow" \
  -H "Content-Type: application/json" \
  -d '{
    "input": "Analyze the impact of renewable energy on the economy",
    "workflow_type": "research_analyze_write",
    "save_conversation": true
  }'

# Get agent capabilities
curl "http://127.0.0.1:8000/api/v1/multi-agent/capabilities"

# Enhanced chat with multi-agent support
curl -X POST "http://127.0.0.1:8000/api/v1/agent/chat?use_multi_agent=true" \
  -H "Content-Type: application/json" \
  -d '{
    "input": "Explain quantum computing in simple terms",
    "save_conversation": true
  }'
```

### Chat History Management
```bash
# List conversations
curl "http://127.0.0.1:8000/api/v1/history/conversations"

# Get conversation details
curl "http://127.0.0.1:8000/api/v1/history/conversations/{conversation_id}"

# Get conversation messages
curl "http://127.0.0.1:8000/api/v1/history/conversations/{conversation_id}/messages"

# Get conversation summary with agent interactions
curl "http://127.0.0.1:8000/api/v1/multi-agent/conversations/{conversation_id}/summary"
```

## 🏗️ Architecture

```
DRYAD_backend/
├── app/
│   ├── api/v1/
│   │   ├── endpoints/          # API route handlers
│   │   └── schemas/            # Pydantic models
│   ├── core/
│   │   ├── agent.py           # LangGraph agent implementation
│   │   └── tools.py           # Agent tools (search, etc.)
│   ├── database/
│   │   ├── database.py        # Database configuration
│   │   └── models.py          # SQLAlchemy models
│   ├── services/
│   │   └── chat_history.py    # Business logic layer
│   └── main.py                # FastAPI application
├── alembic/                   # Database migrations
├── data/                      # SQLite database storage
└── requirements.txt           # Python dependencies
```

## 🔧 Configuration

### Environment Variables (.env)
```bash
# Core Application Settings
LOG_LEVEL="INFO"
DATABASE_URL="sqlite:///./data/DRYAD.AI.db"

# External Service Configurations
OLLAMA_BASE_URL="http://localhost:11434"
QDRANT_HOST="localhost"
QDRANT_PORT="6333"
REDIS_URL="redis://localhost:6379"
```

## 🗄️ Database Management

### Run Migrations
```bash
# Upgrade to latest schema
alembic upgrade head

# Create new migration
alembic revision --autogenerate -m "Description"

# Check current version
alembic current
```

## 🔌 API Endpoints

### Agent Endpoints
- `POST /api/v1/agent/invoke` - Simple agent invocation
- `POST /api/v1/agent/chat` - Context-aware chat with history

### Chat History Endpoints
- `POST /api/v1/history/conversations` - Create conversation
- `GET /api/v1/history/conversations` - List conversations
- `GET /api/v1/history/conversations/{id}` - Get conversation
- `PUT /api/v1/history/conversations/{id}` - Update conversation
- `DELETE /api/v1/history/conversations/{id}` - Delete conversation
- `POST /api/v1/history/messages` - Add message
- `GET /api/v1/history/conversations/{id}/messages` - Get messages
- `GET /api/v1/history/conversations/{id}/context` - Get AI context

### Dryad Knowledge Tree Endpoints
- `POST /api/v1/dryad/groves` - Create grove (knowledge tree workspace)
- `GET /api/v1/dryad/groves` - List all groves
- `GET /api/v1/dryad/groves/{id}` - Get grove details
- `PUT /api/v1/dryad/groves/{id}` - Update grove
- `DELETE /api/v1/dryad/groves/{id}` - Delete grove (cascades to branches)
- `POST /api/v1/dryad/branches` - Create branch
- `GET /api/v1/dryad/branches/{id}` - Get branch details
- `GET /api/v1/dryad/branches/{id}/tree` - Get branch tree structure
- `PUT /api/v1/dryad/branches/{id}` - Update branch
- `DELETE /api/v1/dryad/branches/{id}` - Delete branch (cascades to vessel)
- `POST /api/v1/dryad/vessels` - Create vessel (context container)
- `GET /api/v1/dryad/vessels/{id}` - Get vessel content
- `PUT /api/v1/dryad/vessels/{id}` - Update vessel content
- `POST /api/v1/dryad/oracle/consult` - Consult AI oracle
- `GET /api/v1/dryad/dialogues/{id}` - Get dialogue history
- **See `DRYAD_API_EXAMPLES.md` for complete API documentation**

## 🧪 Development

### Code Quality
- Follow PEP 8 style guidelines
- Use type hints throughout the codebase
- Maintain comprehensive docstrings

### Adding New Tools
1. Implement tool function in `app/core/tools.py`
2. Add tool to the agent's tool list in `app/core/agent.py`
3. Update API documentation

### Database Changes
1. Modify models in `app/database/models.py`
2. Generate migration: `alembic revision --autogenerate -m "Description"`
3. Apply migration: `alembic upgrade head`

## 🔧 Troubleshooting

### **Common Issues and Solutions**

#### **❌ Multi-Agent System Not Working**
```bash
# Solution: Multi-agent system is built-in, ensure LLM is configured
# Check LLM configuration
python -c "from app.core.llm_config import get_llm_provider; print('LLM configured:', get_llm_provider())"

# Verify multi-agent system
python -c "from app.core.multi_agent import CREWAI_AVAILABLE; print('Built-in multi-agent available:', not CREWAI_AVAILABLE)"
```

#### **❌ AI Responses Show Error Messages Instead of AI Content**
```bash
# Issue: LLM not properly configured
# Check current LLM status
curl http://localhost:8000/api/v1/health/status

# Solutions:
# 1. For local LLM:
export LLM_PROVIDER="llamacpp"
ls -la models/  # Verify model file exists

# 2. For external LLM:
export LLM_PROVIDER="openai"
export OPENAI_API_KEY="your-actual-api-key"
```

#### **❌ Multi-Agent Endpoints Return Errors**
```bash
# Issue: LLM not properly configured for built-in multi-agent system
# Solution: Configure local LLM (recommended: LlamaCpp)
export LLM_PROVIDER="llamacpp"
export LLAMACPP_MODEL="tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf"

# Alternative: Use Ollama
export LLM_PROVIDER="ollama"
export OLLAMA_BASE_URL="http://localhost:11434"
```

#### **❌ Document Search Returns "Not Available" Messages**
```bash
# Issue: Weaviate not running
# Solution: Start Weaviate server (port 8081 to avoid conflict with backend)
docker run -d -p 8081:8080 semitechnologies/weaviate:latest
export WEAVIATE_URL="http://localhost:8081"
```

#### **❌ Tests Return Empty Output**
```bash
# Issue: Test execution problems
# Solutions:
python -m pytest tests/functional/test_basic_functionality.py -v -s
# Or try:
python verify_tests.py
```

### **System Requirements Verification**
```bash
# Check Python version (requires 3.11+)
python --version

# Check available memory (local LLM needs 2GB+)
python -c "import psutil; print(f'Available RAM: {psutil.virtual_memory().available / (1024**3):.1f} GB')"

# Check model file integrity
ls -la models/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf
```

## 🚦 Deployment

### **Production Readiness Checklist**
- ✅ **Profile 1 (API Platform)**: Ready for production
- ⚠️ **Profile 2 (Basic AI)**: Verify local LLM works before deployment
- ⚠️ **Profile 3 (Advanced)**: Ensure external services are production-ready
- ❌ **Profile 4 (Complete)**: Requires significant infrastructure planning

### Production Considerations
- Use a production WSGI server (e.g., Gunicorn)
- Configure proper logging levels
- Set up database backups
- Use environment-specific configuration
- Enable HTTPS in production
- **Test your chosen profile thoroughly before deployment**

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## 📞 Support

For questions and support, please open an issue in the repository or contact the development team.
# CI/CD Pipeline Ready!
