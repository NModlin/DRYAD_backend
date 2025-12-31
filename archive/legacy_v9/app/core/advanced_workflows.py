"""
Advanced Workflow Engine for DRYAD.AI Backend
Implements complex multi-step workflows, advanced agent orchestration, and intelligent task routing.
"""

import asyncio
import json
import time
import uuid
from typing import Dict, Any, List, Optional, Callable, Union
from dataclasses import dataclass, asdict
from enum import Enum
import logging

from app.core.logging_config import get_logger
from app.core.monitoring import metrics_collector
from app.core.scalability import task_queue
from app.core.llm_config import get_llm, get_llm_info

logger = get_logger(__name__)


class WorkflowStatus(str, Enum):
    """Workflow execution status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PAUSED = "paused"


class TaskType(str, Enum):
    """Types of workflow tasks."""
    RESEARCH = "research"
    ANALYSIS = "analysis"
    GENERATION = "generation"
    VALIDATION = "validation"
    SYNTHESIS = "synthesis"
    DECISION = "decision"
    PARALLEL = "parallel"
    CONDITIONAL = "conditional"


@dataclass
class WorkflowTask:
    """Individual task within a workflow."""
    id: str
    type: TaskType
    name: str
    description: str
    inputs: Dict[str, Any]
    outputs: Dict[str, Any]
    dependencies: List[str]
    agent_requirements: List[str]
    timeout: int
    retry_count: int
    max_retries: int
    status: WorkflowStatus
    created_at: float
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    error: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class Workflow:
    """Complete workflow definition."""
    id: str
    name: str
    description: str
    tasks: List[WorkflowTask]
    status: WorkflowStatus
    created_at: float
    results: Dict[str, Any]
    metadata: Dict[str, Any]
    started_at: Optional[float] = None
    completed_at: Optional[float] = None


class AdvancedWorkflowEngine:
    """Advanced workflow execution engine with intelligent orchestration."""
    
    def __init__(self):
        self.workflows: Dict[str, Workflow] = {}
        self.task_executors: Dict[TaskType, Callable] = {}
        self.running_workflows: Dict[str, asyncio.Task] = {}
        
        # Register default task executors
        self._register_default_executors()
        
        # Workflow templates
        self.workflow_templates = self._create_workflow_templates()
    
    def _register_default_executors(self):
        """Register default task executors."""
        self.task_executors[TaskType.RESEARCH] = self._execute_research_task
        self.task_executors[TaskType.ANALYSIS] = self._execute_analysis_task
        self.task_executors[TaskType.GENERATION] = self._execute_generation_task
        self.task_executors[TaskType.VALIDATION] = self._execute_validation_task
        self.task_executors[TaskType.SYNTHESIS] = self._execute_synthesis_task
        self.task_executors[TaskType.DECISION] = self._execute_decision_task
        self.task_executors[TaskType.PARALLEL] = self._execute_parallel_task
        self.task_executors[TaskType.CONDITIONAL] = self._execute_conditional_task
    
    def _create_workflow_templates(self) -> Dict[str, Dict[str, Any]]:
        """Create predefined workflow templates."""
        return {
            "research_and_analysis": {
                "name": "Research and Analysis Workflow",
                "description": "Comprehensive research followed by detailed analysis",
                "tasks": [
                    {
                        "type": TaskType.RESEARCH,
                        "name": "Initial Research",
                        "description": "Gather comprehensive information on the topic",
                        "dependencies": [],
                        "agent_requirements": ["researcher"],
                        "timeout": 300
                    },
                    {
                        "type": TaskType.ANALYSIS,
                        "name": "Data Analysis",
                        "description": "Analyze gathered research data",
                        "dependencies": ["Initial Research"],
                        "agent_requirements": ["analyst"],
                        "timeout": 240
                    },
                    {
                        "type": TaskType.SYNTHESIS,
                        "name": "Synthesis",
                        "description": "Synthesize research and analysis into insights",
                        "dependencies": ["Data Analysis"],
                        "agent_requirements": ["writer", "analyst"],
                        "timeout": 180
                    }
                ]
            },
            "content_creation": {
                "name": "Content Creation Workflow",
                "description": "Research, plan, write, and validate content",
                "tasks": [
                    {
                        "type": TaskType.RESEARCH,
                        "name": "Topic Research",
                        "description": "Research the content topic thoroughly",
                        "dependencies": [],
                        "agent_requirements": ["researcher"],
                        "timeout": 200
                    },
                    {
                        "type": TaskType.GENERATION,
                        "name": "Content Planning",
                        "description": "Create content outline and structure",
                        "dependencies": ["Topic Research"],
                        "agent_requirements": ["writer"],
                        "timeout": 120
                    },
                    {
                        "type": TaskType.GENERATION,
                        "name": "Content Writing",
                        "description": "Write the actual content",
                        "dependencies": ["Content Planning"],
                        "agent_requirements": ["writer"],
                        "timeout": 300
                    },
                    {
                        "type": TaskType.VALIDATION,
                        "name": "Content Review",
                        "description": "Review and validate content quality",
                        "dependencies": ["Content Writing"],
                        "agent_requirements": ["analyst"],
                        "timeout": 120
                    }
                ]
            },
            "decision_support": {
                "name": "Decision Support Workflow",
                "description": "Comprehensive decision analysis and recommendation",
                "tasks": [
                    {
                        "type": TaskType.PARALLEL,
                        "name": "Parallel Research",
                        "description": "Research multiple aspects simultaneously",
                        "dependencies": [],
                        "agent_requirements": ["researcher"],
                        "timeout": 300,
                        "subtasks": [
                            {"name": "Market Research", "focus": "market_analysis"},
                            {"name": "Technical Research", "focus": "technical_analysis"},
                            {"name": "Risk Research", "focus": "risk_analysis"}
                        ]
                    },
                    {
                        "type": TaskType.ANALYSIS,
                        "name": "Comprehensive Analysis",
                        "description": "Analyze all research findings",
                        "dependencies": ["Parallel Research"],
                        "agent_requirements": ["analyst"],
                        "timeout": 240
                    },
                    {
                        "type": TaskType.DECISION,
                        "name": "Decision Recommendation",
                        "description": "Generate decision recommendations",
                        "dependencies": ["Comprehensive Analysis"],
                        "agent_requirements": ["coordinator", "analyst"],
                        "timeout": 180
                    }
                ]
            }
        }
    
    async def create_workflow_from_template(self, template_name: str, inputs: Dict[str, Any]) -> str:
        """Create a workflow from a predefined template."""
        if template_name not in self.workflow_templates:
            raise ValueError(f"Unknown workflow template: {template_name}")
        
        template = self.workflow_templates[template_name]
        workflow_id = str(uuid.uuid4())
        
        # Create workflow tasks from template
        tasks = []
        for i, task_template in enumerate(template["tasks"]):
            task_id = f"{workflow_id}_task_{i}"
            
            task = WorkflowTask(
                id=task_id,
                type=TaskType(task_template["type"]),
                name=task_template["name"],
                description=task_template["description"],
                inputs=inputs.copy(),
                outputs={},
                dependencies=task_template.get("dependencies", []),
                agent_requirements=task_template.get("agent_requirements", []),
                timeout=task_template.get("timeout", 300),
                retry_count=0,
                max_retries=task_template.get("max_retries", 2),
                status=WorkflowStatus.PENDING,
                created_at=time.time(),
                metadata=task_template.get("metadata", {})
            )
            tasks.append(task)
        
        # Create workflow
        workflow = Workflow(
            id=workflow_id,
            name=template["name"],
            description=template["description"],
            tasks=tasks,
            status=WorkflowStatus.PENDING,
            created_at=time.time(),
            results={},
            metadata={"template": template_name, "inputs": inputs}
        )
        
        self.workflows[workflow_id] = workflow
        logger.info(f"Created workflow {workflow_id} from template {template_name}")
        
        return workflow_id
    
    async def execute_workflow(self, workflow_id: str) -> Dict[str, Any]:
        """Execute a workflow asynchronously."""
        if workflow_id not in self.workflows:
            raise ValueError(f"Workflow {workflow_id} not found")
        
        workflow = self.workflows[workflow_id]
        
        if workflow.status != WorkflowStatus.PENDING:
            raise ValueError(f"Workflow {workflow_id} is not in pending state")
        
        # Start workflow execution
        workflow.status = WorkflowStatus.RUNNING
        workflow.started_at = time.time()
        
        logger.info(f"Starting workflow execution: {workflow_id}")
        metrics_collector.record_counter("workflows.started")
        
        try:
            # Create execution task
            execution_task = asyncio.create_task(self._execute_workflow_tasks(workflow))
            self.running_workflows[workflow_id] = execution_task
            
            # Wait for completion
            results = await execution_task
            
            # Update workflow status
            workflow.status = WorkflowStatus.COMPLETED
            workflow.completed_at = time.time()
            workflow.results = results
            
            # Clean up
            if workflow_id in self.running_workflows:
                del self.running_workflows[workflow_id]
            
            logger.info(f"Workflow {workflow_id} completed successfully")
            metrics_collector.record_counter("workflows.completed")
            metrics_collector.record_timer(
                "workflows.duration", 
                (workflow.completed_at - workflow.started_at) * 1000
            )
            
            return results
            
        except Exception as e:
            workflow.status = WorkflowStatus.FAILED
            workflow.completed_at = time.time()
            
            if workflow_id in self.running_workflows:
                del self.running_workflows[workflow_id]
            
            logger.error(f"Workflow {workflow_id} failed: {e}")
            metrics_collector.record_counter("workflows.failed")
            
            raise e
    
    async def _execute_workflow_tasks(self, workflow: Workflow) -> Dict[str, Any]:
        """Execute all tasks in a workflow with dependency management."""
        completed_tasks = set()
        task_results = {}
        
        while len(completed_tasks) < len(workflow.tasks):
            # Find tasks ready to execute
            ready_tasks = []
            for task in workflow.tasks:
                if (task.status == WorkflowStatus.PENDING and 
                    all(dep in completed_tasks for dep in task.dependencies)):
                    ready_tasks.append(task)
            
            if not ready_tasks:
                # Check for deadlock
                pending_tasks = [t for t in workflow.tasks if t.status == WorkflowStatus.PENDING]
                if pending_tasks:
                    raise RuntimeError(f"Workflow deadlock detected. Pending tasks: {[t.name for t in pending_tasks]}")
                break
            
            # Execute ready tasks (potentially in parallel)
            task_executions = []
            for task in ready_tasks:
                task.status = WorkflowStatus.RUNNING
                task.started_at = time.time()
                
                # Prepare task inputs with results from dependencies
                task_inputs = task.inputs.copy()
                for dep_name in task.dependencies:
                    if dep_name in task_results:
                        task_inputs[f"dep_{dep_name}"] = task_results[dep_name]
                
                # Execute task
                execution = self._execute_single_task(task, task_inputs)
                task_executions.append((task, execution))
            
            # Wait for all ready tasks to complete
            for task, execution in task_executions:
                try:
                    result = await execution
                    task.status = WorkflowStatus.COMPLETED
                    task.completed_at = time.time()
                    task.outputs = result
                    task_results[task.name] = result
                    completed_tasks.add(task.name)
                    
                    logger.info(f"Task {task.name} completed successfully")
                    
                except Exception as e:
                    task.status = WorkflowStatus.FAILED
                    task.completed_at = time.time()
                    task.error = str(e)
                    
                    logger.error(f"Task {task.name} failed: {e}")
                    
                    # Check if we should retry
                    if task.retry_count < task.max_retries:
                        task.retry_count += 1
                        task.status = WorkflowStatus.PENDING
                        task.started_at = None
                        task.completed_at = None
                        task.error = None
                        logger.info(f"Retrying task {task.name} (attempt {task.retry_count + 1})")
                    else:
                        raise e
        
        return task_results
    
    async def _execute_single_task(self, task: WorkflowTask, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a single workflow task."""
        if task.type not in self.task_executors:
            raise ValueError(f"No executor found for task type: {task.type}")
        
        executor = self.task_executors[task.type]
        
        # Execute with timeout
        try:
            result = await asyncio.wait_for(
                executor(task, inputs),
                timeout=task.timeout
            )
            return result
        except asyncio.TimeoutError:
            raise TimeoutError(f"Task {task.name} timed out after {task.timeout} seconds")
    
    async def _execute_research_task(self, task: WorkflowTask, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a research task."""
        query = inputs.get("query", inputs.get("topic", ""))
        context = inputs.get("context", "")
        
        # Use multi-agent system for research
        try:
            from app.core.multi_agent import multi_agent_orchestrator
            result = multi_agent_orchestrator.execute_simple_query(query, context)
            
            return {
                "research_results": result,
                "query": query,
                "sources": result.get("sources", []),
                "summary": result.get("result", "")
            }
        except Exception as e:
            logger.error(f"Research task failed: {e}")
            return {
                "research_results": {"error": str(e)},
                "query": query,
                "sources": [],
                "summary": f"Research failed: {e}"
            }
    
    async def _execute_analysis_task(self, task: WorkflowTask, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Execute an analysis task."""
        data = inputs.get("data", inputs.get("research_results", {}))
        analysis_type = inputs.get("analysis_type", "general")
        
        # Use LLM for analysis
        try:
            llm = get_llm()
            if llm is None:
                return {"analysis": "Analysis unavailable - no LLM configured", "insights": []}
            
            prompt = f"""
            Analyze the following data and provide insights:
            
            Data: {json.dumps(data, indent=2)}
            Analysis Type: {analysis_type}
            
            Please provide:
            1. Key findings
            2. Patterns and trends
            3. Insights and implications
            4. Recommendations
            """
            
            response = await llm.ainvoke(prompt)
            
            return {
                "analysis": response.content if hasattr(response, 'content') else str(response),
                "analysis_type": analysis_type,
                "data_analyzed": data,
                "insights": []  # Could be extracted from response
            }
            
        except Exception as e:
            logger.error(f"Analysis task failed: {e}")
            return {
                "analysis": f"Analysis failed: {e}",
                "analysis_type": analysis_type,
                "insights": []
            }
    
    async def _execute_generation_task(self, task: WorkflowTask, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a content generation task."""
        prompt = inputs.get("prompt", inputs.get("topic", ""))
        content_type = inputs.get("content_type", "general")
        
        try:
            llm = get_llm()
            if llm is None:
                return {"content": "Content generation unavailable - no LLM configured"}
            
            generation_prompt = f"""
            Generate {content_type} content based on the following:
            
            {prompt}
            
            Please create high-quality, relevant content that addresses the requirements.
            """
            
            response = await llm.ainvoke(generation_prompt)
            
            return {
                "content": response.content if hasattr(response, 'content') else str(response),
                "content_type": content_type,
                "prompt": prompt
            }
            
        except Exception as e:
            logger.error(f"Generation task failed: {e}")
            return {
                "content": f"Generation failed: {e}",
                "content_type": content_type
            }
    
    async def _execute_validation_task(self, task: WorkflowTask, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a validation task."""
        content = inputs.get("content", "")
        criteria = inputs.get("validation_criteria", ["quality", "accuracy", "completeness"])
        
        try:
            llm = get_llm()
            if llm is None:
                return {"validation_result": "Validation unavailable - no LLM configured", "score": 0}
            
            validation_prompt = f"""
            Validate the following content against these criteria: {', '.join(criteria)}
            
            Content to validate:
            {content}
            
            Please provide:
            1. Overall validation score (0-100)
            2. Assessment for each criterion
            3. Specific feedback and suggestions
            4. Pass/fail recommendation
            """
            
            response = await llm.ainvoke(validation_prompt)
            
            return {
                "validation_result": response.content if hasattr(response, 'content') else str(response),
                "criteria": criteria,
                "content_validated": content,
                "score": 85  # Could be extracted from response
            }
            
        except Exception as e:
            logger.error(f"Validation task failed: {e}")
            return {
                "validation_result": f"Validation failed: {e}",
                "score": 0
            }
    
    async def _execute_synthesis_task(self, task: WorkflowTask, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a synthesis task."""
        sources = inputs.get("sources", [])
        synthesis_goal = inputs.get("goal", "comprehensive synthesis")
        
        try:
            llm = get_llm()
            if llm is None:
                return {"synthesis": "Synthesis unavailable - no LLM configured"}
            
            synthesis_prompt = f"""
            Synthesize the following information to achieve: {synthesis_goal}
            
            Sources:
            {json.dumps(sources, indent=2)}
            
            Please create a comprehensive synthesis that:
            1. Integrates key insights from all sources
            2. Identifies patterns and connections
            3. Provides a unified perspective
            4. Highlights important conclusions
            """
            
            response = await llm.ainvoke(synthesis_prompt)
            
            return {
                "synthesis": response.content if hasattr(response, 'content') else str(response),
                "sources_count": len(sources),
                "goal": synthesis_goal
            }
            
        except Exception as e:
            logger.error(f"Synthesis task failed: {e}")
            return {
                "synthesis": f"Synthesis failed: {e}",
                "sources_count": len(sources)
            }
    
    async def _execute_decision_task(self, task: WorkflowTask, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a decision-making task."""
        options = inputs.get("options", [])
        criteria = inputs.get("decision_criteria", [])
        context = inputs.get("context", "")
        
        try:
            llm = get_llm()
            if llm is None:
                return {"decision": "Decision making unavailable - no LLM configured", "recommendation": None}
            
            decision_prompt = f"""
            Make a decision based on the following:
            
            Context: {context}
            Options: {json.dumps(options, indent=2)}
            Decision Criteria: {', '.join(criteria)}
            
            Please provide:
            1. Recommended decision
            2. Reasoning and justification
            3. Risk assessment
            4. Alternative considerations
            5. Implementation suggestions
            """
            
            response = await llm.ainvoke(decision_prompt)
            
            return {
                "decision": response.content if hasattr(response, 'content') else str(response),
                "options_considered": len(options),
                "criteria": criteria,
                "recommendation": "Option 1"  # Could be extracted from response
            }
            
        except Exception as e:
            logger.error(f"Decision task failed: {e}")
            return {
                "decision": f"Decision making failed: {e}",
                "recommendation": None
            }
    
    async def _execute_parallel_task(self, task: WorkflowTask, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Execute parallel subtasks."""
        subtasks = task.metadata.get("subtasks", [])
        
        if not subtasks:
            return {"results": [], "message": "No subtasks defined"}
        
        # Execute all subtasks in parallel
        parallel_executions = []
        for subtask in subtasks:
            subtask_inputs = inputs.copy()
            subtask_inputs.update(subtask.get("inputs", {}))
            
            # Create a simple task for each subtask
            simple_task = WorkflowTask(
                id=f"{task.id}_{subtask['name']}",
                type=TaskType.RESEARCH,  # Default type
                name=subtask["name"],
                description=subtask.get("description", ""),
                inputs=subtask_inputs,
                outputs={},
                dependencies=[],
                agent_requirements=[],
                timeout=task.timeout // len(subtasks),
                retry_count=0,
                max_retries=1,
                status=WorkflowStatus.PENDING,
                created_at=time.time()
            )
            
            execution = self._execute_research_task(simple_task, subtask_inputs)
            parallel_executions.append((subtask["name"], execution))
        
        # Wait for all to complete
        results = {}
        for name, execution in parallel_executions:
            try:
                result = await execution
                results[name] = result
            except Exception as e:
                results[name] = {"error": str(e)}
        
        return {
            "results": results,
            "subtasks_completed": len(results),
            "subtasks_total": len(subtasks)
        }
    
    async def _execute_conditional_task(self, task: WorkflowTask, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Execute conditional logic task."""
        condition = task.metadata.get("condition", "true")
        true_action = task.metadata.get("true_action", {})
        false_action = task.metadata.get("false_action", {})
        
        # Simple condition evaluation (could be enhanced)
        condition_result = self._evaluate_condition(condition, inputs)
        
        action = true_action if condition_result else false_action
        
        if not action:
            return {"condition_result": condition_result, "action_taken": None}
        
        # Execute the chosen action
        action_type = TaskType(action.get("type", TaskType.GENERATION))
        action_inputs = inputs.copy()
        action_inputs.update(action.get("inputs", {}))
        
        if action_type in self.task_executors:
            executor = self.task_executors[action_type]
            result = await executor(task, action_inputs)
            
            return {
                "condition_result": condition_result,
                "action_taken": action_type,
                "result": result
            }
        
        return {
            "condition_result": condition_result,
            "action_taken": None,
            "error": f"No executor for action type: {action_type}"
        }
    
    def _evaluate_condition(self, condition: str, inputs: Dict[str, Any]) -> bool:
        """Evaluate a simple condition (could be enhanced with proper expression parser)."""
        # Simple condition evaluation - in production, use a proper expression parser
        try:
            # Replace input references
            for key, value in inputs.items():
                condition = condition.replace(f"${key}", str(value))
            
            # Basic evaluation (unsafe - use proper parser in production)
            return eval(condition) if condition else True
        except:
            return True
    
    def get_workflow_status(self, workflow_id: str) -> Dict[str, Any]:
        """Get detailed workflow status."""
        if workflow_id not in self.workflows:
            return {"error": "Workflow not found"}
        
        workflow = self.workflows[workflow_id]
        
        return {
            "workflow": asdict(workflow),
            "progress": {
                "total_tasks": len(workflow.tasks),
                "completed_tasks": len([t for t in workflow.tasks if t.status == WorkflowStatus.COMPLETED]),
                "failed_tasks": len([t for t in workflow.tasks if t.status == WorkflowStatus.FAILED]),
                "running_tasks": len([t for t in workflow.tasks if t.status == WorkflowStatus.RUNNING])
            },
            "is_running": workflow_id in self.running_workflows
        }
    
    def list_workflows(self) -> Dict[str, Any]:
        """List all workflows with summary information."""
        workflows_summary = []
        
        for workflow_id, workflow in self.workflows.items():
            summary = {
                "id": workflow_id,
                "name": workflow.name,
                "status": workflow.status,
                "created_at": workflow.created_at,
                "task_count": len(workflow.tasks),
                "is_running": workflow_id in self.running_workflows
            }
            workflows_summary.append(summary)
        
        return {
            "workflows": workflows_summary,
            "total_workflows": len(workflows_summary),
            "running_workflows": len(self.running_workflows),
            "templates_available": list(self.workflow_templates.keys())
        }


# Global instance
advanced_workflow_engine = AdvancedWorkflowEngine()


def get_workflow_engine() -> AdvancedWorkflowEngine:
    """Get the global workflow engine instance."""
    return advanced_workflow_engine
