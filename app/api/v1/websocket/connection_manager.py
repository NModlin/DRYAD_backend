# app/api/v1/websocket/connection_manager.py
"""
WebSocket connection manager for real-time communication.
Handles WebSocket connections, message broadcasting, and real-time updates.
"""

import json
import logging
import asyncio
from typing import Dict, List, Set, Optional, Any
from fastapi import WebSocket, WebSocketDisconnect
from datetime import datetime

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages WebSocket connections for real-time communication."""
    
    def __init__(self):
        # Active connections by connection ID
        self.active_connections: Dict[str, WebSocket] = {}
        
        # Connections subscribed to specific conversations
        self.conversation_subscribers: Dict[str, Set[str]] = {}
        
        # Connections subscribed to system events
        self.system_subscribers: Set[str] = set()
        
        # Connections subscribed to task updates
        self.task_subscribers: Dict[str, Set[str]] = {}
        
        # Connection metadata
        self.connection_metadata: Dict[str, Dict[str, Any]] = {}
    
    async def connect(self, websocket: WebSocket, connection_id: str, 
                     client_info: Optional[Dict[str, Any]] = None) -> bool:
        """Accept a new WebSocket connection."""
        try:
            await websocket.accept()
            self.active_connections[connection_id] = websocket
            self.connection_metadata[connection_id] = {
                "connected_at": datetime.utcnow(),
                "client_info": client_info or {},
                "subscriptions": []
            }
            
            logger.info(f"WebSocket connection established: {connection_id}")
            
            # Send welcome message
            await self.send_personal_message({
                "type": "connection_established",
                "connection_id": connection_id,
                "timestamp": datetime.utcnow().isoformat(),
                "message": "Connected to DRYAD.AI real-time API"
            }, connection_id)
            
            return True
            
        except Exception as e:
            logger.error(f"Error establishing WebSocket connection {connection_id}: {e}")
            return False
    
    def disconnect(self, connection_id: str):
        """Remove a WebSocket connection."""
        try:
            # Remove from active connections
            if connection_id in self.active_connections:
                del self.active_connections[connection_id]
            
            # Remove from all subscriptions
            self._remove_from_all_subscriptions(connection_id)
            
            # Remove metadata
            if connection_id in self.connection_metadata:
                del self.connection_metadata[connection_id]
            
            logger.info(f"WebSocket connection disconnected: {connection_id}")
            
        except Exception as e:
            logger.error(f"Error disconnecting WebSocket {connection_id}: {e}")
    
    def _remove_from_all_subscriptions(self, connection_id: str):
        """Remove connection from all subscriptions."""
        # Remove from conversation subscriptions
        for conversation_id, subscribers in self.conversation_subscribers.items():
            subscribers.discard(connection_id)
        
        # Remove from system subscriptions
        self.system_subscribers.discard(connection_id)
        
        # Remove from task subscriptions
        for task_id, subscribers in self.task_subscribers.items():
            subscribers.discard(connection_id)
    
    async def send_personal_message(self, message: Dict[str, Any], connection_id: str):
        """Send a message to a specific connection."""
        if connection_id in self.active_connections:
            try:
                websocket = self.active_connections[connection_id]
                await websocket.send_text(json.dumps(message))
            except Exception as e:
                logger.error(f"Error sending message to {connection_id}: {e}")
                # Connection might be dead, remove it
                self.disconnect(connection_id)
    
    async def broadcast_to_conversation(self, conversation_id: str, message: Dict[str, Any]):
        """Broadcast a message to all subscribers of a conversation."""
        if conversation_id in self.conversation_subscribers:
            subscribers = self.conversation_subscribers[conversation_id].copy()
            
            # Add conversation context to message
            message["conversation_id"] = conversation_id
            
            for connection_id in subscribers:
                await self.send_personal_message(message, connection_id)
    
    async def broadcast_system_message(self, message: Dict[str, Any]):
        """Broadcast a system message to all system subscribers."""
        message["type"] = "system_update"
        message["timestamp"] = datetime.utcnow().isoformat()
        
        subscribers = self.system_subscribers.copy()
        for connection_id in subscribers:
            await self.send_personal_message(message, connection_id)
    
    async def broadcast_task_update(self, task_id: str, message: Dict[str, Any]):
        """Broadcast a task update to all task subscribers."""
        if task_id in self.task_subscribers:
            subscribers = self.task_subscribers[task_id].copy()
            
            # Add task context to message
            message["task_id"] = task_id
            message["type"] = "task_update"
            message["timestamp"] = datetime.utcnow().isoformat()
            
            for connection_id in subscribers:
                await self.send_personal_message(message, connection_id)
    
    def subscribe_to_conversation(self, connection_id: str, conversation_id: str):
        """Subscribe a connection to conversation updates."""
        if connection_id not in self.active_connections:
            return False
        
        if conversation_id not in self.conversation_subscribers:
            self.conversation_subscribers[conversation_id] = set()
        
        self.conversation_subscribers[conversation_id].add(connection_id)
        
        # Update connection metadata
        if connection_id in self.connection_metadata:
            subscriptions = self.connection_metadata[connection_id]["subscriptions"]
            if f"conversation:{conversation_id}" not in subscriptions:
                subscriptions.append(f"conversation:{conversation_id}")
        
        logger.info(f"Connection {connection_id} subscribed to conversation {conversation_id}")
        return True
    
    def unsubscribe_from_conversation(self, connection_id: str, conversation_id: str):
        """Unsubscribe a connection from conversation updates."""
        if conversation_id in self.conversation_subscribers:
            self.conversation_subscribers[conversation_id].discard(connection_id)
        
        # Update connection metadata
        if connection_id in self.connection_metadata:
            subscriptions = self.connection_metadata[connection_id]["subscriptions"]
            subscription_key = f"conversation:{conversation_id}"
            if subscription_key in subscriptions:
                subscriptions.remove(subscription_key)
        
        logger.info(f"Connection {connection_id} unsubscribed from conversation {conversation_id}")
    
    def subscribe_to_system(self, connection_id: str):
        """Subscribe a connection to system updates."""
        if connection_id not in self.active_connections:
            return False
        
        self.system_subscribers.add(connection_id)
        
        # Update connection metadata
        if connection_id in self.connection_metadata:
            subscriptions = self.connection_metadata[connection_id]["subscriptions"]
            if "system" not in subscriptions:
                subscriptions.append("system")
        
        logger.info(f"Connection {connection_id} subscribed to system updates")
        return True
    
    def unsubscribe_from_system(self, connection_id: str):
        """Unsubscribe a connection from system updates."""
        self.system_subscribers.discard(connection_id)
        
        # Update connection metadata
        if connection_id in self.connection_metadata:
            subscriptions = self.connection_metadata[connection_id]["subscriptions"]
            if "system" in subscriptions:
                subscriptions.remove("system")
        
        logger.info(f"Connection {connection_id} unsubscribed from system updates")
    
    def subscribe_to_task(self, connection_id: str, task_id: str):
        """Subscribe a connection to task updates."""
        if connection_id not in self.active_connections:
            return False
        
        if task_id not in self.task_subscribers:
            self.task_subscribers[task_id] = set()
        
        self.task_subscribers[task_id].add(connection_id)
        
        # Update connection metadata
        if connection_id in self.connection_metadata:
            subscriptions = self.connection_metadata[connection_id]["subscriptions"]
            if f"task:{task_id}" not in subscriptions:
                subscriptions.append(f"task:{task_id}")
        
        logger.info(f"Connection {connection_id} subscribed to task {task_id}")
        return True
    
    def unsubscribe_from_task(self, connection_id: str, task_id: str):
        """Unsubscribe a connection from task updates."""
        if task_id in self.task_subscribers:
            self.task_subscribers[task_id].discard(connection_id)
        
        # Update connection metadata
        if connection_id in self.connection_metadata:
            subscriptions = self.connection_metadata[connection_id]["subscriptions"]
            subscription_key = f"task:{task_id}"
            if subscription_key in subscriptions:
                subscriptions.remove(subscription_key)
        
        logger.info(f"Connection {connection_id} unsubscribed from task {task_id}")
    
    def get_connection_count(self) -> int:
        """Get the number of active connections."""
        return len(self.active_connections)
    
    def get_connection_info(self, connection_id: str) -> Optional[Dict[str, Any]]:
        """Get information about a specific connection."""
        return self.connection_metadata.get(connection_id)
    
    def get_all_connections_info(self) -> Dict[str, Dict[str, Any]]:
        """Get information about all active connections."""
        return self.connection_metadata.copy()


# Global connection manager instance
connection_manager = ConnectionManager()
