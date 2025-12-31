"""
Agent-related asynchronous tasks for Phase 5.
Handles long-running agent operations and multi-agent workflows.
"""

import asyncio
import logging
import time
from typing import Dict, Any, List, Optional
from app.core.celery_app import task
from app.database.database import AsyncSessionLocal
from app.services.chat_history import ChatHistoryService
from app.core.multi_agent import multi_agent_orchestrator

logger = logging.getLogger(__name__)

@task(bind=True, name="agent_tasks.run_multi_agent_workflow")
def run_multi_agent_workflow_task(self, workflow_type: str, input_data: str, 
                                 conversation_id: Optional[str] = None,
                                 save_conversation: bool = True) -> Dict[str, Any]:
    """
    Asynchronously execute a multi-agent workflow.
    
    Args:
        workflow_type: Type of workflow to execute
        input_data: Input data for the workflow
        conversation_id: Optional conversation ID to continue
        save_conversation: Whether to save the conversation
    
    Returns:
        Dict containing workflow results and metadata
    """
    try:
        # Update task state
        self.update_state(state='PROGRESS', meta={'status': 'Starting multi-agent workflow'})
        
        # Run the workflow asynchronously
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            result = loop.run_until_complete(
                _execute_multi_agent_workflow(
                    workflow_type, input_data, conversation_id, save_conversation
                )
            )
            
            self.update_state(state='SUCCESS', meta={'status': 'Workflow completed successfully'})
            return result
            
        finally:
            loop.close()
            
    except Exception as e:
        logger.error(f"Multi-agent workflow task failed: {str(e)}")
        self.update_state(
            state='FAILURE',
            meta={'status': 'Workflow failed', 'error': str(e)}
        )
        raise

async def _execute_multi_agent_workflow(workflow_type: str, input_data: str,
                                      conversation_id: Optional[str],
                                      save_conversation: bool) -> Dict[str, Any]:
    """Execute the multi-agent workflow asynchronously."""
    
    async with AsyncSessionLocal() as db:
        try:
            # Get conversation context if provided
            context = []
            if conversation_id:
                conversation = await ChatHistoryService.get_conversation(db, conversation_id)
                if conversation:
                    context = [
                        {"role": msg.role, "content": msg.content}
                        for msg in conversation.messages[-10:]  # Last 10 messages
                    ]
            
            # Execute multi-agent workflow
            workflow_result = await multi_agent_orchestrator.execute_workflow(
                workflow_type=workflow_type,
                input_data=input_data,
                context=context
            )
            
            # Save conversation if requested
            if save_conversation:
                if not conversation_id:
                    # Create new conversation
                    conversation = await ChatHistoryService.create_conversation(
                        db=db,
                        title=f"Multi-Agent Workflow: {workflow_type}",
                        initial_message=input_data
                    )
                    conversation_id = conversation.id
                
                # Add workflow result as assistant message
                await ChatHistoryService.add_message(
                    db=db,
                    conversation_id=conversation_id,
                    role="assistant",
                    content=workflow_result.get("result", ""),
                    metadata={
                        "workflow_type": workflow_type,
                        "agents_used": workflow_result.get("agents_used", []),
                        "execution_time": workflow_result.get("execution_time", 0),
                        "task_type": "multi_agent_workflow"
                    }
                )
            
            return {
                "result": workflow_result.get("result", ""),
                "agents_used": workflow_result.get("agents_used", []),
                "execution_time": workflow_result.get("execution_time", 0),
                "conversation_id": conversation_id,
                "workflow_type": workflow_type,
                "status": "completed"
            }
            
        except Exception as e:
            logger.error(f"Multi-agent workflow execution failed: {str(e)}")
            raise

@task(bind=True, name="agent_tasks.run_enhanced_agent_chat")
def run_enhanced_agent_chat_task(self, input_data: str, conversation_id: Optional[str] = None,
                                use_multi_agent: bool = False, use_rag: bool = False,
                                save_conversation: bool = True) -> Dict[str, Any]:
    """
    Asynchronously execute an enhanced agent chat with optional multi-agent and RAG.
    
    Args:
        input_data: User input
        conversation_id: Optional conversation ID
        use_multi_agent: Whether to use multi-agent processing
        use_rag: Whether to use RAG for document context
        save_conversation: Whether to save the conversation
    
    Returns:
        Dict containing chat results and metadata
    """
    try:
        self.update_state(state='PROGRESS', meta={'status': 'Processing enhanced chat'})
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            result = loop.run_until_complete(
                _execute_enhanced_chat(
                    input_data, conversation_id, use_multi_agent, use_rag, save_conversation
                )
            )
            
            self.update_state(state='SUCCESS', meta={'status': 'Chat completed successfully'})
            return result
            
        finally:
            loop.close()
            
    except Exception as e:
        logger.error(f"Enhanced agent chat task failed: {str(e)}")
        self.update_state(
            state='FAILURE',
            meta={'status': 'Chat failed', 'error': str(e)}
        )
        raise

