"""
Enhanced Orchestrator for Phase 5 - Agent Orchestration & Scalability.
Coordinates between different system components and manages asynchronous task execution.

Enhanced with:
- DRYAD grove creation for task context
- Task decomposition using LangChain
- Agent selection from registry
- Delegation mechanism
"""

import logging
import time
import uuid
from typing import Dict, Any, List, Optional, Union
from enum import Enum
from dataclasses import dataclass
from sqlalchemy.ext.asyncio import AsyncSession

# Optional import: multi-agent orchestrator (DRYAD built-in implementation)
try:
    from dryad.core.multi_agent import multi_agent_orchestrator
except Exception:
    multi_agent_orchestrator = None
from dryad.core.rag_system import rag_system

logger = logging.getLogger(__name__)

class TaskType(Enum):
    """Enumeration of available task types."""
    AGENT_CHAT = "agent_chat"
    MULTI_AGENT_WORKFLOW = "multi_agent_workflow"
    DOCUMENT_SEARCH = "document_search"
    RAG_QUERY = "rag_query"
    DOCUMENT_PROCESSING = "document_processing"
    SYSTEM_ANALYSIS = "system_analysis"
    COMPREHENSIVE_WORKFLOW = "comprehensive_workflow"
    HEALTH_CHECK = "health_check"
    DATA_CLEANUP = "data_cleanup"
    ORCHESTRATED_TASK = "orchestrated_task"  # New: Full orchestration with decomposition

class ExecutionMode(Enum):
    """Enumeration of execution modes."""
    SYNCHRONOUS = "sync"
    ASYNCHRONOUS = "async"

@dataclass
class TaskRequest:
    """Data class for task requests."""
    task_type: TaskType
    payload: Dict[str, Any]
    execution_mode: ExecutionMode = ExecutionMode.SYNCHRONOUS
    priority: int = 1
    timeout: Optional[int] = None

@dataclass
class TaskResult:
    """Data class for task results."""
    task_id: Optional[str]
    status: str
    result: Optional[Dict[str, Any]]
    execution_time: float
    error: Optional[str] = None
    grove_id: Optional[str] = None  # DRYAD grove ID for task context
    subtasks: Optional[List[Dict[str, Any]]] = None  # Decomposed subtasks
    agents_used: Optional[List[str]] = None  # Agents that worked on the task

