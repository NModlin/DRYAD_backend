# Docker Configuration Files

This directory contains various Docker Compose configurations for different deployment scenarios. **Note**: With the new unified installation approach, most deployments should use the main configurations in the root directory.

## 📁 Files

### **Main Configurations (Recommended)**
- **docker-compose.yml** (root) - Unified installation with all features, CPU-optimized
- **docker-compose.gpu.yml** (root) - GPU-accelerated deployment with NVIDIA Docker support
- **Dockerfile** (root) - Unified production build with automatic hardware optimization
- **Dockerfile.gpu** (root) - GPU-enabled build with CUDA support

### **Legacy Deployment Variants (Deprecated)**
> **Note**: These configurations are deprecated in favor of the unified approach above.

- **docker-compose.basic.yml** - Basic deployment with minimal services *(deprecated)*
- **docker-compose.development.yml** - Development environment with debugging tools
- **docker-compose.production.yml** - Production-ready configuration *(use main docker-compose.yml)*
- **docker-compose.full.yml** - Complete deployment *(use main docker-compose.yml)*
- **docker-compose.minimal.yml** - Minimal deployment *(use main docker-compose.yml)*

### **Service-Specific Configurations**
- **docker-compose.external.yml** - Configuration for external service integrations
- **docker-compose.redis.yml** - Redis-specific configuration
- **docker-compose.weaviate.yml** - Weaviate vector database configuration
- **docker-compose.scalable.yml** - Scalable deployment configuration

### **Additional Dockerfiles**
- **Dockerfile.basic** - Basic Docker image build
- **Dockerfile.production** - Production-optimized Docker image

## 🚀 Usage

### Unified Deployment (Recommended)
```bash
# Standard deployment with all features (CPU-optimized)
docker-compose up -d

# GPU-accelerated deployment (requires NVIDIA Docker)
docker-compose -f docker-compose.gpu.yml up -d
```

### Legacy Configurations (Deprecated)
```bash
# Basic deployment (deprecated - use main docker-compose.yml)
docker-compose -f docker/docker-compose.basic.yml up -d

# Development environment
docker-compose -f docker/docker-compose.development.yml up -d

# Production deployment (deprecated - use main docker-compose.yml)
docker-compose -f docker/docker-compose.production.yml up -d

# Full deployment (deprecated - use main docker-compose.yml)
docker-compose -f docker/docker-compose.full.yml up -d
```

### GPU Deployment Requirements
For GPU-accelerated deployment:
```bash
# Install NVIDIA Docker runtime
curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | sudo tee /etc/apt/sources.list.d/nvidia-docker.list
sudo apt-get update && sudo apt-get install -y nvidia-docker2
sudo systemctl restart docker

# Deploy with GPU support
docker-compose -f docker-compose.gpu.yml up -d
```

### Combined Configurations
```bash
# Combine main config with specific services
docker-compose -f docker-compose.yml -f docker/docker-compose.redis.yml up -d

# Development with external services
docker-compose -f docker/docker-compose.development.yml -f docker/docker-compose.external.yml up -d
```

## 🔧 Configuration Notes

- All configurations assume the main application code is in the parent directory
- Environment variables should be configured in `.env` file in the root directory
- Volume mounts are relative to the root directory
- Network configurations are designed to work together when combining files

## 📋 Maintenance

When adding new Docker configurations:
1. Follow the naming convention: `docker-compose.{purpose}.yml`
2. Document the purpose and usage in this README
3. Test compatibility with existing configurations
4. Ensure environment variables are properly referenced
