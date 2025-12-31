# app/api/v1/schemas/realtime.py
"""
Pydantic schemas for real-time communication and WebSocket APIs.
Phase 6: API Modernization & Real-time Communication
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Union
from datetime import datetime
from enum import Enum


class WebSocketMessageType(str, Enum):
    """Types of WebSocket messages."""
    SUBSCRIBE = "subscribe"
    UNSUBSCRIBE = "unsubscribe"
    PING = "ping"
    PONG = "pong"
    GET_STATUS = "get_status"
    CONNECTION_ESTABLISHED = "connection_established"
    SUBSCRIPTION_CONFIRMED = "subscription_confirmed"
    UNSUBSCRIPTION_CONFIRMED = "unsubscription_confirmed"
    STATUS_RESPONSE = "status_response"
    CONVERSATION_UPDATE = "conversation_update"
    TASK_UPDATE = "task_update"
    SYSTEM_UPDATE = "system_update"
    ERROR = "error"


class SubscriptionType(str, Enum):
    """Types of subscriptions available."""
    CONVERSATION = "conversation"
    SYSTEM = "system"
    TASK = "task"


class WebSocketMessage(BaseModel):
    """Base WebSocket message schema."""
    type: WebSocketMessageType = Field(..., description="Type of the message")
    timestamp: Optional[datetime] = Field(None, description="Message timestamp")
    data: Optional[Dict[str, Any]] = Field(None, description="Message data")


class SubscribeMessage(BaseModel):
    """WebSocket subscription message schema."""
    type: WebSocketMessageType = Field(WebSocketMessageType.SUBSCRIBE, description="Message type")
    subscription_type: SubscriptionType = Field(..., description="Type of subscription")
    conversation_id: Optional[str] = Field(None, description="Conversation ID for conversation subscriptions")
    task_id: Optional[str] = Field(None, description="Task ID for task subscriptions")


class UnsubscribeMessage(BaseModel):
    """WebSocket unsubscription message schema."""
    type: WebSocketMessageType = Field(WebSocketMessageType.UNSUBSCRIBE, description="Message type")
    subscription_type: SubscriptionType = Field(..., description="Type of subscription")
    conversation_id: Optional[str] = Field(None, description="Conversation ID for conversation subscriptions")
    task_id: Optional[str] = Field(None, description="Task ID for task subscriptions")


class PingMessage(BaseModel):
    """WebSocket ping message schema."""
    type: WebSocketMessageType = Field(WebSocketMessageType.PING, description="Message type")


class StatusRequestMessage(BaseModel):
    """WebSocket status request message schema."""
    type: WebSocketMessageType = Field(WebSocketMessageType.GET_STATUS, description="Message type")
    status_type: str = Field("connection", description="Type of status to retrieve")


class ConnectionEstablishedMessage(BaseModel):
    """WebSocket connection established message schema."""
    type: WebSocketMessageType = Field(WebSocketMessageType.CONNECTION_ESTABLISHED, description="Message type")
    connection_id: str = Field(..., description="Unique connection identifier")
    timestamp: datetime = Field(..., description="Connection timestamp")
    message: str = Field(..., description="Welcome message")


class SubscriptionConfirmedMessage(BaseModel):
    """WebSocket subscription confirmed message schema."""
    type: WebSocketMessageType = Field(WebSocketMessageType.SUBSCRIPTION_CONFIRMED, description="Message type")
    subscription_type: SubscriptionType = Field(..., description="Type of subscription")
    success: bool = Field(..., description="Whether subscription was successful")
    conversation_id: Optional[str] = Field(None, description="Conversation ID if applicable")
    task_id: Optional[str] = Field(None, description="Task ID if applicable")


class ConversationUpdateMessage(BaseModel):
    """WebSocket conversation update message schema."""
    type: WebSocketMessageType = Field(WebSocketMessageType.CONVERSATION_UPDATE, description="Message type")
    conversation_id: str = Field(..., description="Conversation ID")
    update_type: str = Field(..., description="Type of update (new_message, status_change, etc.)")
    data: Dict[str, Any] = Field(..., description="Update data")
    timestamp: datetime = Field(..., description="Update timestamp")


class TaskUpdateMessage(BaseModel):
    """WebSocket task update message schema."""
    type: WebSocketMessageType = Field(WebSocketMessageType.TASK_UPDATE, description="Message type")
    task_id: str = Field(..., description="Task ID")
    progress: Optional[float] = Field(None, description="Task progress (0.0 to 1.0)")
    status: str = Field(..., description="Task status")
    result: Optional[str] = Field(None, description="Task result if completed")
    timestamp: datetime = Field(..., description="Update timestamp")


class SystemUpdateMessage(BaseModel):
    """WebSocket system update message schema."""
    type: WebSocketMessageType = Field(WebSocketMessageType.SYSTEM_UPDATE, description="Message type")
    event_type: str = Field(..., description="Type of system event")
    data: Dict[str, Any] = Field(..., description="Event data")
    timestamp: datetime = Field(..., description="Event timestamp")


class ErrorMessage(BaseModel):
    """WebSocket error message schema."""
    type: WebSocketMessageType = Field(WebSocketMessageType.ERROR, description="Message type")
    message: str = Field(..., description="Error message")
    error_code: Optional[str] = Field(None, description="Error code")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")


class ConnectionInfo(BaseModel):
    """Connection information schema."""
    connection_id: str = Field(..., description="Unique connection identifier")
    connected_at: datetime = Field(..., description="Connection timestamp")
    client_info: Dict[str, Any] = Field(..., description="Client information")
    subscriptions: List[str] = Field(..., description="Active subscriptions")


class SystemStatus(BaseModel):
    """System status schema."""
    status: str = Field(..., description="System operational status")
    active_connections: int = Field(..., description="Number of active WebSocket connections")
    active_subscriptions: int = Field(..., description="Number of active subscriptions")
    events_processed_today: int = Field(..., description="Number of events processed today")
    average_latency_ms: float = Field(..., description="Average response latency in milliseconds")
    uptime: float = Field(..., description="System uptime in seconds")
    last_event_time: Optional[str] = Field(None, description="Timestamp of last event")
    system_health: Dict[str, Any] = Field(..., description="Overall system health status")


class RealTimeAPIInfo(BaseModel):
    """Real-time API information schema."""
    websocket_endpoint: str = Field(..., description="WebSocket endpoint URL")
    supported_message_types: List[str] = Field(..., description="Supported message types")
    supported_subscriptions: List[str] = Field(..., description="Supported subscription types")
    connection_count: int = Field(..., description="Current active connections")


# GraphQL-related schemas for real-time features

class GraphQLSubscriptionRequest(BaseModel):
    """GraphQL subscription request schema."""
    query: str = Field(..., description="GraphQL subscription query")
    variables: Optional[Dict[str, Any]] = Field(None, description="Query variables")
    operation_name: Optional[str] = Field(None, description="Operation name")


class GraphQLSubscriptionResponse(BaseModel):
    """GraphQL subscription response schema."""
    data: Optional[Dict[str, Any]] = Field(None, description="Subscription data")
    errors: Optional[List[Dict[str, Any]]] = Field(None, description="GraphQL errors")


class GraphQLRealtimeMessage(BaseModel):
    """GraphQL real-time message schema."""
    id: str = Field(..., description="Message ID")
    type: str = Field(..., description="Message type (start, data, error, complete)")
    payload: Optional[Dict[str, Any]] = Field(None, description="Message payload")


# Enhanced API capabilities

class APICapabilities(BaseModel):
    """API capabilities schema for Phase 6."""
    rest_api: bool = Field(True, description="REST API availability")
    graphql_api: bool = Field(..., description="GraphQL API availability")
    websocket_api: bool = Field(True, description="WebSocket API availability")
    real_time_subscriptions: bool = Field(True, description="Real-time subscription support")
    supported_features: List[str] = Field(..., description="List of supported features")


class ModernAPIResponse(BaseModel):
    """Modern API response schema with enhanced metadata."""
    data: Any = Field(..., description="Response data")
    metadata: Dict[str, Any] = Field(..., description="Response metadata")
    api_version: str = Field("6.0.0", description="API version")
    timestamp: datetime = Field(..., description="Response timestamp")
    request_id: Optional[str] = Field(None, description="Request tracking ID")


# Union types for WebSocket message handling

WebSocketIncomingMessage = Union[
    SubscribeMessage,
    UnsubscribeMessage,
    PingMessage,
    StatusRequestMessage
]

WebSocketOutgoingMessage = Union[
    ConnectionEstablishedMessage,
    SubscriptionConfirmedMessage,
    ConversationUpdateMessage,
    TaskUpdateMessage,
    SystemUpdateMessage,
    ErrorMessage
]


# REST API Schemas for Real-time Endpoints

class SubscriptionRequest(BaseModel):
    """Request schema for creating a real-time subscription."""
    user_id: Optional[str] = Field(None, description="User ID for the subscription")
    event_types: List[str] = Field(..., description="List of event types to subscribe to")
    callback_url: Optional[str] = Field(None, description="Optional callback URL for notifications")
    filters: Optional[Dict[str, Any]] = Field(None, description="Optional filters for events")
    max_events: Optional[int] = Field(None, description="Maximum number of events before expiration")
    expires_in_hours: Optional[int] = Field(None, description="Subscription expiration in hours")


class SubscriptionResponse(BaseModel):
    """Response schema for subscription operations."""
    subscription_id: str = Field(..., description="Unique subscription ID")
    user_id: str = Field(..., description="User ID for the subscription")
    event_types: List[str] = Field(..., description="List of subscribed event types")
    callback_url: Optional[str] = Field(None, description="Callback URL for notifications")
    filters: Optional[Dict[str, Any]] = Field(None, description="Event filters")
    status: str = Field(..., description="Subscription status")
    created_at: str = Field(..., description="Creation timestamp")
    expires_at: Optional[str] = Field(None, description="Expiration timestamp")
    event_count: Optional[int] = Field(None, description="Number of events received")
    last_event_at: Optional[str] = Field(None, description="Last event timestamp")


class SubscriptionUpdateRequest(BaseModel):
    """Request schema for updating a subscription."""
    event_types: Optional[List[str]] = Field(None, description="Updated event types")
    callback_url: Optional[str] = Field(None, description="Updated callback URL")
    filters: Optional[Dict[str, Any]] = Field(None, description="Updated filters")
    status: Optional[str] = Field(None, description="Updated status")


class EventsResponse(BaseModel):
    """Response schema for recent events."""
    events: List[Dict[str, Any]] = Field(..., description="List of recent events")
    total: int = Field(..., description="Total number of events")
    limit: int = Field(..., description="Limit used for pagination")
    offset: int = Field(..., description="Offset used for pagination")
    has_more: bool = Field(..., description="Whether more events are available")
