from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from dryad.domain.agent.models import Agent
from dryad.domain.user.models import User

class AgentFactory:
    def __init__(self, db: AsyncSession):
        self.db = db
        
    async def create_agent(
        self, 
        name: str, 
        system_prompt: str,
        user: User,
        model_name: str = "gpt-4o",
        description: str = None
    ) -> Agent:
        """
        Factory method to create a new Agent.
        """
        agent = Agent(
            name=name,
            system_prompt=system_prompt,
            model_name=model_name,
            description=description,
            created_by=user.id
        )
        self.db.add(agent)
        await self.db.commit()
        await self.db.refresh(agent)
        return agent

    async def list_agents(self) -> list[Agent]:
        stmt = select(Agent)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
