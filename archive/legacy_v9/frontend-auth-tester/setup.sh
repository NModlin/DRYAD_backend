#!/bin/bash

# DRYAD.AI OAuth2 & JWT Authentication Tester Setup Script
# This script sets up the comprehensive frontend testing application

set -e

echo "🚀 Setting up DRYAD.AI Authentication Tester..."

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed. Please install Node.js 16+ and try again."
    exit 1
fi

# Check Node.js version
NODE_VERSION=$(node -v | cut -d'v' -f2 | cut -d'.' -f1)
if [ "$NODE_VERSION" -lt 16 ]; then
    echo "❌ Node.js version 16+ is required. Current version: $(node -v)"
    exit 1
fi

echo "✅ Node.js $(node -v) detected"

# Check if npm is installed
if ! command -v npm &> /dev/null; then
    echo "❌ npm is not installed. Please install npm and try again."
    exit 1
fi

echo "✅ npm $(npm -v) detected"

# Install dependencies
echo "📦 Installing dependencies..."
npm install

if [ $? -ne 0 ]; then
    echo "❌ Failed to install dependencies"
    exit 1
fi

echo "✅ Dependencies installed successfully"

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "📝 Creating .env file from template..."
    cp .env.example .env
    echo "✅ .env file created"
    echo ""
    echo "⚠️  IMPORTANT: Please edit the .env file and set your configuration:"
    echo "   - REACT_APP_GOOGLE_CLIENT_ID: Your Google OAuth2 client ID"
    echo "   - REACT_APP_API_BASE_URL: DRYAD.AI Backend URL (default: http://localhost:8000)"
    echo "   - REACT_APP_WS_BASE_URL: WebSocket server URL (default: ws://localhost:8000)"
    echo ""
else
    echo "✅ .env file already exists"
fi

# Check if DRYAD.AI Backend is running
echo "🔍 Checking DRYAD.AI Backend connectivity..."
BACKEND_URL=${REACT_APP_API_BASE_URL:-"http://localhost:8000"}

if curl -s --connect-timeout 5 "$BACKEND_URL/api/v1/health" > /dev/null 2>&1; then
    echo "✅ DRYAD.AI Backend is accessible at $BACKEND_URL"
else
    echo "⚠️  DRYAD.AI Backend is not accessible at $BACKEND_URL"
    echo "   Please ensure the backend is running before starting the tester"
fi

# Create public directory if it doesn't exist
if [ ! -d "public" ]; then
    mkdir -p public
fi

# Create a simple favicon if it doesn't exist
if [ ! -f "public/favicon.ico" ]; then
    echo "🎨 Creating favicon..."
    # Create a simple 16x16 favicon (base64 encoded)
    echo "Creating basic favicon.ico..."
    touch public/favicon.ico
fi

echo ""
echo "🎉 Setup completed successfully!"
echo ""
echo "📋 Next steps:"
echo "1. Edit the .env file with your configuration"
echo "2. Ensure DRYAD.AI Backend is running at $BACKEND_URL"
echo "3. Start the application with: npm start"
echo ""
echo "🔧 Available commands:"
echo "   npm start          - Start the development server"
echo "   npm run build      - Build for production"
echo "   npm test           - Run tests"
echo ""
echo "📖 For detailed instructions, see README.md"
echo ""
echo "🌐 The application will be available at: http://localhost:3000"
echo ""
echo "Happy testing! 🧪"
