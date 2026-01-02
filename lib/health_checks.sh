#!/bin/bash
# DRYAD.AI Enhanced Installation - Health Check Functions
# Functions for verifying installation health

# Source utilities if not already sourced
if [[ -z "$DRYAD_UTILS_LOADED" ]]; then
    source "$(dirname "${BASH_SOURCE[0]}")/utils.sh"
fi

# Health check for backend
health_check_backend() {
    print_info "Checking backend health..."
    
    if curl -f -s http://localhost:8000/api/v1/health/status &> /dev/null; then
        print_success "✓ Backend API is healthy"
        return 0
    else
        print_error "✗ Backend API health check failed"
        return 1
    fi
}

# Health check for a frontend
health_check_frontend() {
    local frontend=$1
    local port=""
    
    case $frontend in
        "dryads-console") port=3001 ;;
        "university-ui") port=3006 ;;
        "writer-portal") port=3000 ;;
        *) return 1 ;;
    esac
    
    print_info "Checking $frontend health..."
    
    if curl -f -s http://localhost:$port &> /dev/null; then
        print_success "✓ $frontend is healthy (port $port)"
        return 0
    else
        print_error "✗ $frontend health check failed"
        return 1
    fi
}

# Health check for monitoring stack
health_check_monitoring() {
    print_info "Checking monitoring stack..."
    
    local healthy=true
    
    if curl -f -s http://localhost:9090/-/ready &> /dev/null; then
        print_success "✓ Prometheus is healthy"
    else
        print_error "✗ Prometheus health check failed"
        healthy=false
    fi
    
    if curl -f -s http://localhost:3000/api/health &> /dev/null; then
        print_success "✓ Grafana is healthy"
    else
        print_error "✗ Grafana health check failed"
        healthy=false
    fi
    
    $healthy
}

# Health check for logging stack
health_check_logging() {
    print_info "Checking logging stack..."
    
    local healthy=true
    
    if curl -f -s http://localhost:9200/_cluster/health &> /dev/null; then
        print_success "✓ Elasticsearch is healthy"
    else
        print_error "✗ Elasticsearch health check failed"
        healthy=false
    fi
    
    if curl -f -s http://localhost:5601/api/status &> /dev/null; then
        print_success "✓ Kibana is healthy"
    else
        print_error "✗ Kibana health check failed"
        healthy=false
    fi
    
    $healthy
}

# Comprehensive health check
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
    
    # MCP Server
    if [[ " ${OPTIONAL_COMPONENTS[@]} " =~ " mcp " ]]; then
        print_info "Checking MCP Server..."
        if curl -f -s http://localhost:8000/mcp &> /dev/null; then
            print_success "✓ MCP Server is healthy"
        else
            print_warning "⚠ MCP Server health check failed (may not be fully implemented)"
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

# Display service status
display_service_status() {
    print_step "Checking service status..."
    
    echo ""
    echo "═══════════════════════════════════════════════════════════════"
    echo "                        SERVICE STATUS"
    echo "═══════════════════════════════════════════════════════════════"
    echo ""
    
    # Docker services
    docker compose ps 2>/dev/null || docker-compose ps 2>/dev/null
    
    echo ""
    echo "═══════════════════════════════════════════════════════════════"
    echo ""
}

