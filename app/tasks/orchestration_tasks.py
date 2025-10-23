"""
Orchestration-related asynchronous tasks for Phase 5.
Handles complex workflows that coordinate multiple system components.
"""

import asyncio
import logging
import time
from typing import Dict, Any, List, Optional
from app.core.celery_app import task
from app.database.database import AsyncSessionLocal
from app.services.chat_history import ChatHistoryService
from app.services.document_service import DocumentService
from app.core.multi_agent import multi_agent_orchestrator
from app.core.rag_system import rag_system

logger = logging.getLogger(__name__)

@task(bind=True, name="orchestration_tasks.run_comprehensive_workflow")
def run_comprehensive_workflow_task(self, workflow_config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute a comprehensive workflow that combines multiple system capabilities.
    
    Args:
        workflow_config: Configuration for the workflow including steps and parameters
    
    Returns:
        Dict containing comprehensive workflow results
    """
    try:
        self.update_state(
            state='PROGRESS',
            meta={'status': 'Starting comprehensive workflow'}
        )
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            result = loop.run_until_complete(
                _execute_comprehensive_workflow(workflow_config)
            )
            
            self.update_state(state='SUCCESS', meta={'status': 'Comprehensive workflow completed'})
            return result
            
        finally:
            loop.close()
            
    except Exception as e:
        logger.error(f"Comprehensive workflow failed: {str(e)}")
        self.update_state(
            state='FAILURE',
            meta={'status': 'Workflow failed', 'error': str(e)}
        )
        raise

async def _execute_comprehensive_workflow(workflow_config: Dict[str, Any]) -> Dict[str, Any]:
    """Execute comprehensive workflow asynchronously."""
    
    async with AsyncSessionLocal() as db:
        try:
            start_time = time.time()
            workflow_results = []
            
            # Extract workflow configuration
            steps = workflow_config.get("steps", [])
            input_data = workflow_config.get("input", "")
            conversation_id = workflow_config.get("conversation_id")
            save_conversation = workflow_config.get("save_conversation", True)
            
            # Create conversation if needed
            if save_conversation and not conversation_id:
                conversation = await ChatHistoryService.create_conversation(
                    db=db,
                    title=f"Comprehensive Workflow: {workflow_config.get('name', 'Unnamed')}",
                    initial_message=input_data
                )
                conversation_id = conversation.id
            
            # Execute workflow steps
            current_input = input_data
            
            for i, step in enumerate(steps):
                step_start_time = time.time()
                step_type = step.get("type")
                step_config = step.get("config", {})
                
                logger.info(f"Executing workflow step {i+1}: {step_type}")
                
                if step_type == "document_search":
                    # Perform document search
                    search_results, _ = await DocumentService.semantic_search(
                        db=db,
                        query=current_input,
                        limit=step_config.get("limit", 5),
                        score_threshold=step_config.get("score_threshold", 0.1),
                        search_type=step_config.get("search_type", "chunks")
                    )
                    
                    step_result = {
                        "type": step_type,
                        "results": [
                            {
                                "content": result.content,
                                "score": result.score,
                                "document_title": result.document_title
                            }
                            for result in search_results
                        ],
                        "execution_time": time.time() - step_start_time
                    }
                    
                    # Update input for next step
                    if search_results:
                        current_input = f"Based on the search results: {search_results[0].content}"
                
                elif step_type == "multi_agent_analysis":
                    # Run multi-agent analysis
                    workflow_result = await multi_agent_orchestrator.execute_workflow(
                        workflow_type=step_config.get("workflow_type", "analysis"),
                        input_data=current_input,
                        context=[]
                    )
                    
                    step_result = {
                        "type": step_type,
                        "result": workflow_result.get("result", ""),
                        "agents_used": workflow_result.get("agents_used", []),
                        "execution_time": time.time() - step_start_time
                    }
                    
                    # Update input for next step
                    current_input = workflow_result.get("result", current_input)
                
                elif step_type == "rag_query":
                    # Execute RAG query
                    rag_result = await rag_system.retrieve_and_generate(
                        db=db,
                        query=current_input,
                        search_limit=step_config.get("search_limit", 3),
                        score_threshold=step_config.get("score_threshold", 0.1),
                        use_multi_agent=step_config.get("use_multi_agent", False)
                    )
                    
                    step_result = {
                        "type": step_type,
                        "response": rag_result.get("response", ""),
                        "retrieved_documents": len(rag_result.get("retrieved_documents", [])),
                        "context_used": rag_result.get("context_used", False),
                        "execution_time": time.time() - step_start_time
                    }
                    
                    # Update input for next step
                    current_input = rag_result.get("response", current_input)
                
                elif step_type == "conversation_summary":
                    # Summarize conversation
                    if conversation_id:
                        conversation = await ChatHistoryService.get_conversation(db, conversation_id)
                        if conversation:
                            messages = [msg.content for msg in conversation.messages]
                            summary = f"Conversation summary: {len(messages)} messages exchanged"
                            
                            step_result = {
                                "type": step_type,
                                "summary": summary,
                                "message_count": len(messages),
                                "execution_time": time.time() - step_start_time
                            }
                        else:
                            step_result = {
                                "type": step_type,
                                "error": "Conversation not found",
                                "execution_time": time.time() - step_start_time
                            }
                    else:
                        step_result = {
                            "type": step_type,
                            "error": "No conversation ID provided",
                            "execution_time": time.time() - step_start_time
                        }
                
                else:
                    step_result = {
                        "type": step_type,
                        "error": f"Unknown step type: {step_type}",
                        "execution_time": time.time() - step_start_time
                    }
                
                workflow_results.append(step_result)
            
            # Save final result to conversation
            if save_conversation and conversation_id:
                final_result = workflow_results[-1] if workflow_results else {"result": "No steps executed"}
                
                await ChatHistoryService.add_message(
                    db=db,
                    conversation_id=conversation_id,
                    role="assistant",
                    content=str(final_result),
                    metadata={
                        "workflow_type": "comprehensive",
                        "steps_executed": len(workflow_results),
                        "total_execution_time": time.time() - start_time,
                        "task_type": "comprehensive_workflow"
                    }
                )
            
            return {
                "workflow_name": workflow_config.get("name", "Unnamed"),
                "input": input_data,
                "steps_executed": len(workflow_results),
                "results": workflow_results,
                "conversation_id": conversation_id,
                "total_execution_time": time.time() - start_time,
                "status": "completed"
            }
            
        except Exception as e:
            logger.error(f"Comprehensive workflow execution failed: {str(e)}")
            raise

@task(bind=True, name="orchestration_tasks.system_health_check")
def system_health_check_task(self) -> Dict[str, Any]:
    """
    Perform a comprehensive system health check.
    
    Returns:
        Dict containing system health status
    """
    try:
        self.update_state(state='PROGRESS', meta={'status': 'Performing system health check'})
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            result = loop.run_until_complete(_perform_system_health_check())
            
            self.update_state(state='SUCCESS', meta={'status': 'Health check completed'})
            return result
            
        finally:
            loop.close()
            
    except Exception as e:
        logger.error(f"System health check failed: {str(e)}")
        self.update_state(
            state='FAILURE',
            meta={'status': 'Health check failed', 'error': str(e)}
        )
        raise

async def _perform_system_health_check() -> Dict[str, Any]:
    """Perform comprehensive system health check."""
    
    health_status = {
        "timestamp": time.time(),
        "overall_status": "healthy",
        "components": {}
    }
    
    try:
        # Check database connectivity
        async with AsyncSessionLocal() as db:
            from sqlalchemy import text
            await db.execute(text("SELECT 1"))
            health_status["components"]["database"] = {
                "status": "healthy",
                "message": "Database connection successful"
            }
    except Exception as e:
        health_status["components"]["database"] = {
            "status": "unhealthy",
            "message": f"Database connection failed: {str(e)}"
        }
        health_status["overall_status"] = "degraded"
    
    try:
        # Check vector store
        from app.core.vector_store import vector_store
        vector_info = vector_store.get_collection_info()
        health_status["components"]["vector_store"] = {
            "status": "healthy" if vector_info.get("connected", False) else "degraded",
            "message": f"Vector store connected: {vector_info.get('connected', False)}"
        }
        
        if not vector_info.get("connected", False):
            health_status["overall_status"] = "degraded"
            
    except Exception as e:
        health_status["components"]["vector_store"] = {
            "status": "unhealthy",
            "message": f"Vector store check failed: {str(e)}"
        }
        health_status["overall_status"] = "degraded"
    
    try:
        # Check multi-agent system
        capabilities = multi_agent_orchestrator.get_agent_capabilities()
        agent_count = len(capabilities.get("agents", {}))
        health_status["components"]["multi_agent"] = {
            "status": "healthy" if agent_count >= 4 else "degraded",
            "message": f"Multi-agent system with {agent_count} agents available"
        }
        
        if agent_count < 4:
            health_status["overall_status"] = "degraded"
            
    except Exception as e:
        health_status["components"]["multi_agent"] = {
            "status": "unhealthy",
            "message": f"Multi-agent system check failed: {str(e)}"
        }
        health_status["overall_status"] = "degraded"
    
    try:
        # Check document service
        async with AsyncSessionLocal() as db:
            documents = await DocumentService.list_documents(db, limit=1)
            health_status["components"]["document_service"] = {
                "status": "healthy",
                "message": f"Document service operational, {documents.total} documents available"
            }
    except Exception as e:
        health_status["components"]["document_service"] = {
            "status": "unhealthy",
            "message": f"Document service check failed: {str(e)}"
        }
        health_status["overall_status"] = "degraded"
    
    return health_status

@task(bind=True, name="orchestration_tasks.cleanup_old_data")
def cleanup_old_data_task(self, days_old: int = 30) -> Dict[str, Any]:
    """
    Clean up old data from the system.
    
    Args:
        days_old: Number of days old data should be to be considered for cleanup
    
    Returns:
        Dict containing cleanup results
    """
    try:
        self.update_state(state='PROGRESS', meta={'status': 'Cleaning up old data'})
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            result = loop.run_until_complete(_cleanup_old_data(days_old))
            
            self.update_state(state='SUCCESS', meta={'status': 'Cleanup completed'})
            return result
            
        finally:
            loop.close()
            
    except Exception as e:
        logger.error(f"Data cleanup failed: {str(e)}")
        self.update_state(
            state='FAILURE',
            meta={'status': 'Cleanup failed', 'error': str(e)}
        )
        raise

async def _cleanup_old_data(days_old: int) -> Dict[str, Any]:
    """Clean up old data asynchronously."""
    
    async with AsyncSessionLocal() as db:
        try:
            from datetime import datetime, timedelta
            from app.database.models import SearchQuery
            
            cutoff_date = datetime.utcnow() - timedelta(days=days_old)
            
            # Clean up old search queries
            old_searches = await db.execute(
                f"SELECT COUNT(*) FROM search_queries WHERE created_at < '{cutoff_date}'"
            )
            old_search_count = old_searches.scalar()
            
            # Delete old search queries
            await db.execute(
                f"DELETE FROM search_queries WHERE created_at < '{cutoff_date}'"
            )
            await db.commit()
            
            return {
                "cutoff_date": cutoff_date.isoformat(),
                "days_old": days_old,
                "cleaned_up": {
                    "search_queries": old_search_count
                },
                "status": "completed"
            }
            
        except Exception as e:
            logger.error(f"Data cleanup failed: {str(e)}")
            raise
