# 🚀 Start Here - DRYAD.AI Installation

## ⚠️ Important: Use the Enhanced Installer

If you just tried `install_dryad_server.sh` and got a Redis error, **that's the old installer**.

Use the **new enhanced installer** instead:

```bash
./install_dryad_enhanced.sh
```

---

## Why the Enhanced Installer?

The old `install_dryad_server.sh` tries to install Redis on your system, which:
- ❌ Conflicts with Arch Linux's Valkey package
- ❌ Requires system-level configuration
- ❌ Can cause permission issues

The new `install_dryad_enhanced.sh`:
- ✅ Uses Docker for ALL services (including Redis)
- ✅ No system-level dependencies needed
- ✅ Interactive menu-driven installation
- ✅ Automatic health checks
- ✅ Better error handling
- ✅ Works perfectly on remote servers

---

## Quick Start

### Step 1: Run the Enhanced Installer

```bash
./install_dryad_enhanced.sh
```

### Step 2: Follow the Interactive Prompts

The installer will guide you through:

1. **Deployment Configuration** - Choose based on your needs:
   - Minimal (1-2GB RAM) - Testing
   - Basic (2-4GB RAM) - Small projects ← **Recommended for remote servers**
   - Development (4-6GB RAM) - Active development
   - Full (6-8GB RAM) - Production with workers
   - Production (8-10GB RAM) - Public deployment
   - Scalable (10-12GB RAM) - High traffic
   - GPU (12GB+ RAM) - ML workloads

2. **Frontend Applications** (Optional)
   - Dryads Console (Port 3001)
   - University UI (Port 3006)
   - Writer Portal (Port 3000)

3. **Optional Components**
   - MCP Server
   - PostgreSQL Database
   - Celery Workers
   - Prometheus + Grafana
   - ELK Stack
   - Full Metrics Suite

4. **LLM Provider**
   - Mock (testing)
   - OpenAI (requires API key)
   - Anthropic (requires API key)
   - Ollama (local LLM)

5. **Domain Configuration**
   - Enter your server's IP or domain name
   - Example: `192.168.1.100` or `madhatter.local`

### Step 3: Wait for Installation

The installer will:
- ✅ Check prerequisites
- ✅ Create necessary directories
- ✅ Generate configuration files
- ✅ Pull and start Docker containers
- ✅ Run health checks
- ✅ Display access URLs

---

## After Installation

### Access Your Installation

**From the same machine:**
```bash
curl http://localhost:8000/api/v1/health/status
```

**From your local machine (SSH port forwarding):**
```bash
# On your local machine
ssh -L 8000:localhost:8000 -L 3001:localhost:3001 katalyst@madhatter

# Then open in browser:
# http://localhost:8000 - Backend API
# http://localhost:8000/docs - API Documentation
# http://localhost:3001 - Dryads Console (if installed)
```

**Direct access (configure firewall first):**
```bash
# On the remote server
sudo ufw allow 8000/tcp
sudo ufw allow 3001/tcp
sudo ufw allow 3006/tcp

# Then access from anywhere:
# http://madhatter:8000
# http://madhatter:3001
```

---

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

---

## Troubleshooting

### If Installation Fails

1. **Check the log file:**
   ```bash
   cat ~/dryad_install_*.log
   ```

2. **Verify Docker is running:**
   ```bash
   docker info
   ```

3. **Check available resources:**
   ```bash
   free -h  # Check RAM
   df -h    # Check disk space
   ```

4. **Test the installer components:**
   ```bash
   ./test_installer.sh
   ```

### Common Issues

**Port Already in Use:**
```bash
# Find what's using the port
sudo lsof -i :8000

# Stop the conflicting service
```

**Docker Permission Denied:**
```bash
# Add user to docker group
sudo usermod -aG docker $USER

# Log out and back in for changes to take effect
```

---

## Documentation

- **User Guide:** [ENHANCED_INSTALLER_GUIDE.md](ENHANCED_INSTALLER_GUIDE.md)
- **Remote Installation:** [INSTALL_ON_REMOTE_SERVER.md](INSTALL_ON_REMOTE_SERVER.md)
- **Quick Reference:** [QUICK_REFERENCE.md](QUICK_REFERENCE.md)
- **All Options:** [INSTALLATION_OPTIONS.md](INSTALLATION_OPTIONS.md)

---

## Summary

**Old installer (DON'T USE):**
```bash
./install_dryad_server.sh  # ❌ Causes Redis errors
```

**New installer (USE THIS):**
```bash
./install_dryad_enhanced.sh  # ✅ Works perfectly
```

---

**Ready? Run:** `./install_dryad_enhanced.sh`

