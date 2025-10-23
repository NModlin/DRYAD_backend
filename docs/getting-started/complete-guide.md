# DRYAD.AI Backend - Complete Guide

**Version:** 9.0.0 | **Architecture:** Self-Contained AI with Local LLM + Vector Database + Multi-Client Support

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Docker & Docker Compose
- 8GB+ RAM (4GB minimum)
- 10GB+ free disk space

### 1. Clone and Setup
```bash
git clone <repository-url>
cd DRYAD_backend
cp .env.example .env
# Edit .env with your configuration
```

### 2. Install Dependencies
```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# or
.venv\Scripts\activate     # Windows

# Install based on your needs
pip install -r requirements-minimal.txt    # Basic functionality
pip install -r requirements-standard.txt   # Full AI features (recommended)
pip install -r requirements-full.txt       # All features including multimodal
```

### 3. Start External Services (Optional)
```bash
# Option 1: Use built-in LlamaCpp (Recommended - No external services needed)
# Models are automatically downloaded to ./models/ directory

# Option 2: Use Ollama (Alternative)
docker run -d -p 11434:11434 --name ollama ollama/ollama:latest

# Start Weaviate (Vector Database) - Optional for advanced features
docker run -d -p 8080:8080 --name weaviate semitechnologies/weaviate:1.26.1

# Start Redis (Task Queue) - Optional for background processing
docker run -d -p 6379:6379 --name redis redis:alpine
```

### 4. Download AI Models (If using Ollama)
```bash
# Only needed if using Ollama instead of LlamaCpp
docker exec ollama ollama pull llama3.2:3b    # High quality (1.9GB)
docker exec ollama ollama pull tinyllama       # Fast/lightweight (608MB)
```

### 5. Configure Environment
Edit your `.env` file:
```env
# LLM Configuration (Self-Contained AI)
LLM_PROVIDER="llamacpp"
LLAMACPP_MODEL="tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf"

# Alternative: Ollama (optional)
OLLAMA_BASE_URL="http://localhost:11434"
OLLAMA_MODEL="llama3.2:3b"

# Database Configuration
DATABASE_URL="sqlite:///./data/DRYAD.AI.db"
WEAVIATE_URL="http://localhost:8080"
REDIS_URL="redis://localhost:6379"

# Security
JWT_SECRET_KEY="your-secure-secret-key-change-in-production"
```

### 6. Initialize Database
```bash
alembic upgrade head
```

