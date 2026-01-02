#!/bin/bash
# DRYAD.AI Backend Installation Script for Arch Linux Server
# This script installs DRYAD and all dependencies on a headless Arch server
# Version: 2.0 with improved error handling

# DO NOT use set -e - we handle errors manually for better control

echo "=========================================="
echo "DRYAD.AI Backend Installation Script v2.0"
echo "=========================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Installation directory
INSTALL_DIR="$HOME/dryad_backend"
VENV_DIR="$INSTALL_DIR/.venv"
LOG_FILE="$HOME/dryad_install.log"

# Track installation state
INSTALL_STATE=()

# Logging function
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Error handling function
handle_error() {
    echo -e "${RED}ERROR: $1${NC}" | tee -a "$LOG_FILE"
    echo -e "${YELLOW}Check log file: $LOG_FILE${NC}"
    return 1
}

# Success function
success() {
    echo -e "${GREEN}✓ $1${NC}" | tee -a "$LOG_FILE"
    INSTALL_STATE+=("$1")
}

# Warning function
warn() {
    echo -e "${YELLOW}⚠ $1${NC}" | tee -a "$LOG_FILE"
}

# Info function
info() {
    echo -e "${BLUE}ℹ $1${NC}" | tee -a "$LOG_FILE"
}

# Check if package is installed (Arch Linux)
is_package_installed() {
    pacman -Q "$1" &> /dev/null
}

# Check if service is running
is_service_running() {
    systemctl is-active --quiet "$1"
}

# Check if service exists
service_exists() {
    systemctl list-unit-files | grep -q "^$1.service"
}

log "Starting DRYAD.AI installation"

echo -e "${GREEN}Step 1: Checking system requirements...${NC}"

# Check if running as root
if [ "$EUID" -eq 0 ]; then
   handle_error "Please do not run this script as root"
   exit 1
fi
success "Not running as root"

# Check Python version
if ! command -v python3 &> /dev/null; then
    warn "Python 3 is not installed. Installing..."
    if sudo pacman -S --noconfirm python python-pip; then
        success "Python installed"
    else
        handle_error "Failed to install Python"
        exit 1
    fi
else
    PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
    success "Python $PYTHON_VERSION found"
fi

# Check git
if ! command -v git &> /dev/null; then
    warn "Git not found. Installing..."
    if sudo pacman -S --noconfirm git; then
        success "Git installed"
    else
        handle_error "Failed to install Git"
        exit 1
    fi
else
    success "Git found"
fi

echo ""
echo -e "${GREEN}Step 2: Installing system dependencies...${NC}"

# List of packages to install
PACKAGES=(
    "base-devel"
    "python-pip"
    "python-virtualenv"
    "docker"
    "docker-compose"
    "redis"
    "wget"
    "curl"
)

# Check and install packages
for pkg in "${PACKAGES[@]}"; do
    if is_package_installed "$pkg"; then
        info "$pkg already installed"
    else
        info "Installing $pkg..."
        if sudo pacman -S --noconfirm "$pkg"; then
            success "$pkg installed"
        else
            warn "Failed to install $pkg (may not be critical)"
        fi
    fi
done

echo ""
echo -e "${GREEN}Step 3: Configuring Docker...${NC}"

# Enable Docker
if service_exists "docker"; then
    if ! systemctl is-enabled --quiet docker; then
        sudo systemctl enable docker
        success "Docker enabled"
    else
        info "Docker already enabled"
    fi

    # Start Docker
    if ! is_service_running "docker"; then
        if sudo systemctl start docker; then
            success "Docker started"
        else
            handle_error "Failed to start Docker"
            exit 1
        fi
    else
        success "Docker already running"
    fi

    # Add user to docker group
    if groups $USER | grep -q '\bdocker\b'; then
        info "User already in docker group"
    else
        sudo usermod -aG docker $USER
        warn "Added to docker group - you may need to log out and back in"
    fi
else
    handle_error "Docker service not found"
    exit 1
fi

echo ""
echo -e "${GREEN}Step 4: Configuring Redis...${NC}"

if service_exists "redis"; then
    # Enable Redis
    if ! systemctl is-enabled --quiet redis; then
        sudo systemctl enable redis
        success "Redis enabled"
    else
        info "Redis already enabled"
    fi

    # Start Redis
    if ! is_service_running "redis"; then
        if sudo systemctl start redis; then
            success "Redis started"
        else
            handle_error "Failed to start Redis"
            exit 1
        fi
    else
        success "Redis already running"
    fi
else
    handle_error "Redis service not found"
    exit 1
fi

echo ""
echo -e "${GREEN}Step 5: Installing Ollama...${NC}"

