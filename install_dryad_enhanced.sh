#!/bin/bash
# DRYAD.AI Enhanced Installation Script
# Interactive installer for DRYAD.AI with full component selection
# Version: 2.0

set -e

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export PROJECT_ROOT="$SCRIPT_DIR"

# Log file
export LOG_FILE="$HOME/dryad_install_$(date +%Y%m%d_%H%M%S).log"

# Source library files
source "$SCRIPT_DIR/lib/utils.sh"
source "$SCRIPT_DIR/lib/menu_functions.sh"
source "$SCRIPT_DIR/lib/install_functions.sh"
source "$SCRIPT_DIR/lib/config_generators.sh"
source "$SCRIPT_DIR/lib/health_checks.sh"

# Cleanup function
cleanup() {
    local exit_code=$?
    
    if [[ $exit_code -ne 0 ]]; then
        print_error "Installation failed with exit code $exit_code"
        echo ""
        print_info "Log file: $LOG_FILE"
        print_info "You can try running the script again or check the logs for details"
        echo ""
        
        if confirm "Would you like to clean up partially installed components?" "n"; then
            print_step "Cleaning up..."
            docker compose down 2>/dev/null || docker-compose down 2>/dev/null || true
            
            # Stop frontend processes
            for frontend in "${SELECTED_FRONTENDS[@]}"; do
                if [[ -f "$PROJECT_ROOT/logs/${frontend}.pid" ]]; then
                    local pid=$(cat "$PROJECT_ROOT/logs/${frontend}.pid")
                    kill $pid 2>/dev/null || true
                    rm -f "$PROJECT_ROOT/logs/${frontend}.pid"
                fi
            done
            
            print_success "Cleanup complete"
        fi
    fi
}

trap cleanup EXIT

