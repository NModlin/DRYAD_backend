# DRYAD.AI Enhanced Installer - Quick Reference Card

## Installation

### Local Installation
```bash
./install_dryad_enhanced.sh
```

### Remote Installation (SSH)

**Method 1: One-Line Install (Easiest)**
```bash
# On remote server
curl -fsSL https://raw.githubusercontent.com/NModlin/DRYAD_backend/main/quick_install.sh | bash
```

**Method 2: Git Clone**
```bash
# SSH into server
ssh user@your-server-ip

# Clone and install
git clone https://github.com/NModlin/DRYAD_backend.git
cd DRYAD_backend
./install_dryad_enhanced.sh
```

**Method 3: Download ZIP**
```bash
# SSH into server
ssh user@your-server-ip

# Download and extract
wget https://github.com/NModlin/DRYAD_backend/archive/refs/heads/main.zip
unzip main.zip
cd DRYAD_backend-main
chmod +x install_dryad_enhanced.sh lib/*.sh
./install_dryad_enhanced.sh
```

See `REMOTE_INSTALLATION_GUIDE.md` for detailed remote installation instructions.

## Deployment Configurations

| Config       | RAM    | Use Case                    |
|-------------|--------|------------------------------|
| Minimal     | 1-2GB  | Testing, development         |
| Basic       | 2-4GB  | Small projects               |
| Development | 4-6GB  | Active development           |
| Full        | 6-8GB  | Production with workers      |
| Production  | 8-10GB | Public deployment            |
| Scalable    | 10-12GB| High traffic                 |
| GPU         | 12GB+  | ML workloads                 |

## Frontend Applications

| Application      | Port | Description                    |
|-----------------|------|--------------------------------|
| Dryads Console  | 3001 | Knowledge tree navigator       |
| University UI   | 3006 | Student/Faculty dashboards     |
| Writer Portal   | 3000 | Document management            |

## Optional Components

**Backend:**
- MCP Server - Model Context Protocol
- PostgreSQL - Production database
- Celery Workers - Background tasks

**Monitoring:**
- Prometheus + Grafana - Metrics
- ELK Stack - Logging
- Full Metrics Suite - All exporters

## LLM Providers

| Provider   | API Key Required | Notes                    |
|-----------|------------------|--------------------------|
| Mock      | No               | Testing only             |
| OpenAI    | Yes              | GPT models               |
| Anthropic | Yes              | Claude models            |
| Ollama    | No               | Local LLM (auto-download)|

## Access Points

After installation:

- **Backend API:** http://localhost:8000
- **API Docs:** http://localhost:8000/docs
- **Health Check:** http://localhost:8000/api/v1/health/status
- **Dryads Console:** http://localhost:3001 (if installed)
- **University UI:** http://localhost:3006 (if installed)
- **Writer Portal:** http://localhost:3000 (if installed)
- **Prometheus:** http://localhost:9090 (if monitoring enabled)
- **Grafana:** http://localhost:3000 (if monitoring enabled)
- **Kibana:** http://localhost:5601 (if logging enabled)

## Management Commands

### View Logs
```bash
docker compose logs -f dryad-backend
```

### Stop Services
```bash
docker compose down
```

### Restart Services
```bash
docker compose restart
```

### Check Status
```bash
docker compose ps
```

### Stop Frontend
```bash
kill $(cat logs/dryads-console.pid)  # Dryads Console
kill $(cat logs/university-ui.pid)   # University UI
kill $(cat logs/writer-portal.pid)   # Writer Portal
```

## Troubleshooting

### Installation Logs
```bash
cat ~/dryad_install_*.log
```

### Service Logs
```bash
docker compose logs [service-name]
```

### Frontend Logs
```bash
cat logs/dryads-console.log
cat logs/university-ui.log
cat logs/writer-portal.log
```

### Common Issues

**Docker Not Running:**
```bash
# Check Docker status
docker info

# Start Docker Desktop (macOS/Windows)
# Or start Docker service (Linux)
sudo systemctl start docker
```

**Port Conflicts:**
```bash
# Find what's using a port
lsof -i :8000
netstat -tuln | grep 8000

# Stop the conflicting service or choose different ports
```

**Backend Not Starting:**
```bash
# Check logs
docker compose logs dryad-backend

# Verify .env file
cat .env

# Check available memory
free -h
```

**Frontend Build Failures:**
```bash
# Check Node.js version (requires 18+)
node --version

# Try manual installation
cd archive/legacy_v9/clients/[frontend-name]
npm install --legacy-peer-deps
npm run dev
```

## Uninstallation

```bash
# Stop all services
docker compose down

# Remove volumes (WARNING: Deletes all data!)
docker compose down -v

# Stop frontends
kill $(cat logs/*.pid) 2>/dev/null || true

# Remove installation files (optional)
rm -rf data logs monitoring .env
```

## Testing

Test the installer without installing:
```bash
./test_installer.sh
```

## Files

- **Installation Summary:** `INSTALLATION_SUMMARY.txt`
- **Backend Config:** `.env`
- **Frontend Configs:** `archive/legacy_v9/clients/*/. env`
- **Installation Log:** `~/dryad_install_*.log`

## Support

- **User Guide:** `ENHANCED_INSTALLER_GUIDE.md`
- **Technical Docs:** `README_INSTALLER.md`
- **Implementation Summary:** `INSTALLATION_SYSTEM_SUMMARY.md`

---

**Quick Start:** `./install_dryad_enhanced.sh` → Follow prompts → Access at http://localhost:8000

