"""
WebSocket endpoints for real-time communication in Uni0
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from sqlalchemy.orm import Session
import json
import asyncio
from typing import Dict, List
from datetime import datetime, timezone

from dryad.university.database.database import get_db
from dryad.university.database.models_university import UniversityAgent

router = APIRouter()

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.agent_connections: Dict[int, str] = {}  # agent_id -> connection_id
        self.university_connections: Dict[int, List[str]] = {}  # university_id -> list of connection_ids

    async def connect(self, websocket: WebSocket, connection_id: str):
        await websocket.accept()
        self.active_connections[connection_id] = websocket

    def disconnect(self, connection_id: str):
        if connection_id in self.active_connections:
            del self.active_connections[connection_id]
        
        # Remove from agent connections
        agent_id_to_remove = None
        for agent_id, conn_id in self.agent_connections.items():
            if conn_id == connection_id:
                agent_id_to_remove = agent_id
                break
        if agent_id_to_remove:
            del self.agent_connections[agent_id_to_remove]
        
        # Remove from university connections
        for university_id, connections in self.university_connections.items():
            if connection_id in connections:
                connections.remove(connection_id)
                if not connections:
                    del self.university_connections[university_id]

    async def send_personal_message(self, message: str, connection_id: str):
        if connection_id in self.active_connections:
            await self.active_connections[connection_id].send_text(message)

    async def broadcast_to_university(self, message: str, university_id: int):
        if university_id in self.university_connections:
            disconnected_connections = []
            for connection_id in self.university_connections[university_id]:
                if connection_id in self.active_connections:
                    await self.active_connections[connection_id].send_text(message)
                else:
                    disconnected_connections.append(connection_id)
            
            # Clean up disconnected connections
            for connection_id in disconnected_connections:
                self.university_connections[university_id].remove(connection_id)

    async def broadcast_to_all(self, message: str):
        disconnected_connections = []
        for connection_id, websocket in self.active_connections.items():
            try:
                await websocket.send_text(message)
            except:
                disconnected_connections.append(connection_id)
        
        # Clean up disconnected connections
        for connection_id in disconnected_connections:
            self.disconnect(connection_id)

    def register_agent(self, agent_id: int, connection_id: str):
        self.agent_connections[agent_id] = connection_id

    def register_university(self, university_id: int, connection_id: str):
        if university_id not in self.university_connections:
            self.university_connections[university_id] = []
        self.university_connections[university_id].append(connection_id)

    def get_connection_stats(self):
        return {
            "total_connections": len(self.active_connections),
            "agent_connections": len(self.agent_connections),
            "university_connections": len(self.university_connections),
            "universities_with_connections": list(self.university_connections.keys())
        }

manager = ConnectionManager()

@router.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    """WebSocket endpoint for real-time communication"""
    await manager.connect(websocket, client_id)
    
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # Handle different message types
            message_type = message.get("type")
            
            if message_type == "ping":
                # Respond to ping
                await manager.send_personal_message(
                    json.dumps({
                        "type": "pong",
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    }),
                    client_id
                )
            
            elif message_type == "register_agent":
                # Register an agent connection
                agent_id = message.get("agent_id")
                university_id = message.get("university_id")
                
                if agent_id:
                    manager.register_agent(agent_id, client_id)
                
                if university_id:
                    manager.register_university(university_id, client_id)
                
                await manager.send_personal_message(
                    json.dumps({
                        "type": "registration_confirmed",
                        "agent_id": agent_id,
                        "university_id": university_id,
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    }),
                    client_id
                )
            
            elif message_type == "agent_status_update":
                # Broadcast agent status updates to university
                agent_id = message.get("agent_id")
                university_id = message.get("university_id")
                status = message.get("status")
                
                if university_id:
                    await manager.broadcast_to_university(
                        json.dumps({
                            "type": "agent_status_changed",
                            "agent_id": agent_id,
                            "status": status,
                            "timestamp": datetime.now(timezone.utc).isoformat()
                        }),
                        university_id
                    )
            
            elif message_type == "competition_update":
                # Broadcast competition updates
                competition_id = message.get("competition_id")
                university_id = message.get("university_id")
                update_type = message.get("update_type")
                
                if university_id:
                    await manager.broadcast_to_university(
                        json.dumps({
                            "type": "competition_update",
                            "competition_id": competition_id,
                            "update_type": update_type,
                            "data": message.get("data", {}),
                            "timestamp": datetime.now(timezone.utc).isoformat()
                        }),
                        university_id
                    )
            
            elif message_type == "curriculum_progress":
                # Broadcast curriculum progress updates
                agent_id = message.get("agent_id")
                university_id = message.get("university_id")
                curriculum_id = message.get("curriculum_id")
                progress = message.get("progress")
                
                if university_id:
                    await manager.broadcast_to_university(
                        json.dumps({
                            "type": "curriculum_progress_update",
                            "agent_id": agent_id,
                            "curriculum_id": curriculum_id,
                            "progress": progress,
                            "timestamp": datetime.now(timezone.utc).isoformat()
                        }),
                        university_id
                    )
            
            elif message_type == "chat_message":
                # Handle chat messages
                room_id = message.get("room_id")
                message_text = message.get("message")
                sender_id = message.get("sender_id")
                
                # For now, broadcast to all connections in the same room
                # In a real implementation, you'd have room-based broadcasting
                await manager.broadcast_to_all(
                    json.dumps({
                        "type": "chat_message",
                        "room_id": room_id,
                        "sender_id": sender_id,
                        "message": message_text,
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    })
                )
            
            else:
                # Echo back unknown message types
                await manager.send_personal_message(
                    json.dumps({
                        "type": "echo",
                        "original_message": message,
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    }),
                    client_id
                )
    
    except WebSocketDisconnect:
        manager.disconnect(client_id)

@router.get("/ws/stats")
async def get_websocket_stats():
    """Get WebSocket connection statistics"""
    return manager.get_connection_stats()

@router.post("/ws/broadcast/{university_id}")
async def broadcast_to_university(university_id: int, message: dict):
    """Broadcast a message to all connections in a university"""
    await manager.broadcast_to_university(
        json.dumps(message),
        university_id
    )
    return {"message": f"Broadcast sent to university {university_id}"}

@router.post("/ws/send/{agent_id}")
async def send_to_agent(agent_id: int, message: dict, db: Session = Depends(get_db)):
    """Send a message to a specific agent"""
    # Verify agent exists
    agent = db.query(UniversityAgent).filter(UniversityAgent.id == agent_id).first()
    if not agent:
        return {"error": "Agent not found"}
    
    # Find agent's connection
    if agent_id in manager.agent_connections:
        connection_id = manager.agent_connections[agent_id]
        await manager.send_personal_message(
            json.dumps(message),
            connection_id
        )
        return {"message": f"Message sent to agent {agent_id}"}
    else:
        return {"error": "Agent is not connected"}

# WebSocket message types and their schemas
class WebSocketMessage:
    """Base WebSocket message schema"""
    
    @staticmethod
    def ping():
        return {
            "type": "ping",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    @staticmethod
    def register_agent(agent_id: int, university_id: int):
        return {
            "type": "register_agent",
            "agent_id": agent_id,
            "university_id": university_id,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    @staticmethod
    def agent_status_update(agent_id: int, university_id: int, status: str, data: dict = None):
        return {
            "type": "agent_status_update",
            "agent_id": agent_id,
            "university_id": university_id,
            "status": status,
            "data": data or {},
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    @staticmethod
    def competition_update(competition_id: int, university_id: int, update_type: str, data: dict = None):
        return {
            "type": "competition_update",
            "competition_id": competition_id,
            "university_id": university_id,
            "update_type": update_type,
            "data": data or {},
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    @staticmethod
    def curriculum_progress(agent_id: int, university_id: int, curriculum_id: int, progress: float, data: dict = None):
        return {
            "type": "curriculum_progress",
            "agent_id": agent_id,
            "university_id": university_id,
            "curriculum_id": curriculum_id,
            "progress": progress,
            "data": data or {},
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    @staticmethod
    def chat_message(room_id: str, sender_id: int, message: str, data: dict = None):
        return {
            "type": "chat_message",
            "room_id": room_id,
            "sender_id": sender_id,
            "message": message,
            "data": data or {},
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

# Background task for periodic health checks
async def websocket_health_check():
    """Periodic health check for WebSocket connections"""
    while True:
        await asyncio.sleep(30)  # Check every 30 seconds
        
        # Send ping to all connections and check for responses
        current_time = datetime.now(timezone.utc).isoformat()
        ping_message = json.dumps({
            "type": "health_check",
            "timestamp": current_time
        })
        
        await manager.broadcast_to_all(ping_message)
        
        # Log connection statistics
        stats = manager.get_connection_stats()
        print(f"WebSocket Health Check - Connections: {stats}")

# You would typically start this in your main application startup
# asyncio.create_task(websocket_health_check())