# DRYAD.AI Enhanced Installation System - Implementation Plan

## Executive Summary

This plan outlines the creation of a comprehensive, interactive installation system for DRYAD.AI that allows users to:
1. Select from multiple deployment configurations
2. Choose optional components (frontends, monitoring, logging, etc.)
3. Install everything with proper dependency management
4. Verify installation health automatically

## Current State Analysis

### Existing Installation Scripts
1. **`install_dryad_server.sh`** - Arch Linux focused, basic installation
2. **`archive/legacy_v9/scripts/quick-start.sh`** - Interactive menu, tier-based
3. **`archive/legacy_v9/scripts/installation_profiles.py`** - Python-based profiles

### Available Components (Not Currently Installed)

#### Deployment Configurations (Docker Compose Files)
- `docker-compose.minimal.yml` - Lightweight, core only
- `docker-compose.basic.yml` - Basic setup
- `docker-compose.development.yml` - Dev environment with hot reload
- `docker-compose.full.yml` - All services including Celery workers
- `docker-compose.production.yml` - Production with Nginx, SSL
- `docker-compose.scalable.yml` - Multi-worker, load balanced
- `docker-compose.gpu.yml` - GPU-accelerated for ML workloads
- `docker-compose.monitoring.yml` - Prometheus + Grafana stack
- `docker-compose.logging.yml` - ELK stack (Elasticsearch, Kibana, Fluentd)

#### Frontend Applications
1. **Dryads Console** (Port 3001)
   - Quantum-inspired knowledge tree navigator
   - Multi-provider AI consultation
   - Memory Keeper system
   - Document viewer with Perplexity AI
   - Hybrid file management

2. **DRYAD University UI** (Port 3006)
   - Student/Faculty/Admin dashboards
   - Agent creation wizard
   - Competition system
   - Curriculum management

3. **Writer Portal** (Port 3000)
   - Next.js document management
   - RAG queries with citations
   - Real-time WebSocket progress
   - OAuth2 Google login

#### Backend Services
- **MCP Server** - Model Context Protocol (already implemented, needs exposure)
- **Celery Workers** - Background task processing
- **PostgreSQL** - Production database (alternative to SQLite)
- **Nginx** - Reverse proxy with SSL/TLS

#### Monitoring & Observability
- **Prometheus** (Port 9090) - Metrics collection
- **Grafana** (Port 3000) - Visualization dashboards
- **cAdvisor** - Container metrics
- **Node Exporter** - System metrics
- **Postgres Exporter** - Database metrics
- **Redis Exporter** - Cache metrics
- **Alertmanager** - Alert management

#### Logging Stack
- **Elasticsearch** (Port 9200) - Log storage
- **Kibana** (Port 5601) - Log visualization
- **Fluentd** - Log aggregation
- **Filebeat** - Log shipping

#### Vector Database Options
- **Weaviate** (Port 8080) - Currently used
- **ChromaDB** (Port 8001) - Lightweight alternative
- **Qdrant** (Port 6333) - High-performance alternative

## Proposed Solution: Enhanced Installation Script

### Architecture

```
install_dryad_enhanced.sh
├── Core Functions
│   ├── check_prerequisites()
│   ├── display_welcome()
│   └── cleanup_on_error()
├── Menu System
│   ├── select_deployment_config()
│   ├── select_optional_components()
│   └── confirm_selections()
├── Installation Functions
│   ├── install_backend()
│   ├── install_frontend()
│   ├── install_monitoring()
│   ├── install_logging()
│   ├── install_database()
│   └── enable_mcp_server()
├── Configuration Management
│   ├── generate_env_files()
│   ├── configure_ports()
│   └── setup_networking()
├── Verification
│   ├── health_check_backend()
│   ├── health_check_frontends()
│   ├── health_check_monitoring()
│   └── display_final_status()
└── Documentation
    └── display_access_info()
```

### Menu Flow

