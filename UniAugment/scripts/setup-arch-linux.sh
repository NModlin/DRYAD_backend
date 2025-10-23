#!/bin/bash

################################################################################
# UniAugment - Arch Linux Setup Script
# For HP Envy computers with Arch Linux + Sway
# 
# This script sets up Docker and Docker Compose on Arch Linux
# and configures the machine for distributed UniAugment deployment
################################################################################

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
MACHINE_NAME=""
MACHINE_ROLE=""
WINDOWS_HOST=""
ARCH_HOST_1=""
ARCH_HOST_2=""

################################################################################
# Functions
################################################################################

print_header() {
    echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║${NC}  $1"
    echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

check_root() {
    if [[ $EUID -ne 0 ]]; then
        print_error "This script must be run as root"
        exit 1
    fi
}

check_arch_linux() {
    if ! grep -q "Arch Linux" /etc/os-release; then
        print_error "This script is designed for Arch Linux"
        exit 1
    fi
    print_success "Arch Linux detected"
}

install_docker() {
    print_header "Installing Docker"
    
    if command -v docker &> /dev/null; then
        print_warning "Docker already installed"
        docker --version
    else
        print_info "Installing Docker..."
        pacman -Syu --noconfirm
        pacman -S --noconfirm docker docker-compose
        
        # Enable and start Docker
        systemctl enable docker
        systemctl start docker
        
        print_success "Docker installed and started"
    fi
}

configure_docker_user() {
    print_header "Configuring Docker User"
    
    # Add current user to docker group
    if [ -n "$SUDO_USER" ]; then
        usermod -aG docker "$SUDO_USER"
        print_success "Added $SUDO_USER to docker group"
        print_warning "Please log out and log back in for group changes to take effect"
    fi
}

configure_networking() {
    print_header "Configuring Networking"
    
    read -p "Enter this machine's hostname (e.g., arch-1, arch-2): " MACHINE_NAME
    read -p "Enter this machine's IP address (e.g., 192.168.1.100): " MACHINE_IP
    read -p "Enter Windows machine IP address: " WINDOWS_HOST
    read -p "Enter Arch Linux Machine 1 IP address: " ARCH_HOST_1
    read -p "Enter Arch Linux Machine 2 IP address: " ARCH_HOST_2
    
    # Set hostname
    hostnamectl set-hostname "$MACHINE_NAME"
    print_success "Hostname set to $MACHINE_NAME"
    
    # Create network config file
    cat > /etc/docker/daemon.json << EOF
{
    "storage-driver": "overlay2",
    "log-driver": "json-file",
    "log-opts": {
        "max-size": "10m",
        "max-file": "3"
    },
    "insecure-registries": [
        "$WINDOWS_HOST:5000",
        "$ARCH_HOST_1:5000",
        "$ARCH_HOST_2:5000"
    ]
}
EOF
    
    systemctl restart docker
    print_success "Docker networking configured"
}

create_docker_network() {
    print_header "Creating Docker Networks"
    
    # Create overlay network for distributed deployment
    docker network create --driver overlay --attachable uniaugment-distributed || true
    print_success "Created distributed network"
    
    # Create bridge network for local services
    docker network create --driver bridge uniaugment-local || true
    print_success "Created local network"
}

select_machine_role() {
    print_header "Select Machine Role"

    echo "This machine will run:"
    echo "1) API Server + Redis + Prometheus (Arch Machine 1)"
    echo "2) Celery Workers + Grafana (Arch Machine 2)"
    echo "3) Custom configuration"

    read -p "Select role (1-3): " ROLE_CHOICE

    case $ROLE_CHOICE in
        1)
            MACHINE_ROLE="api-server"
            print_success "Selected: API Server + Redis + Prometheus"
            ;;
        2)
            MACHINE_ROLE="workers"
            print_success "Selected: Celery Workers + Grafana"
            ;;
        3)
            MACHINE_ROLE="custom"
            print_success "Selected: Custom configuration"
            ;;
        *)
            print_error "Invalid selection"
            exit 1
            ;;
    esac
}

