#!/usr/bin/env python3
"""
DRYAD.AI Service Manager
Automatically start, stop, and monitor Weaviate, Redis, and Ollama services.
"""

import os
import sys
import time
import subprocess
import argparse
import requests
from pathlib import Path

class ServiceManager:
    """Manage external services for DRYAD.AI."""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.compose_file = self.project_root / "docker-compose.services.yml"
        
        self.services = {
            "weaviate": {
                "name": "Weaviate Vector Database",
                "url": "http://localhost:8080/v1/.well-known/ready",
                "port": 8080,
                "container": "gremlins-weaviate"
            },
            "redis": {
                "name": "Redis Cache",
                "url": None,  # Redis doesn't have HTTP endpoint
                "port": 6379,
                "container": "gremlins-redis"
            },
            "ollama": {
                "name": "Ollama LLM Server",
                "url": "http://localhost:11434/api/tags",
                "port": 11434,
                "container": "gremlins-ollama"
            }
        }
    
    def check_docker(self):
        """Check if Docker is installed and running."""
        try:
            result = subprocess.run(
                ["docker", "ps"],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False
    
    def check_service_health(self, service_key):
        """Check if a service is healthy."""
        service = self.services[service_key]
        
        # Special handling for Redis
        if service_key == "redis":
            try:
                import redis
                r = redis.Redis(host='localhost', port=6379, db=0, socket_timeout=2)
                r.ping()
                return True
            except:
                return False
        
        # HTTP-based health check
        if service["url"]:
            try:
                response = requests.get(service["url"], timeout=5)
                return response.status_code == 200
            except:
                return False
        
        return False
    
    def check_container_running(self, container_name):
        """Check if a Docker container is running."""
        try:
            result = subprocess.run(
                ["docker", "ps", "--filter", f"name={container_name}", "--format", "{{.Names}}"],
                capture_output=True,
                text=True,
                timeout=5
            )
            return container_name in result.stdout
        except:
            return False
    
    def start_services(self, detached=True):
        """Start all services using Docker Compose."""
        print("🚀 Starting DRYAD.AI Services...")
        print("=" * 50)
        
        if not self.check_docker():
            print("❌ Docker is not running!")
            print("   Please start Docker Desktop and try again.")
            return False
        
        print("✅ Docker is running")
        print(f"📁 Using compose file: {self.compose_file}")
        
        # Start services
        cmd = ["docker-compose", "-f", str(self.compose_file), "up"]
        if detached:
            cmd.append("-d")
        
        print("\n🐳 Starting containers...")
        try:
            result = subprocess.run(cmd, cwd=self.project_root)
            if result.returncode != 0:
                print("❌ Failed to start services")
                return False
        except KeyboardInterrupt:
            print("\n⚠️  Startup interrupted")
            return False
        
        if detached:
            print("\n⏳ Waiting for services to be healthy...")
            self.wait_for_services()
        
        return True
    
    def wait_for_services(self, timeout=120):
        """Wait for all services to become healthy."""
        start_time = time.time()
        services_ready = {key: False for key in self.services.keys()}
        
        while time.time() - start_time < timeout:
            all_ready = True
            
            for service_key in self.services.keys():
                if not services_ready[service_key]:
                    if self.check_service_health(service_key):
                        services_ready[service_key] = True
                        service_name = self.services[service_key]["name"]
                        print(f"   ✅ {service_name} is ready")
                    else:
                        all_ready = False
            
            if all_ready:
                print("\n🎉 All services are ready!")
                return True
            
            time.sleep(2)
        
        print("\n⚠️  Timeout waiting for services")
        for service_key, ready in services_ready.items():
            if not ready:
                service_name = self.services[service_key]["name"]
                print(f"   ❌ {service_name} is not ready")
        
        return False
    
    def stop_services(self):
        """Stop all services."""
        print("🛑 Stopping DRYAD.AI Services...")
        
        cmd = ["docker-compose", "-f", str(self.compose_file), "down"]
        
        try:
            subprocess.run(cmd, cwd=self.project_root)
            print("✅ Services stopped")
            return True
        except Exception as e:
            print(f"❌ Failed to stop services: {e}")
            return False
    
    def restart_services(self):
        """Restart all services."""
        print("🔄 Restarting DRYAD.AI Services...")
        self.stop_services()
        time.sleep(2)
        return self.start_services()
    
    def status(self):
        """Show status of all services."""
        print("📊 DRYAD.AI Services Status")
        print("=" * 50)
        
        if not self.check_docker():
            print("❌ Docker is not running")
            return
        
        print("✅ Docker is running\n")
        
        for service_key, service in self.services.items():
            name = service["name"]
            container = service["container"]
            port = service["port"]
            
            # Check container
            container_running = self.check_container_running(container)
            
            # Check health
            healthy = self.check_service_health(service_key) if container_running else False
            
            # Status display
            status_icon = "✅" if healthy else ("⚠️" if container_running else "❌")
            status_text = "Healthy" if healthy else ("Starting" if container_running else "Stopped")
            
            print(f"{status_icon} {name}")
            print(f"   Container: {container}")
            print(f"   Port: {port}")
            print(f"   Status: {status_text}")
            print()
    
    def logs(self, service=None, follow=False):
        """Show logs for services."""
        cmd = ["docker-compose", "-f", str(self.compose_file), "logs"]
        
        if follow:
            cmd.append("-f")
        
        if service:
            cmd.append(service)
        
        try:
            subprocess.run(cmd, cwd=self.project_root)
        except KeyboardInterrupt:
            print("\n")
    
    def pull_images(self):
        """Pull latest Docker images."""
        print("📥 Pulling latest Docker images...")
        
        cmd = ["docker-compose", "-f", str(self.compose_file), "pull"]
        
        try:
            subprocess.run(cmd, cwd=self.project_root)
            print("✅ Images updated")
            return True
        except Exception as e:
            print(f"❌ Failed to pull images: {e}")
            return False
    
    def setup_ollama_models(self):
        """Download recommended Ollama models."""
        print("📥 Setting up Ollama models...")
        
        if not self.check_service_health("ollama"):
            print("❌ Ollama is not running. Start services first.")
            return False
        
        models = [
            "llama3.2:3b",
            "llama3.2:1b",
            "tinyllama"
        ]
        
        for model in models:
            print(f"\n📦 Pulling {model}...")
            try:
                subprocess.run(
                    ["docker", "exec", "gremlins-ollama", "ollama", "pull", model],
                    check=True
                )
                print(f"   ✅ {model} downloaded")
            except subprocess.CalledProcessError:
                print(f"   ⚠️  Failed to download {model}")
        
        print("\n✅ Ollama setup complete")
        return True


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Manage DRYAD.AI external services (Weaviate, Redis, Ollama)"
    )
    
    parser.add_argument(
        "command",
        choices=["start", "stop", "restart", "status", "logs", "pull", "setup-ollama"],
        help="Command to execute"
    )
    
    parser.add_argument(
        "--service",
        choices=["weaviate", "redis", "ollama"],
        help="Specific service (for logs command)"
    )
    
    parser.add_argument(
        "--follow", "-f",
        action="store_true",
        help="Follow log output"
    )
    
    parser.add_argument(
        "--foreground",
        action="store_true",
        help="Run services in foreground (not detached)"
    )
    
    args = parser.parse_args()
    
    manager = ServiceManager()
    
    if args.command == "start":
        success = manager.start_services(detached=not args.foreground)
        sys.exit(0 if success else 1)
    
    elif args.command == "stop":
        success = manager.stop_services()
        sys.exit(0 if success else 1)
    
    elif args.command == "restart":
        success = manager.restart_services()
        sys.exit(0 if success else 1)
    
    elif args.command == "status":
        manager.status()
    
    elif args.command == "logs":
        manager.logs(service=args.service, follow=args.follow)
    
    elif args.command == "pull":
        success = manager.pull_images()
        sys.exit(0 if success else 1)
    
    elif args.command == "setup-ollama":
        success = manager.setup_ollama_models()
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

