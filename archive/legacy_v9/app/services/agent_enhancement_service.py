"""
Agent Enhancement Service - Phase 1

Business logic for visual and behavioral customization of agents.
"""

import logging
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session

from app.models.agent_enhancements import (
    VisualProfile,
    BehavioralProfile,
    VisualProfileSchema,
    BehavioralProfileSchema,
)

logger = logging.getLogger(__name__)


class AgentEnhancementService:
    """Service for managing agent enhancements."""

    @staticmethod
    def create_visual_profile(
        db: Session,
        agent_id: str,
        profile_data: VisualProfileSchema
    ) -> VisualProfile:
        """
        Create a new visual profile for an agent.
        
        Args:
            db: Database session
            agent_id: Agent ID
            profile_data: Visual profile data
            
        Returns:
            Created VisualProfile instance
        """
        # Check if profile already exists
        existing = db.query(VisualProfile).filter(
            VisualProfile.agent_id == agent_id
        ).first()
        
        if existing:
            logger.warning(f"Visual profile already exists for agent {agent_id}")
            return existing
        
        # Create new profile
        profile = VisualProfile(
            agent_id=agent_id,
            **profile_data.dict()
        )
        db.add(profile)
        db.commit()
        db.refresh(profile)
        
        logger.info(f"Created visual profile for agent {agent_id}")
        return profile

    @staticmethod
    def update_visual_profile(
        db: Session,
        agent_id: str,
        profile_data: VisualProfileSchema
    ) -> VisualProfile:
        """
        Update visual profile for an agent.
        
        Args:
            db: Database session
            agent_id: Agent ID
            profile_data: Updated visual profile data
            
        Returns:
            Updated VisualProfile instance
        """
        profile = db.query(VisualProfile).filter(
            VisualProfile.agent_id == agent_id
        ).first()
        
        if not profile:
            logger.error(f"Visual profile not found for agent {agent_id}")
            raise ValueError(f"Visual profile not found for agent {agent_id}")
        
        # Update fields
        for key, value in profile_data.dict().items():
            setattr(profile, key, value)
        
        db.commit()
        db.refresh(profile)
        
        logger.info(f"Updated visual profile for agent {agent_id}")
        return profile

    @staticmethod
    def get_visual_profile(
        db: Session,
        agent_id: str
    ) -> Optional[VisualProfile]:
        """
        Get visual profile for an agent.
        
        Args:
            db: Database session
            agent_id: Agent ID
            
        Returns:
            VisualProfile instance or None
        """
        return db.query(VisualProfile).filter(
            VisualProfile.agent_id == agent_id
        ).first()

    @staticmethod
    def create_behavioral_profile(
        db: Session,
        agent_id: str,
        profile_data: BehavioralProfileSchema
    ) -> BehavioralProfile:
        """
        Create a new behavioral profile for an agent.
        
        Args:
            db: Database session
            agent_id: Agent ID
            profile_data: Behavioral profile data
            
        Returns:
            Created BehavioralProfile instance
        """
        # Check if profile already exists
        existing = db.query(BehavioralProfile).filter(
            BehavioralProfile.agent_id == agent_id
        ).first()
        
        if existing:
            logger.warning(f"Behavioral profile already exists for agent {agent_id}")
            return existing
        
        # Create new profile
        profile = BehavioralProfile(
            agent_id=agent_id,
            **profile_data.dict()
        )
        db.add(profile)
        db.commit()
        db.refresh(profile)
        
        logger.info(f"Created behavioral profile for agent {agent_id}")
        return profile

    @staticmethod
    def update_behavioral_profile(
        db: Session,
        agent_id: str,
        profile_data: BehavioralProfileSchema
    ) -> BehavioralProfile:
        """
        Update behavioral profile for an agent.
        
        Args:
            db: Database session
            agent_id: Agent ID
            profile_data: Updated behavioral profile data
            
        Returns:
            Updated BehavioralProfile instance
        """
        profile = db.query(BehavioralProfile).filter(
            BehavioralProfile.agent_id == agent_id
        ).first()
        
        if not profile:
            logger.error(f"Behavioral profile not found for agent {agent_id}")
            raise ValueError(f"Behavioral profile not found for agent {agent_id}")
        
        # Update fields
        for key, value in profile_data.dict().items():
            setattr(profile, key, value)
        
        db.commit()
        db.refresh(profile)
        
        logger.info(f"Updated behavioral profile for agent {agent_id}")
        return profile

    @staticmethod
    def get_behavioral_profile(
        db: Session,
        agent_id: str
    ) -> Optional[BehavioralProfile]:
        """
        Get behavioral profile for an agent.
        
        Args:
            db: Database session
            agent_id: Agent ID
            
        Returns:
            BehavioralProfile instance or None
        """
        return db.query(BehavioralProfile).filter(
            BehavioralProfile.agent_id == agent_id
        ).first()

    @staticmethod
    def get_enhanced_profile(
        db: Session,
        agent_id: str
    ) -> Dict[str, Any]:
        """
        Get complete enhanced profile (visual + behavioral) for an agent.
        
        Args:
            db: Database session
            agent_id: Agent ID
            
        Returns:
            Dictionary with visual and behavioral profiles
        """
        visual = AgentEnhancementService.get_visual_profile(db, agent_id)
        behavioral = AgentEnhancementService.get_behavioral_profile(db, agent_id)
        
        if not visual or not behavioral:
            logger.error(f"Enhanced profile incomplete for agent {agent_id}")
            raise ValueError(f"Enhanced profile not found for agent {agent_id}")
        
        return {
            "agent_id": agent_id,
            "visual_profile": visual,
            "behavioral_profile": behavioral,
            "created_at": visual.created_at,
            "updated_at": max(visual.updated_at, behavioral.updated_at)
        }

    @staticmethod
    def delete_visual_profile(
        db: Session,
        agent_id: str
    ) -> bool:
        """
        Delete visual profile for an agent.
        
        Args:
            db: Database session
            agent_id: Agent ID
            
        Returns:
            True if deleted, False if not found
        """
        profile = db.query(VisualProfile).filter(
            VisualProfile.agent_id == agent_id
        ).first()
        
        if not profile:
            return False
        
        db.delete(profile)
        db.commit()
        logger.info(f"Deleted visual profile for agent {agent_id}")
        return True

    @staticmethod
    def delete_behavioral_profile(
        db: Session,
        agent_id: str
    ) -> bool:
        """
        Delete behavioral profile for an agent.
        
        Args:
            db: Database session
            agent_id: Agent ID
            
        Returns:
            True if deleted, False if not found
        """
        profile = db.query(BehavioralProfile).filter(
            BehavioralProfile.agent_id == agent_id
        ).first()
        
        if not profile:
            return False
        
        db.delete(profile)
        db.commit()
        logger.info(f"Deleted behavioral profile for agent {agent_id}")
        return True

