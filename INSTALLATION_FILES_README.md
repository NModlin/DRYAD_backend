# DRYAD.AI Server Installation Files

This directory contains automated installation scripts and documentation for deploying DRYAD.AI Backend to your Arch Linux server at `192.168.6.65`.

## 📁 Files Created

### 🚀 Installation Scripts

1. **`install_dryad_server.sh`** - Main automated installation script
   - Installs all system dependencies (Docker, Redis, etc.)
   - Sets up Ollama with recommended models for RTX 3060
   - Clones DRYAD repository
   - Creates Python virtual environment
   - Installs all Python dependencies
   - Configures Weaviate vector database
   - Creates environment configuration
   - Initializes database

2. **`deploy_to_server.sh`** - Deployment helper script
   - Copies all installation files to the server via SCP
   - Provides next-step instructions

3. **`verify_installation.sh`** - Post-installation verification
   - Checks all services are running
   - Verifies Ollama models are installed
   - Tests HTTP endpoints
   - Validates Python environment
   - Checks GPU availability

### ⚙️ Configuration Files

4. **`dryad.service`** - Systemd service file
   - Runs DRYAD as a system service
   - Auto-starts on boot
   - Manages dependencies (Redis, Docker, Ollama)
   - Handles logging and restarts

### 📚 Documentation

5. **`SERVER_INSTALLATION_GUIDE.md`** - Complete installation guide
   - Automated installation instructions
   - Manual installation steps
   - Service configuration
   - Troubleshooting guide
   - Performance tips for RTX 3060

6. **`QUICK_START_SERVER.md`** - Quick reference guide
   - 3-step quick start
   - Common commands
   - Access points
   - Verification steps
   - Troubleshooting tips

7. **`INSTALLATION_FILES_README.md`** - This file
   - Overview of all installation files
   - Usage instructions

## 🎯 Quick Start

### Option 1: Automated Installation (Recommended)

```bash
# From your local machine:
./deploy_to_server.sh

# Then SSH to server:
ssh katalyst@192.168.6.65

# Run installation:
chmod +x install_dryad_server.sh
./install_dryad_server.sh

# Verify installation:
chmod +x verify_installation.sh
./verify_installation.sh

# Set up as service:
sudo cp dryad.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable dryad
sudo systemctl start dryad
```

### Option 2: Manual Installation

See `SERVER_INSTALLATION_GUIDE.md` for detailed manual installation steps.

## 📋 What Gets Installed

### System Packages
- Docker & Docker Compose
- Redis (in-memory cache)
- Python 3.11+ with pip
- Git and build tools
- Ollama (LLM inference engine)

### AI Models (Optimized for RTX 3060 12GB VRAM)
- **llama3.2:8b** - General purpose (5-6GB VRAM) ⭐ Recommended
- **mistral:7b** - Fast inference (4-5GB VRAM)
- **qwen2.5:14b** - Advanced reasoning (8-10GB VRAM)

### Services
- **DRYAD Backend** - FastAPI application on port 8000
- **Weaviate** - Vector database on port 8080
- **Redis** - Cache/queue on port 6379
- **Ollama** - LLM service on port 11434

## 🌐 Access Points

After installation, DRYAD will be available at:

- **API Documentation:** http://192.168.6.65:8000/docs
- **Health Check:** http://192.168.6.65:8000/health
- **API Base:** http://192.168.6.65:8000/api/v1/

## ✅ Verification

After installation, run the verification script:

```bash
./verify_installation.sh
```

This will check:
- ✓ All services are running
- ✓ Ollama models are installed
- ✓ HTTP endpoints are accessible
- ✓ Python environment is configured
- ✓ GPU is available

## 🔧 Service Management

### Using Systemd (Recommended)

```bash
# Start DRYAD
sudo systemctl start dryad

# Stop DRYAD
sudo systemctl stop dryad

# Restart DRYAD
sudo systemctl restart dryad

# Check status
sudo systemctl status dryad

# View logs
sudo journalctl -u dryad -f
```

### Manual Start

```bash
cd ~/dryad_backend
source .venv/bin/activate
python -m uvicorn dryad.main:app --host 0.0.0.0 --port 8000
```

## 🐛 Troubleshooting

### Check Service Status

```bash
# Redis
sudo systemctl status redis
redis-cli ping

# Ollama
sudo systemctl status ollama
curl http://localhost:11434/api/tags

# Weaviate
docker ps
curl http://localhost:8080/v1/.well-known/ready

# DRYAD
sudo systemctl status dryad
curl http://localhost:8000/health
```

### View Logs

```bash
# DRYAD logs
sudo journalctl -u dryad -n 50

# Ollama logs
sudo journalctl -u ollama -n 50

# Weaviate logs
docker logs <weaviate-container-id>
```

### Restart All Services

```bash
sudo systemctl restart redis
sudo systemctl restart ollama
cd ~/dryad_backend && docker-compose -f docker-compose.weaviate.yml restart
sudo systemctl restart dryad
```

## 📊 Performance Monitoring

### GPU Usage
```bash
# Real-time GPU monitoring
nvidia-smi -l 1

# Or use watch
watch -n 1 nvidia-smi
```

### System Resources
```bash
# CPU and memory
htop

# Disk usage
df -h

# Service resource usage
systemctl status dryad
```

## 🔒 Security Considerations

After installation, consider:

1. **Change default secrets** in `.env` file
2. **Configure firewall** rules
3. **Set up SSL/TLS** with nginx reverse proxy
4. **Restrict CORS** origins in production
5. **Enable authentication** for API endpoints
6. **Regular backups** of database and configuration

## 📖 Additional Documentation

- `README.md` - Project overview
- `/docs` - Full documentation directory
- `pyproject.toml` - Python project configuration

## 🆘 Support

If you encounter issues:

1. Run verification script: `./verify_installation.sh`
2. Check logs: `sudo journalctl -u dryad -f`
3. Review installation guide: `SERVER_INSTALLATION_GUIDE.md`
4. Check GitHub issues: https://github.com/NModlin/DRYAD_backend/issues

## 📝 Notes

- Installation directory: `~/dryad_backend`
- Virtual environment: `~/dryad_backend/.venv`
- Database: `~/dryad_backend/dryad.db`
- Configuration: `~/dryad_backend/.env`
- Logs: `journalctl -u dryad`

---

**Created for:** Arch Linux server at 192.168.6.65  
**Hardware:** Intel i7-9700K, RTX 3060 12GB, 16GB RAM  
**Optimized for:** Local LLM inference with Ollama