if ! command -v ollama &> /dev/null; then
    info "Ollama not found. Installing..."
    if curl -fsSL https://ollama.com/install.sh | sh; then
        success "Ollama installed"

        # Enable and start Ollama service
        if service_exists "ollama"; then
            sudo systemctl enable ollama
            sudo systemctl start ollama
            info "Waiting for Ollama to start..."
            sleep 5
            success "Ollama service started"
        else
            warn "Ollama service not found (may need manual start)"
        fi
    else
        handle_error "Failed to install Ollama"
        exit 1
    fi
else
    success "Ollama already installed"

    # Check if service is running
    if service_exists "ollama"; then
        if ! is_service_running "ollama"; then
            info "Starting Ollama service..."
            sudo systemctl start ollama
            sleep 3
        fi
        success "Ollama service running"
    fi
fi

# Verify Ollama is accessible
if curl -s http://localhost:11434/api/tags &> /dev/null; then
    success "Ollama API is accessible"
else
    warn "Ollama API not accessible yet (may need a moment to start)"
fi

echo ""
echo -e "${GREEN}Step 6: Pulling recommended Ollama models...${NC}"
info "This may take a while depending on your internet connection..."

# Function to pull model with error handling
pull_model() {
    local model=$1
    info "Checking model: $model"

    # Check if model already exists
    if ollama list | grep -q "^$model"; then
        success "Model $model already installed"
        return 0
    fi

    info "Pulling model: $model (this may take several minutes)..."
    if ollama pull "$model"; then
        success "Model $model downloaded"
        return 0
    else
        warn "Failed to pull model $model (you can pull it later)"
        return 1
    fi
}

# Pull recommended models for RTX 3060 (12GB VRAM)
pull_model "llama3.2:8b"
pull_model "mistral:7b"
pull_model "qwen2.5:14b"

echo ""
echo -e "${GREEN}Step 7: Setting up DRYAD repository...${NC}"

if [ -d "$INSTALL_DIR" ]; then
    warn "Directory $INSTALL_DIR already exists"
    cd "$INSTALL_DIR" || exit 1

    # Check if it's a git repository
    if [ -d ".git" ]; then
        info "Updating existing repository..."

        # Stash any local changes
        if ! git diff-index --quiet HEAD --; then
            warn "Local changes detected, stashing..."
            git stash
        fi

        # Pull latest changes
        if git pull; then
            success "Repository updated"
        else
            warn "Failed to update repository (continuing with existing version)"
        fi
    else
        warn "Directory exists but is not a git repository"
        info "Using existing directory"
    fi
else
    info "Cloning DRYAD repository..."
    if git clone https://github.com/NModlin/DRYAD_backend.git "$INSTALL_DIR"; then
        success "Repository cloned"
        cd "$INSTALL_DIR" || exit 1
    else
        handle_error "Failed to clone repository"
        exit 1
    fi
fi

# Checkout refactor branch
info "Switching to refactor branch..."
if git checkout refactor; then
    success "On refactor branch"
else
    warn "Failed to checkout refactor branch (using current branch)"
fi

echo ""
echo -e "${GREEN}Step 8: Setting up Python virtual environment...${NC}"

if [ -d "$VENV_DIR" ]; then
    info "Virtual environment already exists"
    success "Using existing virtual environment"
else
    info "Creating virtual environment..."
    if python3 -m venv "$VENV_DIR"; then
        success "Virtual environment created"
    else
        handle_error "Failed to create virtual environment"
        exit 1
    fi
fi

# Activate virtual environment
if source "$VENV_DIR/bin/activate"; then
    success "Virtual environment activated"
else
    handle_error "Failed to activate virtual environment"
    exit 1
fi

echo ""
echo -e "${GREEN}Step 9: Upgrading pip and installing build tools...${NC}"

if pip install --upgrade pip setuptools wheel; then
    success "Build tools updated"
else
    warn "Failed to upgrade build tools (continuing anyway)"
fi

echo ""
echo -e "${GREEN}Step 10: Installing Python dependencies...${NC}"

# Install from pyproject.toml
info "Installing DRYAD package..."
if pip install -e .; then
    success "DRYAD package installed"
else
    handle_error "Failed to install DRYAD package"
    exit 1
fi

# Install optional dependencies if needed
if [ -f "archive/legacy_v9/requirements.txt" ]; then
    info "Installing additional legacy dependencies..."
    if pip install -r archive/legacy_v9/requirements.txt; then
        success "Legacy dependencies installed"
    else
        warn "Some legacy dependencies failed to install (may not be critical)"
    fi
fi

