"""
Enhanced University Service

Provides advanced business logic for the enhanced university system including:
- University agent management with detailed metrics
- Training data collection and quality assessment
- Improvement proposal generation and validation
- Achievement and gamification system
- Advanced curriculum and competition features
"""

import uuid
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc

from app.database.models_university import (
    University,
    UniversityAgent,
    CurriculumPath,
    CurriculumLevel,
    AgentProgress,
    TrainingDataCollection,
    ImprovementProposal,
    Achievement,
    AgentAchievement
)


class EnhancedUniversityService:
    """Service for managing enhanced university features"""
    
    # ==================== University Agent Operations ====================
    
    @staticmethod
    def create_agent(
        db: Session,
        university_id: str,
        name: str,
        agent_type: str = "student",
        configuration: Dict[str, Any] = None,
        specialization: Optional[str] = None
    ) -> UniversityAgent:
        """Create a new university agent"""
        if configuration is None:
            configuration = {}
            
        agent = UniversityAgent(
            id=str(uuid.uuid4()),
            university_id=university_id,
            name=name,
            agent_type=agent_type,
            configuration=configuration,
            specialization=specialization,
            status="active"
        )
        
        db.add(agent)
        db.commit()
        db.refresh(agent)
        
        return agent
    
    @staticmethod
    def get_agent(db: Session, agent_id: str) -> Optional[UniversityAgent]:
        """Get an agent by ID"""
        return db.query(UniversityAgent).filter(UniversityAgent.id == agent_id).first()
    
    @staticmethod
    def get_agents_by_university(
        db: Session,
        university_id: str,
        agent_type: Optional[str] = None,
        status: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[UniversityAgent]:
        """Get agents for a university with filters"""
        query = db.query(UniversityAgent).filter(UniversityAgent.university_id == university_id)
        
        if agent_type:
            query = query.filter(UniversityAgent.agent_type == agent_type)
        if status:
            query = query.filter(UniversityAgent.status == status)
            
        return query.order_by(UniversityAgent.created_at.desc()).offset(skip).limit(limit).all()
    
    @staticmethod
    def update_agent_competency(
        db: Session,
        agent_id: str,
        competency_score: float,
        training_hours: Optional[float] = None
    ) -> Optional[UniversityAgent]:
        """Update agent competency metrics"""
        agent = db.query(UniversityAgent).filter(UniversityAgent.id == agent_id).first()
        
        if not agent:
            return None
            
        agent.competency_score = competency_score
        if training_hours is not None:
            agent.training_hours = training_hours
        agent.updated_at = datetime.now(timezone.utc)
        
        db.commit()
        db.refresh(agent)
        
        return agent
    
    @staticmethod
    def update_agent_competition_stats(
        db: Session,
        agent_id: str,
        won: bool = False,
        lost: bool = False,
        draw: bool = False,
        score: Optional[float] = None
    ) -> Optional[UniversityAgent]:
        """Update agent competition statistics"""
        agent = db.query(UniversityAgent).filter(UniversityAgent.id == agent_id).first()
        
        if not agent:
            return None
            
        if won:
            agent.competition_wins += 1
        if lost:
            agent.competition_losses += 1
        if draw:
            agent.competition_draws += 1
            
        if score is not None:
            # Update average score
            total_matches = agent.competition_wins + agent.competition_losses + agent.competition_draws
            if total_matches > 0:
                agent.average_score = (
                    (agent.average_score * (total_matches - 1) + score) / total_matches
                )
            
            # Update highest score
            if score > agent.highest_score:
                agent.highest_score = score
                
            # Update Elo rating (simplified)
            if won:
                agent.elo_rating += 20
            elif lost:
                agent.elo_rating = max(100, agent.elo_rating - 20)
                
        agent.last_competed_at = datetime.now(timezone.utc)
        agent.updated_at = datetime.now(timezone.utc)
        
        db.commit()
        db.refresh(agent)
        
        return agent
    
    # ==================== Agent Progress Operations ====================
    
    @staticmethod
    def create_agent_progress(
        db: Session,
        agent_id: str,
        curriculum_level_id: str,
        total_challenges: int
    ) -> AgentProgress:
        """Create a new agent progress record"""
        progress = AgentProgress(
            id=str(uuid.uuid4()),
            agent_id=agent_id,
            curriculum_level_id=curriculum_level_id,
            total_challenges=total_challenges,
            status="not_started"
        )
        
        db.add(progress)
        db.commit()
        db.refresh(progress)
        
        return progress
    
    @staticmethod
    def update_agent_progress(
        db: Session,
        progress_id: str,
        challenge_index: int,
        score: float,
        time_spent_minutes: int,
        challenge_result: Dict[str, Any]
    ) -> Optional[AgentProgress]:
        """Update agent progress with challenge results"""
        progress = db.query(AgentProgress).filter(AgentProgress.id == progress_id).first()
        
        if not progress:
            return None
            
        progress.current_challenge_index = challenge_index
        progress.current_score = score
        progress.time_spent_minutes += time_spent_minutes
        
        # Update best score
        if score > progress.best_score:
            progress.best_score = score
            
        # Update average score
        if progress.challenges_completed > 0:
            progress.average_score = (
                (progress.average_score * progress.challenges_completed + score) / 
                (progress.challenges_completed + 1)
            )
        else:
            progress.average_score = score
            
        # Add challenge result
        challenge_results = list(progress.challenge_results)
        challenge_results.append({
            "challenge_index": challenge_index,
            "score": score,
            "time_spent_minutes": time_spent_minutes,
            "result": challenge_result,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        progress.challenge_results = challenge_results
        
        # Update status
        if challenge_index >= progress.total_challenges:
            progress.status = "completed"
            progress.completed_at = datetime.now(timezone.utc)
        else:
            progress.status = "in_progress"
            if not progress.started_at:
                progress.started_at = datetime.now(timezone.utc)
                
        progress.challenges_completed += 1
        progress.last_activity_at = datetime.now(timezone.utc)
        
        db.commit()
        db.refresh(progress)
        
        return progress
    
    # ==================== Training Data Operations ====================
    
    @staticmethod
    def collect_training_data(
        db: Session,
        university_id: str,
        agent_id: str,
        source_type: str,
        data_type: str,
        raw_data: Dict[str, Any],
        source_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> TrainingDataCollection:
        """Collect training data from agent activities"""
        collection = TrainingDataCollection(
            id=str(uuid.uuid4()),
            university_id=university_id,
            agent_id=agent_id,
            source_type=source_type,
            source_id=source_id,
            data_type=data_type,
            raw_data=raw_data,
            metadata=metadata or {},
            validation_status="pending"
        )
        
        db.add(collection)
        
        # Update agent's training data count
        agent = db.query(UniversityAgent).filter(UniversityAgent.id == agent_id).first()
        if agent:
            agent.training_data_collected += 1
            
        db.commit()
        db.refresh(collection)
        
        return collection
    
    @staticmethod
    def validate_training_data(
        db: Session,
        collection_id: str,
        quality_score: float,
        completeness_score: float,
        consistency_score: float,
        validity_score: float,
        validation_results: Dict[str, Any],
        validated_by: str
    ) -> Optional[TrainingDataCollection]:
        """Validate training data collection"""
        collection = db.query(TrainingDataCollection).filter(
            TrainingDataCollection.id == collection_id
        ).first()
        
        if not collection:
            return None
            
        collection.quality_score = quality_score
        collection.completeness_score = completeness_score
        collection.consistency_score = consistency_score
        collection.validity_score = validity_score
        collection.validation_results = validation_results
        collection.validated_by = validated_by
        collection.validated_at = datetime.now(timezone.utc)
        collection.validation_status = "validated"
        
        db.commit()
        db.refresh(collection)
        
        return collection
    
    # ==================== Improvement Proposal Operations ====================
    
    @staticmethod
    def create_improvement_proposal(
        db: Session,
        university_id: str,
        title: str,
        description: str,
        generated_by: str = "professor_agent",
        source_data_collection_id: Optional[str] = None,
        implementation_details: Optional[str] = None,
        expected_improvement: Optional[float] = None
    ) -> ImprovementProposal:
        """Create an improvement proposal"""
        proposal = ImprovementProposal(
            id=str(uuid.uuid4()),
            university_id=university_id,
            title=title,
            description=description,
            generated_by=generated_by,
            source_data_collection_id=source_data_collection_id,
            implementation_details=implementation_details,
            expected_improvement=expected_improvement,
            validation_status="pending",
            implementation_status="not_started"
        )
        
        db.add(proposal)
        db.commit()
        db.refresh(proposal)
        
        return proposal
    
    @staticmethod
    def validate_improvement_proposal(
        db: Session,
        proposal_id: str,
        validation_status: str,
        validation_results: Dict[str, Any],
        validated_by: str
    ) -> Optional[ImprovementProposal]:
        """Validate an improvement proposal"""
        proposal = db.query(ImprovementProposal).filter(ImprovementProposal.id == proposal_id).first()
        
        if not proposal:
            return None
            
        proposal.validation_status = validation_status
        proposal.validation_results = validation_results
        proposal.validated_by = validated_by
        proposal.validated_at = datetime.now(timezone.utc)
        proposal.updated_at = datetime.now(timezone.utc)
        
        db.commit()
        db.refresh(proposal)
        
        return proposal
    
    @staticmethod
    def implement_improvement_proposal(
        db: Session,
        proposal_id: str,
        implementation_status: str
    ) -> Optional[ImprovementProposal]:
        """Update implementation status of a proposal"""
        proposal = db.query(ImprovementProposal).filter(ImprovementProposal.id == proposal_id).first()
        
        if not proposal:
            return None
            
        proposal.implementation_status = implementation_status
        if implementation_status == "completed":
            proposal.implemented_at = datetime.now(timezone.utc)
        proposal.updated_at = datetime.now(timezone.utc)
        
        db.commit()
        db.refresh(proposal)
        
        return proposal
    
    # ==================== Achievement Operations ====================
    
    @staticmethod
    def create_achievement(
        db: Session,
        name: str,
        description: str,
        criteria: Dict[str, Any],
        category: Optional[str] = None,
        difficulty: str = "easy",
        points: int = 10,
        required_count: int = 1
    ) -> Achievement:
        """Create a new achievement"""
        achievement = Achievement(
            id=str(uuid.uuid4()),
            name=name,
            description=description,
            category=category,
            difficulty=difficulty,
            points=points,
            criteria=criteria,
            required_count=required_count
        )
        
        db.add(achievement)
        db.commit()
        db.refresh(achievement)
        
        return achievement
    
    @staticmethod
    def award_achievement(
        db: Session,
        agent_id: str,
        achievement_id: str,
        progress: Optional[int] = None
    ) -> AgentAchievement:
        """Award an achievement to an agent"""
        # Check if already awarded
        existing = db.query(AgentAchievement).filter(
            and_(
                AgentAchievement.agent_id == agent_id,
                AgentAchievement.achievement_id == achievement_id
            )
        ).first()
        
        if existing:
            if progress is not None:
                existing.progress = progress
                if progress >= existing.achievement.required_count:
                    existing.is_completed = True
                db.commit()
                db.refresh(existing)
            return existing
            
        achievement = db.query(Achievement).filter(Achievement.id == achievement_id).first()
        if not achievement:
            raise ValueError("Achievement not found")
            
        agent_achievement = AgentAchievement(
            id=str(uuid.uuid4()),
            agent_id=agent_id,
            achievement_id=achievement_id,
            progress=progress or 0,
            is_completed=(progress or 0) >= achievement.required_count
        )
        
        db.add(agent_achievement)
        db.commit()
        db.refresh(agent_achievement)
        
        return agent_achievement
    
    @staticmethod
    def get_agent_achievements(
        db: Session,
        agent_id: str,
        completed_only: bool = False
    ) -> List[AgentAchievement]:
        """Get achievements for an agent"""
        query = db.query(AgentAchievement).filter(AgentAchievement.agent_id == agent_id)
        
        if completed_only:
            query = query.filter(AgentAchievement.is_completed == True)
            
        return query.all()
    
    # ==================== Analytics and Reporting ====================
    
    @staticmethod
    def get_university_analytics(db: Session, university_id: str) -> Dict[str, Any]:
        """Get comprehensive analytics for a university"""
        # Agent statistics
        total_agents = db.query(func.count(UniversityAgent.id)).filter(
            UniversityAgent.university_id == university_id
        ).scalar() or 0
        
        active_agents = db.query(func.count(UniversityAgent.id)).filter(
            and_(
                UniversityAgent.university_id == university_id,
                UniversityAgent.status == "active"
            )
        ).scalar() or 0
        
        # Training data statistics
        training_data_count = db.query(func.count(TrainingDataCollection.id)).filter(
            TrainingDataCollection.university_id == university_id
        ).scalar() or 0
        
        validated_data_count = db.query(func.count(TrainingDataCollection.id)).filter(
            and_(
                TrainingDataCollection.university_id == university_id,
                TrainingDataCollection.validation_status == "validated"
            )
        ).scalar() or 0
        
        # Improvement proposal statistics
        proposal_count = db.query(func.count(ImprovementProposal.id)).filter(
            ImprovementProposal.university_id == university_id
        ).scalar() or 0
        
        implemented_proposals = db.query(func.count(ImprovementProposal.id)).filter(
            and_(
                ImprovementProposal.university_id == university_id,
                ImprovementProposal.implementation_status == "completed"
            )
        ).scalar() or 0
        
        # Average competency score
        avg_competency = db.query(func.avg(UniversityAgent.competency_score)).filter(
            UniversityAgent.university_id == university_id
        ).scalar() or 0.0
        
        return {
            "university_id": university_id,
            "agent_statistics": {
                "total_agents": total_agents,
                "active_agents": active_agents,
                "average_competency": round(avg_competency, 3)
            },
            "training_data_statistics": {
                "total_collections": training_data_count,
                "validated_collections": validated_data_count,
                "validation_rate": round(validated_data_count / max(training_data_count, 1) * 100, 2)
            },
            "improvement_statistics": {
                "total_proposals": proposal_count,
                "implemented_proposals": implemented_proposals,
                "implementation_rate": round(implemented_proposals / max(proposal_count, 1) * 100, 2)
            }
        }