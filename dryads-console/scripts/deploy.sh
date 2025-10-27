#!/bin/bash

# The Dryads Console Deployment Script
# Autonomous deployment for DRYAD.AI frontend

set -e

echo "🚀 Starting The Dryads Console deployment..."

# Configuration
PROJECT_NAME="dryads-console"
BUILD_DIR="dist"
DEPLOY_DIR="/var/www/dryads-console"
BACKUP_DIR="/var/backups/dryads-console"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
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

# Check prerequisites
check_prerequisites() {
    log "Checking prerequisites..."
    
    # Check Node.js
    if ! command -v node &> /dev/null; then
        error "Node.js is not installed"
        exit 1
    fi
    
    # Check npm
    if ! command -v npm &> /dev/null; then
        error "npm is not installed"
        exit 1
    fi
    
    # Check required Node.js version
    NODE_VERSION=$(node -v | cut -d 'v' -f 2)
    REQUIRED_VERSION="18.0.0"
    
    if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$NODE_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]; then
        error "Node.js version $NODE_VERSION is less than required $REQUIRED_VERSION"
        exit 1
    fi
    
    success "Prerequisites check passed"
}

# Backup existing deployment
backup_existing() {
    if [ -d "$DEPLOY_DIR" ]; then
        log "Backing up existing deployment..."
        
        BACKUP_PATH="$BACKUP_DIR/$TIMESTAMP"
        mkdir -p "$BACKUP_PATH"
        
        cp -r "$DEPLOY_DIR"/* "$BACKUP_PATH/" 2>/dev/null || true
        
        success "Backup created at $BACKUP_PATH"
    else
        log "No existing deployment found, skipping backup"
    fi
}

# Install dependencies
install_dependencies() {
    log "Installing dependencies..."
    
    if [ ! -d "node_modules" ]; then
        npm ci --silent
    else
        npm install --silent
    fi
    
    success "Dependencies installed"
}

# Build the project
build_project() {
    log "Building project..."
    
    # Run type checking
    log "Running TypeScript type checking..."
    npm run type-check
    
    # Run linting
    log "Running ESLint..."
    npm run lint
    
    # Build the project
    npm run build
    
    if [ ! -d "$BUILD_DIR" ]; then
        error "Build failed - dist directory not found"
        exit 1
    fi
    
    success "Project built successfully"
}

# Deploy to target directory
deploy() {
    log "Deploying to $DEPLOY_DIR..."
    
    # Create deployment directory if it doesn't exist
    sudo mkdir -p "$DEPLOY_DIR"
    
    # Copy build files
    sudo cp -r "$BUILD_DIR"/* "$DEPLOY_DIR/"
    
    # Set proper permissions
    sudo chown -R www-data:www-data "$DEPLOY_DIR"
    sudo chmod -R 755 "$DEPLOY_DIR"
    
    success "Deployment completed"
}

# Configure nginx (if needed)
configure_nginx() {
    log "Checking nginx configuration..."
    
    NGINX_CONF="/etc/nginx/sites-available/dryads-console"
    
    if [ ! -f "$NGINX_CONF" ]; then
        warning "nginx configuration not found, creating template..."
        
        sudo tee "$NGINX_CONF" > /dev/null <<EOF
server {
    listen 80;
    server_name dryads-console.local;
    
    root $DEPLOY_DIR;
    index index.html;
    
    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_proxied any;
    gzip_comp_level 6;
    gzip_types
        application/atom+xml
        application/geo+json
        application/javascript
        application/x-javascript
        application/json
        application/ld+json
        application/manifest+json
        application/rdf+xml
        application/rss+xml
        application/xhtml+xml
        application/xml
        font/eot
        font/otf
        font/ttf
        image/svg+xml
        text/css
        text/javascript
        text/plain
        text/xml;
    
    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;
    add_header Content-Security-Policy "default-src 'self' http: https: data: blob: 'unsafe-inline'" always;
    
    # API proxy
    location /api/ {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_cache_bypass \$http_upgrade;
    }
    
    # WebSocket proxy
    location /ws/ {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "Upgrade";
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
    
    # SPA fallback
    location / {
        try_files \$uri \$uri/ /index.html;
    }
    
    # Cache static assets
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
EOF
        
        # Enable site
        sudo ln -sf "$NGINX_CONF" "/etc/nginx/sites-enabled/"
        sudo nginx -t && sudo systemctl reload nginx
        
        success "nginx configuration created and reloaded"
    else
        success "nginx configuration already exists"
    fi
}

# Health check
health_check() {
    log "Performing health check..."
    
    # Wait a moment for nginx to reload
    sleep 2
    
    # Basic curl check
    if curl -f http://localhost > /dev/null 2>&1; then
        success "Health check passed - application is responding"
    else
        warning "Health check warning - application may need manual verification"
    fi
}

# Cleanup old backups
cleanup_backups() {
    log "Cleaning up old backups (keeping last 5)..."
    
    # Keep only the 5 most recent backups
    ls -dt "$BACKUP_DIR"/*/ | tail -n +6 | xargs rm -rf 2>/dev/null || true
    
    success "Backup cleanup completed"
}

# Main deployment process
main() {
    log "Starting The Dryads Console deployment process..."
    
    check_prerequisites
    backup_existing
    install_dependencies
    build_project
    deploy
    configure_nginx
    health_check
    cleanup_backups
    
    success "🎉 The Dryads Console deployment completed successfully!"
    log "Application should be available at http://localhost"
    log "Backup created at: $BACKUP_DIR/$TIMESTAMP"
}

# Run main function
main "$@"