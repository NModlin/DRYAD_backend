# DRYAD.AI - Quick Start for Server Installation

## 🚀 Super Quick Installation (3 Steps)

### From Your Local Machine:

```bash
# 1. Copy files to server
./deploy_to_server.sh

# 2. SSH into server
ssh katalyst@192.168.6.65

# 3. Run installation (on server)
chmod +x install_dryad_server.sh
./install_dryad_server.sh
```

That's it! The script handles everything automatically.

---

## 📋 What Gets Installed

### System Packages
- Docker & Docker Compose
- Redis
- Python 3.11+ with pip
- Git and build tools

### AI Services
- **Ollama** - Local LLM inference engine
- **Open WebUI** - Beautiful chat interface for Ollama
- **Weaviate** - Vector database (via Docker)
- **Redis** - Caching and task queue

### Ollama Models (Optimized for RTX 3060 12GB)
- `llama3.2:8b` - General purpose (5-6GB VRAM) ⭐ Recommended
- `mistral:7b` - Fast inference (4-5GB VRAM)
- `qwen2.5:14b` - Advanced reasoning (8-10GB VRAM)

### DRYAD Backend
- Full Python backend with FastAPI
- Multi-agent AI system
- Vector search capabilities
- GraphQL API
- Authentication system

---

## 🎯 After Installation

### Start DRYAD Manually
```bash
cd ~/dryad_backend
source .venv/bin/activate
python -m uvicorn dryad.main:app --host 0.0.0.0 --port 8000
```

### Or Set Up as System Service (Recommended)
```bash
sudo cp ~/dryad.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable dryad
sudo systemctl start dryad
```

### Manage Service
```bash
# Check status
sudo systemctl status dryad

# View logs
sudo journalctl -u dryad -f

# Restart
sudo systemctl restart dryad

# Stop
sudo systemctl stop dryad
```

---

## 🌐 Access Points

Once running, access DRYAD at:

- **API Docs (Swagger):** http://192.168.6.65:8000/docs
- **Health Check:** http://192.168.6.65:8000/health
- **API Base:** http://192.168.6.65:8000/api/v1/

### Service Endpoints
- **Ollama:** http://192.168.6.65:11434
- **Weaviate:** http://192.168.6.65:8080
- **Redis:** localhost:6379

---

## ✅ Verify Installation

```bash
# Check all services
redis-cli ping                                    # Should return: PONG
curl http://localhost:11434/api/tags              # Lists Ollama models
curl http://localhost:8080/v1/.well-known/ready   # Weaviate health
curl http://localhost:8000/health                 # DRYAD health

# Test Ollama model
ollama run llama3.2:8b "Hello, how are you?"

# Monitor GPU usage
nvidia-smi -l 1
```

---

## 🔧 Common Commands

### Ollama
```bash
ollama list                           # List installed models
ollama pull <model>                   # Download a model
ollama run <model> "prompt"           # Test a model
ollama rm <model>                     # Remove a model
```

### Docker (Weaviate)
```bash
cd ~/dryad_backend
docker-compose -f docker-compose.weaviate.yml ps      # Check status
docker-compose -f docker-compose.weaviate.yml logs    # View logs
docker-compose -f docker-compose.weaviate.yml restart # Restart
```

### DRYAD
```bash
# View logs (if using systemd)
sudo journalctl -u dryad -f

# Or if running manually
cd ~/dryad_backend
source .venv/bin/activate
python -m uvicorn dryad.main:app --host 0.0.0.0 --port 8000 --reload
```

---

## 🎮 Access Your Services

### Web Interfaces

Open in your browser:

- **Open WebUI (Chat):** http://192.168.6.65:3000
  - Beautiful chat interface for Ollama models
  - First user becomes admin
  - See `OPEN_WEBUI_GUIDE.md` for details

- **DRYAD API Docs:** http://192.168.6.65:8000/docs
  - Interactive API documentation
  - Test endpoints directly in browser

### Using curl
```bash
# Health check
curl http://192.168.6.65:8000/health

# Check Open WebUI
curl http://192.168.6.65:3000

# List Ollama models
curl http://192.168.6.65:11434/api/tags
```

### Using Python
```python
import requests

# Health check
response = requests.get("http://192.168.6.65:8000/health")
print(response.json())

# API documentation
print("API Docs: http://192.168.6.65:8000/docs")
print("Chat UI: http://192.168.6.65:3000")
```

---

## 🐛 Troubleshooting

### Service won't start
```bash
# Check what's using port 8000
sudo netstat -tulpn | grep 8000

# Check logs
sudo journalctl -u dryad -n 50 --no-pager

# Restart all services
sudo systemctl restart redis
sudo systemctl restart ollama
cd ~/dryad_backend && docker-compose -f docker-compose.weaviate.yml restart
sudo systemctl restart dryad
```

### Ollama issues
```bash
# Check Ollama service
sudo systemctl status ollama

# Restart Ollama
sudo systemctl restart ollama

# Test Ollama
curl http://localhost:11434/api/tags
```

### Out of VRAM
```bash
# Check GPU usage
nvidia-smi

# Use smaller model
ollama pull llama3.2:3b  # Only ~2GB VRAM
```

---

## 📊 Performance Tips

### For RTX 3060 (12GB VRAM)

1. **Best Models:**
   - Daily use: `llama3.2:8b` or `mistral:7b`
   - Complex tasks: `qwen2.5:14b`
   - Multiple users: `mistral:7b` (leaves room for concurrent requests)

2. **Monitor Resources:**
   ```bash
   # GPU usage
   watch -n 1 nvidia-smi
   
   # System resources
   htop
   ```

3. **Optimize Performance:**
   - Use quantized models (Q4/Q5)
   - Limit concurrent requests
   - Keep models loaded in VRAM (faster inference)

---

## 📚 Next Steps

1. ✅ Review API documentation at http://192.168.6.65:8000/docs
2. ✅ Configure authentication (edit `.env` file)
3. ✅ Set up SSL/TLS with nginx (for production)
4. ✅ Configure firewall rules
5. ✅ Set up automated backups
6. ✅ Review security settings

---

## 📖 Full Documentation

For detailed information, see:
- `SERVER_INSTALLATION_GUIDE.md` - Complete installation guide
- `README.md` - Project overview
- `/docs` - Full documentation

---

## 🆘 Need Help?

- Check logs: `sudo journalctl -u dryad -f`
- Review installation guide: `cat SERVER_INSTALLATION_GUIDE.md`
- GitHub Issues: https://github.com/NModlin/DRYAD_backend/issues