echo ""
echo -e "${GREEN}Step 11: Setting up Weaviate with Docker...${NC}"

# Check if Weaviate container already exists
if docker ps -a --format '{{.Names}}' | grep -q "weaviate"; then
    warn "Weaviate container already exists"

    # Check if it's running
    if docker ps --format '{{.Names}}' | grep -q "weaviate"; then
        success "Weaviate already running"
    else
        info "Starting existing Weaviate container..."
        if docker start weaviate; then
            success "Weaviate started"
        else
            warn "Failed to start existing container, will recreate"
            docker rm -f weaviate 2>/dev/null || true
        fi
    fi
else
    info "Creating Weaviate docker-compose configuration..."

    # Create docker-compose file for Weaviate
    cat > docker-compose.weaviate.yml <<'EOF'
version: '3.8'
services:
  weaviate:
    container_name: weaviate
    image: semitechnologies/weaviate:latest
    ports:
      - "8080:8080"
    environment:
      QUERY_DEFAULTS_LIMIT: 25
      AUTHENTICATION_ANONYMOUS_ACCESS_ENABLED: 'true'
      PERSISTENCE_DATA_PATH: '/var/lib/weaviate'
      DEFAULT_VECTORIZER_MODULE: 'none'
      ENABLE_MODULES: ''
      CLUSTER_HOSTNAME: 'node1'
    volumes:
      - weaviate_data:/var/lib/weaviate
    restart: unless-stopped

volumes:
  weaviate_data:
EOF

    success "Docker-compose file created"

    # Start Weaviate
    info "Starting Weaviate container..."
    if docker-compose -f docker-compose.weaviate.yml up -d; then
        success "Weaviate started"
        sleep 3
    else
        warn "Failed to start Weaviate (you can start it manually later)"
    fi
fi

# Verify Weaviate is accessible
info "Waiting for Weaviate to be ready..."
for i in {1..30}; do
    if curl -s http://localhost:8080/v1/.well-known/ready &> /dev/null; then
        success "Weaviate is ready"
        break
    fi
    if [ $i -eq 30 ]; then
        warn "Weaviate not responding (may need more time to start)"
    fi
    sleep 1
done

echo ""
echo -e "${GREEN}Step 12: Setting up Open WebUI...${NC}"

# Check if Open WebUI container already exists
if docker ps -a --format '{{.Names}}' | grep -q "open-webui"; then
    warn "Open WebUI container already exists"

    # Check if it's running
    if docker ps --format '{{.Names}}' | grep -q "open-webui"; then
        success "Open WebUI already running"
    else
        info "Starting existing Open WebUI container..."
        if docker start open-webui; then
            success "Open WebUI started"
        else
            warn "Failed to start existing container, will recreate"
            docker rm -f open-webui 2>/dev/null || true
        fi
    fi
else
    info "Creating Open WebUI docker-compose configuration..."

    # Create docker-compose file for Open WebUI
    cat > docker-compose.openwebui.yml <<'EOF'
version: '3.8'
services:
  open-webui:
    container_name: open-webui
    image: ghcr.io/open-webui/open-webui:main
    ports:
      - "3000:8080"
    environment:
      - OLLAMA_BASE_URL=http://host.docker.internal:11434
      - WEBUI_SECRET_KEY=${WEBUI_SECRET_KEY:-$(openssl rand -hex 32)}
      - ENABLE_SIGNUP=true
      - DEFAULT_USER_ROLE=user
    volumes:
      - open_webui_data:/app/backend/data
    extra_hosts:
      - "host.docker.internal:host-gateway"
    restart: unless-stopped

volumes:
  open_webui_data:
EOF

    success "Docker-compose file created"

    # Start Open WebUI
    info "Starting Open WebUI container..."
    if docker-compose -f docker-compose.openwebui.yml up -d; then
        success "Open WebUI started"
        sleep 3
    else
        warn "Failed to start Open WebUI (you can start it manually later)"
    fi
fi

# Verify Open WebUI is accessible
info "Waiting for Open WebUI to be ready..."
for i in {1..30}; do
    if curl -s http://localhost:3000 &> /dev/null; then
        success "Open WebUI is ready"
        break
    fi
    if [ $i -eq 30 ]; then
        warn "Open WebUI not responding (may need more time to start)"
    fi
    sleep 1
done

echo ""
echo -e "${GREEN}Step 13: Creating environment configuration...${NC}"

if [ -f ".env" ]; then
    warn ".env file already exists"

    # Backup existing .env
    BACKUP_FILE=".env.backup.$(date +%s)"
    cp .env "$BACKUP_FILE"
    info "Backed up existing .env to $BACKUP_FILE"

    read -p "Overwrite existing .env? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        info "Keeping existing .env file"
    else
        info "Creating new .env file..."
        CREATE_ENV=true
    fi
