"""
Curriculum Service

Provides business logic for curriculum management including:
- CRUD operations for curriculum paths and levels
- Agent enrollment and progress tracking
- Performance evaluation
- Completion tracking
"""

import uuid
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import and_, or_, func, select

from app.models.curriculum import (
    CurriculumPath,
    CurriculumLevel,
    AgentCurriculumProgress,
    DifficultyLevel,
    CurriculumStatus,
    AgentProgressStatus,
    CurriculumPathCreate,
    CurriculumPathUpdate,
    CurriculumLevelCreate,
    AgentProgressCreate,
    AgentProgressUpdate
)


class CurriculumService:
    """Service for managing curriculum paths and agent progress"""

    def __init__(self, db: AsyncSession):
        self.db = db

    # ==================== Curriculum Path Operations ====================

    async def create_curriculum_path(self, path_data: CurriculumPathCreate) -> CurriculumPath:
        """
        Create a new curriculum path.
        
        Args:
            path_data: Curriculum path creation data
            
        Returns:
            Created curriculum path
        """
        curriculum_path = CurriculumPath(
            id=str(uuid.uuid4()),
            university_id=path_data.university_id,
            name=path_data.name,
            description=path_data.description,
            difficulty_level=path_data.difficulty_level.value,
            estimated_duration_hours=path_data.estimated_duration_hours,
            prerequisites=path_data.prerequisites,
            specialization=path_data.specialization,
            skill_tree_id=path_data.skill_tree_id,
            version="1.0.0",
            tags=path_data.tags,
            is_public=path_data.is_public,
            status=CurriculumStatus.ACTIVE.value,
            total_enrollments=0,
            total_completions=0
        )
        
        self.db.add(curriculum_path)
        await self.db.commit()
        await self.db.refresh(curriculum_path)
        
        return curriculum_path

    async def get_curriculum_path(self, path_id: str) -> Optional[CurriculumPath]:
        """Get a curriculum path by ID"""
        result = await self.db.execute(select(CurriculumPath).filter(CurriculumPath.id == path_id))
        return result.scalars().first()

    async def get_curriculum_paths_by_university(
        self,
        university_id: str,
        difficulty: Optional[DifficultyLevel] = None,
        specialization: Optional[str] = None,
        status: Optional[CurriculumStatus] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[CurriculumPath]:
        """Get curriculum paths for a university with filters"""
        query = select(CurriculumPath).filter(CurriculumPath.university_id == university_id)
        
        if difficulty:
            query = query.filter(CurriculumPath.difficulty_level == difficulty.value)
        if specialization:
            query = query.filter(CurriculumPath.specialization == specialization)
        if status:
            query = query.filter(CurriculumPath.status == status.value)
        
        query = query.order_by(CurriculumPath.created_at.desc()).offset(skip).limit(limit)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def update_curriculum_path(
        self,
        path_id: str,
        update_data: CurriculumPathUpdate
    ) -> Optional[CurriculumPath]:
        """Update a curriculum path"""
        result = await self.db.execute(select(CurriculumPath).filter(CurriculumPath.id == path_id))
        curriculum_path = result.scalars().first()
        
        if not curriculum_path:
            return None
        
        update_dict = update_data.model_dump(exclude_unset=True)
        
        for field, value in update_dict.items():
            if field == 'difficulty_level' and value is not None:
                value = value.value if hasattr(value, 'value') else value
            if field == 'status' and value is not None:
                value = value.value if hasattr(value, 'value') else value
            
            setattr(curriculum_path, field, value)
        
        curriculum_path.updated_at = datetime.now(timezone.utc)
        
        await self.db.commit()
        await self.db.refresh(curriculum_path)
        
        return curriculum_path

    async def delete_curriculum_path(self, path_id: str) -> bool:
        """Delete a curriculum path (soft delete)"""
        result = await self.db.execute(select(CurriculumPath).filter(CurriculumPath.id == path_id))
        curriculum_path = result.scalars().first()
        
        if not curriculum_path:
            return False
        
        curriculum_path.status = CurriculumStatus.ARCHIVED.value
        curriculum_path.updated_at = datetime.now(timezone.utc)
        
        await self.db.commit()
        
        return True

    # ==================== Curriculum Level Operations ====================

    async def create_curriculum_level(self, level_data: CurriculumLevelCreate) -> CurriculumLevel:
        """Create a new curriculum level"""
        curriculum_level = CurriculumLevel(
            id=str(uuid.uuid4()),
            curriculum_path_id=level_data.curriculum_path_id,
            level_number=level_data.level_number,
            name=level_data.name,
            description=level_data.description,
            objectives=level_data.objectives,
            challenges=level_data.challenges,
            required_challenges=level_data.required_challenges,
            evaluation_criteria=level_data.evaluation_criteria,
            required_score=level_data.required_score,
            learning_resources=level_data.learning_resources,
            estimated_hours=level_data.estimated_hours
        )
        
        self.db.add(curriculum_level)
        await self.db.commit()
        await self.db.refresh(curriculum_level)
        
        return curriculum_level

    async def get_curriculum_level(self, level_id: str) -> Optional[CurriculumLevel]:
        """Get a curriculum level by ID"""
        result = await self.db.execute(select(CurriculumLevel).filter(CurriculumLevel.id == level_id))
        return result.scalars().first()

    async def get_levels_by_path(self, path_id: str) -> List[CurriculumLevel]:
        """Get all levels for a curriculum path, ordered by level number"""
        result = await self.db.execute(
            select(CurriculumLevel)
            .filter(CurriculumLevel.curriculum_path_id == path_id)
            .order_by(CurriculumLevel.level_number)
        )
        return list(result.scalars().all())

    async def delete_curriculum_level(self, level_id: str) -> bool:
        """Delete a curriculum level"""
        result = await self.db.execute(select(CurriculumLevel).filter(CurriculumLevel.id == level_id))
        curriculum_level = result.scalars().first()
        
        if not curriculum_level:
            return False
        
        await self.db.delete(curriculum_level)
        await self.db.commit()
        
        return True

    # ==================== Agent Progress Operations ====================

    async def enroll_agent(self, enrollment_data: AgentProgressCreate) -> AgentCurriculumProgress:
        """
        Enroll an agent in a curriculum path.
        
        Args:
            enrollment_data: Enrollment data
            
        Returns:
            Created progress record
        """
        # Check if already enrolled
        result = await self.db.execute(
            select(AgentCurriculumProgress).filter(
                and_(
                    AgentCurriculumProgress.agent_id == enrollment_data.agent_id,
                    AgentCurriculumProgress.curriculum_path_id == enrollment_data.curriculum_path_id
                )
            )
        )
        existing = result.scalars().first()
        
        if existing:
            return existing
        
        progress = AgentCurriculumProgress(
            id=str(uuid.uuid4()),
            agent_id=enrollment_data.agent_id,
            curriculum_path_id=enrollment_data.curriculum_path_id,
            current_level_number=1,
            completed_levels=[],
            status=AgentProgressStatus.NOT_STARTED.value,
            level_scores={},
            total_attempts=0,
            failed_attempts=0,
            custom_metadata={}
        )
        
        self.db.add(progress)
        
        # Increment enrollment count on curriculum path
        path_result = await self.db.execute(select(CurriculumPath).filter(CurriculumPath.id == enrollment_data.curriculum_path_id))
        curriculum_path = path_result.scalars().first()
        
        if curriculum_path:
            curriculum_path.total_enrollments += 1
        
        await self.db.commit()
        await self.db.refresh(progress)
        
        return progress

    async def get_agent_progress(self, agent_id: str, path_id: str) -> Optional[AgentCurriculumProgress]:
        """Get agent's progress on a curriculum path"""
        result = await self.db.execute(
            select(AgentCurriculumProgress).filter(
                and_(
                    AgentCurriculumProgress.agent_id == agent_id,
                    AgentCurriculumProgress.curriculum_path_id == path_id
                )
            )
        )
        return result.scalars().first()

    async def get_agent_all_progress(
        self,
        agent_id: str,
        status: Optional[AgentProgressStatus] = None
    ) -> List[AgentCurriculumProgress]:
        """Get all curriculum progress for an agent"""
        query = select(AgentCurriculumProgress).filter(AgentCurriculumProgress.agent_id == agent_id)
        
        if status:
            query = query.filter(AgentCurriculumProgress.status == status.value)
        
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def start_curriculum(self, agent_id: str, path_id: str) -> Optional[AgentCurriculumProgress]:
        """Mark curriculum as started"""
        progress = await self.get_agent_progress(agent_id, path_id)
        
        if not progress:
            return None
        
        if progress.status == AgentProgressStatus.NOT_STARTED.value:
            progress.status = AgentProgressStatus.IN_PROGRESS.value
            progress.started_at = datetime.now(timezone.utc)
            progress.last_activity_at = datetime.now(timezone.utc)
            
            await self.db.commit()
            await self.db.refresh(progress)
        
        return progress

    async def complete_level(
        self,
        agent_id: str,
        path_id: str,
        level_number: int,
        score: float
    ) -> Optional[AgentCurriculumProgress]:
        """
        Mark a level as completed and update progress.
        
        Args:
            agent_id: Agent ID
            path_id: Curriculum path ID
            level_number: Level number completed
            score: Score achieved (0.0-1.0)
            
        Returns:
            Updated progress or None
        """
        progress = await self.get_agent_progress(agent_id, path_id)
        
        if not progress:
            return None
        
        # Add to completed levels if not already there
        if level_number not in progress.completed_levels:
            # Create new list to trigger SQLAlchemy change detection
            new_completed = list(progress.completed_levels)
            new_completed.append(level_number)
            progress.completed_levels = new_completed
        
        # Update level score
        level_scores = dict(progress.level_scores)
        level_scores[str(level_number)] = score
        progress.level_scores = level_scores
        
        # Calculate overall score
        if level_scores:
            progress.overall_score = sum(level_scores.values()) / len(level_scores)
        
        # Move to next level
        progress.current_level_number = level_number + 1
        progress.last_activity_at = datetime.now(timezone.utc)
        progress.updated_at = datetime.now(timezone.utc)
        
        # Check if curriculum is complete
        path_result = await self.db.execute(select(CurriculumPath).filter(CurriculumPath.id == path_id))
        curriculum_path = path_result.scalars().first()
        
        if curriculum_path:
            count_result = await self.db.execute(
                select(func.count(CurriculumLevel.id)).filter(
                    CurriculumLevel.curriculum_path_id == path_id
                )
            )
            total_levels = count_result.scalar()
            
            if len(progress.completed_levels) >= total_levels:
                progress.status = AgentProgressStatus.COMPLETED.value
                progress.completed_at = datetime.now(timezone.utc)
                
                # Calculate total time
                if progress.started_at:
                    started_at = progress.started_at
                    if started_at.tzinfo is None:
                        started_at = started_at.replace(tzinfo=timezone.utc)
                    duration = progress.completed_at - started_at
                    progress.total_time_hours = duration.total_seconds() / 3600
                
                # Increment completion count
                curriculum_path.total_completions += 1
                
                # Update average completion time
                if curriculum_path.total_completions > 0:
                    avg_time_result = await self.db.execute(
                        select(AgentCurriculumProgress).filter(
                            and_(
                                AgentCurriculumProgress.curriculum_path_id == path_id,
                                AgentCurriculumProgress.status == AgentProgressStatus.COMPLETED.value,
                                AgentCurriculumProgress.total_time_hours.isnot(None)
                            )
                        )
                    )
                    all_progress = avg_time_result.scalars().all()
                    
                    if all_progress:
                        avg_time = sum(p.total_time_hours for p in all_progress) / len(all_progress)
                        curriculum_path.average_completion_time_hours = avg_time
                
                # Update average score
                avg_score_result = await self.db.execute(
                    select(AgentCurriculumProgress.overall_score).filter(
                        and_(
                            AgentCurriculumProgress.curriculum_path_id == path_id,
                            AgentCurriculumProgress.overall_score.isnot(None)
                        )
                    )
                )
                all_scores = avg_score_result.scalars().all()
                
                if all_scores:
                    curriculum_path.average_score = sum(all_scores) / len(all_scores)
        
        await self.db.commit()
        await self.db.refresh(progress)
        
        return progress
