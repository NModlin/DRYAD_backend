"""
Project Manager Agent

Tier 1 Orchestrator agent responsible for:
- Task breakdown and planning
- DRYAD branch creation for subtasks
- Dependency tracking
- Progress monitoring
- Sprint management
"""

import logging
import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from dataclasses import dataclass
from enum import Enum
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.task_decomposition import task_decomposer, Subtask, TaskComplexity
from app.dryad.services.branch_service import BranchService
from app.dryad.services.grove_service import GroveService
from app.dryad.schemas.branch_schemas import BranchCreate, BranchUpdate
from app.dryad.models.branch import BranchStatus, BranchPriority
from app.services.agent_registry_service import AgentRegistryService
from app.models.agent_registry import AgentSelectionRequest, AgentMetricsUpdate

logger = logging.getLogger(__name__)


class TaskStatus(str, Enum):
    """Task status enumeration."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    BLOCKED = "blocked"
    FAILED = "failed"
    CANCELLED = "cancelled"


class SprintStatus(str, Enum):
    """Sprint status enumeration."""
    PLANNING = "planning"
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


@dataclass
class ManagedTask:
    """Represents a task managed by the Project Manager."""
    id: str
    description: str
    subtask: Subtask
    branch_id: Optional[str]
    assigned_agent_id: Optional[str]
    status: TaskStatus
    dependencies: List[str]
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    progress: float  # 0.0 to 1.0
    metadata: Dict[str, Any]


@dataclass
class Sprint:
    """Represents a sprint managed by the Project Manager."""
    id: str
    name: str
    grove_id: str
    tasks: List[str]  # Task IDs
    status: SprintStatus
    start_date: datetime
    end_date: Optional[datetime]
    goal: str
    metadata: Dict[str, Any]


class ProjectManagerAgent:
    """
    Project Manager Agent - Tier 1 Orchestrator
    
    Responsibilities:
    - Break down projects into manageable tasks
    - Create DRYAD branches for task tracking
    - Assign tasks to appropriate agents
    - Track dependencies and progress
    - Manage sprints and milestones
    """
    
    def __init__(self, db: AsyncSession):
        """Initialize the Project Manager agent."""
        self.db = db
        self.agent_id = "project_manager"
        self.tasks: Dict[str, ManagedTask] = {}
        self.sprints: Dict[str, Sprint] = {}
        logger.info(f"✅ Project Manager Agent initialized")
    
    async def create_project_plan(
        self,
        grove_id: str,
        project_description: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create a comprehensive project plan.
        
        Args:
            grove_id: DRYAD grove ID for the project
            project_description: Description of the project
            context: Additional context
            
        Returns:
            Dict containing the project plan
        """
        try:
            logger.info(f"📋 Creating project plan for grove {grove_id}")
            
            # Step 1: Decompose project into subtasks
            subtasks = await task_decomposer.decompose_task(
                project_description,
                context
            )
            logger.info(f"✅ Decomposed into {len(subtasks)} subtasks")
            
            # Step 2: Create managed tasks
            managed_tasks = []
            for subtask in subtasks:
                task = ManagedTask(
                    id=subtask.id,
                    description=subtask.description,
                    subtask=subtask,
                    branch_id=None,
                    assigned_agent_id=None,
                    status=TaskStatus.PENDING,
                    dependencies=subtask.dependencies,
                    created_at=datetime.now(timezone.utc),
                    started_at=None,
                    completed_at=None,
                    progress=0.0,
                    metadata={
                        "category": subtask.category.value,
                        "complexity": subtask.estimated_complexity.value,
                        "priority": subtask.priority
                    }
                )
                self.tasks[task.id] = task
                managed_tasks.append(task)
            
            # Step 3: Create DRYAD branches for each task
            for task in managed_tasks:
                branch_id = await self._create_task_branch(grove_id, task)
                task.branch_id = branch_id
                logger.info(f"  📌 Created branch {branch_id} for task {task.id}")
            
            # Step 4: Assign agents to tasks
            for task in managed_tasks:
                agent = await self._assign_agent_to_task(task)
                if agent:
                    task.assigned_agent_id = agent.agent_id
                    logger.info(f"  👤 Assigned {agent.name} to task {task.id}")
            
            # Step 5: Create execution plan
            execution_plan = task_decomposer.get_execution_plan(subtasks)
            
            return {
                "status": "success",
                "grove_id": grove_id,
                "total_tasks": len(managed_tasks),
                "execution_waves": len(execution_plan),
                "tasks": [
                    {
                        "id": task.id,
                        "description": task.description,
                        "status": task.status.value,
                        "branch_id": task.branch_id,
                        "assigned_agent": task.assigned_agent_id,
                        "dependencies": task.dependencies,
                        "priority": task.subtask.priority
                    }
                    for task in managed_tasks
                ],
                "execution_plan": execution_plan,
                "message": f"Project plan created with {len(managed_tasks)} tasks"
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to create project plan: {e}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    async def _create_task_branch(
        self,
        grove_id: str,
        task: ManagedTask
    ) -> str:
        """Create a DRYAD branch for a task."""
        branch_service = BranchService(self.db)
        
        # Map task priority to branch priority
        priority_map = {
            5: BranchPriority.HIGHEST,
            4: BranchPriority.HIGH,
            3: BranchPriority.MEDIUM,
            2: BranchPriority.LOW,
            1: BranchPriority.LOWEST
        }
        
        branch_data = BranchCreate(
            grove_id=grove_id,
            name=f"Task: {task.id}",
            description=task.description,
            parent_id=None,  # Root level
            priority=priority_map.get(task.subtask.priority, BranchPriority.MEDIUM),
            metadata={
                "task_id": task.id,
                "category": task.subtask.category.value,
                "complexity": task.subtask.estimated_complexity.value,
                "required_capabilities": task.subtask.required_capabilities,
                "dependencies": task.dependencies,
                "created_by": "project_manager"
            }
        )
        
        branch = await branch_service.create_branch(branch_data)
        return branch.id
    
    async def _assign_agent_to_task(
        self,
        task: ManagedTask
    ) -> Optional[Any]:
        """Assign an agent to a task based on capabilities."""
        agent_service = AgentRegistryService(self.db)
        
        selection_request = AgentSelectionRequest(
            required_capabilities=task.subtask.required_capabilities,
            preferred_tier=None,
            task_context={
                "description": task.description,
                "category": task.subtask.category.value,
                "complexity": task.subtask.estimated_complexity.value
            }
        )
        
        try:
            agent = await agent_service.select_agent(selection_request)
            return agent
        except Exception as e:
            logger.warning(f"Agent assignment failed for {task.id}: {e}")
            return None
    
    async def update_task_progress(
        self,
        task_id: str,
        progress: float,
        status: Optional[TaskStatus] = None
    ) -> Dict[str, Any]:
        """Update task progress and status."""
        if task_id not in self.tasks:
            return {"status": "error", "error": f"Task {task_id} not found"}
        
        task = self.tasks[task_id]
        task.progress = max(0.0, min(1.0, progress))
        
        if status:
            task.status = status
            
            if status == TaskStatus.IN_PROGRESS and not task.started_at:
                task.started_at = datetime.now(timezone.utc)
            elif status == TaskStatus.COMPLETED:
                task.completed_at = datetime.now(timezone.utc)
                task.progress = 1.0
        
        # Update branch status
        if task.branch_id:
            await self._update_branch_status(task)
        
        logger.info(f"📊 Task {task_id} progress: {progress:.0%}, status: {task.status.value}")
        
        return {
            "status": "success",
            "task_id": task_id,
            "progress": task.progress,
            "task_status": task.status.value
        }
    
    async def _update_branch_status(self, task: ManagedTask):
        """Update DRYAD branch status based on task status."""
        branch_service = BranchService(self.db)

        status_map = {
            TaskStatus.PENDING: BranchStatus.ACTIVE,
            TaskStatus.IN_PROGRESS: BranchStatus.ACTIVE,
            TaskStatus.COMPLETED: BranchStatus.ARCHIVED,  # Completed tasks are archived
            TaskStatus.BLOCKED: BranchStatus.PRUNED,  # Blocked tasks are pruned
            TaskStatus.FAILED: BranchStatus.PRUNED,  # Failed tasks are pruned
            TaskStatus.CANCELLED: BranchStatus.ARCHIVED
        }

        branch_status = status_map.get(task.status, BranchStatus.ACTIVE)
        
        update_data = BranchUpdate(
            status=branch_status,
            metadata={
                **task.metadata,
                "progress": task.progress,
                "task_status": task.status.value,
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
        )
        
        await branch_service.update_branch(task.branch_id, update_data)
    
    def get_project_status(self, grove_id: Optional[str] = None) -> Dict[str, Any]:
        """Get overall project status."""
        tasks = list(self.tasks.values())
        
        if grove_id:
            # Filter tasks by grove (would need to track grove_id in tasks)
            pass
        
        total_tasks = len(tasks)
        if total_tasks == 0:
            return {"status": "no_tasks", "message": "No tasks found"}
        
        status_counts = {}
        for status in TaskStatus:
            status_counts[status.value] = sum(1 for t in tasks if t.status == status)
        
        avg_progress = sum(t.progress for t in tasks) / total_tasks
        
        return {
            "total_tasks": total_tasks,
            "status_breakdown": status_counts,
            "overall_progress": avg_progress,
            "completed_tasks": status_counts.get(TaskStatus.COMPLETED.value, 0),
            "in_progress_tasks": status_counts.get(TaskStatus.IN_PROGRESS.value, 0),
            "pending_tasks": status_counts.get(TaskStatus.PENDING.value, 0),
            "blocked_tasks": status_counts.get(TaskStatus.BLOCKED.value, 0)
        }

