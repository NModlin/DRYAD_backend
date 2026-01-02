#!/bin/bash
# DRYAD.AI Quick Remote Installation Script
# This script downloads and runs the enhanced installer in one command

set -e

echo "=========================================="
echo "DRYAD.AI Quick Installation"
echo "=========================================="
echo ""

# Configuration
REPO_URL="https://github.com/NModlin/DRYAD_backend.git"
BRANCH="${1:-main}"  # Default to main branch, or use first argument
INSTALL_DIR="${2:-$HOME/DRYAD_backend}"  # Default to home directory

echo "Repository: $REPO_URL"
echo "Branch: $BRANCH"
echo "Installation Directory: $INSTALL_DIR"
echo ""

# Check if git is installed
if ! command -v git &> /dev/null; then
    echo "Error: git is not installed"
    echo ""
    echo "Please install git first:"
    echo "  Ubuntu/Debian: sudo apt install git -y"
    echo "  CentOS/RHEL:   sudo yum install git -y"
    echo "  macOS:         brew install git"
    exit 1
fi

# Check if directory already exists
if [ -d "$INSTALL_DIR" ]; then
    echo "Warning: Directory $INSTALL_DIR already exists"
    read -p "Do you want to remove it and continue? (y/N): " response
    if [[ "$response" =~ ^[Yy]$ ]]; then
        rm -rf "$INSTALL_DIR"
        echo "Removed existing directory"
    else
        echo "Installation cancelled"
        exit 0
    fi
fi

# Clone the repository
echo "Cloning repository..."
if git clone -b "$BRANCH" "$REPO_URL" "$INSTALL_DIR"; then
    echo "✓ Repository cloned successfully"
else
    echo "✗ Failed to clone repository"
    echo ""
    echo "If the repository is private, you may need to:"
    echo "  1. Set up SSH keys: https://docs.github.com/en/authentication/connecting-to-github-with-ssh"
    echo "  2. Or use a personal access token"
    exit 1
fi

# Navigate to directory
cd "$INSTALL_DIR"

# Make scripts executable
echo "Making scripts executable..."
chmod +x install_dryad_enhanced.sh lib/*.sh test_installer.sh 2>/dev/null || true
echo "✓ Scripts are now executable"

echo ""
echo "=========================================="
echo "Download Complete!"
echo "=========================================="
echo ""
echo "Installation directory: $INSTALL_DIR"
echo ""
echo "Next steps:"
echo "  1. cd $INSTALL_DIR"
echo "  2. ./install_dryad_enhanced.sh"
echo ""
echo "Or run the installer now:"
read -p "Do you want to run the installer now? (Y/n): " run_now
run_now=${run_now:-y}

if [[ "$run_now" =~ ^[Yy]$ ]]; then
    echo ""
    echo "Starting DRYAD.AI Enhanced Installer..."
    echo ""
    ./install_dryad_enhanced.sh
else
    echo ""
    echo "You can run the installer later with:"
    echo "  cd $INSTALL_DIR"
    echo "  ./install_dryad_enhanced.sh"
fi

