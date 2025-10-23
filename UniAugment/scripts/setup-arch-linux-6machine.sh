#!/bin/bash

################################################################################
# UniAugment - Arch Linux Setup Script for 6-Machine Deployment
# For Dell OptiPlex PCs with 8GB RAM
# 
# This script sets up Docker and Docker Compose on Arch Linux
# and configures the machine for 6-machine distributed UniAugment deployment
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
MACHINE_IP=""
API_HOST_1=""
DB_HOST_2=""
WORKER_HOST_3=""
MONITOR_HOST_4=""
DEV_HOST_5=""
TEST_HOST_6=""

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

configure_networking_6machine() {
    print_header "Configuring 6-Machine Networking"
    
    read -p "Enter this machine's hostname (e.g., optiplex-1, optiplex-2): " MACHINE_NAME
    read -p "Enter this machine's IP address (e.g., 192.168.1.100): " MACHINE_IP
    read -p "Enter Machine 1 (API Server) IP address: " API_HOST_1
    read -p "Enter Machine 2 (Database Server) IP address: " DB_HOST_2
    read -p "Enter Machine 3 (Worker Server) IP address: " WORKER_HOST_3
    read -p "Enter Machine 4 (Monitoring Server) IP address: " MONITOR_HOST_4
    read -p "Enter Machine 5 (Development Server) IP address: " DEV_HOST_5
    read -p "Enter Machine 6 (Testing Server) IP address: " TEST_HOST_6
    
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
        "$API_HOST_1:5000",
        "$DB_HOST_2:5000",
        "$WORKER_HOST_3:5000",
        "$MONITOR_HOST_4:5000",
        "$DEV_HOST_5:5000",
        "$TEST_HOST_6:5000"
    ]
}
EOF
    
    systemctl restart docker
    print_success "Docker networking configured for 6-machine deployment"
}

create_docker_network() {
    print_header "Creating Docker Networks"
    
    # Create overlay network for distributed deployment
    docker network create --driver overlay --attachable uniaugment-6machine || true
    print_success "Created 6-machine distributed network"
    
    # Create bridge network for local services
    docker network create --driver bridge uniaugment-local || true
    print_success "Created local network"
}

select_machine_role_6machine() {
    print_header "Select 6-Machine Role"
    
    echo "This machine will run:"
    echo "1) Primary API Server + Redis + Prometheus (Machine 1)"
    echo "2) Database Server - PostgreSQL + Weaviate (Machine 2)"
    echo "3) Worker Server - Celery Workers + Flower (Machine 3)"
    echo "4) Monitoring Server - Grafana + Loki (Machine 4)"
    echo "5) Development Server - Dev API + Test DB (Machine 5)"
    echo "6) Testing Server - QA API + Testing Tools (Machine 6)"
    
    read -p "Select role (1-6): " ROLE_CHOICE
    
    case $ROLE_CHOICE in
        1)
            MACHINE_ROLE="api-server"
            print_success "Selected: Primary API Server + Redis + Prometheus"
            ;;
        2)
            MACHINE_ROLE="database-server"
            print_success "Selected: Database Server - PostgreSQL + Weaviate"
            ;;
        3)
            MACHINE_ROLE="worker-server"
            print_success "Selected: Worker Server - Celery Workers + Flower"
            ;;
        4)
            MACHINE_ROLE="monitoring-server"
            print_success "Selected: Monitoring Server - Grafana + Loki"
            ;;
        5)
            MACHINE_ROLE="development-server"
            print_success "Selected: Development Server - Dev API + Test DB"
            ;;
        6)
            MACHINE_ROLE="testing-server"
            print_success "Selected: Testing Server - QA API + Testing Tools"
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

