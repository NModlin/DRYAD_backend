#!/bin/bash

################################################################################
# UniAugment - Dynamic Deployment Automation Script
# Supports 3, 6, or custom machine configurations
# 
# This script dynamically adapts configuration based on user-specified machine count
################################################################################

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration variables
MACHINE_COUNT=""
BASE_IP=""
MACHINE_NAME=""
MACHINE_IP=""
MACHINE_ROLE=""
DEPLOYMENT_TYPE=""
ROLE_ASSIGNMENTS=()

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

detect_os() {
    if [[ -f /etc/os-release ]]; then
        if grep -q "Arch Linux" /etc/os-release; then
            OS="arch"
        elif grep -q "Ubuntu" /etc/os-release; then
            OS="ubuntu"
        elif grep -q "CentOS" /etc/os-release; then
            OS="centos"
        else
            OS="linux"
        fi
    else
        OS="unknown"
    fi
    print_success "Detected OS: $OS"
}

get_machine_count() {
    print_header "Deployment Configuration"
    
    echo "Select deployment type:"
    echo "1) 3-Machine Setup (Basic)"
    echo "2) 6-Machine Setup (Development/Testing)"
    echo "3) Custom Configuration"
    
    read -p "Enter choice (1-3): " DEPLOYMENT_CHOICE
    
    case $DEPLOYMENT_CHOICE in
        1)
            MACHINE_COUNT=3
            DEPLOYMENT_TYPE="basic"
            print_success "Selected: 3-Machine Basic Setup"
            ;;
        2)
            MACHINE_COUNT=6
            DEPLOYMENT_TYPE="development"
            print_success "Selected: 6-Machine Development Setup"
            ;;
        3)
            read -p "Enter number of machines (minimum 2): " CUSTOM_COUNT
            if [[ $CUSTOM_COUNT -lt 2 ]]; then
                print_error "Minimum 2 machines required"
                exit 1
            fi
            MACHINE_COUNT=$CUSTOM_COUNT
            DEPLOYMENT_TYPE="custom"
            print_success "Selected: Custom $MACHINE_COUNT-Machine Setup"
            ;;
        *)
            print_error "Invalid selection"
            exit 1
            ;;
    esac
}

get_network_configuration() {
    print_header "Network Configuration"
    
    read -p "Enter base IP address (e.g., 192.168.1): " BASE_IP
    read -p "Enter starting IP octet (e.g., 100): " START_OCTET
    
    # Validate IP format
    if ! [[ $BASE_IP =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
        print_error "Invalid base IP format"
        exit 1
    fi
    
    # Generate IP addresses for all machines
    MACHINE_IPS=()
    for ((i=0; i<MACHINE_COUNT; i++)); do
        IP_OCTET=$((START_OCTET + i))
        MACHINE_IPS+=("$BASE_IP.$IP_OCTET")
    done
    
    print_info "Generated IP addresses: ${MACHINE_IPS[*]}"
    
    # Get current machine details
    read -p "Enter this machine's hostname: " MACHINE_NAME
    read -p "Enter this machine's IP address: " MACHINE_IP
    
    # Validate current machine IP is in the list
    if [[ ! " ${MACHINE_IPS[@]} " =~ " ${MACHINE_IP} " ]]; then
        print_warning "Current machine IP not in generated list. Continuing anyway."
    fi
}

assign_roles_dynamically() {
    print_header "Role Assignment"
    
    # Define role templates based on deployment type
    case $DEPLOYMENT_TYPE in
        "basic")
            ROLES=("api-server" "database-server" "worker-server")
            ;;
        "development")
            ROLES=("api-server" "database-server" "worker-server" "monitoring-server" "development-server" "testing-server")
            ;;
        "custom")
            # For custom deployments, assign roles based on machine count
            if [[ $MACHINE_COUNT -eq 2 ]]; then
                ROLES=("api-database-server" "worker-monitoring-server")
            elif [[ $MACHINE_COUNT -eq 3 ]]; then
                ROLES=("api-server" "database-server" "worker-server")
            elif [[ $MACHINE_COUNT -eq 4 ]]; then
                ROLES=("api-server" "database-server" "worker-server" "monitoring-server")
            elif [[ $MACHINE_COUNT -eq 5 ]]; then
                ROLES=("api-server" "database-server" "worker-server" "monitoring-server" "development-server")
            else
                # For 6+ machines, use development pattern with extras as additional workers
                ROLES=("api-server" "database-server" "worker-server" "monitoring-server" "development-server" "testing-server")
                # Add extra worker servers for machines beyond 6
                for ((i=6; i<MACHINE_COUNT; i++)); do
                    ROLES+=("extra-worker-$((i-5))")
                done
            fi
            ;;
    esac
    
    # Find current machine's role based on IP position
    for ((i=0; i<${#MACHINE_IPS[@]}; i++)); do
        if [[ "${MACHINE_IPS[$i]}" == "$MACHINE_IP" ]]; then
            MACHINE_ROLE="${ROLES[$i]}"
            break
        fi
    done
    
    if [[ -z "$MACHINE_ROLE" ]]; then
        print_warning "Could not auto-assign role. Manual selection required."
        select_role_manually
    else
        print_success "Assigned role: $MACHINE_ROLE"
    fi
    
    # Store all role assignments for configuration
    for ((i=0; i<${#MACHINE_IPS[@]}; i++)); do
        ROLE_ASSIGNMENTS+=("${MACHINE_IPS[$i]}:${ROLES[$i]}")
    done
}

select_role_manually() {
    print_header "Manual Role Selection"
    
    echo "Available roles:"
    echo "1) API Server (FastAPI + Redis + Prometheus)"
    echo "2) Database Server (PostgreSQL + Weaviate)"
    echo "3) Worker Server (Celery Workers + Flower)"
    echo "4) Monitoring Server (Grafana + Loki)"
    echo "5) Development Server (Dev API + Test DB)"
    echo "6) Testing Server (QA API + Testing Tools)"
    echo "7) Combined Server (Multiple services)"
    
    read -p "Select role (1-7): " ROLE_CHOICE
    
    case $ROLE_CHOICE in
        1) MACHINE_ROLE="api-server" ;;
        2) MACHINE_ROLE="database-server" ;;
        3) MACHINE_ROLE="worker-server" ;;
        4) MACHINE_ROLE="monitoring-server" ;;
        5) MACHINE_ROLE="development-server" ;;
        6) MACHINE_ROLE="testing-server" ;;
        7) MACHINE_ROLE="combined-server" ;;
        *) 
            print_error "Invalid selection"
            exit 1
            ;;
    esac
    
    print_success "Selected role: $MACHINE_ROLE"
}

