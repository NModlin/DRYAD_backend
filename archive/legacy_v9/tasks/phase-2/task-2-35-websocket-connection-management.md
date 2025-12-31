# Task 2-35: WebSocket Connection Management

**Phase:** 2 - Performance & Production Readiness  
**Week:** 5 - Performance Optimization  
**Priority:** HIGH  
**Estimated Hours:** 4 hours

---

## 📋 OVERVIEW

Implement robust WebSocket connection management with connection pooling, heartbeat/ping-pong, automatic reconnection, and proper cleanup to support real-time features.

---

## 🎯 OBJECTIVES

1. Implement WebSocket connection manager
2. Add heartbeat/ping-pong mechanism
3. Implement connection pooling
4. Add automatic reconnection logic
5. Implement proper connection cleanup
6. Test connection scenarios

---

## 📊 CURRENT STATE

**Existing:**
- Basic WebSocket support in FastAPI
- No connection management
- No heartbeat mechanism

**Gaps:**
- No connection pooling
- No heartbeat/keepalive
- No reconnection logic
- No connection cleanup
- Risk of stale connections

---

## 🔧 IMPLEMENTATION

### 1. WebSocket Connection Manager

Create `app/core/websocket_manager.py`:

```python
"""
WebSocket Connection Manager

Manages WebSocket connections with pooling and heartbeat.
"""
from __future__ import annotations

import asyncio
import logging
from typing import Dict, Set
from datetime import datetime, timedelta
from fastapi import WebSocket, WebSocketDisconnect
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class ConnectionInfo(BaseModel):
    """WebSocket connection information."""
    connection_id: str
    user_id: str | None = None
    connected_at: datetime
    last_ping: datetime
    is_alive: bool = True


class WebSocketManager:
    """Manages WebSocket connections."""
    
    def __init__(
        self,
        ping_interval: int = 30,
        ping_timeout: int = 10,
        max_connections_per_user: int = 5
    ):
        self.active_connections: Dict[str, WebSocket] = {}
        self.connection_info: Dict[str, ConnectionInfo] = {}
        self.user_connections: Dict[str, Set[str]] = {}
        
        self.ping_interval = ping_interval
        self.ping_timeout = ping_timeout
        self.max_connections_per_user = max_connections_per_user
        
        self._heartbeat_task = None
    
    async def connect(
        self,
        websocket: WebSocket,
        connection_id: str,
        user_id: str | None = None
    ) -> bool:
        """
        Accept and register WebSocket connection.
        
        Args:
            websocket: WebSocket connection
            connection_id: Unique connection identifier
            user_id: Optional user identifier
        
        Returns:
            True if connected, False if rejected
        """
        # Check connection limit per user
        if user_id and len(self.user_connections.get(user_id, set())) >= self.max_connections_per_user:
            logger.warning(f"Connection limit reached for user {user_id}")
            await websocket.close(code=1008, reason="Connection limit reached")
            return False
        
        # Accept connection
        await websocket.accept()
        
        # Register connection
        self.active_connections[connection_id] = websocket
        self.connection_info[connection_id] = ConnectionInfo(
            connection_id=connection_id,
            user_id=user_id,
            connected_at=datetime.now(),
            last_ping=datetime.now()
        )
        
        # Track user connections
        if user_id:
            if user_id not in self.user_connections:
                self.user_connections[user_id] = set()
            self.user_connections[user_id].add(connection_id)
        
        logger.info(
            f"WebSocket connected: {connection_id}",
            extra={"connection_id": connection_id, "user_id": user_id}
        )
        
        # Start heartbeat if not running
        if not self._heartbeat_task:
            self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())
        
        return True
    
    async def disconnect(self, connection_id: str):
        """
        Disconnect and cleanup WebSocket connection.
        
        Args:
            connection_id: Connection identifier
        """
        if connection_id not in self.active_connections:
            return
        
        # Get connection info
        info = self.connection_info.get(connection_id)
        
        # Remove from user connections
        if info and info.user_id:
            if info.user_id in self.user_connections:
                self.user_connections[info.user_id].discard(connection_id)
                if not self.user_connections[info.user_id]:
                    del self.user_connections[info.user_id]
        
        # Remove connection
        del self.active_connections[connection_id]
        if connection_id in self.connection_info:
            del self.connection_info[connection_id]
        
        logger.info(
            f"WebSocket disconnected: {connection_id}",
            extra={"connection_id": connection_id}
        )
    
    async def send_message(
        self,
        connection_id: str,
        message: dict
    ):
        """
        Send message to specific connection.
        
        Args:
            connection_id: Connection identifier
            message: Message to send
        """
        if connection_id not in self.active_connections:
            logger.warning(f"Connection not found: {connection_id}")
            return
        
        websocket = self.active_connections[connection_id]
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.error(f"Error sending message: {e}")
            await self.disconnect(connection_id)
    
    async def broadcast(
        self,
        message: dict,
        exclude: Set[str] | None = None
    ):
        """
        Broadcast message to all connections.
        
        Args:
            message: Message to broadcast
            exclude: Connection IDs to exclude
        """
        exclude = exclude or set()
        
        for connection_id in list(self.active_connections.keys()):
            if connection_id not in exclude:
                await self.send_message(connection_id, message)
    
    async def send_to_user(
        self,
        user_id: str,
        message: dict
    ):
        """
        Send message to all connections for a user.
        
        Args:
            user_id: User identifier
            message: Message to send
        """
        if user_id not in self.user_connections:
            return
        
        for connection_id in self.user_connections[user_id]:
            await self.send_message(connection_id, message)
    
    async def _heartbeat_loop(self):
        """Heartbeat loop to check connection health."""
        while True:
            try:
                await asyncio.sleep(self.ping_interval)
                await self._send_pings()
            except Exception as e:
                logger.error(f"Heartbeat error: {e}")
    
    async def _send_pings(self):
        """Send ping to all connections."""
        now = datetime.now()
        dead_connections = []
        
        for connection_id, websocket in list(self.active_connections.items()):
            info = self.connection_info.get(connection_id)
            if not info:
                continue
            
            # Check if connection is stale
            if now - info.last_ping > timedelta(seconds=self.ping_timeout * 2):
                dead_connections.append(connection_id)
                continue
            
            # Send ping
            try:
                await websocket.send_json({"type": "ping"})
                info.last_ping = now
            except Exception as e:
                logger.error(f"Ping failed for {connection_id}: {e}")
                dead_connections.append(connection_id)
        
        # Clean up dead connections
        for connection_id in dead_connections:
            await self.disconnect(connection_id)
    
    def get_stats(self) -> dict:
        """Get connection statistics."""
        return {
            "total_connections": len(self.active_connections),
            "total_users": len(self.user_connections),
            "connections_by_user": {
                user_id: len(conn_ids)
                for user_id, conn_ids in self.user_connections.items()
            }
        }


# Global WebSocket manager
ws_manager = WebSocketManager()
```