configure_agent_studio() {
    print_header "Agent Creation Studio Configuration"

    # Ask if user wants to enable Agent Creation Studio
    read -p "Enable Agent Creation Studio enhancements? (y/n) [default: y]: " ENABLE_STUDIO
    ENABLE_STUDIO=${ENABLE_STUDIO:-y}

    if [[ "$ENABLE_STUDIO" =~ ^[Yy]$ ]]; then
        AGENT_STUDIO_ENABLED="true"
        print_success "Agent Creation Studio enabled"

        # Visual customization
        read -p "Enable visual customization (avatars, colors, themes)? (y/n) [default: y]: " ENABLE_VISUAL
        ENABLE_VISUAL=${ENABLE_VISUAL:-y}
        if [[ "$ENABLE_VISUAL" =~ ^[Yy]$ ]]; then
            AGENT_VISUAL_CUSTOMIZATION="true"
            print_success "Visual customization enabled"
        else
            AGENT_VISUAL_CUSTOMIZATION="false"
        fi

        # Behavioral customization
        read -p "Enable behavioral customization (learning style, risk tolerance)? (y/n) [default: y]: " ENABLE_BEHAVIORAL
        ENABLE_BEHAVIORAL=${ENABLE_BEHAVIORAL:-y}
        if [[ "$ENABLE_BEHAVIORAL" =~ ^[Yy]$ ]]; then
            AGENT_BEHAVIORAL_CUSTOMIZATION="true"
            print_success "Behavioral customization enabled"
        else
            AGENT_BEHAVIORAL_CUSTOMIZATION="false"
        fi

        # Default settings
        print_info "Using default visual and behavioral settings (can be changed in .env file)"
        DEFAULT_AVATAR_STYLE="abstract"
        DEFAULT_PRIMARY_COLOR="#0066CC"
        DEFAULT_VISUAL_THEME="professional"
        DEFAULT_LEARNING_STYLE="visual"
        DEFAULT_RISK_TOLERANCE="0.5"
        DEFAULT_COLLABORATION_STYLE="equal"
    else
        AGENT_STUDIO_ENABLED="false"
        AGENT_VISUAL_CUSTOMIZATION="false"
        AGENT_BEHAVIORAL_CUSTOMIZATION="false"
        print_info "Agent Creation Studio disabled"
    fi
}

