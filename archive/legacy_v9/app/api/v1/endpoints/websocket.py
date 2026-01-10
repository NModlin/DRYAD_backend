# app/api/v1/endpoints/websocket.py
import logging
import json
import uuid
from typing import Dict, Any, Optional
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.websocket_manager import connection_manager, real_time_processor
from app.database.database import get_db

logger = logging.getLogger(__name__)
router = APIRouter()

@router.websocket("/ws/{session_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    session_id: str,
    user_id: Optional[str] = Query(None),
    user_name: Optional[str] = Query(None)
):
    """Main WebSocket endpoint for real-time communication."""
    try:
        # Prepare user info
        user_info = {}
        if user_id:
            user_info["user_id"] = user_id
        if user_name:
            user_info["user_name"] = user_name
        
        # Connect to WebSocket
        await connection_manager.connect(websocket, session_id, user_info)
        
        try:
            while True:
                # Receive message from client
                data = await websocket.receive_text()
                
                try:
                    message = json.loads(data)
                    await handle_websocket_message(websocket, session_id, message)
                    
                except json.JSONDecodeError:
                    await connection_manager.send_personal_message({
                        "type": "error",
                        "message": "Invalid JSON format",
                        "timestamp": None
                    }, session_id)
                    
                except Exception as e:
                    logger.error(f"Error handling WebSocket message from {session_id}: {e}")
                    await connection_manager.send_personal_message({
                        "type": "error",
                        "message": f"Message handling error: {str(e)}",
                        "timestamp": None
                    }, session_id)
        
        except WebSocketDisconnect:
            logger.info(f"WebSocket disconnected: {session_id}")
        
        except Exception as e:
            logger.error(f"WebSocket error for {session_id}: {e}")
        
        finally:
            connection_manager.disconnect(session_id)
    
    except Exception as e:
        logger.error(f"Failed to establish WebSocket connection for {session_id}: {e}")

async def handle_websocket_message(websocket: WebSocket, session_id: str, message: Dict[str, Any]):
    """Handle incoming WebSocket messages."""
    try:
        message_type = message.get("type")
        
        if message_type == "ping":
            # Respond to ping with pong
            await connection_manager.send_personal_message({
                "type": "pong",
                "timestamp": message.get("timestamp")
            }, session_id)
        
        elif message_type == "subscribe":
            # Subscribe to a topic
            topic = message.get("topic")
            if topic:
                success = await connection_manager.subscribe_to_topic(session_id, topic)
                if not success:
                    await connection_manager.send_personal_message({
                        "type": "error",
                        "message": f"Failed to subscribe to topic: {topic}"
                    }, session_id)
        
        elif message_type == "unsubscribe":
            # Unsubscribe from a topic
            topic = message.get("topic")
            if topic:
                await connection_manager.unsubscribe_from_topic(session_id, topic)
        
        elif message_type == "get_stats":
            # Send connection statistics
            stats = connection_manager.get_connection_stats()
            await connection_manager.send_personal_message({
                "type": "connection_stats",
                "stats": stats
            }, session_id)
        
        elif message_type == "start_upload":
            # Start tracking an upload
            upload_info = message.get("upload_info", {})
            upload_id = upload_info.get("upload_id") or str(uuid.uuid4())
            total_size = upload_info.get("total_size", 0)
            
            await real_time_processor.start_upload_task(session_id, upload_id, total_size)
        
        elif message_type == "upload_progress":
            # Update upload progress
            upload_id = message.get("upload_id")
            uploaded_size = message.get("uploaded_size", 0)
            
            if upload_id:
                await real_time_processor.update_upload_progress(upload_id, uploaded_size)
        
        elif message_type == "start_processing":
            # Start tracking a processing task
            task_info = message.get("task_info", {})
            task_id = task_info.get("task_id") or str(uuid.uuid4())
            task_type = task_info.get("task_type", "unknown")
            
            await real_time_processor.start_processing_task(session_id, task_id, task_type)
        
        else:
            # Unknown message type
            await connection_manager.send_personal_message({
                "type": "error",
                "message": f"Unknown message type: {message_type}"
            }, session_id)
    
    except Exception as e:
        logger.error(f"Error handling message type {message.get('type')}: {e}")
        await connection_manager.send_personal_message({
            "type": "error",
            "message": f"Message processing error: {str(e)}"
        }, session_id)

@router.get("/ws/stats")
async def get_websocket_stats():
    """Get WebSocket connection statistics."""
    try:
        stats = connection_manager.get_connection_stats()
        return {
            "status": "success",
            "stats": stats,
            "timestamp": None
        }
    except Exception as e:
        logger.error(f"Failed to get WebSocket stats: {e}")
        return {
            "status": "error",
            "message": str(e),
            "timestamp": None
        }

