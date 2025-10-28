# WebSocket Integration Architecture

**Version:** 1.0.0  
**Status:** Design Phase  
**Purpose:** Real-time communication for universities and arena

---

## Overview

The WebSocket system provides **real-time bidirectional communication** for:
- Live competition updates
- Agent status monitoring
- Curriculum progress tracking
- Training data streaming
- System notifications

---

## Architecture

### Connection Hierarchy

```
┌─────────────────────────────────────────────────────┐
│         WebSocket Gateway                           │
│  - Connection management                            │
│  - Authentication & authorization                   │
│  - Message routing                                  │
│  - Subscription management                          │
└─────────────────────────────────────────────────────┘
        ↓
┌─────────────────────────────────────────────────────┐
│    University-Specific Channels                     │
│  - /ws/university/{university_id}                   │
│  - /ws/arena/{arena_id}                             │
│  - /ws/curriculum/{curriculum_id}                   │
│  - /ws/agent/{agent_id}                             │
└─────────────────────────────────────────────────────┘
        ↓
┌─────────────────────────────────────────────────────┐
│    Message Handlers                                 │
│  - Competition updates                              │
│  - Agent status                                     │
│  - Curriculum progress                              │
│  - Training data                                    │
│  - System events                                    │
└─────────────────────────────────────────────────────┘
```

---

## Message Types

### 1. Competition Messages

```python
class CompetitionStartMessage:
    type: str = "competition_start"
    competition_id: str
    participants: List[str]
    challenge_type: str
    timestamp: datetime

class CompetitionRoundMessage:
    type: str = "competition_round"
    competition_id: str
    round_number: int
    agent_1_action: Dict[str, Any]
    agent_2_action: Dict[str, Any]
    scores: Dict[str, float]
    timestamp: datetime

class CompetitionEndMessage:
    type: str = "competition_end"
    competition_id: str
    winner_id: str
    final_scores: Dict[str, float]
    training_data_collected: int
    timestamp: datetime
```

### 2. Agent Status Messages

```python
class AgentStatusMessage:
    type: str = "agent_status"
    agent_id: str
    status: str  # "idle", "training", "competing", "learning"
    current_level: int
    progress_percentage: float
    last_update: datetime

class AgentProgressMessage:
    type: str = "agent_progress"
    agent_id: str
    curriculum_id: str
    level_completed: int
    score: float
    achievements: List[str]
    timestamp: datetime
```

### 3. Curriculum Messages

```python
class CurriculumProgressMessage:
    type: str = "curriculum_progress"
    curriculum_id: str
    university_id: str
    total_agents: int
    agents_at_level: Dict[int, int]
    average_progress: float
    timestamp: datetime

class CurriculumUpdateMessage:
    type: str = "curriculum_update"
    curriculum_id: str
    update_type: str  # "level_added", "challenge_updated"
    details: Dict[str, Any]
    timestamp: datetime
```

### 4. Training Data Messages

```python
class TrainingDataMessage:
    type: str = "training_data"
    data_point_id: str
    competition_id: str
    agent_id: str
    action: str
    outcome: str
    reward: float
    timestamp: datetime

class DatasetReadyMessage:
    type: str = "dataset_ready"
    dataset_id: str
    source_universities: List[str]
    data_points_count: int
    quality_score: float
    timestamp: datetime
```

### 5. System Messages

```python
class SystemNotificationMessage:
    type: str = "system_notification"
    level: str  # "info", "warning", "error"
    message: str
    affected_components: List[str]
    timestamp: datetime

class ErrorMessage:
    type: str = "error"
    error_code: str
    error_message: str
    context: Dict[str, Any]
    timestamp: datetime
```

---

## Subscription Model

### Channel Subscriptions

```python
class ChannelSubscription:
    channel: str  # e.g., "/ws/university/univ_123"
    filters: Dict[str, Any]  # Optional filtering
    
    # Examples:
    # /ws/university/univ_123 - All events for university
    # /ws/arena/arena_456 - All competition events
    # /ws/agent/agent_789 - All events for specific agent
    # /ws/curriculum/curr_101 - All curriculum events
```

### Subscription Management

```python
# Subscribe to university events
{
    "type": "subscribe",
    "channel": "/ws/university/univ_123",
    "filters": {
        "event_types": ["competition", "agent_status"]
    }
}

# Unsubscribe
{
    "type": "unsubscribe",
    "channel": "/ws/university/univ_123"
}

# Get subscription status
{
    "type": "get_subscriptions"
}
```

---

## Real-Time Data Streaming

### Competition Live Stream

```
Client connects to /ws/arena/arena_123
    ↓
Subscribe to competition_123
    ↓
Receive: competition_start
    ↓
For each round:
    Receive: competition_round (with actions & scores)
    ↓
Receive: competition_end (with results)
    ↓
Receive: training_data (collected data points)
```

### Agent Progress Tracking

```
Client connects to /ws/agent/agent_456
    ↓
Subscribe to agent_456
    ↓
Receive: agent_status (periodic updates)
    ↓
Receive: agent_progress (on level completion)
    ↓
Receive: achievement_unlocked (on achievement)
```

---

## Performance Optimization

### Message Batching

```python
class MessageBatch:
    batch_id: str
    messages: List[Dict[str, Any]]
    timestamp: datetime
    
# Send multiple updates in single message
{
    "type": "batch",
    "messages": [
        {"type": "agent_status", ...},
        {"type": "competition_round", ...},
        {"type": "training_data", ...}
    ]
}
```

### Compression

- Enable gzip compression for large messages
- Use binary format for high-frequency updates
- Implement delta updates (only changed fields)

### Rate Limiting

```python
class RateLimitPolicy:
    max_messages_per_second: int = 100
    max_connections_per_user: int = 10
    message_size_limit_kb: int = 1024
```

---

## Security

### Authentication
- OAuth2 token validation
- Per-channel authorization
- User role-based access

### Data Privacy
- Encrypt sensitive data in transit
- Anonymize training data
- Audit all connections

### Error Handling
- Graceful disconnection
- Automatic reconnection
- Message queue on disconnect

---

## Monitoring & Debugging

### Metrics
- Active connections per university
- Messages per second
- Average message latency
- Error rates
- Subscription counts

### Logging
- Connection events
- Message routing
- Error conditions
- Performance anomalies


