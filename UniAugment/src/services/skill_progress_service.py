"""
Skill Progress Service - Phase 2

Business logic for tracking agent progress through skill trees.
"""

import logging
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.models.skill_progress import (
    AgentSkillProgress,
    AgentSkillProgressCreate,
    AgentSkillProgressUpdate,
    AgentSkillProgressResponse,
    GainExperienceResponse,
    UnlockSkillResponse,
    AgentSkillSummary,
)
from app.models.skill_tree import SkillNode

logger = logging.getLogger(__name__)


class SkillProgressService:
    """Service for managing agent skill progress."""

    @staticmethod
    def create_skill_progress(
        db: Session,
        agent_id: str,
        progress_data: AgentSkillProgressCreate
    ) -> AgentSkillProgress:
        """
        Create a new skill progress record for an agent.
        
        Args:
            db: Database session
            agent_id: Agent ID
            progress_data: Skill progress data
            
        Returns:
            Created AgentSkillProgress instance
            
        Raises:
            ValueError: If progress already exists or validation fails
        """
        # Check if progress already exists
        existing = db.query(AgentSkillProgress).filter(
            AgentSkillProgress.agent_id == agent_id,
            AgentSkillProgress.skill_node_id == progress_data.skill_node_id
        ).first()
        
        if existing:
            raise ValueError(f"Progress already exists for agent {agent_id} and skill {progress_data.skill_node_id}")
        
        # Verify skill node exists
        skill_node = db.query(SkillNode).filter(SkillNode.id == progress_data.skill_node_id).first()
        if not skill_node:
            raise ValueError(f"Skill node not found: {progress_data.skill_node_id}")
        
        progress = AgentSkillProgress(
            agent_id=agent_id,
            skill_node_id=progress_data.skill_node_id,
            current_level=progress_data.current_level,
            current_experience=progress_data.current_experience,
            is_unlocked=progress_data.is_unlocked,
            unlocked_at=datetime.now(timezone.utc) if progress_data.is_unlocked else None,
        )
        
        try:
            db.add(progress)
            db.commit()
            db.refresh(progress)
            logger.info(f"Created skill progress for agent {agent_id}, skill {progress_data.skill_node_id}")
            return progress
        except IntegrityError as e:
            db.rollback()
            logger.error(f"Database error creating skill progress: {e}")
            raise ValueError(f"Failed to create skill progress: {e}")

    @staticmethod
    def get_skill_progress(
        db: Session,
        agent_id: str,
        skill_node_id: str
    ) -> Optional[AgentSkillProgress]:
        """
        Get skill progress for an agent and skill.
        
        Args:
            db: Database session
            agent_id: Agent ID
            skill_node_id: Skill node ID
            
        Returns:
            AgentSkillProgress instance or None
        """
        return db.query(AgentSkillProgress).filter(
            AgentSkillProgress.agent_id == agent_id,
            AgentSkillProgress.skill_node_id == skill_node_id
        ).first()

    @staticmethod
    def get_all_agent_progress(
        db: Session,
        agent_id: str
    ) -> List[AgentSkillProgress]:
        """
        Get all skill progress for an agent.
        
        Args:
            db: Database session
            agent_id: Agent ID
            
        Returns:
            List of AgentSkillProgress instances
        """
        return db.query(AgentSkillProgress).filter(
            AgentSkillProgress.agent_id == agent_id
        ).all()

    @staticmethod
    def gain_experience(
        db: Session,
        agent_id: str,
        skill_node_id: str,
        experience_amount: int,
        reason: Optional[str] = None
    ) -> GainExperienceResponse:
        """
        Add experience to a skill and handle leveling up.
        
        Args:
            db: Database session
            agent_id: Agent ID
            skill_node_id: Skill node ID
            experience_amount: Amount of experience to gain
            reason: Optional reason for gaining experience
            
        Returns:
            GainExperienceResponse with level up information
            
        Raises:
            ValueError: If progress not found or skill not unlocked
        """
        # Get progress
        progress = db.query(AgentSkillProgress).filter(
            AgentSkillProgress.agent_id == agent_id,
            AgentSkillProgress.skill_node_id == skill_node_id
        ).first()
        
        if not progress:
            raise ValueError(f"Skill progress not found for agent {agent_id} and skill {skill_node_id}")
        
        if not progress.is_unlocked:
            raise ValueError(f"Skill {skill_node_id} is not unlocked for agent {agent_id}")
        
        # Get skill node
        skill_node = db.query(SkillNode).filter(SkillNode.id == skill_node_id).first()
        if not skill_node:
            raise ValueError(f"Skill node not found: {skill_node_id}")
        
        # Store previous values
        previous_level = progress.current_level
        previous_experience = progress.current_experience
        
        # Add experience
        progress.current_experience += experience_amount
        
        # Check for level ups
        levels_gained = 0
        while (progress.current_level < skill_node.max_level and 
               progress.current_experience >= skill_node.experience_per_level):
            progress.current_experience -= skill_node.experience_per_level
            progress.current_level += 1
            levels_gained += 1
        
        # Cap experience at max for max level
        if progress.current_level >= skill_node.max_level:
            progress.current_experience = 0
        
        db.commit()
        db.refresh(progress)
        
        # Build response
        response = GainExperienceResponse(
            skill_node_id=skill_node_id,
            previous_level=previous_level,
            new_level=progress.current_level,
            previous_experience=previous_experience,
            new_experience=progress.current_experience,
            leveled_up=levels_gained > 0,
            levels_gained=levels_gained,
            bonuses_applied=skill_node.capability_bonuses if levels_gained > 0 else {},
            tools_unlocked=skill_node.unlocks_tools if levels_gained > 0 else [],
            competitions_unlocked=skill_node.unlocks_competitions if levels_gained > 0 else [],
        )
        
        logger.info(f"Agent {agent_id} gained {experience_amount} XP in skill {skill_node_id}. "
                   f"Level: {previous_level} -> {progress.current_level}")
        
        return response

    @staticmethod
    def unlock_skill(
        db: Session,
        agent_id: str,
        skill_node_id: str,
        force: bool = False
    ) -> UnlockSkillResponse:
        """
        Unlock a skill for an agent (if prerequisites met).
        
        Args:
            db: Database session
            agent_id: Agent ID
            skill_node_id: Skill node ID
            force: Force unlock even if prerequisites not met
            
        Returns:
            UnlockSkillResponse with unlock status
            
        Raises:
            ValueError: If skill node not found
        """
        # Get skill node
        skill_node = db.query(SkillNode).filter(SkillNode.id == skill_node_id).first()
        if not skill_node:
            raise ValueError(f"Skill node not found: {skill_node_id}")
        
        # Check if already unlocked
        progress = db.query(AgentSkillProgress).filter(
            AgentSkillProgress.agent_id == agent_id,
            AgentSkillProgress.skill_node_id == skill_node_id
        ).first()
        
        if progress and progress.is_unlocked:
            return UnlockSkillResponse(
                skill_node_id=skill_node_id,
                unlocked=True,
                prerequisites_met=True,
                missing_prerequisites=[],
                message="Skill already unlocked"
            )
        
        # Check prerequisites
        missing_prerequisites = []
        if not force and skill_node.prerequisites:
            for prereq_id in skill_node.prerequisites:
                prereq_progress = db.query(AgentSkillProgress).filter(
                    AgentSkillProgress.agent_id == agent_id,
                    AgentSkillProgress.skill_node_id == prereq_id
                ).first()
                
                if not prereq_progress or not prereq_progress.is_unlocked:
                    missing_prerequisites.append(prereq_id)
        
        # If prerequisites not met and not forcing, return failure
        if missing_prerequisites and not force:
            return UnlockSkillResponse(
                skill_node_id=skill_node_id,
                unlocked=False,
                prerequisites_met=False,
                missing_prerequisites=missing_prerequisites,
                message=f"Prerequisites not met: {len(missing_prerequisites)} skills required"
            )
        
        # Create or update progress
        if not progress:
            progress = AgentSkillProgress(
                agent_id=agent_id,
                skill_node_id=skill_node_id,
                current_level=0,
                current_experience=0,
                is_unlocked=True,
                unlocked_at=datetime.now(timezone.utc)
            )
            db.add(progress)
        else:
            progress.is_unlocked = True
            progress.unlocked_at = datetime.now(timezone.utc)
        
        db.commit()
        db.refresh(progress)
        
        logger.info(f"Unlocked skill {skill_node_id} for agent {agent_id}")
        
        return UnlockSkillResponse(
            skill_node_id=skill_node_id,
            unlocked=True,
            prerequisites_met=len(missing_prerequisites) == 0,
            missing_prerequisites=missing_prerequisites if force else [],
            message="Skill unlocked successfully" + (" (forced)" if force and missing_prerequisites else "")
        )

    @staticmethod
    def delete_skill_progress(
        db: Session,
        agent_id: str,
        skill_node_id: str
    ) -> bool:
        """
        Delete skill progress for an agent.
        
        Args:
            db: Database session
            agent_id: Agent ID
            skill_node_id: Skill node ID
            
        Returns:
            True if deleted, False if not found
        """
        progress = db.query(AgentSkillProgress).filter(
            AgentSkillProgress.agent_id == agent_id,
            AgentSkillProgress.skill_node_id == skill_node_id
        ).first()
        
        if not progress:
            return False
        
        db.delete(progress)
        db.commit()
        
        logger.info(f"Deleted skill progress for agent {agent_id}, skill {skill_node_id}")
        return True

