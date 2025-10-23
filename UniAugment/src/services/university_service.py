"""
University Service

Provides business logic for university management including:
- CRUD operations for universities
- Statistics tracking
- Resource management
- Multi-tenant operations
"""

import uuid
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func

from app.models.university import (
    University,
    UniversityStatus,
    IsolationLevel,
    UniversityCreate,
    UniversityUpdate
)


class UniversityService:
    """Service for managing universities"""

    @staticmethod
    def create_university(db: Session, university_data: UniversityCreate) -> University:
        """
        Create a new university instance.
        
        Args:
            db: Database session
            university_data: University creation data
            
        Returns:
            Created university instance
        """
        # Convert settings to dict if it's a Pydantic model
        settings_dict = university_data.settings.dict() if hasattr(university_data.settings, 'dict') else university_data.settings
        
        university = University(
            id=str(uuid.uuid4()),
            name=university_data.name,
            description=university_data.description,
            owner_user_id=university_data.owner_user_id,
            client_app_id=university_data.client_app_id,
            tenant_id=university_data.tenant_id,
            organization_id=university_data.organization_id,
            settings=settings_dict,
            isolation_level=university_data.isolation_level.value,
            max_agents=university_data.max_agents,
            max_concurrent_competitions=university_data.max_concurrent_competitions,
            storage_quota_mb=university_data.storage_quota_mb,
            primary_specialization=university_data.primary_specialization,
            secondary_specializations=university_data.secondary_specializations,
            status=UniversityStatus.ACTIVE.value,
            total_agents=0,
            active_agents=0,
            total_competitions=0,
            total_training_data_points=0,
            tags=university_data.tags,
            custom_metadata=university_data.custom_metadata,
            last_activity_at=datetime.now(timezone.utc)
        )
        
        db.add(university)
        db.commit()
        db.refresh(university)
        
        return university

    @staticmethod
    def get_university(db: Session, university_id: str) -> Optional[University]:
        """
        Get a university by ID.
        
        Args:
            db: Database session
            university_id: University ID
            
        Returns:
            University instance or None
        """
        return db.query(University).filter(University.id == university_id).first()

    @staticmethod
    def get_universities_by_owner(
        db: Session,
        owner_user_id: str,
        status: Optional[UniversityStatus] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[University]:
        """
        Get universities owned by a user.
        
        Args:
            db: Database session
            owner_user_id: Owner user ID
            status: Optional status filter
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of universities
        """
        query = db.query(University).filter(University.owner_user_id == owner_user_id)
        
        if status:
            query = query.filter(University.status == status.value)
        
        return query.order_by(University.created_at.desc()).offset(skip).limit(limit).all()

    @staticmethod
    def get_universities_by_tenant(
        db: Session,
        tenant_id: str,
        status: Optional[UniversityStatus] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[University]:
        """
        Get universities by tenant ID.
        
        Args:
            db: Database session
            tenant_id: Tenant ID
            status: Optional status filter
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of universities
        """
        query = db.query(University).filter(University.tenant_id == tenant_id)
        
        if status:
            query = query.filter(University.status == status.value)
        
        return query.order_by(University.created_at.desc()).offset(skip).limit(limit).all()

    @staticmethod
    def update_university(
        db: Session,
        university_id: str,
        update_data: UniversityUpdate
    ) -> Optional[University]:
        """
        Update a university.
        
        Args:
            db: Database session
            university_id: University ID
            update_data: Update data
            
        Returns:
            Updated university or None
        """
        university = db.query(University).filter(University.id == university_id).first()
        
        if not university:
            return None
        
        # Update fields if provided
        update_dict = update_data.dict(exclude_unset=True)
        
        for field, value in update_dict.items():
            if field == 'settings' and value is not None:
                # Convert settings to dict if it's a Pydantic model
                value = value.dict() if hasattr(value, 'dict') else value
            if field == 'status' and value is not None:
                value = value.value if hasattr(value, 'value') else value
            
            setattr(university, field, value)
        
        university.updated_at = datetime.now(timezone.utc)
        
        db.commit()
        db.refresh(university)
        
        return university

    @staticmethod
    def delete_university(db: Session, university_id: str) -> bool:
        """
        Delete a university (soft delete by setting status to ARCHIVED).
        
        Args:
            db: Database session
            university_id: University ID
            
        Returns:
            True if deleted, False if not found
        """
        university = db.query(University).filter(University.id == university_id).first()
        
        if not university:
            return False
        
        university.status = UniversityStatus.ARCHIVED.value
        university.updated_at = datetime.now(timezone.utc)
        
        db.commit()
        
        return True

    @staticmethod
    def update_statistics(
        db: Session,
        university_id: str,
        total_agents: Optional[int] = None,
        active_agents: Optional[int] = None,
        total_competitions: Optional[int] = None,
        total_training_data_points: Optional[int] = None
    ) -> Optional[University]:
        """
        Update university statistics.
        
        Args:
            db: Database session
            university_id: University ID
            total_agents: Total agents count
            active_agents: Active agents count
            total_competitions: Total competitions count
            total_training_data_points: Total training data points
            
        Returns:
            Updated university or None
        """
        university = db.query(University).filter(University.id == university_id).first()
        
        if not university:
            return None
        
        if total_agents is not None:
            university.total_agents = total_agents
        if active_agents is not None:
            university.active_agents = active_agents
        if total_competitions is not None:
            university.total_competitions = total_competitions
        if total_training_data_points is not None:
            university.total_training_data_points = total_training_data_points
        
        university.last_activity_at = datetime.now(timezone.utc)
        university.updated_at = datetime.now(timezone.utc)
        
        db.commit()
        db.refresh(university)
        
        return university

    @staticmethod
    def increment_agent_count(db: Session, university_id: str, active: bool = True) -> Optional[University]:
        """
        Increment agent count for a university.
        
        Args:
            db: Database session
            university_id: University ID
            active: Whether the agent is active
            
        Returns:
            Updated university or None
        """
        university = db.query(University).filter(University.id == university_id).first()
        
        if not university:
            return None
        
        university.total_agents += 1
        if active:
            university.active_agents += 1
        
        university.last_activity_at = datetime.now(timezone.utc)
        university.updated_at = datetime.now(timezone.utc)
        
        db.commit()
        db.refresh(university)
        
        return university

    @staticmethod
    def increment_competition_count(db: Session, university_id: str) -> Optional[University]:
        """
        Increment competition count for a university.
        
        Args:
            db: Database session
            university_id: University ID
            
        Returns:
            Updated university or None
        """
        university = db.query(University).filter(University.id == university_id).first()
        
        if not university:
            return None
        
        university.total_competitions += 1
        university.last_activity_at = datetime.now(timezone.utc)
        university.updated_at = datetime.now(timezone.utc)
        
        db.commit()
        db.refresh(university)
        
        return university

    @staticmethod
    def search_universities(
        db: Session,
        query: Optional[str] = None,
        specialization: Optional[str] = None,
        status: Optional[UniversityStatus] = None,
        is_public: bool = False,
        skip: int = 0,
        limit: int = 100
    ) -> List[University]:
        """
        Search universities with filters.
        
        Args:
            db: Database session
            query: Search query for name/description
            specialization: Filter by specialization
            status: Filter by status
            is_public: Only return public universities
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of universities
        """
        filters = []
        
        if query:
            filters.append(
                or_(
                    University.name.ilike(f"%{query}%"),
                    University.description.ilike(f"%{query}%")
                )
            )
        
        if specialization:
            filters.append(
                or_(
                    University.primary_specialization == specialization,
                    University.secondary_specializations.contains([specialization])
                )
            )
        
        if status:
            filters.append(University.status == status.value)
        
        query_obj = db.query(University)
        
        if filters:
            query_obj = query_obj.filter(and_(*filters))
        
        return query_obj.order_by(University.created_at.desc()).offset(skip).limit(limit).all()

