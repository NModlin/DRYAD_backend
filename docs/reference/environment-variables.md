# DRYAD.AI Backend - Environment Variables Reference

## Overview

This document provides a comprehensive reference for all environment variables used in the DRYAD.AI Backend system. Variables are organized by category with descriptions, default values, and usage examples.

## Quick Reference

### Essential Variables (Required)

```bash
# Security
JWT_SECRET_KEY=your-super-secret-jwt-key-change-in-production

# Installation
INSTALL_TIER=standard  # minimal, standard, full, development

# LLM Provider
LLM_PROVIDER=ollama  # ollama (hybrid cloud/local), llamacpp, mock, openai, huggingface
```

### Common Configuration

```bash
# Environment
ENVIRONMENT=development
LOG_LEVEL=INFO
DATABASE_URL=sqlite:///./data/DRYAD.AI.db

# Services (for standard/full installations)
WEAVIATE_URL=http://weaviate:8080
CELERY_BROKER_URL=redis://redis:6379/0
```

## Core Application Variables

### Installation and Environment

| Variable | Description | Default | Required | Values |
|----------|-------------|---------|----------|---------|
| `INSTALL_TIER` | Installation tier/feature set | `standard` | Yes | `minimal`, `standard`, `full`, `development` |
| `ENVIRONMENT` | Deployment environment | `development` | No | `development`, `staging`, `production` |
| `LOG_LEVEL` | Logging verbosity | `INFO` | No | `DEBUG`, `INFO`, `WARNING`, `ERROR` |
| `DEBUG` | Enable debug mode | `false` | No | `true`, `false` |

**Examples:**
```bash
# Development setup
INSTALL_TIER=development
ENVIRONMENT=development
LOG_LEVEL=DEBUG
DEBUG=true

# Production setup
INSTALL_TIER=standard
ENVIRONMENT=production
LOG_LEVEL=INFO
DEBUG=false
```

### API Configuration

| Variable | Description | Default | Required | Example |
|----------|-------------|---------|----------|---------|
| `API_BASE_URL` | Base URL for API | `http://localhost:8000` | No | `https://api.yourdomain.com` |
| `FRONTEND_URL` | Frontend application URL | `http://localhost:3000` | No | `https://yourdomain.com` |
| `WORKER_COUNT` | Number of API workers | `2` | No | `4` |
| `RELOAD` | Enable hot reload (dev) | `false` | No | `true`, `false` |

**Examples:**
```bash
# Local development
API_BASE_URL=http://localhost:8000
FRONTEND_URL=http://localhost:3000
WORKER_COUNT=2
RELOAD=true

# Production
API_BASE_URL=https://api.yourdomain.com
FRONTEND_URL=https://yourdomain.com
WORKER_COUNT=4
RELOAD=false
```

## Security Configuration

### Authentication and Authorization

| Variable | Description | Default | Required | Notes |
|----------|-------------|---------|----------|-------|
| `JWT_SECRET_KEY` | JWT signing secret | None | **Yes** | Must be changed in production |
| `JWT_ALGORITHM` | JWT signing algorithm | `HS256` | No | Recommended: `HS256` |
| `JWT_EXPIRATION_HOURS` | JWT token lifetime | `24` | No | Hours until token expires |
| `REFRESH_TOKEN_EXPIRATION_DAYS` | Refresh token lifetime | `30` | No | Days until refresh expires |

**Security Best Practices:**
```bash
# Generate secure secret
JWT_SECRET_KEY=$(python -c "import secrets; print(secrets.token_urlsafe(48))")

# Production settings
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24
REFRESH_TOKEN_EXPIRATION_DAYS=30
```

### OAuth2 Configuration

| Variable | Description | Default | Required | Notes |
|----------|-------------|---------|----------|-------|
| `GOOGLE_CLIENT_ID` | Google OAuth2 client ID | None | No | For Google authentication |
| `GOOGLE_CLIENT_SECRET` | Google OAuth2 client secret | None | No | Keep secret |
| `OAUTH_REDIRECT_URI` | OAuth2 redirect URI | Auto-generated | No | Must match provider settings |

**OAuth2 Setup:**
```bash
# Google OAuth2
GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-client-secret
OAUTH_REDIRECT_URI=http://localhost:8000/api/v1/auth/google/callback
```

### CORS and Security Headers