---

### 2. WebSocket Endpoint

Create `app/api/v1/endpoints/websocket.py`:

```python
"""
WebSocket Endpoints

Real-time communication endpoints.
"""
from __future__ import annotations

import uuid
import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from app.core.websocket_manager import ws_manager
from app.core.auth import get_current_user_ws

router = APIRouter()
logger = logging.getLogger(__name__)


@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    user_id: str = Depends(get_current_user_ws)
):
    """
    WebSocket endpoint for real-time communication.
    
    Args:
        websocket: WebSocket connection
        user_id: Authenticated user ID
    """
    connection_id = str(uuid.uuid4())
    
    # Connect
    connected = await ws_manager.connect(websocket, connection_id, user_id)
    if not connected:
        return
    
    try:
        while True:
            # Receive message
            data = await websocket.receive_json()
            
            # Handle message types
            if data.get("type") == "pong":
                # Update last ping time
                info = ws_manager.connection_info.get(connection_id)
                if info:
                    from datetime import datetime
                    info.last_ping = datetime.now()
            
            elif data.get("type") == "message":
                # Echo message back
                await ws_manager.send_message(
                    connection_id,
                    {"type": "message", "content": data.get("content")}
                )
            
            elif data.get("type") == "broadcast":
                # Broadcast to all users
                await ws_manager.broadcast(
                    {"type": "broadcast", "content": data.get("content")},
                    exclude={connection_id}
                )
    
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected: {connection_id}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        await ws_manager.disconnect(connection_id)


@router.get("/ws/stats")
async def get_websocket_stats():
    """Get WebSocket connection statistics."""
    return ws_manager.get_stats()
```

