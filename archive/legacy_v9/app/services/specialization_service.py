"""
Specialization Service - Phase 2

Business logic for agent specialization management.
"""

import logging
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.models.specialization import (
    SpecializationProfile,
    SpecializationType,
    SpecializationProfileCreate,
    SpecializationProfileUpdate,
    SpecializationProfileResponse,
    SpecializationTypeInfo,
    get_specialization_info,
    get_all_specialization_types,
)

logger = logging.getLogger(__name__)


class SpecializationService:
    """Service for managing agent specializations."""

    @staticmethod
    def create_specialization_profile(
        db: Session,
        agent_id: str,
        profile_data: SpecializationProfileCreate
    ) -> SpecializationProfile:
        """
        Create a new specialization profile for an agent.
        
        Args:
            db: Database session
            agent_id: Agent ID
            profile_data: Specialization profile data
            
        Returns:
            Created SpecializationProfile instance
            
        Raises:
            ValueError: If profile already exists or validation fails
        """
        # Check if profile already exists
        existing = db.query(SpecializationProfile).filter(
            SpecializationProfile.agent_id == agent_id
        ).first()
        
        if existing:
            logger.warning(f"Specialization profile already exists for agent {agent_id}")
            raise ValueError(f"Specialization profile already exists for agent {agent_id}")
        
        # Validate secondary specializations don't include primary
        if profile_data.primary_specialization in profile_data.secondary_specializations:
            raise ValueError("Secondary specializations cannot include the primary specialization")
        
        # Create new profile
        profile = SpecializationProfile(
            agent_id=agent_id,
            primary_specialization=profile_data.primary_specialization,
            specialization_level=profile_data.specialization_level,
            secondary_specializations=[s.value for s in profile_data.secondary_specializations],
            specialization_tools=profile_data.specialization_tools,
            specialization_curriculum=profile_data.specialization_curriculum,
            specialization_constraints=profile_data.specialization_constraints,
            cross_specialization_enabled=profile_data.cross_specialization_enabled,
            cross_specialization_penalty=profile_data.cross_specialization_penalty,
        )
        
        try:
            db.add(profile)
            db.commit()
            db.refresh(profile)
            logger.info(f"Created specialization profile for agent {agent_id}: {profile_data.primary_specialization.value}")
            return profile
        except IntegrityError as e:
            db.rollback()
            logger.error(f"Database error creating specialization profile: {e}")
            raise ValueError(f"Failed to create specialization profile: {e}")

    @staticmethod
    def update_specialization_profile(
        db: Session,
        agent_id: str,
        profile_data: SpecializationProfileUpdate
    ) -> SpecializationProfile:
        """
        Update specialization profile for an agent.
        
        Args:
            db: Database session
            agent_id: Agent ID
            profile_data: Updated specialization profile data
            
        Returns:
            Updated SpecializationProfile instance
            
        Raises:
            ValueError: If profile not found or validation fails
        """
        profile = db.query(SpecializationProfile).filter(
            SpecializationProfile.agent_id == agent_id
        ).first()
        
        if not profile:
            logger.error(f"Specialization profile not found for agent {agent_id}")
            raise ValueError(f"Specialization profile not found for agent {agent_id}")
        
        # Update fields
        update_data = profile_data.dict(exclude_unset=True)
        
        # Validate secondary specializations if being updated
        if 'secondary_specializations' in update_data:
            primary = update_data.get('primary_specialization', profile.primary_specialization)
            if primary in update_data['secondary_specializations']:
                raise ValueError("Secondary specializations cannot include the primary specialization")
            update_data['secondary_specializations'] = [s.value for s in update_data['secondary_specializations']]
        
        for key, value in update_data.items():
            setattr(profile, key, value)
        
        db.commit()
        db.refresh(profile)
        
        logger.info(f"Updated specialization profile for agent {agent_id}")
        return profile

    @staticmethod
    def get_specialization_profile(
        db: Session,
        agent_id: str
    ) -> Optional[SpecializationProfile]:
        """
        Get specialization profile for an agent.
        
        Args:
            db: Database session
            agent_id: Agent ID
            
        Returns:
            SpecializationProfile instance or None
        """
        return db.query(SpecializationProfile).filter(
            SpecializationProfile.agent_id == agent_id
        ).first()

    @staticmethod
    def delete_specialization_profile(
        db: Session,
        agent_id: str
    ) -> bool:
        """
        Delete specialization profile for an agent.
        
        Args:
            db: Database session
            agent_id: Agent ID
            
        Returns:
            True if deleted, False if not found
        """
        profile = db.query(SpecializationProfile).filter(
            SpecializationProfile.agent_id == agent_id
        ).first()
        
        if not profile:
            logger.warning(f"Specialization profile not found for agent {agent_id}")
            return False
        
        db.delete(profile)
        db.commit()
        
        logger.info(f"Deleted specialization profile for agent {agent_id}")
        return True

    @staticmethod
    def level_up_specialization(
        db: Session,
        agent_id: str
    ) -> SpecializationProfile:
        """
        Increase specialization level by 1 (max 10).
        
        Args:
            db: Database session
            agent_id: Agent ID
            
        Returns:
            Updated SpecializationProfile instance
            
        Raises:
            ValueError: If profile not found or already at max level
        """
        profile = db.query(SpecializationProfile).filter(
            SpecializationProfile.agent_id == agent_id
        ).first()
        
        if not profile:
            raise ValueError(f"Specialization profile not found for agent {agent_id}")
        
        if profile.specialization_level >= 10:
            raise ValueError(f"Specialization already at max level (10)")
        
        profile.specialization_level += 1
        db.commit()
        db.refresh(profile)
        
        logger.info(f"Leveled up specialization for agent {agent_id} to level {profile.specialization_level}")
        return profile

    @staticmethod
    def add_secondary_specialization(
        db: Session,
        agent_id: str,
        specialization: SpecializationType
    ) -> SpecializationProfile:
        """
        Add a secondary specialization to an agent.
        
        Args:
            db: Database session
            agent_id: Agent ID
            specialization: Specialization type to add
            
        Returns:
            Updated SpecializationProfile instance
            
        Raises:
            ValueError: If profile not found or validation fails
        """
        profile = db.query(SpecializationProfile).filter(
            SpecializationProfile.agent_id == agent_id
        ).first()
        
        if not profile:
            raise ValueError(f"Specialization profile not found for agent {agent_id}")
        
        if specialization == profile.primary_specialization:
            raise ValueError("Cannot add primary specialization as secondary")
        
        if specialization.value in profile.secondary_specializations:
            raise ValueError(f"Specialization {specialization.value} already in secondary list")

        # Create new list to trigger SQLAlchemy change detection
        new_secondaries = list(profile.secondary_specializations)
        new_secondaries.append(specialization.value)
        profile.secondary_specializations = new_secondaries

        db.commit()
        db.refresh(profile)
        
        logger.info(f"Added secondary specialization {specialization.value} to agent {agent_id}")
        return profile

    @staticmethod
    def get_all_specialization_types() -> List[SpecializationTypeInfo]:
        """
        Get information about all available specialization types.
        
        Returns:
            List of SpecializationTypeInfo
        """
        return get_all_specialization_types()

    @staticmethod
    def get_specialization_type_info(spec_type: SpecializationType) -> SpecializationTypeInfo:
        """
        Get information about a specific specialization type.
        
        Args:
            spec_type: Specialization type
            
        Returns:
            SpecializationTypeInfo
        """
        return get_specialization_info(spec_type)

