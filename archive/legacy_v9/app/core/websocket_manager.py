# app/core/websocket_manager.py
import logging
import json
import asyncio
from typing import Dict, List, Any, Optional, Set
from fastapi import WebSocket, WebSocketDisconnect
from datetime import datetime

logger = logging.getLogger(__name__)

class ConnectionManager:
    """Manages WebSocket connections for real-time communication."""
    
    def __init__(self):
        # Active connections by session ID
        self.active_connections: Dict[str, WebSocket] = {}
        
        # Subscriptions by topic
        self.subscriptions: Dict[str, Set[str]] = {}
        
        # Connection metadata
        self.connection_metadata: Dict[str, Dict[str, Any]] = {}
    
    async def connect(self, websocket: WebSocket, session_id: str, user_info: Optional[Dict[str, Any]] = None):
        """Accept a WebSocket connection and register it."""
        try:
            await websocket.accept()
            self.active_connections[session_id] = websocket
            
            # Store connection metadata
            self.connection_metadata[session_id] = {
                "connected_at": datetime.utcnow().isoformat(),
                "user_info": user_info or {},
                "subscriptions": set()
            }
            
            logger.info(f"WebSocket connected: {session_id}")
            
            # Send welcome message
            await self.send_personal_message({
                "type": "connection_established",
                "session_id": session_id,
                "timestamp": datetime.utcnow().isoformat(),
                "message": "WebSocket connection established"
            }, session_id)
            
        except Exception as e:
            logger.error(f"Failed to connect WebSocket {session_id}: {e}")
            raise
    
    def disconnect(self, session_id: str):
        """Disconnect and clean up a WebSocket connection."""
        try:
            # Remove from active connections
            if session_id in self.active_connections:
                del self.active_connections[session_id]
            
            # Clean up subscriptions
            if session_id in self.connection_metadata:
                user_subscriptions = self.connection_metadata[session_id].get("subscriptions", set())
                for topic in user_subscriptions:
                    if topic in self.subscriptions:
                        self.subscriptions[topic].discard(session_id)
                        if not self.subscriptions[topic]:
                            del self.subscriptions[topic]
            
            # Remove metadata
            if session_id in self.connection_metadata:
                del self.connection_metadata[session_id]
            
            logger.info(f"WebSocket disconnected: {session_id}")
            
        except Exception as e:
            logger.error(f"Error disconnecting WebSocket {session_id}: {e}")
    
    async def send_personal_message(self, message: Dict[str, Any], session_id: str):
        """Send a message to a specific WebSocket connection."""
        try:
            if session_id in self.active_connections:
                websocket = self.active_connections[session_id]
                await websocket.send_text(json.dumps(message))
                logger.debug(f"Sent message to {session_id}: {message.get('type', 'unknown')}")
            else:
                logger.warning(f"Attempted to send message to disconnected session: {session_id}")
                
        except Exception as e:
            logger.error(f"Failed to send message to {session_id}: {e}")
            # Clean up broken connection
            self.disconnect(session_id)
    
    async def broadcast_to_topic(self, message: Dict[str, Any], topic: str):
        """Broadcast a message to all subscribers of a topic."""
        try:
            if topic in self.subscriptions:
                subscribers = list(self.subscriptions[topic])  # Copy to avoid modification during iteration
                
                for session_id in subscribers:
                    await self.send_personal_message(message, session_id)
                
                logger.debug(f"Broadcasted to topic '{topic}': {len(subscribers)} recipients")
            else:
                logger.debug(f"No subscribers for topic: {topic}")
                
        except Exception as e:
            logger.error(f"Failed to broadcast to topic {topic}: {e}")
    
    async def subscribe_to_topic(self, session_id: str, topic: str):
        """Subscribe a session to a topic."""
        try:
            if session_id not in self.active_connections:
                logger.warning(f"Cannot subscribe inactive session {session_id} to topic {topic}")
                return False
            
            # Add to subscriptions
            if topic not in self.subscriptions:
                self.subscriptions[topic] = set()
            
            self.subscriptions[topic].add(session_id)
            
            # Update connection metadata
            if session_id in self.connection_metadata:
                self.connection_metadata[session_id]["subscriptions"].add(topic)
            
            logger.info(f"Session {session_id} subscribed to topic: {topic}")
            
            # Send confirmation
            await self.send_personal_message({
                "type": "subscription_confirmed",
                "topic": topic,
                "session_id": session_id,
                "timestamp": datetime.utcnow().isoformat()
            }, session_id)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to subscribe {session_id} to topic {topic}: {e}")
            return False
    
    async def unsubscribe_from_topic(self, session_id: str, topic: str):
        """Unsubscribe a session from a topic."""
        try:
            # Remove from subscriptions
            if topic in self.subscriptions:
                self.subscriptions[topic].discard(session_id)
                if not self.subscriptions[topic]:
                    del self.subscriptions[topic]
            
            # Update connection metadata
            if session_id in self.connection_metadata:
                self.connection_metadata[session_id]["subscriptions"].discard(topic)
            
            logger.info(f"Session {session_id} unsubscribed from topic: {topic}")
            
            # Send confirmation
            await self.send_personal_message({
                "type": "unsubscription_confirmed",
                "topic": topic,
                "session_id": session_id,
                "timestamp": datetime.utcnow().isoformat()
            }, session_id)
            
        except Exception as e:
            logger.error(f"Failed to unsubscribe {session_id} from topic {topic}: {e}")
    
    def get_connection_stats(self) -> Dict[str, Any]:
        """Get statistics about active connections."""
        try:
            topic_stats = {}
            for topic, subscribers in self.subscriptions.items():
                topic_stats[topic] = len(subscribers)

            return {
                "active_connections": len(self.active_connections),
                "active_sessions": list(self.active_connections.keys()),
                "topic_subscribers": topic_stats,
                "total_topics": len(self.subscriptions)
            }

        except Exception as e:
            logger.error(f"Failed to get connection stats: {e}")
            return {
                "active_connections": 0,
                "total_topics": 0,
                "topic_subscribers": {}
            }

    def get_connection_count(self) -> int:
        """Compatibility helper: return number of active connections."""
        try:
            return len(self.active_connections)
        except Exception:
            return 0

    async def send_upload_progress(self, session_id: str, upload_id: str, progress: Dict[str, Any]):
        """Send upload progress update to a specific session."""
        message = {
            "type": "upload_progress",
            "upload_id": upload_id,
            "session_id": session_id,
            "progress": progress,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        await self.send_personal_message(message, session_id)
    
    async def send_processing_status(self, session_id: str, task_id: str, status: Dict[str, Any]):
        """Send processing status update to a specific session."""
        message = {
            "type": "processing_status",
            "task_id": task_id,
            "session_id": session_id,
            "status": status,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        await self.send_personal_message(message, session_id)
    
    async def send_completion_notification(self, session_id: str, task_id: str, result: Dict[str, Any]):
        """Send task completion notification to a specific session."""
        message = {
            "type": "task_completed",
            "task_id": task_id,
            "session_id": session_id,
            "result": result,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        await self.send_personal_message(message, session_id)
    
    async def broadcast_system_notification(self, notification: Dict[str, Any]):
        """Broadcast a system-wide notification to all connected clients."""
        message = {
            "type": "system_notification",
            "notification": notification,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Send to all active connections
        for session_id in list(self.active_connections.keys()):
            await self.send_personal_message(message, session_id)

# Global connection manager instance
connection_manager = ConnectionManager()


class RealTimeProcessor:
    """Handles real-time processing tasks with WebSocket notifications."""
    
    def __init__(self, connection_manager: ConnectionManager):
        self.connection_manager = connection_manager
        self.active_tasks: Dict[str, Dict[str, Any]] = {}
    
    async def start_upload_task(self, session_id: str, upload_id: str, total_size: int) -> str:
        """Start tracking an upload task."""
        task_info = {
            "task_id": upload_id,
            "session_id": session_id,
            "task_type": "upload",
            "total_size": total_size,
            "uploaded_size": 0,
            "status": "started",
            "started_at": datetime.utcnow().isoformat()
        }
        
        self.active_tasks[upload_id] = task_info
        
        # Notify client
        await self.connection_manager.send_upload_progress(
            session_id=session_id,
            upload_id=upload_id,
            progress={
                "status": "started",
                "progress_percent": 0,
                "uploaded_size": 0,
                "total_size": total_size,
                "estimated_time_remaining": None
            }
        )
        
        return upload_id
    
    async def update_upload_progress(self, upload_id: str, uploaded_size: int):
        """Update upload progress."""
        if upload_id not in self.active_tasks:
            return
        
        task_info = self.active_tasks[upload_id]
        task_info["uploaded_size"] = uploaded_size
        
        progress_percent = (uploaded_size / task_info["total_size"]) * 100 if task_info["total_size"] > 0 else 0
        
        await self.connection_manager.send_upload_progress(
            session_id=task_info["session_id"],
            upload_id=upload_id,
            progress={
                "status": "uploading",
                "progress_percent": round(progress_percent, 2),
                "uploaded_size": uploaded_size,
                "total_size": task_info["total_size"],
                "estimated_time_remaining": None  # Could calculate based on upload speed
            }
        )
    
    async def complete_upload_task(self, upload_id: str, result: Dict[str, Any]):
        """Complete an upload task."""
        if upload_id not in self.active_tasks:
            return
        
        task_info = self.active_tasks[upload_id]
        task_info["status"] = "completed"
        task_info["completed_at"] = datetime.utcnow().isoformat()
        
        await self.connection_manager.send_completion_notification(
            session_id=task_info["session_id"],
            task_id=upload_id,
            result={
                "task_type": "upload",
                "status": "completed",
                "result": result,
                "duration_seconds": None  # Could calculate from start/end times
            }
        )
        
        # Clean up completed task
        del self.active_tasks[upload_id]
    
    async def start_processing_task(self, session_id: str, task_id: str, task_type: str) -> str:
        """Start tracking a processing task."""
        task_info = {
            "task_id": task_id,
            "session_id": session_id,
            "task_type": task_type,
            "status": "processing",
            "started_at": datetime.utcnow().isoformat()
        }
        
        self.active_tasks[task_id] = task_info
        
        await self.connection_manager.send_processing_status(
            session_id=session_id,
            task_id=task_id,
            status={
                "status": "processing",
                "task_type": task_type,
                "message": f"Started {task_type} processing"
            }
        )
        
        return task_id
    
    async def complete_processing_task(self, task_id: str, result: Dict[str, Any]):
        """Complete a processing task."""
        if task_id not in self.active_tasks:
            return
        
        task_info = self.active_tasks[task_id]
        task_info["status"] = "completed"
        task_info["completed_at"] = datetime.utcnow().isoformat()
        
        await self.connection_manager.send_completion_notification(
            session_id=task_info["session_id"],
            task_id=task_id,
            result={
                "task_type": task_info["task_type"],
                "status": "completed",
                "result": result
            }
        )
        
        # Clean up completed task
        del self.active_tasks[task_id]

# Global real-time processor instance
real_time_processor = RealTimeProcessor(connection_manager)
