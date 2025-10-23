"""
Memory Guild API Endpoints - Level 1 Component

API endpoints for the Memory Coordinator Agent.
Provides unified memory operations across short-term and long-term storage.

Part of DRYAD.AI Agent Evolution Architecture Level 1.
"""

from typing import Dict, Any, Optional, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from app.database.database import get_db
from app.services.memory_guild.coordinator import (
    MemoryCoordinatorAgent, MemoryRequest, MemoryResponse,
    MemoryType, MemoryOperation
)
from app.services.logging.logger import StructuredLogger
from app.core.security import get_current_user

router = APIRouter(prefix="/memory", tags=["memory"])
logger = StructuredLogger("memory_api")


# API Schemas
class MemoryStoreRequest(BaseModel):
    """Schema for storing memory."""
    key: str = Field(..., description="Memory key identifier")
    value: Dict[str, Any] = Field(..., description="Memory value data")
    memory_type: MemoryType = Field(MemoryType.SHORT_TERM, description="Type of memory storage")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")
    ttl_seconds: Optional[int] = Field(None, description="Time to live in seconds")


class MemoryRetrieveRequest(BaseModel):
    """Schema for retrieving memory."""
    key: str = Field(..., description="Memory key identifier")
    memory_type: Optional[MemoryType] = Field(None, description="Preferred memory type")


class MemorySearchRequest(BaseModel):
    """Schema for searching memory."""
    query: str = Field(..., description="Search query")
    memory_type: MemoryType = Field(MemoryType.LONG_TERM, description="Memory type to search")
    limit: Optional[int] = Field(10, description="Maximum number of results")


class MemoryArchiveRequest(BaseModel):
    """Schema for archiving memory."""
    key: str = Field(..., description="Memory key to archive")


class MemoryDeleteRequest(BaseModel):
    """Schema for deleting memory."""
    key: str = Field(..., description="Memory key to delete")
    memory_type: Optional[MemoryType] = Field(None, description="Memory type to delete from")


class MemoryPolicyResponse(BaseModel):
    """Schema for memory policy response."""
    tenant_id: str
    short_term_ttl: int
    long_term_enabled: bool
    max_memory_size: int
    retention_days: int


