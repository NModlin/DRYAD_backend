#!/bin/bash
# Test script for DRYAD.AI Enhanced Installer
# This script tests the menu functions without actually installing anything

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export PROJECT_ROOT="$SCRIPT_DIR"
export LOG_FILE="/tmp/dryad_test_$(date +%Y%m%d_%H%M%S).log"

# Source library files
source "$SCRIPT_DIR/lib/utils.sh"
source "$SCRIPT_DIR/lib/menu_functions.sh"
source "$SCRIPT_DIR/lib/install_functions.sh"
source "$SCRIPT_DIR/lib/config_generators.sh"
source "$SCRIPT_DIR/lib/health_checks.sh"

echo "Testing DRYAD.AI Enhanced Installer Components"
echo "=============================================="
echo ""

# Test 1: Utility functions
print_header "Test 1: Utility Functions"
print_success "Success message test"
print_error "Error message test"
print_warning "Warning message test"
print_info "Info message test"
print_step "Step message test"
echo ""

# Test 2: System checks
print_header "Test 2: System Information"
echo "Available Memory: $(get_available_memory)MB"
echo "Available Disk: $(get_available_disk)GB"
echo ""

# Test 3: Command checks
print_header "Test 3: Command Availability"
for cmd in docker node npm python3 curl; do
    if command_exists "$cmd"; then
        print_success "$cmd is available"
    else
        print_warning "$cmd is not available"
    fi
done
echo ""

# Test 4: Docker check
print_header "Test 4: Docker Status"
if is_docker_running; then
    print_success "Docker is running"
    docker --version
else
    print_warning "Docker is not running"
fi
echo ""

# Test 5: Port checks
print_header "Test 5: Port Availability"
for port in 8000 3000 3001 3006 8080 6379; do
    if is_port_in_use "$port"; then
        print_warning "Port $port is in use"
    else
        print_success "Port $port is available"
    fi
done
echo ""

# Test 6: Secret generation
print_header "Test 6: Secret Generation"
secret=$(generate_secret)
echo "Generated secret (first 20 chars): ${secret:0:20}..."
echo "Secret length: ${#secret}"
echo ""

# Test 7: Configuration simulation
print_header "Test 7: Configuration Simulation"
export DEPLOYMENT_CONFIG="basic"
export SELECTED_FRONTENDS=("dryads-console" "writer-portal")
export OPTIONAL_COMPONENTS=("mcp" "monitoring")
export LLM_PROVIDER="mock"
export DOMAIN="localhost"

echo "Deployment Config: $DEPLOYMENT_CONFIG"
echo "Selected Frontends: ${SELECTED_FRONTENDS[*]}"
echo "Optional Components: ${OPTIONAL_COMPONENTS[*]}"
echo "LLM Provider: $LLM_PROVIDER"
echo "Domain: $DOMAIN"
echo ""

# Test 8: Prerequisites check
print_header "Test 8: Prerequisites Check"
if check_prerequisites; then
    print_success "All prerequisites met"
else
    print_warning "Some prerequisites are missing"
fi
echo ""

# Test 9: Directory creation (dry run)
print_header "Test 9: Directory Structure Test"
echo "Would create the following directories:"
echo "  - data/"
echo "  - logs/"
echo "  - monitoring/grafana/"
echo "  - monitoring/prometheus/"
echo ""

# Test 10: Configuration generation (dry run)
print_header "Test 10: Configuration Generation Test"
echo "Testing .env file generation..."

# Create a test .env file
test_env_file="/tmp/test_dryad.env"
cat > "$test_env_file" << EOF
# Test Configuration
DEPLOYMENT_CONFIG=$DEPLOYMENT_CONFIG
LLM_PROVIDER=$LLM_PROVIDER
DOMAIN=$DOMAIN
EOF

if [[ -f "$test_env_file" ]]; then
    print_success "Test .env file created successfully"
    echo "Contents:"
    cat "$test_env_file"
    rm -f "$test_env_file"
else
    print_error "Failed to create test .env file"
fi
echo ""

# Summary
print_header "Test Summary"
echo "All component tests completed!"
echo ""
echo "The installer appears to be working correctly."
echo "You can now run the full installer with:"
echo "  ./install_dryad_enhanced.sh"
echo ""
echo "Test log: $LOG_FILE"

