#!/bin/bash
# Quick fix for Python installation in Ubuntu 24.04

set -e

echo "🔧 Quick Python Fix for Ubuntu 24.04"
echo "====================================="
echo ""

# Check if Python 3.12 is available (default in Ubuntu 24.04)
if command -v python3.12 &> /dev/null; then
    echo "✅ Python 3.12 found (default in Ubuntu 24.04)"
    echo "   The project supports Python 3.11+, so we'll use Python 3.12"
    PYTHON_CMD="python3.12"
    
    # Install Python 3.12 venv and dev packages
    echo "📦 Installing Python 3.12 development packages..."
    sudo apt-get install -y python3.12-venv python3.12-dev python3-pip
    
    echo "✅ Python 3.12 development packages installed"
else
    echo "⚠️  Python 3.12 not found. Installing Python 3.11 from deadsnakes PPA..."
    
    # Add deadsnakes PPA
    sudo apt-get install -y software-properties-common
    sudo add-apt-repository -y ppa:deadsnakes/ppa
    sudo apt-get update
    
    # Install Python 3.11
    sudo apt-get install -y python3.11 python3.11-venv python3.11-dev
    PYTHON_CMD="python3.11"
    
    echo "✅ Python 3.11 installed"
fi

echo ""
echo "✅ Python setup complete!"
echo "   Using: ${PYTHON_CMD} ($(${PYTHON_CMD} --version))"
echo ""
echo "🚀 Next steps:"
echo "   1. Continue with the main setup script:"
echo "      bash setup-ubuntu-wsl.sh"
echo ""
echo "   Or manually continue:"
echo "      ${PYTHON_CMD} -m venv .venv"
echo "      source .venv/bin/activate"
echo "      pip install -r requirements.txt"
echo ""

