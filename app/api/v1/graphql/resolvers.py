# app/api/v1/graphql/resolvers.py
"""
GraphQL resolvers for the DRYAD.AI Backend.
Contains resolver functions for GraphQL queries, mutations, and subscriptions.
"""

import logging
from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.database import AsyncSessionLocal
from app.services.chat_history import ChatHistoryService
from app.services.document_service import DocumentService
from app.services.agent_memory import AgentMemoryService
from app.core.multi_agent import multi_agent_orchestrator

logger = logging.getLogger(__name__)


async def conversation_resolver(conversation_id: str) -> Optional[Dict[str, Any]]:
    """Resolve a conversation by ID."""
    try:
        async with AsyncSessionLocal() as db:
            conversation = await ChatHistoryService.get_conversation(
                db=db,
                conversation_id=conversation_id,
                include_messages=True
            )
            
            if not conversation:
                return None
                
            return {
                "id": conversation.id,
                "title": conversation.title,
                "created_at": conversation.created_at,
                "updated_at": conversation.updated_at,
                "is_active": conversation.is_active,
                "messages": [
                    {
                        "id": msg.id,
                        "role": msg.role,
                        "content": msg.content,
                        "created_at": msg.created_at,
                        "tool_calls": msg.tool_calls,
                        "extra_data": msg.extra_data
                    }
                    for msg in conversation.messages
                ]
            }
    except Exception as e:
        logger.error(f"Error resolving conversation {conversation_id}: {e}")
        return None


async def conversations_resolver(limit: int = 50, offset: int = 0) -> Dict[str, Any]:
    """Resolve conversations list with pagination."""
    try:
        async with AsyncSessionLocal() as db:
            conversations = await ChatHistoryService.get_conversations(
                db=db,
                limit=limit,
                offset=offset
            )
            
            return {
                "conversations": [
                    {
                        "id": conv.id,
                        "title": conv.title,
                        "created_at": conv.created_at,
                        "updated_at": conv.updated_at,
                        "is_active": conv.is_active,
                        "messages": []  # Don't load messages for list view
                    }
                    for conv in conversations.conversations
                ],
                "total": conversations.total,
                "limit": limit,
                "offset": offset
            }
    except Exception as e:
        logger.error(f"Error resolving conversations: {e}")
        return {
            "conversations": [],
            "total": 0,
            "limit": limit,
            "offset": offset
        }


async def agent_capabilities_resolver() -> Dict[str, Any]:
    """Resolve agent capabilities."""
    try:
        # Get capabilities from multi-agent orchestrator
        capabilities = multi_agent_orchestrator.get_capabilities()
        
        agents_data = []
        workflows_data = []
        
        # Extract agent information
        if "agents" in capabilities:
            for agent_name, agent_info in capabilities["agents"].items():
                agents_data.append({
                    "name": agent_name,
                    "role": agent_info.get("role", "Unknown"),
                    "capabilities": agent_info.get("capabilities", ""),
                    "tools": agent_info.get("tools", "")
                })
        
        # Extract workflow information
        if "workflows" in capabilities:
            for workflow_name, workflow_info in capabilities["workflows"].items():
                workflows_data.append({
                    "name": workflow_name,
                    "description": workflow_info.get("description", ""),
                    "agents_required": workflow_info.get("agents_required", [])
                })
        
        return {
            "agents": agents_data,
            "workflows": workflows_data,
            "totalAgents": len(agents_data)
        }
    except Exception as e:
        logger.error(f"Error resolving agent capabilities: {e}")
        return {
            "agents": [],
            "workflows": [],
            "totalAgents": 0
        }


async def create_conversation_resolver(title: str, initial_message: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Resolve conversation creation."""
    try:
        async with AsyncSessionLocal() as db:
            conversation = await ChatHistoryService.create_conversation(
                db=db,
                title=title,
                initial_message=initial_message
            )
            
            if not conversation:
                return None
                
            # Get the full conversation with messages
            full_conv = await ChatHistoryService.get_conversation(
                db=db,
                conversation_id=conversation.id,
                include_messages=True
            )
            
            return {
                "id": full_conv.id,
                "title": full_conv.title,
                "created_at": full_conv.created_at,
                "updated_at": full_conv.updated_at,
                "is_active": full_conv.is_active,
                "messageCount": len(full_conv.messages),
                "messages": [
                    {
                        "id": msg.id,
                        "role": msg.role,
                        "content": msg.content,
                        "created_at": msg.created_at
                    }
                    for msg in full_conv.messages
                ]
            }
    except Exception as e:
        logger.error(f"Error creating conversation: {e}")
        return None


async def add_message_resolver(conversation_id: str, role: str, content: str, 
                              tool_calls: Optional[str] = None, 
                              extra_data: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Resolve message addition (replaces sendMessage)."""
    try:
        async with AsyncSessionLocal() as db:
            message = await ChatHistoryService.add_message(
                db=db,
                conversation_id=conversation_id,
                role=role,
                content=content,
                tool_calls=tool_calls,
                extra_data=extra_data
            )
            
            if not message:
                return None
                
            return {
                "id": message.id,
                "conversation_id": message.conversation_id,
                "role": message.role,
                "content": message.content,
                "created_at": message.created_at,
                "tool_calls": message.tool_calls,
                "extra_data": message.extra_data
            }
    except Exception as e:
        logger.error(f"Error adding message: {e}")
        return None


async def execute_agent_resolver(input_data: str, workflow_type: str = "simple_research", 
                                conversation_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Resolve agent execution."""
    try:
        # Execute multi-agent workflow
        result = multi_agent_orchestrator.execute_simple_query(
            query=input_data,
            context=""
        )
        
        return {
            "output": result.get("result", ""),
            "agents_used": result.get("agents_used", []),
            "execution_time": result.get("execution_time", 0.0),
            "workflow_type": workflow_type
        }
    except Exception as e:
        logger.error(f"Error executing agent: {e}")
        return {
            "output": f"Error: {str(e)}",
            "agents_used": [],
            "execution_time": 0.0,
            "workflow_type": workflow_type
        }
