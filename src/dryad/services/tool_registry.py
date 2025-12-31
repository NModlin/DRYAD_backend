from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from dryad.domain.tool.models import Tool
from dryad.domain.tool.schemas import ToolCreate, ToolUpdate

class ToolRegistryService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_tool(self, tool_id: str) -> Optional[Tool]:
        stmt = select(Tool).where(Tool.id == tool_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_tool_by_name(self, name: str) -> Optional[Tool]:
        stmt = select(Tool).where(Tool.name == name)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def list_tools(self, skip: int = 0, limit: int = 100) -> List[Tool]:
        stmt = select(Tool).offset(skip).limit(limit)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def register_tool(self, tool_in: ToolCreate) -> Tool:
        # Check if already exists
        existing = await self.get_tool_by_name(tool_in.name)
        if existing:
            raise ValueError(f"Tool with name '{tool_in.name}' already exists.")
            
        tool = Tool(**tool_in.model_dump())
        self.db.add(tool)
        await self.db.commit()
        await self.db.refresh(tool)
        return tool

    async def update_tool(self, tool_id: str, tool_in: ToolUpdate) -> Optional[Tool]:
        tool = await self.get_tool(tool_id)
        if not tool:
            return None
            
        update_data = tool_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(tool, field, value)
            
        self.db.add(tool)
        await self.db.commit()
        await self.db.refresh(tool)
        return tool

    async def delete_tool(self, tool_id: str) -> bool:
        tool = await self.get_tool(tool_id)
        if not tool:
            return False
            
        await self.db.delete(tool)
        await self.db.commit()
        return True
