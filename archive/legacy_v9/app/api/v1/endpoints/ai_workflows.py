"""
Production-Ready AI Workflows API Endpoints
Comprehensive endpoints for advanced AI workflows with authentication, rate limiting, and error handling.
"""

import asyncio
import time
import uuid
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Request, BackgroundTasks
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field, validator
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging_config import get_logger
from app.core.security import get_current_user, check_rate_limit, sanitize_input
from app.core.monitoring import metrics_collector
from app.database.database import get_db
from app.database.models import User
from app.core.prompt_engineering import prompt_engine, ReasoningType
from app.core.conversation_context import conversation_manager
from app.core.advanced_workflows import AdvancedWorkflowEngine
from app.core.multi_agent import multi_agent_orchestrator
from app.core.rag_system import rag_system

logger = get_logger(__name__)
router = APIRouter()
security = HTTPBearer()

# Request/Response Models
class ChainOfThoughtRequest(BaseModel):
    """Request model for chain-of-thought reasoning."""
    query: str = Field(..., min_length=1, max_length=2000, description="The query to analyze")
    reasoning_type: ReasoningType = Field(default=ReasoningType.CHAIN_OF_THOUGHT, description="Type of reasoning to apply")
    context: Optional[str] = Field(None, max_length=5000, description="Additional context for reasoning")
    max_steps: int = Field(default=5, ge=1, le=10, description="Maximum reasoning steps")
    conversation_id: Optional[str] = Field(None, description="Conversation ID for context")

class ChainOfThoughtResponse(BaseModel):
    """Response model for chain-of-thought reasoning."""
    query: str
    reasoning_type: str
    steps: List[Dict[str, Any]]
    final_answer: str
    confidence_score: float
    execution_time: float
    conversation_id: Optional[str]
    metadata: Dict[str, Any]

class AdvancedRAGRequest(BaseModel):
    """Request model for advanced RAG queries."""
    query: str = Field(..., min_length=1, max_length=2000, description="The query to process")
    search_limit: int = Field(default=5, ge=1, le=20, description="Number of documents to retrieve")
    score_threshold: float = Field(default=0.7, ge=0.0, le=1.0, description="Minimum relevance score")
    use_multi_agent: bool = Field(default=False, description="Use multi-agent processing")
    conversation_id: Optional[str] = Field(None, description="Conversation ID for context")
    include_reasoning: bool = Field(default=True, description="Include reasoning steps")

class AdvancedRAGResponse(BaseModel):
    """Response model for advanced RAG queries."""
    query: str
    response: str
    retrieved_documents: List[Dict[str, Any]]
    context_used: bool
    reasoning_steps: Optional[List[Dict[str, Any]]]
    confidence_score: float
    execution_time: float
    conversation_id: Optional[str]
    metadata: Dict[str, Any]

class WorkflowExecutionRequest(BaseModel):
    """Request model for workflow execution."""
    template_name: str = Field(..., description="Workflow template to use")
    inputs: Dict[str, Any] = Field(..., description="Input parameters for the workflow")
    conversation_id: Optional[str] = Field(None, description="Conversation ID for context")
    async_execution: bool = Field(default=False, description="Execute workflow asynchronously")

class WorkflowExecutionResponse(BaseModel):
    """Response model for workflow execution."""
    workflow_id: str
    status: str
    results: Optional[Dict[str, Any]]
    execution_time: Optional[float]
    conversation_id: Optional[str]
    metadata: Dict[str, Any]

class ConversationContextRequest(BaseModel):
    """Request model for conversation context operations."""
    conversation_id: Optional[str] = Field(None, description="Conversation ID")
    message: str = Field(..., min_length=1, max_length=2000, description="Message content")
    role: str = Field(default="user", description="Message role (user/assistant)")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")

class ConversationContextResponse(BaseModel):
    """Response model for conversation context operations."""
    conversation_id: str
    turn_id: str
    contextual_prompt: str
    user_preferences: Dict[str, Any]
    key_topics: List[str]
    analytics: Dict[str, Any]

# Rate limiting decorator
async def rate_limit_check(request: Request, current_user: User = Depends(get_current_user)):
    """Check rate limits for AI workflow endpoints."""
    client_id = f"user_{current_user.id}" if current_user else request.client.host
    
    # Different rate limits for different endpoints
    endpoint = request.url.path
    if "chain-of-thought" in endpoint:
        limit = await check_rate_limit(client_id, "cot_reasoning", max_requests=10, window_seconds=60)
    elif "rag" in endpoint:
        limit = await check_rate_limit(client_id, "rag_queries", max_requests=20, window_seconds=60)
    elif "workflow" in endpoint:
        limit = await check_rate_limit(client_id, "workflow_execution", max_requests=5, window_seconds=60)
    else:
        limit = await check_rate_limit(client_id, "general_ai", max_requests=30, window_seconds=60)
    
    if not limit:
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded. Please try again later.",
            headers={"Retry-After": "60"}
        )
    
    return current_user

