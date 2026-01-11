#!/bin/bash

# Standalone University System Launcher

echo "🎓 Starting University System Standalone App..."

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
  echo "❌ Docker is not running. Please start Docker and try again."
  exit 1
fi

# Check for .env file, create default if missing
if [ ! -f .env ]; then
    echo "⚠️  No .env file found. Creating default..."
    echo "SECRET_KEY=dev_secret_key_change_me" > .env
    echo "ALGORITHM=HS256" >> .env
    echo "ACCESS_TOKEN_EXPIRE_MINUTES=30" >> .env
fi

# Stop existing containers
echo "🔄 Stopping any existing containers..."
docker compose -f docker-compose.university.yml down

# Build and start
echo "🚀 Building and starting services..."
docker compose -f docker-compose.university.yml up -d --build

# Wait for services to be ready
echo "⏳ Waiting for services to startup..."
sleep 10

# Check status
if docker compose -f docker-compose.university.yml ps | grep -q "Up"; then
    echo "✅ University System is RUNNING!"
    echo ""
    echo "🖥️  Frontend: http://localhost:3333"
    echo "🔌 Backend API: http://localhost:8000/docs"
    echo ""
    echo "Run 'docker compose -f docker-compose.university.yml logs -f' to see logs."
else
    echo "❌ Startup failed. Check logs."
    docker compose -f docker-compose.university.yml logs
fi
