# app/api/v1/endpoints/agent.py
import logging
import html
import re
from fastapi import APIRouter, Depends, HTTPException, Query, Response
from app.core.security import get_current_user, User
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.core.agent import agent_graph_app
from app.core.multi_agent import multi_agent_orchestrator
from app.database.database import get_db
from app.services.chat_history import ChatHistoryService
from app.services.agent_memory import AgentMemoryService
from app.api.v1.schemas.chat_history import AgentConversationRequest, AgentConversationResponse
from app.api.v1.schemas.multi_agent import LegacyAgentRequest, LegacyAgentResponse
from langchain_core.messages import HumanMessage, AIMessage
from app.core.exceptions import (
    AgentProcessingException,
    ValidationException,
    ValidationErrorDetail,
    ExternalServiceException
)

logger = logging.getLogger(__name__)

router = APIRouter()

@router.options("/chat")
async def chat_options():
    """Handle OPTIONS request for CORS preflight."""
    from app.core.security import get_cors_headers

    response = Response(status_code=200)
    cors_headers = get_cors_headers()

    for header, value in cors_headers.items():
        response.headers[header] = value

    return response

def sanitize_input(text: str) -> str:
    """Sanitize user input to prevent XSS and other injection attacks."""
    if not text:
        return text

    # Remove potentially dangerous HTML/JavaScript patterns
    dangerous_patterns = [
        r'<script[^>]*>.*?</script>',
        r'javascript:',
        r'on\w+\s*=',
        r'<iframe[^>]*>.*?</iframe>',
        r'<object[^>]*>.*?</object>',
        r'<embed[^>]*>.*?</embed>',
        r'<link[^>]*>',
        r'<meta[^>]*>',
        r'<style[^>]*>.*?</style>'
    ]

    sanitized = text
    for pattern in dangerous_patterns:
        sanitized = re.sub(pattern, '', sanitized, flags=re.IGNORECASE | re.DOTALL)

    # HTML escape remaining content
    sanitized = html.escape(sanitized)

    return sanitized

# Keep the original simple endpoint for backward compatibility
@router.post("/invoke")
async def invoke_agent_simple(request: dict, current_user: User = Depends(get_current_user)):
    """Simple agent invocation (backward compatibility)."""
    import time
    start_time = time.time()

    try:
        input_text = request.get("input", "")

        # Validate input
        if not input_text or not input_text.strip():
            raise ValidationException(
                error_message="Input text is required",
                validation_errors=[ValidationErrorDetail(
                    field="input",
                    message="Input text cannot be empty",
                    invalid_value=input_text,
                    expected_type="non-empty string"
                )]
            )

        # Sanitize input to prevent XSS and injection attacks
        sanitized_input = sanitize_input(input_text)

        human_message = HumanMessage(content=sanitized_input)
        inputs = {"messages": [human_message]}

        try:
            final_state = {}
            for s in agent_graph_app.stream(inputs):
                final_state.update(s)

            logger.info(f"Agent final_state: {final_state}")

            # Extract simple string output from agent response
            output_text = ""

            # Check if data is nested under 'agent' key
            agent_data = final_state.get('agent', final_state)

            if "agent_outcome" in agent_data:
                outcome = agent_data["agent_outcome"]
                logger.info(f"Agent outcome type: {type(outcome)}, value: {outcome}")
                # Handle AgentFinish object
                if hasattr(outcome, 'return_values') and isinstance(outcome.return_values, dict):
                    output_text = outcome.return_values.get('output', '')
                    logger.info(f"Extracted from AgentFinish: {output_text}")
                # Handle dict format
                elif isinstance(outcome, dict) and 'return_values' in outcome:
                    output_text = outcome['return_values'].get('output', '')
                    logger.info(f"Extracted from dict: {output_text}")

            # Also check for messages in agent_data
            if not output_text and "messages" in agent_data:
                messages = agent_data["messages"]
                logger.info(f"Checking messages: {messages}")
                if messages and len(messages) > 0:
                    last_message = messages[-1]
                    if hasattr(last_message, 'content'):
                        output_text = last_message.content
                        logger.info(f"Extracted from message: {output_text}")

            if not output_text:
                output_text = "No response generated"
                logger.warning(f"No output text found in agent response. Final state: {final_state}")

            # Sanitize output to prevent XSS in responses
            sanitized_output = sanitize_input(output_text)

            execution_time = time.time() - start_time
            return {
                "output": sanitized_output,
                "execution_time": execution_time
            }

        except Exception as e:
            logger.error(f"Agent processing failed: {e}")
            raise AgentProcessingException(
                error_message="Agent processing failed",
                error_details=str(e),
                processing_step="agent_execution"
            )

    except (ValidationException, AgentProcessingException):
        raise
    except Exception as e:
        logger.error(f"Unexpected error in agent endpoint: {e}")
        raise AgentProcessingException(
            error_message="Unexpected error in agent processing",
            error_details=str(e),
            processing_step="endpoint_handling"
        )