@router.post("/chain-of-thought", response_model=ChainOfThoughtResponse)
async def execute_chain_of_thought_reasoning(
    request: ChainOfThoughtRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(rate_limit_check),
    db: AsyncSession = Depends(get_db)
):
    """
    Execute sophisticated chain-of-thought reasoning on a query.
    
    This endpoint provides advanced reasoning capabilities with multiple reasoning types,
    context awareness, and detailed step-by-step analysis.
    """
    start_time = time.time()
    
    try:
        # Sanitize input
        sanitized_query = sanitize_input(request.query)
        sanitized_context = sanitize_input(request.context) if request.context else None
        
        # Get conversation context if provided
        conversation_context = None
        if request.conversation_id:
            conversation_context = await conversation_manager.get_conversation_context(request.conversation_id)
            if conversation_context:
                # Enhance query with conversation context
                contextual_prompt = await conversation_manager.get_contextual_prompt(
                    request.conversation_id,
                    sanitized_query,
                    include_reasoning=True
                )
                sanitized_query = contextual_prompt
        
        # Execute chain-of-thought reasoning
        cot_result = await prompt_engine.generate_chain_of_thought_response(
            query=sanitized_query,
            reasoning_type=request.reasoning_type,
            context=sanitized_context,
            max_steps=request.max_steps
        )
        
        # Add result to conversation if conversation_id provided
        if request.conversation_id:
            await conversation_manager.add_turn(
                conversation_id=request.conversation_id,
                role="assistant",
                content=cot_result.final_answer,
                metadata={"reasoning_type": cot_result.reasoning_type.value},
                reasoning_steps=[{"step": i+1, "reasoning": step.reasoning} for i, step in enumerate(cot_result.steps)]
            )
        
        # Record metrics
        execution_time = time.time() - start_time
        background_tasks.add_task(
            metrics_collector.record_histogram,
            "ai_workflows.chain_of_thought.execution_time",
            execution_time
        )
        background_tasks.add_task(
            metrics_collector.record_counter,
            "ai_workflows.chain_of_thought.requests"
        )
        
        return ChainOfThoughtResponse(
            query=request.query,
            reasoning_type=cot_result.reasoning_type.value,
            steps=[{
                "step_number": step.step_number,
                "description": step.description,
                "reasoning": step.reasoning,
                "confidence": step.confidence
            } for step in cot_result.steps],
            final_answer=cot_result.final_answer,
            confidence_score=cot_result.confidence_score,
            execution_time=execution_time,
            conversation_id=request.conversation_id,
            metadata={
                "user_id": current_user.id,
                "reasoning_type": cot_result.reasoning_type.value,
                "steps_generated": len(cot_result.steps),
                "context_provided": sanitized_context is not None
            }
        )
        
    except Exception as e:
        logger.error(f"Chain-of-thought reasoning failed: {e}")
        background_tasks.add_task(
            metrics_collector.record_counter,
            "ai_workflows.chain_of_thought.errors"
        )
        raise HTTPException(
            status_code=500,
            detail=f"Chain-of-thought reasoning failed: {str(e)}"
        )

