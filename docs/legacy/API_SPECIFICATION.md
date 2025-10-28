# University System API Specification
## Complete REST API and WebSocket Interface for Level 6

**Date**: October 22, 2025  
**Status**: Ready for Implementation  
**Target**: FastAPI endpoints with OpenAPI documentation

---

## API Overview

The University System API provides comprehensive management of university instances, agents, curriculum, competitions, and training data. All endpoints are secured with DRYAD's existing OAuth2/JWT authentication system.

### Base URL
```
https://api.dryad.ai/v1/university
```

### Authentication
- **Bearer Token**: `Authorization: Bearer <jwt_token>`
- **API Key**: `X-API-Key: <api_key>` (for university-level automation)
- **University Context**: All requests include university_id in path or context

---

## University Management Endpoints

### 1. University Instance Management

#### Create University
```http
POST /universities
Content-Type: application/json
Authorization: Bearer <token>

{
  "name": "AI Research University",
  "description": "Advanced AI agent training facility",
  "settings": {
    "max_agents": 50,
    "isolation_level": "strict",
    "privacy_level": "private"
  }
}
```

**Response:**
```json
{
  "id": "uni_abc123def456",
  "name": "AI Research University",
  "description": "Advanced AI agent training facility",
  "owner_user_id": "uid_xyz789",
  "settings": {
    "max_agents": 50,
    "isolation_level": "strict",
    "privacy_level": "private"
  },
  "status": "active",
  "created_at": "2025-10-22T14:00:00Z",
  "agent_count": 0,
  "competition_count": 0
}
```

#### List Universities
```http
GET /universities?page=1&limit=20&status=active
Authorization: Bearer <token>
```

#### Get University Details
```http
GET /universities/{university_id}
Authorization: Bearer <token>
```

#### Update University
```http
PUT /universities/{university_id}
Content-Type: application/json
Authorization: Bearer <token>

{
  "name": "Updated University Name",
  "description": "Updated description",
  "settings": {
    "max_agents": 100
  }
}
```

#### Archive University
```http
DELETE /universities/{university_id}
Authorization: Bearer <token>
```

### 2. Agent Management

#### Create Agent
```http
POST /universities/{university_id}/agents
Content-Type: application/json
Authorization: Bearer <token>

{
  "name": "Research Agent Alpha",
  "description": "Specialized research agent",
  "agent_type": "researcher",
  "configuration": {
    "llm_model": "gpt-4",
    "temperature": 0.7,
    "tools": ["research", "analysis", "writing"],
    "memory_size": 1000
  },
  "specialization": "scientific_research"
}
```

**Response:**
```json
{
  "id": "agent_xyz789abc123",
  "name": "Research Agent Alpha",
  "agent_type": "researcher",
  "status": "active",
  "competency_score": 0.0,
  "created_at": "2025-10-22T14:05:00Z",
  "training_progress": {
    "current_path": null,
    "current_level": null,
    "challenges_completed": 0
  }
}
```

#### List Agents
```http
GET /universities/{university_id}/agents?agent_type=researcher&status=active&page=1&limit=20
Authorization: Bearer <token>
```

#### Get Agent Details
```http
GET /universities/{university_id}/agents/{agent_id}
Authorization: Bearer <token>
```

#### Update Agent Configuration
```http
PUT /universities/{university_id}/agents/{agent_id}
Content-Type: application/json
Authorization: Bearer <token>

{
  "configuration": {
    "temperature": 0.5,
    "tools": ["research", "analysis", "writing", "evaluation"]
  }
}
```

#### Start Agent Training
```http
POST /universities/{university_id}/agents/{agent_id}/training
Content-Type: application/json
Authorization: Bearer <token>

{
  "curriculum_path_id": "path_abc123",
  "starting_level": 1
}
```

---

## Curriculum Engine Endpoints

### 3. Curriculum Path Management

#### Create Curriculum Path
```http
POST /universities/{university_id}/curriculum/paths
Content-Type: application/json
Authorization: Bearer <token>

{
  "name": "Novice to Expert Research Path",
  "description": "Comprehensive research agent training",
  "difficulty_level": "beginner",
  "estimated_duration_hours": 80,
  "prerequisites": [],
  "tags": ["research", "comprehensive", "progressive"]
}
```

#### List Curriculum Paths
```http
GET /universities/{university_id}/curriculum/paths?difficulty_level=beginner&is_public=true
Authorization: Bearer <token>
```

#### Get Path Details with Levels
```http
GET /universities/{university_id}/curriculum/paths/{path_id}?include_levels=true
Authorization: Bearer <token>
```

### 4. Curriculum Level Management

