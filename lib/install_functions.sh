#!/bin/bash
# DRYAD.AI Enhanced Installation - Installation Functions
# Functions for installing each component

# Source utilities if not already sourced
if [[ -z "$DRYAD_UTILS_LOADED" ]]; then
    source "$(dirname "${BASH_SOURCE[0]}")/utils.sh"
fi

# Check prerequisites
check_prerequisites() {
    print_step "Checking prerequisites..."
    
    local all_ok=true
    
    # Check Docker
    if ! command_exists docker; then
        print_error "Docker is not installed"
        echo "Visit: https://docs.docker.com/get-docker/"
        all_ok=false
    else
        print_success "Docker found: $(docker --version | cut -d' ' -f3 | tr -d ',')"
    fi
    
    # Check Docker Compose
    if ! docker compose version &> /dev/null && ! command_exists docker-compose; then
        print_error "Docker Compose is not installed"
        echo "Visit: https://docs.docker.com/compose/install/"
        all_ok=false
    else
        print_success "Docker Compose found"
    fi
    
    # Check Docker is running
    if ! is_docker_running; then
        print_error "Docker is not running. Please start Docker and try again."
        all_ok=false
    else
        print_success "Docker is running"
    fi
    
    # Check Node.js (for frontends)
    if [[ ${#SELECTED_FRONTENDS[@]} -gt 0 ]]; then
        if ! command_exists node; then
            print_warning "Node.js not found. Frontend installation will fail."
            print_info "Install Node.js from: https://nodejs.org/"
            all_ok=false
        else
            print_success "Node.js found: $(node --version)"
        fi
        
        if ! command_exists npm; then
            print_warning "npm not found. Frontend installation will fail."
            all_ok=false
        else
            print_success "npm found: $(npm --version)"
        fi
    fi
    
    # Check system resources
    local mem_available=$(get_available_memory)
    if [[ "$mem_available" != "unknown" ]]; then
        if [[ $mem_available -lt 2048 ]]; then
            print_warning "Available memory is ${mem_available}MB. Recommended: 4GB+"
            print_warning "Consider using minimal deployment configuration"
        else
            print_success "Available memory: ${mem_available}MB"
        fi
    fi
    
    # Check disk space
    local disk_available=$(get_available_disk)
    if [[ -n "$disk_available" && $disk_available -lt 10 ]]; then
        print_warning "Available disk space is ${disk_available}GB. Recommended: 20GB+"
    else
        print_success "Available disk space: ${disk_available}GB"
    fi
    
    if ! $all_ok; then
        print_error "Prerequisites check failed"
        return 1
    fi
    
    print_success "All prerequisites met"
    return 0
}

# Create necessary directories
create_directories() {
    print_step "Creating necessary directories..."

    mkdir -p data logs monitoring/grafana monitoring/prometheus
    chmod 755 data logs monitoring

    print_success "Directories created"
}

# Install backend services
install_backend() {
    print_step "Installing DRYAD Backend..."

    # Determine which docker-compose files to use
    local compose_files=""

    case $DEPLOYMENT_CONFIG in
        "minimal")
            compose_files="-f archive/legacy_v9/docker/docker-compose.minimal.yml"
            ;;
        "basic")
            compose_files="-f archive/legacy_v9/docker/docker-compose.basic.yml"
            ;;
        "development")
            compose_files="-f archive/legacy_v9/docker/docker-compose.development.yml"
            ;;
        "full")
            compose_files="-f archive/legacy_v9/docker/docker-compose.full.yml"
            ;;
        "production")
            compose_files="-f archive/legacy_v9/docker-compose.production.yml"
            ;;
        "scalable")
            compose_files="-f archive/legacy_v9/docker/docker-compose.scalable.yml"
            ;;
        "gpu")
            compose_files="-f archive/legacy_v9/docker/docker-compose.gpu.yml"
            ;;
    esac

    # Add monitoring if selected
    if [[ " ${OPTIONAL_COMPONENTS[@]} " =~ " monitoring " ]]; then
        compose_files="$compose_files -f archive/legacy_v9/docker-compose.monitoring.yml"
    fi

    # Add logging if selected
    if [[ " ${OPTIONAL_COMPONENTS[@]} " =~ " logging " ]]; then
        compose_files="$compose_files -f archive/legacy_v9/docker/docker-compose.logging.yml"
    fi

    # Create override file for external services
    if [[ "$USE_EXTERNAL_REDIS" == "true" ]] || [[ "$USE_EXTERNAL_OLLAMA" == "true" ]]; then
        print_info "Creating docker-compose override for external services..."

        # Create the override file
        cat > docker-compose.override.yml << 'EOF'
