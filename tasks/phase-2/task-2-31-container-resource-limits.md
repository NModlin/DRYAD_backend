# Task 2-31: Container Resource Limits

**Phase:** 2 - Performance & Production Readiness  
**Week:** 7 - Production Infrastructure  
**Priority:** HIGH  
**Estimated Hours:** 2 hours

---

## 📋 OVERVIEW

Configure CPU and memory limits for all Docker containers and Kubernetes pods to prevent resource exhaustion and ensure stable production operation.

---

## 🎯 OBJECTIVES

1. Analyze resource usage patterns
2. Define resource limits for each service
3. Configure Docker Compose resource limits
4. Configure Kubernetes resource requests/limits
5. Implement resource monitoring
6. Test under load

---

## 📊 CURRENT STATE

**Existing:**
- Docker containers running without limits
- Kubernetes manifests without resource specs
- No resource monitoring

**Gaps:**
- No CPU limits
- No memory limits
- Risk of resource exhaustion
- No resource guarantees

---

## 🔧 IMPLEMENTATION

### 1. Docker Compose Resource Limits

Update `docker-compose.prod.yml`:

```yaml
version: '3.8'

services:
  gremlins-api:
    image: dryad-backend:latest
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 4G
        reservations:
          cpus: '1.0'
          memory: 2G
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 60s

  weaviate:
    image: semitechnologies/weaviate:latest
    deploy:
      resources:
        limits:
          cpus: '4.0'
          memory: 8G
        reservations:
          cpus: '2.0'
          memory: 4G
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    deploy:
      resources:
        limits:
          cpus: '1.0'
          memory: 2G
        reservations:
          cpus: '0.5'
          memory: 1G
    restart: unless-stopped

  celery-worker:
    image: dryad-backend:latest
    command: celery -A app.core.celery_app worker --loglevel=info
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 3G
        reservations:
          cpus: '1.0'
          memory: 1.5G
      replicas: 2
    restart: unless-stopped

  nginx:
    image: nginx:alpine
    deploy:
      resources:
        limits:
          cpus: '1.0'
          memory: 512M
        reservations:
          cpus: '0.5'
          memory: 256M
    restart: unless-stopped

  prometheus:
    image: prom/prometheus:latest
    deploy:
      resources:
        limits:
          cpus: '1.0'
          memory: 2G
        reservations:
          cpus: '0.5'
          memory: 1G
    restart: unless-stopped

  grafana:
    image: grafana/grafana:latest
    deploy:
      resources:
        limits:
          cpus: '0.5'
          memory: 1G
        reservations:
          cpus: '0.25'
          memory: 512M
    restart: unless-stopped
```

---

### 2. Kubernetes Resource Specifications

Update `k8s/deployments/backend-deployment.yaml`:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: dryad-backend
  namespace: dryad
spec:
  replicas: 3
  selector:
    matchLabels:
      app: dryad-backend
  template:
    metadata:
      labels:
        app: dryad-backend
    spec:
      containers:
      - name: backend
        image: dryad-backend:latest
        ports:
        - containerPort: 8000
        
        # Resource requests and limits
        resources:
          requests:
            cpu: "1000m"      # 1 CPU core
            memory: "2Gi"     # 2 GB RAM
          limits:
            cpu: "2000m"      # 2 CPU cores
            memory: "4Gi"     # 4 GB RAM
        
        # Liveness probe
        livenessProbe:
          httpGet:
            path: /health/live
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
          timeoutSeconds: 5
          failureThreshold: 3
        
        # Readiness probe
        readinessProbe:
          httpGet:
            path: /health/ready
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 5
          timeoutSeconds: 3
          failureThreshold: 3
        
        env:
        - name: ENVIRONMENT
          value: "production"
```

Update `k8s/deployments/weaviate-deployment.yaml`:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: weaviate
  namespace: dryad
spec:
  replicas: 1
  selector:
    matchLabels:
      app: weaviate
  template:
    metadata:
      labels:
        app: weaviate
    spec:
      containers:
      - name: weaviate
        image: semitechnologies/weaviate:latest
        ports:
        - containerPort: 8080
        
        resources:
          requests:
            cpu: "2000m"
            memory: "4Gi"
          limits:
            cpu: "4000m"
            memory: "8Gi"
        
        volumeMounts:
        - name: weaviate-data
          mountPath: /var/lib/weaviate
      
      volumes:
      - name: weaviate-data
        persistentVolumeClaim:
          claimName: weaviate-pvc
```

---

### 3. Resource Monitoring Script

Create `scripts/monitoring/check-resources.sh`:

