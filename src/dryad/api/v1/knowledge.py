from typing import List, Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from dryad.infrastructure.database import get_db
from dryad.domain.knowledge.schemas import GroveResponse, GroveCreate, BranchResponse, BranchCreate
from dryad.services.knowledge.grove_service import GroveService
from dryad.services.knowledge.branch_service import BranchService
from dryad.api.v1.auth import get_current_user

router = APIRouter()

# --- Groves ---

@router.post("/groves", response_model=GroveResponse, status_code=status.HTTP_201_CREATED)
async def create_grove(
    grove_in: GroveCreate,
    current_user: Annotated[dict, Depends(get_current_user)], # Using dict or User model
    db: Annotated[AsyncSession, Depends(get_db)]
):
    service = GroveService(db)
    return await service.create_grove(grove_in)

@router.get("/groves", response_model=List[GroveResponse])
async def list_groves(
    db: Annotated[AsyncSession, Depends(get_db)],
    skip: int = 0,
    limit: int = 100
):
    service = GroveService(db)
    return await service.list_groves(skip, limit)

@router.get("/groves/{grove_id}", response_model=GroveResponse)
async def get_grove(
    grove_id: str,
    db: Annotated[AsyncSession, Depends(get_db)]
):
    service = GroveService(db)
    grove = await service.get_grove(grove_id)
    if not grove:
        raise HTTPException(status_code=404, detail="Grove not found")
    return grove

# --- Branches ---

@router.post("/branches", response_model=BranchResponse, status_code=status.HTTP_201_CREATED)
async def create_branch(
    branch_in: BranchCreate,
    db: Annotated[AsyncSession, Depends(get_db)]
):
    service = BranchService(db)
    # Validate Grove exists? DB constraint will handle it but logic check nice
    return await service.create_branch(branch_in)

@router.get("/branches/{branch_id}", response_model=BranchResponse)
async def get_branch(
    branch_id: str,
    db: Annotated[AsyncSession, Depends(get_db)]
):
    service = BranchService(db)
    branch = await service.get_branch(branch_id)
    if not branch:
        raise HTTPException(status_code=404, detail="Branch not found")
    return branch

@router.get("/groves/{grove_id}/branches", response_model=List[BranchResponse])
async def list_branches(
    grove_id: str,
    db: Annotated[AsyncSession, Depends(get_db)]
):
    service = BranchService(db)
    return await service.list_branches_in_grove(grove_id)