#### Create Curriculum Level
```http
POST /universities/{university_id}/curriculum/paths/{path_id}/levels
Content-Type: application/json
Authorization: Bearer <token>

{
  "level_number": 1,
  "name": "Research Fundamentals",
  "description": "Basic research concepts and techniques",
  "learning_objectives": [
    "Understand research methodology",
    "Learn literature review techniques",
    "Practice hypothesis formulation"
  ],
  "challenges": [
    {
      "type": "research_task",
      "description": "Conduct literature review on given topic",
      "evaluation_criteria": ["completeness", "accuracy", "insightfulness"],
      "passing_score": 0.7
    }
  ],
  "passing_score": 0.7,
  "time_limit_minutes": 120
}
```

#### Update Level Challenges
```http
PUT /universities/{university_id}/curriculum/levels/{level_id}
Content-Type: application/json
Authorization: Bearer <token>

{
  "challenges": [
    // Updated challenge array
  ]
}
```

### 5. Agent Progress Tracking

#### Get Agent Progress
```http
GET /universities/{university_id}/agents/{agent_id}/progress
Authorization: Bearer <token>
```

**Response:**
```json
{
  "agent_id": "agent_xyz789abc123",
  "current_path": {
    "id": "path_abc123",
    "name": "Novice to Expert Research Path",
    "current_level": {
      "id": "level_456def",
      "level_number": 3,
      "name": "Advanced Research Techniques",
      "challenges_completed": 2,
      "total_challenges": 5,
      "current_score": 0.85
    }
  },
  "overall_competency": 0.72,
  "training_hours": 45.5,
  "recent_activity": [
    {
      "type": "challenge_completion",
      "level_id": "level_456def",
      "challenge_index": 2,
      "score": 0.92,
      "timestamp": "2025-10-22T13:30:00Z"
    }
  ]
}
```

#### Start Level Challenge
```http
POST /universities/{university_id}/agents/{agent_id}/levels/{level_id}/challenges/{challenge_index}/start
Authorization: Bearer <token>
```

#### Submit Challenge Result
```http
POST /universities/{university_id}/agents/{agent_id}/levels/{level_id}/challenges/{challenge_index}/submit
Content-Type: application/json
Authorization: Bearer <token>

{
  "result_data": {
    "response": "Agent's response to challenge",
    "reasoning_steps": ["step1", "step2", "step3"],
    "tools_used": ["research", "analysis"],
    "time_taken_seconds": 180
  },
  "self_evaluation": {
    "confidence": 0.8,
    "difficulty_rating": 0.6
  }
}
```

---

## Competition Framework Endpoints

### 6. Competition Management

#### Create Competition
```http
POST /universities/{university_id}/competitions
Content-Type: application/json
Authorization: Bearer <token>

{
  "name": "Research Excellence Tournament",
  "description": "Quarterly research agent competition",
  "competition_type": "tournament",
  "rules": {
    "scoring_method": "weighted_average",
    "time_limit_minutes": 180,
    "evaluation_criteria": ["accuracy", "creativity", "efficiency"]
  },
  "benchmark_id": "benchmark_research_v1",
  "evaluation_config": {
    "llm_model": "gpt-4",
    "temperature": 0.3,
    "max_tokens": 2000
  },
  "scheduled_start": "2025-11-01T10:00:00Z",
  "scheduled_end": "2025-11-01T16:00:00Z",
  "max_participants": 16
}
```

#### List Competitions
```http
GET /universities/{university_id}/competitions?status=active&type=tournament&page=1&limit=10
Authorization: Bearer <token>
```

#### Register Agent for Competition
```http
POST /universities/{university_id}/competitions/{competition_id}/register
Content-Type: application/json
Authorization: Bearer <token>

{
  "agent_id": "agent_xyz789abc123",
  "participant_type": "competitor"
}
```

#### Start Competition
```http
POST /universities/{university_id}/competitions/{competition_id}/start
Authorization: Bearer <token>
```

#### Get Competition Results
```http
GET /universities/{university_id}/competitions/{competition_id}/results
Authorization: Bearer <token>
```

**Response:**
```json
{
  "competition_id": "comp_789ghi",
  "name": "Research Excellence Tournament",
  "status": "completed",
  "winner_agent_id": "agent_xyz789abc123",
  "participants": [
    {
      "agent_id": "agent_xyz789abc123",
      "name": "Research Agent Alpha",
      "final_score": 0.92,
      "ranking": 1,
      "detailed_scores": {
        "accuracy": 0.95,
        "creativity": 0.88,
        "efficiency": 0.93
      }
    }
  ],
  "leaderboard": [
    // Sorted participant list
  ]
}
```

### 7. Real-time Competition Updates (WebSocket)