@router.post("/store", response_model=MemoryResponse)
async def store_memory(
    request: MemoryStoreRequest,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Store memory in the Memory Guild.
    
    Routes to appropriate storage based on memory type:
    - SHORT_TERM: Fast cache storage (Redis)
    - LONG_TERM: Persistent vector storage
    - WORKING: Both short-term and long-term
    """
    try:
        coordinator = MemoryCoordinatorAgent(db)
        
        memory_request = MemoryRequest(
            operation=MemoryOperation.STORE,
            memory_type=request.memory_type,
            key=request.key,
            value=request.value,
            metadata=request.metadata,
            tenant_id=current_user.get("tenant_id", "default"),
            agent_id=current_user.get("agent_id"),
            ttl_seconds=request.ttl_seconds
        )
        
        logger.log_info(
            "memory_store_request",
            {
                "key": request.key,
                "memory_type": request.memory_type,
                "user_id": current_user.get("user_id"),
                "tenant_id": current_user.get("tenant_id")
            }
        )
        
        result = await coordinator.handle_memory_request(memory_request)
        return result
        
    except ValueError as e:
        logger.log_warning(
            "memory_store_validation_error",
            {"error": str(e), "key": request.key}
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.log_error(
            "memory_store_error",
            {"error": str(e), "key": request.key}
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to store memory"
        )


@router.post("/retrieve", response_model=MemoryResponse)
async def retrieve_memory(
    request: MemoryRetrieveRequest,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Retrieve memory from the Memory Guild.
    
    Searches short-term storage first for speed, then falls back to long-term.
    """
    try:
        coordinator = MemoryCoordinatorAgent(db)
        
        memory_request = MemoryRequest(
            operation=MemoryOperation.RETRIEVE,
            memory_type=request.memory_type or MemoryType.WORKING,
            key=request.key,
            tenant_id=current_user.get("tenant_id", "default"),
            agent_id=current_user.get("agent_id")
        )
        
        logger.log_info(
            "memory_retrieve_request",
            {
                "key": request.key,
                "memory_type": request.memory_type,
                "user_id": current_user.get("user_id")
            }
        )
        
        result = await coordinator.handle_memory_request(memory_request)
        return result
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.log_error(
            "memory_retrieve_error",
            {"error": str(e), "key": request.key}
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve memory"
        )


@router.post("/search", response_model=MemoryResponse)
async def search_memory(
    request: MemorySearchRequest,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Search memory using semantic similarity.
    
    Primarily searches long-term vector storage for semantic matches.
    """
    try:
        coordinator = MemoryCoordinatorAgent(db)
        
        memory_request = MemoryRequest(
            operation=MemoryOperation.SEARCH,
            memory_type=request.memory_type,
            query=request.query,
            tenant_id=current_user.get("tenant_id", "default"),
            agent_id=current_user.get("agent_id"),
            metadata={"limit": request.limit}
        )
        
        logger.log_info(
            "memory_search_request",
            {
                "query": request.query[:100],  # Truncate for logging
                "memory_type": request.memory_type,
                "limit": request.limit,
                "user_id": current_user.get("user_id")
            }
        )
        
        result = await coordinator.handle_memory_request(memory_request)
        return result
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.log_error(
            "memory_search_error",
            {"error": str(e), "query": request.query[:50]}
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to search memory"
        )


@router.post("/archive", response_model=MemoryResponse)
async def archive_memory(
    request: MemoryArchiveRequest,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Archive memory from short-term to long-term storage.
    
    Moves memory from fast cache to persistent vector storage.
    """
    try:
        coordinator = MemoryCoordinatorAgent(db)
        
        memory_request = MemoryRequest(
            operation=MemoryOperation.ARCHIVE,
            memory_type=MemoryType.SHORT_TERM,  # Source is always short-term
            key=request.key,
            tenant_id=current_user.get("tenant_id", "default"),
            agent_id=current_user.get("agent_id")
        )
        
        logger.log_info(
            "memory_archive_request",
            {
                "key": request.key,
                "user_id": current_user.get("user_id")
            }
        )
        
        result = await coordinator.handle_memory_request(memory_request)
        return result
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.log_error(
            "memory_archive_error",
            {"error": str(e), "key": request.key}
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to archive memory"
        )


@router.delete("/delete", response_model=MemoryResponse)
async def delete_memory(
    request: MemoryDeleteRequest,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Delete memory from storage.
    
    Removes memory from specified storage type or both if WORKING type.
    """
    try:
        coordinator = MemoryCoordinatorAgent(db)
        
        memory_request = MemoryRequest(
            operation=MemoryOperation.DELETE,
            memory_type=request.memory_type or MemoryType.WORKING,
            key=request.key,
            tenant_id=current_user.get("tenant_id", "default"),
            agent_id=current_user.get("agent_id")
        )
        
        logger.log_info(
            "memory_delete_request",
            {
                "key": request.key,
                "memory_type": request.memory_type,
                "user_id": current_user.get("user_id")
            }
        )
        
        result = await coordinator.handle_memory_request(memory_request)
        return result
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.log_error(
            "memory_delete_error",
            {"error": str(e), "key": request.key}
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete memory"
        )


@router.get("/policy", response_model=MemoryPolicyResponse)
async def get_memory_policy(
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Get the current memory policy for the tenant.
    
    Returns policy configuration including TTL, limits, and permissions.
    """
    try:
        coordinator = MemoryCoordinatorAgent(db)
        tenant_id = current_user.get("tenant_id", "default")
        
        policy = await coordinator._get_memory_policy(tenant_id)
        
        return MemoryPolicyResponse(
            tenant_id=policy.tenant_id,
            short_term_ttl=policy.short_term_ttl,
            long_term_enabled=policy.long_term_enabled,
            max_memory_size=policy.max_memory_size,
            retention_days=policy.retention_days
        )
        
    except Exception as e:
        logger.log_error(
            "memory_policy_error",
            {"error": str(e), "tenant_id": current_user.get("tenant_id")}
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get memory policy"
        )
