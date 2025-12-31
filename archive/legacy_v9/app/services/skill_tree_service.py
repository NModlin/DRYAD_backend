"""
Skill Tree Service - Phase 2

Business logic for skill tree and skill node management.
"""

import logging
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.models.skill_tree import (
    SkillTree,
    SkillNode,
    SkillTreeCreate,
    SkillTreeUpdate,
    SkillTreeResponse,
    SkillNodeCreate,
    SkillNodeUpdate,
    SkillNodeResponse,
    SkillTreeVisualization,
)
from app.models.specialization import SpecializationType

logger = logging.getLogger(__name__)


class SkillTreeService:
    """Service for managing skill trees and skill nodes."""

    # ========================================================================
    # Skill Tree CRUD Operations
    # ========================================================================

    @staticmethod
    def create_skill_tree(
        db: Session,
        tree_data: SkillTreeCreate
    ) -> SkillTree:
        """
        Create a new skill tree.
        
        Args:
            db: Database session
            tree_data: Skill tree data
            
        Returns:
            Created SkillTree instance
        """
        tree = SkillTree(
            name=tree_data.name,
            description=tree_data.description,
            specialization=tree_data.specialization,
            is_custom=tree_data.is_custom,
            creator_id=tree_data.creator_id,
            is_public=tree_data.is_public,
        )
        
        try:
            db.add(tree)
            db.commit()
            db.refresh(tree)
            logger.info(f"Created skill tree: {tree.name} ({tree.specialization.value})")
            return tree
        except IntegrityError as e:
            db.rollback()
            logger.error(f"Database error creating skill tree: {e}")
            raise ValueError(f"Failed to create skill tree: {e}")

    @staticmethod
    def get_skill_tree(
        db: Session,
        tree_id: str
    ) -> Optional[SkillTree]:
        """
        Get a skill tree by ID.
        
        Args:
            db: Database session
            tree_id: Skill tree ID
            
        Returns:
            SkillTree instance or None
        """
        return db.query(SkillTree).filter(SkillTree.id == tree_id).first()

    @staticmethod
    def get_skill_trees_by_specialization(
        db: Session,
        specialization: SpecializationType,
        include_custom: bool = True,
        public_only: bool = False
    ) -> List[SkillTree]:
        """
        Get all skill trees for a specialization.
        
        Args:
            db: Database session
            specialization: Specialization type
            include_custom: Include custom trees
            public_only: Only return public trees
            
        Returns:
            List of SkillTree instances
        """
        query = db.query(SkillTree).filter(
            SkillTree.specialization == specialization
        )
        
        if not include_custom:
            query = query.filter(SkillTree.is_custom == False)
        
        if public_only:
            query = query.filter(SkillTree.is_public == True)
        
        return query.all()

    @staticmethod
    def update_skill_tree(
        db: Session,
        tree_id: str,
        tree_data: SkillTreeUpdate
    ) -> SkillTree:
        """
        Update a skill tree.
        
        Args:
            db: Database session
            tree_id: Skill tree ID
            tree_data: Updated skill tree data
            
        Returns:
            Updated SkillTree instance
            
        Raises:
            ValueError: If tree not found
        """
        tree = db.query(SkillTree).filter(SkillTree.id == tree_id).first()
        
        if not tree:
            raise ValueError(f"Skill tree not found: {tree_id}")
        
        update_data = tree_data.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(tree, key, value)
        
        db.commit()
        db.refresh(tree)
        
        logger.info(f"Updated skill tree: {tree.name}")
        return tree

    @staticmethod
    def delete_skill_tree(
        db: Session,
        tree_id: str
    ) -> bool:
        """
        Delete a skill tree (and all its nodes).
        
        Args:
            db: Database session
            tree_id: Skill tree ID
            
        Returns:
            True if deleted, False if not found
        """
        tree = db.query(SkillTree).filter(SkillTree.id == tree_id).first()
        
        if not tree:
            return False
        
        db.delete(tree)
        db.commit()
        
        logger.info(f"Deleted skill tree: {tree.name}")
        return True

    # ========================================================================
    # Skill Node CRUD Operations
    # ========================================================================

    @staticmethod
    def create_skill_node(
        db: Session,
        tree_id: str,
        node_data: SkillNodeCreate
    ) -> SkillNode:
        """
        Create a new skill node in a tree.
        
        Args:
            db: Database session
            tree_id: Skill tree ID
            node_data: Skill node data
            
        Returns:
            Created SkillNode instance
            
        Raises:
            ValueError: If tree not found or validation fails
        """
        # Verify tree exists
        tree = db.query(SkillTree).filter(SkillTree.id == tree_id).first()
        if not tree:
            raise ValueError(f"Skill tree not found: {tree_id}")
        
        # Verify prerequisites exist
        if node_data.prerequisites:
            for prereq_id in node_data.prerequisites:
                prereq = db.query(SkillNode).filter(SkillNode.id == prereq_id).first()
                if not prereq:
                    raise ValueError(f"Prerequisite skill node not found: {prereq_id}")
        
        node = SkillNode(
            skill_tree_id=tree_id,
            name=node_data.name,
            description=node_data.description,
            max_level=node_data.max_level,
            experience_per_level=node_data.experience_per_level,
            prerequisites=node_data.prerequisites,
            capability_bonuses=node_data.capability_bonuses,
            personality_shifts=node_data.personality_shifts,
            unlocks_tools=node_data.unlocks_tools,
            unlocks_competitions=node_data.unlocks_competitions,
            tree_position_x=node_data.tree_position_x,
            tree_position_y=node_data.tree_position_y,
        )
        
        try:
            db.add(node)
            db.commit()
            db.refresh(node)
            logger.info(f"Created skill node: {node.name} in tree {tree.name}")
            return node
        except IntegrityError as e:
            db.rollback()
            logger.error(f"Database error creating skill node: {e}")
            raise ValueError(f"Failed to create skill node: {e}")

    @staticmethod
    def get_skill_node(
        db: Session,
        node_id: str
    ) -> Optional[SkillNode]:
        """
        Get a skill node by ID.
        
        Args:
            db: Database session
            node_id: Skill node ID
            
        Returns:
            SkillNode instance or None
        """
        return db.query(SkillNode).filter(SkillNode.id == node_id).first()

    @staticmethod
    def get_skill_nodes_by_tree(
        db: Session,
        tree_id: str
    ) -> List[SkillNode]:
        """
        Get all skill nodes in a tree.
        
        Args:
            db: Database session
            tree_id: Skill tree ID
            
        Returns:
            List of SkillNode instances
        """
        return db.query(SkillNode).filter(SkillNode.skill_tree_id == tree_id).all()

    @staticmethod
    def update_skill_node(
        db: Session,
        node_id: str,
        node_data: SkillNodeUpdate
    ) -> SkillNode:
        """
        Update a skill node.
        
        Args:
            db: Database session
            node_id: Skill node ID
            node_data: Updated skill node data
            
        Returns:
            Updated SkillNode instance
            
        Raises:
            ValueError: If node not found
        """
        node = db.query(SkillNode).filter(SkillNode.id == node_id).first()
        
        if not node:
            raise ValueError(f"Skill node not found: {node_id}")
        
        update_data = node_data.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(node, key, value)
        
        db.commit()
        db.refresh(node)
        
        logger.info(f"Updated skill node: {node.name}")
        return node

    @staticmethod
    def delete_skill_node(
        db: Session,
        node_id: str
    ) -> bool:
        """
        Delete a skill node.
        
        Args:
            db: Database session
            node_id: Skill node ID
            
        Returns:
            True if deleted, False if not found
        """
        node = db.query(SkillNode).filter(SkillNode.id == node_id).first()
        
        if not node:
            return False
        
        db.delete(node)
        db.commit()
        
        logger.info(f"Deleted skill node: {node.name}")
        return True

