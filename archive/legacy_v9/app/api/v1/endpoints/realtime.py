# app/api/v1/endpoints/realtime.py
"""
Enhanced REST API endpoints for real-time communication features.
Phase 6: API Modernization & Real-time Communication
"""

import logging
from typing import Dict, Any, List
from fastapi import APIRouter, HTTPException, Depends, Query
from app.core.security import get_current_user, User
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.schemas.realtime import (
    RealTimeAPIInfo,
    ConnectionInfo,
    SystemStatus,
    APICapabilities,
    ModernAPIResponse,
    SubscriptionRequest,
    SubscriptionResponse,
    EventsResponse,
    SubscriptionUpdateRequest
)
from app.core.websocket_manager import connection_manager
from app.core.orchestrator import enhanced_orchestrator
from app.services.realtime_service import realtime_service, EventType
from app.database.database import get_db

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/subscribe", response_model=SubscriptionResponse, summary="Subscribe to Real-time Events")
async def subscribe_to_events(request: SubscriptionRequest, current_user: User = Depends(get_current_user)):
    """
    Subscribe to real-time events with optional filters and callback URL.

    Args:
        request: Subscription request with event types, filters, and callback URL

    Returns:
        SubscriptionResponse: Subscription details including subscription ID
    """
    try:
        # Create subscription using realtime service
        user_id = request.user_id or "anonymous"  # Default user_id if not provided
        subscription = await realtime_service.create_subscription(
            user_id=user_id,
            event_types=request.event_types,
            callback_url=request.callback_url,
            filters=request.filters,
            max_events=request.max_events,
            expires_in_hours=request.expires_in_hours
        )

        return SubscriptionResponse(
            subscription_id=subscription.id,
            user_id=subscription.user_id,
            event_types=subscription.event_types,
            callback_url=subscription.callback_url,
            filters=subscription.filters,
            status=subscription.status.value,
            created_at=subscription.created_at.isoformat(),
            expires_at=subscription.expires_at.isoformat() if subscription.expires_at else None
        )

    except Exception as e:
        logger.error(f"Failed to create subscription: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create subscription: {str(e)}")


@router.get("/status", response_model=SystemStatus, summary="Get Real-time System Status")
async def get_realtime_status(current_user: User = Depends(get_current_user)):
    """
    Get the current status of the real-time system including active subscriptions and events.

    Returns:
        SystemStatus: Current system status and metrics
    """
    try:
        status = await realtime_service.get_status()

        return SystemStatus(
            status="operational",
            active_connections=connection_manager.get_connection_count(),
            active_subscriptions=status["active_subscriptions"],
            events_processed_today=status["recent_events_count"],  # Using recent events as proxy
            average_latency_ms=25.5,  # Mock latency value
            uptime=status["uptime_seconds"],
            last_event_time=None,  # Would be populated with actual last event time
            system_health={
                "overall": "healthy",
                "components": {
                    "realtime_service": "operational",
                    "websocket_manager": "operational",
                    "event_publisher": "operational"
                }
            }
        )

    except Exception as e:
        logger.error(f"Failed to get realtime status: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get system status: {str(e)}")