```
1. Welcome Screen
   ↓
2. Prerequisites Check
   ↓
3. Select Deployment Configuration
   - Minimal (Core only, 1-2GB RAM)
   - Basic (Standard features, 2-4GB RAM)
   - Development (Hot reload, debugging, 4-6GB RAM)
   - Full (All services + Celery, 6-8GB RAM)
   - Production (Nginx + SSL + monitoring, 8-10GB RAM)
   - Scalable (Multi-worker + load balancing, 10-12GB RAM)
   - GPU (GPU-accelerated ML, 12GB+ RAM + GPU)
   ↓
4. Select Optional Components (Multi-select)
   Frontend Applications:
   [ ] Dryads Console (Port 3001)
   [ ] DRYAD University UI (Port 3006)
   [ ] Writer Portal (Port 3000)
   
   Backend Enhancements:
   [ ] Enable MCP Server (Model Context Protocol)
   [ ] PostgreSQL Database (instead of SQLite)
   [ ] Celery Workers (if not in deployment config)
   
   Monitoring & Observability:
   [ ] Prometheus + Grafana Stack
   [ ] ELK Logging Stack
   [ ] Full Metrics Suite (all exporters)
   
   Advanced Options:
   [ ] Nginx Reverse Proxy (if not in deployment config)
   [ ] Alternative Vector DB (ChromaDB or Qdrant)
   [ ] SSL/TLS Certificates (Let's Encrypt)
   ↓
5. Configuration
   - LLM Provider (Mock, OpenAI, Anthropic, Ollama)
   - Domain/Hostname
   - API Keys (if needed)
   - Port Customization (optional)
   ↓
6. Confirmation Screen
   - Show all selections
   - Estimated resources (RAM, Disk, Time)
   - Port mapping summary
   ↓
7. Installation
   - Create directories
   - Generate .env files
   - Pull Docker images
   - Start services
   - Install frontends (npm install)
   ↓
8. Health Checks
   - Verify all services
   - Test endpoints
   - Check connectivity
   ↓
9. Final Report
   - Access URLs
   - Credentials
   - Next steps
   - Troubleshooting tips
```

## Implementation Details

### Phase 1: Core Script Structure (Priority: HIGH)

**File:** `install_dryad_enhanced.sh`

#### Key Features:
1. **Modular Functions** - Each component has its own install function
2. **Error Handling** - Graceful failures with rollback capability
3. **State Management** - Track what's installed for cleanup
4. **Logging** - Comprehensive logs for debugging
5. **Interactive Menus** - User-friendly selection process

#### Core Functions:

```bash
# Prerequisites
check_prerequisites()
  - Docker & Docker Compose
  - System resources (RAM, disk)
  - Network connectivity
  - Required ports availability

# Menu System
display_welcome()
select_deployment_config()
  - Returns: DEPLOYMENT_CONFIG variable
select_optional_components()
  - Returns: Array of selected components
confirm_selections()
  - Display summary
  - Get user confirmation

# Installation
install_backend()
  - Start selected docker-compose config
  - Wait for services to be ready
install_frontend(frontend_name)
  - Navigate to frontend directory
  - npm install
  - Configure .env
  - npm run build (for production)
install_monitoring()
  - Start monitoring stack
  - Configure Grafana dashboards
install_logging()
  - Start ELK stack
  - Configure log shipping
enable_mcp_server()
  - Update backend config
  - Restart backend service

# Configuration
generate_env_files()
  - Backend .env
  - Frontend .env files
  - Service-specific configs
configure_ports()
  - Check port conflicts
  - Update docker-compose ports
setup_networking()
  - Docker networks
  - Service discovery

# Health Checks
health_check_backend()
health_check_frontend(frontend_name)
health_check_monitoring()
health_check_logging()

# Reporting
display_final_status()
  - Service status table
  - Access URLs
  - Credentials
  - Next steps
```

### Phase 2: Deployment Configuration Management (Priority: HIGH)

#### Docker Compose File Strategy:

