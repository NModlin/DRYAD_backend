"""
WebSocket Manager for University System

Provides real-time communication for the Agentic University System.
Handles WebSocket connections, event broadcasting, and real-time updates.
"""

import asyncio
import json
import logging
from typing import Dict, Set, List, Any, Optional
from fastapi import WebSocket, WebSocketDisconnect
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages WebSocket connections and message broadcasting"""
    
    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        self.connection_info: Dict[str, Dict[str, Any]] = {}
    
    async def connect(self, websocket: WebSocket, channel: str, user_id: str = None):
        """Accept WebSocket connection and add to channel"""
        await websocket.accept()
        
        if channel not in self.active_connections:
            self.active_connections[channel] = set()
        
        self.active_connections[channel].add(websocket)
        
        # Store connection info
        connection_id = id(websocket)
        self.connection_info[connection_id] = {
            "websocket": websocket,
            "channel": channel,
            "user_id": user_id,
            "connected_at": datetime.now(timezone.utc)
        }
        
        logger.info(f"WebSocket connected to channel '{channel}' (user: {user_id})")
        
        # Send welcome message
        await self.send_personal_message(
            websocket,
            {
                "type": "connection_established",
                "message": f"Connected to channel: {channel}",
                "channel": channel,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        )
    
    def disconnect(self, websocket: WebSocket):
        """Remove WebSocket connection"""
        connection_id = id(websocket)
        info = self.connection_info.get(connection_id)
        
        if info:
            channel = info["channel"]
            user_id = info["user_id"]
            
            if channel in self.active_connections:
                self.active_connections[channel].discard(websocket)
                if not self.active_connections[channel]:
                    del self.active_connections[channel]
            
            del self.connection_info[connection_id]
            logger.info(f"WebSocket disconnected from channel '{channel}' (user: {user_id})")
    
    async def send_personal_message(self, websocket: WebSocket, message: Dict[str, Any]):
        """Send message to a specific WebSocket connection"""
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.error(f"Failed to send personal message: {e}")
            self.disconnect(websocket)
    
    async def broadcast_to_channel(self, channel: str, message: Dict[str, Any]):
        """Broadcast message to all connections in a channel"""
        if channel not in self.active_connections:
            return
        
        disconnected = set()
        for websocket in self.active_connections[channel]:
            try:
                await websocket.send_json(message)
            except Exception as e:
                logger.error(f"Failed to broadcast to channel '{channel}': {e}")
                disconnected.add(websocket)
        
        # Remove disconnected sockets
        for websocket in disconnected:
            self.active_connections[channel].discard(websocket)
        
        if not self.active_connections[channel]:
            del self.active_connections[channel]
    
    async def broadcast_to_user(self, user_id: str, message: Dict[str, Any]):
        """Broadcast message to all connections for a specific user"""
        user_connections = []
        
        for connection_id, info in self.connection_info.items():
            if info["user_id"] == user_id:
                user_connections.append(info["websocket"])
        
        disconnected = set()
        for websocket in user_connections:
            try:
                await websocket.send_json(message)
            except Exception as e:
                logger.error(f"Failed to broadcast to user '{user_id}': {e}")
                disconnected.add(websocket)
        
        # Remove disconnected sockets
        for websocket in disconnected:
            self.disconnect(websocket)
    
    def get_connection_stats(self) -> Dict[str, Any]:
        """Get connection statistics"""
        total_connections = sum(len(connections) for connections in self.active_connections.values())
        channels = list(self.active_connections.keys())
        
        return {
            "total_connections": total_connections,
            "active_channels": len(channels),
            "channels": channels,
            "connection_info": {
                channel: len(connections) for channel, connections in self.active_connections.items()
            }
        }


class UniversityWebSocketManager:
    """University-specific WebSocket event manager"""
    
    def __init__(self):
        self.connection_manager = ConnectionManager()
        self.event_handlers = {
            "agent_progress": self._handle_agent_progress_event,
            "competition_update": self._handle_competition_update_event,
            "training_data_collected": self._handle_training_data_event,
            "improvement_proposal": self._handle_improvement_proposal_event,
            "achievement_awarded": self._handle_achievement_event,
            "curriculum_completed": self._handle_curriculum_event,
            "match_result": self._handle_match_result_event,
            "leaderboard_update": self._handle_leaderboard_event
        }
    
    async def handle_websocket_connection(self, websocket: WebSocket, channel: str, user_id: str = None):
        """Handle WebSocket connection lifecycle"""
        await self.connection_manager.connect(websocket, channel, user_id)
        
        try:
            while True:
                # Receive and handle messages from client
                data = await websocket.receive_text()
                await self._handle_client_message(websocket, data)
                
        except WebSocketDisconnect:
            self.connection_manager.disconnect(websocket)
        except Exception as e:
            logger.error(f"WebSocket error: {e}")
            self.connection_manager.disconnect(websocket)
    
    async def _handle_client_message(self, websocket: WebSocket, message: str):
        """Handle messages from WebSocket client"""
        try:
            data = json.loads(message)
            message_type = data.get("type")
            
            if message_type == "ping":
                # Respond to ping
                await self.connection_manager.send_personal_message(
                    websocket,
                    {
                        "type": "pong",
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    }
                )
            elif message_type == "subscribe":
                # Handle subscription requests
                channels = data.get("channels", [])
                await self._handle_subscription(websocket, channels)
            elif message_type == "unsubscribe":
                # Handle unsubscription requests
                channels = data.get("channels", [])
                await self._handle_unsubscription(websocket, channels)
            else:
                logger.warning(f"Unknown message type: {message_type}")
                
        except json.JSONDecodeError:
            logger.error("Invalid JSON message from WebSocket")
        except Exception as e:
            logger.error(f"Error handling client message: {e}")
    
    async def _handle_subscription(self, websocket: WebSocket, channels: List[str]):
        """Handle channel subscription"""
        # For simplicity, we'll use a single channel per connection
        # In a real implementation, you might support multiple channels
        if channels:
            # Note: This is a simplified implementation
            # A real implementation would manage multiple subscriptions per connection
            logger.info(f"Subscription request for channels: {channels}")
    
    async def _handle_unsubscription(self, websocket: WebSocket, channels: List[str]):
        """Handle channel unsubscription"""
        if channels:
            logger.info(f"Unsubscription request for channels: {channels}")
    
    # Event handlers for university system events
    async def _handle_agent_progress_event(self, event_data: Dict[str, Any]):
        """Handle agent progress events"""
        university_id = event_data.get("university_id")
        agent_id = event_data.get("agent_id")
        
        if university_id:
            # Broadcast to university channel
            channel = f"university_{university_id}"
            await self.connection_manager.broadcast_to_channel(channel, {
                "type": "agent_progress",
                "data": event_data,
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
        
        if agent_id:
            # Send to specific user (if user_id is associated with agent)
            # This would require mapping agent_id to user_id
            pass
    
    async def _handle_competition_update_event(self, event_data: Dict[str, Any]):
        """Handle competition update events"""
        university_id = event_data.get("university_id")
        competition_id = event_data.get("competition_id")
        
        if university_id:
            channel = f"university_{university_id}"
            await self.connection_manager.broadcast_to_channel(channel, {
                "type": "competition_update",
                "data": event_data,
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
        
        if competition_id:
            # Also broadcast to competition-specific channel
            channel = f"competition_{competition_id}"
            await self.connection_manager.broadcast_to_channel(channel, {
                "type": "competition_update",
                "data": event_data,
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
    
    async def _handle_training_data_event(self, event_data: Dict[str, Any]):
        """Handle training data collection events"""
        university_id = event_data.get("university_id")
        
        if university_id:
            channel = f"university_{university_id}"
            await self.connection_manager.broadcast_to_channel(channel, {
                "type": "training_data_collected",
                "data": event_data,
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
    
    async def _handle_improvement_proposal_event(self, event_data: Dict[str, Any]):
        """Handle improvement proposal events"""
        university_id = event_data.get("university_id")
        
        if university_id:
            channel = f"university_{university_id}"
            await self.connection_manager.broadcast_to_channel(channel, {
                "type": "improvement_proposal",
                "data": event_data,
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
    
    async def _handle_achievement_event(self, event_data: Dict[str, Any]):
        """Handle achievement events"""
        university_id = event_data.get("university_id")
        agent_id = event_data.get("agent_id")
        
        if university_id:
            channel = f"university_{university_id}"
            await self.connection_manager.broadcast_to_channel(channel, {
                "type": "achievement_awarded",
                "data": event_data,
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
    
    async def _handle_curriculum_event(self, event_data: Dict[str, Any]):
        """Handle curriculum completion events"""
        university_id = event_data.get("university_id")
        agent_id = event_data.get("agent_id")
        
        if university_id:
            channel = f"university_{university_id}"
            await self.connection_manager.broadcast_to_channel(channel, {
                "type": "curriculum_completed",
                "data": event_data,
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
    
    async def _handle_match_result_event(self, event_data: Dict[str, Any]):
        """Handle match result events"""
        university_id = event_data.get("university_id")
        competition_id = event_data.get("competition_id")
        
        if university_id:
            channel = f"university_{university_id}"
            await self.connection_manager.broadcast_to_channel(channel, {
                "type": "match_result",
                "data": event_data,
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
        
        if competition_id:
            channel = f"competition_{competition_id}"
            await self.connection_manager.broadcast_to_channel(channel, {
                "type": "match_result",
                "data": event_data,
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
    
    async def _handle_leaderboard_event(self, event_data: Dict[str, Any]):
        """Handle leaderboard update events"""
        university_id = event_data.get("university_id")
        competition_id = event_data.get("competition_id")
        
        if university_id:
            channel = f"university_{university_id}"
            await self.connection_manager.broadcast_to_channel(channel, {
                "type": "leaderboard_update",
                "data": event_data,
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
    
    # Public methods for emitting events
    async def emit_agent_progress(self, university_id: str, agent_id: str, progress_data: Dict[str, Any]):
        """Emit agent progress event"""
        event_data = {
            "university_id": university_id,
            "agent_id": agent_id,
            "progress": progress_data
        }
        await self._handle_agent_progress_event(event_data)
    
    async def emit_competition_update(self, university_id: str, competition_id: str, update_data: Dict[str, Any]):
        """Emit competition update event"""
        event_data = {
            "university_id": university_id,
            "competition_id": competition_id,
            "update": update_data
        }
        await self._handle_competition_update_event(event_data)
    
    async def emit_training_data_collected(self, university_id: str, collection_data: Dict[str, Any]):
        """Emit training data collection event"""
        event_data = {
            "university_id": university_id,
            "collection": collection_data
        }
        await self._handle_training_data_event(event_data)
    
    async def emit_improvement_proposal(self, university_id: str, proposal_data: Dict[str, Any]):
        """Emit improvement proposal event"""
        event_data = {
            "university_id": university_id,
            "proposal": proposal_data
        }
        await self._handle_improvement_proposal_event(event_data)
    
    async def emit_achievement_awarded(self, university_id: str, agent_id: str, achievement_data: Dict[str, Any]):
        """Emit achievement awarded event"""
        event_data = {
            "university_id": university_id,
            "agent_id": agent_id,
            "achievement": achievement_data
        }
        await self._handle_achievement_event(event_data)
    
    async def emit_curriculum_completed(self, university_id: str, agent_id: str, curriculum_data: Dict[str, Any]):
        """Emit curriculum completed event"""
        event_data = {
            "university_id": university_id,
            "agent_id": agent_id,
            "curriculum": curriculum_data
        }
        await self._handle_curriculum_event(event_data)
    
    async def emit_match_result(self, university_id: str, competition_id: str, match_data: Dict[str, Any]):
        """Emit match result event"""
        event_data = {
            "university_id": university_id,
            "competition_id": competition_id,
            "match": match_data
        }
        await self._handle_match_result_event(event_data)
    
    async def emit_leaderboard_update(self, university_id: str, competition_id: str, leaderboard_data: Dict[str, Any]):
        """Emit leaderboard update event"""
        event_data = {
            "university_id": university_id,
            "competition_id": competition_id,
            "leaderboard": leaderboard_data
        }
        await self._handle_leaderboard_event(event_data)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get WebSocket manager statistics"""
        return self.connection_manager.get_connection_stats()


# Global WebSocket manager instance
websocket_manager = UniversityWebSocketManager()