@router.get("/events", response_model=EventsResponse, summary="Get Recent Events")
async def get_recent_events(
    limit: int = Query(50, ge=1, le=1000, description="Maximum number of events to return"),
    offset: int = Query(0, ge=0, description="Number of events to skip"),
    event_type: str = Query(None, description="Filter by event type"),
    priority: str = Query(None, description="Filter by priority level"),
    since: str = Query(None, description="ISO timestamp to filter events since"),
    current_user: User = Depends(get_current_user)
):
    """
    Get recent events with optional filtering and pagination.

    Args:
        limit: Maximum number of events to return
        offset: Number of events to skip for pagination
        event_type: Filter by specific event type
        priority: Filter by priority level
        since: ISO timestamp to filter events since

    Returns:
        EventsResponse: List of recent events with metadata
    """
    try:
        from datetime import datetime

        # Parse since timestamp if provided
        since_dt = None
        if since:
            try:
                since_dt = datetime.fromisoformat(since.replace('Z', '+00:00'))
            except ValueError:
                raise HTTPException(status_code=422, detail="Invalid since timestamp format")

        # Get events from realtime service
        event_types = [event_type] if event_type else None
        events = await realtime_service.get_recent_events(
            limit=limit + offset,  # Get more to handle offset
            event_types=event_types,
            since=since_dt
        )

        # Apply offset and limit
        paginated_events = events[offset:offset + limit]

        # Convert events to response format
        event_data = []
        for event in paginated_events:
            event_data.append({
                "id": event.id,
                "event_type": event.event_type.value,
                "data": event.data,
                "timestamp": event.timestamp.isoformat(),
                "source": event.source,
                "conversation_id": event.conversation_id,
                "user_id": event.user_id,
                "metadata": event.metadata
            })

        return EventsResponse(
            events=event_data,
            total=len(events),
            limit=limit,
            offset=offset,
            has_more=len(events) > offset + limit
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get recent events: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get recent events: {str(e)}")


@router.get("/subscriptions/{subscription_id}", response_model=SubscriptionResponse, summary="Get Subscription Details")
async def get_subscription(subscription_id: str, current_user: User = Depends(get_current_user)):
    """
    Get details of a specific subscription.

    Args:
        subscription_id: ID of the subscription to retrieve

    Returns:
        SubscriptionResponse: Subscription details
    """
    try:
        subscription = await realtime_service.get_subscription(subscription_id)

        if not subscription:
            raise HTTPException(status_code=404, detail="Subscription not found")

        return SubscriptionResponse(
            subscription_id=subscription.id,
            user_id=subscription.user_id,
            event_types=subscription.event_types,
            callback_url=subscription.callback_url,
            filters=subscription.filters,
            status=subscription.status.value,
            created_at=subscription.created_at.isoformat(),
            expires_at=subscription.expires_at.isoformat() if subscription.expires_at else None,
            event_count=subscription.event_count,
            last_event_at=subscription.last_event_at.isoformat() if subscription.last_event_at else None
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get subscription {subscription_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get subscription: {str(e)}")


@router.put("/subscriptions/{subscription_id}", response_model=SubscriptionResponse, summary="Update Subscription")
async def update_subscription(subscription_id: str, request: SubscriptionUpdateRequest, current_user: User = Depends(get_current_user)):
    """
    Update an existing subscription.

    Args:
        subscription_id: ID of the subscription to update
        request: Updated subscription parameters

    Returns:
        SubscriptionResponse: Updated subscription details
    """
    try:
        subscription = await realtime_service.update_subscription(
            subscription_id=subscription_id,
            event_types=request.event_types,
            callback_url=request.callback_url,
            filters=request.filters,
            status=request.status
        )

        if not subscription:
            raise HTTPException(status_code=404, detail="Subscription not found")

        return SubscriptionResponse(
            subscription_id=subscription.id,
            user_id=subscription.user_id,
            event_types=subscription.event_types,
            callback_url=subscription.callback_url,
            filters=subscription.filters,
            status=subscription.status.value,
            created_at=subscription.created_at.isoformat(),
            expires_at=subscription.expires_at.isoformat() if subscription.expires_at else None,
            event_count=subscription.event_count,
            last_event_at=subscription.last_event_at.isoformat() if subscription.last_event_at else None
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update subscription {subscription_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update subscription: {str(e)}")


@router.delete("/subscriptions/{subscription_id}", summary="Delete Subscription")
async def delete_subscription(subscription_id: str, current_user: User = Depends(get_current_user)):
    """
    Delete a subscription.

    Args:
        subscription_id: ID of the subscription to delete

    Returns:
        Success message
    """
    try:
        success = await realtime_service.delete_subscription(subscription_id)

        if not success:
            raise HTTPException(status_code=404, detail="Subscription not found")

        return {"message": f"Subscription {subscription_id} deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete subscription {subscription_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete subscription: {str(e)}")


@router.get("/info", response_model=RealTimeAPIInfo, summary="Get Real-time API Information")
async def get_realtime_api_info(current_user: User = Depends(get_current_user)):
    """
    Get information about the real-time API capabilities and current status.
    
    Returns:
        RealTimeAPIInfo: Information about WebSocket endpoints and capabilities
    """
    try:
        return RealTimeAPIInfo(
            websocket_endpoint="/api/v1/realtime-ws/ws",
            supported_message_types=[
                "subscribe",
                "unsubscribe", 
                "ping",
                "get_status"
            ],
            supported_subscriptions=[
                "conversation",
                "system",
                "task"
            ],
            connection_count=connection_manager.get_connection_count()
        )
    except Exception as e:
        logger.error(f"Error getting real-time API info: {e}")
        raise HTTPException(status_code=500, detail="Failed to get API information")


@router.get("/connections", response_model=List[ConnectionInfo], summary="Get Active Connections")
async def get_active_connections(current_user: User = Depends(get_current_user)):
    """
    Get information about all active WebSocket connections.
    
    Returns:
        List[ConnectionInfo]: List of active connection information
    """
    try:
        connections_data = connection_manager.get_all_connections_info()
        
        connections = []
        for connection_id, info in connections_data.items():
            connections.append(ConnectionInfo(
                connection_id=connection_id,
                connected_at=info["connected_at"],
                client_info=info["client_info"],
                subscriptions=info["subscriptions"]
            ))
        
        return connections
    except Exception as e:
        logger.error(f"Error getting active connections: {e}")
        raise HTTPException(status_code=500, detail="Failed to get connection information")


@router.get("/connections/{connection_id}", response_model=ConnectionInfo, summary="Get Connection Info")
async def get_connection_info(connection_id: str, current_user: User = Depends(get_current_user)):
    """
    Get information about a specific WebSocket connection.
    
    Args:
        connection_id: The unique connection identifier
        
    Returns:
        ConnectionInfo: Connection information
    """
    try:
        info = connection_manager.get_connection_info(connection_id)
        
        if not info:
            raise HTTPException(status_code=404, detail="Connection not found")
        
        return ConnectionInfo(
            connection_id=connection_id,
            connected_at=info["connected_at"],
            client_info=info["client_info"],
            subscriptions=info["subscriptions"]
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting connection info for {connection_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get connection information")


@router.get("/system/status", response_model=SystemStatus, summary="Get System Status")
async def get_system_status(current_user: User = Depends(get_current_user)):
    """
    Get current system status including component availability and performance metrics.
    
    Returns:
        SystemStatus: Current system status
    """
    try:
        capabilities = enhanced_orchestrator.get_capabilities()
        
        return SystemStatus(
            version=capabilities.get("version", "6.0.0"),
            active_connections=connection_manager.get_connection_count(),
            components={
                "database": True,
                "vector_store": capabilities.get("vector_store_available", False),
                "multi_agent": capabilities.get("multi_agent_available", False),
                "orchestrator": True,
                "websocket": True,
                "graphql": True
            },
            uptime=0.0  # Would be calculated from application startup time
        )
    except Exception as e:
        logger.error(f"Error getting system status: {e}")
        raise HTTPException(status_code=500, detail="Failed to get system status")


@router.get("/capabilities", response_model=APICapabilities, summary="Get API Capabilities")
async def get_api_capabilities(current_user: User = Depends(get_current_user)):
    """
    Get information about available API capabilities and features.
    
    Returns:
        APICapabilities: Available API capabilities
    """
    try:
        # Check if GraphQL is available
        graphql_available = True
        try:
            import strawberry
        except ImportError:
            graphql_available = False
        
        return APICapabilities(
            rest_api=True,
            graphql_api=graphql_available,
            websocket_api=True,
            real_time_subscriptions=True,
            supported_features=[
                "REST API",
                "GraphQL API" if graphql_available else "GraphQL API (disabled)",
                "WebSocket Real-time Communication",
                "Multi-Agent Workflows",
                "Document Management & RAG",
                "Asynchronous Task Orchestration",
                "Real-time Subscriptions",
                "Cross-API Integration"
            ]
        )
    except Exception as e:
        logger.error(f"Error getting API capabilities: {e}")
        raise HTTPException(status_code=500, detail="Failed to get API capabilities")


@router.post("/broadcast/conversation/{conversation_id}", summary="Broadcast to Conversation")
async def broadcast_to_conversation(
    conversation_id: str,
    message: Dict[str, Any],
    update_type: str = Query("custom", description="Type of update to broadcast")
):
    """
    Broadcast a message to all subscribers of a specific conversation.
    
    Args:
        conversation_id: The conversation ID to broadcast to
        message: The message data to broadcast
        update_type: Type of update (new_message, status_change, etc.)
        
    Returns:
        Dict: Broadcast result
    """
    try:
        from app.api.v1.websocket.endpoints import broadcast_conversation_update
        
        await broadcast_conversation_update(conversation_id, update_type, message)
        
        return ModernAPIResponse(
            data={
                "success": True,
                "conversation_id": conversation_id,
                "update_type": update_type,
                "subscribers_notified": len(connection_manager.conversation_subscribers.get(conversation_id, set()))
            },
            metadata={
                "action": "broadcast_conversation_update",
                "conversation_id": conversation_id
            },
            timestamp=logger.info(f"Broadcasted message to conversation {conversation_id}")
        )
    except Exception as e:
        logger.error(f"Error broadcasting to conversation {conversation_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to broadcast message")


@router.post("/broadcast/system", summary="Broadcast System Message")
async def broadcast_system_message(
    message: Dict[str, Any],
    event_type: str = Query("custom", description="Type of system event")
):
    """
    Broadcast a system message to all system subscribers.
    
    Args:
        message: The message data to broadcast
        event_type: Type of system event
        
    Returns:
        Dict: Broadcast result
    """
    try:
        from app.api.v1.websocket.endpoints import broadcast_system_event
        
        await broadcast_system_event(event_type, message)
        
        return ModernAPIResponse(
            data={
                "success": True,
                "event_type": event_type,
                "subscribers_notified": len(connection_manager.system_subscribers)
            },
            metadata={
                "action": "broadcast_system_message",
                "event_type": event_type
            },
            timestamp=logger.info(f"Broadcasted system message: {event_type}")
        )
    except Exception as e:
        logger.error(f"Error broadcasting system message: {e}")
        raise HTTPException(status_code=500, detail="Failed to broadcast system message")


@router.post("/broadcast/task/{task_id}", summary="Broadcast Task Update")
async def broadcast_task_update(
    task_id: str,
    progress: float = Query(..., description="Task progress (0.0 to 1.0)"),
    status: str = Query(..., description="Task status"),
    result: str = Query(None, description="Task result if completed")
):
    """
    Broadcast a task update to all subscribers of a specific task.
    
    Args:
        task_id: The task ID to broadcast to
        progress: Task progress (0.0 to 1.0)
        status: Task status
        result: Task result if completed
        
    Returns:
        Dict: Broadcast result
    """
    try:
        from app.api.v1.websocket.endpoints import broadcast_task_progress
        
        await broadcast_task_progress(task_id, progress, status, result)
        
        return ModernAPIResponse(
            data={
                "success": True,
                "task_id": task_id,
                "progress": progress,
                "status": status,
                "subscribers_notified": len(connection_manager.task_subscribers.get(task_id, set()))
            },
            metadata={
                "action": "broadcast_task_update",
                "task_id": task_id
            },
            timestamp=logger.info(f"Broadcasted task update for {task_id}")
        )
    except Exception as e:
        logger.error(f"Error broadcasting task update for {task_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to broadcast task update")


@router.get("/health", summary="Real-time API Health Check")
async def realtime_health_check(current_user: User = Depends(get_current_user)):
    """
    Health check endpoint for real-time API components.
    
    Returns:
        Dict: Health status of real-time components
    """
    try:
        # Check WebSocket manager
        websocket_healthy = connection_manager is not None
        
        # Check GraphQL availability
        graphql_healthy = True
        try:
            import strawberry
            from app.api.v1.graphql.schema import graphql_schema
        except ImportError:
            graphql_healthy = False
        
        health_status = {
            "status": "healthy" if websocket_healthy and graphql_healthy else "degraded",
            "components": {
                "websocket_manager": websocket_healthy,
                "graphql": graphql_healthy,
                "connection_count": connection_manager.get_connection_count() if websocket_healthy else 0
            },
            "timestamp": logger.info("Real-time API health check completed")
        }
        
        return health_status
    except Exception as e:
        logger.error(f"Error in real-time health check: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": logger.error("Real-time API health check failed")
        }