configure_agentic_university() {
    print_header "Agentic Research University System Configuration"

    # Ask if user wants to enable Agentic University System
    read -p "Enable Agentic Research University System (Level 6)? (y/n) [default: n]: " ENABLE_UNIVERSITY
    ENABLE_UNIVERSITY=${ENABLE_UNIVERSITY:-n}

    if [[ "$ENABLE_UNIVERSITY" =~ ^[Yy]$ ]]; then
        UNIVERSITY_ENABLED="true"
        print_success "Agentic University System enabled"

        # University management
        read -p "Enable university management? (y/n) [default: y]: " ENABLE_UNI_MGMT
        ENABLE_UNI_MGMT=${ENABLE_UNI_MGMT:-y}
        if [[ "$ENABLE_UNI_MGMT" =~ ^[Yy]$ ]]; then
            UNIVERSITY_MANAGEMENT_ENABLED="true"
            print_success "University management enabled"
        else
            UNIVERSITY_MANAGEMENT_ENABLED="false"
        fi

        # Curriculum system
        read -p "Enable curriculum system? (y/n) [default: y]: " ENABLE_CURRICULUM
        ENABLE_CURRICULUM=${ENABLE_CURRICULUM:-y}
        if [[ "$ENABLE_CURRICULUM" =~ ^[Yy]$ ]]; then
            CURRICULUM_SYSTEM_ENABLED="true"
            print_success "Curriculum system enabled"
        else
            CURRICULUM_SYSTEM_ENABLED="false"
        fi

        # Competition system
        read -p "Enable competition/arena system? (y/n) [default: y]: " ENABLE_COMPETITION
        ENABLE_COMPETITION=${ENABLE_COMPETITION:-y}
        if [[ "$ENABLE_COMPETITION" =~ ^[Yy]$ ]]; then
            COMPETITION_SYSTEM_ENABLED="true"
            print_success "Competition system enabled"

            # Leaderboards and Elo ratings
            read -p "Enable leaderboards and Elo ratings? (y/n) [default: y]: " ENABLE_LEADERBOARD
            ENABLE_LEADERBOARD=${ENABLE_LEADERBOARD:-y}
            if [[ "$ENABLE_LEADERBOARD" =~ ^[Yy]$ ]]; then
                ENABLE_LEADERBOARDS="true"
                ENABLE_ELO_RATINGS="true"
                print_success "Leaderboards and Elo ratings enabled"
            else
                ENABLE_LEADERBOARDS="false"
                ENABLE_ELO_RATINGS="false"
            fi
        else
            COMPETITION_SYSTEM_ENABLED="false"
            ENABLE_LEADERBOARDS="false"
            ENABLE_ELO_RATINGS="false"
        fi

        # Resource limits
        print_info "Setting resource limits (can be changed in .env file)"
        read -p "Max agents per university [default: 1000]: " MAX_AGENTS
        MAX_AGENTS_PER_UNIVERSITY=${MAX_AGENTS:-1000}

        read -p "Max competitions per university [default: 100]: " MAX_COMPS
        MAX_COMPETITIONS_PER_UNIVERSITY=${MAX_COMPS:-100}

        read -p "Default storage limit in GB [default: 100]: " STORAGE_LIMIT
        DEFAULT_STORAGE_LIMIT_GB=${STORAGE_LIMIT:-100}

        # Isolation level
        print_info "Select default isolation level:"
        echo "  1) strict - Complete isolation between universities"
        echo "  2) shared - Shared resources with logical separation"
        echo "  3) hybrid - Mix of strict and shared"
        read -p "Choice [default: 1]: " ISOLATION_CHOICE
        ISOLATION_CHOICE=${ISOLATION_CHOICE:-1}
        case $ISOLATION_CHOICE in
            1) DEFAULT_ISOLATION_LEVEL="strict" ;;
            2) DEFAULT_ISOLATION_LEVEL="shared" ;;
            3) DEFAULT_ISOLATION_LEVEL="hybrid" ;;
            *) DEFAULT_ISOLATION_LEVEL="strict" ;;
        esac
        print_success "Isolation level set to: $DEFAULT_ISOLATION_LEVEL"

        # Training data collection
        read -p "Enable training data collection from competitions? (y/n) [default: y]: " ENABLE_TRAINING_DATA
        ENABLE_TRAINING_DATA=${ENABLE_TRAINING_DATA:-y}
        if [[ "$ENABLE_TRAINING_DATA" =~ ^[Yy]$ ]]; then
            TRAINING_DATA_COLLECTION="true"
            print_success "Training data collection enabled"
        else
            TRAINING_DATA_COLLECTION="false"
        fi

        # Arena mode
        read -p "Enable Arena/Dojo competition mode? (y/n) [default: y]: " ENABLE_ARENA
        ENABLE_ARENA=${ENABLE_ARENA:-y}
        if [[ "$ENABLE_ARENA" =~ ^[Yy]$ ]]; then
            ARENA_MODE_ENABLED="true"
            print_success "Arena mode enabled"
        else
            ARENA_MODE_ENABLED="false"
        fi

        # Default Elo K-factor
        DEFAULT_ELO_K_FACTOR="32"
        print_info "Using default Elo K-factor: 32 (can be changed in .env file)"
    else
        UNIVERSITY_ENABLED="false"
        UNIVERSITY_MANAGEMENT_ENABLED="false"
        CURRICULUM_SYSTEM_ENABLED="false"
        COMPETITION_SYSTEM_ENABLED="false"
        ENABLE_LEADERBOARDS="false"
        ENABLE_ELO_RATINGS="false"
        TRAINING_DATA_COLLECTION="false"
        ARENA_MODE_ENABLED="false"
        DEFAULT_ISOLATION_LEVEL="strict"
        MAX_AGENTS_PER_UNIVERSITY="1000"
        MAX_COMPETITIONS_PER_UNIVERSITY="100"
        DEFAULT_STORAGE_LIMIT_GB="100"
        DEFAULT_ELO_K_FACTOR="32"
        print_info "Agentic University System disabled"
    fi
}

