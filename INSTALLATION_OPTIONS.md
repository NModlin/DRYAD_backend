# DRYAD.AI Installation Options

Choose the installation method that best fits your needs.

---

## 🌟 Option 1: Enhanced Interactive Installer (RECOMMENDED)

**Best for:** Most users, especially those who want full control over components

### Features
- ✅ Interactive menu-driven installation
- ✅ 7 deployment configurations (minimal to GPU)
- ✅ 3 optional frontend applications
- ✅ 6 optional backend/monitoring components
- ✅ Automatic resource checking
- ✅ Port conflict detection
- ✅ Comprehensive health checks

### Local Installation
```bash
./install_dryad_enhanced.sh
```

### Remote Installation (SSH)
```bash
# One-line install
curl -fsSL https://raw.githubusercontent.com/NModlin/DRYAD_backend/main/quick_install.sh | bash

# Or manual
git clone https://github.com/NModlin/DRYAD_backend.git
cd DRYAD_backend
./install_dryad_enhanced.sh
```

### Documentation
- **User Guide:** [ENHANCED_INSTALLER_GUIDE.md](ENHANCED_INSTALLER_GUIDE.md)
- **Remote Guide:** [INSTALL_ON_REMOTE_SERVER.md](INSTALL_ON_REMOTE_SERVER.md)
- **Quick Reference:** [QUICK_REFERENCE.md](QUICK_REFERENCE.md)
- **Technical Docs:** [README_INSTALLER.md](README_INSTALLER.md)

---

## 🚀 Option 2: Unified Installation (Simple)

**Best for:** Quick setup, development, testing

### Features
- ✅ Automatic capability detection
- ✅ GPU acceleration when available
- ✅ Graceful fallbacks
- ✅ Single command installation

### Installation
```bash
# Clone and setup
git clone https://github.com/NModlin/DRYAD_backend.git
cd DRYAD_backend

# Install dependencies
pip install -r requirements.txt

# Start the system
python start.py basic
```

### Documentation
- **Complete Guide:** [DRYAD.AI_COMPLETE_GUIDE.md](DRYAD.AI_COMPLETE_GUIDE.md)
- **Quick Start:** [QUICK_START.md](QUICK_START.md)

---

## 🐳 Option 3: Docker Compose

**Best for:** Containerized deployments, production environments

### Features
- ✅ Isolated containers
- ✅ Easy scaling
- ✅ Multiple configurations available
- ✅ Production-ready

### Installation
```bash
# Clone repository
git clone https://github.com/NModlin/DRYAD_backend.git
cd DRYAD_backend

# Choose a configuration
docker compose -f archive/legacy_v9/docker/docker-compose.basic.yml up -d

# Or use production config
docker compose -f archive/legacy_v9/docker-compose.production.yml up -d
```

### Available Configurations
- `docker-compose.minimal.yml` - Core API only (1-2GB RAM)
- `docker-compose.basic.yml` - Standard features (2-4GB RAM)
- `docker-compose.development.yml` - Hot reload + debugging (4-6GB RAM)
- `docker-compose.full.yml` - All services + Celery (6-8GB RAM)
- `docker-compose.production.yml` - Nginx + SSL + monitoring (8-10GB RAM)
- `docker-compose.scalable.yml` - Multi-worker + load balancing (10-12GB RAM)
- `docker-compose.gpu.yml` - GPU-accelerated ML (12GB+ RAM)

### Documentation
- **Docker Guide:** [docs/deployment/docker.md](docs/deployment/docker.md)

---

## 📦 Option 4: Manual Installation

**Best for:** Custom setups, advanced users

### Prerequisites
- Python 3.11+
- Docker (for Weaviate, Redis)
- Node.js 18+ (for frontends)

### Installation
```bash
# 1. Clone repository
git clone https://github.com/NModlin/DRYAD_backend.git
cd DRYAD_backend

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
cp .env.example .env
# Edit .env with your settings

# 5. Start external services
docker compose up -d weaviate redis

# 6. Run migrations (if needed)
alembic upgrade head

# 7. Start the backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 8. (Optional) Install and start frontends
cd archive/legacy_v9/clients/dryads-console
npm install
npm run dev
```

### Documentation
- **Getting Started:** [docs/getting-started/](docs/getting-started/)
- **Architecture:** [docs/architecture/](docs/architecture/)

---

## 🎯 Comparison Table

| Feature | Enhanced Installer | Unified Install | Docker Compose | Manual |
|---------|-------------------|-----------------|----------------|--------|
| **Ease of Use** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐ |
| **Customization** | ⭐⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **Remote Install** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ |
| **Production Ready** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| **Health Checks** | ⭐⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐ | ⭐ |
| **Monitoring** | ⭐⭐⭐⭐⭐ | ⭐ | ⭐⭐⭐⭐ | ⭐⭐ |
| **Time to Install** | 10-15 min | 5 min | 5-10 min | 15-30 min |

---

## 🤔 Which Should I Choose?

### Choose Enhanced Installer if:
- ✅ You want an interactive, guided installation
- ✅ You're installing on a remote server via SSH
- ✅ You want to select specific components
- ✅ You want automatic health checks and validation
- ✅ You're new to DRYAD.AI

### Choose Unified Install if:
- ✅ You want the quickest setup
- ✅ You're doing local development
- ✅ You don't need frontends or monitoring
- ✅ You want automatic capability detection

### Choose Docker Compose if:
- ✅ You prefer containerized deployments
- ✅ You're deploying to production
- ✅ You need easy scaling
- ✅ You want isolated services

### Choose Manual Install if:
- ✅ You need complete control
- ✅ You have custom requirements
- ✅ You're integrating with existing infrastructure
- ✅ You're an advanced user

---

## 📚 Additional Resources

- **Main README:** [README.md](README.md)
- **Documentation Index:** [docs/README.md](docs/README.md)
- **API Reference:** [docs/api_reference.md](docs/api_reference.md)
- **Deployment Guides:** [docs/deployment/](docs/deployment/)

---

## 🆘 Need Help?

- **Installation Issues:** Check the troubleshooting section in each guide
- **Remote Installation:** See [INSTALL_ON_REMOTE_SERVER.md](INSTALL_ON_REMOTE_SERVER.md)
- **Quick Reference:** See [QUICK_REFERENCE.md](QUICK_REFERENCE.md)
- **Logs:** Check installation logs for detailed error information

---

**Recommended:** Start with the **Enhanced Interactive Installer** for the best experience!

