# 🚀 Auto-Start Services - Complete Setup

## Overview

DRYAD.AI now **automatically starts and manages** Weaviate, Redis, and Ollama services. These services are always active and restart automatically if they fail.

---

## 🎯 What's New

### Auto-Start Services
- ✅ **Weaviate** - Vector database (port 8080)
- ✅ **Redis** - Cache & task queue (port 6379)
- ✅ **Ollama** - Local LLM server (port 11434)

### Features
- 🔄 **Auto-restart** - Services restart if they crash
- 🏥 **Health monitoring** - Automatic health checks
- 📊 **Status tracking** - Real-time service status
- 🐳 **Docker-based** - Isolated, reproducible environments
- 💾 **Persistent data** - Data survives restarts

---

## 📋 Prerequisites

### 1. Docker Desktop
**Required for running services**

**Windows:**
- Download: https://www.docker.com/products/docker-desktop
- Install and start Docker Desktop
- Ensure it's running (check system tray)

**Verify Docker:**
```bash
docker --version
docker ps
```

### 2. Python Dependencies
```bash
pip install requests redis
```

---

## 🚀 Quick Start

### Option 1: Automatic (Recommended)

**Just start the backend - services auto-start!**

```bash
python start.py basic
```

That's it! The backend will:
1. Check if services are running
2. Auto-start them if needed
3. Wait for them to be healthy
4. Start the backend

### Option 2: Manual Service Management

**Start services separately:**

```bash
# Windows
services.bat start

# Linux/Mac
python scripts/manage_services.py start
```

**Then start backend:**
```bash
python start.py basic --no-services
```

---

## 🛠️ Service Management Commands

### Windows (Easy)

```bash
# Start all services
services.bat start

# Check status
services.bat status

# Stop services
services.bat stop

# Restart services
services.bat restart

# View logs
services.bat logs

# View specific service logs
services.bat logs weaviate
services.bat logs redis
services.bat logs ollama

# Setup Ollama models
services.bat setup
```

### Linux/Mac/Windows (Python)

```bash
# Start services
python scripts/manage_services.py start

# Check status
python scripts/manage_services.py status

# Stop services
python scripts/manage_services.py stop

# Restart services
python scripts/manage_services.py restart

# View logs (follow mode)
python scripts/manage_services.py logs -f

# View specific service
python scripts/manage_services.py logs --service weaviate

# Pull latest images
python scripts/manage_services.py pull

# Setup Ollama models
python scripts/manage_services.py setup-ollama
```

---

## 📊 Service Details

### Weaviate (Vector Database)
- **Port**: 8080
- **Health**: http://localhost:8080/v1/.well-known/ready
- **Purpose**: Semantic search, RAG, document similarity
- **Data**: Persisted in Docker volume `weaviate_data`

### Redis (Cache & Queue)
- **Port**: 6379
- **Purpose**: Response caching, session storage, task queue
- **Data**: Persisted in Docker volume `redis_data`
- **Config**: 512MB max memory, LRU eviction

### Ollama (LLM Server)
- **Port**: 11434
- **API**: http://localhost:11434/api/tags
- **Purpose**: Alternative local LLM (optional)
- **Models**: llama3.2:3b, llama3.2:1b, tinyllama
- **Data**: Persisted in Docker volume `ollama_data`

---

## 🔧 Configuration

### Environment Variables

Update `.env` to configure services:

```bash
# Weaviate
WEAVIATE_URL="http://localhost:8080"
WEAVIATE_API_KEY=""  # Optional

# Redis
REDIS_URL="redis://localhost:6379"

# Ollama
OLLAMA_BASE_URL="http://localhost:11434"
OLLAMA_MODEL="llama3.2:3b"
```

### Docker Compose File

Services are defined in `docker-compose.services.yml`:
- Restart policy: `always`
- Health checks: Every 10 seconds
- Persistent volumes for data
- Isolated network

---

## 🎮 Usage Examples

### Example 1: Normal Startup (Auto-Services)

```bash
# Start backend (services auto-start)
python start.py basic

# Output:
# 🚀 Starting external services (Weaviate, Redis, Ollama)...
# ✅ Services started successfully
# 
# Starting DRYAD.AI Backend...
# Server: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

### Example 2: Check Service Status

```bash
services.bat status