@router.post("/chat", response_model=AgentConversationResponse)
async def invoke_agent_with_conversation(
    request: AgentConversationRequest,
    use_multi_agent: bool = Query(False, description="Use multi-agent system for enhanced reasoning"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Invoke agent with conversation context and history management."""
    import time
    start_time = time.time()

    try:
        conversation_id = request.conversation_id
        context_used = False

        # Handle conversation management only if saving is enabled
        if request.save_conversation:
            if conversation_id:
                conversation = await ChatHistoryService.get_conversation(
                    db=db,
                    conversation_id=conversation_id,
                    include_messages=False
                )
                if not conversation:
                    raise HTTPException(status_code=404, detail="Conversation not found")
            else:
                # Create new conversation
                conversation = await ChatHistoryService.create_conversation(
                    db=db,
                    title=f"Chat: {request.input[:50]}...",
                    initial_message=None  # We'll add the message separately
                )
                conversation_id = conversation.id
        else:
            # Don't create conversation if not saving
            conversation_id = None

        # Add user message to conversation if saving is enabled
        user_message = None
        if request.save_conversation:
            user_message = await ChatHistoryService.add_message(
                db=db,
                conversation_id=conversation_id,
                role="user",
                content=request.input
            )

        # Choose between single-agent and multi-agent processing
        if use_multi_agent:
            # Use multi-agent system for enhanced reasoning
            logger.info(f"Using multi-agent system for query: {request.input}")

            # Create context-aware prompt
            context_prompt = await AgentMemoryService.create_agent_context_prompt(
                db=db,
                conversation_id=conversation_id,
                current_query=request.input
            ) if conversation_id else request.input

            # Execute simple multi-agent workflow
            multi_result = multi_agent_orchestrator.execute_simple_query(
                query=context_prompt,
                context=""
            )

            agent_response = str(multi_result.get("result", ""))
            # Create a simple dict structure instead of a dynamic object
            final_state = {
                "multi_agent_result": multi_result,
                "agent_outcome": {
                    'return_values': {'output': agent_response}
                }
            }
            context_used = True

        else:
            # Use original single-agent system
            context_messages = []
            if conversation_id and request.save_conversation:
                context = await ChatHistoryService.get_conversation_context(
                    db=db,
                    conversation_id=conversation_id,
                    max_messages=10  # Limit context to last 10 messages
                )

                if context:
                    context_used = True
                    # Convert context to LangChain messages
                    for ctx_msg in context[:-1]:  # Exclude the message we just added
                        if ctx_msg["role"] == "user":
                            context_messages.append(HumanMessage(content=ctx_msg["content"]))
                        elif ctx_msg["role"] == "assistant":
                            context_messages.append(AIMessage(content=ctx_msg["content"]))

            # Add current user message
            context_messages.append(HumanMessage(content=request.input))

            # Invoke the agent with context
            inputs = {"messages": context_messages}
            final_state = {}
            for s in agent_graph_app.stream(inputs):
                final_state.update(s)

            # Extract agent response
            agent_response = ""

            # Check if data is nested under 'agent' key
            agent_data = final_state.get('agent', final_state)

            if "agent_outcome" in agent_data:
                outcome = agent_data["agent_outcome"]
                # Handle AgentFinish object
                if hasattr(outcome, 'return_values') and isinstance(outcome.return_values, dict):
                    agent_response = outcome.return_values.get('output', '')
                # Handle dict format
                elif isinstance(outcome, dict) and 'return_values' in outcome:
                    agent_response = outcome['return_values'].get('output', '')

            # Also check for messages in agent_data
            if not agent_response and "messages" in agent_data:
                messages = agent_data["messages"]
                if messages and len(messages) > 0:
                    last_message = messages[-1]
                    if hasattr(last_message, 'content'):
                        agent_response = last_message.content

        # Save agent response to conversation if saving is enabled
        response_message = None
        if request.save_conversation and agent_response:
            # Create serializable extra_data
            extra_data = {
                "agent_used": True,
                "execution_time": time.time() - start_time,
                "context_used": context_used
            }

            response_message = await ChatHistoryService.add_message(
                db=db,
                conversation_id=conversation_id,
                role="assistant",
                content=agent_response,
                extra_data=extra_data
            )

        # Extract simple string output from agent response
        output_text = agent_response if agent_response else "No response generated"

        execution_time = time.time() - start_time

        return AgentConversationResponse(
            output=output_text,
            conversation_id=conversation_id,
            message_id=response_message.id if response_message else None,
            context_used=context_used,
            execution_time=execution_time
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent invocation failed: {str(e)}")
