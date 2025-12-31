from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from dryad.domain.knowledge.models import Grove
from dryad.domain.knowledge.schemas import GroveCreate, GroveUpdate

class GroveService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_grove(self, grove_id: str) -> Optional[Grove]:
        stmt = select(Grove).where(Grove.id == grove_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def list_groves(self, skip: int = 0, limit: int = 100) -> List[Grove]:
        stmt = select(Grove).offset(skip).limit(limit)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def create_grove(self, grove_in: GroveCreate) -> Grove:
        grove = Grove(**grove_in.model_dump())
        self.db.add(grove)
        await self.db.commit()
        await self.db.refresh(grove)
        return grove

    async def update_grove(self, grove_id: str, grove_in: GroveUpdate) -> Optional[Grove]:
        grove = await self.get_grove(grove_id)
        if not grove:
            return None
            
        update_data = grove_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(grove, field, value)
            
        self.db.add(grove)
        await self.db.commit()
        await self.db.refresh(grove)
        return grove

    async def delete_grove(self, grove_id: str) -> bool:
        grove = await self.get_grove(grove_id)
        if not grove:
            return False
            
        await self.db.delete(grove)
        await self.db.commit()
        return True