@router.post("/rag/advanced", response_model=AdvancedRAGResponse)
async def execute_advanced_rag_query(
    request: AdvancedRAGRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(rate_limit_check),
    db: AsyncSession = Depends(get_db)
):
    """
    Execute advanced RAG (Retrieval-Augmented Generation) queries.
    
    This endpoint combines document retrieval with sophisticated LLM generation,
    supporting multi-agent processing and conversation context.
    """
    start_time = time.time()
    
    try:
        # Sanitize input
        sanitized_query = sanitize_input(request.query)
        
        # Execute RAG query
        rag_result = await rag_system.retrieve_and_generate(
            db=db,
            query=sanitized_query,
            search_limit=request.search_limit,
            score_threshold=request.score_threshold,
            use_multi_agent=request.use_multi_agent,
            conversation_id=request.conversation_id
        )
        
        # Add reasoning steps if requested
        reasoning_steps = None
        if request.include_reasoning and request.use_multi_agent:
            # Get reasoning from multi-agent system
            reasoning_steps = [
                {"step": 1, "description": "Document retrieval", "reasoning": f"Retrieved {len(rag_result.get('retrieved_documents', []))} relevant documents"},
                {"step": 2, "description": "Context analysis", "reasoning": "Analyzed document relevance and context"},
                {"step": 3, "description": "Response generation", "reasoning": "Generated contextual response using retrieved information"}
            ]
        
        # Add to conversation if conversation_id provided
        if request.conversation_id:
            await conversation_manager.add_turn(
                conversation_id=request.conversation_id,
                role="assistant",
                content=rag_result.get("response", ""),
                metadata={"rag_query": True, "documents_used": len(rag_result.get("retrieved_documents", []))},
                reasoning_steps=reasoning_steps
            )
        
        # Record metrics
        execution_time = time.time() - start_time
        background_tasks.add_task(
            metrics_collector.record_histogram,
            "ai_workflows.rag.execution_time",
            execution_time
        )
        background_tasks.add_task(
            metrics_collector.record_counter,
            "ai_workflows.rag.requests"
        )
        
        return AdvancedRAGResponse(
            query=request.query,
            response=rag_result.get("response", ""),
            retrieved_documents=rag_result.get("retrieved_documents", []),
            context_used=rag_result.get("context_used", False),
            reasoning_steps=reasoning_steps,
            confidence_score=rag_result.get("confidence_score", 0.8),
            execution_time=execution_time,
            conversation_id=request.conversation_id,
            metadata={
                "user_id": current_user.id,
                "documents_retrieved": len(rag_result.get("retrieved_documents", [])),
                "multi_agent_used": request.use_multi_agent,
                "search_threshold": request.score_threshold
            }
        )
        
    except Exception as e:
        logger.error(f"Advanced RAG query failed: {e}")
        background_tasks.add_task(
            metrics_collector.record_counter,
            "ai_workflows.rag.errors"
        )
        raise HTTPException(
            status_code=500,
            detail=f"Advanced RAG query failed: {str(e)}"
        )

@router.post("/workflow/execute", response_model=WorkflowExecutionResponse)
async def execute_advanced_workflow(
    request: WorkflowExecutionRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(rate_limit_check),
    db: AsyncSession = Depends(get_db)
):
    """
    Execute advanced multi-step AI workflows.
    
    This endpoint orchestrates complex workflows with multiple AI agents,
    supporting both synchronous and asynchronous execution.
    """
    start_time = time.time()
    
    try:
        # Initialize workflow engine
        workflow_engine = AdvancedWorkflowEngine()
        
        # Sanitize inputs
        sanitized_inputs = {}
        for key, value in request.inputs.items():
            if isinstance(value, str):
                sanitized_inputs[key] = sanitize_input(value)
            else:
                sanitized_inputs[key] = value
        
        # Create workflow from template
        workflow_id = await workflow_engine.create_workflow_from_template(
            template_name=request.template_name,
            inputs=sanitized_inputs
        )
        
        if request.async_execution:
            # Execute asynchronously
            background_tasks.add_task(
                workflow_engine.execute_workflow,
                workflow_id
            )
            
            execution_time = time.time() - start_time
            
            return WorkflowExecutionResponse(
                workflow_id=workflow_id,
                status="running",
                results=None,
                execution_time=execution_time,
                conversation_id=request.conversation_id,
                metadata={
                    "user_id": current_user.id,
                    "template_name": request.template_name,
                    "async_execution": True,
                    "inputs_count": len(sanitized_inputs)
                }
            )
        else:
            # Execute synchronously
            results = await workflow_engine.execute_workflow(workflow_id)
            execution_time = time.time() - start_time
            
            # Record metrics
            background_tasks.add_task(
                metrics_collector.record_histogram,
                "ai_workflows.workflow.execution_time",
                execution_time
            )
            background_tasks.add_task(
                metrics_collector.record_counter,
                "ai_workflows.workflow.requests"
            )
            
            return WorkflowExecutionResponse(
                workflow_id=workflow_id,
                status="completed",
                results=results,
                execution_time=execution_time,
                conversation_id=request.conversation_id,
                metadata={
                    "user_id": current_user.id,
                    "template_name": request.template_name,
                    "async_execution": False,
                    "inputs_count": len(sanitized_inputs),
                    "tasks_completed": len(results.get("task_results", {}))
                }
            )
        
    except Exception as e:
        logger.error(f"Workflow execution failed: {e}")
        background_tasks.add_task(
            metrics_collector.record_counter,
            "ai_workflows.workflow.errors"
        )
        raise HTTPException(
            status_code=500,
            detail=f"Workflow execution failed: {str(e)}"
        )