### 7. Start DRYAD.AI
```bash
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 8. Verify Setup
- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/api/v1/health/status
- **Weaviate Console**: http://localhost:8080/v1/meta

## 🏗️ Architecture Overview

### Core Components
- **FastAPI**: REST API framework with 100+ endpoints
- **SQLite**: Primary database for structured data (users, documents, chat history)
- **Weaviate**: Vector database for semantic search and RAG
- **LlamaCpp**: Primary local LLM provider for AI inference
- **Ollama**: Alternative local LLM server (optional)
- **Redis**: Task queue and caching
- **LangChain + Built-in Multi-Agent**: AI orchestration and multi-agent workflows

### Data Flow
1. **User Request** → FastAPI endpoint
2. **Authentication** → JWT validation
3. **AI Processing** → Local LlamaCpp LLM (no external APIs)
4. **Vector Search** → Weaviate for document retrieval (optional)
5. **Response** → JSON with AI-generated content

### Self-Contained AI Features
- ✅ **No External API Dependencies**: All AI processing happens locally
- ✅ **Explicit Failure Handling**: System fails clearly if local LLM unavailable
- ✅ **No Data Leakage**: No data sent to external services
- ✅ **Offline Capable**: Works without internet connection
- ✅ **Privacy First**: All conversations and documents stay local

## 📚 API Reference

### Authentication Endpoints
- `POST /api/v1/auth/token` - Get JWT token
- `GET /api/v1/auth/me` - Get current user info
- `POST /api/v1/auth/logout` - Logout user

### AI Agent Endpoints
- `POST /api/v1/agent/simple-chat` - Basic AI chat
- `POST /api/v1/agent/chat` - Advanced AI chat with context
- `POST /api/v1/multi-agent/workflow` - Multi-agent collaboration

### Document & RAG Endpoints
- `POST /api/v1/documents/upload` - Upload documents
- `POST /api/v1/documents/rag` - RAG query against documents
- `GET /api/v1/documents` - List documents
- `DELETE /api/v1/documents/{id}` - Delete document

### Real-time Communication
- `WebSocket /api/v1/realtime-ws/ws/{session_id}` - Real-time updates
- `POST /api/v1/realtime/broadcast` - Broadcast messages

### Health & Monitoring
- `GET /api/v1/health/status` - System health
- `GET /api/v1/health/performance` - Performance metrics
- `GET /api/v1/health/errors` - Error statistics

## 🔧 Configuration

### Installation Tiers

#### Minimal (`requirements-minimal.txt`)
- Basic API functionality
- Simple chat with local LLM
- Document upload/storage
- SQLite database
- **Use Case**: Development, testing, lightweight deployments

#### Standard (`requirements-standard.txt`) - **Recommended**
- All minimal features
- Vector search with Weaviate
- Multi-agent workflows
- Task orchestration with Celery
- GraphQL API
- **Use Case**: Production AI applications

#### Full (`requirements-full.txt`)
- All standard features
- Multimodal processing (audio, video, image)
- Advanced ML models
- Computer vision capabilities
- **Use Case**: Complete AI platform with multimedia

### Environment Variables

#### Core Settings
```env
ENVIRONMENT=development          # development, staging, production
LOG_LEVEL=INFO                  # DEBUG, INFO, WARNING, ERROR
INSTALL_TIER=standard           # minimal, standard, full
```

#### LLM Configuration
```env
LLM_PROVIDER=llamacpp           # llamacpp (recommended), ollama, mock (for testing)
LLAMACPP_MODEL=tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf  # Primary model
OLLAMA_BASE_URL=http://localhost:11434  # If using Ollama
OLLAMA_MODEL=llama3.2:3b        # If using Ollama
LLM_TEMPERATURE=0.1             # 0.0-1.0, lower = more focused
LLM_MAX_TOKENS=2048             # Maximum response length
```

#### Database Configuration
```env
DATABASE_URL=sqlite:///./data/DRYAD.AI.db
WEAVIATE_URL=http://localhost:8080
WEAVIATE_CLASS_NAME=GremlinsDocument
EMBEDDING_MODEL=all-MiniLM-L6-v2
REDIS_URL=redis://localhost:6379
```

## 🚨 Troubleshooting

### Common Issues

#### 1. "Connection refused" errors
**Symptoms**: Cannot connect to Ollama, Weaviate, or Redis
**Solution**:
```bash
# Check if services are running
docker ps

# Start missing services
docker start ollama weaviate redis

# Check service health
curl http://localhost:11434/api/tags    # Ollama
curl http://localhost:8080/v1/meta      # Weaviate
redis-cli ping                          # Redis
```

#### 2. "No models available" error
**Symptoms**: LLM requests fail with model not found
**Solution**:
```bash
# List available models
docker exec ollama ollama list

# Download models if missing
docker exec ollama ollama pull llama3.2:3b
docker exec ollama ollama pull tinyllama
```

#### 3. Import errors or dependency conflicts
**Symptoms**: ModuleNotFoundError or version conflicts
**Solution**:
```bash
# Clean install
pip uninstall -r requirements.txt -y
pip install -r requirements-standard.txt

# Check Python version
python --version  # Should be 3.11+
```

#### 4. Database migration errors
**Symptoms**: SQLAlchemy or Alembic errors
**Solution**:
```bash
# Reset database (WARNING: loses data)
rm data/DRYAD.AI.db
alembic upgrade head

# Or create data directory
mkdir -p data
alembic upgrade head
```

#### 5. Performance issues
**Symptoms**: Slow responses, high memory usage
**Solution**:
```bash
# Use lighter model
# In .env: OLLAMA_MODEL=tinyllama

# Check system resources
docker stats

# Restart services
docker restart ollama weaviate redis
```

### Health Checks
```bash
# System health
curl http://localhost:8000/api/v1/health/status