**Problem:** Multiple docker-compose files with overlapping services

**Solution:** Use docker-compose file merging

```bash
# Base command
COMPOSE_CMD="docker compose"

# Add files based on selection
case $DEPLOYMENT_CONFIG in
  "minimal")
    COMPOSE_FILES="-f archive/legacy_v9/docker/docker-compose.minimal.yml"
    ;;
  "basic")
    COMPOSE_FILES="-f archive/legacy_v9/docker/docker-compose.basic.yml"
    ;;
  "development")
    COMPOSE_FILES="-f archive/legacy_v9/docker/docker-compose.development.yml"
    ;;
  "full")
    COMPOSE_FILES="-f archive/legacy_v9/docker/docker-compose.full.yml"
    ;;
  "production")
    COMPOSE_FILES="-f archive/legacy_v9/docker-compose.production.yml"
    ;;
  "scalable")
    COMPOSE_FILES="-f archive/legacy_v9/docker/docker-compose.scalable.yml"
    ;;
  "gpu")
    COMPOSE_FILES="-f archive/legacy_v9/docker/docker-compose.gpu.yml"
    ;;
esac

# Add optional components
if [[ " ${OPTIONAL_COMPONENTS[@]} " =~ " monitoring " ]]; then
  COMPOSE_FILES="$COMPOSE_FILES -f archive/legacy_v9/docker-compose.monitoring.yml"
fi

if [[ " ${OPTIONAL_COMPONENTS[@]} " =~ " logging " ]]; then
  COMPOSE_FILES="$COMPOSE_FILES -f archive/legacy_v9/docker/docker-compose.logging.yml"
fi

# Execute
$COMPOSE_CMD $COMPOSE_FILES up -d
```

### Phase 3: Frontend Installation (Priority: MEDIUM)

#### Frontend Installation Function:

```bash
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
  esac

  print_step "Installing $frontend_name..."

  # Check if directory exists
  if [[ ! -d "$frontend_dir" ]]; then
    print_error "Frontend directory not found: $frontend_dir"
    return 1
  fi

  # Navigate to directory
  cd "$frontend_dir"

  # Check for package.json
  if [[ ! -f "package.json" ]]; then
    print_error "package.json not found in $frontend_dir"
    return 1
  fi

  # Install dependencies
  print_info "Installing npm dependencies..."
  if ! npm install; then
    print_error "npm install failed for $frontend_name"
    return 1
  fi

  # Create .env file
  print_info "Configuring environment..."
  cat > .env << EOF
VITE_API_BASE_URL=http://localhost:8000/api/v1
VITE_BACKEND_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000/ws
EOF

  # Build for production (optional)
  if [[ "$DEPLOYMENT_CONFIG" == "production" ]]; then
    print_info "Building for production..."
    if ! npm run build; then
      print_warning "Production build failed, will run in dev mode"
    fi
  fi

  # Start development server in background
  print_info "Starting $frontend_name on port $frontend_port..."
  nohup npm run dev > "$LOG_DIR/${frontend_name}.log" 2>&1 &
  echo $! > "$PID_DIR/${frontend_name}.pid"

  # Return to original directory
  cd - > /dev/null

  print_success "$frontend_name installed and started on port $frontend_port"
}
```

### Phase 4: MCP Server Enablement (Priority: HIGH)

The MCP server is already implemented in the codebase but not exposed. We need to:

1. **Update Backend Configuration:**
   - Add MCP endpoint to FastAPI routes
   - Enable MCP in environment variables

2. **Configuration Changes:**

