# GremlinsAI Backend - Unified Installation Dockerfile
# Single installation with automatic GPU detection and optimization

# Build arguments
ARG PYTHON_VERSION=3.11
ARG ENABLE_GPU=false

# Base stage - Common setup
FROM python:${PYTHON_VERSION}-slim as base

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Create app user
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Set working directory
WORKDIR /app

# Copy requirements files
COPY requirements.txt requirements-dev.txt ./

# Production stage - Unified installation with all features
FROM base as production

# Install system dependencies for all features (ML, multimodal, etc.)
RUN apt-get update && apt-get install -y \
    libpq-dev \
    ffmpeg \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libglib2.0-0 \
    libsndfile1 \
    && rm -rf /var/lib/apt/lists/*

# Install unified Python dependencies (includes all features)
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
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
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]

# Development stage - Includes dev tools for local development
FROM production as development

# Switch back to root for dev tool installation
USER root

# Install development dependencies
RUN pip install --no-cache-dir -r requirements-dev.txt

# Install additional dev tools
RUN apt-get update && apt-get install -y \
    vim \
    htop \
    && rm -rf /var/lib/apt/lists/*

# Switch back to app user
USER appuser

# Development command with auto-reload
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# Default to production stage
FROM production as final
