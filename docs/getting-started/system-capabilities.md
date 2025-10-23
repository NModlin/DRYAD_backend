# 🤖 DRYAD.AI Backend - System Capabilities & Connections

## Overview

DRYAD.AI is a **self-contained AI backend** designed for local operation with optional external service integrations.

---

## 🧠 Core AI Capabilities

### 1. Local LLM Processing
**Primary Provider: LlamaCpp**
- ✅ **Status**: Active (TinyLlama 1.1B Q4_K_M)
- 📦 **Dependency**: `llama-cpp-python>=0.2.0`
- 🎯 **Purpose**: Self-contained AI without external API dependencies
- 🚀 **Features**:
  - GGUF model format support
  - CPU/GPU inference (auto-detection)
  - Memory-mapped model loading
  - Optimized thread management
  - Context window: 2048-8192 tokens (dynamic)

**Alternative Providers**:
- **Ollama**: Local LLM server (http://localhost:11434)
  - Models: llama3.2:3b, llama3.2:1b, tinyllama
- **Hugging Face**: Transformers-based models
  - Model: microsoft/DialoGPT-medium
- **Mock**: Testing/development fallback

### 2. Multi-Agent Orchestration
- ✅ **Built-in system** (no CrewAI dependency)
- 🤖 **Available Agents**:
  - Research Agent
  - Analysis Agent
  - Writing Agent
  - Code Agent
  - Planning Agent
- 🔄 **Workflows**:
  - Simple research
  - Research → Analyze → Write
  - Complex analysis
  - Content creation
- ⚡ **Advantages**:
  - No external dependencies
  - Faster execution
  - Better error handling
  - Lower memory footprint

### 3. Vector Search & RAG
**Provider: Weaviate**
- 🔗 **Connection**: http://localhost:8080
- 📊 **Embedding Model**: all-MiniLM-L6-v2 (384 dimensions)
- 🎨 **CLIP Support**: Multi-modal embeddings (optional)
- 🔍 **Search Types**:
  - Semantic vector search
  - BM25 keyword search
  - Hybrid search
  - Document similarity
- 📝 **Collection**: GremlinsDocument

### 4. Multi-Modal Processing
- 🎵 **Audio**: Speech-to-text (Whisper)
- 🖼️ **Images**: CLIP embeddings, OCR
- 🎥 **Video**: Frame extraction, analysis
- 📄 **Documents**: PDF, DOCX, TXT parsing
- 💾 **Storage**: Local filesystem (`./data/multimodal`)

---

## 🗄️ Data Storage

### 1. Primary Database
**SQLite**
- 📍 **Location**: `sqlite:///./data/DRYAD.AI.db`
- 🔧 **ORM**: SQLAlchemy 2.0+ (async)
- 🔄 **Migrations**: Alembic
- 📊 **Data Types**:
  - Users & authentication
  - Documents & metadata
  - Chat history
  - Organizations
  - Client applications
  - Shared knowledge base

### 2. Vector Database
**Weaviate**
- 📍 **URL**: http://localhost:8080
- 🎯 **Purpose**: Semantic search, RAG
- 📦 **Status**: Optional (graceful degradation)

### 3. Cache & Task Queue
**Redis**
- 📍 **URL**: redis://localhost:6379
- 🎯 **Purpose**: 
  - Response caching
  - Session storage
  - Task queue (Celery)
- 📦 **Status**: Optional

---

## 🔐 Authentication & Security

### 1. OAuth 2.0
**Google OAuth**
- ✅ **Status**: Fully configured
- 🔑 **Client ID**: 818968828866-...
- 🌐 **Redirect**: http://localhost:3000/auth/callback
- 🎫 **Scopes**: openid, email, profile

### 2. JWT Tokens
- 🔐 **Algorithm**: HS256
- ⏱️ **Access Token**: 1 hour
- 🔄 **Refresh Token**: 30 days (HttpOnly cookie)
- 🛡️ **Security**: Client IP + User Agent tracking

### 3. Advanced Security
- 🔑 **API Key Management**: Rate limiting, expiration
- 🔏 **Data Encryption**: Fernet (AES-128)
- 🕵️ **PII Detection**: Automatic redaction
- 📝 **Audit Logging**: Security events
- 🚨 **Threat Detection**: Risk scoring

---

## 🌐 API Interfaces

### 1. REST API
- 📍 **Base URL**: http://localhost:8000
- 📚 **Docs**: http://localhost:8000/docs
- 🔢 **Endpoints**: 35+
- 📋 **Categories**:
  - `/api/v1/auth` - Authentication
  - `/api/v1/chat` - Chat & conversations
  - `/api/v1/documents` - Document management
  - `/api/v1/orchestrator` - Multi-agent tasks
  - `/api/v1/multimodal` - Multi-modal processing
  - `/api/v1/health` - System health
  - `/api/v1/mcp` - Model Context Protocol

### 2. WebSocket API
- 📍 **URL**: ws://localhost:8000/api/v1/ws/ws
- 🔄 **Real-time**: Bidirectional communication
- 📨 **Message Types**: 13+
- 🎯 **Use Cases**:
  - Live chat streaming
  - Agent workflow updates
  - System notifications
  - Progress tracking

### 3. GraphQL API
- 📍 **URL**: http://localhost:8000/graphql
- 📊 **Types**: 12+
- 🎯 **Features**:
  - Flexible queries
  - Nested data fetching
  - Real-time subscriptions

### 4. MCP (Model Context Protocol)
- 📍 **URL**: http://localhost:8000/api/v1/mcp
- 🎯 **Purpose**: Standardized AI model communication
- 🔌 **Capabilities**: Dynamic capability discovery

---

## 🔗 External Service Integrations

### Currently Connected

1. **Google OAuth** ✅
   - Authentication provider
   - User profile data

2. **Google Gemini API** ⚠️ (Optional)
   - API Key: Configured
   - Model: gemini-1.5-pro
   - Purpose: Project proposal generation
   - Status: Optional feature

### Available (Not Connected)

3. **Weaviate** ⚠️
   - Status: Degraded (not running)
   - Fallback: In-memory search

4. **Redis** ⚠️
   - Status: Not connected
   - Fallback: In-memory cache

5. **Ollama** ⚠️
   - Status: Not running
   - Alternative: LlamaCpp (active)

### Optional Integrations

6. **MinIO** (Object Storage)
   - Endpoint: localhost:9000
   - Status: Not configured

7. **Kafka** (Event Streaming)
   - Broker: localhost:9092
   - Status: Not configured

8. **Qdrant** (Alternative Vector DB)
   - Host: localhost:6333
   - Status: Not configured

---

## 📊 Monitoring & Observability

### 1. Metrics Collection
- 📈 **System Metrics**: CPU, memory, disk
- ⚡ **Performance**: Request latency, throughput
- 🤖 **AI Metrics**: LLM latency, token usage
- 🔄 **Agent Metrics**: Workflow success rate

### 2. Health Monitoring
- 🏥 **Health Endpoint**: `/api/v1/health/status`
- 🔍 **Checks**:
  - Database connectivity
  - LLM availability
  - Vector store status
  - Service dependencies

### 3. Logging
- 📝 **Structured JSON**: All logs
- 📁 **Files**:
  - `logs/gremlins_app.log` - All logs
  - `logs/gremlins_errors.log` - Errors only
  - `logs/gremlins_access.log` - API access
- 🎚️ **Level**: WARNING (silent mode)

### 4. Distributed Tracing
- 🔗 **Request Tracking**: Unique request IDs
- 📊 **Performance**: End-to-end latency
- 🐛 **Debugging**: Error propagation

---

## 🚀 Deployment Options

### 1. Basic Mode (Current)
```bash
python start.py basic
```
- ✅ SQLite database
- ✅ Local LLM (LlamaCpp)
- ✅ In-memory cache
- ✅ No external services required

### 2. Development Mode
```bash
python start.py development
```
- ✅ All basic features
- ✅ Hot reload
- ✅ Debug logging
- ✅ Development tools

### 3. Docker Basic
```bash
python start.py docker-basic
```
- 🐳 Containerized backend
- 🐳 Redis container
- 🐳 Weaviate container

### 4. Docker Full
```bash
python start.py docker-full
```
- 🐳 All services containerized
- 🐳 Nginx reverse proxy
- 🐳 Ollama LLM server
- 🐳 Celery workers
- 🐳 Production-ready

---

## 🎯 Self-Healing Capability (Proposed)

### Can the backend watch its own logs and fix errors?

**YES!** This is absolutely possible. Here's what we can build:

### Architecture

1. **Log Monitor** 👀
   - Watch `logs/gremlins_errors.log` in real-time
   - Detect error patterns
   - Classify error severity

2. **Error Analyzer** 🔍
   - Parse stack traces
   - Identify root cause
   - Find affected code files

3. **Code Generator** 🤖
   - Use local LLM to generate fixes
   - Analyze codebase context
   - Create patches

4. **Test & Validate** ✅
   - Run unit tests
   - Verify fix works
   - Check for regressions

5. **Auto-Apply** 🔧
   - Apply code changes
   - Restart affected services
   - Monitor for new errors

6. **Rollback** ↩️
   - Undo if fix fails
   - Restore previous version
   - Alert human operator

### Implementation Plan

Would you like me to implement this self-healing system? It would include:

- Real-time log monitoring
- AI-powered error analysis
- Automatic code generation
- Safe patch application
- Rollback mechanism
- Human approval workflow (optional)

---

## 📦 Dependencies Summary

### Core (Required)
- FastAPI, Uvicorn
- SQLAlchemy, Alembic
- Pydantic
- llama-cpp-python
- sentence-transformers

### Optional (Graceful Degradation)
- weaviate-client
- redis
- celery
- whisper (audio)
- PIL, opencv (images)

### External APIs (Optional)
- Google OAuth (authentication)
- Google Gemini (proposals)

---

## 🎛️ Configuration

All settings in `.env`:
- LLM provider & model
- Database URL
- External service URLs
- API keys
- Feature flags
- Security settings

---

## 📈 Current Status

✅ **Fully Operational**:
- Local LLM (LlamaCpp)
- SQLite database
- REST API
- WebSocket API
- OAuth authentication
- Multi-agent system
- Silent logging

⚠️ **Degraded** (Optional):
- Weaviate (not running)
- Redis (not connected)
- Ollama (not running)

🔧 **Ready to Implement**:
- Self-healing system
- Advanced monitoring
- Auto-scaling
- Distributed deployment

---

**Want me to implement the self-healing capability?** 🤖


