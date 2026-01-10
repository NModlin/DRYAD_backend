#!/bin/bash
# DRYAD.AI Backend - Ubuntu WSL Setup Script
# This script sets up your Ubuntu WSL environment for development

set -e  # Exit on error

echo "🚀 DRYAD.AI Backend - Ubuntu WSL Setup"
echo "========================================"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running in WSL
if ! grep -qi microsoft /proc/version; then
    print_error "This script is designed for WSL (Windows Subsystem for Linux)"
    exit 1
fi

print_success "Running in WSL environment"

# Update package lists
print_status "Updating package lists..."
sudo apt-get update

# Install essential build tools
print_status "Installing essential build tools..."
sudo apt-get install -y \
    build-essential \
    gcc \
    g++ \
    make \
    cmake \
    pkg-config \
    libffi-dev \
    libssl-dev \
    zlib1g-dev \
    libbz2-dev \
    libreadline-dev \
    libsqlite3-dev \
    wget \
    curl \
    llvm \
    libncurses5-dev \
    libncursesw5-dev \
    xz-utils \
    tk-dev \
    libxml2-dev \
    libxmlsec1-dev \
    liblzma-dev

print_success "Build tools installed"

# Install Python 3.11 (required for the project)
print_status "Checking Python installation..."

# Check if Python 3.11 is available
if ! command -v python3.11 &> /dev/null; then
    print_status "Python 3.11 not found. Checking Python 3.12..."

    if command -v python3.12 &> /dev/null; then
        print_warning "Python 3.12 found. The project supports Python 3.11+, so we'll use 3.12."
        PYTHON_CMD="python3.12"

        # Install Python 3.12 venv and dev packages
        print_status "Installing Python 3.12 development packages..."
        sudo apt-get install -y python3.12-venv python3.12-dev
        print_success "Python 3.12 development packages installed"
    else
        # Add deadsnakes PPA for Python 3.11
        print_status "Adding deadsnakes PPA for Python 3.11..."
        sudo apt-get install -y software-properties-common
        sudo add-apt-repository -y ppa:deadsnakes/ppa
        sudo apt-get update

        print_status "Installing Python 3.11..."
        sudo apt-get install -y python3.11 python3.11-venv python3.11-dev
        PYTHON_CMD="python3.11"
        print_success "Python 3.11 installed"
    fi
else
    PYTHON_CMD="python3.11"
    print_success "Python 3.11 already installed"
fi

print_status "Using Python: $PYTHON_CMD ($(${PYTHON_CMD} --version))"

# Install pip for Python
print_status "Installing pip for ${PYTHON_CMD}..."
if ! ${PYTHON_CMD} -m pip --version &> /dev/null; then
    curl -sS https://bootstrap.pypa.io/get-pip.py | sudo ${PYTHON_CMD}
    print_success "pip installed for ${PYTHON_CMD}"
else
    print_success "pip already installed for ${PYTHON_CMD}"
fi

# Install additional Python tools
print_status "Installing Python development tools..."
# Skip system-wide pip installation on Ubuntu 24.04+ (PEP 668)
# We'll install in virtual environment instead
print_success "Python tools will be installed in virtual environment (PEP 668 compliance)"

# Install Docker (if not using Docker Desktop integration)
print_status "Checking Docker installation..."
if ! command -v docker &> /dev/null; then
    print_warning "Docker not found. You have two options:"
    echo "  1. Enable Docker Desktop WSL integration (recommended)"
    echo "  2. Install Docker directly in WSL"
    echo ""
    read -p "Install Docker in WSL? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        print_status "Installing Docker in WSL..."
        
        # Add Docker's official GPG key
        sudo apt-get install -y ca-certificates curl gnupg
        sudo install -m 0755 -d /etc/apt/keyrings
        curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
        sudo chmod a+r /etc/apt/keyrings/docker.gpg
        
        # Add Docker repository
        echo \
          "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
          $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
          sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
        
        # Install Docker
        sudo apt-get update
        sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
        
        # Add user to docker group
        sudo usermod -aG docker $USER
        
        print_success "Docker installed. You may need to log out and back in for group changes to take effect."
    else
        print_warning "Skipping Docker installation. Enable Docker Desktop WSL integration in Docker Desktop settings."
    fi
else
    print_success "Docker already available"
fi

# Install Redis (for local development)
print_status "Installing Redis..."
if ! command -v redis-server &> /dev/null; then
    sudo apt-get install -y redis-server
    print_success "Redis installed"
else
    print_success "Redis already installed"
fi

# Install PostgreSQL client (for database operations)
print_status "Installing PostgreSQL client..."
if ! command -v psql &> /dev/null; then
    sudo apt-get install -y postgresql-client
    print_success "PostgreSQL client installed"
else
    print_success "PostgreSQL client already installed"
fi

# Install ffmpeg (required for audio/video processing)
print_status "Installing ffmpeg..."
if ! command -v ffmpeg &> /dev/null; then
    sudo apt-get install -y ffmpeg
    print_success "ffmpeg installed"
else
    print_success "ffmpeg already installed"