create_config_files() {
    print_header "Creating Configuration Files"
    
    # Create config directory
    mkdir -p /opt/uniaugment/config
    mkdir -p /opt/uniaugment/data
    mkdir -p /opt/uniaugment/logs
    
    # Create environment file
    cat > /opt/uniaugment/config/.env.distributed << EOF
# UniAugment Distributed Deployment Configuration
STACK_TYPE=full
MACHINE_NAME=$MACHINE_NAME
MACHINE_ROLE=$MACHINE_ROLE

# Network Configuration
WINDOWS_HOST=$WINDOWS_HOST
ARCH_HOST_1=$ARCH_HOST_1
ARCH_HOST_2=$ARCH_HOST_2

# Database (on Windows machine)
DATABASE_URL=postgresql://uniaugment:changeme@$WINDOWS_HOST:5432/uniaugment

# Redis (on Arch Machine 1)
REDIS_URL=redis://$ARCH_HOST_1:6379/0
CELERY_BROKER_URL=redis://$ARCH_HOST_1:6379/0

# Weaviate (on Windows machine)
WEAVIATE_URL=http://$WINDOWS_HOST:8080

# Monitoring
PROMETHEUS_URL=http://$ARCH_HOST_1:9090
GRAFANA_URL=http://$ARCH_HOST_2:3000

# Security
JWT_SECRET_KEY=$(openssl rand -base64 32)
POSTGRES_PASSWORD=$(openssl rand -base64 32)
REDIS_PASSWORD=$(openssl rand -base64 32)

# Logging
LOG_LEVEL=INFO

# Agent Creation Studio - Phase 1
AGENT_CREATION_STUDIO_ENABLED=${AGENT_STUDIO_ENABLED:-false}
AGENT_VISUAL_CUSTOMIZATION=${AGENT_VISUAL_CUSTOMIZATION:-true}
AGENT_BEHAVIORAL_CUSTOMIZATION=${AGENT_BEHAVIORAL_CUSTOMIZATION:-true}

# Default Visual Settings
DEFAULT_AVATAR_STYLE=${DEFAULT_AVATAR_STYLE:-abstract}
DEFAULT_PRIMARY_COLOR=${DEFAULT_PRIMARY_COLOR:-#0066CC}
DEFAULT_SECONDARY_COLOR=${DEFAULT_SECONDARY_COLOR:-#00CC66}
DEFAULT_ACCENT_COLOR=${DEFAULT_ACCENT_COLOR:-#CC6600}
DEFAULT_VISUAL_THEME=${DEFAULT_VISUAL_THEME:-professional}
DEFAULT_GLOW_INTENSITY=${DEFAULT_GLOW_INTENSITY:-0.5}

# Default Behavioral Settings
DEFAULT_LEARNING_STYLE=${DEFAULT_LEARNING_STYLE:-visual}
DEFAULT_LEARNING_PACE=${DEFAULT_LEARNING_PACE:-1.0}
DEFAULT_RISK_TOLERANCE=${DEFAULT_RISK_TOLERANCE:-0.5}
DEFAULT_COLLABORATION_STYLE=${DEFAULT_COLLABORATION_STYLE:-equal}
DEFAULT_COMMUNICATION_TONE=${DEFAULT_COMMUNICATION_TONE:-professional}
DEFAULT_DECISION_SPEED=${DEFAULT_DECISION_SPEED:-0.5}
DEFAULT_DECISION_CONFIDENCE=${DEFAULT_DECISION_CONFIDENCE:-0.7}

# Specialization & Skill Trees - Phase 2
SPECIALIZATION_SKILL_TREES_ENABLED=${SPECIALIZATION_ENABLED:-false}
DEFAULT_PRIMARY_SPECIALIZATION=${DEFAULT_PRIMARY_SPECIALIZATION:-data_science}
MAX_SECONDARY_SPECIALIZATIONS=${MAX_SECONDARY_SPECIALIZATIONS:-3}
CROSS_SPECIALIZATION_PENALTY=${CROSS_SPECIALIZATION_PENALTY:-0.2}
SKILL_TREE_ENABLED=${SKILL_TREE_ENABLED:-true}
PROGRESSION_PATHS_ENABLED=${PROGRESSION_PATHS_ENABLED:-true}

# Agentic Research University System - Level 6
AGENTIC_UNIVERSITY_ENABLED=${UNIVERSITY_ENABLED:-false}
UNIVERSITY_MANAGEMENT_ENABLED=${UNIVERSITY_MANAGEMENT_ENABLED:-true}
CURRICULUM_SYSTEM_ENABLED=${CURRICULUM_SYSTEM_ENABLED:-true}
COMPETITION_SYSTEM_ENABLED=${COMPETITION_SYSTEM_ENABLED:-true}
DEFAULT_ISOLATION_LEVEL=${DEFAULT_ISOLATION_LEVEL:-strict}
MAX_AGENTS_PER_UNIVERSITY=${MAX_AGENTS_PER_UNIVERSITY:-1000}
MAX_COMPETITIONS_PER_UNIVERSITY=${MAX_COMPETITIONS_PER_UNIVERSITY:-100}
DEFAULT_STORAGE_LIMIT_GB=${DEFAULT_STORAGE_LIMIT_GB:-100}
ENABLE_LEADERBOARDS=${ENABLE_LEADERBOARDS:-true}
ENABLE_ELO_RATINGS=${ENABLE_ELO_RATINGS:-true}
DEFAULT_ELO_K_FACTOR=${DEFAULT_ELO_K_FACTOR:-32}
TRAINING_DATA_COLLECTION=${TRAINING_DATA_COLLECTION:-true}
ARENA_MODE_ENABLED=${ARENA_MODE_ENABLED:-true}
EOF

    print_success "Configuration files created"
    print_info "Config location: /opt/uniaugment/config/.env.distributed"
}

setup_sway_compatibility() {
    print_header "Setting up Sway Compatibility"
    
    # Sway uses Wayland, Docker needs some special configuration
    print_info "Configuring Docker for Wayland/Sway..."
    
    # Create systemd override for Docker
    mkdir -p /etc/systemd/system/docker.service.d
    cat > /etc/systemd/system/docker.service.d/override.conf << EOF
[Service]
Environment="DOCKER_BUILDKIT=1"
EOF
    
    systemctl daemon-reload
    systemctl restart docker
    
    print_success "Sway compatibility configured"
}

create_docker_compose_api() {
    print_header "Generating Docker Compose - API Server"

    cat > /opt/uniaugment/compose/docker-compose.arch-api.yml << 'EOF'
version: '3.8'

services:
  uniaugment-api:
    image: uniaugment:full
    container_name: uniaugment-api
    ports:
      - "8000:8000"
    environment:
      - STACK_TYPE=full
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=redis://redis:6379/0
      - WEAVIATE_URL=${WEAVIATE_URL}
      - JWT_SECRET_KEY=${JWT_SECRET_KEY}
      - LOG_LEVEL=${LOG_LEVEL}
    networks:
      - uniaugment-local
      - uniaugment-distributed
    depends_on:
      redis:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    container_name: uniaugment-redis
    ports:
      - "6379:6379"
    command: redis-server --appendonly yes --requirepass ${REDIS_PASSWORD}
    volumes:
      - redis-data:/data
    networks:
      - uniaugment-local
      - uniaugment-distributed
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 30s
      timeout: 10s
      retries: 3
    restart: unless-stopped

  prometheus:
    image: prom/prometheus:latest
    container_name: uniaugment-prometheus
    ports:
      - "9090:9090"
    volumes:
      - /opt/uniaugment/monitoring/prometheus.yml:/etc/prometheus/prometheus.yml:ro
      - prometheus-data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
    networks:
      - uniaugment-local
      - uniaugment-distributed
    restart: unless-stopped

  node-exporter:
    image: prom/node-exporter:latest
    container_name: uniaugment-node-exporter
    ports:
      - "9100:9100"
    volumes:
      - /proc:/host/proc:ro
      - /sys:/host/sys:ro
      - /:/rootfs:ro
    command:
      - '--path.procfs=/host/proc'
      - '--path.sysfs=/host/sys'
      - '--collector.filesystem.mount-points-exclude=^/(sys|proc|dev|host|etc)($$|/)'
    networks:
      - uniaugment-local
      - uniaugment-distributed
    restart: unless-stopped

volumes:
  redis-data:
  prometheus-data:

networks:
  uniaugment-local:
    driver: bridge
  uniaugment-distributed:
    driver: overlay
    driver_opts:
      com.docker.network.driver.overlay.vxlanid: "4096"
EOF

    print_success "Docker Compose API file generated"
}

create_docker_compose_workers() {
    print_header "Generating Docker Compose - Workers"

    cat > /opt/uniaugment/compose/docker-compose.arch-workers.yml << 'EOF'
version: '3.8'

services:
  celery-worker-1:
    image: uniaugment:full
    container_name: uniaugment-celery-worker-1
    command: celery -A src.core.celery_app worker --loglevel=info --concurrency=2 -n worker1@%h
    environment:
      - CELERY_BROKER_URL=redis://:${REDIS_PASSWORD}@${ARCH_HOST_1}:6379/0
      - DATABASE_URL=${DATABASE_URL}
      - WEAVIATE_URL=${WEAVIATE_URL}
      - LOG_LEVEL=${LOG_LEVEL}
    networks:
      - uniaugment-distributed
    depends_on:
      - redis
    restart: unless-stopped

  celery-worker-2:
    image: uniaugment:full
    container_name: uniaugment-celery-worker-2
    command: celery -A src.core.celery_app worker --loglevel=info --concurrency=2 -n worker2@%h
    environment:
      - CELERY_BROKER_URL=redis://:${REDIS_PASSWORD}@${ARCH_HOST_1}:6379/0
      - DATABASE_URL=${DATABASE_URL}
      - WEAVIATE_URL=${WEAVIATE_URL}
      - LOG_LEVEL=${LOG_LEVEL}
    networks:
      - uniaugment-distributed
    depends_on:
      - redis
    restart: unless-stopped

  flower:
    image: mher/flower:latest
    container_name: uniaugment-flower
    ports:
      - "5555:5555"
    environment:
      - CELERY_BROKER_URL=redis://:${REDIS_PASSWORD}@${ARCH_HOST_1}:6379/0
      - CELERY_RESULT_BACKEND=redis://:${REDIS_PASSWORD}@${ARCH_HOST_1}:6379/0
    networks:
      - uniaugment-distributed
    restart: unless-stopped

  grafana:
    image: grafana/grafana:latest
    container_name: uniaugment-grafana
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=${GRAFANA_PASSWORD:-admin}
      - GF_INSTALL_PLUGINS=grafana-piechart-panel
    volumes:
      - grafana-data:/var/lib/grafana
      - /opt/uniaugment/monitoring/grafana/provisioning:/etc/grafana/provisioning:ro
    networks:
      - uniaugment-distributed
    restart: unless-stopped

  loki:
    image: grafana/loki:latest
    container_name: uniaugment-loki
    ports:
      - "3100:3100"
    volumes:
      - /opt/uniaugment/monitoring/loki-config.yml:/etc/loki/local-config.yml:ro
      - loki-data:/loki
    command: -config.file=/etc/loki/local-config.yml
    networks:
      - uniaugment-distributed
    restart: unless-stopped

  promtail:
    image: grafana/promtail:latest
    container_name: uniaugment-promtail
    volumes:
      - /var/log:/var/log:ro
      - /opt/uniaugment/monitoring/promtail-config.yml:/etc/promtail/config.yml:ro
    command: -config.file=/etc/promtail/config.yml
    networks:
      - uniaugment-distributed
    restart: unless-stopped

volumes:
  grafana-data:
  loki-data:

networks:
  uniaugment-distributed:
    driver: overlay
    driver_opts:
      com.docker.network.driver.overlay.vxlanid: "4096"
EOF

    print_success "Docker Compose Workers file generated"
}

create_startup_script() {
    print_header "Creating Startup Script"

    cat > /opt/uniaugment/start-services.sh << 'EOF'
#!/bin/bash

# Load environment
source /opt/uniaugment/config/.env.distributed

# Start Docker services based on machine role
case $MACHINE_ROLE in
    api-server)
        echo "Starting API Server + Redis + Prometheus..."
        docker-compose -f /opt/uniaugment/compose/docker-compose.arch-api.yml up -d
        ;;
    workers)
        echo "Starting Celery Workers + Grafana..."
        docker-compose -f /opt/uniaugment/compose/docker-compose.arch-workers.yml up -d
        ;;
    custom)
        echo "Starting custom configuration..."
        docker-compose -f /opt/uniaugment/compose/docker-compose.custom.yml up -d
        ;;
esac

echo "Services started successfully"
docker ps
EOF

    chmod +x /opt/uniaugment/start-services.sh
    print_success "Startup script created"
}

