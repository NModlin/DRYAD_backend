# app/services/chat_history.py
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, and_
from sqlalchemy.orm import selectinload
import json
import uuid
from datetime import datetime

from app.database.models import Conversation, Message
from app.database.database import AsyncSessionLocal


class ChatHistoryService:
    """Service for managing chat conversations and messages."""

    @staticmethod
    async def create_conversation(
        db: AsyncSession,
        title: Optional[str] = None,
        initial_message: Optional[str] = None
    ) -> Conversation:
        """Create a new conversation."""
        conversation = Conversation(
            id=str(uuid.uuid4()),
            title=title or "New Conversation",
            is_active=True
        )
        
        db.add(conversation)
        await db.flush()  # Get the ID without committing
        
        # Add initial message if provided
        if initial_message:
            await ChatHistoryService.add_message(
                db=db,
                conversation_id=conversation.id,
                role="user",
                content=initial_message
            )
        
        await db.commit()
        await db.refresh(conversation)

        # Create a detached copy to avoid session issues
        from app.database.models import Conversation as ConversationModel
        detached_conversation = ConversationModel(
            id=conversation.id,
            title=conversation.title,
            created_at=conversation.created_at,
            updated_at=conversation.updated_at,
            is_active=conversation.is_active
        )
        return detached_conversation

    @staticmethod
    async def get_conversation(
        db: AsyncSession,
        conversation_id: str,
        include_messages: bool = True,
        active_only: bool = True
    ) -> Optional[Conversation]:
        """Get a conversation by ID."""
        query = select(Conversation).where(Conversation.id == conversation_id)

        if active_only:
            query = query.where(Conversation.is_active == True)

        if include_messages:
            query = query.options(selectinload(Conversation.messages))

        result = await db.execute(query)
        conversation = result.scalar_one_or_none()

        if not conversation:
            return None

        # For internal use (like checking existence), return the attached object
        # For external use (endpoints), we'll create detached copies in the endpoint methods
        return conversation

    @staticmethod
    async def get_conversation_detached(
        db: AsyncSession,
        conversation_id: str,
        include_messages: bool = True
    ) -> Optional[Conversation]:
        """Get a conversation by ID as a detached object for API responses."""
        conversation = await ChatHistoryService.get_conversation(
            db, conversation_id, include_messages, active_only=True
        )

        if not conversation:
            return None

        # Create a detached copy to avoid session issues
        from app.database.models import Conversation as ConversationModel, Message as MessageModel
        detached_conversation = ConversationModel(
            id=conversation.id,
            title=conversation.title,
            created_at=conversation.created_at,
            updated_at=conversation.updated_at,
            is_active=conversation.is_active
        )

        # If messages are included, create detached message copies
        if include_messages and hasattr(conversation, 'messages') and conversation.messages:
            detached_messages = []
            for msg in conversation.messages:
                # Deserialize JSON fields
                tool_calls_data = None
                if msg.tool_calls:
                    try:
                        tool_calls_data = json.loads(msg.tool_calls)
                    except json.JSONDecodeError:
                        tool_calls_data = msg.tool_calls

                extra_data_dict = None
                if msg.extra_data:
                    try:
                        extra_data_dict = json.loads(msg.extra_data)
                    except json.JSONDecodeError:
                        extra_data_dict = msg.extra_data

                detached_msg = MessageModel(
                    id=msg.id,
                    conversation_id=msg.conversation_id,
                    role=msg.role,
                    content=msg.content,
                    tool_calls=tool_calls_data,
                    extra_data=extra_data_dict,
                    created_at=msg.created_at
                )
                detached_messages.append(detached_msg)
            detached_conversation.messages = detached_messages

        return detached_conversation

    @staticmethod
    async def get_conversations(
        db: AsyncSession,
        limit: int = 50,
        offset: int = 0,
        active_only: bool = True
    ) -> List[Conversation]:
        """Get a list of conversations."""
        query = select(Conversation)

        if active_only:
            query = query.where(Conversation.is_active == True)

        query = query.order_by(desc(Conversation.updated_at)).limit(limit).offset(offset)

        result = await db.execute(query)
        conversations = list(result.scalars().all())

        # Create detached copies to avoid session issues
        from app.database.models import Conversation as ConversationModel
        detached_conversations = []
        for conv in conversations:
            detached_conv = ConversationModel(
                id=conv.id,
                title=conv.title,
                created_at=conv.created_at,
                updated_at=conv.updated_at,
                is_active=conv.is_active
            )
            detached_conversations.append(detached_conv)

        return detached_conversations

    @staticmethod
    async def update_conversation(
        db: AsyncSession,
        conversation_id: str,
        title: Optional[str] = None,
        is_active: Optional[bool] = None
    ) -> Optional[Conversation]:
        """Update a conversation."""
        conversation = await ChatHistoryService.get_conversation(
            db, conversation_id, include_messages=False, active_only=True
        )

        if not conversation:
            return None

        if title is not None:
            conversation.title = title

        if is_active is not None:
            conversation.is_active = is_active

        await db.commit()
        await db.refresh(conversation)

        # Create a detached copy to avoid session issues
        from app.database.models import Conversation as ConversationModel
        detached_conversation = ConversationModel(
            id=conversation.id,
            title=conversation.title,
            created_at=conversation.created_at,
            updated_at=conversation.updated_at,
            is_active=conversation.is_active
        )
        return detached_conversation

    @staticmethod
    async def delete_conversation(
        db: AsyncSession,
        conversation_id: str,
        soft_delete: bool = True
    ) -> bool:
        """Delete a conversation (soft delete by default)."""
        conversation = await ChatHistoryService.get_conversation(
            db, conversation_id, include_messages=False, active_only=False
        )
        
        if not conversation:
            return False
        
        if soft_delete:
            conversation.is_active = False
            await db.commit()
        else:
            await db.delete(conversation)
            await db.commit()
        
        return True

    @staticmethod
    async def add_message(
        db: AsyncSession,
        conversation_id: str,
        role: str,
        content: str,
        tool_calls: Optional[Dict[str, Any]] = None,
        extra_data: Optional[Dict[str, Any]] = None
    ) -> Optional[Message]:
        """Add a message to a conversation."""
        # Verify conversation exists
        conversation = await ChatHistoryService.get_conversation(
            db, conversation_id, include_messages=False, active_only=True
        )
        
        if not conversation:
            return None
        
        message = Message(
            id=str(uuid.uuid4()),
            conversation_id=conversation_id,
            role=role,
            content=content,
            tool_calls=json.dumps(tool_calls) if tool_calls else None,
            extra_data=json.dumps(extra_data) if extra_data else None
        )
        
        db.add(message)
        
        # Update conversation's updated_at timestamp
        conversation.updated_at = datetime.utcnow()
        
        await db.commit()
        await db.refresh(message)

        # Create a detached copy to avoid session issues with deserialized JSON fields
        from app.database.models import Message as MessageModel

        tool_calls_data = None
        if message.tool_calls:
            try:
                tool_calls_data = json.loads(message.tool_calls)
            except json.JSONDecodeError:
                tool_calls_data = message.tool_calls

        extra_data_dict = None
        if message.extra_data:
            try:
                extra_data_dict = json.loads(message.extra_data)
            except json.JSONDecodeError:
                extra_data_dict = message.extra_data

        detached_message = MessageModel(
            id=message.id,
            conversation_id=message.conversation_id,
            role=message.role,
            content=message.content,
            tool_calls=tool_calls_data,
            extra_data=extra_data_dict,
            created_at=message.created_at
        )
        return detached_message

    @staticmethod
    async def get_messages(
        db: AsyncSession,
        conversation_id: str,
        limit: int = 100,
        offset: int = 0
    ) -> List[Message]:
        """Get messages for a conversation with properly deserialized JSON fields."""
        query = (
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.created_at)
            .limit(limit)
            .offset(offset)
        )

        result = await db.execute(query)
        raw_messages = list(result.scalars().all())

        # Create detached copies with deserialized JSON fields
        from app.database.models import Message as MessageModel
        detached_messages = []

        for msg in raw_messages:
            # Deserialize JSON fields
            tool_calls_data = None
            if msg.tool_calls:
                try:
                    tool_calls_data = json.loads(msg.tool_calls)
                except json.JSONDecodeError:
                    tool_calls_data = msg.tool_calls

            extra_data_dict = None
            if msg.extra_data:
                try:
                    extra_data_dict = json.loads(msg.extra_data)
                except json.JSONDecodeError:
                    extra_data_dict = msg.extra_data

            detached_msg = MessageModel(
                id=msg.id,
                conversation_id=msg.conversation_id,
                role=msg.role,
                content=msg.content,
                tool_calls=tool_calls_data,
                extra_data=extra_data_dict,
                created_at=msg.created_at
            )
            detached_messages.append(detached_msg)

        return detached_messages

    @staticmethod
    async def get_conversation_context(
        db: AsyncSession,
        conversation_id: str,
        max_messages: int = 20
    ) -> List[Dict[str, Any]]:
        """Get conversation context for AI agents."""
        messages = await ChatHistoryService.get_messages(
            db, conversation_id, limit=max_messages
        )
        
        context = []
        for message in messages:
            msg_dict = {
                "role": message.role,
                "content": message.content,
                "created_at": message.created_at.isoformat()
            }
            
            if message.tool_calls:
                # tool_calls is already deserialized by get_messages()
                msg_dict["tool_calls"] = message.tool_calls

            if message.extra_data:
                # extra_data is already deserialized by get_messages()
                msg_dict["extra_data"] = message.extra_data
            
            context.append(msg_dict)
        
        return context