@router.post("/conversation/context", response_model=ConversationContextResponse)
async def manage_conversation_context(
    request: ConversationContextRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(rate_limit_check),
    db: AsyncSession = Depends(get_db)
):
    """
    Manage conversation context with intelligent memory and analytics.

    This endpoint provides context-aware conversation management with
    user preference extraction and conversation analytics.
    """
    try:
        # Sanitize input
        sanitized_message = sanitize_input(request.message)

        # Create or get conversation
        conversation_id = request.conversation_id
        if not conversation_id:
            conversation_id = await conversation_manager.create_conversation(
                initial_context={
                    "user_id": current_user.id,
                    "metadata": request.metadata or {}
                }
            )

        # Add turn to conversation
        turn = await conversation_manager.add_turn(
            conversation_id=conversation_id,
            role=request.role,
            content=sanitized_message,
            metadata=request.metadata
        )

        # Generate contextual prompt
        contextual_prompt = await conversation_manager.get_contextual_prompt(
            conversation_id=conversation_id,
            current_query="",
            include_reasoning=True
        )

        # Extract user preferences
        user_preferences = await conversation_manager.extract_user_preferences(conversation_id)

        # Get conversation analytics
        analytics = await conversation_manager.get_conversation_analytics(conversation_id)

        # Record metrics
        background_tasks.add_task(
            metrics_collector.record_counter,
            "ai_workflows.conversation.context_updates"
        )

        return ConversationContextResponse(
            conversation_id=conversation_id,
            turn_id=turn.turn_id,
            contextual_prompt=contextual_prompt,
            user_preferences=user_preferences,
            key_topics=analytics.get("key_topics", []),
            analytics={
                "total_turns": analytics.get("total_turns", 0),
                "duration_hours": analytics.get("duration_hours", 0),
                "avg_message_length": analytics.get("avg_user_message_length", 0)
            }
        )

    except Exception as e:
        logger.error(f"Conversation context management failed: {e}")
        background_tasks.add_task(
            metrics_collector.record_counter,
            "ai_workflows.conversation.errors"
        )
        raise HTTPException(
            status_code=500,
            detail=f"Conversation context management failed: {str(e)}"
        )

@router.get("/workflow/{workflow_id}/status")
async def get_workflow_status(
    workflow_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get the status of a running workflow."""
    try:
        workflow_engine = AdvancedWorkflowEngine()
        status = workflow_engine.get_workflow_status(workflow_id)

        if "error" in status:
            raise HTTPException(status_code=404, detail="Workflow not found")

        return status

    except Exception as e:
        logger.error(f"Failed to get workflow status: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get workflow status: {str(e)}"
        )

@router.get("/conversation/{conversation_id}/analytics")
async def get_conversation_analytics(
    conversation_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get detailed analytics for a conversation."""
    try:
        analytics = await conversation_manager.get_conversation_analytics(conversation_id)

        if not analytics:
            raise HTTPException(status_code=404, detail="Conversation not found")

        return analytics

    except Exception as e:
        logger.error(f"Failed to get conversation analytics: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get conversation analytics: {str(e)}"
        )

@router.get("/capabilities")
async def get_ai_workflow_capabilities():
    """Get available AI workflow capabilities and features."""
    try:
        return {
            "chain_of_thought": {
                "available": True,
                "reasoning_types": [rt.value for rt in ReasoningType],
                "max_steps": 10,
                "features": ["context_awareness", "conversation_integration", "step_by_step_analysis"]
            },
            "advanced_rag": {
                "available": True,
                "max_documents": 20,
                "min_score_threshold": 0.0,
                "features": ["multi_agent_processing", "conversation_context", "document_ranking"]
            },
            "workflows": {
                "available": True,
                "templates": ["research_and_analysis", "content_generation", "decision_making"],
                "execution_modes": ["synchronous", "asynchronous"],
                "features": ["multi_step_orchestration", "parallel_processing", "conditional_logic"]
            },
            "conversation_management": {
                "available": True,
                "features": ["context_tracking", "preference_extraction", "analytics", "memory_management"]
            },
            "rate_limits": {
                "chain_of_thought": "10 requests/minute",
                "rag_queries": "20 requests/minute",
                "workflow_execution": "5 requests/minute",
                "general_ai": "30 requests/minute"
            }
        }

    except Exception as e:
        logger.error(f"Failed to get AI workflow capabilities: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get AI workflow capabilities: {str(e)}"
        )