create_systemd_service() {
    print_header "Creating Systemd Service"
    
    cat > /etc/systemd/system/uniaugment.service << EOF
[Unit]
Description=UniAugment Docker Services
After=docker.service
Requires=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
ExecStart=/opt/uniaugment/start-services.sh
ExecStop=/usr/bin/docker-compose -f /opt/uniaugment/compose/docker-compose.arch-*.yml down
Restart=on-failure
RestartSec=10s

[Install]
WantedBy=multi-user.target
EOF
    
    systemctl daemon-reload
    systemctl enable uniaugment
    
    print_success "Systemd service created and enabled"
}

install_monitoring_tools() {
    print_header "Installing Monitoring Tools"

    pacman -S --noconfirm htop iotop nethogs
    print_success "Monitoring tools installed"
}

run_database_migrations() {
    print_header "Running Database Migrations"

    # Only run migrations on API server (where FastAPI runs)
    if [ "$MACHINE_ROLE" != "api-server" ]; then
        print_info "Skipping migrations (not API server)"
        return
    fi

    # Check if Agent Studio is enabled
    if [ "$AGENT_STUDIO_ENABLED" != "true" ]; then
        print_info "Agent Studio disabled, skipping Phase 1 migrations"
        return
    fi

    print_info "Waiting for PostgreSQL to be ready..."
    sleep 10

    # Wait for PostgreSQL to be ready (max 60 seconds)
    local max_attempts=30
    local attempt=0
    while [ $attempt -lt $max_attempts ]; do
        if docker exec -i uniaugment-postgres pg_isready -U uniaugment &> /dev/null; then
            print_success "PostgreSQL is ready"
            break
        fi
        attempt=$((attempt + 1))
        sleep 2
    done

    if [ $attempt -eq $max_attempts ]; then
        print_warning "PostgreSQL not ready, migrations may fail"
    fi

    # Run Alembic migrations
    print_info "Running Alembic migrations..."
    if docker exec -i uniaugment-api alembic upgrade head; then
        print_success "Database migrations complete"
    else
        print_warning "Migration failed - may need to run manually"
        print_info "To run manually: docker exec -it uniaugment-api alembic upgrade head"
    fi
}