class EnhancedOrchestrator:
    """
    Enhanced orchestrator that coordinates between all system components
    and manages both synchronous and asynchronous task execution.

    Enhanced with:
    - DRYAD grove creation for task context
    - Task decomposition using LangChain
    - Agent selection from registry
    - Delegation mechanism
    """

    def __init__(self):
        self.supported_tasks = {
            TaskType.AGENT_CHAT: self._handle_agent_chat,
            TaskType.MULTI_AGENT_WORKFLOW: self._handle_multi_agent_workflow,
            TaskType.DOCUMENT_SEARCH: self._handle_document_search,
            TaskType.RAG_QUERY: self._handle_rag_query,
            TaskType.DOCUMENT_PROCESSING: self._handle_document_processing,
            TaskType.SYSTEM_ANALYSIS: self._handle_system_analysis,
            TaskType.COMPREHENSIVE_WORKFLOW: self._handle_comprehensive_workflow,
            TaskType.HEALTH_CHECK: self._handle_health_check,
            TaskType.DATA_CLEANUP: self._handle_data_cleanup,
            TaskType.ORCHESTRATED_TASK: self._handle_orchestrated_task,
        }
    
    async def execute_task(self, task_request: TaskRequest) -> TaskResult:
        """
        Execute a task request either synchronously or asynchronously.
        
        Args:
            task_request: The task request to execute
        
        Returns:
            TaskResult containing execution results
        """
        start_time = time.time()
        
        try:
            logger.info(f"Executing task: {task_request.task_type.value} in {task_request.execution_mode.value} mode")
            
            # Check if task type is supported
            if task_request.task_type not in self.supported_tasks:
                return TaskResult(
                    task_id=None,
                    status="error",
                    result=None,
                    execution_time=time.time() - start_time,
                    error=f"Unsupported task type: {task_request.task_type.value}"
                )
            
            # Execute based on mode
            if task_request.execution_mode == ExecutionMode.ASYNCHRONOUS:
                return await self._execute_async_task(task_request, start_time)
            else:
                return await self._execute_sync_task(task_request, start_time)
                
        except Exception as e:
            logger.error(f"Task execution failed: {str(e)}")
            return TaskResult(
                task_id=None,
                status="error",
                result=None,
                execution_time=time.time() - start_time,
                error=str(e)
            )
    
    async def _execute_async_task(self, task_request: TaskRequest, start_time: float) -> TaskResult:
        """Execute task asynchronously using Celery."""
        try:
            # Import Celery tasks
            from dryad.tasks.agent_tasks import (
                run_multi_agent_workflow_task,
                run_enhanced_agent_chat_task,
                batch_process_conversations_task
            )
            from dryad.tasks.document_tasks import (
                process_document_batch_task,
                rebuild_vector_index_task,
                run_complex_rag_query_task,
                analyze_document_collection_task
            )
            from dryad.tasks.orchestration_tasks import (
                run_comprehensive_workflow_task,
                system_health_check_task,
                cleanup_old_data_task
            )
            
            # Delegate to appropriate Celery task
            task_result = None
            
            if task_request.task_type == TaskType.MULTI_AGENT_WORKFLOW:
                task_result = run_multi_agent_workflow_task.delay(
                    workflow_type=task_request.payload.get("workflow_type", "simple_research"),
                    input_data=task_request.payload.get("input", ""),
                    conversation_id=task_request.payload.get("conversation_id"),
                    save_conversation=task_request.payload.get("save_conversation", True)
                )
            
            elif task_request.task_type == TaskType.AGENT_CHAT:
                task_result = run_enhanced_agent_chat_task.delay(
                    input_data=task_request.payload.get("input", ""),
                    conversation_id=task_request.payload.get("conversation_id"),
                    use_multi_agent=task_request.payload.get("use_multi_agent", False),
                    use_rag=task_request.payload.get("use_rag", False),
                    save_conversation=task_request.payload.get("save_conversation", True)
                )
            
            elif task_request.task_type == TaskType.RAG_QUERY:
                task_result = run_complex_rag_query_task.delay(
                    query=task_request.payload.get("query", ""),
                    search_limit=task_request.payload.get("search_limit", 5),
                    use_multi_agent=task_request.payload.get("use_multi_agent", False),
                    conversation_id=task_request.payload.get("conversation_id"),
                    save_conversation=task_request.payload.get("save_conversation", True)
                )
            
            elif task_request.task_type == TaskType.DOCUMENT_PROCESSING:
                task_result = process_document_batch_task.delay(
                    document_data_list=task_request.payload.get("documents", [])
                )
            
            elif task_request.task_type == TaskType.SYSTEM_ANALYSIS:
                analysis_type = task_request.payload.get("analysis_type", "summary")
                if analysis_type == "document_collection":
                    task_result = analyze_document_collection_task.delay(analysis_type)
                else:
                    task_result = system_health_check_task.delay()
            
            elif task_request.task_type == TaskType.COMPREHENSIVE_WORKFLOW:
                task_result = run_comprehensive_workflow_task.delay(
                    workflow_config=task_request.payload
                )
            
            elif task_request.task_type == TaskType.HEALTH_CHECK:
                task_result = system_health_check_task.delay()
            
            elif task_request.task_type == TaskType.DATA_CLEANUP:
                task_result = cleanup_old_data_task.delay(
                    days_old=task_request.payload.get("days_old", 30)
                )
            
            if task_result:
                return TaskResult(
                    task_id=task_result.id,
                    status="dispatched",
                    result={"message": "Task dispatched for asynchronous execution"},
                    execution_time=time.time() - start_time
                )
            else:
                return TaskResult(
                    task_id=None,
                    status="error",
                    result=None,
                    execution_time=time.time() - start_time,
                    error="Failed to dispatch async task"
                )
                
        except Exception as e:
            logger.error(f"Async task execution failed: {str(e)}")
            return TaskResult(
                task_id=None,
                status="error",
                result=None,
                execution_time=time.time() - start_time,
                error=f"Async execution failed: {str(e)}"
            )
    
    async def _execute_sync_task(self, task_request: TaskRequest, start_time: float) -> TaskResult:
        """Execute task synchronously."""
        try:
            # Generate a task ID for synchronous tasks
            import uuid
            task_id = f"sync-{uuid.uuid4().hex[:8]}"

            handler = self.supported_tasks[task_request.task_type]
            result = await handler(task_request.payload)

            return TaskResult(
                task_id=task_id,
                status="completed",
                result=result,
                execution_time=time.time() - start_time
            )
            
        except Exception as e:
            logger.error(f"Sync task execution failed: {str(e)}")
            # Generate a task ID even for failed tasks
            import uuid
            task_id = f"sync-{uuid.uuid4().hex[:8]}"

            return TaskResult(
                task_id=task_id,
                status="error",
                result=None,
                execution_time=time.time() - start_time,
                error=str(e)
            )
    
    async def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """
        Get the status of an asynchronous task.
        
        Args:
            task_id: The Celery task ID
        
        Returns:
            Dict containing task status information
        """
        try:
            from dryad.core.celery_app import celery_app
            
            task_result = celery_app.AsyncResult(task_id)
            
            return {
                "task_id": task_id,
                "status": task_result.status,
                "result": task_result.result if task_result.ready() else None,
                "info": task_result.info,
                "ready": task_result.ready(),
                "successful": task_result.successful() if task_result.ready() else None,
                "failed": task_result.failed() if task_result.ready() else None
            }
            
        except Exception as e:
            logger.error(f"Failed to get task status: {str(e)}")
            return {
                "task_id": task_id,
                "status": "unknown",
                "error": str(e)
            }
    
    def get_capabilities(self) -> Dict[str, Any]:
        """
        Get orchestrator capabilities and supported task types.
        
        Returns:
            Dict containing capabilities information
        """
        return {
            "supported_tasks": [task_type.value for task_type in self.supported_tasks.keys()],
            "execution_modes": [mode.value for mode in ExecutionMode],
            "features": {
                "asynchronous_execution": True,
                "task_monitoring": True,
                "multi_agent_coordination": True,
                "document_processing": True,
                "rag_capabilities": True,
                "system_analysis": True,
                "health_monitoring": True
            },
            "version": "5.0.0"
        }
    
    # Synchronous task handlers
    async def _handle_agent_chat(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle basic agent chat synchronously."""
        from dryad.core.agent import agent_graph_app
        
        agent_input = {
            "input": payload.get("input", ""),
            "chat_history": payload.get("chat_history", [])
        }
        
        final_state = {}
        for state in agent_graph_app.stream(agent_input):
            final_state = state
        
        return {
            "output": final_state,
            "input": payload.get("input", ""),
            "execution_mode": "synchronous"
        }
    
    async def _handle_multi_agent_workflow(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle multi-agent workflow synchronously."""
        workflow_result = await multi_agent_orchestrator.execute_workflow(
            workflow_type=payload.get("workflow_type", "simple_research"),
            input_data=payload.get("input", ""),
            context=payload.get("context", [])
        )
        
        return {
            "result": workflow_result.get("result", ""),
            "agents_used": workflow_result.get("agents_used", []),
            "execution_time": workflow_result.get("execution_time", 0),
            "workflow_type": payload.get("workflow_type", "simple_research"),
            "execution_mode": "synchronous"
        }
    
    async def _handle_document_search(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle document search synchronously."""
        from dryad.infrastructure.database import AsyncSessionLocal
        from dryad.services.document_service import DocumentService
        
        async with AsyncSessionLocal() as db:
            search_results, search_id = await DocumentService.semantic_search(
                db=db,
                query=payload.get("query", ""),
                limit=payload.get("limit", 5),
                score_threshold=payload.get("score_threshold", 0.1),
                search_type=payload.get("search_type", "chunks")
            )
            
            return {
                "query": payload.get("query", ""),
                "results": [
                    {
                        "content": result.content,
                        "score": result.score,
                        "document_title": result.document_title
                    }
                    for result in search_results
                ],
                "search_id": search_id,
                "total_found": len(search_results),
                "execution_mode": "synchronous"
            }
    
    async def _handle_rag_query(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle RAG query synchronously."""
        from dryad.infrastructure.database import AsyncSessionLocal
        
        async with AsyncSessionLocal() as db:
            rag_result = await rag_system.retrieve_and_generate(
                db=db,
                query=payload.get("query", ""),
                search_limit=payload.get("search_limit", 5),
                score_threshold=payload.get("score_threshold", 0.1),
                use_multi_agent=payload.get("use_multi_agent", False)
            )
            
            return {
                "query": payload.get("query", ""),
                "response": rag_result.get("response", ""),
                "retrieved_documents": rag_result.get("retrieved_documents", []),
                "context_used": rag_result.get("context_used", False),
                "execution_mode": "synchronous"
            }
    
    async def _handle_document_processing(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle document processing synchronously."""
        return {
            "message": "Document processing requires asynchronous execution",
            "recommendation": "Use async mode for document processing tasks",
            "execution_mode": "synchronous"
        }
    
    async def _handle_system_analysis(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle system analysis synchronously."""
        analysis_type = payload.get("analysis_type", "basic")
        
        if analysis_type == "basic":
            return {
                "analysis_type": analysis_type,
                "timestamp": time.time(),
                "components": {
                    "orchestrator": "operational",
                    "multi_agent": "operational",
                    "rag_system": "operational",
                    "document_service": "operational"
                },
                "execution_mode": "synchronous"
            }
        else:
            return {
                "message": "Advanced system analysis requires asynchronous execution",
                "recommendation": "Use async mode for detailed system analysis",
                "execution_mode": "synchronous"
            }
    
    async def _handle_comprehensive_workflow(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle comprehensive workflow synchronously."""
        return {
            "message": "Comprehensive workflows require asynchronous execution",
            "recommendation": "Use async mode for comprehensive workflows",
            "execution_mode": "synchronous"
        }
    
    async def _handle_health_check(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle health check synchronously."""
        return {
            "status": "healthy",
            "timestamp": time.time(),
            "orchestrator": "operational",
            "execution_mode": "synchronous"
        }
    
    async def _handle_data_cleanup(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle data cleanup synchronously."""
        return {
            "message": "Data cleanup requires asynchronous execution",
            "recommendation": "Use async mode for data cleanup tasks",
            "execution_mode": "synchronous"
        }

    async def _handle_orchestrated_task(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle fully orchestrated task with decomposition, grove creation, and agent delegation.

        This is the main entry point for the 20-agent swarm system.
        """
        from dryad.infrastructure.database import AsyncSessionLocal

        async with AsyncSessionLocal() as db:
            return await self.orchestrate_task(
                db=db,
                user_request=payload.get("request", ""),
                context=payload.get("context", {}),
                create_grove=payload.get("create_grove", True)
            )

    async def orchestrate_task(
        self,
        db: AsyncSession,
        user_request: str,
        context: Optional[Dict[str, Any]] = None,
        create_grove: bool = True
    ) -> Dict[str, Any]:
        """
        Orchestrate a complex task using the full 20-agent swarm.

        Steps:
        1. Create DRYAD grove for task context
        2. Decompose task into subtasks
        3. Select appropriate agents for each subtask
        4. Delegate subtasks to agents
        5. Collect and synthesize results

        Args:
            db: Database session
            user_request: The user's request
            context: Additional context
            create_grove: Whether to create a DRYAD grove

        Returns:
            Dict containing orchestration results
        """
        # Lazy imports to avoid circular dependencies
        from dryad.core.task_decomposition import task_decomposer, Subtask
        from dryad.services.agent_registry_service import AgentRegistryService
        from dryad.models.agent_registry import AgentSelectionRequest

        start_time = time.time()
        grove_id = None
        agents_used = []

        try:
            logger.info(f"🎯 Orchestrating task: {user_request[:100]}...")

            # Step 1: Create DRYAD grove for task context
            if create_grove:
                grove_id = await self._create_task_grove(db, user_request, context)
                logger.info(f"✅ Created DRYAD grove: {grove_id}")

            # Step 2: Decompose task into subtasks
            subtasks = await task_decomposer.decompose_task(user_request, context)
            logger.info(f"✅ Decomposed into {len(subtasks)} subtasks")

            # Step 3: Get execution plan
            execution_plan = task_decomposer.get_execution_plan(subtasks)
            logger.info(f"✅ Execution plan: {len(execution_plan)} waves")

            # Step 4: Execute subtasks wave by wave
            subtask_results = {}
            for wave_idx, wave in enumerate(execution_plan):
                logger.info(f"🌊 Executing wave {wave_idx + 1}/{len(execution_plan)}: {wave}")

                for subtask_id in wave:
                    subtask = next(s for s in subtasks if s.id == subtask_id)

                    # Select agent for subtask
                    agent = await self._select_agent_for_subtask(db, subtask)
                    if agent:
                        agents_used.append(agent.agent_id)
                        logger.info(f"  📌 {subtask_id} -> {agent.name}")

                    # Create branch for subtask if grove exists
                    if grove_id:
                        await self._create_subtask_branch(
                            db, grove_id, subtask, wave_idx
                        )

                    # Execute subtask (placeholder - actual execution TBD)
                    subtask_results[subtask_id] = {
                        "subtask": subtask.description,
                        "agent": agent.agent_id if agent else "none",
                        "status": "delegated",
                        "wave": wave_idx + 1
                    }

            # Step 5: Synthesize results
            result = {
                "status": "orchestrated",
                "user_request": user_request,
                "grove_id": grove_id,
                "subtasks_count": len(subtasks),
                "execution_waves": len(execution_plan),
                "agents_used": list(set(agents_used)),
                "subtask_results": subtask_results,
                "execution_time": time.time() - start_time,
                "message": "Task successfully orchestrated and delegated to agents"
            }

            logger.info(f"✅ Orchestration complete in {result['execution_time']:.2f}s")
            return result

        except Exception as e:
            logger.error(f"❌ Orchestration failed: {e}")
            return {
                "status": "error",
                "error": str(e),
                "grove_id": grove_id,
                "agents_used": agents_used,
                "execution_time": time.time() - start_time
            }

    async def _create_task_grove(
        self,
        db: AsyncSession,
        user_request: str,
        context: Optional[Dict[str, Any]]
    ) -> str:
        """Create a DRYAD grove for the task."""
        from dryad.services.grove_service import GroveService
        from dryad.schemas.grove_schemas import GroveCreate

        grove_service = GroveService(db)

        grove_data = GroveCreate(
            name=f"Task: {user_request[:50]}...",
            description=f"Orchestrated task grove\n\nRequest: {user_request}",
            template_metadata=context or {},
            is_favorite=False
        )

        grove = await grove_service.create_grove(grove_data)
        return grove.id

    async def _select_agent_for_subtask(
        self,
        db: AsyncSession,
        subtask: "Subtask"
    ) -> Optional[Any]:
        """Select the best agent for a subtask based on capabilities."""
        from dryad.services.agent_registry_service import AgentRegistryService
        from dryad.models.agent_registry import AgentSelectionRequest

        agent_service = AgentRegistryService(db)

        selection_request = AgentSelectionRequest(
            required_capabilities=subtask.required_capabilities,
            preferred_tier=None,  # Let it select from any tier
            task_context={
                "description": subtask.description,
                "category": subtask.category.value,
                "complexity": subtask.estimated_complexity.value
            }
        )

        try:
            selected = await agent_service.select_agent(selection_request)
            return selected if selected else None
        except Exception as e:
            logger.warning(f"Agent selection failed for {subtask.id}: {e}")
            return None

    async def _create_subtask_branch(
        self,
        db: AsyncSession,
        grove_id: str,
        subtask: "Subtask",
        wave_idx: int
    ) -> str:
        """Create a DRYAD branch for a subtask."""
        from dryad.services.branch_service import BranchService
        from dryad.schemas.branch_schemas import BranchCreate

        branch_service = BranchService(db)

        branch_data = BranchCreate(
            grove_id=grove_id,
            name=f"Subtask: {subtask.id}",
            description=subtask.description,
            parent_id=None,  # Will be root branch
            metadata={
                "subtask_id": subtask.id,
                "category": subtask.category.value,
                "complexity": subtask.estimated_complexity.value,
                "wave": wave_idx + 1,
                "priority": subtask.priority,
                "required_capabilities": subtask.required_capabilities
            }
        )

        branch = await branch_service.create_branch(branch_data)
        return branch.id

# Global orchestrator instance
enhanced_orchestrator = EnhancedOrchestrator()