create_config_files_6machine() {
    print_header "Creating 6-Machine Configuration Files"
    
    # Create config directory
    mkdir -p /opt/uniaugment/config
    mkdir -p /opt/uniaugment/data
    mkdir -p /opt/uniaugment/logs
    
    # Create environment file
    cat > /opt/uniaugment/config/.env.6machine << EOF
# UniAugment 6-Machine Deployment Configuration
STACK_TYPE=full
MACHINE_NAME=$MACHINE_NAME
MACHINE_ROLE=$MACHINE_ROLE

# 6-Machine Network Configuration
API_HOST_1=$API_HOST_1
DB_HOST_2=$DB_HOST_2
WORKER_HOST_3=$WORKER_HOST_3
MONITOR_HOST_4=$MONITOR_HOST_4
DEV_HOST_5=$DEV_HOST_5
TEST_HOST_6=$TEST_HOST_6

# Database (on Machine 2)
DATABASE_URL=postgresql://uniaugment:changeme@$DB_HOST_2:5432/uniaugment
TEST_DATABASE_URL=postgresql://uniaugment:changeme@$DEV_HOST_5:5433/uniaugment-dev

# Redis (on Machine 1)
REDIS_URL=redis://$API_HOST_1:6379/0
CELERY_BROKER_URL=redis://$API_HOST_1:6379/0

# Weaviate (on Machine 2)
WEAVIATE_URL=http://$DB_HOST_2:8080

# Monitoring
PROMETHEUS_URL=http://$API_HOST_1:9090
GRAFANA_URL=http://$MONITOR_HOST_4:3000
LOKI_URL=http://$MONITOR_HOST_4:3100

# Development/Testing
DEV_API_URL=http://$DEV_HOST_5:8001
QA_API_URL=http://$TEST_HOST_6:8002

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

    print_success "6-machine configuration files created"
    print_info "Config location: /opt/uniaugment/config/.env.6machine"
}

# [Rest of the functions remain similar but adapted for 6-machine roles...]

create_docker_compose_api_6machine() {
    print_header "Generating Docker Compose - API Server (Machine 1)"
    
    cat > /opt/uniaugment/compose/docker-compose.api-6machine.yml << 'EOF'
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
      - uniaugment-6machine
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
      - uniaugment-6machine
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
      - uniaugment-6machine
    restart: unless-stopped

volumes:
  redis-data:
  prometheus-data:

networks:
  uniaugment-local:
    driver: bridge
  uniaugment-6machine:
    driver: overlay
    driver_opts:
      com.docker.network.driver.overlay.vxlanid: "4096"
EOF

    print_success "Docker Compose API file generated for 6-machine deployment"
}

# [Additional Docker Compose files for other roles would be created here...]

print_summary_6machine() {
    print_header "6-Machine Setup Complete!"
    
    echo ""
    echo "Machine Configuration:"
    echo "  Name: $MACHINE_NAME"
    echo "  Role: $MACHINE_ROLE"
    echo "  IP: $MACHINE_IP"
    echo ""
    echo "6-Machine Network Configuration:"
    echo "  API Server (M1): $API_HOST_1"
    echo "  Database Server (M2): $DB_HOST_2"
    echo "  Worker Server (M3): $WORKER_HOST_3"
    echo "  Monitoring Server (M4): $MONITOR_HOST_4"
    echo "  Development Server (M5): $DEV_HOST_5"
    echo "  Testing Server (M6): $TEST_HOST_6"
    echo ""
    echo "Next Steps:"
    echo "  1. Log out and log back in for docker group changes"
    echo "  2. Copy docker-compose files to /opt/uniaugment/compose/"
    echo "  3. Run: systemctl start uniaugment"
    echo "  4. Check status: docker ps"
    echo ""
    echo "Configuration file: /opt/uniaugment/config/.env.6machine"
    echo ""
}

################################################################################
# Main Execution
################################################################################

main() {
    print_header "UniAugment - 6-Machine Arch Linux Setup"
    
    check_root
    check_arch_linux
    install_docker
    configure_docker_user
    configure_networking_6machine
    create_docker_network
    select_machine_role_6machine
    configure_agent_studio
    configure_agentic_university
    create_config_files_6machine
    
    # Generate appropriate docker-compose files based on role
    if [ "$MACHINE_ROLE" = "api-server" ]; then
        create_docker_compose_api_6machine
    # Additional role-specific compose file generation would go here
    fi
    
    # [Rest of main function remains similar...]
    
    print_summary_6machine
}

main "$@"