"""
Progression Path Service - Phase 2

Business logic for managing progression paths through skill trees.
"""

import logging
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.models.progression_path import (
    ProgressionPath,
    ProgressionPathCreate,
    ProgressionPathUpdate,
    ProgressionPathResponse,
    ProgressionPathWithDetails,
    AgentProgressionPathProgress,
)
from app.models.skill_tree import SkillTree, SkillNode
from app.models.skill_progress import AgentSkillProgress
from app.models.specialization import SpecializationType

logger = logging.getLogger(__name__)


class ProgressionPathService:
    """Service for managing progression paths."""

    @staticmethod
    def create_progression_path(
        db: Session,
        path_data: ProgressionPathCreate
    ) -> ProgressionPath:
        """
        Create a new progression path.
        
        Args:
            db: Database session
            path_data: Progression path data
            
        Returns:
            Created ProgressionPath instance
            
        Raises:
            ValueError: If validation fails
        """
        # Verify skill tree exists
        tree = db.query(SkillTree).filter(SkillTree.id == path_data.skill_tree_id).first()
        if not tree:
            raise ValueError(f"Skill tree not found: {path_data.skill_tree_id}")
        
        # Verify all skills in sequence exist and belong to the tree
        for skill_id in path_data.skill_sequence:
            skill = db.query(SkillNode).filter(
                SkillNode.id == skill_id,
                SkillNode.skill_tree_id == path_data.skill_tree_id
            ).first()
            if not skill:
                raise ValueError(f"Skill node {skill_id} not found in tree {path_data.skill_tree_id}")
        
        path = ProgressionPath(
            skill_tree_id=path_data.skill_tree_id,
            name=path_data.name,
            description=path_data.description,
            skill_sequence=path_data.skill_sequence,
            estimated_duration_weeks=path_data.estimated_duration_weeks,
            specialization=path_data.specialization,
            is_custom=path_data.is_custom,
            creator_id=path_data.creator_id,
            is_public=path_data.is_public,
        )
        
        try:
            db.add(path)
            db.commit()
            db.refresh(path)
            logger.info(f"Created progression path: {path.name} ({path.specialization.value})")
            return path
        except IntegrityError as e:
            db.rollback()
            logger.error(f"Database error creating progression path: {e}")
            raise ValueError(f"Failed to create progression path: {e}")

    @staticmethod
    def get_progression_path(
        db: Session,
        path_id: str
    ) -> Optional[ProgressionPath]:
        """
        Get a progression path by ID.
        
        Args:
            db: Database session
            path_id: Progression path ID
            
        Returns:
            ProgressionPath instance or None
        """
        return db.query(ProgressionPath).filter(ProgressionPath.id == path_id).first()

    @staticmethod
    def get_progression_paths_by_specialization(
        db: Session,
        specialization: SpecializationType,
        public_only: bool = False
    ) -> List[ProgressionPath]:
        """
        Get all progression paths for a specialization.
        
        Args:
            db: Database session
            specialization: Specialization type
            public_only: Only return public paths
            
        Returns:
            List of ProgressionPath instances
        """
        query = db.query(ProgressionPath).filter(
            ProgressionPath.specialization == specialization
        )
        
        if public_only:
            query = query.filter(ProgressionPath.is_public == True)
        
        return query.all()

    @staticmethod
    def get_progression_paths_by_tree(
        db: Session,
        tree_id: str
    ) -> List[ProgressionPath]:
        """
        Get all progression paths for a skill tree.
        
        Args:
            db: Database session
            tree_id: Skill tree ID
            
        Returns:
            List of ProgressionPath instances
        """
        return db.query(ProgressionPath).filter(
            ProgressionPath.skill_tree_id == tree_id
        ).all()

    @staticmethod
    def update_progression_path(
        db: Session,
        path_id: str,
        path_data: ProgressionPathUpdate
    ) -> ProgressionPath:
        """
        Update a progression path.
        
        Args:
            db: Database session
            path_id: Progression path ID
            path_data: Updated progression path data
            
        Returns:
            Updated ProgressionPath instance
            
        Raises:
            ValueError: If path not found or validation fails
        """
        path = db.query(ProgressionPath).filter(ProgressionPath.id == path_id).first()
        
        if not path:
            raise ValueError(f"Progression path not found: {path_id}")
        
        update_data = path_data.dict(exclude_unset=True)
        
        # Validate skill sequence if being updated
        if 'skill_sequence' in update_data:
            for skill_id in update_data['skill_sequence']:
                skill = db.query(SkillNode).filter(
                    SkillNode.id == skill_id,
                    SkillNode.skill_tree_id == path.skill_tree_id
                ).first()
                if not skill:
                    raise ValueError(f"Skill node {skill_id} not found in tree {path.skill_tree_id}")
        
        for key, value in update_data.items():
            setattr(path, key, value)
        
        db.commit()
        db.refresh(path)
        
        logger.info(f"Updated progression path: {path.name}")
        return path

    @staticmethod
    def delete_progression_path(
        db: Session,
        path_id: str
    ) -> bool:
        """
        Delete a progression path.
        
        Args:
            db: Database session
            path_id: Progression path ID
            
        Returns:
            True if deleted, False if not found
        """
        path = db.query(ProgressionPath).filter(ProgressionPath.id == path_id).first()
        
        if not path:
            return False
        
        db.delete(path)
        db.commit()
        
        logger.info(f"Deleted progression path: {path.name}")
        return True

    @staticmethod
    def get_agent_progress_on_path(
        db: Session,
        agent_id: str,
        path_id: str
    ) -> AgentProgressionPathProgress:
        """
        Get an agent's progress through a progression path.
        
        Args:
            db: Database session
            agent_id: Agent ID
            path_id: Progression path ID
            
        Returns:
            AgentProgressionPathProgress with detailed progress information
            
        Raises:
            ValueError: If path not found
        """
        # Get progression path
        path = db.query(ProgressionPath).filter(ProgressionPath.id == path_id).first()
        if not path:
            raise ValueError(f"Progression path not found: {path_id}")
        
        # Get agent's progress on all skills in the path
        completed_skills = []
        remaining_skills = []
        current_step = 0
        current_skill = None
        next_skill = None
        
        for i, skill_id in enumerate(path.skill_sequence):
            progress = db.query(AgentSkillProgress).filter(
                AgentSkillProgress.agent_id == agent_id,
                AgentSkillProgress.skill_node_id == skill_id
            ).first()
            
            skill_node = db.query(SkillNode).filter(SkillNode.id == skill_id).first()
            
            if progress and progress.is_unlocked and progress.current_level >= skill_node.max_level:
                # Skill completed
                completed_skills.append(skill_id)
            else:
                # Skill not completed
                remaining_skills.append(skill_id)
                if current_skill is None:
                    current_step = i
                    current_skill = {
                        "id": skill_id,
                        "name": skill_node.name if skill_node else "Unknown",
                        "current_level": progress.current_level if progress else 0,
                        "max_level": skill_node.max_level if skill_node else 0,
                    }
                    # Get next skill
                    if i + 1 < len(path.skill_sequence):
                        next_skill_id = path.skill_sequence[i + 1]
                        next_skill_node = db.query(SkillNode).filter(SkillNode.id == next_skill_id).first()
                        if next_skill_node:
                            next_skill = {
                                "id": next_skill_id,
                                "name": next_skill_node.name,
                            }
        
        # Calculate progress percentage
        total_steps = len(path.skill_sequence)
        completed_steps = len(completed_skills)
        progress_percentage = (completed_steps / total_steps * 100) if total_steps > 0 else 0
        
        # Estimate remaining weeks
        estimated_weeks_remaining = None
        if path.estimated_duration_weeks and total_steps > 0:
            weeks_per_skill = path.estimated_duration_weeks / total_steps
            estimated_weeks_remaining = int(len(remaining_skills) * weeks_per_skill)
        
        return AgentProgressionPathProgress(
            agent_id=agent_id,
            progression_path_id=path_id,
            path_name=path.name,
            current_step=current_step,
            total_steps=total_steps,
            completed_steps=completed_steps,
            progress_percentage=progress_percentage,
            current_skill=current_skill,
            next_skill=next_skill,
            completed_skills=completed_skills,
            remaining_skills=remaining_skills,
            estimated_weeks_remaining=estimated_weeks_remaining,
        )

    @staticmethod
    def get_path_with_details(
        db: Session,
        path_id: str
    ) -> ProgressionPathWithDetails:
        """
        Get a progression path with full skill details.
        
        Args:
            db: Database session
            path_id: Progression path ID
            
        Returns:
            ProgressionPathWithDetails with skill information
            
        Raises:
            ValueError: If path not found
        """
        path = db.query(ProgressionPath).filter(ProgressionPath.id == path_id).first()
        if not path:
            raise ValueError(f"Progression path not found: {path_id}")
        
        # Get skill details
        skills = []
        total_estimated_experience = 0
        
        for skill_id in path.skill_sequence:
            skill_node = db.query(SkillNode).filter(SkillNode.id == skill_id).first()
            if skill_node:
                skill_info = {
                    "id": skill_node.id,
                    "name": skill_node.name,
                    "description": skill_node.description,
                    "max_level": skill_node.max_level,
                    "experience_per_level": skill_node.experience_per_level,
                    "total_experience": skill_node.max_level * skill_node.experience_per_level,
                }
                skills.append(skill_info)
                total_estimated_experience += skill_info["total_experience"]
        
        return ProgressionPathWithDetails(
            path=ProgressionPathResponse.from_orm(path),
            skills=skills,
            total_skills=len(skills),
            total_estimated_experience=total_estimated_experience,
        )

