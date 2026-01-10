#!/bin/bash

# Dryad.AI React Chat App Setup Script
# This script sets up the React chat interface to connect to Dryad backend

echo "🤖 Setting up Dryad.AI React Chat Interface..."

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed. Please install Node.js first."
    exit 1
fi

# Check if npm is installed
if ! command -v npm &> /dev/null; then
    echo "❌ npm is not installed. Please install npm first."
    exit 1
fi

echo "✅ Node.js and npm are installed"

# Install dependencies
echo "📦 Installing dependencies..."
npm install

# Create environment file if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env file from template..."
    cp .env.example .env
    echo "⚠️  Please edit .env file to configure your Dryad.AI backend URL"
fi

# Build the project
echo "🔨 Building the project..."
npm run build

echo ""
echo "🎉 Setup complete!"
echo ""
echo "To start the chat interface:"
echo "  npm start"
echo ""
echo "Configuration:"
echo "  - Backend URL: http://localhost:8000 (default)"
echo "  - Edit .env file to change configuration"
echo ""
echo "Make sure your Dryad.AI backend is running before starting the chat interface!"