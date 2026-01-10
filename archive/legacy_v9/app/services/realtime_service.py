# app/services/realtime_service.py
"""
Real-time Service for managing real-time communication features.
Handles subscriptions, events, and real-time status monitoring.
"""

import logging
import asyncio
from typing import Dict, Any, List, Optional, Set
from datetime import datetime, timedelta, timezone
from enum import Enum
from dataclasses import dataclass, field
import json
import uuid

logger = logging.getLogger(__name__)


class EventType(str, Enum):
    """Types of real-time events."""
    CONVERSATION_UPDATE = "conversation_update"
    AGENT_STATUS = "agent_status"
    SYSTEM_STATUS = "system_status"
    TASK_UPDATE = "task_update"
    USER_ACTIVITY = "user_activity"
    ERROR = "error"


class SubscriptionStatus(str, Enum):
    """Status of a subscription."""
    ACTIVE = "active"
    PAUSED = "paused"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


@dataclass
class Subscription:
    """Represents a real-time subscription."""
    id: str
    user_id: str
    event_types: List[str]
    callback_url: Optional[str] = None
    filters: Dict[str, Any] = field(default_factory=dict)
    status: SubscriptionStatus = SubscriptionStatus.ACTIVE
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_event_at: Optional[datetime] = None
    event_count: int = 0
    max_events: Optional[int] = None
    expires_at: Optional[datetime] = None


