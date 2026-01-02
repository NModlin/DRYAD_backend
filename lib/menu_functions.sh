#!/bin/bash
# DRYAD.AI Enhanced Installation - Menu Functions
# Interactive menu system for user selections

# Source utilities if not already sourced
if [[ -z "$DRYAD_UTILS_LOADED" ]]; then
    source "$(dirname "${BASH_SOURCE[0]}")/utils.sh"
fi

# Global variables for selections
export DEPLOYMENT_CONFIG=""
export SELECTED_FRONTENDS=()
export OPTIONAL_COMPONENTS=()
export LLM_PROVIDER=""
export DOMAIN="localhost"
export OPENAI_API_KEY=""
export ANTHROPIC_API_KEY=""

# Display welcome screen
display_welcome() {
    clear
    print_header "🚀 DRYAD.AI Enhanced Installation System"
    
    cat << EOF
Welcome to the DRYAD.AI Enhanced Installation System!

This installer will help you set up DRYAD.AI with:
  • Multiple deployment configurations (minimal to GPU-accelerated)
  • Optional frontend applications (3 choices)
  • Monitoring & logging stacks
  • MCP Server support
  • Database options
  • And much more!

The installation is fully customizable - you choose what you need.

EOF
    
    read -p "Press Enter to continue..."
}

# Select deployment configuration
select_deployment_config() {
    print_header "Step 1: Select Deployment Configuration"
    
    cat << EOF
Choose the deployment configuration that best fits your needs:

1) Minimal       - Core API only (1-2GB RAM)
                   Perfect for: Testing, development, resource-constrained environments
                   
2) Basic         - Standard features (2-4GB RAM)
                   Perfect for: Small projects, personal use
                   
3) Development   - Hot reload + debugging (4-6GB RAM)
                   Perfect for: Active development, testing new features
                   
4) Full          - All services + Celery workers (6-8GB RAM)
                   Perfect for: Production use, background tasks
                   
5) Production    - Nginx + SSL + monitoring (8-10GB RAM)
                   Perfect for: Production deployment, public-facing
                   
6) Scalable      - Multi-worker + load balancing (10-12GB RAM)
                   Perfect for: High traffic, distributed workloads
                   
7) GPU           - GPU-accelerated ML (12GB+ RAM + GPU required)
                   Perfect for: Machine learning, heavy AI workloads

EOF
    
    local mem_available=$(get_available_memory)
    if [[ "$mem_available" != "unknown" ]]; then
        print_info "Available memory: ${mem_available}MB"
    fi
    
    while true; do
        read -p "Enter your choice (1-7) [2]: " choice
        choice=${choice:-2}
        
        case $choice in
            1) DEPLOYMENT_CONFIG="minimal"; break;;
            2) DEPLOYMENT_CONFIG="basic"; break;;
            3) DEPLOYMENT_CONFIG="development"; break;;
            4) DEPLOYMENT_CONFIG="full"; break;;
            5) DEPLOYMENT_CONFIG="production"; break;;
            6) DEPLOYMENT_CONFIG="scalable"; break;;
            7) DEPLOYMENT_CONFIG="gpu"; break;;
            *) print_error "Please enter a number between 1 and 7";;
        esac
    done
    
    print_success "Selected deployment: $DEPLOYMENT_CONFIG"
}

# Select frontend applications
select_frontends() {
    print_header "Step 2: Select Frontend Applications (Optional)"
    
    cat << EOF
Choose which frontend applications to install:
(You can select multiple by entering numbers separated by spaces, or 0 for none)

1) Dryads Console (Port 3001)
   - Quantum-inspired knowledge tree navigator
   - Multi-provider AI consultation
   - Memory Keeper system
   - Document viewer with Perplexity AI
   
2) DRYAD University UI (Port 3006)
   - Student/Faculty/Admin dashboards
   - Agent creation wizard
   - Competition system
   - Curriculum management
   
3) Writer Portal (Port 3000)
   - Next.js document management
   - RAG queries with citations
   - Real-time WebSocket progress
   - OAuth2 Google login

0) None - Skip frontend installation

