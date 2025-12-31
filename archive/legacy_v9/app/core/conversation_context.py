"""
Context-Aware Conversation Management System
Implements intelligent conversation context tracking, memory management, and Redis-based caching.
"""

import json
import time
import uuid
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import logging

from app.core.logging_config import get_logger
from app.core.caching import cache

logger = get_logger(__name__)


@dataclass
class ConversationTurn:
    """Individual turn in a conversation."""
    turn_id: str
    role: str  # 'user' or 'assistant'
    content: str
    timestamp: float
    metadata: Dict[str, Any]
    context_used: Optional[Dict[str, Any]] = None
    reasoning_steps: Optional[List[Dict[str, Any]]] = None


@dataclass
class ConversationContext:
    """Complete conversation context with memory and state."""
    conversation_id: str
    turns: List[ConversationTurn]
    context_summary: str
    key_topics: List[str]
    user_preferences: Dict[str, Any]
    conversation_state: Dict[str, Any]
    created_at: float
    updated_at: float
    metadata: Dict[str, Any]


class ContextAwareConversationManager:
    """Manages conversation context with intelligent memory and caching."""
    
    def __init__(self, max_context_length: int = 8000, max_turns_memory: int = 20):
        self.max_context_length = max_context_length
        self.max_turns_memory = max_turns_memory
        self.active_conversations: Dict[str, ConversationContext] = {}
        
    async def create_conversation(
        self,
        conversation_id: Optional[str] = None,
        initial_context: Optional[Dict[str, Any]] = None
    ) -> str:
        """Create a new conversation context."""
        if not conversation_id:
            conversation_id = str(uuid.uuid4())
        
        context = ConversationContext(
            conversation_id=conversation_id,
            turns=[],
            context_summary="",
            key_topics=[],
            user_preferences=initial_context.get("user_preferences", {}) if initial_context else {},
            conversation_state=initial_context.get("state", {}) if initial_context else {},
            created_at=time.time(),
            updated_at=time.time(),
            metadata=initial_context.get("metadata", {}) if initial_context else {}
        )
        
        # Store in memory and cache
        self.active_conversations[conversation_id] = context
        await self._cache_conversation_context(context)
        
        logger.info(f"Created conversation context: {conversation_id}")
        return conversation_id
    
    async def add_turn(
        self,
        conversation_id: str,
        role: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
        context_used: Optional[Dict[str, Any]] = None,
        reasoning_steps: Optional[List[Dict[str, Any]]] = None
    ) -> ConversationTurn:
        """Add a new turn to the conversation."""
        # Get or create conversation context
        context = await self.get_conversation_context(conversation_id)
        if not context:
            await self.create_conversation(conversation_id)
            context = self.active_conversations[conversation_id]
        
        # Create new turn
        turn = ConversationTurn(
            turn_id=str(uuid.uuid4()),
            role=role,
            content=content,
            timestamp=time.time(),
            metadata=metadata or {},
            context_used=context_used,
            reasoning_steps=reasoning_steps
        )
        
        # Add turn to context
        context.turns.append(turn)
        context.updated_at = time.time()
        
        # Manage memory limits
        if len(context.turns) > self.max_turns_memory:
            # Keep recent turns and summarize older ones
            await self._compress_conversation_history(context)
        
        # Update context summary and topics
        await self._update_context_intelligence(context)
        
        # Cache updated context
        await self._cache_conversation_context(context)
        
        logger.debug(f"Added turn to conversation {conversation_id}: {role}")
        return turn
    
    async def get_conversation_context(self, conversation_id: str) -> Optional[ConversationContext]:
        """Get conversation context with intelligent loading."""
        # Check memory first
        if conversation_id in self.active_conversations:
            return self.active_conversations[conversation_id]
        
        # Try to load from cache
        cached_context = await self._load_conversation_from_cache(conversation_id)
        if cached_context:
            self.active_conversations[conversation_id] = cached_context
            return cached_context
        
        return None
    
    async def get_contextual_prompt(
        self,
        conversation_id: str,
        current_query: str,
        include_reasoning: bool = True
    ) -> str:
        """Generate a contextual prompt including conversation history."""
        context = await self.get_conversation_context(conversation_id)
        if not context:
            return current_query
        
        # Build contextual prompt
        prompt_parts = []
        
        # Add conversation summary if available
        if context.context_summary:
            prompt_parts.append(f"Conversation Summary: {context.context_summary}")
        
        # Add key topics
        if context.key_topics:
            prompt_parts.append(f"Key Topics: {', '.join(context.key_topics)}")
        
        # Add user preferences
        if context.user_preferences:
            prefs = []
            for key, value in context.user_preferences.items():
                prefs.append(f"{key}: {value}")
            if prefs:
                prompt_parts.append(f"User Preferences: {'; '.join(prefs)}")
        
        # Add recent conversation turns
        recent_turns = context.turns[-5:]  # Last 5 turns
        if recent_turns:
            prompt_parts.append("Recent Conversation:")
            for turn in recent_turns:
                role_label = "User" if turn.role == "user" else "Assistant"
                prompt_parts.append(f"{role_label}: {turn.content}")
        
        # Add current query
        prompt_parts.append(f"Current Query: {current_query}")
        
        # Add reasoning instruction if requested
        if include_reasoning:
            prompt_parts.append(
                "Please provide a thoughtful response that takes into account the conversation context, "
                "user preferences, and maintains consistency with previous interactions."
            )
        
        return "\n\n".join(prompt_parts)
    
    async def extract_user_preferences(self, conversation_id: str) -> Dict[str, Any]:
        """Extract and update user preferences from conversation."""
        context = await self.get_conversation_context(conversation_id)
        if not context:
            return {}
        
        # Analyze conversation for preference indicators
        preferences = context.user_preferences.copy()
        
        # Simple preference extraction (can be enhanced with NLP)
        user_turns = [turn for turn in context.turns if turn.role == "user"]
        
        for turn in user_turns[-10:]:  # Analyze recent user messages
            content = turn.content.lower()
            
            # Extract communication style preferences
            if "brief" in content or "short" in content:
                preferences["response_style"] = "brief"
            elif "detailed" in content or "comprehensive" in content:
                preferences["response_style"] = "detailed"
            
            # Extract topic interests
            if "interested in" in content or "like" in content:
                # Simple keyword extraction (can be enhanced)
                interests = preferences.get("interests", [])
                # Add basic interest detection logic here
                preferences["interests"] = interests
            
            # Extract format preferences
            if "bullet points" in content or "list" in content:
                preferences["format_preference"] = "structured"
            elif "paragraph" in content or "essay" in content:
                preferences["format_preference"] = "narrative"
        
        # Update context
        context.user_preferences = preferences
        await self._cache_conversation_context(context)
        
        return preferences
    
    async def _compress_conversation_history(self, context: ConversationContext):
        """Compress older conversation history to maintain memory limits."""
        if len(context.turns) <= self.max_turns_memory:
            return
        
        # Keep recent turns
        recent_turns = context.turns[-self.max_turns_memory:]
        older_turns = context.turns[:-self.max_turns_memory]
        
        # Create summary of older turns
        if older_turns:
            summary_content = []
            for turn in older_turns:
                summary_content.append(f"{turn.role}: {turn.content[:100]}...")
            
            # Add to context summary
            older_summary = f"Earlier conversation: {'; '.join(summary_content)}"
            if context.context_summary:
                context.context_summary = f"{context.context_summary}\n\n{older_summary}"
            else:
                context.context_summary = older_summary
        
        # Update turns to keep only recent ones
        context.turns = recent_turns
        
        logger.info(f"Compressed conversation history for {context.conversation_id}")
    
    async def _update_context_intelligence(self, context: ConversationContext):
        """Update context summary and extract key topics."""
        if not context.turns:
            return
        
        # Extract key topics from recent turns
        recent_content = []
        for turn in context.turns[-5:]:
            recent_content.append(turn.content)
        
        # Simple topic extraction (can be enhanced with NLP)
        combined_content = " ".join(recent_content).lower()
        
        # Basic keyword extraction for topics
        potential_topics = []
        topic_keywords = [
            "artificial intelligence", "machine learning", "deep learning",
            "programming", "python", "javascript", "web development",
            "data science", "analytics", "business", "technology",
            "health", "finance", "education", "research"
        ]
        
        for keyword in topic_keywords:
            if keyword in combined_content:
                potential_topics.append(keyword)
        
        # Update key topics (keep unique and recent)
        context.key_topics = list(set(context.key_topics + potential_topics))[-10:]
        
        # Update context summary for recent activity
        if len(context.turns) >= 3:
            recent_summary = f"Recent discussion about: {', '.join(context.key_topics[:3])}"
            context.context_summary = recent_summary
    
    async def _cache_conversation_context(self, context: ConversationContext):
        """Cache conversation context in Redis."""
        try:
            cache_key = f"conversation_context:{context.conversation_id}"
            context_data = asdict(context)
            
            # Convert to JSON-serializable format
            context_json = json.dumps(context_data, default=str)
            
            # Cache for 24 hours
            cache.set(
                cache_key,
                context_json,
                ttl=86400  # 24 hours
            )
            
        except Exception as e:
            logger.error(f"Failed to cache conversation context: {e}")
    
    async def _load_conversation_from_cache(self, conversation_id: str) -> Optional[ConversationContext]:
        """Load conversation context from Redis cache."""
        try:
            cache_key = f"conversation_context:{conversation_id}"
            cached_data = cache.get(cache_key)
            
            if cached_data:
                context_data = json.loads(cached_data)
                
                # Reconstruct ConversationTurn objects
                turns = []
                for turn_data in context_data.get("turns", []):
                    turns.append(ConversationTurn(**turn_data))
                
                # Reconstruct ConversationContext
                context_data["turns"] = turns
                return ConversationContext(**context_data)
            
        except Exception as e:
            logger.error(f"Failed to load conversation context from cache: {e}")
        
        return None
    
    async def get_conversation_analytics(self, conversation_id: str) -> Dict[str, Any]:
        """Get analytics and insights about the conversation."""
        context = await self.get_conversation_context(conversation_id)
        if not context:
            return {}
        
        user_turns = [turn for turn in context.turns if turn.role == "user"]
        assistant_turns = [turn for turn in context.turns if turn.role == "assistant"]
        
        analytics = {
            "conversation_id": conversation_id,
            "total_turns": len(context.turns),
            "user_messages": len(user_turns),
            "assistant_messages": len(assistant_turns),
            "duration_hours": (context.updated_at - context.created_at) / 3600,
            "key_topics": context.key_topics,
            "user_preferences": context.user_preferences,
            "avg_user_message_length": sum(len(turn.content) for turn in user_turns) / len(user_turns) if user_turns else 0,
            "avg_assistant_message_length": sum(len(turn.content) for turn in assistant_turns) / len(assistant_turns) if assistant_turns else 0,
            "context_summary": context.context_summary
        }
        
        return analytics


# Global instance
conversation_manager = ContextAwareConversationManager()