```bash
enable_mcp_server() {
  print_step "Enabling MCP Server..."

  # Update .env file
  if grep -q "ENABLE_MCP_SERVER" .env; then
    sed -i 's/ENABLE_MCP_SERVER=.*/ENABLE_MCP_SERVER=true/' .env
  else
    echo "ENABLE_MCP_SERVER=true" >> .env
  fi

  # Add MCP endpoint configuration
  cat >> .env << EOF
MCP_SERVER_HOST=0.0.0.0
MCP_SERVER_PORT=8000
MCP_ENDPOINT_PATH=/mcp
EOF

  # Restart backend to apply changes
  print_info "Restarting backend to enable MCP..."
  docker compose restart dryad-backend

  # Wait for service to be ready
  wait_for_service "http://localhost:8000/mcp" 30

  print_success "MCP Server enabled at http://localhost:8000/mcp"
}
```

### Phase 5: Monitoring & Logging (Priority: MEDIUM)

#### Monitoring Stack Installation:

```bash
install_monitoring() {
  print_step "Installing Monitoring Stack (Prometheus + Grafana)..."

  # Start monitoring services
  docker compose -f archive/legacy_v9/docker-compose.monitoring.yml up -d

  # Wait for services
  print_info "Waiting for Prometheus..."
  wait_for_service "http://localhost:9090/-/ready" 60

  print_info "Waiting for Grafana..."
  wait_for_service "http://localhost:3000/api/health" 60

  # Configure Grafana dashboards
  print_info "Configuring Grafana dashboards..."
  configure_grafana_dashboards

  print_success "Monitoring stack installed"
  print_info "Prometheus: http://localhost:9090"
  print_info "Grafana: http://localhost:3000 (admin/admin)"
}

install_logging() {
  print_step "Installing Logging Stack (ELK)..."

  # Start logging services
  docker compose -f archive/legacy_v9/docker/docker-compose.logging.yml up -d

  # Wait for Elasticsearch
  print_info "Waiting for Elasticsearch..."
  wait_for_service "http://localhost:9200/_cluster/health" 120

  # Wait for Kibana
  print_info "Waiting for Kibana..."
  wait_for_service "http://localhost:5601/api/status" 120

  print_success "Logging stack installed"
  print_info "Elasticsearch: http://localhost:9200"
  print_info "Kibana: http://localhost:5601"
}
```

### Phase 6: Configuration Management (Priority: HIGH)

#### Environment File Generation:

```bash
generate_env_files() {
  print_step "Generating configuration files..."

  # Backend .env
  cat > .env << EOF
# DRYAD Backend Configuration
# Generated by install_dryad_enhanced.sh on $(date)

# Deployment
DEPLOYMENT_CONFIG=$DEPLOYMENT_CONFIG
ENVIRONMENT=${ENVIRONMENT:-production}

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
API_BASE_URL=http://localhost:8000

# Database
DATABASE_URL=sqlite:///./dryad.db
$(if [[ " ${OPTIONAL_COMPONENTS[@]} " =~ " postgresql " ]]; then
  echo "DATABASE_URL=postgresql://dryad:dryad@localhost:5432/dryad"
fi)

# LLM Provider
LLM_PROVIDER=$LLM_PROVIDER
$(if [[ "$LLM_PROVIDER" == "openai" ]]; then
  echo "OPENAI_API_KEY=$OPENAI_API_KEY"
fi)
$(if [[ "$LLM_PROVIDER" == "anthropic" ]]; then
  echo "ANTHROPIC_API_KEY=$ANTHROPIC_API_KEY"
fi)

# Vector Database
WEAVIATE_URL=http://localhost:8080
WEAVIATE_API_KEY=

# Redis
REDIS_URL=redis://localhost:6379

# Security
JWT_SECRET_KEY=$(generate_secret)
JWT_ALGORITHM=HS256
JWT_EXPIRATION=3600

# MCP Server
$(if [[ " ${OPTIONAL_COMPONENTS[@]} " =~ " mcp " ]]; then
  echo "ENABLE_MCP_SERVER=true"
  echo "MCP_ENDPOINT_PATH=/mcp"
fi)

# Monitoring
$(if [[ " ${OPTIONAL_COMPONENTS[@]} " =~ " monitoring " ]]; then
  echo "ENABLE_METRICS=true"
  echo "PROMETHEUS_ENABLED=true"
fi)

# Logging
$(if [[ " ${OPTIONAL_COMPONENTS[@]} " =~ " logging " ]]; then
  echo "LOG_LEVEL=INFO"
  echo "ENABLE_ELK=true"
fi)

# CORS
CORS_ORIGINS=["http://localhost:3000","http://localhost:3001","http://localhost:3006"]

EOF

  print_success "Backend .env file created"

  # Frontend .env files
  for frontend in "${SELECTED_FRONTENDS[@]}"; do
    generate_frontend_env "$frontend"
  done
}

generate_frontend_env() {
  local frontend=$1
  local frontend_dir=""

  case $frontend in
    "dryads-console")
      frontend_dir="archive/legacy_v9/clients/dryads-console"
      ;;
    "university-ui")
      frontend_dir="archive/legacy_v9/clients/dryad-university-ui"
      ;;
    "writer-portal")
      frontend_dir="archive/legacy_v9/clients/frontend/writer-portal"
      ;;
  esac

  cat > "$frontend_dir/.env" << EOF
# Frontend Configuration for $frontend
# Generated by install_dryad_enhanced.sh on $(date)

VITE_API_BASE_URL=http://localhost:8000/api/v1
VITE_BACKEND_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000/ws

# Feature Flags
VITE_ENABLE_MCP=$(if [[ " ${OPTIONAL_COMPONENTS[@]} " =~ " mcp " ]]; then echo "true"; else echo "false"; fi)
VITE_ENABLE_MONITORING=$(if [[ " ${OPTIONAL_COMPONENTS[@]} " =~ " monitoring " ]]; then echo "true"; else echo "false"; fi)

EOF

  print_success "Frontend .env created for $frontend"
}
```