EOF
    
    read -p "Enter your choices (e.g., '1 2' or '0'): " choices
    
    if [[ "$choices" == "0" ]]; then
        print_info "No frontends selected"
        return
    fi
    
    for choice in $choices; do
        case $choice in
            1) SELECTED_FRONTENDS+=("dryads-console");;
            2) SELECTED_FRONTENDS+=("university-ui");;
            3) SELECTED_FRONTENDS+=("writer-portal");;
            *) print_warning "Invalid choice: $choice (ignored)";;
        esac
    done
    
    if [[ ${#SELECTED_FRONTENDS[@]} -gt 0 ]]; then
        print_success "Selected frontends: ${SELECTED_FRONTENDS[*]}"
    fi
}

# Select optional components
select_optional_components() {
    print_header "Step 3: Select Optional Components"
    
    cat << EOF
Choose additional components to install:
(Enter numbers separated by spaces, or 0 for none)

Backend Enhancements:
1) Enable MCP Server - Model Context Protocol endpoint
2) PostgreSQL Database - Production-grade database (instead of SQLite)
3) Celery Workers - Background task processing (if not in deployment config)

Monitoring & Observability:
4) Prometheus + Grafana - Metrics and visualization
5) ELK Stack - Elasticsearch, Kibana, Fluentd logging
6) Full Metrics Suite - All exporters (cAdvisor, Node, Postgres, Redis)

0) None - Skip optional components

EOF
    
    read -p "Enter your choices (e.g., '1 4 5' or '0'): " choices
    
    if [[ "$choices" == "0" ]]; then
        print_info "No optional components selected"
        return
    fi
    
    for choice in $choices; do
        case $choice in
            1) OPTIONAL_COMPONENTS+=("mcp");;
            2) OPTIONAL_COMPONENTS+=("postgresql");;
            3) OPTIONAL_COMPONENTS+=("celery");;
            4) OPTIONAL_COMPONENTS+=("monitoring");;
            5) OPTIONAL_COMPONENTS+=("logging");;
            6) OPTIONAL_COMPONENTS+=("metrics");;
            *) print_warning "Invalid choice: $choice (ignored)";;
        esac
    done
    
    if [[ ${#OPTIONAL_COMPONENTS[@]} -gt 0 ]]; then
        print_success "Selected components: ${OPTIONAL_COMPONENTS[*]}"
    fi
}

# Configure LLM provider
configure_llm_provider() {
    print_header "Step 4: Configure LLM Provider"

    cat << EOF
Choose your LLM provider:

1) Mock       - Fake responses for testing (no API key needed)
2) OpenAI     - Use OpenAI GPT models (requires API key)
3) Anthropic  - Use Claude models (requires API key)
4) Ollama     - Local LLM (will download models)

EOF

    while true; do
        read -p "Enter your choice (1-4) [1]: " choice
        choice=${choice:-1}

        case $choice in
            1) LLM_PROVIDER="mock"; break;;
            2) LLM_PROVIDER="openai"; break;;
            3) LLM_PROVIDER="anthropic"; break;;
            4) LLM_PROVIDER="ollama"; break;;
            *) print_error "Please enter a number between 1 and 4";;
        esac
    done

    # Get API keys if needed
    if [[ "$LLM_PROVIDER" == "openai" ]]; then
        echo ""
        read -p "Enter your OpenAI API key: " OPENAI_API_KEY
        if [[ -z "$OPENAI_API_KEY" ]]; then
            print_warning "No API key provided. Falling back to mock provider."
            LLM_PROVIDER="mock"
        fi
    elif [[ "$LLM_PROVIDER" == "anthropic" ]]; then
        echo ""
        read -p "Enter your Anthropic API key: " ANTHROPIC_API_KEY
        if [[ -z "$ANTHROPIC_API_KEY" ]]; then
            print_warning "No API key provided. Falling back to mock provider."
            LLM_PROVIDER="mock"
        fi
    fi

    print_success "LLM provider: $LLM_PROVIDER"
}

# Configure domain
configure_domain() {
    print_header "Step 5: Configure Domain"

    echo ""
    read -p "Enter your domain (or press Enter for localhost): " DOMAIN
    DOMAIN=${DOMAIN:-localhost}

    print_success "Domain: $DOMAIN"
}

