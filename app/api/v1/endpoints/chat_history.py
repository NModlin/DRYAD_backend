# app/api/v1/endpoints/chat_history.py
from fastapi import APIRouter, Depends, HTTPException, Query
from app.core.security import get_current_user, User
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from app.database.database import get_db
from app.services.chat_history import ChatHistoryService
from app.api.v1.schemas.chat_history import (
    ConversationCreate,
    ConversationResponse,
    ConversationUpdate,
    ConversationListResponse,
    MessageCreate,
    MessageResponse,
    MessageListResponse,
    ConversationContextResponse
)

router = APIRouter()


@router.post("/conversations", response_model=ConversationResponse, status_code=201)
async def create_conversation(
    conversation: ConversationCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new conversation."""
    try:
        new_conversation = await ChatHistoryService.create_conversation(
            db=db,
            title=conversation.title,
            initial_message=conversation.initial_message
        )
        return new_conversation
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create conversation: {str(e)}")


@router.get("/conversations", response_model=ConversationListResponse)
async def get_conversations(
    limit: int = Query(50, ge=1, le=100, description="Number of conversations to return"),
    offset: int = Query(0, ge=0, description="Number of conversations to skip"),
    active_only: bool = Query(True, description="Only return active conversations"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get a list of conversations."""
    try:
        conversations = await ChatHistoryService.get_conversations(
            db=db,
            limit=limit,
            offset=offset,
            active_only=active_only
        )

        # For simplicity, we're not implementing total count query here
        # In production, you might want to add a separate count query
        return ConversationListResponse(
            conversations=conversations,
            total=len(conversations),
            limit=limit,
            offset=offset
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve conversations: {str(e)}")


@router.get("/conversations/{conversation_id}", response_model=ConversationResponse)
async def get_conversation(
    conversation_id: str,
    include_messages: bool = Query(True, description="Include messages in the response"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get a specific conversation by ID."""
    try:
        conversation = await ChatHistoryService.get_conversation_detached(
            db=db,
            conversation_id=conversation_id,
            include_messages=include_messages
        )

        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")

        # Broadcast real-time update for new conversation
        try:
            from app.api.v1.websocket.endpoints import broadcast_conversation_update
            await broadcast_conversation_update(conversation.id, "conversation_created", {
                "id": conversation.id,
                "title": conversation.title,
                "created_at": conversation.created_at.isoformat()
            })
        except Exception as e:
            logger.warning(f"Failed to broadcast conversation creation: {e}")

        return conversation
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve conversation: {str(e)}")


@router.put("/conversations/{conversation_id}", response_model=ConversationResponse)
async def update_conversation(
    conversation_id: str,
    conversation_update: ConversationUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update a conversation."""
    try:
        updated_conversation = await ChatHistoryService.update_conversation(
            db=db,
            conversation_id=conversation_id,
            title=conversation_update.title,
            is_active=conversation_update.is_active
        )

        if not updated_conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")

        return updated_conversation
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update conversation: {str(e)}")


@router.delete("/conversations/{conversation_id}", status_code=204)
async def delete_conversation(
    conversation_id: str,
    soft_delete: bool = Query(True, description="Perform soft delete (deactivate) instead of hard delete"),
    db: AsyncSession = Depends(get_db)
):
    """Delete a conversation."""
    try:
        success = await ChatHistoryService.delete_conversation(
            db=db,
            conversation_id=conversation_id,
            soft_delete=soft_delete
        )

        if not success:
            raise HTTPException(status_code=404, detail="Conversation not found")

        return None
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete conversation: {str(e)}")


@router.post("/messages", response_model=MessageResponse, status_code=201)
async def add_message(
    message: MessageCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Add a message to a conversation."""
    try:
        new_message = await ChatHistoryService.add_message(
            db=db,
            conversation_id=message.conversation_id,
            role=message.role,
            content=message.content,
            tool_calls=message.tool_calls,
            extra_data=message.extra_data
        )

        if not new_message:
            raise HTTPException(status_code=404, detail="Conversation not found")

        # Broadcast real-time update for new message
        try:
            from app.api.v1.websocket.endpoints import broadcast_new_message
            await broadcast_new_message(message.conversation_id, {
                "id": new_message.id,
                "role": new_message.role,
                "content": new_message.content,
                "created_at": new_message.created_at.isoformat(),
                "tool_calls": new_message.tool_calls,
                "extra_data": new_message.extra_data
            })
        except Exception as e:
            logger.warning(f"Failed to broadcast new message: {e}")

        return new_message
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to add message: {str(e)}")


@router.get("/conversations/{conversation_id}/messages", response_model=MessageListResponse)
async def get_messages(
    conversation_id: str,
    limit: int = Query(100, ge=1, le=500, description="Number of messages to return"),
    offset: int = Query(0, ge=0, description="Number of messages to skip"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get messages for a specific conversation."""
    try:
        # Verify conversation exists
        conversation = await ChatHistoryService.get_conversation(
            db=db,
            conversation_id=conversation_id,
            include_messages=False
        )

        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")

        messages = await ChatHistoryService.get_messages(
            db=db,
            conversation_id=conversation_id,
            limit=limit,
            offset=offset
        )

        return MessageListResponse(
            messages=messages,
            conversation_id=conversation_id,
            total=len(messages),
            limit=limit,
            offset=offset
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve messages: {str(e)}")


@router.get("/conversations/{conversation_id}/context", response_model=ConversationContextResponse)
async def get_conversation_context(
    conversation_id: str,
    max_messages: int = Query(20, ge=1, le=100, description="Maximum number of messages to include in context"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get conversation context for AI agents."""
    try:
        # Verify conversation exists
        conversation = await ChatHistoryService.get_conversation(
            db=db,
            conversation_id=conversation_id,
            include_messages=False
        )

        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")

        context = await ChatHistoryService.get_conversation_context(
            db=db,
            conversation_id=conversation_id,
            max_messages=max_messages
        )

        return ConversationContextResponse(
            conversation_id=conversation_id,
            messages=context,
            context_summary=f"Conversation context with {len(context)} messages"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve conversation context: {str(e)}")