else
    CREATE_ENV=true
fi

if [ "$CREATE_ENV" = true ]; then
    cat > .env <<EOF
# DRYAD.AI Backend Configuration

# Server Configuration
HOST=0.0.0.0
PORT=8000
ENVIRONMENT=production

# Database
DATABASE_URL=sqlite:///./dryad.db

# External Services
WEAVIATE_URL=http://localhost:8080
REDIS_URL=redis://localhost:6379
OLLAMA_BASE_URL=http://localhost:11434

# Default Model
DEFAULT_MODEL=llama3.2:8b

# Security (CHANGE THESE IN PRODUCTION!)
SECRET_KEY=$(openssl rand -hex 32)
JWT_SECRET_KEY=$(openssl rand -hex 32)
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# CORS
ALLOWED_ORIGINS=*

# Logging
LOG_LEVEL=INFO
EOF
    success "Environment configuration created"
fi

echo ""
echo -e "${GREEN}Step 14: Initializing database...${NC}"

# Create data directory
if [ ! -d "data" ]; then
    mkdir -p data
    success "Data directory created"
else
    info "Data directory already exists"
fi

# Database will be initialized on first run
info "Database will be initialized on first server start"

echo ""
echo -e "${GREEN}=========================================="
echo "Installation Complete!"
echo "==========================================${NC}"
echo ""

# Summary of what was installed
log "Installation completed successfully"
echo -e "${BLUE}Installation Summary:${NC}"
echo ""

# Show installed components
echo "Installed components:"
for item in "${INSTALL_STATE[@]}"; do
    echo -e "  ${GREEN}✓${NC} $item"
done

echo ""
echo -e "${YELLOW}Next Steps:${NC}"
echo ""
echo "1. Start DRYAD manually:"
echo "   cd $INSTALL_DIR"
echo "   source .venv/bin/activate"
echo "   python -m uvicorn dryad.main:app --host 0.0.0.0 --port 8000"
echo ""
echo "2. Or set up as systemd service (recommended):"
echo "   sudo cp ~/dryad.service /etc/systemd/system/"
echo "   sudo systemctl daemon-reload"
echo "   sudo systemctl enable dryad"
echo "   sudo systemctl start dryad"
echo ""
echo "3. Verify installation:"
echo "   ./verify_installation.sh"
echo ""

echo -e "${BLUE}Service Status:${NC}"
echo "  - Redis: $(is_service_running redis && echo -e "${GREEN}Running${NC}" || echo -e "${RED}Not running${NC}")"
echo "  - Ollama: $(is_service_running ollama && echo -e "${GREEN}Running${NC}" || echo -e "${RED}Not running${NC}")"
echo "  - Docker: $(is_service_running docker && echo -e "${GREEN}Running${NC}" || echo -e "${RED}Not running${NC}")"
echo "  - Weaviate: $(docker ps | grep -q weaviate && echo -e "${GREEN}Running${NC}" || echo -e "${RED}Not running${NC}")"
echo "  - Open WebUI: $(docker ps | grep -q open-webui && echo -e "${GREEN}Running${NC}" || echo -e "${RED}Not running${NC}")"
echo ""

echo -e "${BLUE}Access Points:${NC}"
echo "  - DRYAD API Docs: http://192.168.6.65:8000/docs"
echo "  - DRYAD Health: http://192.168.6.65:8000/health"
echo "  - Open WebUI (Chat Interface): http://192.168.6.65:3000"
echo "  - Ollama API: http://localhost:11434"
echo "  - Weaviate: http://localhost:8080"
echo ""

echo -e "${BLUE}Installed Ollama Models:${NC}"
ollama list 2>/dev/null || echo "  Run 'ollama list' to see installed models"
echo ""

echo -e "${YELLOW}Important Notes:${NC}"
echo "  - Log file saved to: $LOG_FILE"
echo "  - If you were added to docker group, log out and back in for it to take effect"
echo "  - Review and update .env file for production use"
echo "  - Change SECRET_KEY and JWT_SECRET_KEY in .env for security"
echo ""
echo -e "${BLUE}Open WebUI Quick Start:${NC}"
echo "  1. Open http://192.168.6.65:3000 in your browser"
echo "  2. Create an account (first user becomes admin)"
echo "  3. Start chatting with your Ollama models!"
echo "  4. Models available: llama3.2:8b, mistral:7b, qwen2.5:14b"
echo ""

echo -e "${GREEN}Installation script completed!${NC}"
echo ""