# Display confirmation screen
display_confirmation() {
    clear
    print_header "📋 Installation Summary - Please Confirm"

    echo ""
    echo "═══════════════════════════════════════════════════════════════"
    echo "                    INSTALLATION CONFIGURATION"
    echo "═══════════════════════════════════════════════════════════════"
    echo ""

    # Deployment config
    echo -e "${CYAN}Deployment Configuration:${NC} $DEPLOYMENT_CONFIG"
    echo ""

    # Frontends
    if [[ ${#SELECTED_FRONTENDS[@]} -gt 0 ]]; then
        echo -e "${CYAN}Frontend Applications:${NC}"
        for frontend in "${SELECTED_FRONTENDS[@]}"; do
            case $frontend in
                "dryads-console") echo "  • Dryads Console (Port 3001)";;
                "university-ui") echo "  • DRYAD University UI (Port 3006)";;
                "writer-portal") echo "  • Writer Portal (Port 3000)";;
            esac
        done
        echo ""
    else
        echo -e "${CYAN}Frontend Applications:${NC} None"
        echo ""
    fi

    # Optional components
    if [[ ${#OPTIONAL_COMPONENTS[@]} -gt 0 ]]; then
        echo -e "${CYAN}Optional Components:${NC}"
        for component in "${OPTIONAL_COMPONENTS[@]}"; do
            case $component in
                "mcp") echo "  • MCP Server";;
                "postgresql") echo "  • PostgreSQL Database";;
                "celery") echo "  • Celery Workers";;
                "monitoring") echo "  • Prometheus + Grafana";;
                "logging") echo "  • ELK Stack";;
                "metrics") echo "  • Full Metrics Suite";;
            esac
        done
        echo ""
    else
        echo -e "${CYAN}Optional Components:${NC} None"
        echo ""
    fi

    # LLM Provider
    echo -e "${CYAN}LLM Provider:${NC} $LLM_PROVIDER"
    echo ""

    # Domain
    echo -e "${CYAN}Domain:${NC} $DOMAIN"
    echo ""

    # Estimated resources
    echo "═══════════════════════════════════════════════════════════════"
    echo "                    RESOURCE REQUIREMENTS"
    echo "═══════════════════════════════════════════════════════════════"
    echo ""

    local estimated_ram=0
    local estimated_disk=0

    # Calculate based on deployment config
    case $DEPLOYMENT_CONFIG in
        "minimal") estimated_ram=2; estimated_disk=5;;
        "basic") estimated_ram=4; estimated_disk=10;;
        "development") estimated_ram=6; estimated_disk=15;;
        "full") estimated_ram=8; estimated_disk=20;;
        "production") estimated_ram=10; estimated_disk=25;;
        "scalable") estimated_ram=12; estimated_disk=30;;
        "gpu") estimated_ram=16; estimated_disk=40;;
    esac

    # Add for frontends
    estimated_ram=$((estimated_ram + ${#SELECTED_FRONTENDS[@]} * 1))
    estimated_disk=$((estimated_disk + ${#SELECTED_FRONTENDS[@]} * 2))

    # Add for optional components
    [[ " ${OPTIONAL_COMPONENTS[@]} " =~ " monitoring " ]] && estimated_ram=$((estimated_ram + 2)) && estimated_disk=$((estimated_disk + 5))
    [[ " ${OPTIONAL_COMPONENTS[@]} " =~ " logging " ]] && estimated_ram=$((estimated_ram + 3)) && estimated_disk=$((estimated_disk + 10))
    [[ " ${OPTIONAL_COMPONENTS[@]} " =~ " postgresql " ]] && estimated_ram=$((estimated_ram + 1)) && estimated_disk=$((estimated_disk + 5))

    echo -e "${CYAN}Estimated RAM:${NC} ${estimated_ram}GB"
    echo -e "${CYAN}Estimated Disk:${NC} ${estimated_disk}GB"
    echo -e "${CYAN}Estimated Time:${NC} 10-15 minutes (excluding downloads)"
    echo ""

    # Check available resources
    local mem_available=$(get_available_memory)
    local disk_available=$(get_available_disk)

    if [[ "$mem_available" != "unknown" ]]; then
        local mem_available_gb=$((mem_available / 1024))
        echo -e "${CYAN}Available RAM:${NC} ${mem_available_gb}GB"

        if [[ $mem_available_gb -lt $estimated_ram ]]; then
            print_warning "Available RAM (${mem_available_gb}GB) is less than estimated (${estimated_ram}GB)"
            print_warning "Installation may fail or system may become slow"
        fi
    fi

    if [[ "$disk_available" != "" ]]; then
        echo -e "${CYAN}Available Disk:${NC} ${disk_available}GB"

        if [[ $disk_available -lt $estimated_disk ]]; then
            print_warning "Available disk (${disk_available}GB) is less than estimated (${estimated_disk}GB)"
        fi
    fi

    echo ""
    echo "═══════════════════════════════════════════════════════════════"
    echo ""

    if ! confirm "Proceed with installation?" "n"; then
        print_error "Installation cancelled by user"
        exit 0
    fi

    print_success "Installation confirmed!"
}