| Variable | Description | Default | Required | Example |
|----------|-------------|---------|----------|---------|
| `CORS_ORIGINS` | Allowed CORS origins | `["*"]` | No | `["https://yourdomain.com"]` |
| `SECURE_COOKIES` | Use secure cookies | `false` | No | `true` for HTTPS |
| `HTTPS_ONLY` | Force HTTPS redirects | `false` | No | `true` for production |

**Security Headers:**
```bash
# Production CORS
CORS_ORIGINS=["https://yourdomain.com", "https://app.yourdomain.com"]

# Security settings
SECURE_COOKIES=true
HTTPS_ONLY=true
```

## Database Configuration

### Primary Database

| Variable | Description | Default | Required | Example |
|----------|-------------|---------|----------|---------|
| `DATABASE_URL` | Database connection URL | `sqlite:///./data/DRYAD.AI.db` | No | See examples below |

**Database URL Examples:**
```bash
# SQLite (default and recommended)
DATABASE_URL=sqlite:///./data/DRYAD.AI.db

# Note: DRYAD.AI uses SQLite for structured data and Weaviate for vector storage
# This hybrid approach provides optimal performance for AI applications
```

### Database Pool Settings

| Variable | Description | Default | Required | Notes |
|----------|-------------|---------|----------|-------|
| `DB_POOL_SIZE` | Connection pool size | `5` | No | Max concurrent connections |
| `DB_MAX_OVERFLOW` | Pool overflow limit | `10` | No | Additional connections |
| `DB_POOL_TIMEOUT` | Connection timeout | `30` | No | Seconds |

### Multi-Client Database Settings

| Variable | Description | Default | Required | Notes |
|----------|-------------|---------|----------|-------|
| `ENABLE_MULTI_CLIENT` | Enable multi-client architecture | `false` | No | Enables client isolation |
| `DEFAULT_ISOLATION_LEVEL` | Default client isolation level | `strict` | No | strict, shared, collaborative |
| `ENABLE_CROSS_CLIENT_LEARNING` | Enable knowledge sharing | `false` | No | Privacy-preserving learning |
| `DIFFERENTIAL_PRIVACY_EPSILON` | Privacy noise parameter | `1.0` | No | Lower = more privacy |

## LLM Provider Configuration

### Provider Selection

| Variable | Description | Default | Required | Values |
|----------|-------------|---------|----------|---------|
| `LLM_PROVIDER` | LLM service provider | `ollama` | No | `ollama` (hybrid), `llamacpp`, `mock`, `openai`, `huggingface` |

### LlamaCpp Configuration (Recommended)

| Variable | Description | Default | Required | Notes |
|----------|-------------|---------|----------|-------|
| `LLAMACPP_MODEL` | GGUF model filename | `tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf` | No | Auto-downloaded to ./models/ |
| `LLAMACPP_N_CTX` | Context window size | `2048` | No | Model-dependent |
| `LLAMACPP_N_THREADS` | CPU threads to use | `auto` | No | Auto-detects optimal |

**LlamaCpp Setup (Recommended):**
```bash
LLM_PROVIDER=llamacpp
LLAMACPP_MODEL=tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf
LLM_TEMPERATURE=0.1
LLM_MAX_TOKENS=2048
```

### OpenAI Configuration

| Variable | Description | Default | Required | Notes |
|----------|-------------|---------|----------|-------|
| `OPENAI_API_KEY` | OpenAI API key | None | If using OpenAI | Keep secret |
| `OPENAI_MODEL` | OpenAI model name | `gpt-3.5-turbo` | No | `gpt-4`, `gpt-3.5-turbo`, etc. |
| `OPENAI_MAX_TOKENS` | Max tokens per request | `2048` | No | Model-dependent limit |
| `OPENAI_TEMPERATURE` | Response randomness | `0.1` | No | 0.0-2.0 |

**OpenAI Setup:**
```bash
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-your-openai-api-key-here
OPENAI_MODEL=gpt-3.5-turbo
OPENAI_MAX_TOKENS=2048
OPENAI_TEMPERATURE=0.1
```

### Ollama Configuration (Hybrid Cloud/Local)

| Variable | Description | Default | Required | Notes |
|----------|-------------|---------|----------|-------|
| `OLLAMA_BASE_URL` | Local Ollama server URL | `http://localhost:11434` | No | Local fallback server |
| `OLLAMA_MODEL` | Default local model | `llama3.2:3b` | No | Must be pulled first |
| `OLLAMA_CLOUD_URL` | Ollama Cloud endpoint | `https://ollama.com` | No | Cloud service URL |
| `OLLAMA_CLOUD_ENABLED` | Enable cloud routing | `true` | No | `true`, `false` |
| `OLLAMA_CLOUD_FIRST` | Prefer cloud models | `true` | No | Cloud-first routing |
| `OLLAMA_API_KEY` | Ollama Cloud API key | None | For cloud | Keep secret |
| `OLLAMA_TIMEOUT` | Request timeout | `60` | No | Seconds |