async def _execute_enhanced_chat(input_data: str, conversation_id: Optional[str],
                               use_multi_agent: bool, use_rag: bool,
                               save_conversation: bool) -> Dict[str, Any]:
    """Execute enhanced chat with optional multi-agent and RAG."""
    
    async with AsyncSessionLocal() as db:
        try:
            # Get conversation context
            context = []
            if conversation_id:
                conversation = await ChatHistoryService.get_conversation(db, conversation_id)
                if conversation:
                    context = [
                        {"role": msg.role, "content": msg.content}
                        for msg in conversation.messages[-10:]
                    ]
            
            # Prepare response
            response_data = {
                "input": input_data,
                "conversation_id": conversation_id,
                "context_used": len(context) > 0,
                "multi_agent_used": use_multi_agent,
                "rag_used": use_rag,
                "status": "completed"
            }
            
            # Execute based on configuration
            if use_multi_agent:
                # Use multi-agent processing
                workflow_result = await multi_agent_orchestrator.execute_workflow(
                    workflow_type="enhanced_chat",
                    input_data=input_data,
                    context=context
                )
                response_data["output"] = workflow_result.get("result", "")
                response_data["agents_used"] = workflow_result.get("agents_used", [])
                response_data["execution_time"] = workflow_result.get("execution_time", 0)
            else:
                # Use basic agent processing
                from app.core.agent import agent_graph_app
                
                agent_input = {
                    "input": input_data,
                    "chat_history": context
                }
                
                final_state = {}
                for state in agent_graph_app.stream(agent_input):
                    final_state = state
                
                response_data["output"] = final_state
                response_data["agents_used"] = ["basic_agent"]
                response_data["execution_time"] = 0
            
            # Save conversation if requested
            if save_conversation:
                if not conversation_id:
                    conversation = await ChatHistoryService.create_conversation(
                        db=db,
                        title="Enhanced Agent Chat",
                        initial_message=input_data
                    )
                    conversation_id = conversation.id
                    response_data["conversation_id"] = conversation_id
                
                # Add response as assistant message
                await ChatHistoryService.add_message(
                    db=db,
                    conversation_id=conversation_id,
                    role="assistant",
                    content=str(response_data["output"]),
                    metadata={
                        "multi_agent_used": use_multi_agent,
                        "rag_used": use_rag,
                        "agents_used": response_data.get("agents_used", []),
                        "task_type": "enhanced_chat"
                    }
                )
            
            return response_data
            
        except Exception as e:
            logger.error(f"Enhanced chat execution failed: {str(e)}")
            raise

@task(bind=True, name="agent_tasks.batch_process_conversations")
def batch_process_conversations_task(self, conversation_ids: List[str],
                                   operation: str) -> Dict[str, Any]:
    """
    Batch process multiple conversations asynchronously.
    
    Args:
        conversation_ids: List of conversation IDs to process
        operation: Operation to perform (summarize, analyze, etc.)
    
    Returns:
        Dict containing batch processing results
    """
    try:
        self.update_state(
            state='PROGRESS',
            meta={'status': f'Processing {len(conversation_ids)} conversations'}
        )
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            result = loop.run_until_complete(
                _batch_process_conversations(conversation_ids, operation)
            )
            
            self.update_state(state='SUCCESS', meta={'status': 'Batch processing completed'})
            return result
            
        finally:
            loop.close()
            
    except Exception as e:
        logger.error(f"Batch conversation processing failed: {str(e)}")
        self.update_state(
            state='FAILURE',
            meta={'status': 'Batch processing failed', 'error': str(e)}
        )
        raise

async def _batch_process_conversations(conversation_ids: List[str],
                                     operation: str) -> Dict[str, Any]:
    """Execute batch conversation processing."""
    
    async with AsyncSessionLocal() as db:
        results = []
        
        for conv_id in conversation_ids:
            try:
                conversation = await ChatHistoryService.get_conversation(db, conv_id)
                if not conversation:
                    results.append({
                        "conversation_id": conv_id,
                        "status": "not_found",
                        "result": None
                    })
                    continue
                
                # Process based on operation
                if operation == "summarize":
                    # Create summary of conversation
                    messages = [msg.content for msg in conversation.messages]
                    summary = f"Conversation with {len(messages)} messages"
                    
                    result = {
                        "conversation_id": conv_id,
                        "status": "completed",
                        "result": {
                            "summary": summary,
                            "message_count": len(messages),
                            "title": conversation.title
                        }
                    }
                else:
                    result = {
                        "conversation_id": conv_id,
                        "status": "unsupported_operation",
                        "result": None
                    }
                
                results.append(result)
                
            except Exception as e:
                results.append({
                    "conversation_id": conv_id,
                    "status": "error",
                    "result": str(e)
                })
        
        return {
            "operation": operation,
            "total_processed": len(conversation_ids),
            "results": results,
            "status": "completed"
        }
