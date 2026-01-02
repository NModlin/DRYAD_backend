# Install DRYAD.AI on a Remote Server

## 🚀 Quick Start (Recommended)

### Option 1: One-Line Installation

SSH into your remote server and run:

```bash
curl -fsSL https://raw.githubusercontent.com/NModlin/DRYAD_backend/main/quick_install.sh | bash
```

This will:
- Download the installer
- Make scripts executable
- Prompt you to run the installation

---

### Option 2: Manual Git Clone

```bash
# 1. SSH into your server
ssh user@your-server-ip

# 2. Clone the repository
git clone https://github.com/NModlin/DRYAD_backend.git
cd DRYAD_backend

# 3. Run the installer
./install_dryad_enhanced.sh
```

---

### Option 3: Download Without Git

```bash
# 1. SSH into your server
ssh user@your-server-ip

# 2. Download the repository
wget https://github.com/NModlin/DRYAD_backend/archive/refs/heads/main.zip
unzip main.zip
cd DRYAD_backend-main

# 3. Make scripts executable
chmod +x install_dryad_enhanced.sh lib/*.sh

# 4. Run the installer
./install_dryad_enhanced.sh
```

---

## 📋 Prerequisites

Your remote server needs:

- **Docker** (20.10+)
- **Docker Compose** (2.0+)
- **Node.js** (18+) - Only if installing frontend applications
- **Bash** (4.0+)
- **2GB+ RAM** (more for advanced configurations)
- **10GB+ Disk Space**

### Install Prerequisites

```bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER
# Log out and back in for group changes to take effect

# Install Node.js (if you want frontends)
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs

# Install git (if using git clone method)
sudo apt install git -y
```

---

## 🌐 Accessing Your Installation

After installation, you have several options to access DRYAD.AI:

### Option 1: SSH Port Forwarding (Easiest)

From your **local machine**:

```bash
ssh -L 8000:localhost:8000 \
    -L 3001:localhost:3001 \
    -L 3006:localhost:3006 \
    user@your-server-ip
```

Then open in your browser:
- Backend API: http://localhost:8000
- Dryads Console: http://localhost:3001
- University UI: http://localhost:3006

### Option 2: Configure Firewall for Direct Access

On your **remote server**:

```bash
# Allow access to DRYAD ports
sudo ufw allow 8000/tcp   # Backend API
sudo ufw allow 3001/tcp   # Dryads Console
sudo ufw allow 3006/tcp   # University UI
sudo ufw allow 3000/tcp   # Writer Portal or Grafana
```

Then access directly:
- http://your-server-ip:8000
- http://your-server-ip:3001
- http://your-server-ip:3006

### Option 3: Use Production Deployment

During installation, select **"Production"** deployment configuration which includes:
- Nginx reverse proxy
- SSL/TLS support
- Proper domain configuration
- Access via standard ports (80/443)

---

## 🔧 Installation Tips

### Use screen or tmux

Prevent disconnection issues during installation:

```bash
# Start a screen session
screen -S dryad-install

# Run the installer
./install_dryad_enhanced.sh

# If disconnected, reconnect with:
screen -r dryad-install
```

### Check Resources First

```bash
# Check available RAM
free -h

# Check disk space
df -h

# Check Docker is running
docker info
```

### Test Before Installing

```bash
./test_installer.sh
```

---

## 📝 During Installation

The installer will ask you to:

1. **Select Deployment Configuration**
   - For remote servers, recommend: **Basic**, **Full**, or **Production**

2. **Select Frontend Applications** (optional)
   - Choose based on your needs

3. **Select Optional Components** (optional)
   - Monitoring recommended for production servers

4. **Configure LLM Provider**
   - Mock, OpenAI, Anthropic, or Ollama

5. **Configure Domain**
   - Enter your server's IP address or domain name
   - Example: `192.168.1.100` or `dryad.yourdomain.com`

---

## 🆘 Troubleshooting

### Permission Denied

```bash
chmod +x install_dryad_enhanced.sh lib/*.sh
```

### Docker Not Running

```bash
sudo systemctl start docker
sudo systemctl enable docker
```

### Port Already in Use

```bash
# Find what's using port 8000
sudo lsof -i :8000

# Stop the conflicting service or choose different ports
```

### Installation Logs

```bash
# View installation log
cat ~/dryad_install_*.log

# View service logs
docker compose logs dryad-backend
```

---

## 📚 Next Steps

After installation:

1. **Test the API**
   ```bash
   curl http://localhost:8000/api/v1/health/status
   ```

2. **View API Documentation**
   - http://your-server-ip:8000/docs

3. **Check Installation Summary**
   ```bash
   cat INSTALLATION_SUMMARY.txt
   ```

4. **Review Logs**
   ```bash
   docker compose logs -f
   ```

---

## 🔗 Additional Resources

- **Detailed Remote Guide:** `REMOTE_INSTALLATION_GUIDE.md`
- **User Guide:** `ENHANCED_INSTALLER_GUIDE.md`
- **Quick Reference:** `QUICK_REFERENCE.md`
- **Technical Docs:** `README_INSTALLER.md`

---

## 🎯 Complete Example

Here's a complete workflow from start to finish:

```bash
# 1. SSH into your server
ssh user@your-server-ip

# 2. Install prerequisites (if needed)
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker $USER
# Log out and back in

# 3. Download and install DRYAD.AI
git clone https://github.com/NModlin/DRYAD_backend.git
cd DRYAD_backend
./install_dryad_enhanced.sh

# 4. Follow the prompts and wait for installation

# 5. Configure firewall (if needed)
sudo ufw allow 8000/tcp

# 6. Test the installation
curl http://localhost:8000/api/v1/health/status

# 7. Access from your local machine
# Exit SSH and run:
ssh -L 8000:localhost:8000 user@your-server-ip
# Then open http://localhost:8000 in your browser
```

---

**Need help?** Check the troubleshooting section or review the installation logs.