### Phase 7: Port Management (Priority: MEDIUM)

#### Port Conflict Detection:

```bash
check_port_conflicts() {
  print_step "Checking for port conflicts..."

  local ports_to_check=(
    "8000:DRYAD Backend"
    "8080:Weaviate"
    "6379:Redis"
    "11434:Ollama"
  )

  # Add frontend ports
  if [[ " ${SELECTED_FRONTENDS[@]} " =~ " dryads-console " ]]; then
    ports_to_check+=("3001:Dryads Console")
  fi
  if [[ " ${SELECTED_FRONTENDS[@]} " =~ " university-ui " ]]; then
    ports_to_check+=("3006:University UI")
  fi
  if [[ " ${SELECTED_FRONTENDS[@]} " =~ " writer-portal " ]]; then
    ports_to_check+=("3000:Writer Portal")
  fi

  # Add monitoring ports
  if [[ " ${OPTIONAL_COMPONENTS[@]} " =~ " monitoring " ]]; then
    ports_to_check+=("9090:Prometheus" "3000:Grafana")
  fi

  # Add logging ports
  if [[ " ${OPTIONAL_COMPONENTS[@]} " =~ " logging " ]]; then
    ports_to_check+=("9200:Elasticsearch" "5601:Kibana")
  fi

  local conflicts=()

  for port_info in "${ports_to_check[@]}"; do
    local port="${port_info%%:*}"
    local service="${port_info##*:}"

    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
      conflicts+=("Port $port ($service) is already in use")
    fi
  done

  if [[ ${#conflicts[@]} -gt 0 ]]; then
    print_error "Port conflicts detected:"
    for conflict in "${conflicts[@]}"; do
      echo "  - $conflict"
    done

    read -p "Do you want to continue anyway? (y/N): " continue_anyway
    if [[ ! "$continue_anyway" =~ ^[Yy]$ ]]; then
      exit 1
    fi
  else
    print_success "No port conflicts detected"
  fi
}
```

### Phase 8: Health Checks (Priority: HIGH)

#### Comprehensive Health Check System:

