#!/bin/bash
# DRYAD.AI Enhanced Installation - Utility Functions
# Common utilities used across all installation modules

# Mark as loaded
export DRYAD_UTILS_LOADED=1

# Colors for output
export RED='\033[0;31m'
export GREEN='\033[0;32m'
export YELLOW='\033[1;33m'
export BLUE='\033[0;34m'
export PURPLE='\033[0;35m'
export CYAN='\033[0;36m'
export NC='\033[0m' # No Color

# Global variables
export LOG_FILE="${LOG_FILE:-$HOME/dryad_install.log}"
export INSTALL_STATE=()

# Only set SCRIPT_DIR and PROJECT_ROOT if not already set
if [[ -z "$SCRIPT_DIR" ]]; then
    export SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
fi
if [[ -z "$PROJECT_ROOT" ]]; then
    export PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
fi

# Logging function
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Print functions
print_header() {
    echo ""
    echo -e "${PURPLE}========================================${NC}"
    echo -e "${PURPLE}$1${NC}"
    echo -e "${PURPLE}========================================${NC}"
    echo ""
}

print_step() {
    echo -e "${BLUE}[STEP]${NC} $1" | tee -a "$LOG_FILE"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1" | tee -a "$LOG_FILE"
    INSTALL_STATE+=("$1")
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1" | tee -a "$LOG_FILE"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1" | tee -a "$LOG_FILE"
}

print_info() {
    echo -e "${CYAN}[INFO]${NC} $1" | tee -a "$LOG_FILE"
}

# Error handling
handle_error() {
    print_error "$1"
    echo -e "${YELLOW}Check log file: $LOG_FILE${NC}"
    return 1
}

# Generate secure random string
generate_secret() {
    if command -v python3 &> /dev/null; then
        python3 -c "import secrets; print(secrets.token_urlsafe(48))"
    elif command -v openssl &> /dev/null; then
        openssl rand -base64 48
    else
        # Fallback to /dev/urandom
        cat /dev/urandom | tr -dc 'a-zA-Z0-9' | fold -w 48 | head -n 1
    fi
}

# Wait for service to be ready
wait_for_service() {
    local url=$1
    local max_wait=${2:-60}
    local wait_time=0
    local interval=5
    
    print_info "Waiting for service at $url..."
    
    while [[ $wait_time -lt $max_wait ]]; do
        if curl -f -s "$url" &> /dev/null; then
            print_success "Service is ready!"
            return 0
        fi
        
        echo -n "."
        sleep $interval
        wait_time=$((wait_time + interval))
    done
    
    echo ""
    print_error "Service did not become ready within ${max_wait}s"
    return 1
}

# Check if port is in use
is_port_in_use() {
    local port=$1
    if command -v lsof &> /dev/null; then
        lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1
    elif command -v netstat &> /dev/null; then
        netstat -tuln | grep -q ":$port "
    elif command -v ss &> /dev/null; then
        ss -tuln | grep -q ":$port "
    else
        # Fallback: try to connect
        timeout 1 bash -c "cat < /dev/null > /dev/tcp/127.0.0.1/$port" 2>/dev/null
    fi
}

# Check if command exists
command_exists() {
    command -v "$1" &> /dev/null
}

# Check if Docker is running
is_docker_running() {
    docker info &> /dev/null
}

# Check if service is running (Docker)
is_service_running() {
    local service_name=$1
    docker compose ps "$service_name" 2>/dev/null | grep -q "Up"
}

# Check if Redis is running and accessible
is_redis_running() {
    # Check if redis-cli is available and can connect
    if command_exists redis-cli; then
        if redis-cli ping &>/dev/null; then
            return 0
        fi
    fi

    # Check if Redis is running in Docker
    if command_exists docker; then
        if docker ps --format '{{.Names}}' 2>/dev/null | grep -q "redis"; then
            return 0
        fi
    fi

    # Check via network connection
    if timeout 1 bash -c "cat < /dev/null > /dev/tcp/127.0.0.1/6379" 2>/dev/null; then
        return 0
    fi

    return 1
}

# Check if Ollama is running and accessible
is_ollama_running() {
    # Check if ollama command is available
    if command_exists ollama; then
        if ollama list &>/dev/null; then
            return 0
        fi
    fi

    # Check via HTTP API
    if command_exists curl; then
        if curl -s --max-time 2 http://localhost:11434/api/tags &>/dev/null; then
            return 0
        fi
    fi

    # Check if Ollama is running as a service
    if command_exists systemctl; then
        if systemctl is-active --quiet ollama 2>/dev/null; then
            return 0
        fi
    fi

    return 1
}

# Get the name of the service running on a port
get_service_on_port() {
    local port=$1

    if command_exists lsof; then
        local pid=$(lsof -ti:$port 2>/dev/null | head -1)
        if [[ -n "$pid" ]]; then
            ps -p $pid -o comm= 2>/dev/null
        fi
    elif command_exists netstat; then
        netstat -tulpn 2>/dev/null | grep ":$port " | awk '{print $7}' | cut -d'/' -f2
    fi
}

# Get available memory in MB
get_available_memory() {
    if [[ -f /proc/meminfo ]]; then
        awk '/MemAvailable/ {printf "%.0f", $2/1024}' /proc/meminfo
    elif command -v free &> /dev/null; then
        free -m | awk 'NR==2{printf "%.0f", $7}'
    else
        echo "unknown"
    fi
}

# Get available disk space in GB
get_available_disk() {
    df -BG . | awk 'NR==2{print $4}' | sed 's/G//'
}

# Confirm action with user
confirm() {
    local prompt="${1:-Are you sure?}"
    local default="${2:-n}"
    
    if [[ "$default" == "y" ]]; then
        read -p "$prompt (Y/n): " response
        response=${response:-y}
    else
        read -p "$prompt (y/N): " response
        response=${response:-n}
    fi
    
    [[ "$response" =~ ^[Yy]$ ]]
}

# Display a menu and get user selection
display_menu() {
    local title=$1
    shift
    local options=("$@")
    
    echo ""
    echo -e "${CYAN}$title${NC}"
    echo ""
    
    for i in "${!options[@]}"; do
        echo "  $((i+1))) ${options[$i]}"
    done
    echo ""
}

