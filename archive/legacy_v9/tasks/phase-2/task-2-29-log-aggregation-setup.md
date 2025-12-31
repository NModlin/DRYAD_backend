# Task 2-29: Log Aggregation Setup

**Phase:** 2 - Performance & Production Readiness  
**Week:** 6 - Monitoring & Observability  
**Priority:** HIGH  
**Estimated Hours:** 4 hours

---

## 📋 OVERVIEW

Set up centralized log aggregation system for collecting, searching, and analyzing logs from all services in production. Supports ELK Stack, Loki, or CloudWatch Logs.

---

## 🎯 OBJECTIVES

1. Choose log aggregation solution
2. Configure log shipping from containers
3. Set up log parsing and indexing
4. Create log search dashboards
5. Configure log-based alerts
6. Implement log retention policies

---

## 📊 CURRENT STATE

**Existing:**
- Structured JSON logging with structlog
- Logs written to stdout/stderr
- Docker log drivers configured

**Gaps:**
- No centralized log aggregation
- No log search capability
- No log-based alerting
- No log retention policy

---

## 🔧 IMPLEMENTATION

### Option A: Grafana Loki (Recommended for Kubernetes)

#### 1. Loki Configuration

Create `docker/loki/loki-config.yaml`:

```yaml
auth_enabled: false

server:
  http_listen_port: 3100
  grpc_listen_port: 9096

common:
  path_prefix: /loki
  storage:
    filesystem:
      chunks_directory: /loki/chunks
      rules_directory: /loki/rules
  replication_factor: 1
  ring:
    instance_addr: 127.0.0.1
    kvstore:
      store: inmemory

schema_config:
  configs:
    - from: 2020-10-24
      store: boltdb-shipper
      object_store: filesystem
      schema: v11
      index:
        prefix: index_
        period: 24h

ruler:
  alertmanager_url: http://localhost:9093

# Retention
limits_config:
  retention_period: 744h  # 31 days
  
# Compactor for retention
compactor:
  working_directory: /loki/compactor
  shared_store: filesystem
  compaction_interval: 10m
  retention_enabled: true
  retention_delete_delay: 2h
  retention_delete_worker_count: 150
```

---

#### 2. Promtail Configuration

Create `docker/loki/promtail-config.yaml`:

```yaml
server:
  http_listen_port: 9080
  grpc_listen_port: 0

positions:
  filename: /tmp/positions.yaml

clients:
  - url: http://loki:3100/loki/api/v1/push

scrape_configs:
  # Docker containers
  - job_name: docker
    docker_sd_configs:
      - host: unix:///var/run/docker.sock
        refresh_interval: 5s
    relabel_configs:
      - source_labels: ['__meta_docker_container_name']
        regex: '/(.*)'
        target_label: 'container'
      - source_labels: ['__meta_docker_container_log_stream']
        target_label: 'stream'
      - source_labels: ['__meta_docker_container_label_com_docker_compose_service']
        target_label: 'service'
    
    # Parse JSON logs
    pipeline_stages:
      - json:
          expressions:
            level: level
            timestamp: timestamp
            message: message
            request_id: request_id
            trace_id: trace_id
      - labels:
          level:
          request_id:
      - timestamp:
          source: timestamp
          format: RFC3339
```

---

#### 3. Docker Compose Integration

Update `docker-compose.yml`:

```yaml
services:
  loki:
    image: grafana/loki:2.9.0
    container_name: dryad-loki
    ports:
      - "3100:3100"
    volumes:
      - ./docker/loki/loki-config.yaml:/etc/loki/local-config.yaml
      - loki-data:/loki
    command: -config.file=/etc/loki/local-config.yaml
    networks:
      - gremlins-network
    restart: unless-stopped

  promtail:
    image: grafana/promtail:2.9.0
    container_name: dryad-promtail
    volumes:
      - ./docker/loki/promtail-config.yaml:/etc/promtail/config.yaml
      - /var/run/docker.sock:/var/run/docker.sock
      - /var/lib/docker/containers:/var/lib/docker/containers:ro
    command: -config.file=/etc/promtail/config.yaml
    networks:
      - gremlins-network
    restart: unless-stopped
    depends_on:
      - loki

  grafana:
    # ... existing grafana config ...
    environment:
      - GF_EXPLORE_ENABLED=true
    volumes:
      - ./docker/grafana/datasources.yaml:/etc/grafana/provisioning/datasources/datasources.yaml

volumes:
  loki-data:
```

---

#### 4. Grafana Datasource Configuration

