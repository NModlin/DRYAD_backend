# Requirements Files

This directory contains various Python requirements files for different installation profiles and environments.

## 📁 Files

### **Main Requirements**
- **Main requirements.txt** is located in the root directory for standard installation

### **Installation Profiles**
- **requirements-minimal.txt** - Minimal dependencies for basic functionality
- **requirements-standard.txt** - Standard installation with common features
- **requirements-full.txt** - Complete installation with all optional dependencies
- **requirements-dev.txt** - Development dependencies (testing, linting, etc.)

### **Generated Variants (RPC-prefixed)**
- **requirements-*-RPC-12345678901.txt** - Auto-generated variants with specific version locks
- These files contain pinned versions for reproducible builds

## 🚀 Installation

### Standard Installation
```bash
# Use main requirements (from root directory)
pip install -r requirements.txt
```

### Profile-Based Installation
```bash
# Minimal installation (basic API functionality)
pip install -r requirements/requirements-minimal.txt

# Standard installation (includes vector search, multi-agent)
pip install -r requirements/requirements-standard.txt

# Full installation (includes multimodal processing)
pip install -r requirements/requirements-full.txt

# Development installation (includes testing tools)
pip install -r requirements/requirements-dev.txt
```

### Combined Installation
```bash
# Standard + development tools
pip install -r requirements/requirements-standard.txt -r requirements/requirements-dev.txt
```

## 📋 Profile Comparison

| Feature | Minimal | Standard | Full | Dev |
|---------|---------|----------|------|-----|
| **FastAPI Core** | ✅ | ✅ | ✅ | ✅ |
| **Local LLM (LlamaCpp)** | ✅ | ✅ | ✅ | ✅ |
| **Built-in Multi-Agent** | ✅ | ✅ | ✅ | ✅ |
| **SQLite Database** | ✅ | ✅ | ✅ | ✅ |
| **OAuth2 Authentication** | ✅ | ✅ | ✅ | ✅ |
| **Vector Search (Weaviate)** | ❌ | ✅ | ✅ | ✅ |
| **Task Queue (Celery/Redis)** | ❌ | ✅ | ✅ | ✅ |
| **GraphQL API** | ❌ | ✅ | ✅ | ✅ |
| **Multimodal Processing** | ❌ | ❌ | ✅ | ✅ |
| **Testing Framework** | ❌ | ❌ | ❌ | ✅ |
| **Code Quality Tools** | ❌ | ❌ | ❌ | ✅ |

## 🔧 Dependency Management

### Version Pinning Strategy
- **Main requirements.txt**: Flexible version ranges for compatibility
- **Profile requirements**: Specific versions tested to work together
- **RPC variants**: Exact version pins for reproducible builds

### Updating Dependencies
```bash
# Generate new pinned versions
pip-compile requirements/requirements-standard.txt --output-file requirements/requirements-standard-RPC-$(date +%s).txt

# Update existing requirements
pip-compile --upgrade requirements/requirements-standard.txt
```

### Conflict Resolution
If you encounter dependency conflicts:
1. Try the RPC-prefixed variant files (pre-tested combinations)
2. Use virtual environments to isolate installations
3. Check the main requirements.txt for compatible version ranges

## 📊 Installation Size Estimates

| Profile | Download Size | Disk Space | Key Dependencies |
|---------|---------------|------------|------------------|
| **Minimal** | ~200MB | ~800MB | FastAPI, LlamaCpp, SQLAlchemy |
| **Standard** | ~500MB | ~2GB | + Weaviate client, Celery, Redis |
| **Full** | ~2GB | ~8GB | + PyTorch, Transformers, Whisper |
| **Dev** | ~2.5GB | ~10GB | + pytest, black, mypy, coverage |

## 🧹 Maintenance

When updating requirements:
1. Test all installation profiles for compatibility
2. Update version numbers in this README if significant changes
3. Generate new RPC variants for stable releases
4. Document any new dependencies or breaking changes