#### WebSocket Connection
```javascript
// Connect to university-specific competition channel
const ws = new WebSocket('wss://api.dryad.ai/ws/university');
ws.onopen = () => {
  // Authenticate and subscribe
  ws.send(JSON.stringify({
    type: 'authenticate',
    token: 'jwt_token_here',
    university_id: 'uni_abc123def456'
  }));
  
  // Subscribe to competition updates
  ws.send(JSON.stringify({
    type: 'subscribe',
    topic: 'competitions'
  }));
};
```

#### WebSocket Message Types

**Competition Start**
```json
{
  "type": "competition_started",
  "competition_id": "comp_789ghi",
  "name": "Research Excellence Tournament",
  "started_at": "2025-11-01T10:00:00Z",
  "participant_count": 16
}
```

**Match Update**
```json
{
  "type": "match_update",
  "competition_id": "comp_789ghi",
  "match_id": "match_123jkl",
  "participant1": {
    "agent_id": "agent_xyz789abc123",
    "name": "Research Agent Alpha",
    "current_score": 0.85
  },
  "participant2": {
    "agent_id": "agent_456mno",
    "name": "Research Agent Beta", 
    "current_score": 0.78
  },
  "progress": 0.6,
  "estimated_completion": "2025-11-01T10:45:00Z"
}
```

**Competition Result**
```json
{
  "type": "competition_result",
  "competition_id": "comp_789ghi",
  "winner_agent_id": "agent_xyz789abc123",
  "final_scores": {
    "agent_xyz789abc123": 0.92,
    "agent_456mno": 0.87
  },
  "leaderboard": [
    {
      "rank": 1,
      "agent_id": "agent_xyz789abc123",
      "score": 0.92,
      "agent_name": "Research Agent Alpha"
    }
  ]
}
```

---

## Training Data Pipeline Endpoints

### 8. Training Data Management

#### Get Training Data Collections
```http
GET /universities/{university_id}/training/data?source_type=competition&agent_id=agent_xyz789abc123&page=1&limit=20
Authorization: Bearer <token>
```

#### Export Training Data
```http
POST /universities/{university_id}/training/data/export
Content-Type: application/json
Authorization: Bearer <token>

{
  "data_types": ["conversation", "reasoning"],
  "date_range": {
    "start": "2025-10-01T00:00:00Z",
    "end": "2025-10-22T23:59:59Z"
  },
  "format": "jsonl",
  "anonymize": true
}
```

### 9. Improvement Proposals (Lyceum Integration)

#### Get Improvement Proposals
```http
GET /universities/{university_id}/improvement/proposals?validation_status=approved&page=1&limit=10
Authorization: Bearer <token>
```

#### Implement Improvement Proposal
```http
POST /universities/{university_id}/improvement/proposals/{proposal_id}/implement
Content-Type: application/json
Authorization: Bearer <token>

{
  "implementation_notes": "Applied optimization to research agents",
  "expected_impact": "15% performance improvement"
}
```

---

## Error Handling

### Standard Error Responses

**Authentication Error (401)**
```json
{
  "error": "authentication_required",
  "message": "Valid authentication token required",
  "details": "Please provide a valid OAuth2 bearer token"
}
```

**Authorization Error (403)**
```json
{
  "error": "insufficient_permissions", 
  "message": "User lacks required permissions for this operation",
  "required_permission": "university_admin",
  "user_permissions": ["university_read"]
}
```

**Validation Error (422)**
```json
{
  "error": "validation_error",
  "message": "Request validation failed",
  "details": [
    {
      "field": "max_agents",
      "error": "Value must be between 1 and 1000"
    }
  ]
}
```

**Resource Not Found (404)**
```json
{
  "error": "resource_not_found",
  "message": "University instance not found",
  "resource_type": "university",
  "resource_id": "uni_invalid123"
}
```

**Rate Limit Exceeded (429)**
```json
{
  "error": "rate_limit_exceeded",
  "message": "Too many requests for university operations",
  "retry_after": 3600,
  "limit": 1000,
  "window": "1 hour"
}
```

---

## Rate Limiting

### University-Level Rate Limits
- **University Management**: 100 requests/hour per university
- **Agent Operations**: 500 requests/hour per university  
- **Competition Operations**: 200 requests/hour per university
- **Training Data**: 50 requests/hour per university

### User-Level Rate Limits
- **API Requests**: 1000 requests/hour per user
- **WebSocket Connections**: 10 concurrent connections per user
- **Data Export**: 2 exports/hour per user

---

## WebSocket Performance Targets

- **Connection Latency**: <100ms for initial handshake
- **Message Delivery**: <50ms for competition updates
- **Subscription Management**: <10ms for topic subscriptions
- **Concurrent Connections**: Support for 1000+ simultaneous university connections

This API specification provides a complete interface for managing the Agentic University System while maintaining compatibility with DRYAD's existing security and performance standards.