calculate_resource_allocation() {
    print_header "Resource Allocation"
    
    # Calculate memory allocation based on machine count and role
    case $MACHINE_ROLE in
        "api-server")
            MEMORY_LIMIT="2G"
            MEMORY_RESERVATION="1G"
            ;;
        "database-server")
            MEMORY_LIMIT="3G"
            MEMORY_RESERVATION="2G"
            ;;
        "worker-server")
            MEMORY_LIMIT="1G"
            MEMORY_RESERVATION="512M"
            ;;
        "monitoring-server")
            MEMORY_LIMIT="1G"
            MEMORY_RESERVATION="512M"
            ;;
        "development-server")
            MEMORY_LIMIT="2G"
            MEMORY_RESERVATION="1G"
            ;;
        "testing-server")
            MEMORY_LIMIT="2G"
            MEMORY_RESERVATION="1G"
            ;;
        "combined-server")
            # For combined roles in smaller deployments
            if [[ $MACHINE_COUNT -le 3 ]]; then
                MEMORY_LIMIT="4G"
                MEMORY_RESERVATION="2G"
            else
                MEMORY_LIMIT="3G"
                MEMORY_RESERVATION="1.5G"
            fi
            ;;
        "extra-worker-"*)
            MEMORY_LIMIT="1G"
            MEMORY_RESERVATION="512M"
            ;;
        *)
            MEMORY_LIMIT="2G"
            MEMORY_RESERVATION="1G"
            ;;
    esac
    
    print_info "Memory allocation: Limit=$MEMORY_LIMIT, Reservation=$MEMORY_RESERVATION"
}

install_docker() {
    print_header "Installing Docker"
    
    if command -v docker &> /dev/null; then
        print_warning "Docker already installed"
        docker --version
    else
        print_info "Installing Docker..."
        
        case $OS in
            "arch")
                pacman -Syu --noconfirm
                pacman -S --noconfirm docker docker-compose
                ;;
            "ubuntu")
                apt-get update
                apt-get install -y docker.io docker-compose
                ;;
            "centos")
                yum install -y docker docker-compose
                ;;
            *)
                print_error "Unsupported OS for automated Docker installation"
                print_info "Please install Docker manually and run this script again"
                exit 1
                ;;
        esac
        
        # Enable and start Docker
        systemctl enable docker
        systemctl start docker
        
        print_success "Docker installed and started"
    fi
}

