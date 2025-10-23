# Role Assignment Templates for Different Machine Counts

## Overview
This document defines the role assignment patterns for different machine count configurations. The dynamic deployment script uses these templates to automatically assign roles based on the number of machines specified.

---

## 1-Machine Setup (All-in-One)

### Role Assignment
- **Machine 1**: `all-in-one-server`

### Services on Machine 1
- FastAPI Application (Port 8000)
- PostgreSQL Database (Port 5432)
- Redis Cache (Port 6379)
- Weaviate Vector DB (Port 8080)
- Celery Workers
- Flower Task Monitor (Port 5555)
- Grafana Dashboards (Port 3000)
- Prometheus Monitoring (Port 9090)

### Use Case
- Development and testing on a single machine
- Small-scale deployments
- Resource-constrained environments

---

## 2-Machine Setup (Basic Separation)

### Role Assignment
- **Machine 1**: `api-database-server`
- **Machine 2**: `worker-monitoring-server`

### Services Distribution

**Machine 1 (API + Database)**:
- FastAPI Application (Port 8000)
- PostgreSQL Database (Port 5432)
- Weaviate Vector DB (Port 8080)
- Redis Cache (Port 6379)

**Machine 2 (Worker + Monitoring)**:
- Celery Workers
- Flower Task Monitor (Port 5555)
- Grafana Dashboards (Port 3000)
- Prometheus Monitoring (Port 9090)
- Loki Log Aggregation (Port 3100)

### Use Case
- Basic separation of concerns
- Improved performance over single machine
- Small team development

---

## 3-Machine Setup (Standard)

### Role Assignment
- **Machine 1**: `api-server`
- **Machine 2**: `database-server`
- **Machine 3**: `worker-server`

### Services Distribution

**Machine 1 (API)**:
- FastAPI Application (Port 8000)
- Redis Cache (Port 6379)
- Prometheus Monitoring (Port 9090)

**Machine 2 (Database)**:
- PostgreSQL Database (Port 5432)
- Weaviate Vector DB (Port 8080)
- pgAdmin (Port 5050)

**Machine 3 (Worker)**:
- Celery Workers
- Flower Task Monitor (Port 5555)

### Use Case
- Standard production deployment
- Good performance and reliability
- Clear service separation

---

## 4-Machine Setup (Enhanced)

### Role Assignment
- **Machine 1**: `api-server`
- **Machine 2**: `database-server`
- **Machine 3**: `worker-server`
- **Machine 4**: `monitoring-server`

### Services Distribution

**Machine 1 (API)**:
- FastAPI Application (Port 8000)
- Redis Cache (Port 6379)

**Machine 2 (Database)**:
- PostgreSQL Database (Port 5432)
- Weaviate Vector DB (Port 8080)
- pgAdmin (Port 5050)

**Machine 3 (Worker)**:
- Celery Workers
- Flower Task Monitor (Port 5555)

**Machine 4 (Monitoring)**:
- Grafana Dashboards (Port 3000)
- Prometheus Monitoring (Port 9090)
- Loki Log Aggregation (Port 3100)

### Use Case
- Enhanced monitoring capabilities
- Better resource isolation
- Medium-scale production

---

## 5-Machine Setup (Advanced)

### Role Assignment
- **Machine 1**: `api-server`
- **Machine 2**: `database-server`
- **Machine 3**: `worker-server`
- **Machine 4**: `monitoring-server`
- **Machine 5**: `development-server`

### Services Distribution

**Machine 1 (API)**:
- FastAPI Application (Port 8000)
- Redis Cache (Port 6379)
- Prometheus Monitoring (Port 9090)

**Machine 2 (Database)**:
- PostgreSQL Database (Port 5432)
- Weaviate Vector DB (Port 8080)
- pgAdmin (Port 5050)

**Machine 3 (Worker)**:
- Celery Workers
- Flower Task Monitor (Port 5555)

**Machine 4 (Monitoring)**:
- Grafana Dashboards (Port 3000)
- Loki Log Aggregation (Port 3100)

**Machine 5 (Development)**:
- Development API (Port 8001)
- Test Database (Port 5433)
- Development tools
- Test runner

### Use Case
- Advanced development workflow
- Separate development environment
- Team development with testing

---

## 6-Machine Setup (Development/Testing)

### Role Assignment
- **Machine 1**: `api-server`
- **Machine 2**: `database-server`
- **Machine 3**: `worker-server`
- **Machine 4**: `monitoring-server`
- **Machine 5**: `development-server`
- **Machine 6**: `testing-server`

### Services Distribution

