"""
Production Deployment System for DRYAD.AI Backend
Provides Docker containerization, health checks, and deployment automation.
"""

import os
import json
import yaml
import asyncio
import subprocess
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from pathlib import Path

from app.core.logging_config import get_logger
from app.core.monitoring import health_monitor
from app.core.advanced_security import api_key_manager

logger = get_logger(__name__)

@dataclass
class DeploymentConfig:
    """Deployment configuration."""
    environment: str  # development, staging, production
    replicas: int = 1
    cpu_limit: str = "1000m"
    memory_limit: str = "2Gi"
    cpu_request: str = "500m"
    memory_request: str = "1Gi"
    port: int = 8000
    health_check_path: str = "/health"
    readiness_check_path: str = "/ready"
    enable_monitoring: bool = True
    enable_security: bool = True
    log_level: str = "INFO"

class DockerManager:
    """Docker container management."""
    
    def __init__(self):
        self.dockerfile_template = """
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \\
    gcc \\
    g++ \\
    curl \\
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user
RUN useradd --create-home --shell /bin/bash app \\
    && chown -R app:app /app
USER app

# Expose port
EXPOSE {port}

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \\
    CMD curl -f http://localhost:{port}/health || exit 1

# Run application
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "{port}"]
"""
    
    def generate_dockerfile(self, config: DeploymentConfig) -> str:
        """Generate Dockerfile content."""
        return self.dockerfile_template.format(port=config.port)
    
    def generate_docker_compose(self, config: DeploymentConfig) -> Dict[str, Any]:
        """Generate docker-compose.yml content."""
        return {
            "version": "3.8",
            "services": {
                "DRYAD.AI-backend": {
                    "build": ".",
                    "ports": [f"{config.port}:{config.port}"],
                    "environment": {
                        "LOG_LEVEL": config.log_level,
                        "ENVIRONMENT": config.environment,
                        "DATABASE_URL": "${DATABASE_URL}",
                        "REDIS_URL": "${REDIS_URL}",
                        "WEAVIATE_URL": "${WEAVIATE_URL}",
                        "OPENAI_API_KEY": "${OPENAI_API_KEY}",
                        "ANTHROPIC_API_KEY": "${ANTHROPIC_API_KEY}"
                    },
                    "volumes": [
                        "./logs:/app/logs",
                        "./data:/app/data"
                    ],
                    "restart": "unless-stopped",
                    "healthcheck": {
                        "test": [f"curl -f http://localhost:{config.port}/health || exit 1"],
                        "interval": "30s",
                        "timeout": "10s",
                        "retries": 3,
                        "start_period": "40s"
                    },
                    "deploy": {
                        "replicas": config.replicas,
                        "resources": {
                            "limits": {
                                "cpus": config.cpu_limit,
                                "memory": config.memory_limit
                            },
                            "reservations": {
                                "cpus": config.cpu_request,
                                "memory": config.memory_request
                            }
                        }
                    }
                },
                "redis": {
                    "image": "redis:7-alpine",
                    "ports": ["6379:6379"],
                    "volumes": ["redis_data:/data"],
                    "restart": "unless-stopped"
                },
                "weaviate": {
                    "image": "semitechnologies/weaviate:1.22.4",
                    "ports": ["8080:8080"],
                    "environment": {
                        "QUERY_DEFAULTS_LIMIT": "25",
                        "AUTHENTICATION_ANONYMOUS_ACCESS_ENABLED": "true",
                        "PERSISTENCE_DATA_PATH": "/var/lib/weaviate",
                        "DEFAULT_VECTORIZER_MODULE": "none",
                        "ENABLE_MODULES": "text2vec-openai,text2vec-cohere,text2vec-huggingface,ref2vec-centroid,generative-openai,qna-openai"
                    },
                    "volumes": ["weaviate_data:/var/lib/weaviate"],
                    "restart": "unless-stopped"
                }
            },
            "volumes": {
                "redis_data": {},
                "weaviate_data": {}
            }
        }

