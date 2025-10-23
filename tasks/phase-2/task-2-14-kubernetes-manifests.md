# Task 2-14: Kubernetes Deployment Manifests

**Phase:** 2 - Performance & Production Readiness  
**Week:** 7  
**Estimated Hours:** 6 hours  
**Priority:** HIGH  
**Dependencies:** Task 2-13 (Production Dockerfile)

---

## 🎯 OBJECTIVE

Create Kubernetes deployment manifests for production deployment with auto-scaling, health checks, and resource limits.

---

## 📋 REQUIREMENTS

### Functional Requirements
- Deployment configuration
- Service configuration
- ConfigMap and Secrets
- Horizontal Pod Autoscaler
- Ingress configuration

### Technical Requirements
- Kubernetes 1.25+
- Resource limits
- Liveness/readiness probes
- Rolling updates

---

## 🔧 IMPLEMENTATION

**File:** `k8s/deployment.yaml`

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: dryad-api
  labels:
    app: dryad-api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: dryad-api
  template:
    metadata:
      labels:
        app: dryad-api
    spec:
      containers:
      - name: api
        image: dryad-api:latest
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: dryad-secrets
              key: database-url
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 30
        readinessProbe:
          httpGet:
            path: /health/ready
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 10
```

**File:** `k8s/hpa.yaml`

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: dryad-api-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: dryad-api
  minReplicas: 3
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
```

---

## ✅ DEFINITION OF DONE

- [ ] Deployment manifests created
- [ ] Auto-scaling configured
- [ ] Health checks working
- [ ] Resource limits set
- [ ] Tests passing

---

## 📊 SUCCESS METRICS

- Deployment successful
- Auto-scaling working
- Zero-downtime updates

---

**Estimated Completion:** 6 hours  
**Status:** NOT STARTED

