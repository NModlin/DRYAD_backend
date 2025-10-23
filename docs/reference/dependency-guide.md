# DRYAD.AI Backend - Dependency Management Guide

## Overview

The DRYAD.AI Backend now uses a **unified installation system** with automatic hardware detection and GPU acceleration. This approach eliminates the complexity of multiple installation profiles while providing optimal performance for all system configurations.

## Unified Installation

### Single Installation Command

**Installation**:
```bash
pip install -r requirements.txt
```

**What You Get**:
- ✅ **FastAPI REST API** (103+ endpoints)
- ✅ **GraphQL API** with real-time subscriptions
- ✅ **WebSocket** real-time communication
- ✅ **SQLite Database** with SQLAlchemy ORM and migrations
- ✅ **OAuth2 Authentication** (Google SSO + JWT)
- ✅ **Local LLM Support** (LlamaCpp with automatic GPU acceleration)
- ✅ **Multi-Agent System** (Built-in, no external dependencies)
- ✅ **Vector Search** (Weaviate integration with graceful fallback)
- ✅ **Document Processing** (PDF, text, semantic search)
- ✅ **Task Orchestration** (Celery + Redis with fallback)
- ✅ **Multimodal Processing** (Audio, video, image with GPU acceleration)
- ✅ **CLI Tools** and utilities

### Automatic Hardware Detection

The system automatically detects and utilizes available hardware:

**GPU Acceleration (Automatic)**:
- **CUDA Detection**: Automatically detects NVIDIA GPUs
- **LLM Acceleration**: Optimizes layer distribution based on VRAM
- **Multimodal GPU**: Accelerates Whisper, PyTorch models
- **CPU Fallback**: Graceful degradation when GPU unavailable

**Memory Optimization**:
- **Dynamic Context**: Adjusts based on available RAM
- **Model Selection**: Chooses optimal model size for system
- **Thread Optimization**: CPU core detection and optimization

### 2. Standard Installation (`requirements-standard.txt`)
**Use Case**: Production deployments with AI features, business applications

**Additional Features**:
- ✅ Vector search with Weaviate
- ✅ Multi-agent workflows (Built-in system with enhanced features)
- ✅ Semantic document search
- ✅ RAG (Retrieval-Augmented Generation)
- ✅ Task orchestration with Celery/Redis
- ✅ GraphQL API
- ✅ Advanced document processing
- ✅ Hugging Face model integration

**Installation**:
```bash
pip install -r requirements-standard.txt
```

**Resource Requirements**:
- RAM: 2GB - 4GB
- CPU: 2+ cores
- Storage: 1GB + models + data
- External Services: Weaviate, Redis

### 3. Full Installation (`requirements-full.txt`)
**Use Case**: Complete AI platform with multimodal capabilities

**Additional Features**:
- ✅ Audio processing (Whisper, TTS)
- ✅ Video processing (OpenCV, FFmpeg)
- ✅ Image processing (CLIP, PIL)
- ✅ Computer vision capabilities
- ✅ Advanced ML model support

**Installation**:
```bash
pip install -r requirements-full.txt
```

**Resource Requirements**:
- RAM: 8GB+ (16GB recommended)
- CPU: 4+ cores
- GPU: Optional but recommended for ML models
- Storage: 5GB+ for models and dependencies

### 4. Development Installation (`requirements-dev.txt`)
**Use Case**: Development, testing, code quality

**Additional Tools**:
- ✅ Testing framework (pytest, coverage)
- ✅ Test containers (Docker-based testing)
- ✅ Code quality tools (black, flake8, mypy)
- ✅ Documentation tools (mkdocs)
- ✅ Performance testing (locust)

## Dependency Conflict Resolution

### Previous Issues Fixed:
1. **CrewAI dependency removed**: Replaced with optimized built-in multi-agent system
2. **Version range conflicts**: Pinned specific compatible versions
3. **Heavy ML dependencies**: Separated into full installation tier
4. **Test dependencies**: Isolated in development requirements

### Version Pinning Strategy:
- All versions are pinned to specific releases that are tested to work together
- Regular updates will be provided as new compatible versions are verified
- Use `pip-tools` for dependency resolution in future updates

## Quick Start Commands

### For Development:
```bash
# Clone and setup
git clone <repo>
cd DRYAD_backend
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Install minimal for development
pip install -r requirements-minimal.txt
pip install -r requirements-dev.txt

# Run tests
pytest tests/
```

### For Production (Standard):
```bash
# Install standard features
pip install -r requirements-standard.txt

# Setup external services (see Docker section)
docker-compose up -d weaviate redis

# Run server
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### For Full AI Platform:
```bash
# Install all features (requires significant resources)
pip install -r requirements-full.txt

# Setup all services
docker-compose up -d

# Run with GPU support (if available)
CUDA_VISIBLE_DEVICES=0 uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## Feature Compatibility Matrix

| Feature | Minimal | Standard | Full |
|---------|---------|----------|------|
| REST API | ✅ | ✅ | ✅ |
| WebSocket | ✅ | ✅ | ✅ |
| OAuth2 Auth | ✅ | ✅ | ✅ |
| Document Upload | ✅ | ✅ | ✅ |
| Simple Chat | ✅ | ✅ | ✅ |
| Vector Search | ❌ | ✅ | ✅ |
| Multi-Agent | ❌ | ✅ | ✅ |
| GraphQL | ❌ | ✅ | ✅ |
| Task Queue | ❌ | ✅ | ✅ |
| Audio Processing | ❌ | ❌ | ✅ |
| Video Processing | ❌ | ❌ | ✅ |
| Image Processing | ❌ | ❌ | ✅ |

## Troubleshooting

### Common Issues:

1. **Import Errors**: Ensure you're using the correct requirements file for your use case
2. **Memory Issues**: Use minimal installation for resource-constrained environments
3. **GPU Issues**: Full installation works without GPU but performance may be limited
4. **Service Dependencies**: Standard/Full require external services (see Docker guide)

### Upgrade Path:
```bash
# From minimal to standard
pip install -r requirements-standard.txt

# From standard to full
pip install -r requirements-full.txt
```

## Next Steps

1. Choose your installation tier based on needs and resources
2. Follow the Docker setup guide for external services
3. Review the deployment documentation for production setup
4. Run the test suite to verify your installation
