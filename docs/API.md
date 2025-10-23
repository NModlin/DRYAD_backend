# DRYAD.AI API Documentation

## Overview

The DRYAD.AI API provides a comprehensive interface for interacting with AI agents and managing conversation history. The API is built with FastAPI and follows RESTful principles.

## Base URL

```
http://localhost:8000
```

## Authentication

Currently, no authentication is required.

## API Endpoints

### Health Check

#### GET /
Returns a welcome message to verify the API is running.

**Response:**
```json
{
  "message": "Welcome to the DRYAD.AI API!"
}
```

---

## Agent Endpoints

### Simple Agent Invocation

#### POST /api/v1/agent/invoke
Invoke the AI agent with a simple query.

**Request Body:**
```json
{
  "input": "What is artificial intelligence?"
}
```

**Response:**
```json
{
  "output": {
    "messages": [...],
    "agent_outcome": {
      "return_values": {
        "output": "AI search results and response"
      }
    }
  }
}
```

### Context-Aware Chat

#### POST /api/v1/agent/chat
Invoke the AI agent with conversation context and automatic history saving.

**Request Body:**
```json
{
  "input": "What is machine learning?",
  "conversation_id": "optional-existing-conversation-id",
  "save_conversation": true
}
```

**Response:**
```json
{
  "output": {
    "messages": [...],
    "agent_outcome": {...}
  },
  "conversation_id": "uuid-of-conversation",
  "message_id": "uuid-of-response-message",
  "context_used": true
}
```

---

## Chat History Endpoints

### Conversations

#### POST /api/v1/history/conversations
Create a new conversation.

**Request Body:**
```json
{
  "title": "My Conversation",
  "initial_message": "Hello, how are you?"
}
```

**Response:** `201 Created`
```json
{
  "id": "conversation-uuid",
  "title": "My Conversation",
  "created_at": "2024-01-01T12:00:00Z",
  "updated_at": "2024-01-01T12:00:00Z",
  "is_active": true,
  "messages": [...]
}
```

#### GET /api/v1/history/conversations
List conversations with pagination.

**Query Parameters:**
- `limit` (int, default: 50): Number of conversations to return
- `offset` (int, default: 0): Number of conversations to skip
- `active_only` (bool, default: true): Only return active conversations

**Response:**
```json
{
  "conversations": [...],
  "total": 25,
  "limit": 50,
  "offset": 0
}
```

#### GET /api/v1/history/conversations/{conversation_id}
Get a specific conversation by ID.

**Query Parameters:**
- `include_messages` (bool, default: true): Include messages in response

**Response:**
```json
{
  "id": "conversation-uuid",
  "title": "My Conversation",
  "created_at": "2024-01-01T12:00:00Z",
  "updated_at": "2024-01-01T12:00:00Z",
  "is_active": true,
  "messages": [...]
}
```

#### PUT /api/v1/history/conversations/{conversation_id}
Update a conversation.

**Request Body:**
```json
{
  "title": "Updated Title",
  "is_active": false
}
```

**Response:**
```json
{
  "id": "conversation-uuid",
  "title": "Updated Title",
  "created_at": "2024-01-01T12:00:00Z",
  "updated_at": "2024-01-01T12:05:00Z",
  "is_active": false,
  "messages": null
}
```

#### DELETE /api/v1/history/conversations/{conversation_id}
Delete a conversation.

**Query Parameters:**
- `soft_delete` (bool, default: true): Perform soft delete (deactivate) instead of hard delete

**Response:** `204 No Content`

### Messages

#### POST /api/v1/history/messages
Add a message to a conversation.

**Request Body:**
```json
{
  "conversation_id": "conversation-uuid",
  "role": "user",
  "content": "This is my message",
  "tool_calls": {"search": "optional tool call data"},
  "extra_data": {"confidence": 0.95}
}
```

**Response:** `201 Created`
```json
{
  "id": "message-uuid",
  "conversation_id": "conversation-uuid",
  "role": "user",
  "content": "This is my message",
  "tool_calls": {"search": "optional tool call data"},
  "extra_data": {"confidence": 0.95},
  "created_at": "2024-01-01T12:00:00Z"
}
```

#### GET /api/v1/history/conversations/{conversation_id}/messages
Get messages for a conversation.

**Query Parameters:**
- `limit` (int, default: 100): Number of messages to return
- `offset` (int, default: 0): Number of messages to skip

**Response:**
```json
{
  "messages": [...],
  "conversation_id": "conversation-uuid",
  "total": 10,
  "limit": 100,
  "offset": 0
}
```

#### GET /api/v1/history/conversations/{conversation_id}/context
Get conversation context formatted for AI agents.

**Query Parameters:**
- `max_messages` (int, default: 20): Maximum number of messages to include

**Response:**
```json
{
  "conversation_id": "conversation-uuid",
  "context": [
    {
      "role": "user",
      "content": "Hello",
      "created_at": "2024-01-01T12:00:00Z"
    },
    {
      "role": "assistant",
      "content": "Hi there!",
      "created_at": "2024-01-01T12:00:01Z"
    }
  ],
  "message_count": 2
}
```

---

## Error Responses

### 400 Bad Request
```json
{
  "detail": "Invalid request format"
}
```

### 404 Not Found
```json
{
  "detail": "Conversation not found"
}
```

### 422 Validation Error
```json
{
  "code": "VALIDATION_ERROR",
  "message": "Input validation failed",
  "details": [
    {
      "loc": ["body", "input"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

### 500 Internal Server Error
```json
{
  "detail": "Internal server error occurred"
}
```

---

## Interactive Documentation

Visit these URLs when the server is running:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Rate Limiting

Currently, no rate limiting is implemented.

## Versioning

The API uses URL versioning (e.g., `/api/v1/`). Breaking changes will result in a new version number.