# Display final status and information
display_final_status() {
    clear
    print_header "🎉 DRYAD.AI Installation Complete!"
    
    echo ""
    echo "═══════════════════════════════════════════════════════════════"
    echo "                    INSTALLATION SUMMARY"
    echo "═══════════════════════════════════════════════════════════════"
    echo ""
    
    # Deployment Configuration
    echo -e "${CYAN}📦 Deployment Configuration:${NC} $DEPLOYMENT_CONFIG"
    echo ""
    
    # Backend Services
    echo -e "${CYAN}🔧 Backend Services:${NC}"
    echo "   ✓ DRYAD API         → http://localhost:8000"
    echo "   ✓ API Docs          → http://localhost:8000/docs"
    echo "   ✓ Health Check      → http://localhost:8000/api/v1/health/status"
    
    if [[ " ${OPTIONAL_COMPONENTS[@]} " =~ " mcp " ]]; then
        echo "   ✓ MCP Server        → http://localhost:8000/mcp"
    fi
    
    echo ""
    
    # Frontend Applications
    if [[ ${#SELECTED_FRONTENDS[@]} -gt 0 ]]; then
        echo -e "${CYAN}🎨 Frontend Applications:${NC}"
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
        echo -e "${CYAN}📊 Monitoring & Metrics:${NC}"
        echo "   ✓ Prometheus        → http://localhost:9090"
        echo "   ✓ Grafana           → http://localhost:3000 (admin/admin)"
        echo ""
    fi
    
    # Logging
    if [[ " ${OPTIONAL_COMPONENTS[@]} " =~ " logging " ]]; then
        echo -e "${CYAN}📝 Logging Stack:${NC}"
        echo "   ✓ Elasticsearch     → http://localhost:9200"
        echo "   ✓ Kibana            → http://localhost:5601"
        echo ""
    fi
    
    # Database
    echo -e "${CYAN}🗄️  Database:${NC}"
    if [[ " ${OPTIONAL_COMPONENTS[@]} " =~ " postgresql " ]]; then
        echo "   ✓ PostgreSQL        → localhost:5432"
    else
        echo "   ✓ SQLite            → ./dryad.db"
    fi
    echo ""
    
    # Vector Database
    echo -e "${CYAN}🔍 Vector Database:${NC}"
    echo "   ✓ Weaviate          → http://localhost:8080"
    echo ""
    
    # Cache
    echo -e "${CYAN}⚡ Cache:${NC}"
    echo "   ✓ Redis             → localhost:6379"
    echo ""
    
    # LLM Provider
    echo -e "${CYAN}🤖 LLM Provider:${NC} $LLM_PROVIDER"
    if [[ "$LLM_PROVIDER" == "ollama" ]]; then
        echo "   ✓ Ollama            → http://localhost:11434"
    fi
    echo ""
    
    echo "═══════════════════════════════════════════════════════════════"
    echo ""

    # Management Commands
    echo -e "${CYAN}🔧 Management Commands:${NC}"
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

    # Frontend management
    if [[ ${#SELECTED_FRONTENDS[@]} -gt 0 ]]; then
        echo "   Stop Frontend:"
        for frontend in "${SELECTED_FRONTENDS[@]}"; do
            if [[ -f "$PROJECT_ROOT/logs/${frontend}.pid" ]]; then
                echo "     kill \$(cat $PROJECT_ROOT/logs/${frontend}.pid)"
            fi
        done
        echo ""
    fi

    # Next Steps
    echo -e "${CYAN}📚 Next Steps:${NC}"
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
    echo -e "${CYAN}🆘 Troubleshooting:${NC}"
    echo ""
    echo "   Installation Logs:"
    echo "     $LOG_FILE"
    echo ""
    echo "   Service Logs:"
    echo "     docker compose logs [service-name]"
    echo ""
    if [[ ${#SELECTED_FRONTENDS[@]} -gt 0 ]]; then
        echo "   Frontend Logs:"
        for frontend in "${SELECTED_FRONTENDS[@]}"; do
            echo "     $PROJECT_ROOT/logs/${frontend}.log"
        done
        echo ""
    fi

    # Configuration Files
    echo -e "${CYAN}⚙️  Configuration Files:${NC}"
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

    # Save installation summary
    cat > "$PROJECT_ROOT/INSTALLATION_SUMMARY.txt" << EOF
DRYAD.AI Installation Summary
Generated: $(date)

Deployment Configuration: $DEPLOYMENT_CONFIG
LLM Provider: $LLM_PROVIDER
Domain: $DOMAIN

Selected Frontends:
$(for f in "${SELECTED_FRONTENDS[@]}"; do echo "  - $f"; done)

Optional Components:
$(for c in "${OPTIONAL_COMPONENTS[@]}"; do echo "  - $c"; done)

Installation Log: $LOG_FILE

Access Points:
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs
$(for frontend in "${SELECTED_FRONTENDS[@]}"; do
    case $frontend in
        "dryads-console") echo "- Dryads Console: http://localhost:3001";;
        "university-ui") echo "- University UI: http://localhost:3006";;
        "writer-portal") echo "- Writer Portal: http://localhost:3000";;
    esac
done)
$(if [[ " ${OPTIONAL_COMPONENTS[@]} " =~ " monitoring " ]]; then
    echo "- Prometheus: http://localhost:9090"
    echo "- Grafana: http://localhost:3000"
fi)
$(if [[ " ${OPTIONAL_COMPONENTS[@]} " =~ " logging " ]]; then
    echo "- Elasticsearch: http://localhost:9200"
    echo "- Kibana: http://localhost:5601"
fi)
EOF

    print_info "Installation summary saved to: $PROJECT_ROOT/INSTALLATION_SUMMARY.txt"
}

# Main installation flow
main() {
    # Initialize log
    log "Starting DRYAD.AI Enhanced Installation"
    log "Script version: 2.0"
    log "Date: $(date)"

    # Step 1: Welcome
    display_welcome

    # Step 2: Prerequisites
    if ! check_prerequisites; then
        print_error "Prerequisites check failed. Please install required software and try again."
        exit 1
    fi

    # Step 3: Select deployment configuration
    select_deployment_config

    # Step 4: Select frontends
    select_frontends

    # Step 5: Select optional components
    select_optional_components

    # Step 6: Configure LLM provider
    configure_llm_provider

    # Step 7: Configure domain
    configure_domain

    # Step 8: Check port conflicts
    check_port_conflicts

    # Step 9: Display confirmation
    display_confirmation

    # Step 10: Create directories
    create_directories

    # Step 11: Generate configuration
    generate_backend_env

    # Step 12: Install backend
    if ! install_backend; then
        print_error "Backend installation failed"
        exit 1
    fi

    # Step 13: Setup Ollama if needed
    setup_ollama

    # Step 14: Enable MCP if selected
    if [[ " ${OPTIONAL_COMPONENTS[@]} " =~ " mcp " ]]; then
        enable_mcp_server
    fi

    # Step 15: Install frontends
    install_frontends

    # Step 16: Health checks
    sleep 5  # Give services a moment to stabilize
    health_check_all

    # Step 17: Display service status
    display_service_status

    # Step 18: Display final status
    display_final_status

    log "Installation completed successfully"
}

# Run main function
main "$@"

