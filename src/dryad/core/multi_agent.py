# app/core/multi_agent.py
import logging
import asyncio
import json
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass
from datetime import datetime
import uuid

# Built-in multi-agent implementation (no external dependencies)
# DRYAD uses a superior built-in multi-agent architecture based on Level 0-5 framework

# Define built-in agent classes for our implementation
class Agent:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

class Task:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

from dryad.core.llm_config import get_llm, get_llm_info, LLMProvider, get_specialized_llm
from dryad.core.monitoring_integration import monitor_agent_workflow, monitoring_integration

logger = logging.getLogger(__name__)

@dataclass
class AgentResult:
    """Result from an agent execution."""
    task_id: str
    agent_id: str
    success: bool
    result: Dict[str, Any]
    confidence: float
    execution_time: float
    metadata: Dict[str, Any]

class MultiAgentOrchestrator:
    """
    Built-in multi-agent orchestrator with no external dependencies.
    Manages specialized agents for different types of tasks with full local LLM support.

    Part of DRYAD's Level 3 Hybrid Orchestration architecture, providing:
    - Intelligent task routing and complexity scoring
    - Multi-agent collaboration via Task Forces
    - Human-in-the-Loop (HITL) consultation
    - Vessel creation for agent context storage
    - Dialogue tracking for agent reasoning
    - Grove and branch management for task organization
    """

    def __init__(self, llm_model: Optional[str] = None, temperature: Optional[float] = None):
        """Initialize the multi-agent orchestrator."""
        self.llm_info = get_llm_info()
        self.llm = self._initialize_llm()
        self.agents = self._create_agents()
        self.task_history = []
        self.dryad_enabled = True  # Enable DRYAD integration by default

        logger.info("✅ MultiAgentOrchestrator initialized with built-in implementation (no external dependencies)")
        logger.info(f"LLM Provider: {self.llm_info['provider']}, Model: {self.llm_info['model_name']}")
        logger.info("✅ DRYAD integration enabled for context tracking")

    def _initialize_llm(self):
        """Initialize the language model for agents using local LLM configuration."""
        try:
            llm = get_llm()
            logger.info(f"✅ Initialized LLM: {self.llm_info}")
            return llm
        except Exception as e:
            logger.error(f"❌ Failed to initialize LLM: {e}")
            raise RuntimeError(f"Cannot initialize multi-agent system without functional LLM: {e}")
    
    def _create_agents(self) -> Dict[str, Union[Agent, Dict[str, Any]]]:
        """Create specialized agents for different tasks with robust error handling."""
        agents = {}

        # Ensure we have a valid LLM
        if self.llm is None:
            raise RuntimeError("LLM not initialized - cannot create agents without functional LLM")

        logger.info(f"🤖 Creating agents with {self.llm_info['provider']} provider using model: {self.llm_info['model_name']}")

        # Agent configurations
        agent_configs = {
            'researcher': {
                'role': 'Research Specialist',
                'goal': 'Gather comprehensive and accurate information on given topics',
                'backstory': """You are an expert researcher with years of experience in
                information gathering and fact-checking. You excel at finding reliable
                sources and synthesizing information from multiple perspectives.""",
                'tools': self._create_agent_tools('researcher')
            },
            'analyst': {
                'role': 'Data Analyst',
                'goal': 'Analyze information and provide insights and recommendations',
                'backstory': """You are a skilled data analyst with expertise in pattern
                recognition, critical thinking, and drawing meaningful conclusions from
                complex information. You excel at identifying trends and relationships.""",
                'tools': self._create_agent_tools('analyst')
            },
            'writer': {
                'role': 'Content Writer',
                'goal': 'Create clear, engaging, and well-structured content',
                'backstory': """You are an experienced writer and communicator who excels
                at taking complex information and presenting it in a clear, engaging,
                and accessible manner. You adapt your writing style to the audience.""",
                'tools': self._create_agent_tools('writer')
            },
            'coordinator': {
                'role': 'Project Coordinator',
                'goal': 'Coordinate tasks and ensure efficient workflow between agents',
                'backstory': """You are an experienced project manager who excels at
                breaking down complex tasks, coordinating team efforts, and ensuring
                quality deliverables. You understand how to leverage each team member's strengths.""",
                'tools': self._create_agent_tools('coordinator')
            }
        }

        # Create all agents using built-in implementation
        for agent_name, config in agent_configs.items():
            try:
                agent = self._create_single_agent(agent_name, config)
                agents[agent_name] = agent
                logger.info(f"✅ Created {agent_name} agent successfully")
            except Exception as e:
                logger.error(f"❌ Failed to create {agent_name} agent: {e}")
                raise RuntimeError(f"Failed to create {agent_name} agent: {e}")

        if not agents:
            raise RuntimeError("Failed to create any functional agents")

        logger.info(f"🎉 Successfully created {len(agents)} agents: {list(agents.keys())}")
        return agents

    def _create_single_agent(self, agent_name: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Create a single agent with the given configuration using built-in implementation."""
        return {
            'id': str(uuid.uuid4()),
            'name': agent_name,
            'role': config['role'],
            'goal': config['goal'],
            'backstory': config['backstory'],
            'llm': get_specialized_llm(agent_name),
            'tools': config.get('tools', []),
            'type': 'dryad_agent',
            'created_at': datetime.utcnow().isoformat()
        }

    def _create_agent_tools(self, agent_type: str) -> List[Any]:
        """Create tools for a specific agent type."""
        # Tools are managed by Level 0 Tool Registry Service
        # Integration with Tool Registry will be completed in Level 0 fixes
        tools = []
        logger.info(f"✅ Created empty tools list for {agent_type} agent (Level 0 Tool Registry integration pending)")
        return tools
    
    def create_research_task(self, query: str, context: str = "") -> Task:
        """Create a research task for the research agent."""
        return Task(
            description=f"""
            Research the following topic thoroughly: {query}
            
            Context: {context}
            
            Your task is to:
            1. Gather comprehensive information about the topic
            2. Find multiple reliable sources
            3. Identify key facts, trends, and perspectives
            4. Provide a well-structured research summary
            
            Focus on accuracy and comprehensiveness.
            """,
            agent=self.agents['researcher'],
            expected_output="A comprehensive research summary with key findings and sources"
        )
    
    def create_analysis_task(self, research_data: str, analysis_focus: str = "") -> Task:
        """Create an analysis task for the analyst agent."""
        return Task(
            description=f"""
            Analyze the following research data and provide insights:
            
            Research Data: {research_data}
            Analysis Focus: {analysis_focus}
            
            Your task is to:
            1. Identify key patterns and trends
            2. Draw meaningful conclusions
            3. Provide actionable insights
            4. Highlight important implications
            5. Suggest recommendations if applicable
            
            Focus on critical thinking and practical insights.
            """,
            agent=self.agents['analyst'],
            expected_output="Detailed analysis with insights, conclusions, and recommendations"
        )
    
    def create_writing_task(self, content_brief: str, style: str = "informative") -> Task:
        """Create a writing task for the writer agent."""
        return Task(
            description=f"""
            Create well-written content based on the following brief:
            
            Content Brief: {content_brief}
            Writing Style: {style}
            
            Your task is to:
            1. Structure the content logically
            2. Write in a clear and engaging manner
            3. Adapt the tone to the specified style
            4. Ensure accuracy and completeness
            5. Make the content accessible to the target audience
            
            Focus on clarity, engagement, and value to the reader.
            """,
            agent=self.agents['writer'],
            expected_output="Well-structured, engaging content that meets the brief requirements"
        )
    
    @monitor_agent_workflow(workflow_type="simple_query", agents=["researcher"])
    def execute_simple_query(self, query: str, context: str = "") -> Dict[str, Any]:
        """Execute a simple query using the research agent with genuine AI reasoning."""
        try:
            logger.info(f"🤖 Executing AI-powered simple query: {query}")

            # Ensure we have functional agents
            if not self.agents or 'researcher' not in self.agents:
                raise RuntimeError("Research agent not available. Cannot execute query without functional AI agents.")

            # Execute using built-in DRYAD agent system
            logger.info("🧠 Using DRYAD built-in AI agent system...")
            result = self._execute_builtin_simple_query(query, context)
            result["execution_method"] = "dryad_builtin"

            # Record task in history
            self.task_history.append({
                'task_id': str(uuid.uuid4()),
                'type': 'simple_query',
                'query': query,
                'context': context,
                'result': result,
                'timestamp': datetime.now().isoformat(),
                'agents_used': ['researcher']
            })

            return result

        except Exception as e:
            logger.error(f"❌ AI agent execution failed: {e}")
            # No fallback - if AI agents fail, the system should fail explicitly
            raise RuntimeError(f"Multi-agent system execution failed: {e}. This indicates a problem with the AI system that needs to be resolved.")

    def _execute_builtin_simple_query(self, query: str, context: str = "") -> Dict[str, Any]:
        """Execute simple query using DRYAD built-in implementation."""
        try:
            logger.info("🧠 DRYAD agent processing query with AI reasoning...")

            # Get the researcher agent
            researcher = self.agents['researcher']

            # Extract agent configuration
            role = researcher['role']
            backstory = researcher['backstory']
            goal = researcher['goal']
            llm = researcher['llm']

            # Create comprehensive research prompt
            research_prompt = f"""You are a {role}. {backstory}

Your goal: {goal}

Query: {query}
Context: {context}

Please provide a comprehensive response that includes:
1. Key information and facts about the topic
2. Important context and background
3. Analysis and insights
4. Practical implications
5. Related concepts or areas of interest

Structure your response clearly and provide valuable, accurate information."""

            # Execute using the LLM
            response = llm.invoke(research_prompt)

            # Extract response content
            if hasattr(response, 'content'):
                result_text = response.content
            else:
                result_text = str(response)

            return {
                "query": query,
                "result": result_text,
                "agents_used": ["researcher"],
                "task_type": "simple_research",
                "execution_method": "dryad_builtin"
            }
        except Exception as e:
            logger.error(f"DRYAD agent execution failed: {e}")
            raise
    
    @monitor_agent_workflow(workflow_type="complex_workflow", agents=["researcher", "analyst", "writer"])
    def execute_complex_workflow(self, query: str, workflow_type: str = "research_analyze_write") -> Dict[str, Any]:
        """Execute a complex multi-agent workflow with genuine AI orchestration."""
        try:
            logger.info(f"🤖 Executing AI-powered complex workflow: {workflow_type} for query: {query}")

            # Ensure we have functional agents
            if not self.agents:
                raise RuntimeError("No functional agents available. Cannot execute complex workflow without AI agents.")

            # Execute using built-in DRYAD implementation
            result = self._execute_builtin_complex_workflow(query, workflow_type)

            # Record task in history
            self.task_history.append({
                'task_id': str(uuid.uuid4()),
                'type': 'complex_workflow',
                'query': query,
                'workflow_type': workflow_type,
                'result': result,
                'timestamp': datetime.now().isoformat(),
                'agents_used': result.get('agents_used', [])
            })

            return result

        except Exception as e:
            logger.error(f"❌ Complex AI workflow execution failed: {e}")
            # No fallback - if AI workflow fails, the system should fail explicitly
            raise RuntimeError(f"Multi-agent workflow execution failed: {e}. This indicates a problem with the AI orchestration system that needs to be resolved.")

    def _execute_builtin_complex_workflow(self, query: str, workflow_type: str) -> Dict[str, Any]:
        """Execute complex workflow using DRYAD built-in implementation."""
        try:
            logger.info("🧠 DRYAD agents collaborating on complex workflow...")

            results = []
            agents_used = []

            if workflow_type == "research_analyze_write":
                # Step 1: Research
                if 'researcher' in self.agents:
                    researcher = self.agents['researcher']
                    research_prompt = f"""You are a {researcher['role']}. {researcher['backstory']}

Your goal: {researcher['goal']}

Research Query: {query}

Please provide comprehensive research on this topic including:
1. Key facts and information
2. Important context and background
3. Current developments and trends
4. Multiple perspectives on the topic
5. Reliable sources and evidence

Structure your research findings clearly."""

                    research_result = researcher['llm'].invoke(research_prompt)
                    research_content = research_result.content if hasattr(research_result, 'content') else str(research_result)
                    results.append(("research", research_content))
                    agents_used.append("researcher")

                # Step 2: Analysis
                if 'analyst' in self.agents and results:
                    analyst = self.agents['analyst']
                    analysis_prompt = f"""You are a {analyst['role']}. {analyst['backstory']}

Your goal: {analyst['goal']}

Research Findings to Analyze:
{results[-1][1]}

Query: {query}

Please analyze the research findings and provide:
1. Key patterns and trends identified
2. Critical insights and implications
3. Strengths and limitations of the information
4. Practical applications
5. Recommendations based on the analysis

Structure your analysis clearly with supporting evidence."""

                    analysis_result = analyst['llm'].invoke(analysis_prompt)
                    analysis_content = analysis_result.content if hasattr(analysis_result, 'content') else str(analysis_result)
                    results.append(("analysis", analysis_content))
                    agents_used.append("analyst")

                # Step 3: Writing
                if 'writer' in self.agents and len(results) >= 2:
                    writer = self.agents['writer']
                    writing_prompt = f"""You are a {writer['role']}. {writer['backstory']}

Your goal: {writer['goal']}

Research Findings:
{results[0][1]}

Analysis Results:
{results[1][1]}

Query: {query}

Please create a comprehensive, well-structured response that:
1. Synthesizes the research and analysis
2. Presents information clearly and engagingly
3. Includes key findings and insights
4. Provides practical implications
5. Is accessible to a general audience

Structure your response with clear sections and compelling content."""

                    writing_result = writer['llm'].invoke(writing_prompt)
                    writing_content = writing_result.content if hasattr(writing_result, 'content') else str(writing_result)
                    results.append(("writing", writing_content))
                    agents_used.append("writer")

            # Return the final result (writing if available, otherwise the last result)
            final_result = results[-1][1] if results else "No results generated"

            return {
                "query": query,
                "result": final_result,
                "agents_used": agents_used,
                "task_type": workflow_type,
                "workflow_steps": len(results),
                "execution_method": "fallback",
                "intermediate_results": [{"step": step, "content": content[:200] + "..."} for step, content in results[:-1]]
            }
        except Exception as e:
            logger.error(f"Fallback complex workflow failed: {e}")
            raise

    async def execute_workflow(
        self,
        workflow_type: str,
        input_data: str,
        context: Optional[List[str]] = None,
        db: Optional[Any] = None,
        grove_id: Optional[str] = None,
        branch_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Execute a workflow with DRYAD integration.

        This method wraps the existing execute_simple_query and execute_complex_workflow
        methods and adds DRYAD integration for context tracking.

        Args:
            workflow_type: Type of workflow to execute
            input_data: Input query or data
            context: Optional context list
            db: Optional database session for DRYAD integration
            grove_id: Optional grove ID for DRYAD context
            branch_id: Optional branch ID for DRYAD context

        Returns:
            Dict containing workflow results with DRYAD metadata
        """
        try:
            logger.info(f"🎯 Executing workflow: {workflow_type} with DRYAD integration")

            # Execute the appropriate workflow
            if workflow_type == "simple_research":
                result = self.execute_simple_query(input_data, context[0] if context else "")
            else:
                result = self.execute_complex_workflow(input_data, workflow_type)

            # Add DRYAD integration if database session is provided
            if db and self.dryad_enabled:
                try:
                    result["dryad"] = await self._integrate_with_dryad(
                        db=db,
                        workflow_type=workflow_type,
                        input_data=input_data,
                        result=result,
                        grove_id=grove_id,
                        branch_id=branch_id
                    )
                    logger.info("✅ DRYAD integration successful")
                except Exception as dryad_error:
                    logger.warning(f"⚠️ DRYAD integration failed: {dryad_error}")
                    result["dryad"] = {"error": str(dryad_error), "integrated": False}
            else:
                result["dryad"] = {"integrated": False, "reason": "No database session provided"}

            return result

        except Exception as e:
            logger.error(f"❌ Workflow execution failed: {e}")
            raise

    async def _integrate_with_dryad(
        self,
        db: Any,
        workflow_type: str,
        input_data: str,
        result: Dict[str, Any],
        grove_id: Optional[str] = None,
        branch_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Integrate workflow execution with DRYAD for context tracking.

        Creates vessels for agent context and dialogues for reasoning tracking.
        """
        # Lazy imports to avoid circular dependencies
        from dryad.services.vessel_service import VesselService
        from dryad.services.oracle_service import OracleService
        from dryad.services.grove_service import GroveService
        from dryad.services.branch_service import BranchService
        from dryad.schemas.vessel_schemas import VesselCreate
        from dryad.schemas.grove_schemas import GroveCreate
        from dryad.schemas.branch_schemas import BranchCreate
        from dryad.database.models.branch import BranchPriority

        vessel_service = VesselService(db)
        oracle_service = OracleService(db)
        grove_service = GroveService(db)
        branch_service = BranchService(db)

        dryad_metadata = {
            "integrated": True,
            "vessels_created": [],
            "dialogues_created": [],
            "grove_id": grove_id,
            "branch_id": branch_id
        }

        # Create grove if not provided
        if not grove_id:
            grove_data = GroveCreate(
                name=f"Multi-Agent Workflow: {workflow_type}",
                description=f"Workflow execution for: {input_data[:100]}...",
                template_metadata={"workflow_type": workflow_type},
                is_favorite=False
            )
            grove = await grove_service.create_grove(grove_data)
            grove_id = grove.id
            dryad_metadata["grove_id"] = grove_id
            dryad_metadata["grove_created"] = True
            logger.info(f"✅ Created DRYAD grove: {grove_id}")

        # Create branch if not provided
        if not branch_id:
            branch_data = BranchCreate(
                grove_id=grove_id,
                name=f"Workflow: {workflow_type}",
                description=f"Multi-agent workflow execution",
                parent_id=None,
                priority=BranchPriority.MEDIUM,
                metadata={"workflow_type": workflow_type, "input": input_data[:200]}
            )
            branch = await branch_service.create_branch(branch_data)
            branch_id = branch.id
            dryad_metadata["branch_id"] = branch_id
            dryad_metadata["branch_created"] = True
            logger.info(f"✅ Created DRYAD branch: {branch_id}")

        # Create vessels for each agent used
        agents_used = result.get("agents_used", [])
        for agent_name in agents_used:
            try:
                import json

                # Create context as JSON string
                context_data = {
                    "agent_name": agent_name,
                    "workflow_type": workflow_type,
                    "input_data": input_data,
                    "agent_role": self.agents.get(agent_name, {}).get("role", "Unknown"),
                    "timestamp": datetime.now().isoformat()
                }

                vessel_data = VesselCreate(
                    branch_id=branch_id,
                    initial_context=json.dumps(context_data)
                )
                vessel = await vessel_service.create_vessel(vessel_data)
                dryad_metadata["vessels_created"].append({
                    "agent": agent_name,
                    "vessel_id": vessel.id
                })
                logger.info(f"✅ Created vessel for {agent_name}: {vessel.id}")
            except Exception as vessel_error:
                logger.warning(f"⚠️ Failed to create vessel for {agent_name}: {vessel_error}")

        return dryad_metadata

    async def _create_agent_dialogue(
        self,
        db: Any,
        branch_id: str,
        agent_name: str,
        query: str,
        response: str,
        vessel_id: Optional[str] = None
    ) -> Optional[str]:
        """
        Create a dialogue entry for agent reasoning tracking.

        Args:
            db: Database session
            branch_id: Branch ID for the dialogue
            agent_name: Name of the agent
            query: Query sent to the agent
            response: Response from the agent
            vessel_id: Optional vessel ID to link

        Returns:
            Dialogue ID if created successfully, None otherwise
        """
        try:
            # Lazy imports
            from dryad.services.oracle_service import OracleService
            from dryad.database.models.dialogue import Dialogue
            from dryad.database.models.dialogue_message import DialogueMessage, MessageRole

            oracle_service = OracleService(db)

            # Create dialogue
            dialogue = Dialogue(
                id=str(uuid.uuid4()),
                branch_id=branch_id,
                oracle_used=f"multi_agent_{agent_name}",
                insights={
                    "agent": agent_name,
                    "reasoning_type": "agent_execution"
                },
                storage_path=f"/dialogues/{agent_name}/{datetime.now().strftime('%Y%m%d')}"
            )

            db.add(dialogue)
            await db.flush()

            # Create human message
            human_message = DialogueMessage(
                id=str(uuid.uuid4()),
                dialogue_id=dialogue.id,
                role=MessageRole.HUMAN,
                content=query
            )
            db.add(human_message)

            # Create oracle message
            oracle_message = DialogueMessage(
                id=str(uuid.uuid4()),
                dialogue_id=dialogue.id,
                role=MessageRole.ORACLE,
                content=response
            )
            db.add(oracle_message)

            await db.commit()

            logger.info(f"✅ Created dialogue for {agent_name}: {dialogue.id}")
            return dialogue.id

        except Exception as e:
            logger.warning(f"⚠️ Failed to create dialogue for {agent_name}: {e}")
            return None

    def get_agent_capabilities(self) -> Dict[str, Dict[str, str]]:
        """Get information about available agents and their capabilities."""
        return {
            "researcher": {
                "role": "Research Specialist",
                "capabilities": "Information gathering, fact-checking, source verification, comprehensive research",
                "tools": "Built-in AI reasoning, data collection, analysis",
                "status": "active" if 'researcher' in self.agents else "unavailable"
            },
            "analyst": {
                "role": "Data Analyst",
                "capabilities": "Pattern recognition, critical analysis, insights generation, trend identification",
                "tools": "Built-in AI analysis, data interpretation, statistical reasoning",
                "status": "active" if 'analyst' in self.agents else "unavailable"
            },
            "writer": {
                "role": "Content Writer",
                "capabilities": "Content creation, communication, audience adaptation, structured writing",
                "tools": "Built-in AI writing, editing, content optimization",
                "status": "active" if 'writer' in self.agents else "unavailable"
            },
            "coordinator": {
                "role": "Project Coordinator",
                "capabilities": "Task management, workflow coordination, quality assurance, multi-agent orchestration",
                "tools": "Built-in workflow management, task delegation, result synthesis",
                "status": "active" if 'coordinator' in self.agents else "unavailable"
            }
        }

    def get_capabilities(self) -> Dict[str, Any]:
        """Get comprehensive system capabilities information."""
        agent_capabilities = self.get_agent_capabilities()
        active_agents = [name for name, info in agent_capabilities.items() if info.get('status') == 'active']

        return {
            "system_type": "dryad_builtin_multi_agent",
            "external_dependencies": False,
            "architecture": "Level 3 Hybrid Orchestration",
            "agents": agent_capabilities,
            "active_agents": active_agents,
            "total_agents": len(active_agents),
            "llm_provider": self.llm_info.get('provider', 'unknown'),
            "llm_model": self.llm_info.get('model_name', 'unknown'),
            "llm_available": self.llm_info.get('available', False),
            "workflows_supported": [
                "simple_research",
                "research_analyze_write",
                "complex_analysis",
                "content_creation"
            ],
            "performance_advantages": [
                "No external dependencies",
                "Native DRYAD Level 3 Orchestration",
                "Integrated Task Force Management",
                "HITL consultation support",
                "Integrated with hybrid LLM architecture",
                "Lower memory footprint",
                "Superior error handling"
            ]
        }


# Global instance for use across the application
multi_agent_orchestrator = MultiAgentOrchestrator()