fi

# Install additional dependencies for ML/AI
print_status "Installing ML/AI dependencies..."
sudo apt-get install -y \
    libopenblas-dev \
    liblapack-dev \
    gfortran \
    libhdf5-dev

print_success "ML/AI dependencies installed"

# Install Node.js and npm (useful for some tools)
print_status "Installing Node.js..."
if ! command -v node &> /dev/null; then
    curl -fsSL https://deb.nodesource.com/setup_lts.x | sudo -E bash -
    sudo apt-get install -y nodejs
    print_success "Node.js installed"
else
    print_success "Node.js already installed"
fi

# Install useful development tools
print_status "Installing development tools..."
sudo apt-get install -y \
    vim \
    nano \
    htop \
    tree \
    jq \
    unzip \
    zip

print_success "Development tools installed"

# Set up Git configuration (if not already configured)
print_status "Checking Git configuration..."
if [ -z "$(git config --global user.name)" ]; then
    print_warning "Git user.name not configured"
    read -p "Enter your Git name: " git_name
    git config --global user.name "$git_name"
fi

if [ -z "$(git config --global user.email)" ]; then
    print_warning "Git user.email not configured"
    read -p "Enter your Git email: " git_email
    git config --global user.email "$git_email"
fi

print_success "Git configured: $(git config --global user.name) <$(git config --global user.email)>"

# Create project directory structure
print_status "Setting up project directory..."
PROJECT_DIR="$HOME/projects/DRYAD_backend"

if [ ! -d "$PROJECT_DIR" ]; then
    mkdir -p "$HOME/projects"
    print_status "Cloning repository..."
    cd "$HOME/projects"
    git clone https://github.com/NModlin/DRYAD_backend.git
    cd DRYAD_backend
    print_success "Repository cloned to $PROJECT_DIR"
else
    print_success "Project directory already exists at $PROJECT_DIR"
    cd "$PROJECT_DIR"
fi

# Create Python virtual environment
print_status "Creating Python virtual environment..."
if [ ! -d ".venv" ]; then
    ${PYTHON_CMD} -m venv .venv
    print_success "Virtual environment created with ${PYTHON_CMD}"
else
    print_success "Virtual environment already exists"
fi

# Activate virtual environment and install dependencies
print_status "Installing Python dependencies..."
source .venv/bin/activate
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt

if [ -f "requirements-dev.txt" ]; then
    pip install -r requirements-dev.txt
fi

print_success "Python dependencies installed"

# Create necessary directories
print_status "Creating project directories..."
mkdir -p data logs models uploads

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    print_status "Creating .env file..."
    cat > .env << 'EOF'
# DRYAD.AI Backend Environment Configuration

# Environment
ENVIRONMENT=development

# Database
DATABASE_URL=sqlite:///./data/DRYAD.AI.db

# JWT Secret (generate a secure one for production)
JWT_SECRET_KEY=your-secret-key-here-change-in-production
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# LLM Configuration
LLM_PROVIDER=llamacpp
LLM_MODEL_NAME=tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf
LLM_TEMPERATURE=0.7
LLM_MAX_TOKENS=2048

# Redis (optional)
REDIS_HOST=localhost
REDIS_PORT=6379

# Logging
LOG_LEVEL=INFO

# Feature Flags
ENABLE_MULTI_AGENT=true
ENABLE_GRAPHQL=true
ENABLE_MCP_SERVER=true
EOF
    print_success ".env file created"
else
    print_success ".env file already exists"
fi

# Print summary
echo ""
echo "========================================"
echo -e "${GREEN}✅ Setup Complete!${NC}"
echo "========================================"
echo ""
echo "📋 Summary:"
echo "  • Python: $(${PYTHON_CMD} --version)"
echo "  • pip: $(${PYTHON_CMD} -m pip --version | cut -d' ' -f2)"
echo "  • Git: $(git --version | cut -d' ' -f3)"
echo "  • Docker: $(docker --version 2>/dev/null || echo 'Not configured')"
echo "  • Redis: $(redis-server --version 2>/dev/null | cut -d' ' -f3 || echo 'Not installed')"
echo "  • Node.js: $(node --version 2>/dev/null || echo 'Not installed')"
echo ""
echo "📁 Project Location: $PROJECT_DIR"
echo ""
echo "🚀 Next Steps:"
echo "  1. Activate virtual environment:"
echo "     cd $PROJECT_DIR"
echo "     source .venv/bin/activate"
echo ""
echo "  2. Run database migrations:"
echo "     alembic upgrade head"
echo ""
echo "  3. Start the development server:"
echo "     uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"
echo ""
echo "  4. Run tests:"
echo "     pytest"
echo ""
echo "  5. Access the API:"
echo "     http://localhost:8000"
echo "     http://localhost:8000/docs (Swagger UI)"
echo ""
echo "💡 Tips:"
echo "  • Edit .env file to configure your environment"
echo "  • Use 'wsl -d Ubuntu' to access this environment from Windows"
echo "  • Your Windows files are accessible at /mnt/c/"
echo ""

