#!/usr/bin/env python3
"""
DRYAD.AI External Services Setup Script
=========================================

This script helps set up and configure external services for DRYAD.AI:
- Redis (for caching and task queue)
- Weaviate (for vector search)
- Docker Compose orchestration

Usage:
    python setup_external_services.py [--check] [--setup-docker] [--start-services]
"""

import os
import sys
import subprocess
import time
import argparse
from pathlib import Path
from typing import Dict, List, Tuple, Optional

def check_docker_available() -> bool:
    """Check if Docker is available and running."""
    try:
        result = subprocess.run(['docker', '--version'], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print(f"✅ Docker available: {result.stdout.strip()}")
            return True
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass
    
    print("❌ Docker not available or not running")
    return False

def check_docker_compose_available() -> bool:
    """Check if Docker Compose is available."""
    try:
        result = subprocess.run(['docker', 'compose', 'version'], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print(f"✅ Docker Compose available: {result.stdout.strip()}")
            return True
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass
    
    print("❌ Docker Compose not available")
    return False

def check_service_status(service_name: str, host: str, port: int, timeout: int = 5) -> bool:
    """Check if a service is running on the specified host:port."""
    import socket
    
    try:
        with socket.create_connection((host, port), timeout=timeout):
            print(f"✅ {service_name}: Running on {host}:{port}")
            return True
    except (socket.timeout, ConnectionRefusedError, OSError):
        print(f"❌ {service_name}: Not running on {host}:{port}")
        return False

def test_redis_connection(redis_url: str = "redis://localhost:6379") -> bool:
    """Test Redis connection."""
    try:
        import redis
        r = redis.from_url(redis_url, socket_connect_timeout=5)
        r.ping()
        info = r.info()
        print(f"✅ Redis: Connected (version {info.get('redis_version', 'unknown')})")
        return True
    except Exception as e:
        print(f"❌ Redis: Connection failed - {str(e)[:50]}...")
        return False

def test_weaviate_connection(weaviate_url: str = "http://localhost:8080") -> bool:
    """Test Weaviate connection."""
    try:
        import requests
        response = requests.get(f"{weaviate_url}/v1/meta", timeout=5)
        if response.status_code == 200:
            meta = response.json()
            version = meta.get('version', 'unknown')
            print(f"✅ Weaviate: Connected (version {version})")
            return True
        else:
            print(f"❌ Weaviate: HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Weaviate: Connection failed - {str(e)[:50]}...")
        return False

def create_docker_compose_services() -> str:
    """Create a Docker Compose configuration for external services."""
    compose_content = """version: '3.8'

services:
  redis:
    image: redis:7-alpine
    container_name: gremlins-redis
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    environment:
      REDIS_PASSWORD: '${REDIS_PASSWORD:-redis-secure-password-change-in-production}'
    command: >
      redis-server
      --appendonly yes
      --requirepass ${REDIS_PASSWORD:-redis-secure-password-change-in-production}
      --maxmemory 256mb
      --maxmemory-policy allkeys-lru
      --tcp-keepalive 60
      --timeout 300
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "redis-cli", "--no-auth-warning", "-a", "${REDIS_PASSWORD:-redis-secure-password-change-in-production}", "ping"]
      interval: 10s
      timeout: 5s
      retries: 3

  weaviate:
    image: semitechnologies/weaviate:1.22.4
    container_name: gremlins-weaviate
    ports:
      - "8080:8080"
    environment:
      QUERY_DEFAULTS_LIMIT: 25
      AUTHENTICATION_ANONYMOUS_ACCESS_ENABLED: 'false'
      AUTHENTICATION_APIKEY_ENABLED: 'true'
      AUTHENTICATION_APIKEY_ALLOWED_KEYS: '${WEAVIATE_API_KEY:-weaviate-secure-key-change-in-production}'
      AUTHENTICATION_APIKEY_USERS: 'DRYAD.AI-user'
      AUTHORIZATION_ADMINLIST_ENABLED: 'true'
      AUTHORIZATION_ADMINLIST_USERS: 'DRYAD.AI-user'
      PERSISTENCE_DATA_PATH: '/var/lib/weaviate'
      DEFAULT_VECTORIZER_MODULE: 'none'
      ENABLE_MODULES: 'text2vec-openai,text2vec-cohere,text2vec-huggingface,ref2vec-centroid,generative-openai,qna-openai'
      CLUSTER_HOSTNAME: 'node1'
    volumes:
      - weaviate_data:/var/lib/weaviate
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/v1/meta"]
      interval: 10s
      timeout: 5s
      retries: 3

volumes:
  redis_data:
    driver: local
  weaviate_data:
    driver: local

networks:
  default:
    name: gremlins-network
"""
    return compose_content

def setup_docker_services():
    """Set up Docker Compose services."""
    print("\n🐳 SETTING UP DOCKER SERVICES")
    print("="*40)
    
    # Check if docker-compose.external.yml exists
    compose_file = Path("docker-compose.external.yml")
    
    if not compose_file.exists():
        print("📝 Creating docker-compose.external.yml...")
        compose_content = create_docker_compose_services()
        
        with open(compose_file, 'w') as f:
            f.write(compose_content)
        
        print("✅ Created docker-compose.external.yml")
    else:
        print("✅ docker-compose.external.yml already exists")
    
    return compose_file

def start_services(compose_file: Path) -> bool:
    """Start external services using Docker Compose."""
    print(f"\n🚀 STARTING SERVICES")
    print("="*30)
    
    try:
        # Start services
        print("Starting Redis and Weaviate...")
        result = subprocess.run([
            'docker', 'compose', '-f', str(compose_file), 'up', '-d'
        ], capture_output=True, text=True, timeout=120)
        
        if result.returncode != 0:
            print(f"❌ Failed to start services: {result.stderr}")
            return False
        
        print("✅ Services started successfully")
        
        # Wait for services to be ready
        print("\n⏳ Waiting for services to be ready...")
        max_wait = 60
        start_time = time.time()
        
        while time.time() - start_time < max_wait:
            redis_ready = check_service_status("Redis", "localhost", 6379, 2)
            weaviate_ready = check_service_status("Weaviate", "localhost", 8080, 2)
            
            if redis_ready and weaviate_ready:
                print("🎉 All services are ready!")
                return True
            
            time.sleep(5)
        
        print("⚠️  Services started but may not be fully ready yet")
        return True
        
    except subprocess.TimeoutExpired:
        print("❌ Timeout starting services")
        return False
    except Exception as e:
        print(f"❌ Error starting services: {e}")
        return False

def check_all_services():
    """Check status of all external services."""
    print("\n🔍 CHECKING ALL EXTERNAL SERVICES")
    print("="*40)
    
    services_status = {}
    
    # Check Redis
    services_status['redis'] = test_redis_connection()
    
    # Check Weaviate  
    services_status['weaviate'] = test_weaviate_connection()
    
    # Check Database (SQLite)
    try:
        from app.core.config import config
        db_path = config.DATABASE_URL.replace('sqlite:///', '')
        if Path(db_path).exists():
            print("✅ Database (SQLite): File exists")
            services_status['database'] = True
        else:
            print("⚠️  Database (SQLite): File not found")
            services_status['database'] = False
    except Exception as e:
        print(f"❌ Database: Check failed - {e}")
        services_status['database'] = False
    
    # Summary
    print(f"\n📊 SERVICES SUMMARY")
    print("="*25)
    working = sum(services_status.values())
    total = len(services_status)
    
    for service, status in services_status.items():
        status_icon = "✅" if status else "❌"
        print(f"{status_icon} {service.capitalize()}: {'Working' if status else 'Not available'}")
    
    print(f"\n🎯 Status: {working}/{total} services working")
    
    if working == total:
        print("🎉 All services are operational!")
    elif working >= 1:
        print("⚠️  Some services are working, system partially functional")
    else:
        print("❌ No external services available, using fallback modes")
    
    return services_status

def show_service_management_guide():
    """Show guide for managing external services."""
    print("\n" + "="*60)
    print("🛠️  EXTERNAL SERVICES MANAGEMENT GUIDE")
    print("="*60)
    
    print("\n📋 DOCKER COMPOSE COMMANDS:")
    print("  # Start services")
    print("  docker compose -f docker-compose.external.yml up -d")
    print()
    print("  # Stop services")
    print("  docker compose -f docker-compose.external.yml down")
    print()
    print("  # View logs")
    print("  docker compose -f docker-compose.external.yml logs -f")
    print()
    print("  # Check status")
    print("  docker compose -f docker-compose.external.yml ps")
    
    print("\n🔧 INDIVIDUAL SERVICE COMMANDS:")
    print("  # Redis CLI")
    print("  docker exec -it gremlins-redis redis-cli")
    print()
    print("  # Weaviate API")
    print("  curl http://localhost:8080/v1/meta")
    
    print("\n⚠️  TROUBLESHOOTING:")
    print("  1. Port conflicts: Check if ports 6379 (Redis) or 8080 (Weaviate) are in use")
    print("  2. Docker issues: Restart Docker Desktop")
    print("  3. Permission issues: Run with administrator privileges")
    print("  4. Network issues: Check firewall settings")
    
    print("\n✅ VERIFICATION:")
    print("  python setup_external_services.py --check")

def main():
    parser = argparse.ArgumentParser(description="Setup DRYAD.AI External Services")
    parser.add_argument("--check", action="store_true",
                       help="Check status of all external services")
    parser.add_argument("--setup-docker", action="store_true",
                       help="Create Docker Compose configuration")
    parser.add_argument("--start-services", action="store_true",
                       help="Start external services with Docker Compose")
    parser.add_argument("--guide", action="store_true",
                       help="Show service management guide")
    
    args = parser.parse_args()
    
    if args.check:
        check_all_services()
    
    if args.setup_docker:
        if not check_docker_available() or not check_docker_compose_available():
            print("\n❌ Docker/Docker Compose required for setup")
            sys.exit(1)
        
        compose_file = setup_docker_services()
        print(f"\n✅ Docker setup complete!")
        print(f"   Configuration: {compose_file}")
        print(f"   Next: python setup_external_services.py --start-services")
    
    if args.start_services:
        if not check_docker_available() or not check_docker_compose_available():
            print("\n❌ Docker/Docker Compose required to start services")
            sys.exit(1)
        
        compose_file = Path("docker-compose.external.yml")
        if not compose_file.exists():
            print("❌ docker-compose.external.yml not found")
            print("   Run: python setup_external_services.py --setup-docker")
            sys.exit(1)
        
        if start_services(compose_file):
            print("\n🎉 Services started successfully!")
            print("   Run: python setup_external_services.py --check")
        else:
            print("\n❌ Failed to start services")
            sys.exit(1)
    
    if args.guide:
        show_service_management_guide()
    
    if not any([args.check, args.setup_docker, args.start_services, args.guide]):
        print("DRYAD.AI External Services Setup")
        print("Usage: python setup_external_services.py --help")
        print("\nQuick commands:")
        print("  --check           Check service status")
        print("  --setup-docker    Create Docker configuration")
        print("  --start-services  Start all services")
        print("  --guide           Show management guide")

if __name__ == "__main__":
    main()
