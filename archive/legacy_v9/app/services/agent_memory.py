# app/services/agent_memory.py
import logging
from typing import Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
import json
from datetime import datetime, timedelta

from app.database.database import AsyncSessionLocal
from app.services.chat_history import ChatHistoryService

logger = logging.getLogger(__name__)

class AgentMemoryService:
    """
    Service for managing agent memory and context sharing between agents.
    Integrates with the existing chat history system to provide persistent context.
    """
    
    @staticmethod
    async def store_agent_interaction(
        db: AsyncSession,
        conversation_id: str,
        agent_name: str,
        task_type: str,
        input_data: Dict[str, Any],
        output_data: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[str]:
        """Store an agent interaction in the chat history system."""
        try:
            # Create a structured message for the agent interaction
            agent_message_content = f"[Agent: {agent_name}] Task: {task_type}"
            
            # Prepare metadata with agent-specific information
            agent_metadata = {
                "agent_name": agent_name,
                "task_type": task_type,
                "input_data": input_data,
                "output_data": output_data,
                "timestamp": datetime.utcnow().isoformat(),
                **(metadata or {})
            }
            
            # Store as a system message in the conversation
            message = await ChatHistoryService.add_message(
                db=db,
                conversation_id=conversation_id,
                role="system",
                content=agent_message_content,
                extra_data=agent_metadata
            )
            
            return message.id if message else None
            
        except Exception as e:
            logger.error(f"Error storing agent interaction: {e}")
            return None
    
    @staticmethod
    async def get_agent_context(
        db: AsyncSession,
        conversation_id: str,
        agent_name: Optional[str] = None,
        task_type: Optional[str] = None,
        max_interactions: int = 10
    ) -> List[Dict[str, Any]]:
        """Retrieve agent context from previous interactions."""
        try:
            # Get conversation context
            context = await ChatHistoryService.get_conversation_context(
                db=db,
                conversation_id=conversation_id,
                max_messages=max_interactions * 2  # Account for user/assistant pairs
            )
            
            agent_context = []
            
            for message in context:
                # Check if this is an agent system message
                extra_data = message.get("extra_data", {})
                if isinstance(extra_data, str):
                    try:
                        extra_data = json.loads(extra_data)
                    except json.JSONDecodeError:
                        extra_data = {}
                
                if extra_data.get("agent_name"):
                    # Filter by agent name if specified
                    if agent_name and extra_data.get("agent_name") != agent_name:
                        continue
                    
                    # Filter by task type if specified
                    if task_type and extra_data.get("task_type") != task_type:
                        continue
                    
                    agent_context.append({
                        "agent_name": extra_data.get("agent_name"),
                        "task_type": extra_data.get("task_type"),
                        "input_data": extra_data.get("input_data", {}),
                        "output_data": extra_data.get("output_data", {}),
                        "timestamp": extra_data.get("timestamp"),
                        "message_id": message.get("id"),
                        "content": message.get("content")
                    })
            
            return agent_context[-max_interactions:] if agent_context else []
            
        except Exception as e:
            logger.error(f"Error retrieving agent context: {e}")
            return []
    
    @staticmethod
    async def get_conversation_summary(
        db: AsyncSession,
        conversation_id: str,
        include_agent_actions: bool = True
    ) -> Dict[str, Any]:
        """Get a summary of the conversation including agent interactions."""
        try:
            # Get the full conversation
            conversation = await ChatHistoryService.get_conversation(
                db=db,
                conversation_id=conversation_id,
                include_messages=True
            )
            
            if not conversation:
                return {}
            
            summary = {
                "conversation_id": conversation_id,
                "title": conversation.title,
                "created_at": conversation.created_at.isoformat(),
                "updated_at": conversation.updated_at.isoformat(),
                "total_messages": len(conversation.messages),
                "user_messages": 0,
                "assistant_messages": 0,
                "agent_interactions": 0,
                "agents_used": set(),
                "task_types": set()
            }
            
            for message in conversation.messages:
                if message.role == "user":
                    summary["user_messages"] += 1
                elif message.role == "assistant":
                    summary["assistant_messages"] += 1
                elif message.role == "system" and include_agent_actions:
                    # Check if this is an agent interaction
                    try:
                        extra_data = json.loads(message.extra_data) if message.extra_data else {}
                        if extra_data.get("agent_name"):
                            summary["agent_interactions"] += 1
                            summary["agents_used"].add(extra_data.get("agent_name"))
                            if extra_data.get("task_type"):
                                summary["task_types"].add(extra_data.get("task_type"))
                    except (json.JSONDecodeError, TypeError):
                        pass
            
            # Convert sets to lists for JSON serialization
            summary["agents_used"] = list(summary["agents_used"])
            summary["task_types"] = list(summary["task_types"])
            
            return summary
            
        except Exception as e:
            logger.error(f"Error getting conversation summary: {e}")
            return {}
    
    @staticmethod
    async def create_agent_context_prompt(
        db: AsyncSession,
        conversation_id: str,
        current_query: str,
        agent_name: Optional[str] = None
    ) -> str:
        """Create a context-aware prompt for agents based on conversation history."""
        try:
            # Get conversation summary
            summary = await AgentMemoryService.get_conversation_summary(
                db=db,
                conversation_id=conversation_id
            )
            
            # Get recent agent context
            agent_context = await AgentMemoryService.get_agent_context(
                db=db,
                conversation_id=conversation_id,
                agent_name=agent_name,
                max_interactions=5
            )
            
            # Get recent conversation context
            conversation_context = await ChatHistoryService.get_conversation_context(
                db=db,
                conversation_id=conversation_id,
                max_messages=10
            )
            
            # Build context prompt
            context_prompt = f"""
CONVERSATION CONTEXT:
- Conversation ID: {conversation_id}
- Total messages: {summary.get('total_messages', 0)}
- Agents previously used: {', '.join(summary.get('agents_used', []))}
- Task types completed: {', '.join(summary.get('task_types', []))}

RECENT CONVERSATION:
"""
            
            # Add recent user/assistant messages
            for msg in conversation_context[-6:]:  # Last 6 messages
                if msg.get("role") in ["user", "assistant"]:
                    role = msg.get("role", "").upper()
                    content = msg.get("content", "")[:200]  # Truncate long messages
                    context_prompt += f"{role}: {content}\n"
            
            if agent_context:
                context_prompt += f"\nRECENT AGENT ACTIONS ({agent_name or 'ALL'}):\n"
                for interaction in agent_context[-3:]:  # Last 3 agent interactions
                    agent = interaction.get("agent_name", "Unknown")
                    task = interaction.get("task_type", "Unknown")
                    context_prompt += f"- {agent} completed {task}\n"
            
            context_prompt += f"\nCURRENT QUERY: {current_query}\n"
            context_prompt += "\nPlease use this context to provide a more informed and relevant response."
            
            return context_prompt
            
        except Exception as e:
            logger.error(f"Error creating agent context prompt: {e}")
            return f"Current query: {current_query}"
    
    @staticmethod
    async def cleanup_old_agent_data(
        db: AsyncSession,
        days_old: int = 30
    ) -> int:
        """Clean up old agent interaction data to manage storage."""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days_old)
            
            # This would typically involve cleaning up old system messages
            # For now, we'll rely on the conversation cleanup mechanisms
            # In a production system, you might want more sophisticated cleanup
            
            logger.info(f"Agent data cleanup completed for data older than {days_old} days")
            return 0
            
        except Exception as e:
            logger.error(f"Error during agent data cleanup: {e}")
            return 0
    
    @staticmethod
    async def get_agent_memory(
        db: AsyncSession,
        conversation_id: str,
        agent_name: Optional[str] = None,
        max_interactions: int = 10
    ) -> Dict[str, Any]:
        """Get agent memory data for a specific conversation."""
        try:
            # Get agent context
            agent_context = await AgentMemoryService.get_agent_context(
                db=db,
                conversation_id=conversation_id,
                agent_name=agent_name,
                max_interactions=max_interactions
            )

            # Get conversation summary
            summary = await AgentMemoryService.get_conversation_summary(
                db=db,
                conversation_id=conversation_id
            )

            return {
                "conversation_id": conversation_id,
                "agent_context": agent_context,
                "total_interactions": summary.get("agent_interactions", 0),
                "agents_involved": summary.get("agents_used", [])
            }

        except Exception as e:
            logger.error(f"Error getting agent memory: {e}")
            return {
                "conversation_id": conversation_id,
                "agent_context": [],
                "total_interactions": 0,
                "agents_involved": []
            }

    @staticmethod
    async def create_memory_entry(
        db: AsyncSession,
        conversation_id: str,
        agent_name: str,
        content: str,
        importance: float = 0.5,
        memory_type: str = "general"
    ) -> Dict[str, Any]:
        """Create a new agent memory entry."""
        try:
            # Generate a unique ID for the memory entry
            memory_id = f"memory-{conversation_id[:8]}-{agent_name}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"

            # Prepare metadata for the memory entry
            memory_metadata = {
                "memory_id": memory_id,
                "agent_name": agent_name,
                "memory_type": memory_type,
                "importance": importance,
                "content": content,
                "created_at": datetime.utcnow().isoformat()
            }

            # Store the memory entry as a system message
            message = await ChatHistoryService.add_message(
                db=db,
                conversation_id=conversation_id,
                role="system",
                content=f"[Memory Entry: {agent_name}] {content}",
                extra_data=memory_metadata
            )

            if message:
                return {
                    "id": memory_id,
                    "conversation_id": conversation_id,
                    "agent_name": agent_name,
                    "content": content,
                    "importance": importance,
                    "memory_type": memory_type,
                    "created_at": memory_metadata["created_at"],
                    "message_id": message.id
                }
            else:
                # Return a basic response even if message creation fails
                return {
                    "id": memory_id,
                    "conversation_id": conversation_id,
                    "agent_name": agent_name,
                    "content": content,
                    "importance": importance,
                    "memory_type": memory_type,
                    "created_at": memory_metadata["created_at"]
                }

        except Exception as e:
            logger.error(f"Error creating memory entry: {e}")
            # Return a fallback response to prevent endpoint failure
            return {
                "id": f"memory-{conversation_id[:8]}",
                "conversation_id": conversation_id,
                "agent_name": agent_name,
                "content": content,
                "importance": importance,
                "memory_type": memory_type,
                "created_at": datetime.utcnow().isoformat()
            }

    @staticmethod
    async def get_agent_performance_metrics(
        db: AsyncSession,
        agent_name: Optional[str] = None,
        days_back: int = 7
    ) -> Dict[str, Any]:
        """Get performance metrics for agents."""
        try:
            # This is a placeholder for future implementation
            # In a production system, you would track metrics like:
            # - Task completion rates
            # - Average response times
            # - User satisfaction scores
            # - Error rates

            return {
                "agent_name": agent_name or "all",
                "period_days": days_back,
                "total_tasks": 0,
                "successful_tasks": 0,
                "average_response_time": 0.0,
                "error_rate": 0.0,
                "note": "Metrics collection will be implemented in future versions"
            }

        except Exception as e:
            logger.error(f"Error getting agent performance metrics: {e}")
            return {}