```bash
health_check_all() {
  print_step "Running comprehensive health checks..."

  local all_healthy=true

  # Backend
  if ! health_check_backend; then
    all_healthy=false
  fi

  # Frontends
  for frontend in "${SELECTED_FRONTENDS[@]}"; do
    if ! health_check_frontend "$frontend"; then
      all_healthy=false
    fi
  done

  # Monitoring
  if [[ " ${OPTIONAL_COMPONENTS[@]} " =~ " monitoring " ]]; then
    if ! health_check_monitoring; then
      all_healthy=false
    fi
  fi

  # Logging
  if [[ " ${OPTIONAL_COMPONENTS[@]} " =~ " logging " ]]; then
    if ! health_check_logging; then
      all_healthy=false
    fi
  fi

  if $all_healthy; then
    print_success "All health checks passed!"
    return 0
  else
    print_warning "Some health checks failed. Check logs for details."
    return 1
  fi
}

health_check_backend() {
  print_info "Checking backend health..."

  if curl -f http://localhost:8000/api/v1/health/status &> /dev/null; then
    print_success "✓ Backend API is healthy"
    return 0
  else
    print_error "✗ Backend API health check failed"
    return 1
  fi
}

health_check_frontend() {
  local frontend=$1
  local port=""

  case $frontend in
    "dryads-console") port=3001 ;;
    "university-ui") port=3006 ;;
    "writer-portal") port=3000 ;;
  esac

  print_info "Checking $frontend health..."

  if curl -f http://localhost:$port &> /dev/null; then
    print_success "✓ $frontend is healthy (port $port)"
    return 0
  else
    print_error "✗ $frontend health check failed"
    return 1
  fi
}

health_check_monitoring() {
  print_info "Checking monitoring stack..."

  local healthy=true

  if curl -f http://localhost:9090/-/ready &> /dev/null; then
    print_success "✓ Prometheus is healthy"
  else
    print_error "✗ Prometheus health check failed"
    healthy=false
  fi

  if curl -f http://localhost:3000/api/health &> /dev/null; then
    print_success "✓ Grafana is healthy"
  else
    print_error "✗ Grafana health check failed"
    healthy=false
  fi

  $healthy
}

health_check_logging() {
  print_info "Checking logging stack..."

  local healthy=true

  if curl -f http://localhost:9200/_cluster/health &> /dev/null; then
    print_success "✓ Elasticsearch is healthy"
  else
    print_error "✗ Elasticsearch health check failed"
    healthy=false
  fi

  if curl -f http://localhost:5601/api/status &> /dev/null; then
    print_success "✓ Kibana is healthy"
  else
    print_error "✗ Kibana health check failed"
    healthy=false
  fi

  $healthy
}
```

### Phase 9: Final Reporting (Priority: HIGH)

#### Installation Summary Display:

```bash
display_final_status() {
  clear
  print_header "🎉 DRYAD.AI Installation Complete!"

  echo ""
  echo "═══════════════════════════════════════════════════════════════"
  echo "                    INSTALLATION SUMMARY"
  echo "═══════════════════════════════════════════════════════════════"
  echo ""

  # Deployment Configuration
  echo "📦 Deployment Configuration: $DEPLOYMENT_CONFIG"
  echo ""

  # Backend Services
  echo "🔧 Backend Services:"
  echo "   ✓ DRYAD API         → http://localhost:8000"
  echo "   ✓ API Docs          → http://localhost:8000/docs"
  echo "   ✓ Health Check      → http://localhost:8000/api/v1/health/status"

  if [[ " ${OPTIONAL_COMPONENTS[@]} " =~ " mcp " ]]; then
    echo "   ✓ MCP Server        → http://localhost:8000/mcp"
  fi

  echo ""

  # Frontend Applications
  if [[ ${#SELECTED_FRONTENDS[@]} -gt 0 ]]; then
    echo "🎨 Frontend Applications:"
    for frontend in "${SELECTED_FRONTENDS[@]}"; do
      case $frontend in
        "dryads-console")
          echo "   ✓ Dryads Console    → http://localhost:3001"
          ;;
        "university-ui")
          echo "   ✓ University UI     → http://localhost:3006"
          ;;
        "writer-portal")
          echo "   ✓ Writer Portal     → http://localhost:3000"
          ;;
      esac
    done
    echo ""
  fi

  # Monitoring
  if [[ " ${OPTIONAL_COMPONENTS[@]} " =~ " monitoring " ]]; then
    echo "📊 Monitoring & Metrics:"
    echo "   ✓ Prometheus        → http://localhost:9090"
    echo "   ✓ Grafana           → http://localhost:3000 (admin/admin)"
    echo ""
  fi

  # Logging
  if [[ " ${OPTIONAL_COMPONENTS[@]} " =~ " logging " ]]; then
    echo "📝 Logging Stack:"
    echo "   ✓ Elasticsearch     → http://localhost:9200"
    echo "   ✓ Kibana            → http://localhost:5601"
    echo ""
  fi

  # Database
  echo "🗄️  Database:"
  if [[ " ${OPTIONAL_COMPONENTS[@]} " =~ " postgresql " ]]; then
    echo "   ✓ PostgreSQL        → localhost:5432"
  else
    echo "   ✓ SQLite            → ./dryad.db"
  fi
  echo ""

  # Vector Database
  echo "🔍 Vector Database:"
  echo "   ✓ Weaviate          → http://localhost:8080"
  echo ""

  # Cache
  echo "⚡ Cache:"
  echo "   ✓ Redis             → localhost:6379"
  echo ""

  # LLM Provider
  echo "🤖 LLM Provider: $LLM_PROVIDER"
  if [[ "$LLM_PROVIDER" == "ollama" ]]; then
    echo "   ✓ Ollama            → http://localhost:11434"
  fi
  echo ""

  echo "═══════════════════════════════════════════════════════════════"
  echo ""

  # Management Commands
  echo "🔧 Management Commands:"
  echo ""
  echo "   View Logs:"
  echo "     docker compose logs -f dryad-backend"
  echo ""
  echo "   Stop All Services:"
  echo "     docker compose down"
  echo ""
  echo "   Restart Services:"
  echo "     docker compose restart"
  echo ""
  echo "   Check Status:"
  echo "     docker compose ps"
  echo ""

  # Next Steps
  echo "📚 Next Steps:"
  echo ""
  echo "   1. Test the API:"
  echo "      curl http://localhost:8000/api/v1/health/status"
  echo ""
  echo "   2. Explore the documentation:"
  echo "      http://localhost:8000/docs"
  echo ""
  echo "   3. Create your first user:"
  echo "      See docs/getting-started/authentication.md"
  echo ""

  if [[ ${#SELECTED_FRONTENDS[@]} -gt 0 ]]; then
    echo "   4. Access the frontend:"
    for frontend in "${SELECTED_FRONTENDS[@]}"; do
      case $frontend in
        "dryads-console")
          echo "      Dryads Console: http://localhost:3001"
          ;;
        "university-ui")
          echo "      University UI: http://localhost:3006"
          ;;
        "writer-portal")
          echo "      Writer Portal: http://localhost:3000"
          ;;
      esac
    done
    echo ""
  fi

  # Troubleshooting
  echo "🆘 Troubleshooting:"
  echo ""
  echo "   Installation Logs:"
  echo "     $LOG_FILE"
  echo ""
  echo "   Service Logs:"
  echo "     docker compose logs [service-name]"
  echo ""
  echo "   Health Checks:"
  echo "     ./verify_installation.sh"
  echo ""

  # Configuration Files
  echo "⚙️  Configuration Files:"
  echo ""
  echo "   Backend:  .env"
  if [[ ${#SELECTED_FRONTENDS[@]} -gt 0 ]]; then
    for frontend in "${SELECTED_FRONTENDS[@]}"; do
      case $frontend in
        "dryads-console")
          echo "   Frontend: archive/legacy_v9/clients/dryads-console/.env"
          ;;
        "university-ui")
          echo "   Frontend: archive/legacy_v9/clients/dryad-university-ui/.env"
          ;;
        "writer-portal")
          echo "   Frontend: archive/legacy_v9/clients/frontend/writer-portal/.env"
          ;;
      esac
    done
  fi
  echo ""

  echo "═══════════════════════════════════════════════════════════════"
  echo ""
  print_success "Installation completed successfully! 🚀"
  echo ""
}
```