**Hybrid Ollama Setup (Recommended):**
```bash
LLM_PROVIDER=ollama

# Local Ollama (fallback)
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2:3b

# Cloud Ollama (primary)
OLLAMA_CLOUD_URL=https://ollama.com
OLLAMA_CLOUD_ENABLED=true
OLLAMA_CLOUD_FIRST=true
OLLAMA_API_KEY=your_api_key_here
```

**Local-Only Ollama Setup:**
```bash
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2:3b
OLLAMA_CLOUD_ENABLED=false
```

### Hugging Face Configuration

| Variable | Description | Default | Required | Notes |
|----------|-------------|---------|----------|-------|
| `HF_MODEL` | Hugging Face model | `microsoft/DialoGPT-medium` | If using HF | Model identifier |
| `HF_API_KEY` | Hugging Face API key | None | No | For private models |
| `USE_HUGGINGFACE` | Enable HF provider | `false` | No | `true`, `false` |

### General LLM Settings

| Variable | Description | Default | Required | Notes |
|----------|-------------|---------|----------|-------|
| `LLM_TEMPERATURE` | Response randomness | `0.1` | No | 0.0-2.0 |
| `LLM_MAX_TOKENS` | Max tokens per response | `2048` | No | Model-dependent |
| `LLM_TIMEOUT` | Request timeout | `30` | No | Seconds |

## Vector Database Configuration

### Weaviate Settings

| Variable | Description | Default | Required | Notes |
|----------|-------------|---------|----------|-------|
| `WEAVIATE_URL` | Weaviate server URL | `http://weaviate:8081` | For standard/full | HTTP endpoint (port 8081 to avoid conflict) |
| `WEAVIATE_API_KEY` | Weaviate API key | None | No | For cloud instances |
| `WEAVIATE_TIMEOUT_SECONDS` | Request timeout | `10` | No | Seconds |
| `WEAVIATE_MAX_RETRIES` | Max retry attempts | `3` | No | Connection retries |
| `WEAVIATE_CLASS_NAME` | Document class name | `GremlinsDocument` | No | Schema class |

**Weaviate Configuration:**
```bash
# Local Weaviate (port 8081 to avoid conflict with backend on port 8000)
WEAVIATE_URL=http://weaviate:8081
WEAVIATE_TIMEOUT_SECONDS=10
WEAVIATE_MAX_RETRIES=3

# Cloud Weaviate
WEAVIATE_URL=https://your-cluster.weaviate.network
WEAVIATE_API_KEY=your-weaviate-api-key
```

## Model Context Protocol (MCP) Configuration

### MCP Server Settings

| Variable | Description | Default | Required | Notes |
|----------|-------------|---------|----------|-------|
| `MCP_ENABLED` | Enable MCP server | `true` | No | Standardized client interface |
| `MCP_VERSION` | MCP protocol version | `2025-06-18` | No | Protocol compatibility |
| `MCP_MAX_CLIENTS` | Max concurrent MCP clients | `100` | No | Resource management |
| `MCP_TIMEOUT_SECONDS` | MCP request timeout | `30` | No | Seconds |

**MCP Configuration:**
```bash
# Enable MCP server
MCP_ENABLED=true
MCP_VERSION=2025-06-18
MCP_MAX_CLIENTS=100
MCP_TIMEOUT_SECONDS=30
```

### Client Application Authentication

| Variable | Description | Default | Required | Notes |
|----------|-------------|---------|----------|-------|
| `CLIENT_API_KEY_LENGTH` | API key length | `32` | No | Security strength |
| `CLIENT_SESSION_TIMEOUT` | Client session timeout | `3600` | No | Seconds |
| `REQUIRE_CLIENT_REGISTRATION` | Require client registration | `true` | No | Security control |

### Embedding Configuration

| Variable | Description | Default | Required | Notes |
|----------|-------------|---------|----------|-------|
| `EMBEDDING_MODEL` | Sentence transformer model | `all-MiniLM-L6-v2` | No | HuggingFace model |
| `USE_CLIP` | Enable CLIP embeddings | `true` | No | For multimodal |
| `CLIP_MODEL` | CLIP model name | `ViT-B/32` | No | Image embeddings |

