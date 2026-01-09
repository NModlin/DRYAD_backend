#!/bin/bash
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

print_step() { echo -e "${GREEN}==>${NC} $1"; }
print_error() { echo -e "${RED}[ERROR] $1${NC}"; }
print_warning() { echo -e "${YELLOW}[WARNING] $1${NC}"; }

# Check for root/sudo
if [ "$EUID" -ne 0 ]; then
    print_error "Please run as root (use sudo)"
    exit 1
fi

DEST_DIR="/home/containerd-data"
ORIG_DIR="/var/lib/containerd"

print_step "Checking disk space on /home..."
# Ensure /home has space
HOME_SPACE=$(df -BG /home | awk 'NR==2 {print $4}' | tr -d 'G')
if [ "$HOME_SPACE" -lt 10 ]; then
    print_error "Not enough space on /home (only ${HOME_SPACE}GB available). Need at least 10GB."
    exit 1
fi

print_step "Stopping Docker and Containerd services..."
systemctl stop docker || true
systemctl stop containerd || true

print_step "Creating new directory at $DEST_DIR..."
mkdir -p "$DEST_DIR"

if [ -d "$ORIG_DIR" ] && [ ! -L "$ORIG_DIR" ]; then
    print_step "Moving existing containerd data to $DEST_DIR (this may take a while)..."
    cp -a "$ORIG_DIR/." "$DEST_DIR/"
    
    print_step "Backing up original directory..."
    mv "$ORIG_DIR" "${ORIG_DIR}.bak"
elif [ -L "$ORIG_DIR" ]; then
    print_warning "$ORIG_DIR is already a symlink. Checking target..."
    TARGET=$(readlink -f "$ORIG_DIR")
    if [[ "$TARGET" == "$DEST_DIR" ]]; then
        print_step "Already correctly symlinked to $DEST_DIR"
    else
        print_error "Symlinked to unexpected location: $TARGET. Please calculate manually."
        exit 1
    fi
else
    print_step "Original directory not found, just creating symlink..."
fi

# Create symlink if it doesn't verify
if [ ! -L "$ORIG_DIR" ]; then
    print_step "Creating symlink: $ORIG_DIR -> $DEST_DIR"
    ln -s "$DEST_DIR" "$ORIG_DIR"
fi

print_step "Restarting services..."
systemctl start containerd
systemctl start docker

print_step "Verifying services..."
if systemctl is-active --quiet docker; then
    echo -e "${GREEN}[SUCCESS] Docker is running.${NC}"
else
    print_error "Docker failed to start."
    exit 1
fi

echo ""
echo -e "${GREEN}SUCCESS! Containerd data moved to /home/containerd-data.${NC}"
echo "You can now verify disk usage with: df -h $DEST_DIR"