```bash
#!/bin/bash
#
# Container Resource Usage Monitor
#
# Checks current resource usage against limits

echo "📊 Container Resource Usage Report"
echo "=================================="
echo ""

# Docker stats
docker stats --no-stream --format \
  "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.MemPerc}}" \
  | head -20

echo ""
echo "⚠️  Containers using >80% of memory limit:"
docker stats --no-stream --format "{{.Name}}\t{{.MemPerc}}" \
  | awk -F'\t' '$2 > 80 {print $1 " - " $2}'

echo ""
echo "⚠️  Containers using >80% of CPU limit:"
docker stats --no-stream --format "{{.Name}}\t{{.CPUPerc}}" \
  | awk -F'\t' '$2 > 80 {print $1 " - " $2}'
```

---

### 4. Resource Limit Documentation

Create `docs/operations/RESOURCE_LIMITS.md`:

```markdown
# Container Resource Limits

## Service Resource Allocations

### Backend API (gremlins-api)
- **CPU Request:** 1 core
- **CPU Limit:** 2 cores
- **Memory Request:** 2 GB
- **Memory Limit:** 4 GB
- **Rationale:** Handles API requests, needs burst capacity

### Weaviate (Vector Database)
- **CPU Request:** 2 cores
- **CPU Limit:** 4 cores
- **Memory Request:** 4 GB
- **Memory Limit:** 8 GB
- **Rationale:** Memory-intensive vector operations

### Redis (Cache)
- **CPU Request:** 0.5 cores
- **CPU Limit:** 1 core
- **Memory Request:** 1 GB
- **Memory Limit:** 2 GB
- **Rationale:** In-memory cache, predictable usage

### Celery Workers
- **CPU Request:** 1 core
- **CPU Limit:** 2 cores
- **Memory Request:** 1.5 GB
- **Memory Limit:** 3 GB
- **Rationale:** Background task processing

### Nginx (Load Balancer)
- **CPU Request:** 0.5 cores
- **CPU Limit:** 1 core
- **Memory Request:** 256 MB
- **Memory Limit:** 512 MB
- **Rationale:** Lightweight proxy

## Monitoring Thresholds

- **Warning:** >70% of limit
- **Critical:** >85% of limit
- **Action Required:** >90% of limit

## Scaling Guidelines

### Horizontal Scaling (Add Replicas)
- Backend API: Scale when CPU >70% sustained
- Celery Workers: Scale when queue depth >100

### Vertical Scaling (Increase Limits)
- Weaviate: Increase memory if cache hit rate <80%
- Redis: Increase memory if evictions >100/min
```

---

### 5. Resource Alert Rules

Create `docker/prometheus/resource-alerts.yml`:

```yaml
groups:
  - name: resource_limits
    interval: 30s
    rules:
      - alert: ContainerMemoryHigh
        expr: |
          (container_memory_usage_bytes / container_spec_memory_limit_bytes) > 0.85
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Container {{ $labels.name }} memory usage high"
          description: "Memory usage is {{ $value | humanizePercentage }}"
      
      - alert: ContainerCPUHigh
        expr: |
          rate(container_cpu_usage_seconds_total[5m]) > 0.85
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Container {{ $labels.name }} CPU usage high"
          description: "CPU usage is {{ $value | humanizePercentage }}"
      
      - alert: ContainerMemoryCritical
        expr: |
          (container_memory_usage_bytes / container_spec_memory_limit_bytes) > 0.95
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "Container {{ $labels.name }} memory critical"
          description: "Memory usage is {{ $value | humanizePercentage }}"
```

---

## ✅ ACCEPTANCE CRITERIA

- [ ] Resource limits defined for all services
- [ ] Docker Compose limits configured
- [ ] Kubernetes resource specs configured
- [ ] Resource monitoring implemented
- [ ] Alerts configured for high usage
- [ ] Documentation complete
- [ ] Load testing validates limits

---

## 🧪 TESTING

```bash
# Test resource limits
docker-compose -f docker-compose.prod.yml up -d

# Monitor resource usage
./scripts/monitoring/check-resources.sh

# Stress test to verify limits
docker run --rm -it \
  --cpus="2.0" \
  --memory="4g" \
  dryad-backend:latest \
  python -m pytest tests/load/

# Verify Kubernetes limits
kubectl describe pod -n dryad | grep -A 5 "Limits:"
```

---

## 📝 NOTES

- Set requests lower than limits for burst capacity
- Monitor actual usage before setting limits
- Leave headroom for spikes (20-30%)
- Test limits under load
- Adjust based on production metrics


