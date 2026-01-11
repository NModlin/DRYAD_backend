"""
Task Decomposition Module

Decomposes complex user requests into smaller, manageable subtasks
that can be delegated to specialist agents.
"""

import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum
from langchain.prompts import ChatPromptTemplate
from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field

from dryad.core.llm_config import get_llm

logger = logging.getLogger(__name__)


class TaskComplexity(str, Enum):
    """Task complexity levels."""
    SIMPLE = "simple"  # Single agent can handle
    MODERATE = "moderate"  # 2-3 agents needed
    COMPLEX = "complex"  # Multiple agents, coordination required
    VERY_COMPLEX = "very_complex"  # Full orchestration needed


class TaskCategory(str, Enum):
    """Task categories for agent selection."""
    CODE_ANALYSIS = "code_analysis"
    CODE_GENERATION = "code_generation"
    CODE_MODIFICATION = "code_modification"
    TESTING = "testing"
    DOCUMENTATION = "documentation"
    SECURITY = "security"
    DATABASE = "database"
    API_INTEGRATION = "api_integration"
    PERFORMANCE = "performance"
    DEPLOYMENT = "deployment"
    DEBUGGING = "debugging"
    RESEARCH = "research"
    PROJECT_MANAGEMENT = "project_management"
    QUALITY_ASSURANCE = "qa"
    MIXED = "mixed"


@dataclass
class Subtask:
    """Represents a decomposed subtask."""
    id: str
    description: str
    category: TaskCategory
    required_capabilities: List[str]
    dependencies: List[str]  # IDs of subtasks that must complete first
    priority: int  # 1-5, higher is more important
    estimated_complexity: TaskComplexity
    context: Dict[str, Any]  # Additional context for the subtask


class DecomposedTask(BaseModel):
    """Pydantic model for LLM output parsing."""
    complexity: TaskComplexity = Field(description="Overall task complexity")
    subtasks: List[Dict[str, Any]] = Field(description="List of subtasks")
    execution_order: List[str] = Field(description="Recommended execution order (subtask IDs)")
    reasoning: str = Field(description="Explanation of the decomposition")


class TaskDecomposer:
    """
    Decomposes complex tasks into subtasks using LLM reasoning.
    """
    
    def __init__(self):
        """Initialize the task decomposer."""
        self.llm = get_llm()
        self.parser = PydanticOutputParser(pydantic_object=DecomposedTask)
        
        # Task decomposition prompt
        self.decomposition_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert task decomposition AI for a software development system.
Your job is to break down complex user requests into smaller, manageable subtasks.

Available agent capabilities:
- code_analysis: Analyze existing code, understand architecture
- code_generation: Generate new code from scratch
- code_modification: Modify existing code
- testing: Write and run tests
- documentation: Create documentation
- security: Security analysis and vulnerability scanning
- database: Database operations and schema management
- api_integration: External API integrations
- performance: Performance optimization
- deployment: Deployment and CI/CD
- debugging: Error analysis and debugging
- research: Documentation search and research
- project_management: Task coordination and planning
- quality_assurance: Quality checks and validation

Task complexity levels:
- simple: Single agent can handle (1 subtask)
- moderate: 2-3 agents needed (2-3 subtasks)
- complex: Multiple agents, coordination required (4-6 subtasks)
- very_complex: Full orchestration needed (7+ subtasks)

{format_instructions}

Provide a detailed decomposition with:
1. Overall complexity assessment
2. List of subtasks with:
   - id: Unique identifier (e.g., "task_1", "task_2")
   - description: Clear description of what needs to be done
   - category: Task category from the list above
   - required_capabilities: List of capabilities needed
   - dependencies: List of subtask IDs that must complete first
   - priority: 1-5 (higher is more important)
   - estimated_complexity: Complexity of this specific subtask
   - context: Any additional context needed
3. Execution order: Recommended order of execution
4. Reasoning: Explain your decomposition strategy
"""),
            ("human", "User request: {user_request}\n\nAdditional context: {context}")
        ])
    
    async def decompose_task(
        self,
        user_request: str,
        context: Optional[Dict[str, Any]] = None
    ) -> List[Subtask]:
        """
        Decompose a user request into subtasks.
        
        Args:
            user_request: The user's request
            context: Additional context about the request
            
        Returns:
            List of Subtask objects
        """
        try:
            logger.info(f"Decomposing task: {user_request[:100]}...")
            
            # Prepare the prompt
            prompt = self.decomposition_prompt.format_messages(
                user_request=user_request,
                context=context or {},
                format_instructions=self.parser.get_format_instructions()
            )
            
            # Get LLM response
            response = await self.llm.ainvoke(prompt)
            
            # Parse the response
            decomposed = self.parser.parse(response.content)
            
            # Convert to Subtask objects
            subtasks = []
            for subtask_data in decomposed.subtasks:
                subtask = Subtask(
                    id=subtask_data.get("id", f"task_{len(subtasks) + 1}"),
                    description=subtask_data.get("description", ""),
                    category=TaskCategory(subtask_data.get("category", "mixed")),
                    required_capabilities=subtask_data.get("required_capabilities", []),
                    dependencies=subtask_data.get("dependencies", []),
                    priority=subtask_data.get("priority", 3),
                    estimated_complexity=TaskComplexity(
                        subtask_data.get("estimated_complexity", "simple")
                    ),
                    context=subtask_data.get("context", {})
                )
                subtasks.append(subtask)
            
            logger.info(
                f"Task decomposed into {len(subtasks)} subtasks "
                f"(complexity: {decomposed.complexity})"
            )
            logger.debug(f"Decomposition reasoning: {decomposed.reasoning}")
            
            return subtasks
            
        except Exception as e:
            logger.error(f"Task decomposition failed: {e}")
            # Fallback: Create a single subtask for the entire request
            return [
                Subtask(
                    id="task_1",
                    description=user_request,
                    category=TaskCategory.MIXED,
                    required_capabilities=["code_analysis", "code_generation"],
                    dependencies=[],
                    priority=3,
                    estimated_complexity=TaskComplexity.MODERATE,
                    context=context or {}
                )
            ]
    
    def get_execution_plan(self, subtasks: List[Subtask]) -> List[List[str]]:
        """
        Create an execution plan respecting dependencies.
        
        Args:
            subtasks: List of subtasks
            
        Returns:
            List of execution waves (each wave contains subtask IDs that can run in parallel)
        """
        # Build dependency graph
        task_map = {task.id: task for task in subtasks}
        completed = set()
        execution_plan = []
        
        while len(completed) < len(subtasks):
            # Find tasks that can be executed (all dependencies met)
            ready_tasks = []
            for task in subtasks:
                if task.id not in completed:
                    deps_met = all(dep in completed for dep in task.dependencies)
                    if deps_met:
                        ready_tasks.append(task.id)
            
            if not ready_tasks:
                # Circular dependency or error - break it
                remaining = [t.id for t in subtasks if t.id not in completed]
                logger.warning(f"Circular dependency detected, forcing execution of: {remaining}")
                ready_tasks = remaining
            
            # Sort by priority (higher first)
            ready_tasks.sort(
                key=lambda tid: task_map[tid].priority,
                reverse=True
            )
            
            execution_plan.append(ready_tasks)
            completed.update(ready_tasks)
        
        logger.info(f"Execution plan created: {len(execution_plan)} waves")
        return execution_plan


# Global task decomposer instance
task_decomposer = TaskDecomposer()