print_summary() {
    print_header "Setup Complete!"
    
    echo ""
    echo "Machine Configuration:"
    echo "  Name: $MACHINE_NAME"
    echo "  Role: $MACHINE_ROLE"
    echo "  IP: $MACHINE_IP"
    echo ""
    echo "Network Configuration:"
    echo "  Windows Host: $WINDOWS_HOST"
    echo "  Arch Host 1: $ARCH_HOST_1"
    echo "  Arch Host 2: $ARCH_HOST_2"
    echo ""
    echo "Next Steps:"
    echo "  1. Log out and log back in for docker group changes"
    echo "  2. Copy docker-compose files to /opt/uniaugment/compose/"
    echo "  3. Run: systemctl start uniaugment"
    echo "  4. Check status: docker ps"
    echo ""
    echo "Configuration file: /opt/uniaugment/config/.env.distributed"
    echo ""
}

################################################################################
# Main Execution
################################################################################

main() {
    print_header "UniAugment - Arch Linux Setup"

    check_root
    check_arch_linux
    install_docker
    configure_docker_user
    configure_networking
    create_docker_network
    select_machine_role
    configure_agent_studio
    configure_agentic_university
    create_config_files
    setup_sway_compatibility

    # Generate appropriate docker-compose files based on role
    if [ "$MACHINE_ROLE" = "api-server" ]; then
        create_docker_compose_api
    elif [ "$MACHINE_ROLE" = "workers" ]; then
        create_docker_compose_workers
    fi

    create_startup_script
    create_systemd_service
    install_monitoring_tools

    # Run database migrations if Agent Studio or University System is enabled
    if [ "$AGENT_STUDIO_ENABLED" = "true" ] || [ "$UNIVERSITY_ENABLED" = "true" ]; then
        if [ "$MACHINE_ROLE" = "api-server" ]; then
            print_info "Enhanced features enabled - migrations will run after services start"
            print_info "To run migrations manually: docker exec -it uniaugment-api alembic upgrade head"
        fi
    fi

    print_summary
}

main "$@"