---

### 3. Client-Side Reconnection (JavaScript Example)

Create `docs/websocket/CLIENT_EXAMPLE.md`:

```javascript
// WebSocket Client with Auto-Reconnection

class WebSocketClient {
    constructor(url, options = {}) {
        this.url = url;
        this.reconnectDelay = options.reconnectDelay || 1000;
        this.maxReconnectDelay = options.maxReconnectDelay || 30000;
        this.reconnectAttempts = 0;
        this.ws = null;
        this.pingInterval = null;
    }
    
    connect() {
        this.ws = new WebSocket(this.url);
        
        this.ws.onopen = () => {
            console.log('WebSocket connected');
            this.reconnectAttempts = 0;
            this.startPing();
        };
        
        this.ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            
            if (data.type === 'ping') {
                // Respond to ping
                this.send({ type: 'pong' });
            } else {
                // Handle other messages
                this.onMessage(data);
            }
        };
        
        this.ws.onclose = () => {
            console.log('WebSocket closed');
            this.stopPing();
            this.reconnect();
        };
        
        this.ws.onerror = (error) => {
            console.error('WebSocket error:', error);
        };
    }
    
    reconnect() {
        const delay = Math.min(
            this.reconnectDelay * Math.pow(2, this.reconnectAttempts),
            this.maxReconnectDelay
        );
        
        console.log(`Reconnecting in ${delay}ms...`);
        this.reconnectAttempts++;
        
        setTimeout(() => this.connect(), delay);
    }
    
    startPing() {
        this.pingInterval = setInterval(() => {
            if (this.ws.readyState === WebSocket.OPEN) {
                this.send({ type: 'ping' });
            }
        }, 25000); // Ping every 25 seconds
    }
    
    stopPing() {
        if (this.pingInterval) {
            clearInterval(this.pingInterval);
            this.pingInterval = null;
        }
    }
    
    send(data) {
        if (this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify(data));
        }
    }
    
    onMessage(data) {
        // Override this method
        console.log('Received:', data);
    }
}

// Usage
const client = new WebSocketClient('ws://localhost:8000/api/v1/ws');
client.connect();
```

---

## ✅ ACCEPTANCE CRITERIA

- [ ] WebSocket manager implemented
- [ ] Connection pooling working
- [ ] Heartbeat/ping-pong implemented
- [ ] Connection cleanup working
- [ ] Connection limits enforced
- [ ] Statistics endpoint working
- [ ] Client reconnection tested

---

## 🧪 TESTING

```python
# tests/test_websocket.py
"""Tests for WebSocket management."""
import pytest
from fastapi.testclient import TestClient
from app.main import app


def test_websocket_connection():
    """Test WebSocket connection."""
    client = TestClient(app)
    
    with client.websocket_connect("/api/v1/ws") as websocket:
        # Send message
        websocket.send_json({"type": "message", "content": "Hello"})
        
        # Receive response
        data = websocket.receive_json()
        assert data["type"] == "message"


def test_websocket_ping_pong():
    """Test ping-pong mechanism."""
    client = TestClient(app)
    
    with client.websocket_connect("/api/v1/ws") as websocket:
        # Wait for ping
        data = websocket.receive_json()
        if data["type"] == "ping":
            # Send pong
            websocket.send_json({"type": "pong"})
```

---

## 📝 NOTES

- Implement heartbeat to detect dead connections
- Use connection pooling to limit resources
- Implement automatic reconnection on client
- Monitor connection statistics
- Test with network interruptions