class KubernetesManager:
    """Kubernetes deployment management."""
    
    def generate_deployment_yaml(self, config: DeploymentConfig) -> Dict[str, Any]:
        """Generate Kubernetes deployment YAML."""
        return {
            "apiVersion": "apps/v1",
            "kind": "Deployment",
            "metadata": {
                "name": "DRYAD.AI-backend",
                "labels": {
                    "app": "DRYAD.AI-backend",
                    "version": "v1"
                }
            },
            "spec": {
                "replicas": config.replicas,
                "selector": {
                    "matchLabels": {
                        "app": "DRYAD.AI-backend"
                    }
                },
                "template": {
                    "metadata": {
                        "labels": {
                            "app": "DRYAD.AI-backend"
                        }
                    },
                    "spec": {
                        "containers": [{
                            "name": "DRYAD.AI-backend",
                            "image": "DRYAD.AI-backend:latest",
                            "ports": [{
                                "containerPort": config.port
                            }],
                            "env": [
                                {"name": "LOG_LEVEL", "value": config.log_level},
                                {"name": "ENVIRONMENT", "value": config.environment},
                                {"name": "DATABASE_URL", "valueFrom": {"secretKeyRef": {"name": "DRYAD.AI-secrets", "key": "database-url"}}},
                                {"name": "REDIS_URL", "valueFrom": {"secretKeyRef": {"name": "DRYAD.AI-secrets", "key": "redis-url"}}},
                                {"name": "WEAVIATE_URL", "valueFrom": {"secretKeyRef": {"name": "DRYAD.AI-secrets", "key": "weaviate-url"}}},
                                {"name": "OPENAI_API_KEY", "valueFrom": {"secretKeyRef": {"name": "DRYAD.AI-secrets", "key": "openai-api-key"}}},
                                {"name": "ANTHROPIC_API_KEY", "valueFrom": {"secretKeyRef": {"name": "DRYAD.AI-secrets", "key": "anthropic-api-key"}}}
                            ],
                            "resources": {
                                "limits": {
                                    "cpu": config.cpu_limit,
                                    "memory": config.memory_limit
                                },
                                "requests": {
                                    "cpu": config.cpu_request,
                                    "memory": config.memory_request
                                }
                            },
                            "livenessProbe": {
                                "httpGet": {
                                    "path": config.health_check_path,
                                    "port": config.port
                                },
                                "initialDelaySeconds": 30,
                                "periodSeconds": 10
                            },
                            "readinessProbe": {
                                "httpGet": {
                                    "path": config.readiness_check_path,
                                    "port": config.port
                                },
                                "initialDelaySeconds": 5,
                                "periodSeconds": 5
                            }
                        }]
                    }
                }
            }
        }
    
    def generate_service_yaml(self, config: DeploymentConfig) -> Dict[str, Any]:
        """Generate Kubernetes service YAML."""
        return {
            "apiVersion": "v1",
            "kind": "Service",
            "metadata": {
                "name": "DRYAD.AI-backend-service",
                "labels": {
                    "app": "DRYAD.AI-backend"
                }
            },
            "spec": {
                "selector": {
                    "app": "DRYAD.AI-backend"
                },
                "ports": [{
                    "protocol": "TCP",
                    "port": 80,
                    "targetPort": config.port
                }],
                "type": "LoadBalancer"
            }
        }

class HealthCheckManager:
    """Health check and readiness probe management."""
    
    async def health_check(self) -> Dict[str, Any]:
        """Comprehensive health check."""
        health_status = {
            "status": "healthy",
            "timestamp": asyncio.get_event_loop().time(),
            "version": "1.0.0",
            "environment": os.getenv("ENVIRONMENT", "development"),
            "checks": {}
        }
        
        # Database check
        try:
            from app.database.database import async_engine
            async with async_engine.begin() as conn:
                await conn.execute("SELECT 1")
            health_status["checks"]["database"] = {"status": "healthy"}
        except Exception as e:
            health_status["checks"]["database"] = {"status": "unhealthy", "error": str(e)}
            health_status["status"] = "unhealthy"
        
        # Redis check
        try:
            from app.core.caching import cache
            cache.set("health_check", "ok", ttl=10)
            if cache.get("health_check") == "ok":
                health_status["checks"]["redis"] = {"status": "healthy"}
            else:
                health_status["checks"]["redis"] = {"status": "unhealthy", "error": "Cache test failed"}
                health_status["status"] = "degraded"
        except Exception as e:
            health_status["checks"]["redis"] = {"status": "unhealthy", "error": str(e)}
            health_status["status"] = "unhealthy"
        
        # LLM service check
        try:
            from app.core.llm_config import _llm_pools
            if _llm_pools:
                health_status["checks"]["llm"] = {"status": "healthy", "pools": len(_llm_pools)}
            else:
                health_status["checks"]["llm"] = {"status": "degraded", "error": "No LLM pools available"}
        except Exception as e:
            health_status["checks"]["llm"] = {"status": "unhealthy", "error": str(e)}
        
        return health_status
    
    async def readiness_check(self) -> Dict[str, Any]:
        """Readiness probe check."""
        readiness_status = {
            "ready": True,
            "timestamp": asyncio.get_event_loop().time(),
            "checks": {}
        }
        
        # Check if all critical services are ready
        health = await self.health_check()
        
        critical_services = ["database", "redis"]
        for service in critical_services:
            if service in health["checks"]:
                service_status = health["checks"][service]["status"]
                readiness_status["checks"][service] = {"ready": service_status == "healthy"}
                if service_status != "healthy":
                    readiness_status["ready"] = False
        
        return readiness_status

