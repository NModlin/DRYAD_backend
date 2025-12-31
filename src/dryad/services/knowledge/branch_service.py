from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from dryad.domain.knowledge.models import Branch, Vessel
from dryad.domain.knowledge.schemas import BranchCreate, BranchUpdate

class BranchService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_branch(self, branch_id: str) -> Optional[Branch]:
        # Eager load vessel
        stmt = select(Branch).options(selectinload(Branch.vessel)).where(Branch.id == branch_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def list_branches_in_grove(self, grove_id: str, parent_id: Optional[str] = None) -> List[Branch]:
        stmt = select(Branch).options(selectinload(Branch.vessel)).where(Branch.grove_id == grove_id)
        if parent_id:
            stmt = stmt.where(Branch.parent_id == parent_id)
        else:
            # List root branches if parent_id is None? 
            # Or list all if not specified. Let's make it optional filter.
            # If explicit None passed, we might want Key "is None"
            pass
            
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def create_branch(self, branch_in: BranchCreate) -> Branch:
        branch = Branch(**branch_in.model_dump())
        self.db.add(branch)
        await self.db.flush() # flush to get ID
        
        # Auto-create Vessel
        vessel = Vessel(branch_id=branch.id)
        self.db.add(vessel)
        
        await self.db.commit()
        await self.db.refresh(branch) 
        # Need to reload to get vessel
        return await self.get_branch(branch.id)

    async def update_branch(self, branch_id: str, branch_in: BranchUpdate) -> Optional[Branch]:
        branch = await self.get_branch(branch_id)
        if not branch:
            return None
            
        update_data = branch_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(branch, field, value)
            
        self.db.add(branch)
        await self.db.commit()
        await self.db.refresh(branch)
        return branch
