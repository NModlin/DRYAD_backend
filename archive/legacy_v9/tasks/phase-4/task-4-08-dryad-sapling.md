# Task 4-08: DRYAD Sapling (Minimal Deployment) Configuration

**Phase:** 4 - Forest Ecosystem Architecture  
**Week:** 20  
**Estimated Hours:** 12 hours  
**Priority:** MEDIUM  
**Dependencies:** Tasks 4-01 through 4-07 (All core services)

---

## 🎯 OBJECTIVE

Create DRYAD Sapling - a minimal, lightweight deployment configuration that includes only essential services (Grove Keeper, Oracle, Guardian) for small-scale deployments or development environments.

---

## 📋 REQUIREMENTS

### Functional Requirements
- Minimal service set (Grove Keeper, Oracle, Guardian)
- Single-node deployment support
- Reduced resource requirements
- Quick startup time
- Development-friendly configuration

### Technical Requirements
- Docker Compose configuration
- Lightweight Kubernetes manifests
- Shared database configuration
- Simplified networking

### Performance Requirements
- Startup time: <2 minutes
- Memory footprint: <2GB
- CPU usage: <2 cores

---

## 🔧 IMPLEMENTATION

**File:** `deployments/sapling/docker-compose.yml`

```yaml
version: '3.8'

services:
  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: dryad
      POSTGRES_USER: dryad
      POSTGRES_PASSWORD: dryad_dev
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  oracle:
    build: ../../services/oracle
    environment:
      REDIS_URL: redis://redis:6379
    ports:
      - "8001:8000"
    depends_on:
      - redis

  guardian:
    build: ../../services/guardian
    environment:
      DATABASE_URL: postgresql://dryad:dryad_dev@postgres:5432/dryad
      REDIS_URL: redis://redis:6379
    ports:
      - "8002:8000"
    depends_on:
      - postgres
      - redis

  grove-keeper:
    build: ../../services/grove-keeper
    environment:
      DATABASE_URL: postgresql://dryad:dryad_dev@postgres:5432/dryad
      REDIS_URL: redis://redis:6379
      ORACLE_URL: http://oracle:8000
      GUARDIAN_URL: http://guardian:8000
    ports:
      - "8000:8000"
    depends_on:
      - postgres
      - redis
      - oracle
      - guardian

volumes:
  postgres_data:
```

**File:** `deployments/sapling/k8s/sapling-deployment.yaml`

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: dryad-sapling

---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: grove-keeper
  namespace: dryad-sapling
spec:
  replicas: 1
  selector:
    matchLabels:
      app: grove-keeper
  template:
    metadata:
      labels:
        app: grove-keeper
    spec:
      containers:
      - name: grove-keeper
        image: dryad/grove-keeper:latest
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"

---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: oracle
  namespace: dryad-sapling
spec:
  replicas: 1
  selector:
    matchLabels:
      app: oracle
  template:
    metadata:
      labels:
        app: oracle
    spec:
      containers:
      - name: oracle
        image: dryad/oracle:latest
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "1Gi"
            cpu: "1000m"
```

**File:** `deployments/sapling/README.md`

```markdown
# DRYAD Sapling Deployment

Minimal DRYAD deployment for development and small-scale use.

## Quick Start

```bash
# Using Docker Compose
docker-compose up -d

# Using Kubernetes
kubectl apply -f k8s/

# Access Grove Keeper
curl http://localhost:8000/health
```

## Included Services

- Grove Keeper (Core orchestration)
- Oracle (AI Provider Hub)
- Guardian (Security & Auth)
- PostgreSQL (Database)
- Redis (Cache)

## Resource Requirements

- Memory: 2GB minimum
- CPU: 2 cores minimum
- Disk: 10GB minimum
```

---

## ✅ DEFINITION OF DONE

- [ ] Docker Compose configuration created
- [ ] Kubernetes manifests created
- [ ] Documentation complete
- [ ] Tested on local environment
- [ ] Startup time validated
- [ ] Resource usage verified

---

## 📊 SUCCESS METRICS

- Startup time: <2 minutes
- Memory footprint: <2GB
- CPU usage: <2 cores
- All services healthy

---

**Estimated Completion:** 12 hours  
**Status:** NOT STARTED