configure_docker_networking() {
    print_header "Configuring Docker Networking"
    
    # Set hostname
    hostnamectl set-hostname "$MACHINE_NAME"
    print_success "Hostname set to $MACHINE_NAME"
    
    # Create insecure registries list from all machine IPs
    INSECURE_REGISTRIES=""
    for ip in "${MACHINE_IPS[@]}"; do
        INSECURE_REGISTRIES+="\"$ip:5000\","
    done
    INSECURE_REGISTRIES="${INSECURE_REGISTRIES%,}"  # Remove trailing comma
    
    # Create docker daemon config
    cat > /etc/docker/daemon.json << EOF
{
    "storage-driver": "overlay2",
    "log-driver": "json-file",
    "log-opts": {
        "max-size": "10m",
        "max-file": "3"
    },
    "insecure-registries": [$INSECURE_REGISTRIES]
}
EOF
    
    systemctl restart docker
    print_success "Docker networking configured for $MACHINE_COUNT-machine deployment"
}

create_dynamic_configuration() {
    print_header "Creating Dynamic Configuration"
    
    # Create config directory
    mkdir -p /opt/uniaugment/config
    mkdir -p /opt/uniaugment/data
    mkdir -p /opt/uniaugment/logs
    
    # Generate environment file with dynamic configuration
    cat > /opt/uniaugment/config/.env.dynamic << EOF
# UniAugment Dynamic Deployment Configuration
# Machine Count: $MACHINE_COUNT
# Deployment Type: $DEPLOYMENT_TYPE

STACK_TYPE=full
MACHINE_NAME=$MACHINE_NAME
MACHINE_ROLE=$MACHINE_ROLE
MACHINE_COUNT=$MACHINE_COUNT
DEPLOYMENT_TYPE=$DEPLOYMENT_TYPE

# Dynamic IP Configuration
BASE_IP=$BASE_IP
MACHINE_IPS=(${MACHINE_IPS[@]})

# Role Assignments
$(for assignment in "${ROLE_ASSIGNMENTS[@]}"; do
    echo "# $assignment"
done)

# Service Discovery - Auto-generated based on roles
$(generate_service_discovery)

# Resource Allocation
MEMORY_LIMIT=$MEMORY_LIMIT
MEMORY_RESERVATION=$MEMORY_RESERVATION

# Security
JWT_SECRET_KEY=$(openssl rand -base64 32)
POSTGRES_PASSWORD=$(openssl rand -base64 32)
REDIS_PASSWORD=$(openssl rand -base64 32)

# Logging
LOG_LEVEL=INFO

# Agent Creation Studio (default enabled)
AGENT_CREATION_STUDIO_ENABLED=true
AGENT_VISUAL_CUSTOMIZATION=true
AGENT_BEHAVIORAL_CUSTOMIZATION=true

# Agentic University System (default enabled)
AGENTIC_UNIVERSITY_ENABLED=true
UNIVERSITY_MANAGEMENT_ENABLED=true
CURRICULUM_SYSTEM_ENABLED=true
COMPETITION_SYSTEM_ENABLED=true
EOF

    print_success "Dynamic configuration file created"
    print_info "Config location: /opt/uniaugment/config/.env.dynamic"
}

generate_service_discovery() {
    # This function generates service discovery configuration based on roles
    for assignment in "${ROLE_ASSIGNMENTS[@]}"; do
        IP=$(echo $assignment | cut -d: -f1)
        ROLE=$(echo $assignment | cut -d: -f2)
        
        case $ROLE in
            "api-server")
                echo "PRIMARY_API_URL=http://$IP:8000"
                echo "REDIS_URL=redis://$IP:6379/0"
                echo "PROMETHEUS_URL=http://$IP:9090"
                ;;
            "database-server")
                echo "DATABASE_URL=postgresql://uniaugment:\${POSTGRES_PASSWORD}@$IP:5432/uniaugment"
                echo "WEAVIATE_URL=http://$IP:8080"
                echo "PGADMIN_URL=http://$IP:5050"
                ;;
            "worker-server")
                echo "WORKER_URL=$IP"
                echo "FLOWER_URL=http://$IP:5555"
                ;;
            "monitoring-server")
                echo "GRAFANA_URL=http://$IP:3000"
                echo "LOKI_URL=http://$IP:3100"
                ;;
            "development-server")
                echo "DEV_API_URL=http://$IP:8001"
                echo "TEST_DATABASE_URL=postgresql://uniaugment:\${POSTGRES_PASSWORD}@$IP:5433/uniaugment-dev"
                ;;
            "testing-server")
                echo "QA_API_URL=http://$IP:8002"
                echo "TEST_DASHBOARD_URL=http://$IP:3001"
                ;;
        esac
    done
}

generate_docker_compose() {
    print_header "Generating Docker Compose Configuration"
    
    # Generate appropriate compose file based on role
    case $MACHINE_ROLE in
        "api-server")
            generate_api_compose
            ;;
        "database-server")
            generate_database_compose
            ;;
        "worker-server")
            generate_worker_compose
            ;;
        "monitoring-server")
            generate_monitoring_compose
            ;;
        "development-server")
            generate_development_compose
            ;;
        "testing-server")
            generate_testing_compose
            ;;
        "combined-server")
            generate_combined_compose
            ;;
        "extra-worker-"*)
            generate_extra_worker_compose
            ;;
        *)
            print_error "Unknown role: $MACHINE_ROLE"
            exit 1
            ;;
    esac
}