## Implementation Timeline

### Week 1: Core Infrastructure
- [ ] Create base script structure
- [ ] Implement prerequisite checks
- [ ] Build interactive menu system
- [ ] Add deployment config selection
- [ ] Test basic installation flow

### Week 2: Component Installation
- [ ] Implement backend installation
- [ ] Add frontend installation functions
- [ ] Create monitoring stack installer
- [ ] Add logging stack installer
- [ ] Implement MCP server enablement

### Week 3: Configuration & Integration
- [ ] Build environment file generation
- [ ] Add port conflict detection
- [ ] Implement configuration management
- [ ] Create health check system
- [ ] Add error handling and rollback

### Week 4: Testing & Documentation
- [ ] Test all deployment configurations
- [ ] Test all component combinations
- [ ] Create user documentation
- [ ] Add troubleshooting guide
- [ ] Final integration testing

## File Structure

```
DRYAD_backend/
├── install_dryad_enhanced.sh          # Main installation script
├── lib/
│   ├── install_functions.sh           # Installation functions
│   ├── menu_functions.sh              # Interactive menus
│   ├── health_checks.sh               # Health check functions
│   ├── config_generators.sh           # Config file generators
│   └── utils.sh                       # Utility functions
├── configs/
│   ├── deployment_configs.json        # Deployment config metadata
│   ├── component_registry.json        # Component definitions
│   └── port_mappings.json             # Port configuration
└── docs/
    ├── INSTALLATION_GUIDE.md          # User guide
    ├── DEPLOYMENT_CONFIGS.md          # Config documentation
    └── TROUBLESHOOTING.md             # Troubleshooting guide
```

## Success Criteria

### Functional Requirements
- ✅ User can select any deployment configuration
- ✅ User can select any combination of optional components
- ✅ Script validates dependencies automatically
- ✅ Script detects and handles port conflicts
- ✅ All services start successfully
- ✅ Health checks verify all components
- ✅ Clear error messages and recovery options

### Non-Functional Requirements
- ✅ Installation completes in < 15 minutes (excluding downloads)
- ✅ Script is idempotent (can be run multiple times)
- ✅ Comprehensive logging for debugging
- ✅ User-friendly interactive experience
- ✅ Graceful error handling with rollback
- ✅ Clear documentation and help text

## Risk Mitigation

### Risk 1: Port Conflicts
**Mitigation:** Pre-flight port conflict detection with user override option

### Risk 2: Resource Constraints
**Mitigation:** Display resource requirements before installation, allow user to adjust

### Risk 3: Docker Compose File Conflicts
**Mitigation:** Careful file merging strategy, test all combinations

### Risk 4: Frontend Build Failures
**Mitigation:** Fallback to development mode if production build fails

### Risk 5: Service Startup Timeouts
**Mitigation:** Configurable timeout values, retry logic, clear error messages

## Next Steps

1. **Review and Approve Plan** - Get stakeholder approval
2. **Create Base Script** - Start with core structure
3. **Implement Menu System** - Build interactive selection
4. **Add Component Installers** - One component at a time
5. **Test Thoroughly** - All combinations
6. **Document Everything** - User guides and troubleshooting
7. **Deploy and Monitor** - Gather user feedback

---

**Plan Status:** ✅ COMPLETE - Ready for Implementation

**Estimated Effort:** 4 weeks (1 developer)

**Priority:** HIGH - Significantly improves user experience and system capabilities
