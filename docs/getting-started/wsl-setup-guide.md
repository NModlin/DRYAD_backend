# Ubuntu WSL Setup Guide for DRYAD.AI Backend

## Quick Start

### 1. Run the Setup Script

From Windows PowerShell or CMD:

```bash
# Copy the setup script to WSL
wsl -d Ubuntu -- bash -c "cd ~ && cat > setup.sh" < setup-ubuntu-wsl.sh

# Make it executable and run it
wsl -d Ubuntu -- bash -c "chmod +x ~/setup.sh && ~/setup.sh"
```

Or from within WSL Ubuntu:

```bash
# Navigate to the project directory
cd /mnt/c/Users/nmodlin.RPL/OneDrive\ -\ Rehrig\ Pacific\ Company/Documents/GitHub/DRYAD_backend/

# Run the setup script
bash setup-ubuntu-wsl.sh
```

### 2. Access Your WSL Ubuntu Environment

```bash
# From Windows, open Ubuntu WSL
wsl -d Ubuntu

# Or set Ubuntu as default
wsl --set-default Ubuntu
wsl
```

## What the Setup Script Does

### System Packages
- ✅ Updates package lists
- ✅ Installs build tools (gcc, g++, make, cmake)
- ✅ Installs Python 3.11 and development headers
- ✅ Installs Redis server
- ✅ Installs PostgreSQL client
- ✅ Installs ffmpeg (for audio/video processing)
- ✅ Installs ML/AI dependencies (OpenBLAS, LAPACK)
- ✅ Installs Node.js (latest LTS)
- ✅ Installs development tools (vim, htop, tree, jq)

### Docker Setup
- ✅ Optionally installs Docker in WSL
- ✅ Or guides you to enable Docker Desktop WSL integration

### Project Setup
- ✅ Clones the DRYAD_backend repository
- ✅ Creates Python 3.11 virtual environment
- ✅ Installs all Python dependencies
- ✅ Creates necessary directories (data, logs, models, uploads)
- ✅ Creates .env configuration file

## Manual Setup (Alternative)

If you prefer to set up manually:

### 1. Install Python 3.11

```bash
sudo apt-get update
sudo apt-get install -y python3.11 python3.11-venv python3.11-dev
```

### 2. Install Build Dependencies

```bash
sudo apt-get install -y \
    build-essential \
    gcc \
    g++ \
    make \
    cmake \
    libffi-dev \
    libssl-dev \
    libopenblas-dev \
    liblapack-dev \
    ffmpeg
```

### 3. Clone Repository

```bash
mkdir -p ~/projects
cd ~/projects
git clone https://github.com/NModlin/DRYAD_backend.git
cd DRYAD_backend
```

### 4. Create Virtual Environment

```bash
python3.11 -m venv .venv
source .venv/bin/activate
```

### 5. Install Dependencies

```bash
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

### 6. Configure Environment

```bash
cp .env.example .env  # If exists
# Or create .env manually
nano .env
```

### 7. Run Migrations

```bash
alembic upgrade head
```

### 8. Start Development Server

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Docker Desktop WSL Integration

### Enable Docker Desktop Integration

1. Open Docker Desktop
2. Go to **Settings** → **Resources** → **WSL Integration**
3. Enable integration with **Ubuntu** distribution
4. Click **Apply & Restart**

### Verify Docker Access

```bash
wsl -d Ubuntu -- docker --version
wsl -d Ubuntu -- docker ps
```

## Common Commands

### WSL Management

```bash
# List WSL distributions
wsl --list --verbose

# Set default distribution
wsl --set-default Ubuntu

# Shutdown WSL
wsl --shutdown

# Restart specific distribution
wsl --terminate Ubuntu
wsl -d Ubuntu

# Access Ubuntu from Windows
wsl -d Ubuntu

# Run command in Ubuntu from Windows
wsl -d Ubuntu -- <command>
```

### Project Commands

```bash
# Activate virtual environment
source .venv/bin/activate

# Run development server
uvicorn app.main:app --reload

# Run tests
pytest

# Run tests with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_auth.py

# Run linting
flake8 app tests
black app tests --check

# Format code
black app tests