services:
EOF

        # If using external Redis, disable it in Docker
        if [[ "$USE_EXTERNAL_REDIS" == "true" ]]; then
            cat >> docker-compose.override.yml << 'EOF'
  redis:
    deploy:
      replicas: 0
    profiles:
      - disabled
EOF
        fi

        # If using external Ollama, disable it in Docker
        if [[ "$USE_EXTERNAL_OLLAMA" == "true" ]]; then
            cat >> docker-compose.override.yml << 'EOF'
  ollama:
    deploy:
      replicas: 0
    profiles:
      - disabled
EOF
        fi

        print_success "Created docker-compose.override.yml for external services"
        compose_files="$compose_files -f docker-compose.override.yml"
    fi

    print_info "Using docker-compose files: $compose_files"

    # Pull images
    print_info "Pulling Docker images (this may take a while)..."
    if ! docker compose --env-file .env $compose_files pull; then
        print_warning "Some images failed to pull, continuing anyway..."
    fi

    # Start services
    print_info "Starting services..."
    if ! docker compose --env-file .env $compose_files up -d; then
        print_error "Failed to start services"
        return 1
    fi
    
    # Wait for backend to be ready
    print_info "Waiting for backend API to be ready..."
    if wait_for_service "http://localhost:8000/api/v1/health/status" 120; then
        print_success "Backend API is ready"
    else
        print_error "Backend API failed to start"
        print_info "Check logs with: docker compose logs dryad-backend"
        return 1
    fi
    
    print_success "Backend installation complete"
    return 0
}

# Install a frontend application
install_frontend() {
    local frontend_name=$1
    local frontend_dir=""
    local frontend_port=""

    case $frontend_name in
        "dryads-console")
            frontend_dir="archive/legacy_v9/clients/dryads-console"
            frontend_port=3001
            ;;
        "university-ui")
            frontend_dir="archive/legacy_v9/clients/dryad-university-ui"
            frontend_port=3006
            ;;
        "writer-portal")
            frontend_dir="archive/legacy_v9/clients/frontend/writer-portal"
            frontend_port=3000
            ;;
        *)
            print_error "Unknown frontend: $frontend_name"
            return 1
            ;;
    esac

    print_step "Installing $frontend_name..."

    # Check if directory exists
    if [[ ! -d "$frontend_dir" ]]; then
        print_error "Frontend directory not found: $frontend_dir"
        return 1
    fi

    # Navigate to directory
    cd "$frontend_dir" || return 1

    # Check for package.json
    if [[ ! -f "package.json" ]]; then
        print_error "package.json not found in $frontend_dir"
        cd - > /dev/null
        return 1
    fi

    # Install dependencies
    print_info "Installing npm dependencies for $frontend_name..."
    if ! npm install --legacy-peer-deps 2>&1 | tee -a "$LOG_FILE"; then
        print_error "npm install failed for $frontend_name"
        cd - > /dev/null
        return 1
    fi

    # Create .env file
    print_info "Configuring environment for $frontend_name..."
    cat > .env << EOF
# Frontend Configuration for $frontend_name
# Generated by install_dryad_enhanced.sh on $(date)

VITE_API_BASE_URL=http://localhost:8000/api/v1
VITE_BACKEND_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000/ws