# Output:
# 📊 DRYAD.AI Services Status
# ==================================================
# ✅ Docker is running
# 
# ✅ Weaviate Vector Database
#    Container: gremlins-weaviate
#    Port: 8080
#    Status: Healthy
# 
# ✅ Redis Cache
#    Container: gremlins-redis
#    Port: 6379
#    Status: Healthy
# 
# ✅ Ollama LLM Server
#    Container: gremlins-ollama
#    Port: 11434
#    Status: Healthy
```

### Example 3: Setup Ollama Models

```bash
services.bat setup

# Output:
# 📥 Setting up Ollama models...
# 
# 📦 Pulling llama3.2:3b...
#    ✅ llama3.2:3b downloaded
# 
# 📦 Pulling llama3.2:1b...
#    ✅ llama3.2:1b downloaded
# 
# 📦 Pulling tinyllama...
#    ✅ tinyllama downloaded
# 
# ✅ Ollama setup complete
```

### Example 4: View Logs

```bash
# All services
services.bat logs

# Specific service
services.bat logs weaviate

# Follow mode (real-time)
python scripts/manage_services.py logs -f
```

---

## 🔍 Troubleshooting

### Services Won't Start

**Check Docker:**
```bash
docker ps
```

If Docker isn't running:
- Start Docker Desktop
- Wait for it to fully start
- Try again

**Check ports:**
```bash
# Windows
netstat -ano | findstr "8080"
netstat -ano | findstr "6379"
netstat -ano | findstr "11434"

# Linux/Mac
lsof -i :8080
lsof -i :6379
lsof -i :11434
```

If ports are in use, stop conflicting services.

### Services Unhealthy

**View logs:**
```bash
services.bat logs weaviate
```

**Restart services:**
```bash
services.bat restart
```

**Pull latest images:**
```bash
python scripts/manage_services.py pull
```

### Backend Can't Connect

**Check service status:**
```bash
services.bat status
```

**Test connections:**
```bash
# Weaviate
curl http://localhost:8080/v1/.well-known/ready

# Redis
redis-cli ping

# Ollama
curl http://localhost:11434/api/tags
```

---

## 🎯 Integration with Backend

### Automatic Detection

The backend automatically detects and uses services:

```python
# In app/core/config.py
WEAVIATE_URL = "http://localhost:8080"  # Auto-detected
REDIS_URL = "redis://localhost:6379"     # Auto-detected
OLLAMA_BASE_URL = "http://localhost:11434"  # Auto-detected
```

### Graceful Degradation

If services aren't available:
- **Weaviate down** → In-memory search fallback
- **Redis down** → In-memory cache fallback
- **Ollama down** → LlamaCpp used instead

### Health Monitoring

Check service health via API:
```bash
curl http://localhost:8000/api/v1/health/status
```

---

## 📈 Performance

### Resource Usage

**Typical usage:**
- Weaviate: ~500MB RAM
- Redis: ~50MB RAM
- Ollama: ~2GB RAM (with model loaded)

**Total:** ~2.5GB RAM for all services

### Optimization

**Reduce memory:**
```bash
# Edit docker-compose.services.yml
# Adjust memory limits for each service
```

**Faster startup:**
```bash
# Pre-pull images
python scripts/manage_services.py pull
```

---

## 🔐 Security

### Network Isolation

Services run in isolated Docker network:
- Only accessible from localhost
- No external exposure by default

### Data Persistence

All data stored in Docker volumes:
- `weaviate_data` - Vector database
- `redis_data` - Cache data
- `ollama_data` - LLM models

**Backup volumes:**
```bash
docker volume ls
docker run --rm -v weaviate_data:/data -v $(pwd):/backup alpine tar czf /backup/weaviate_backup.tar.gz /data
```

---

## 🎉 Summary

### What You Get

✅ **Auto-start** - Services start automatically
✅ **Always-on** - Services restart if they fail
✅ **Health monitoring** - Automatic health checks
✅ **Easy management** - Simple commands
✅ **Persistent data** - Data survives restarts
✅ **Graceful fallback** - Works without services

### Quick Commands

```bash
# Start everything
python start.py basic

# Check status
services.bat status

# View logs
services.bat logs

# Restart services
services.bat restart

# Setup Ollama
services.bat setup
```

---

**Your services are now always active and ready!** 🚀


