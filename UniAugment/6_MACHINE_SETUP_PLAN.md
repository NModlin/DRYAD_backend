# 🖥️ 6 OptiPlex PC Development/Testing Environment Setup

## Hardware Configuration
- **6 Dell OptiPlex PCs** with 8GB RAM each
- **Total Memory**: 48GB distributed across 6 machines
- **Network**: All machines on same local network with static IPs

## Machine Role Distribution

### Machine 1: Primary API Server & Load Balancer
- **IP**: 192.168.1.100
- **Services**: FastAPI Application (Port 8000), Redis Cache (Port 6379), Prometheus Monitoring (Port 9090)
- **Role**: Primary API endpoint, request routing, system monitoring

### Machine 2: Database & Storage Server
- **IP**: 192.168.1.101
- **Services**: PostgreSQL Database (Port 5432), Weaviate Vector DB (Port 8080), pgAdmin (Port 5050)
- **Role**: Central data storage, vector database operations

### Machine 3: Worker & Processing Server
- **IP**: 192.168.1.102
- **Services**: Celery Workers (4 workers), Flower Task Monitor (Port 5555)
- **Role**: Background task processing, async operations

### Machine 4: Monitoring & Analytics Server
- **IP**: 192.168.1.103
- **Services**: Grafana Dashboards (Port 3000), Loki Log Aggregation (Port 3100)
- **Role**: System monitoring, analytics, log management

### Machine 5: Development Environment Server
- **IP**: 192.168.1.104
- **Services**: Development API instance (Port 8001), Test Database (Port 5433), Development tools
- **Role**: Development sandbox, testing environment

### Machine 6: Testing & QA Server
- **IP**: 192.168.1.105
- **Services**: QA API instance (Port 8002), Test services, Automated testing tools
- **Role**: Quality assurance, automated testing, staging environment

## Network Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                                                                         │
│  Machine 1 (192.168.1.100) - Primary API Server                        │
│  ├─ FastAPI Application (Port 8000)                                    │
│  ├─ Redis Cache (Port 6379)                                            │
│  └─ Prometheus Monitoring (Port 9090)                                  │
│                                                                         │
│  Machine 2 (192.168.1.101) - Database Server                           │
│  ├─ PostgreSQL Database (Port 5432)                                    │
│  ├─ Weaviate Vector DB (Port 8080)                                     │
│  └─ pgAdmin (Port 5050)                                                │
│                                                                         │
│  Machine 3 (192.168.1.102) - Worker Server                             │
│  ├─ Celery Workers (4 workers)                                         │
│  └─ Flower Task Monitor (Port 5555)                                    │
│                                                                         │
│  Machine 4 (192.168.1.103) - Monitoring Server                         │
│  ├─ Grafana Dashboards (Port 3000)                                     │
│  └─ Loki Log Aggregation (Port 3100)                                   │
│                                                                         │
│  Machine 5 (192.168.1.104) - Development Server                        │
│  ├─ Development API (Port 8001)                                        │
│  ├─ Test Database (Port 5433)                                          │
│  └─ Development tools                                                  │
│                                                                         │
│  Machine 6 (192.168.1.105) - Testing Server                            │
│  ├─ QA API (Port 8002)                                                 │
│  ├─ Automated testing tools                                            │
│  └─ Staging environment                                                │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

## Service Port Mapping

| Service | Port | Machine | Purpose |
|---------|------|---------|---------|
| **Primary API** | 8000 | Machine 1 | Production API endpoint |
| **Development API** | 8001 | Machine 5 | Development environment |
| **QA API** | 8002 | Machine 6 | Testing environment |
| **PostgreSQL** | 5432 | Machine 2 | Production database |
| **Test PostgreSQL** | 5433 | Machine 5 | Development database |
| **Redis** | 6379 | Machine 1 | Cache and message broker |
| **Weaviate** | 8080 | Machine 2 | Vector database |
| **Prometheus** | 9090 | Machine 1 | Metrics collection |
| **Grafana** | 3000 | Machine 4 | Monitoring dashboards |
| **Flower** | 5555 | Machine 3 | Task monitoring |
| **Loki** | 3100 | Machine 4 | Log aggregation |
| **pgAdmin** | 5050 | Machine 2 | Database administration |

## Development/Testing Environment Benefits

### Parallel Development
- **Machine 5**: Dedicated development environment
- **Machine 6**: Dedicated testing/staging environment
- **Isolation**: Development changes don't affect production

### Resource Optimization
- **8GB RAM per machine**: Sufficient for individual service loads
- **Distributed processing**: Better performance than single machine
- **Scalability**: Easy to add more machines if needed

### Testing Capabilities
- **A/B testing**: Compare different versions simultaneously
- **Load testing**: Simulate high traffic across multiple machines
- **Integration testing**: Test interactions between services

## Setup Requirements

### Pre-Setup Checklist
- [ ] All 6 machines on same network
- [ ] Static IP addresses assigned (192.168.1.100-105)
- [ ] Docker installed on all machines
- [ ] Firewall rules allow inter-machine communication
- [ ] SSH access configured (if using Linux)

### Operating System Options
- **Option 1**: All Windows (simpler management)
- **Option 2**: Mix of Windows and Linux (optimal performance)
- **Option 3**: All Linux (best for development)

## Next Steps

1. **Choose operating system configuration**
2. **Assign static IP addresses**
3. **Install Docker on all machines**
4. **Run setup scripts for each machine role**
5. **Configure development and testing environments**
6. **Set up monitoring and backup systems**

## Estimated Resource Usage

| Machine | RAM Usage | CPU Usage | Storage |
|---------|-----------|-----------|---------|
| Machine 1 | 2-3GB | Medium | 20GB |
| Machine 2 | 3-4GB | Medium | 50GB |
| Machine 3 | 1-2GB | High | 10GB |
| Machine 4 | 1-2GB | Low | 15GB |
| Machine 5 | 2-3GB | Medium | 30GB |
| Machine 6 | 2-3GB | Medium | 25GB |
| **Total** | **11-17GB** | **Distributed** | **150GB** |

This configuration leaves significant headroom for future expansion and ensures optimal performance for development and testing workflows.