# Feature Flags
VITE_ENABLE_MCP=$(if [[ " ${OPTIONAL_COMPONENTS[@]} " =~ " mcp " ]]; then echo "true"; else echo "false"; fi)
VITE_ENABLE_MONITORING=$(if [[ " ${OPTIONAL_COMPONENTS[@]} " =~ " monitoring " ]]; then echo "true"; else echo "false"; fi)
EOF

    # Start development server in background
    print_info "Starting $frontend_name on port $frontend_port..."

    # Create a simple systemd-style service or use nohup
    nohup npm run dev > "$PROJECT_ROOT/logs/${frontend_name}.log" 2>&1 &
    local pid=$!
    echo $pid > "$PROJECT_ROOT/logs/${frontend_name}.pid"

    # Wait a bit and check if it's still running
    sleep 5
    if kill -0 $pid 2>/dev/null; then
        print_success "$frontend_name started (PID: $pid, Port: $frontend_port)"
    else
        print_error "$frontend_name failed to start"
        print_info "Check logs: $PROJECT_ROOT/logs/${frontend_name}.log"
        cd - > /dev/null
        return 1
    fi

    # Return to original directory
    cd - > /dev/null

    print_success "$frontend_name installation complete"
    return 0
}

# Install all selected frontends
install_frontends() {
    if [[ ${#SELECTED_FRONTENDS[@]} -eq 0 ]]; then
        print_info "No frontends selected, skipping..."
        return 0
    fi

    print_step "Installing frontend applications..."

    for frontend in "${SELECTED_FRONTENDS[@]}"; do
        if ! install_frontend "$frontend"; then
            print_warning "Failed to install $frontend, continuing..."
        fi
    done

    print_success "Frontend installation complete"
}

# Enable MCP Server
enable_mcp_server() {
    print_step "Enabling MCP Server..."

    # Update .env file
    if grep -q "ENABLE_MCP_SERVER" .env 2>/dev/null; then
        sed -i 's/ENABLE_MCP_SERVER=.*/ENABLE_MCP_SERVER=true/' .env
    else
        echo "ENABLE_MCP_SERVER=true" >> .env
    fi

    # Add MCP endpoint configuration
    if ! grep -q "MCP_ENDPOINT_PATH" .env 2>/dev/null; then
        cat >> .env << EOF

# MCP Server Configuration
MCP_SERVER_HOST=0.0.0.0
MCP_SERVER_PORT=8000
MCP_ENDPOINT_PATH=/mcp
EOF
    fi

    # Restart backend to apply changes
    print_info "Restarting backend to enable MCP..."
    docker compose restart dryad-backend 2>/dev/null || docker-compose restart dryad-backend 2>/dev/null

    # Wait for service to be ready
    if wait_for_service "http://localhost:8000/mcp" 30; then
        print_success "MCP Server enabled at http://localhost:8000/mcp"
    else
        print_warning "MCP Server may not be available yet"
        print_info "Check backend logs: docker compose logs dryad-backend"
    fi

    return 0
}

# Setup Ollama if selected
setup_ollama() {
    if [[ "$LLM_PROVIDER" != "ollama" ]]; then
        return 0
    fi

    # Skip if using external Ollama
    if [[ "$USE_EXTERNAL_OLLAMA" == "true" ]]; then
        print_success "Using existing Ollama installation"
        print_info "Checking if llama3.2:3b model is available..."

        if ollama list 2>/dev/null | grep -q "llama3.2:3b"; then
            print_success "Model llama3.2:3b is already available"
        else
            print_warning "Model llama3.2:3b not found"
            if confirm "Would you like to download it now?" "y"; then
                print_info "Downloading model (this may take several minutes)..."
                if ollama pull llama3.2:3b; then
                    print_success "Model downloaded successfully"
                else
                    print_warning "Failed to download model. You can download it later with: ollama pull llama3.2:3b"
                fi
            fi
        fi
        return 0
    fi

    print_step "Setting up Ollama local LLM..."

    # Check if Ollama is running
    if ! docker compose ps ollama 2>/dev/null | grep -q "Up"; then
        print_info "Starting Ollama..."
        docker compose up -d ollama
        sleep 10
    fi

    # Pull recommended model
    print_info "Downloading recommended model (llama3.2:3b)..."
    print_warning "This may take several minutes depending on your internet connection..."

    if docker exec dryad-ollama ollama pull llama3.2:3b 2>&1 | tee -a "$LOG_FILE"; then
        print_success "Ollama model downloaded successfully"
    else
        print_error "Failed to download Ollama model"
        print_info "You can download it later with: docker exec dryad-ollama ollama pull llama3.2:3b"
    fi

    return 0
}