class DeploymentManager:
    """Main deployment management system."""
    
    def __init__(self):
        self.docker_manager = DockerManager()
        self.k8s_manager = KubernetesManager()
        self.health_manager = HealthCheckManager()
    
    def generate_deployment_files(self, config: DeploymentConfig, output_dir: str = "deployment"):
        """Generate all deployment files."""
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        # Generate Dockerfile
        dockerfile_content = self.docker_manager.generate_dockerfile(config)
        with open(output_path / "Dockerfile", "w") as f:
            f.write(dockerfile_content)
        
        # Generate docker-compose.yml
        compose_config = self.docker_manager.generate_docker_compose(config)
        with open(output_path / "docker-compose.yml", "w") as f:
            yaml.dump(compose_config, f, default_flow_style=False)
        
        # Generate Kubernetes files
        deployment_yaml = self.k8s_manager.generate_deployment_yaml(config)
        with open(output_path / "k8s-deployment.yaml", "w") as f:
            yaml.dump(deployment_yaml, f, default_flow_style=False)
        
        service_yaml = self.k8s_manager.generate_service_yaml(config)
        with open(output_path / "k8s-service.yaml", "w") as f:
            yaml.dump(service_yaml, f, default_flow_style=False)
        
        # Generate environment template
        env_template = self._generate_env_template()
        with open(output_path / ".env.template", "w") as f:
            f.write(env_template)
        
        logger.info(f"Deployment files generated in {output_path}")
    
    def _generate_env_template(self) -> str:
        """Generate environment variables template."""
        return """# DRYAD.AI Backend Environment Configuration

# Application Settings
ENVIRONMENT=production
LOG_LEVEL=INFO
PORT=8000

# Database Configuration - SECURE THESE VALUES
DATABASE_URL=postgresql://user:CHANGE_PASSWORD@localhost:5432/DRYAD.AI

# Redis Configuration
REDIS_URL=redis://localhost:6379/0

# Weaviate Configuration
WEAVIATE_URL=http://localhost:8080

# AI Service API Keys - SECURE THESE VALUES
# OPENAI_API_KEY=sk-your-actual-openai-key-here
# ANTHROPIC_API_KEY=your-actual-anthropic-key-here

# Security Configuration - GENERATE SECURE VALUES
# Generate with: python -c "import secrets; print(secrets.token_urlsafe(48))"
# REQUEST_SIGNING_SECRET=
# ENCRYPTION_PASSWORD=
# ENCRYPTION_SALT=

# Monitoring Configuration
ENABLE_METRICS=true
METRICS_PORT=9090
"""

# Global deployment manager
deployment_manager = DeploymentManager()

async def initialize_deployment():
    """Initialize deployment systems."""
    logger.info("Initializing deployment systems")
    
    # Generate deployment files for different environments
    environments = [
        DeploymentConfig(environment="development", replicas=1, log_level="DEBUG"),
        DeploymentConfig(environment="staging", replicas=2, log_level="INFO"),
        DeploymentConfig(environment="production", replicas=3, log_level="WARNING", enable_security=True)
    ]
    
    for config in environments:
        deployment_manager.generate_deployment_files(config, f"deployment/{config.environment}")
    
    logger.info("Deployment systems initialized")

async def health_endpoint():
    """Health check endpoint handler."""
    return await deployment_manager.health_manager.health_check()

async def readiness_endpoint():
    """Readiness check endpoint handler."""
    return await deployment_manager.health_manager.readiness_check()