@dataclass
class RealtimeEvent:
    """Represents a real-time event."""
    id: str
    event_type: EventType
    data: Dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.utcnow)
    source: Optional[str] = None
    conversation_id: Optional[str] = None
    user_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class RealtimeService:
    """
    Service for managing real-time communication features.
    Handles event subscriptions, broadcasting, and status monitoring.
    """
    
    def __init__(self):
        self.subscriptions: Dict[str, Subscription] = {}
        self.recent_events: List[RealtimeEvent] = []
        self.event_subscribers: Dict[str, Set[str]] = {}  # event_type -> subscription_ids
        self.user_subscriptions: Dict[str, Set[str]] = {}  # user_id -> subscription_ids
        self.max_recent_events = 1000
        self.cleanup_interval = 3600  # 1 hour
        self.last_cleanup = datetime.now(timezone.utc)
    
    async def create_subscription(
        self,
        user_id: str,
        event_types: List[str],
        callback_url: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None,
        max_events: Optional[int] = None,
        expires_in_hours: Optional[int] = None
    ) -> Subscription:
        """Create a new real-time subscription."""
        subscription_id = str(uuid.uuid4())

        expires_at = None
        if expires_in_hours:
            expires_at = datetime.now(timezone.utc) + timedelta(hours=expires_in_hours)
        
        subscription = Subscription(
            id=subscription_id,
            user_id=user_id,
            event_types=event_types,
            callback_url=callback_url,
            filters=filters or {},
            max_events=max_events,
            expires_at=expires_at
        )
        
        # Store subscription
        self.subscriptions[subscription_id] = subscription
        
        # Index by event types
        for event_type in event_types:
            if event_type not in self.event_subscribers:
                self.event_subscribers[event_type] = set()
            self.event_subscribers[event_type].add(subscription_id)
        
        # Index by user
        if user_id not in self.user_subscriptions:
            self.user_subscriptions[user_id] = set()
        self.user_subscriptions[user_id].add(subscription_id)
        
        logger.info(f"Created subscription {subscription_id} for user {user_id}")
        return subscription
    
    async def get_subscription(self, subscription_id: str) -> Optional[Subscription]:
        """Get a subscription by ID."""
        return self.subscriptions.get(subscription_id)
    
    async def update_subscription(
        self,
        subscription_id: str,
        event_types: Optional[List[str]] = None,
        callback_url: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None,
        status: Optional[SubscriptionStatus] = None
    ) -> Optional[Subscription]:
        """Update an existing subscription."""
        subscription = self.subscriptions.get(subscription_id)
        if not subscription:
            return None
        
        # Remove from old event type indexes if changing event types
        if event_types is not None:
            for old_event_type in subscription.event_types:
                if old_event_type in self.event_subscribers:
                    self.event_subscribers[old_event_type].discard(subscription_id)
            
            # Update event types
            subscription.event_types = event_types
            
            # Add to new event type indexes
            for event_type in event_types:
                if event_type not in self.event_subscribers:
                    self.event_subscribers[event_type] = set()
                self.event_subscribers[event_type].add(subscription_id)
        
        if callback_url is not None:
            subscription.callback_url = callback_url
        
        if filters is not None:
            subscription.filters = filters
        
        if status is not None:
            subscription.status = status
        
        logger.info(f"Updated subscription {subscription_id}")
        return subscription
    
    async def delete_subscription(self, subscription_id: str) -> bool:
        """Delete a subscription."""
        subscription = self.subscriptions.get(subscription_id)
        if not subscription:
            return False
        
        # Remove from indexes
        for event_type in subscription.event_types:
            if event_type in self.event_subscribers:
                self.event_subscribers[event_type].discard(subscription_id)
        
        if subscription.user_id in self.user_subscriptions:
            self.user_subscriptions[subscription.user_id].discard(subscription_id)
        
        # Remove subscription
        del self.subscriptions[subscription_id]
        
        logger.info(f"Deleted subscription {subscription_id}")
        return True
    
    async def publish_event(self, event: RealtimeEvent) -> int:
        """Publish an event to all matching subscriptions."""
        await self._cleanup_if_needed()
        
        # Add to recent events
        self.recent_events.append(event)
        if len(self.recent_events) > self.max_recent_events:
            self.recent_events = self.recent_events[-self.max_recent_events:]
        
        # Find matching subscriptions
        matching_subscriptions = self._find_matching_subscriptions(event)
        
        # Notify subscribers
        notification_count = 0
        for subscription_id in matching_subscriptions:
            subscription = self.subscriptions.get(subscription_id)
            if subscription and subscription.status == SubscriptionStatus.ACTIVE:
                await self._notify_subscription(subscription, event)
                notification_count += 1
        
        logger.debug(f"Published event {event.id} to {notification_count} subscriptions")
        return notification_count
    
    def _find_matching_subscriptions(self, event: RealtimeEvent) -> Set[str]:
        """Find subscriptions that match the given event."""
        matching = set()
        
        # Get subscriptions for this event type
        event_type_str = event.event_type.value
        if event_type_str in self.event_subscribers:
            for subscription_id in self.event_subscribers[event_type_str]:
                subscription = self.subscriptions.get(subscription_id)
                if subscription and self._event_matches_filters(event, subscription):
                    matching.add(subscription_id)
        
        return matching
    
    def _event_matches_filters(self, event: RealtimeEvent, subscription: Subscription) -> bool:
        """Check if an event matches subscription filters."""
        if not subscription.filters:
            return True
        
        # Check conversation filter
        if "conversation_id" in subscription.filters:
            if event.conversation_id != subscription.filters["conversation_id"]:
                return False
        
        # Check user filter
        if "user_id" in subscription.filters:
            if event.user_id != subscription.filters["user_id"]:
                return False
        
        # Check source filter
        if "source" in subscription.filters:
            if event.source != subscription.filters["source"]:
                return False
        
        return True
    
    async def _notify_subscription(self, subscription: Subscription, event: RealtimeEvent):
        """Notify a subscription about an event."""
        try:
            # Update subscription stats
            subscription.last_event_at = datetime.now(timezone.utc)
            subscription.event_count += 1
            
            # Check if subscription has reached max events
            if subscription.max_events and subscription.event_count >= subscription.max_events:
                subscription.status = SubscriptionStatus.EXPIRED
                logger.info(f"Subscription {subscription.id} expired after {subscription.event_count} events")
            
            # In a real implementation, you would send HTTP callback or WebSocket message
            logger.debug(f"Notified subscription {subscription.id} about event {event.id}")
            
        except Exception as e:
            logger.error(f"Failed to notify subscription {subscription.id}: {e}")
    
    async def get_recent_events(
        self,
        limit: int = 50,
        event_types: Optional[List[str]] = None,
        since: Optional[datetime] = None,
        conversation_id: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> List[RealtimeEvent]:
        """Get recent events with optional filtering."""
        events = self.recent_events.copy()
        
        # Apply filters
        if event_types:
            events = [e for e in events if e.event_type.value in event_types]
        
        if since:
            events = [e for e in events if e.timestamp >= since]
        
        if conversation_id:
            events = [e for e in events if e.conversation_id == conversation_id]
        
        if user_id:
            events = [e for e in events if e.user_id == user_id]
        
        # Sort by timestamp (newest first) and limit
        events.sort(key=lambda e: e.timestamp, reverse=True)
        return events[:limit]
    
    async def get_status(self) -> Dict[str, Any]:
        """Get real-time service status."""
        await self._cleanup_if_needed()
        
        active_subscriptions = sum(
            1 for s in self.subscriptions.values() 
            if s.status == SubscriptionStatus.ACTIVE
        )
        
        return {
            "status": "operational",
            "total_subscriptions": len(self.subscriptions),
            "active_subscriptions": active_subscriptions,
            "recent_events_count": len(self.recent_events),
            "supported_event_types": [e.value for e in EventType],
            "last_cleanup": self.last_cleanup.isoformat(),
            "uptime_seconds": (datetime.now(timezone.utc) - self.last_cleanup).total_seconds()
        }
    
    async def _cleanup_if_needed(self):
        """Clean up expired subscriptions and old events."""
        now = datetime.now(timezone.utc)
        if (now - self.last_cleanup).total_seconds() < self.cleanup_interval:
            return
        
        # Clean up expired subscriptions
        expired_subscriptions = []
        for subscription_id, subscription in self.subscriptions.items():
            if (subscription.expires_at and subscription.expires_at <= now) or \
               subscription.status in [SubscriptionStatus.EXPIRED, SubscriptionStatus.CANCELLED]:
                expired_subscriptions.append(subscription_id)
        
        for subscription_id in expired_subscriptions:
            await self.delete_subscription(subscription_id)
        
        self.last_cleanup = now
        logger.info(f"Cleaned up {len(expired_subscriptions)} expired subscriptions")


# Global service instance
realtime_service = RealtimeService()


# Convenience functions
async def create_subscription(user_id: str, event_types: List[str], **kwargs) -> Subscription:
    """Create a new subscription."""
    return await realtime_service.create_subscription(user_id, event_types, **kwargs)


async def publish_event(event_type: EventType, data: Dict[str, Any], **kwargs) -> int:
    """Publish a new event."""
    event = RealtimeEvent(
        id=str(uuid.uuid4()),
        event_type=event_type,
        data=data,
        **kwargs
    )
    return await realtime_service.publish_event(event)
