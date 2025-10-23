"""
Skill Tree Endpoints - Phase 2

REST API endpoints for skill tree and skill node management.
"""

from fastapi import APIRouter, HTTPException, Depends, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import logging

from app.database.database import get_db
from app.models.skill_tree import (
    SkillTree,
    SkillNode,
    SkillTreeCreate,
    SkillTreeUpdate,
    SkillTreeResponse,
    SkillNodeCreate,
    SkillNodeUpdate,
    SkillNodeResponse,
)
from app.models.specialization import SpecializationType
from app.services.skill_tree_service import SkillTreeService

logger = logging.getLogger(__name__)
router = APIRouter()


# ============================================================================
# Skill Tree Endpoints
# ============================================================================

@router.post("/skill-trees", response_model=SkillTreeResponse, tags=["Skill Trees"])
async def create_skill_tree(
    tree: SkillTreeCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new skill tree.
    
    **Parameters:**
    - `tree`: Skill tree configuration
    
    **Returns:** Created skill tree
    """
    try:
        result = SkillTreeService.create_skill_tree(db, tree)
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error creating skill tree: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create skill tree: {str(e)}"
        )


@router.get("/skill-trees/{tree_id}", response_model=SkillTreeResponse, tags=["Skill Trees"])
async def get_skill_tree(
    tree_id: str,
    db: Session = Depends(get_db)
):
    """
    Get a skill tree by ID.
    
    **Parameters:**
    - `tree_id`: Skill tree ID
    
    **Returns:** Skill tree or 404 if not found
    """
    tree = SkillTreeService.get_skill_tree(db, tree_id)
    if not tree:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Skill tree not found: {tree_id}"
        )
    return tree


@router.get("/skill-trees", response_model=List[SkillTreeResponse], tags=["Skill Trees"])
async def get_skill_trees_by_specialization(
    specialization: SpecializationType,
    include_custom: bool = Query(True, description="Include custom skill trees"),
    public_only: bool = Query(False, description="Only return public skill trees"),
    db: Session = Depends(get_db)
):
    """
    Get all skill trees for a specialization.
    
    **Parameters:**
    - `specialization`: Specialization type
    - `include_custom`: Include custom trees (default: true)
    - `public_only`: Only return public trees (default: false)
    
    **Returns:** List of skill trees
    """
    trees = SkillTreeService.get_skill_trees_by_specialization(
        db, specialization, include_custom, public_only
    )
    return trees


@router.put("/skill-trees/{tree_id}", response_model=SkillTreeResponse, tags=["Skill Trees"])
async def update_skill_tree(
    tree_id: str,
    tree: SkillTreeUpdate,
    db: Session = Depends(get_db)
):
    """
    Update a skill tree.
    
    **Parameters:**
    - `tree_id`: Skill tree ID
    - `tree`: Updated skill tree data
    
    **Returns:** Updated skill tree
    """
    try:
        result = SkillTreeService.update_skill_tree(db, tree_id, tree)
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error updating skill tree: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update skill tree: {str(e)}"
        )


@router.delete("/skill-trees/{tree_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Skill Trees"])
async def delete_skill_tree(
    tree_id: str,
    db: Session = Depends(get_db)
):
    """
    Delete a skill tree (and all its nodes).
    
    **Parameters:**
    - `tree_id`: Skill tree ID
    
    **Returns:** 204 No Content on success, 404 if not found
    """
    success = SkillTreeService.delete_skill_tree(db, tree_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Skill tree not found: {tree_id}"
        )


# ============================================================================
# Skill Node Endpoints
# ============================================================================

@router.post("/skill-trees/{tree_id}/nodes", response_model=SkillNodeResponse, tags=["Skill Trees"])
async def create_skill_node(
    tree_id: str,
    node: SkillNodeCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new skill node in a tree.
    
    **Parameters:**
    - `tree_id`: Skill tree ID
    - `node`: Skill node configuration
    
    **Returns:** Created skill node
    """
    try:
        result = SkillTreeService.create_skill_node(db, tree_id, node)
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error creating skill node: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create skill node: {str(e)}"
        )


@router.get("/skill-nodes/{node_id}", response_model=SkillNodeResponse, tags=["Skill Trees"])
async def get_skill_node(
    node_id: str,
    db: Session = Depends(get_db)
):
    """
    Get a skill node by ID.
    
    **Parameters:**
    - `node_id`: Skill node ID
    
    **Returns:** Skill node or 404 if not found
    """
    node = SkillTreeService.get_skill_node(db, node_id)
    if not node:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Skill node not found: {node_id}"
        )
    return node


@router.get("/skill-trees/{tree_id}/nodes", response_model=List[SkillNodeResponse], tags=["Skill Trees"])
async def get_skill_nodes_by_tree(
    tree_id: str,
    db: Session = Depends(get_db)
):
    """
    Get all skill nodes in a tree.
    
    **Parameters:**
    - `tree_id`: Skill tree ID
    
    **Returns:** List of skill nodes
    """
    nodes = SkillTreeService.get_skill_nodes_by_tree(db, tree_id)
    return nodes


@router.put("/skill-nodes/{node_id}", response_model=SkillNodeResponse, tags=["Skill Trees"])
async def update_skill_node(
    node_id: str,
    node: SkillNodeUpdate,
    db: Session = Depends(get_db)
):
    """
    Update a skill node.
    
    **Parameters:**
    - `node_id`: Skill node ID
    - `node`: Updated skill node data
    
    **Returns:** Updated skill node
    """
    try:
        result = SkillTreeService.update_skill_node(db, node_id, node)
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error updating skill node: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update skill node: {str(e)}"
        )


@router.delete("/skill-nodes/{node_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Skill Trees"])
async def delete_skill_node(
    node_id: str,
    db: Session = Depends(get_db)
):
    """
    Delete a skill node.
    
    **Parameters:**
    - `node_id`: Skill node ID
    
    **Returns:** 204 No Content on success, 404 if not found
    """
    success = SkillTreeService.delete_skill_node(db, node_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Skill node not found: {node_id}"
        )

