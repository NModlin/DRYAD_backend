#!/bin/bash

# The Dryads Console Development Setup Script
# Quick setup for development environment

set -e

echo "🔧 Setting up The Dryads Console development environment..."

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Logging functions
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

success() {
    echo -e "${GREEN}✓ $1${NC}"
}

warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

error() {
    echo -e "${RED}✗ $1${NC}"
}

# Check Node.js installation
check_node() {
    log "Checking Node.js installation..."
    
    if ! command -v node &> /dev/null; then
        error "Node.js is not installed"
        echo "Please install Node.js 18+ from https://nodejs.org/"
        exit 1
    fi
    
    NODE_VERSION=$(node -v | cut -d 'v' -f 2)
    success "Node.js $NODE_VERSION detected"
}

# Check npm installation
check_npm() {
    log "Checking npm installation..."
    
    if ! command -v npm &> /dev/null; then
        error "npm is not installed"
        exit 1
    fi
    
    NPM_VERSION=$(npm -v)
    success "npm $NPM_VERSION detected"
}

# Install dependencies
install_dependencies() {
    log "Installing dependencies..."
    
    if [ -f "package-lock.json" ]; then
        npm ci --silent
    else
        npm install --silent
    fi
    
    success "Dependencies installed successfully"
}

# Create environment file
setup_environment() {
    log "Setting up environment configuration..."
    
    if [ ! -f ".env" ]; then
        cat > .env << EOF
# The Dryads Console Environment Configuration
VITE_API_BASE_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000
VITE_GOOGLE_DRIVE_CLIENT_ID=your_google_drive_client_id_here

# Development settings
VITE_DEBUG=true
VITE_LOG_LEVEL=info

# Feature flags (comma-separated)
VITE_ENABLED_FEATURES=memory_keeper,oracle_consultation,file_manager
EOF
        success "Environment file created (.env)"
    else
        warning "Environment file already exists, skipping creation"
    fi
}

# Run initial type checking
type_check() {
    log "Running TypeScript type checking..."
    
    if npm run type-check; then
        success "TypeScript type checking passed"
    else
        error "TypeScript type checking failed"
        exit 1
    fi
}

# Run linting
run_lint() {
    log "Running ESLint..."
    
    if npm run lint; then
        success "ESLint passed"
    else
        warning "ESLint found issues, please review"
    fi
}

# Build the project for verification
build_verification() {
    log "Building project for verification..."
    
    if npm run build; then
        success "Build verification passed"
    else
        error "Build verification failed"
        exit 1
    fi
}

# Display setup completion
display_completion() {
    echo
    echo "🎉 The Dryads Console development environment is ready!"
    echo
    echo "📋 Next steps:"
    echo "  1. Start the DRYAD backend on localhost:8000"
    echo "  2. Run 'npm run dev' to start the development server"
    echo "  3. Open http://localhost:3001 in your browser"
    echo
    echo "🔧 Available commands:"
    echo "  • npm run dev      - Start development server"
    echo "  • npm run build    - Build for production"
    echo "  • npm run preview  - Preview production build"
    echo "  • npm run lint     - Run ESLint"
    echo "  • npm run type-check - Run TypeScript type checking"
    echo
    echo "📚 Documentation:"
    echo "  • Read README.md for detailed information"
    echo "  • Check src/types/index.ts for API types"
    echo "  • Review src/services/api.ts for API integration"
    echo
}

# Main setup process
main() {
    log "Starting The Dryads Console setup..."
    
    check_node
    check_npm
    install_dependencies
    setup_environment
    type_check
    run_lint
    build_verification
    display_completion
    
    success "Setup completed successfully!"
}

# Run main function
main "$@"