## Task Queue Configuration

### Redis Settings

| Variable | Description | Default | Required | Notes |
|----------|-------------|---------|----------|-------|
| `REDIS_URL` | Redis connection URL | `redis://redis:6379` | For standard/full | Full URL |
| `CELERY_BROKER_URL` | Celery broker URL | `redis://redis:6379/0` | For standard/full | Task queue |
| `CELERY_RESULT_BACKEND` | Result backend URL | `redis://redis:6379/0` | For standard/full | Task results |

### Celery Configuration

| Variable | Description | Default | Required | Notes |
|----------|-------------|---------|----------|-------|
| `CELERY_CONCURRENCY` | Worker concurrency | `2` | No | Concurrent tasks |
| `CELERY_MAX_RETRIES` | Max task retries | `3` | No | Failed task retries |
| `CELERY_RETRY_DELAY` | Retry delay | `60` | No | Seconds between retries |

**Task Queue Setup:**
```bash
# Redis configuration
REDIS_URL=redis://redis:6379
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0

# Worker settings
CELERY_CONCURRENCY=2
CELERY_MAX_RETRIES=3
CELERY_RETRY_DELAY=60
```

## Feature Flags

### Service Toggles

| Variable | Description | Default | Required | Notes |
|----------|-------------|---------|----------|-------|
| `ENABLE_VECTOR_SEARCH` | Enable vector search | `true` | No | Requires Weaviate |
| `ENABLE_MULTI_AGENT` | Enable multi-agent | `true` | No | Requires task queue |
| `ENABLE_MULTIMODAL` | Enable multimodal | `false` | No | Full installation only |
| `ENABLE_TASK_QUEUE` | Enable background tasks | `true` | No | Requires Redis |
| `ENABLE_GRAPHQL` | Enable GraphQL API | `true` | No | Alternative API |

**Feature Configuration:**
```bash
# Standard features
ENABLE_VECTOR_SEARCH=true
ENABLE_MULTI_AGENT=true
ENABLE_TASK_QUEUE=true
ENABLE_GRAPHQL=true

# Disable heavy features
ENABLE_MULTIMODAL=false
```

## Multimodal Configuration (Full Installation)

### Audio Processing

| Variable | Description | Default | Required | Notes |
|----------|-------------|---------|----------|-------|
| `WHISPER_MODEL` | Whisper model size | `base` | No | `tiny`, `base`, `small`, `medium`, `large` |
| `TTS_VOICE` | Text-to-speech voice | `alloy` | No | OpenAI TTS voices |
| `AUDIO_MAX_DURATION` | Max audio length | `300` | No | Seconds |

### Video Processing

| Variable | Description | Default | Required | Notes |
|----------|-------------|---------|----------|-------|
| `FFMPEG_PATH` | FFmpeg binary path | `/usr/bin/ffmpeg` | No | Video processing |
| `VIDEO_MAX_DURATION` | Max video length | `600` | No | Seconds |
| `VIDEO_MAX_SIZE` | Max video file size | `100MB` | No | File size limit |

### Image Processing

| Variable | Description | Default | Required | Notes |
|----------|-------------|---------|----------|-------|
| `CLIP_MODEL` | CLIP model for images | `ViT-B/32` | No | Image understanding |
| `IMAGE_MAX_SIZE` | Max image file size | `10MB` | No | File size limit |
| `IMAGE_MAX_DIMENSION` | Max image dimension | `2048` | No | Pixels |

## Monitoring and Observability

### Logging Configuration

| Variable | Description | Default | Required | Notes |
|----------|-------------|---------|----------|-------|
| `LOG_FORMAT` | Log output format | `text` | No | `text`, `json` |
| `LOG_FILE` | Log file path | None | No | File logging |
| `LOG_ROTATION` | Enable log rotation | `true` | No | Prevent large files |
| `LOG_MAX_SIZE` | Max log file size | `100MB` | No | Before rotation |

### Metrics and Monitoring

| Variable | Description | Default | Required | Notes |
|----------|-------------|---------|----------|-------|
| `PROMETHEUS_ENABLED` | Enable Prometheus metrics | `false` | No | Metrics collection |
| `METRICS_PORT` | Metrics endpoint port | `9090` | No | Prometheus port |
| `HEALTH_CHECK_INTERVAL` | Health check frequency | `30` | No | Seconds |

