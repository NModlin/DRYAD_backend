"""
RADAR Integration Endpoints

API endpoints for RADAR ↔ Dryad.AI integration.
Provides chat, knowledge search, and feedback functionality.
"""

import logging
import time
import uuid
from datetime import datetime, timezone
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc

from app.core.radar_auth import get_radar_user
from app.core.security import User
from app.database.database import get_db
from app.database.models import Conversation, Message
from app.database.models_radar import RADARFeedback, RADARContextLog
from app.api.v1.schemas.radar import (
    ChatMessageRequest,
    ChatMessageResponse,
    ConversationListResponse,
    ConversationListItem,
    ConversationMessagesResponse,
    MessageItem,
    KnowledgeSearchRequest,
    KnowledgeSearchResponse,
    KnowledgeSearchResult,
    FeedbackRequest,
    FeedbackResponse,
    RADARErrorResponse,
    RADARHealthResponse
)

logger = logging.getLogger(__name__)

router = APIRouter()


# ============================================================================
# Health Check Endpoints
# ============================================================================

@router.get("/health", response_model=RADARHealthResponse)
async def health_check(db: AsyncSession = Depends(get_db)):
    """
    Health check endpoint for RADAR integration.
    No authentication required.
    """
    try:
        # Check database connection
        await db.execute(select(1))
        db_status = "connected"
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        db_status = "disconnected"
    
    # Check LLM availability
    try:
        from app.core.llm_config import get_llm_info
        llm_info = get_llm_info()
        llm_status = "available" if llm_info.get("available") else "unavailable"
    except Exception:
        llm_status = "unknown"
    
    return RADARHealthResponse(
        status="healthy" if db_status == "connected" else "degraded",
        database=db_status,
        dryad="connected",
        llm=llm_status,
        timestamp=datetime.now(timezone.utc)
    )


# ============================================================================
# Chat Endpoints
# ============================================================================

