from typing import List, Dict, Any, Optional
import logging
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage

from dryad.domain.agent.models import Agent
from dryad.domain.tool.models import Tool
from dryad.services.tool_registry import ToolRegistryService
from dryad.infrastructure.llm.factory import LLMFactory
from dryad.infrastructure.llm.providers import LLMConfig

logger = logging.getLogger(__name__)

class AgentRunner:
    """
    Executes an Agent's logic loop.
    """
    def __init__(self, db: AsyncSession, agent_id: str):
        self.db = db
        self.agent_id = agent_id
        self.agent: Optional[Agent] = None
        self.llm = None
        self.tools: List[Tool] = []

    async def initialize(self):
        """
        Load agent config and initialize LLM.
        """
        # Load Agent
        stmt = select(Agent).where(Agent.id == self.agent_id)
        result = await self.db.execute(stmt)
        self.agent = result.scalar_one_or_none()
        
        if not self.agent:
            raise ValueError(f"Agent {self.agent_id} not found")

        # Load Tools (mock logic for ID mapping for now)
        # In real impl, we'd fetch tools by IDs in self.agent.tool_ids
        
        # Init LLM
        config = LLMConfig(
            provider=self.agent.model_provider,
            model_name=self.agent.model_name,
            temperature=self.agent.temperature
        )
        self.llm = LLMFactory.create_model(config)

    async def chat(self, user_message: str, history: List[Dict[str, str]] = None) -> str:
        """
        Send a message to the agent and get a response.
        """
        if not self.llm:
            await self.initialize()

        # Build Prompt
        messages = [
            SystemMessage(content=self.agent.system_prompt)
        ]
        
        # Add History (Simplistic implementation)
        if history:
            for msg in history:
                if msg["role"] == "user":
                    messages.append(HumanMessage(content=msg["content"]))
                elif msg["role"] == "assistant":
                    messages.append(AIMessage(content=msg["content"]))
        
        # Add current message
        messages.append(HumanMessage(content=user_message))
        
        # Invoke LLM
        # Note: True tool usage requires bind_tools here
        response = await self.llm.ainvoke(messages)
        
        return response.content
