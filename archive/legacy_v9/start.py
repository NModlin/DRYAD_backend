#!/usr/bin/env python3
"""
DRYAD.AI Backend Startup Script
Easy startup for different deployment modes with auto-service management.
"""

import os
import sys
import subprocess
import argparse
import time
from pathlib import Path

# Add scripts directory to path for service manager
sys.path.insert(0, str(Path(__file__).parent / "scripts"))

try:
    from manage_services import ServiceManager
    SERVICE_MANAGER_AVAILABLE = True
except ImportError:
    SERVICE_MANAGER_AVAILABLE = False

def check_gpu_status():
    """Check and report GPU status for optimal performance."""
    # Silent mode - no hardware detection output
    pass

def check_service(name, url, timeout=30):
    """Check if a service is available."""
    print(f"Checking {name} at {url}...")
    
    import requests
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                print(f"✅ {name} is available")
                return True
        except:
            pass
        time.sleep(2)
    
    print(f"⚠️ {name} is not available (will use fallback)")
    return False

def ensure_services_running():
    """Ensure external services are running."""
    if not SERVICE_MANAGER_AVAILABLE:
        return False

    manager = ServiceManager()

    # Check if services are already running
    all_running = all(
        manager.check_service_health(service)
        for service in ["weaviate", "redis", "ollama"]
    )

    if all_running:
        print("✅ All services already running")
        return True

    # Start services
    print("🚀 Starting external services (Weaviate, Redis, Ollama)...")
    if manager.start_services(detached=True):
        print("✅ Services started successfully")
        return True
    else:
        print("⚠️  Services failed to start (will use fallbacks)")
        return False

def start_basic_mode(auto_services=True):
    """Start in basic mode with optional auto-service management."""
    print("Starting DRYAD.AI Backend...")

    # Auto-start external services
    if auto_services and SERVICE_MANAGER_AVAILABLE:
        ensure_services_running()
        print()

    # Set environment variables
    os.environ["BASIC_MODE"] = "true"
    os.environ["DATABASE_URL"] = "sqlite:///./data/DRYAD.AI.db"

    # Configure service URLs if available
    os.environ["WEAVIATE_URL"] = "http://localhost:8080"
    os.environ["REDIS_URL"] = "redis://localhost:6379"
    os.environ["OLLAMA_BASE_URL"] = "http://localhost:11434"

    # Start the server
    cmd = [
        sys.executable, "-m", "uvicorn",
        "app.main:app",
        "--host", "127.0.0.1",
        "--port", "8000",
        "--reload",
        "--log-level", "warning"  # Only show warnings and errors
    ]

    print("Server: http://localhost:8000")
    print("API Docs: http://localhost:8000/docs")
    print("Press Ctrl+C to stop\n")

    try:
        subprocess.run(cmd)
    except KeyboardInterrupt:
        print("\nServer stopped")

def start_development_mode(auto_services=True):
    """Start in development mode with auto-service management."""
    print("🛠️ Starting DRYAD.AI Backend in Development Mode...")

    # Auto-start external services
    if auto_services and SERVICE_MANAGER_AVAILABLE:
        ensure_services_running()

    # Set environment variables for services
    os.environ["WEAVIATE_URL"] = "http://localhost:8080"
    os.environ["REDIS_URL"] = "redis://localhost:6379"
    os.environ["OLLAMA_BASE_URL"] = "http://localhost:11434"

    # Start the server
    cmd = [
        sys.executable, "-m", "uvicorn",
        "app.main:app",
        "--host", "127.0.0.1",
        "--port", "8000",
        "--reload",
        "--log-level", "warning"
    ]

    print("\nStarting server...")
    print("Server: http://localhost:8000")
    print("API Docs: http://localhost:8000/docs")
    print("Press Ctrl+C to stop\n")

    try:
        subprocess.run(cmd)
    except KeyboardInterrupt:
        print("\n👋 Server stopped")

def start_docker_basic():
    """Start Docker basic mode."""
    print("🐳 Starting DRYAD.AI Backend with Docker (Basic Mode)...")
    
    cmd = ["docker-compose", "-f", "docker-compose.basic.yml", "up"]
    
    print("Starting Docker containers...")
    print("Server will be available at: http://localhost:8000/docs")
    print("Press Ctrl+C to stop")
    
    try:
        subprocess.run(cmd)
    except KeyboardInterrupt:
        print("\n👋 Stopping containers...")
        subprocess.run(["docker-compose", "-f", "docker-compose.basic.yml", "down"])

def start_docker_full():
    """Start Docker full mode."""
    print("🐳 Starting DRYAD.AI Backend with Docker (Full Mode)...")
    
    cmd = ["docker-compose", "-f", "docker-compose.full.yml", "up"]
    
    print("Starting Docker containers...")
    print("This may take a few minutes on first run...")
    print("\nServices will be available at:")
    print("- Backend: http://localhost:8000/docs")
    print("- Weaviate: http://localhost:8080")
    print("- Ollama: http://localhost:11434")
    print("\nPress Ctrl+C to stop")
    
    try:
        subprocess.run(cmd)
    except KeyboardInterrupt:
        print("\n👋 Stopping containers...")
        subprocess.run(["docker-compose", "-f", "docker-compose.full.yml", "down"])

def main():
    """Main startup function."""
    parser = argparse.ArgumentParser(
        description="DRYAD.AI Backend Startup with Auto-Service Management"
    )
    parser.add_argument(
        "mode",
        choices=["basic", "development", "docker-basic", "docker-full"],
        help="Startup mode"
    )
    parser.add_argument(
        "--no-services",
        action="store_true",
        help="Don't auto-start external services (Weaviate, Redis, Ollama)"
    )

    args = parser.parse_args()

    # Silent startup - no banner
    check_gpu_status()

    auto_services = not args.no_services

    if args.mode == "basic":
        start_basic_mode(auto_services=auto_services)
    elif args.mode == "development":
        start_development_mode(auto_services=auto_services)
    elif args.mode == "docker-basic":
        start_docker_basic()
    elif args.mode == "docker-full":
        start_docker_full()

if __name__ == "__main__":
    main()