**Machine 1 (API)**:
- FastAPI Application (Port 8000)
- Redis Cache (Port 6379)
- Prometheus Monitoring (Port 9090)

**Machine 2 (Database)**:
- PostgreSQL Database (Port 5432)
- Weaviate Vector DB (Port 8080)
- pgAdmin (Port 5050)

**Machine 3 (Worker)**:
- Celery Workers
- Flower Task Monitor (Port 5555)

**Machine 4 (Monitoring)**:
- Grafana Dashboards (Port 3000)
- Loki Log Aggregation (Port 3100)

**Machine 5 (Development)**:
- Development API (Port 8001)
- Test Database (Port 5433)
- Development tools
- Code watcher

**Machine 6 (Testing)**:
- QA API (Port 8002)
- Load tester
- Integration tester
- Security scanner
- Performance monitor
- Test dashboard (Port 3001)

### Use Case
- Full development/testing pipeline
- Comprehensive testing capabilities
- Enterprise-grade deployment

---

## 7+ Machine Setup (Custom)

### Role Assignment Pattern
For 7 or more machines, the system uses the 6-machine pattern as a base and adds extra worker servers:

- **Machines 1-6**: Same as 6-machine setup
- **Machine 7+**: `extra-worker-N` (where N starts from 1)

### Services Distribution

**Extra Worker Machines**:
- Additional Celery workers
- Can be specialized for specific task types
- Horizontal scaling for background processing

### Use Case
- High-throughput applications
- Specialized task processing
- Enterprise-scale deployments

---

## Custom Role Assignment

### Manual Role Selection
When auto-assignment fails or for specific requirements, users can manually select from these roles:

1. **all-in-one-server**: All services on one machine
2. **api-server**: API + Redis + Prometheus
3. **database-server**: PostgreSQL + Weaviate
4. **worker-server**: Celery workers + Flower
5. **monitoring-server**: Grafana + Loki
6. **development-server**: Dev API + Test DB + tools
7. **testing-server**: QA API + testing tools
8. **combined-server**: Multiple services (custom)

### Combined Server Roles
For smaller deployments, combined roles are available:
- **api-database-server**: API + Database services
- **worker-monitoring-server**: Worker + Monitoring services

---

## Resource Allocation Guidelines

### Memory Allocation per Role

| Role | Memory Limit | Memory Reservation | Notes |
|------|--------------|-------------------|--------|
| **all-in-one-server** | 6G | 3G | All services on one machine |
| **api-server** | 2G | 1G | API + Redis + Prometheus |
| **database-server** | 3G | 2G | PostgreSQL + Weaviate |
| **worker-server** | 1G | 512M | Celery workers |
| **monitoring-server** | 1G | 512M | Grafana + Loki |
| **development-server** | 2G | 1G | Dev environment |
| **testing-server** | 2G | 1G | Testing environment |
| **api-database-server** | 4G | 2G | Combined API + Database |
| **worker-monitoring-server** | 2G | 1G | Combined Worker + Monitoring |
| **extra-worker-*** | 1G | 512M | Additional workers |

### Total Memory Usage Estimates

| Machine Count | Total Memory Used | Headroom (8GB per machine) |
|---------------|-------------------|----------------------------|
| 1 | 6G | 2G |
| 2 | 6G | 10G |
| 3 | 6G | 18G |
| 4 | 7G | 25G |
| 5 | 9G | 31G |
| 6 | 11G | 37G |
| 7 | 12G | 44G |
| 8 | 13G | 51G |

---

## Service Port Mapping

### Standard Ports
- **API**: 8000 (Production), 8001 (Development), 8002 (Testing)
- **Database**: 5432 (Production), 5433 (Development)
- **Redis**: 6379
- **Weaviate**: 8080
- **Grafana**: 3000 (Production), 3001 (Testing)
- **Prometheus**: 9090
- **Flower**: 5555
- **Loki**: 3100
- **pgAdmin**: 5050

### Port Allocation Rules
- Production services use standard ports
- Development and testing services use alternative ports
- Port conflicts are automatically resolved
- Custom ports can be specified in configuration

---

## Best Practices

### For Small Deployments (1-3 machines)
- Use combined roles when appropriate
- Prioritize essential services
- Consider resource constraints

### For Medium Deployments (4-5 machines)
- Separate monitoring to dedicated machine
- Isolate development environment
- Maintain production stability

### For Large Deployments (6+ machines)
- Implement full development/testing pipeline
- Use specialized worker machines
- Monitor resource usage carefully

### General Recommendations
- Start with the smallest configuration that meets needs
- Scale up as requirements grow
- Monitor performance and adjust allocations
- Use the dynamic deployment script for flexibility