## Resource Limits

### Memory and CPU

| Variable | Description | Default | Required | Notes |
|----------|-------------|---------|----------|-------|
| `MEMORY_LIMIT` | Container memory limit | `2g` | No | Docker memory limit |
| `CPU_LIMIT` | Container CPU limit | `2` | No | CPU cores |
| `MAX_UPLOAD_SIZE` | Max file upload size | `50MB` | No | API upload limit |

### Cache Configuration

| Variable | Description | Default | Required | Notes |
|----------|-------------|---------|----------|-------|
| `REDIS_CACHE_TTL` | Cache time-to-live | `3600` | No | Seconds |
| `ENABLE_QUERY_CACHE` | Enable query caching | `true` | No | Performance optimization |
| `CACHE_MAX_SIZE` | Max cache size | `1GB` | No | Memory limit |

## Development and Testing

### Development Settings

| Variable | Description | Default | Required | Notes |
|----------|-------------|---------|----------|-------|
| `TESTING` | Enable testing mode | `false` | No | Test environment |
| `TEST_DATABASE_URL` | Test database URL | `sqlite:///./data/test.db` | No | Separate test DB |
| `MOCK_EXTERNAL_APIS` | Mock external services | `false` | No | Testing isolation |

### Debug Configuration

| Variable | Description | Default | Required | Notes |
|----------|-------------|---------|----------|-------|
| `DEBUG_SQL` | Log SQL queries | `false` | No | Database debugging |
| `DEBUG_REQUESTS` | Log HTTP requests | `false` | No | API debugging |
| `PROFILING_ENABLED` | Enable performance profiling | `false` | No | Performance analysis |

## Environment File Examples

### Minimal Installation (.env)
```bash
INSTALL_TIER=minimal
ENVIRONMENT=development
JWT_SECRET_KEY=your-secret-key-here
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2:3b
OLLAMA_CLOUD_ENABLED=false
DATABASE_URL=sqlite:///./data/DRYAD.AI.db
LOG_LEVEL=INFO
```

### Standard Installation (.env)
```bash
INSTALL_TIER=standard
ENVIRONMENT=production
JWT_SECRET_KEY=your-production-secret-key
LLM_PROVIDER=ollama

# Hybrid Cloud/Local LLM
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2:3b
OLLAMA_CLOUD_URL=https://ollama.com
OLLAMA_CLOUD_ENABLED=true
OLLAMA_CLOUD_FIRST=true
OLLAMA_API_KEY=your_api_key_here

DATABASE_URL=postgresql://user:pass@db:5432/DRYAD.AI
WEAVIATE_URL=http://weaviate:8081
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0
CORS_ORIGINS=["https://yourdomain.com"]
LOG_LEVEL=INFO
```

### Full Installation (.env)
```bash
INSTALL_TIER=full
ENVIRONMENT=production
JWT_SECRET_KEY=your-production-secret-key
LLM_PROVIDER=openai
OPENAI_API_KEY=your-openai-key
DATABASE_URL=postgresql://user:pass@db:5432/DRYAD.AI
WEAVIATE_URL=http://weaviate:8081
CELERY_BROKER_URL=redis://redis:6379/0
ENABLE_MULTIMODAL=true
WHISPER_MODEL=base
CLIP_MODEL=ViT-B/32
PROMETHEUS_ENABLED=true
LOG_LEVEL=INFO
```

## Validation and Troubleshooting

### Environment Validation

Check your environment configuration:

```bash
# Validate required variables
python -c "
import os
required = ['JWT_SECRET_KEY', 'INSTALL_TIER']
missing = [var for var in required if not os.getenv(var)]
if missing:
    print(f'Missing required variables: {missing}')
else:
    print('All required variables are set')
"

# Check database connection
python -c "
import os
from sqlalchemy import create_engine
try:
    engine = create_engine(os.getenv('DATABASE_URL'))
    engine.connect()
    print('Database connection successful')
except Exception as e:
    print(f'Database connection failed: {e}')
"
```

### Common Issues

1. **JWT_SECRET_KEY not set**: Generate with `python -c "import secrets; print(secrets.token_urlsafe(48))"`
2. **Database connection failed**: Check DATABASE_URL format and credentials
3. **Service connection timeout**: Verify service URLs and network connectivity
4. **Permission denied**: Check file permissions for data directories

For more troubleshooting help, see [TROUBLESHOOTING.md](TROUBLESHOOTING.md).