@router.post("/ws/broadcast/{topic}")
async def broadcast_to_topic(
    topic: str,
    message: Dict[str, Any]
):
    """Broadcast a message to all subscribers of a topic.

    For test and client compatibility, ensure the message includes a 'type' field.
    """
    try:
        payload: Dict[str, Any] = dict(message) if isinstance(message, dict) else {"payload": message}
        payload.setdefault("type", "broadcast")
        payload.setdefault("topic", topic)
        await connection_manager.broadcast_to_topic(payload, topic)
        return {
            "status": "success",
            "message": f"Broadcasted to topic: {topic}",
            "timestamp": None
        }
    except Exception as e:
        logger.error(f"Failed to broadcast to topic {topic}: {e}")
        return {
            "status": "error",
            "message": str(e),
            "timestamp": None
        }

@router.post("/ws/notify/{session_id}")
async def send_notification(
    session_id: str,
    notification: Dict[str, Any]
):
    """Send a notification to a specific session."""
    try:
        await connection_manager.send_personal_message(notification, session_id)
        return {
            "status": "success",
            "message": f"Notification sent to session: {session_id}",
            "timestamp": None
        }
    except Exception as e:
        logger.error(f"Failed to send notification to {session_id}: {e}")
        return {
            "status": "error",
            "message": str(e),
            "timestamp": None
        }

@router.post("/ws/system-notification")
async def broadcast_system_notification(
    notification: Dict[str, Any]
):
    """Broadcast a system-wide notification to all connected clients."""
    try:
        await connection_manager.broadcast_system_notification(notification)
        return {
            "status": "success",
            "message": "System notification broadcasted",
            "timestamp": None
        }
    except Exception as e:
        logger.error(f"Failed to broadcast system notification: {e}")
        return {
            "status": "error",
            "message": str(e),
            "timestamp": None
        }

# Real-time upload progress tracking
@router.post("/ws/upload/start/{session_id}")
async def start_upload_tracking(
    session_id: str,
    upload_info: Dict[str, Any]
):
    """Start tracking an upload with real-time progress updates."""
    try:
        upload_id = upload_info.get("upload_id") or str(uuid.uuid4())
        total_size = upload_info.get("total_size", 0)
        
        await real_time_processor.start_upload_task(session_id, upload_id, total_size)
        
        return {
            "status": "success",
            "upload_id": upload_id,
            "message": "Upload tracking started",
            "timestamp": None
        }
    except Exception as e:
        logger.error(f"Failed to start upload tracking: {e}")
        return {
            "status": "error",
            "message": str(e),
            "timestamp": None
        }

@router.post("/ws/upload/progress/{upload_id}")
async def update_upload_progress(
    upload_id: str,
    progress_info: Dict[str, Any]
):
    """Update upload progress."""
    try:
        uploaded_size = progress_info.get("uploaded_size", 0)
        
        await real_time_processor.update_upload_progress(upload_id, uploaded_size)
        
        return {
            "status": "success",
            "message": "Upload progress updated",
            "timestamp": None
        }
    except Exception as e:
        logger.error(f"Failed to update upload progress: {e}")
        return {
            "status": "error",
            "message": str(e),
            "timestamp": None
        }

@router.post("/ws/upload/complete/{upload_id}")
async def complete_upload_tracking(
    upload_id: str,
    result: Dict[str, Any]
):
    """Complete upload tracking and notify client."""
    try:
        await real_time_processor.complete_upload_task(upload_id, result)
        
        return {
            "status": "success",
            "message": "Upload completed",
            "timestamp": None
        }
    except Exception as e:
        logger.error(f"Failed to complete upload tracking: {e}")
        return {
            "status": "error",
            "message": str(e),
            "timestamp": None
        }

# Real-time processing status tracking
@router.post("/ws/processing/start/{session_id}")
async def start_processing_tracking(
    session_id: str,
    task_info: Dict[str, Any]
):
    """Start tracking a processing task with real-time status updates."""
    try:
        task_id = task_info.get("task_id") or str(uuid.uuid4())
        task_type = task_info.get("task_type", "processing")
        
        await real_time_processor.start_processing_task(session_id, task_id, task_type)
        
        return {
            "status": "success",
            "task_id": task_id,
            "message": "Processing tracking started",
            "timestamp": None
        }
    except Exception as e:
        logger.error(f"Failed to start processing tracking: {e}")
        return {
            "status": "error",
            "message": str(e),
            "timestamp": None
        }

@router.post("/ws/processing/complete/{task_id}")
async def complete_processing_tracking(
    task_id: str,
    result: Dict[str, Any]
):
    """Complete processing tracking and notify client."""
    try:
        await real_time_processor.complete_processing_task(task_id, result)
        
        return {
            "status": "success",
            "message": "Processing completed",
            "timestamp": None
        }
    except Exception as e:
        logger.error(f"Failed to complete processing tracking: {e}")
        return {
            "status": "error",
            "message": str(e),
            "timestamp": None
        }