# Run type checking
mypy app

# Database migrations
alembic revision --autogenerate -m "description"
alembic upgrade head
alembic downgrade -1

# Start Redis (if installed locally)
sudo service redis-server start

# Check Redis status
redis-cli ping
```

### Docker Commands

```bash
# Build production image
docker build -f Dockerfile.prod -t DRYAD.AI-backend:latest .

# Build worker image
docker build -f Dockerfile.worker -t DRYAD.AI-worker:latest .

# Run with Docker Compose
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down

# Rebuild and restart
docker-compose up -d --build
```

## File System Access

### Access Windows Files from WSL

```bash
# Windows C: drive
cd /mnt/c/

# Your project directory
cd /mnt/c/Users/nmodlin.RPL/OneDrive\ -\ Rehrig\ Pacific\ Company/Documents/GitHub/DRYAD_backend/
```

### Access WSL Files from Windows

```
\\wsl$\Ubuntu\home\<username>\projects\DRYAD_backend
```

Or in File Explorer:
```
\\wsl.localhost\Ubuntu\home\<username>\projects\DRYAD_backend
```

## Troubleshooting

### Python Version Issues

```bash
# Check Python version
python3.11 --version

# If python3.11 not found, install it
sudo apt-get install -y python3.11 python3.11-venv python3.11-dev
```

### Permission Issues

```bash
# Fix ownership of project files
sudo chown -R $USER:$USER ~/projects/DRYAD_backend

# Fix Docker permission (if installed in WSL)
sudo usermod -aG docker $USER
# Then log out and back in
```

### Redis Connection Issues

```bash
# Start Redis
sudo service redis-server start

# Check Redis status
sudo service redis-server status

# Test connection
redis-cli ping
```

### Docker Issues

```bash
# If using Docker Desktop, ensure WSL integration is enabled
# Settings → Resources → WSL Integration → Enable Ubuntu

# If Docker installed in WSL, start the service
sudo service docker start

# Check Docker status
sudo service docker status
```

### Build Failures

```bash
# Install missing build dependencies
sudo apt-get install -y build-essential python3.11-dev

# For PyTorch/ML packages
sudo apt-get install -y libopenblas-dev liblapack-dev

# For audio processing
sudo apt-get install -y ffmpeg
```

## Performance Tips

### 1. Store Project in WSL File System

For better performance, clone the repository in WSL's native file system:

```bash
# Better performance
~/projects/DRYAD_backend

# Slower (accessing Windows file system)
/mnt/c/Users/.../DRYAD_backend
```

### 2. Configure Git for WSL

```bash
# Disable Git credential helper for WSL
git config --global credential.helper ""

# Or use WSL-specific credential helper
git config --global credential.helper "/mnt/c/Program\ Files/Git/mingw64/bin/git-credential-manager.exe"
```

### 3. Increase WSL Memory

Create or edit `C:\Users\<username>\.wslconfig`:

```ini
[wsl2]
memory=8GB
processors=4
swap=2GB
```

Then restart WSL:
```bash
wsl --shutdown
```

## Next Steps

1. ✅ Run the setup script
2. ✅ Activate virtual environment
3. ✅ Run database migrations
4. ✅ Start development server
5. ✅ Run tests to verify setup
6. ✅ Configure Docker Desktop integration (if using)
7. ✅ Set up your IDE to use WSL Python interpreter

## IDE Integration

### VS Code

1. Install **Remote - WSL** extension
2. Open project in WSL:
   ```bash
   code ~/projects/DRYAD_backend
   ```
3. Select Python interpreter: `.venv/bin/python`

### PyCharm

1. Go to **Settings** → **Project** → **Python Interpreter**
2. Click **Add Interpreter** → **WSL**
3. Select Ubuntu distribution
4. Choose virtual environment: `~/projects/DRYAD_backend/.venv/bin/python`

## Resources

- [WSL Documentation](https://docs.microsoft.com/en-us/windows/wsl/)
- [Docker Desktop WSL 2 Backend](https://docs.docker.com/desktop/windows/wsl/)
- [VS Code Remote - WSL](https://code.visualstudio.com/docs/remote/wsl)