Create `docker/grafana/datasources.yaml`:

```yaml
apiVersion: 1

datasources:
  - name: Loki
    type: loki
    access: proxy
    url: http://loki:3100
    isDefault: false
    editable: true
    jsonData:
      maxLines: 1000
      derivedFields:
        - datasourceUid: tempo
          matcherRegex: "trace_id=(\\w+)"
          name: TraceID
          url: "$${__value.raw}"
  
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true
    editable: true
```

---

### Option B: ELK Stack (Elasticsearch, Logstash, Kibana)

#### 1. Filebeat Configuration

Create `docker/elk/filebeat.yml`:

```yaml
filebeat.inputs:
  - type: container
    paths:
      - '/var/lib/docker/containers/*/*.log'
    processors:
      - add_docker_metadata:
          host: "unix:///var/run/docker.sock"
      - decode_json_fields:
          fields: ["message"]
          target: ""
          overwrite_keys: true

output.elasticsearch:
  hosts: ["elasticsearch:9200"]
  indices:
    - index: "dryad-logs-%{+yyyy.MM.dd}"

setup.kibana:
  host: "kibana:5601"

setup.ilm:
  enabled: true
  policy_name: "dryad-logs-policy"
  rollover_alias: "dryad-logs"
```

---

### 5. Log Query Examples

Create `docs/operations/LOG_QUERIES.md`:

```markdown
# Log Query Examples

## Loki Queries (LogQL)

### Find errors in last hour
```logql
{service="gremlins-api"} |= "ERROR" | json
```

### Find logs by request ID
```logql
{service="gremlins-api"} | json | request_id="req_abc123"
```

### Count errors by endpoint
```logql
sum by (path) (count_over_time({service="gremlins-api", level="ERROR"} [1h]))
```

### Find slow requests (>2s)
```logql
{service="gremlins-api"} | json | duration > 2000
```

## Elasticsearch Queries (Kibana)

### Find errors
```json
{
  "query": {
    "bool": {
      "must": [
        {"match": {"level": "ERROR"}},
        {"range": {"@timestamp": {"gte": "now-1h"}}}
      ]
    }
  }
}
```
```

---

### 6. Log-Based Alerts

Create `docker/loki/rules.yaml`:

```yaml
groups:
  - name: dryad_alerts
    interval: 1m
    rules:
      - alert: HighErrorRate
        expr: |
          sum(rate({service="gremlins-api", level="ERROR"}[5m])) > 10
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High error rate detected"
          description: "Error rate is {{ $value }} errors/sec"
      
      - alert: DatabaseConnectionErrors
        expr: |
          count_over_time({service="gremlins-api"} |= "database connection" |= "error" [5m]) > 5
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "Database connection errors"
          description: "Multiple database connection errors detected"
```

---

### 7. Python Logging Integration

Update `app/core/logging_config.py`:

```python
"""
Logging Configuration for Log Aggregation

Structured logging optimized for Loki/ELK.
"""
from __future__ import annotations

import logging
import sys
import structlog


def configure_logging_for_aggregation():
    """Configure logging for log aggregation systems."""
    
    # Configure structlog for JSON output
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            # JSON renderer for log aggregation
            structlog.processors.JSONRenderer()
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )
    
    # Configure standard logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=logging.INFO,
    )
    
    # Add context to all logs
    structlog.contextvars.bind_contextvars(
        service="gremlins-api",
        environment="production"
    )
```

---

## ✅ ACCEPTANCE CRITERIA

- [ ] Log aggregation system deployed
- [ ] Logs from all services collected
- [ ] Log search working in Grafana/Kibana
- [ ] Log-based alerts configured
- [ ] Log retention policy implemented
- [ ] Documentation complete
- [ ] Team trained on log queries

---

## 🧪 TESTING

```python
# tests/test_log_aggregation.py
"""Tests for log aggregation."""
import logging
import structlog


def test_structured_logging():
    """Test structured logging output."""
    logger = structlog.get_logger()
    logger.info(
        "test_event",
        request_id="req_123",
        user_id="user_456"
    )
    # Verify JSON output format


def test_log_context():
    """Test log context propagation."""
    structlog.contextvars.bind_contextvars(request_id="req_789")
    logger = structlog.get_logger()
    logger.info("test_with_context")
    # Verify context in output
```

---

## 📝 NOTES

- Choose Loki for Kubernetes deployments
- Choose ELK for advanced search needs
- Implement log retention to manage storage
- Use log sampling for high-volume services
- Create dashboards for common queries