generate_api_compose() {
    cat > /opt/uniaugment/compose/docker-compose.api-dynamic.yml << 'EOF'
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
    deploy:
      resources:
        limits:
          memory: ${MEMORY_LIMIT}
        reservations:
          memory: ${MEMORY_RESERVATION}
    networks:
      - uniaugment-dynamic
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
      - uniaugment-dynamic
    restart: unless-stopped

  prometheus:
    image: prom/prometheus:latest
    container_name: uniaugment-prometheus
    ports:
      - "9090:9090"
    volumes:
      - prometheus-data:/prometheus
    networks:
      - uniaugment-dynamic
    restart: unless-stopped

volumes:
  redis-data:
  prometheus-data:

networks:
  uniaugment-dynamic:
    driver: overlay
EOF

    print_success "API server Docker Compose generated"
}

# Similar functions for other roles would be defined here...
# generate_database_compose(), generate_worker_compose(), etc.

create_startup_script() {
    print_header "Creating Dynamic Startup Script"
    
    cat > /opt/uniaugment/start-dynamic.sh << 'EOF'
#!/bin/bash

# Load dynamic environment
source /opt/uniaugment/config/.env.dynamic

echo "Starting UniAugment Dynamic Deployment"
echo "Machine Count: $MACHINE_COUNT"
echo "Deployment Type: $DEPLOYMENT_TYPE"
echo "Machine Role: $MACHINE_ROLE"

# Start services based on role
case $MACHINE_ROLE in
    api-server)
        docker-compose -f /opt/uniaugment/compose/docker-compose.api-dynamic.yml up -d
        ;;
    database-server)
        docker-compose -f /opt/uniaugment/compose/docker-compose.database-dynamic.yml up -d
        ;;
    worker-server)
        docker-compose -f /opt/uniaugment/compose/docker-compose.worker-dynamic.yml up -d
        ;;
    monitoring-server)
        docker-compose -f /opt/uniaugment/compose/docker-compose.monitoring-dynamic.yml up -d
        ;;
    development-server)
        docker-compose -f /opt/uniaugment/compose/docker-compose.development-dynamic.yml up -d
        ;;
    testing-server)
        docker-compose -f /opt/uniaugment/compose/docker-compose.testing-dynamic.yml up -d
        ;;
    combined-server)
        docker-compose -f /opt/uniaugment/compose/docker-compose.combined-dynamic.yml up -d
        ;;
    extra-worker-*)
        docker-compose -f /opt/uniaugment/compose/docker-compose.extra-worker-dynamic.yml up -d
        ;;
    *)
        echo "Unknown role: $MACHINE_ROLE"
        exit 1
        ;;
esac

echo "Services started successfully"
docker ps
EOF

    chmod +x /opt/uniaugment/start-dynamic.sh
    print_success "Dynamic startup script created"
}

print_deployment_summary() {
    print_header "Dynamic Deployment Setup Complete!"
    
    echo ""
    echo "Deployment Summary:"
    echo "  Machine Count: $MACHINE_COUNT"
    echo "  Deployment Type: $DEPLOYMENT_TYPE"
    echo "  Machine Name: $MACHINE_NAME"
    echo "  Machine IP: $MACHINE_IP"
    echo "  Machine Role: $MACHINE_ROLE"
    echo ""
    echo "Network Configuration:"
    for ((i=0; i<${#MACHINE_IPS[@]}; i++)); do
        echo "  Machine $((i+1)): ${MACHINE_IPS[$i]} - ${ROLE_ASSIGNMENTS[$i]#*:}"
    done
    echo ""
    echo "Resource Allocation:"
    echo "  Memory Limit: $MEMORY_LIMIT"
    echo "  Memory Reservation: $MEMORY_RESERVATION"
    echo ""
    echo "Next Steps:"
    echo "  1. Run setup on all $MACHINE_COUNT machines"
    echo "  2. Start services in order (database first)"
    echo "  3. Verify deployment with health checks"
    echo ""
    echo "Configuration file: /opt/uniaugment/config/.env.dynamic"
    echo ""
}

################################################################################
# Main Execution
################################################################################

main() {
    print_header "UniAugment Dynamic Deployment Setup"
    
    check_root
    detect_os
    get_machine_count
    get_network_configuration
    assign_roles_dynamically
    calculate_resource_allocation
    install_docker
    configure_docker_networking
    create_dynamic_configuration
    generate_docker_compose
    create_startup_script
    
    print_deployment_summary
}

main "$@"