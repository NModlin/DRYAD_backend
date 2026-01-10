# Task 2-13: Production Dockerfile

**Phase:** 2 - Performance & Production Readiness  
**Week:** 7  
**Estimated Hours:** 4 hours  
**Priority:** CRITICAL  
**Dependencies:** None

---

## 🎯 OBJECTIVE

Create optimized production Dockerfile with multi-stage builds, security hardening, and minimal image size.

---

## 📋 REQUIREMENTS

### Functional Requirements
- Multi-stage build
- Security hardening
- Minimal image size
- Non-root user
- Health checks

### Technical Requirements
- Python 3.11 slim base
- Layer caching optimization
- Security scanning
- Image tagging

### Performance Requirements
- Image size: <500MB
- Build time: <5 minutes
- Startup time: <10 seconds

---

## 🔧 IMPLEMENTATION

**File:** `Dockerfile`

```dockerfile
# Multi-stage build for production

# Stage 1: Builder
FROM python:3.11-slim as builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --user -r requirements.txt

# Stage 2: Runtime
FROM python:3.11-slim

WORKDIR /app

# Install runtime dependencies only
RUN apt-get update && apt-get install -y \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd -m -u 1000 dryad && chown -R dryad:dryad /app

# Copy Python packages from builder
COPY --from=builder /root/.local /home/dryad/.local

# Copy application code
COPY --chown=dryad:dryad . .

# Switch to non-root user
USER dryad

# Add local bin to PATH
ENV PATH=/home/dryad/.local/bin:$PATH

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health')"

# Run application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**File:** `.dockerignore`

```
__pycache__
*.pyc
*.pyo
*.pyd
.Python
env/
venv/
.venv
.git
.gitignore
.pytest_cache
.coverage
htmlcov/
*.log
.env
.env.local
```

---

## ✅ DEFINITION OF DONE

- [ ] Dockerfile created
- [ ] Multi-stage build working
- [ ] Security hardened
- [ ] Image size optimized
- [ ] Health check configured
- [ ] Tests passing

---

## 📊 SUCCESS METRICS

- Image size: <500MB
- Build time: <5 minutes
- Security scan: No critical issues

---

**Estimated Completion:** 4 hours  
**Status:** NOT STARTED

