# GremlinsAI Backend - Unified Installation Dockerfile
# Single installation with automatic GPU detection and optimization

# Build arguments
ARG PYTHON_VERSION=3.11
# Use PyTorch base image which includes Torch and CUDA deps pre-installed.
# This avoids downloading/building 5GB+ of dependencies during the build.
FROM pytorch/pytorch:2.3.0-cuda12.1-cudnn8-runtime as base

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    DEBIAN_FRONTEND=noninteractive

# Update apt and install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    git \
    libpq-dev \
    ffmpeg \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libglib2.0-0 \
    libsndfile1 \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Create app user
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Set working directory
WORKDIR /app

# Add src directory to PYTHONPATH
ENV PYTHONPATH=/app/src

# Create a custom temp directory on the disk to avoid /tmp (tmpfs) limits
RUN mkdir -p /app/tmp
ENV TMPDIR=/app/tmp

# Pre-install llama-cpp-python with CUDA support using pre-built wheels
# This avoids complex compilation issues and ensures GPU support
RUN pip install llama-cpp-python \
    --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/cu121

# Copy requirements files
COPY requirements.txt requirements-dev.txt ./

# Stage: Dependencies - Install shared dependencies
FROM base as dependencies

# Install unified Python dependencies
# Torch/CUDA are already in the base image. This installs the rest.
RUN pip install --no-cache-dir -r requirements.txt

# Stage: Production - Unified installation
FROM dependencies as production

# Copy application code (This breaks cache, so we do it late)
COPY --chown=appuser:appuser . .

# Create data and model directories
RUN mkdir -p /app/data /app/models && chown -R appuser:appuser /app/data /app/models

USER appuser

# Health check with comprehensive service checks
HEALTHCHECK --interval=45s --timeout=20s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/health/status || exit 1

# Expose port
EXPOSE 8000

# Default command with automatic GPU detection
CMD ["uvicorn", "dryad.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]

# Stage: Development - Includes dev tools for local development
# Extends dependencies (not production) to avoid cache invalidation from source code changes
FROM dependencies as development

# Switch back to root for dev tool installation
USER root

# Install development dependencies
RUN pip install --no-cache-dir -r requirements-dev.txt

# Install additional dev tools
RUN apt-get update && apt-get install -y \
    vim \
    htop \
    && rm -rf /var/lib/apt/lists/*

# Copy application code for development image
# (Even if mounted, this ensures image matches repo state)
COPY --chown=appuser:appuser . .

# Switch back to app user
USER appuser

# Development command with auto-reload
CMD ["uvicorn", "dryad.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# Default to production stage
FROM production as final