# Service status
curl http://localhost:11434/api/tags     # Ollama models
curl http://localhost:8080/v1/meta       # Weaviate info
redis-cli ping                           # Redis connectivity

# Test AI functionality
curl -X POST http://localhost:8000/api/v1/agent/simple-chat \
  -H "Content-Type: application/json" \
  -d '{"input": "Hello, test message"}'
```

### Log Analysis
```bash
# Application logs
tail -f logs/gremlins_app.log

# Error logs
tail -f logs/gremlins_errors.log

# Docker service logs
docker logs ollama
docker logs weaviate
docker logs redis
```

## 🔒 Security & Production

### Security Features
- JWT-based authentication
- OAuth2 integration (Google)
- Request rate limiting
- Input validation and sanitization
- CORS protection
- Secure headers

### Production Checklist
- [ ] Change default JWT secret key
- [ ] Set up proper SSL/TLS certificates
- [ ] Configure firewall rules
- [ ] Set up log rotation
- [ ] Configure backup strategy
- [ ] Monitor system resources
- [ ] Set up alerting

### Backup Strategy
```bash
# Database backup
cp data/DRYAD.AI.db data/backup_$(date +%Y%m%d).db

# Weaviate backup
docker exec weaviate weaviate-backup create backup_$(date +%Y%m%d)

# Configuration backup
cp .env .env.backup
```

## 📊 Performance Optimization

### Model Selection
- **llama3.2:3b**: Best quality, 3-4GB RAM, 2-5s response time
- **tinyllama**: Fastest, 1GB RAM, <1s response time
- **llama3.2:1b**: Balanced, 2GB RAM, 1-2s response time

### System Requirements
- **Minimal**: 4GB RAM, 2 CPU cores, 5GB storage
- **Standard**: 8GB RAM, 4 CPU cores, 15GB storage
- **Full**: 16GB RAM, 8 CPU cores, 50GB storage

### Optimization Tips
1. Use SSD storage for better I/O performance
2. Allocate sufficient RAM to avoid swapping
3. Use lighter models for development/testing
4. Enable Redis caching for frequently accessed data
5. Monitor and tune Weaviate memory settings

## 🏢 Multi-Client Architecture

### Client Application Integration

DRYAD.AI now supports multiple client applications with secure isolation and cross-client learning:

#### 1. Model Context Protocol (MCP) Integration
```bash
# MCP endpoints
GET  /api/v1/mcp/capabilities     # Get server capabilities
POST /api/v1/mcp                  # Main MCP protocol endpoint
POST /api/v1/mcp/notifications    # Handle client notifications
GET  /api/v1/mcp/health          # MCP server health check
```

#### 2. Client Authentication
```bash
# API Key Authentication (for client applications)
curl -H "X-API-Key: gai_your_api_key_here" \
     -H "Content-Type: application/json" \
     http://localhost:8000/api/v1/mcp/capabilities

# OAuth2 + JWT (for user authentication within clients)
curl -H "Authorization: Bearer your_jwt_token" \
     -H "Content-Type: application/json" \
     http://localhost:8000/api/v1/documents/search
```

#### 3. Tenant Isolation Levels
- **Strict**: Complete data isolation per client
- **Shared**: Shared learning with private data
- **Collaborative**: Explicit data sharing between clients

#### 4. Cross-Client Learning
- Privacy-preserving knowledge aggregation
- Differential privacy for embeddings
- Federated learning insights
- Anonymized content sharing

### Database Schema Updates

The multi-client architecture adds these new tables:
- `organizations`: Client organization management
- `client_applications`: Client app registration and API keys
- `shared_knowledge`: Cross-client learning data with privacy controls

### Environment Variables for Multi-Client

Add these to your `.env` file:
```bash
# Multi-client settings
ENABLE_MULTI_CLIENT=true
DEFAULT_ISOLATION_LEVEL=strict
ENABLE_CROSS_CLIENT_LEARNING=true
DIFFERENTIAL_PRIVACY_EPSILON=1.0
```

---

**Need Help?** Check the API documentation at http://localhost:8000/docs, MCP capabilities at http://localhost:8000/api/v1/mcp/capabilities, or review the health status at http://localhost:8000/api/v1/health/status