@router.post("/api/chat/message", response_model=ChatMessageResponse)
async def send_chat_message(
    request: ChatMessageRequest,
    current_user: User = Depends(get_radar_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Send a chat message and get AI response.
    
    This is the main chat endpoint that RADAR uses for AI interactions.
    """
    start_time = time.time()
    
    try:
        # Get or create conversation
        conversation_id = request.conversationId
        
        if not conversation_id:
            # Create new conversation
            new_conversation = Conversation(
                id=str(uuid.uuid4()),
                user_id=current_user.id,
                title=request.message[:50] + "..." if len(request.message) > 50 else request.message,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
                is_active=True
            )
            db.add(new_conversation)
            await db.flush()
            conversation_id = new_conversation.id
            logger.info(f"Created new conversation: {conversation_id}")
        else:
            # Verify conversation exists and belongs to user
            result = await db.execute(
                select(Conversation).where(
                    Conversation.id == conversation_id,
                    Conversation.user_id == current_user.id
                )
            )
            conversation = result.scalar_one_or_none()
            
            if not conversation:
                raise HTTPException(
                    status_code=404,
                    detail=f"Conversation {conversation_id} not found or access denied"
                )
        
        # Add user message to conversation
        user_message = Message(
            id=str(uuid.uuid4()),
            conversation_id=conversation_id,
            role="user",
            content=request.message,
            created_at=datetime.now(timezone.utc)
        )
        db.add(user_message)
        await db.flush()
        
        # Log RADAR context for analytics
        if request.context:
            context_log = RADARContextLog(
                id=str(uuid.uuid4()),
                conversation_id=conversation_id,
                message_id=user_message.id,
                radar_user_id=request.context.userId,
                radar_username=request.context.username,
                department=request.context.department,
                user_context=request.context.user,
                session_context=request.context.session,
                environment_context=request.context.environment,
                recent_actions=request.context.recentActions,
                request_path="/api/chat/message",
                request_method="POST",
                created_at=datetime.now(timezone.utc)
            )
            db.add(context_log)
        
        # Generate AI response
        ai_response, suggestions, metadata = await _generate_ai_response(
            query=request.message,
            conversation_id=conversation_id,
            context=request.context,
            db=db
        )
        
        # Add assistant message to conversation
        assistant_message = Message(
            id=str(uuid.uuid4()),
            conversation_id=conversation_id,
            role="assistant",
            content=ai_response,
            created_at=datetime.now(timezone.utc)
        )
        db.add(assistant_message)
        
        # Update conversation timestamp
        await db.execute(
            select(Conversation).where(Conversation.id == conversation_id)
        )
        
        await db.commit()
        
        # Calculate response time
        response_time = int((time.time() - start_time) * 1000)  # milliseconds
        metadata["responseTime"] = response_time
        
        # Update context log with response time
        if request.context:
            context_log.response_time_ms = response_time
            await db.commit()
        
        logger.info(f"✅ Chat message processed in {response_time}ms")
        
        return ChatMessageResponse(
            success=True,
            conversationId=conversation_id,
            messageId=assistant_message.id,
            response=ai_response,
            suggestions=suggestions,
            metadata=metadata
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing chat message: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process chat message: {str(e)}"
        )


@router.get("/api/chat/conversations", response_model=ConversationListResponse)
async def get_conversations(
    limit: int = Query(50, ge=1, le=100, description="Number of conversations to return"),
    offset: int = Query(0, ge=0, description="Number of conversations to skip"),
    current_user: User = Depends(get_radar_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get list of conversations for the current user.
    """
    try:
        # Get total count
        count_result = await db.execute(
            select(func.count(Conversation.id)).where(
                Conversation.user_id == current_user.id,
                Conversation.is_active == True
            )
        )
        total = count_result.scalar() or 0
        
        # Get conversations with message count
        result = await db.execute(
            select(
                Conversation,
                func.count(Message.id).label('message_count')
            )
            .outerjoin(Message, Message.conversation_id == Conversation.id)
            .where(
                Conversation.user_id == current_user.id,
                Conversation.is_active == True
            )
            .group_by(Conversation.id)
            .order_by(desc(Conversation.updated_at))
            .limit(limit)
            .offset(offset)
        )
        
        conversations = []
        for row in result:
            conv = row[0]
            msg_count = row[1] or 0
            conversations.append(
                ConversationListItem(
                    id=conv.id,
                    title=conv.title,
                    created_at=conv.created_at,
                    updated_at=conv.updated_at,
                    message_count=msg_count,
                    is_active=conv.is_active
                )
            )
        
        return ConversationListResponse(
            success=True,
            conversations=conversations,
            total=total,
            limit=limit,
            offset=offset
        )
        
    except Exception as e:
        logger.error(f"Error fetching conversations: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch conversations: {str(e)}"
        )


@router.get("/api/chat/conversations/{conversation_id}/messages", response_model=ConversationMessagesResponse)
async def get_conversation_messages(
    conversation_id: str,
    limit: int = Query(100, ge=1, le=500, description="Number of messages to return"),
    offset: int = Query(0, ge=0, description="Number of messages to skip"),
    current_user: User = Depends(get_radar_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get messages for a specific conversation.
    """
    try:
        # Verify conversation exists and belongs to user
        conv_result = await db.execute(
            select(Conversation).where(
                Conversation.id == conversation_id,
                Conversation.user_id == current_user.id
            )
        )
        conversation = conv_result.scalar_one_or_none()
        
        if not conversation:
            raise HTTPException(
                status_code=404,
                detail=f"Conversation {conversation_id} not found or access denied"
            )
        
        # Get total message count
        count_result = await db.execute(
            select(func.count(Message.id)).where(Message.conversation_id == conversation_id)
        )
        total = count_result.scalar() or 0
        
        # Get messages
        result = await db.execute(
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.created_at)
            .limit(limit)
            .offset(offset)
        )
        messages = result.scalars().all()
        
        message_items = [
            MessageItem(
                id=msg.id,
                role=msg.role,
                content=msg.content,
                created_at=msg.created_at,
                metadata={"tool_calls": msg.tool_calls, "extra_data": msg.extra_data} if msg.tool_calls or msg.extra_data else None
            )
            for msg in messages
        ]
        
        return ConversationMessagesResponse(
            success=True,
            conversationId=conversation_id,
            messages=message_items,
            total=total
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching messages: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch messages: {str(e)}"
        )


# ============================================================================
# Knowledge Base Endpoints
# ============================================================================

@router.post("/api/knowledge/search", response_model=KnowledgeSearchResponse)
async def search_knowledge_base(
    request: KnowledgeSearchRequest,
    current_user: User = Depends(get_radar_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Search the knowledge base using RAG (Retrieval-Augmented Generation).

    Returns relevant documents from the knowledge base.
    """
    start_time = time.time()

    try:
        from app.core.rag_system import rag_system

        # Build filter conditions from request
        filter_conditions = {}
        if request.filters:
            if request.filters.category:
                filter_conditions["category"] = request.filters.category
            if request.filters.tags:
                filter_conditions["tags"] = request.filters.tags
            if request.filters.source:
                filter_conditions["source"] = request.filters.source

        # Execute RAG search
        rag_result = await rag_system.retrieve_and_generate(
            db=db,
            query=request.query,
            search_limit=request.limit,
            score_threshold=0.1,
            use_multi_agent=False,
            filter_conditions=filter_conditions if filter_conditions else None
        )

        # Transform results to RADAR format
        results = []
        for doc in rag_result.get("retrieved_docs", []):
            results.append(
                KnowledgeSearchResult(
                    id=doc.get("id", str(uuid.uuid4())),
                    title=doc.get("document_title", "Untitled"),
                    content=doc.get("content", "")[:500],  # Limit content length
                    relevanceScore=doc.get("score", 0.0),
                    source=doc.get("metadata", {}).get("source", "unknown"),
                    url=doc.get("metadata", {}).get("url"),
                    metadata=doc.get("metadata", {})
                )
            )

        query_time = int((time.time() - start_time) * 1000)  # milliseconds

        logger.info(f"✅ Knowledge search completed in {query_time}ms, found {len(results)} results")

        return KnowledgeSearchResponse(
            success=True,
            results=results,
            totalResults=len(results),
            queryTime=query_time
        )

    except Exception as e:
        logger.error(f"Error searching knowledge base: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to search knowledge base: {str(e)}"
        )


# ============================================================================
# Feedback Endpoints
# ============================================================================

@router.post("/api/chat/feedback", response_model=FeedbackResponse)
async def submit_feedback(
    request: FeedbackRequest,
    current_user: User = Depends(get_radar_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Submit user feedback for a message.
    """
    try:
        # Verify message exists
        msg_result = await db.execute(
            select(Message).where(Message.id == request.messageId)
        )
        message = msg_result.scalar_one_or_none()

        if not message:
            raise HTTPException(
                status_code=404,
                detail=f"Message {request.messageId} not found"
            )

        # Create feedback record
        feedback = RADARFeedback(
            id=str(uuid.uuid4()),
            message_id=request.messageId,
            conversation_id=message.conversation_id,
            user_id=current_user.id,
            rating=request.rating,
            comment=request.comment,
            created_at=datetime.now(timezone.utc)
        )
        db.add(feedback)
        await db.commit()

        logger.info(f"✅ Feedback recorded: {feedback.id} ({request.rating})")

        return FeedbackResponse(
            success=True,
            feedbackId=feedback.id,
            message="Feedback recorded successfully"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error submitting feedback: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to submit feedback: {str(e)}"
        )


# ============================================================================
# Helper Functions
# ============================================================================

async def _generate_ai_response(
    query: str,
    conversation_id: str,
    context: Optional[any],
    db: AsyncSession
) -> tuple[str, List[str], dict]:
    """
    Generate AI response using LLM with context awareness.

    Returns:
        Tuple of (response_text, suggestions, metadata)
    """
    try:
        from app.core.llm_config import get_llm, get_llm_info
        from app.services.chat_history import ChatHistoryService

        # Get conversation history for context
        conversation = await ChatHistoryService.get_conversation(
            db=db,
            conversation_id=conversation_id,
            include_messages=True
        )

        # Build context from conversation history
        context_messages = []
        if conversation and conversation.messages:
            for msg in conversation.messages[-5:]:  # Last 5 messages
                context_messages.append(f"{msg.role}: {msg.content}")

        # Build enhanced prompt with RADAR context
        prompt_parts = []

        # Add RADAR context if available
        if context:
            prompt_parts.append("Context from RADAR system:")
            if context.username:
                prompt_parts.append(f"- User: {context.username}")
            if context.department:
                prompt_parts.append(f"- Department: {context.department}")
            if context.environment:
                env = context.environment
                if isinstance(env, dict):
                    if env.get("adDomain"):
                        prompt_parts.append(f"- AD Domain: {env['adDomain']}")
            prompt_parts.append("")

        # Add conversation history
        if context_messages:
            prompt_parts.append("Recent conversation:")
            prompt_parts.extend(context_messages[-3:])  # Last 3 messages
            prompt_parts.append("")

        # Add current query
        prompt_parts.append(f"User query: {query}")
        prompt_parts.append("")
        prompt_parts.append("Please provide a helpful, accurate response. If this is about IT support or Active Directory, provide specific technical guidance.")

        full_prompt = "\n".join(prompt_parts)

        # Get LLM and generate response
        llm = get_llm()
        llm_info = get_llm_info()

        if llm and llm_info.get("available"):
            response = llm.invoke(full_prompt)

            # Extract response content
            if hasattr(response, 'content'):
                ai_response = response.content
            else:
                ai_response = str(response)

            # Generate suggestions based on query
            suggestions = _generate_suggestions(query, context)

            # Build metadata
            metadata = {
                "model": llm_info.get("model_name", "unknown"),
                "provider": llm_info.get("provider", "unknown"),
                "tokensUsed": len(full_prompt.split()) + len(ai_response.split()),  # Rough estimate
            }

            return ai_response, suggestions, metadata
        else:
            # Fallback response if LLM not available
            ai_response = "I'm currently unable to process your request. Please try again later or contact support."
            suggestions = ["Check system status", "Contact IT support"]
            metadata = {
                "model": "fallback",
                "provider": "none",
                "tokensUsed": 0
            }

            return ai_response, suggestions, metadata

    except Exception as e:
        logger.error(f"Error generating AI response: {e}", exc_info=True)
        # Return error response
        return (
            "I encountered an error processing your request. Please try again.",
            ["Try rephrasing your question", "Contact support"],
            {"model": "error", "provider": "none", "tokensUsed": 0}
        )


def _generate_suggestions(query: str, context: Optional[any]) -> List[str]:
    """
    Generate contextual suggestions based on the query.
    """
    query_lower = query.lower()
    suggestions = []

    # IT Support suggestions
    if any(word in query_lower for word in ["password", "reset", "unlock", "account"]):
        suggestions.extend([
            "Reset password for specific user",
            "Unlock user account",
            "Check password policy"
        ])
    elif any(word in query_lower for word in ["active directory", "ad", "user"]):
        suggestions.extend([
            "Search for user in AD",
            "View user properties",
            "Check group memberships"
        ])
    elif any(word in query_lower for word in ["group", "permission", "access"]):
        suggestions.extend([
            "Add user to group",
            "Check group permissions",
            "Review access rights"
        ])
    else:
        # Generic suggestions
        suggestions.extend([
            "Ask a follow-up question",
            "Search knowledge base",
            "View related documentation"
        ])

    return suggestions[:3]  # Return max 3 suggestions

