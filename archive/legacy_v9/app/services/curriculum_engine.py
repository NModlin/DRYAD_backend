"""
Curriculum Engine

Provides intelligent curriculum management for the Agentic University System.
Handles curriculum paths, levels, challenges, and agent progress tracking.
"""

import uuid
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc

from app.database.models_university import (
    CurriculumPath, CurriculumLevel, CurriculumChallenge, 
    AgentProgress, UniversityAgent
)


class CurriculumEngine:
    """Intelligent curriculum management engine"""
    
    @staticmethod
    def create_curriculum_path(
        db: Session,
        university_id: str,
        name: str,
        description: str,
        difficulty: str = "beginner",
        prerequisites: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> CurriculumPath:
        """Create a new curriculum path"""
        path = CurriculumPath(
            id=str(uuid.uuid4()),
            university_id=university_id,
            name=name,
            description=description,
            difficulty=difficulty,
            prerequisites=prerequisites or [],
            metadata=metadata or {},
            status="active"
        )
        
        db.add(path)
        db.commit()
        db.refresh(path)
        
        return path
    
    @staticmethod
    def create_curriculum_level(
        db: Session,
        path_id: str,
        name: str,
        description: str,
        order_index: int,
        learning_objectives: List[str],
        estimated_duration_hours: int = 10,
        prerequisites: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> CurriculumLevel:
        """Create a new curriculum level"""
        level = CurriculumLevel(
            id=str(uuid.uuid4()),
            path_id=path_id,
            name=name,
            description=description,
            order_index=order_index,
            learning_objectives=learning_objectives,
            estimated_duration_hours=estimated_duration_hours,
            prerequisites=prerequisites or [],
            metadata=metadata or {},
            status="active"
        )
        
        db.add(level)
        db.commit()
        db.refresh(level)
        
        return level
    
    @staticmethod
    def create_curriculum_challenge(
        db: Session,
        level_id: str,
        name: str,
        description: str,
        challenge_type: str,
        difficulty: str = "easy",
        content: Dict[str, Any] = None,
        expected_output: Optional[Any] = None,
        scoring_criteria: Dict[str, Any] = None,
        time_limit_minutes: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> CurriculumChallenge:
        """Create a new curriculum challenge"""
        if content is None:
            content = {}
        if scoring_criteria is None:
            scoring_criteria = {}
            
        challenge = CurriculumChallenge(
            id=str(uuid.uuid4()),
            level_id=level_id,
            name=name,
            description=description,
            challenge_type=challenge_type,
            difficulty=difficulty,
            content=content,
            expected_output=expected_output,
            scoring_criteria=scoring_criteria,
            time_limit_minutes=time_limit_minutes,
            metadata=metadata or {},
            status="active"
        )
        
        db.add(challenge)
        db.commit()
        db.refresh(challenge)
        
        return challenge
    
    @staticmethod
    def enroll_agent_in_path(
        db: Session,
        agent_id: str,
        path_id: str
    ) -> AgentProgress:
        """Enroll an agent in a curriculum path"""
        # Get the curriculum path and its levels
        path = db.query(CurriculumPath).filter(CurriculumPath.id == path_id).first()
        if not path:
            raise ValueError("Curriculum path not found")
        
        # Get the first level in the path
        first_level = db.query(CurriculumLevel).filter(
            CurriculumLevel.path_id == path_id
        ).order_by(CurriculumLevel.order_index).first()
        
        if not first_level:
            raise ValueError("No levels found in curriculum path")
        
        # Get challenges for the first level
        challenges = db.query(CurriculumChallenge).filter(
            CurriculumChallenge.level_id == first_level.id
        ).all()
        
        # Create agent progress record
        progress = AgentProgress(
            id=str(uuid.uuid4()),
            agent_id=agent_id,
            curriculum_path_id=path_id,
            curriculum_level_id=first_level.id,
            total_challenges=len(challenges),
            status="not_started"
        )
        
        db.add(progress)
        db.commit()
        db.refresh(progress)
        
        return progress
    
    @staticmethod
    def get_next_challenge(
        db: Session,
        agent_id: str
    ) -> Optional[Tuple[CurriculumChallenge, AgentProgress]]:
        """Get the next challenge for an agent"""
        # Get current progress
        progress = db.query(AgentProgress).filter(
            AgentProgress.agent_id == agent_id,
            AgentProgress.status.in_(["not_started", "in_progress"])
        ).first()
        
        if not progress:
            return None
        
        # Get challenges for current level
        challenges = db.query(CurriculumChallenge).filter(
            CurriculumChallenge.level_id == progress.curriculum_level_id
        ).order_by(CurriculumChallenge.order_index).all()
        
        if not challenges:
            return None
        
        # Find the next challenge based on current progress
        if progress.current_challenge_index is None:
            next_challenge_index = 0
        else:
            next_challenge_index = progress.current_challenge_index + 1
        
        if next_challenge_index >= len(challenges):
            # Move to next level
            return CurriculumEngine._advance_to_next_level(db, agent_id, progress)
        
        next_challenge = challenges[next_challenge_index]
        return next_challenge, progress
    
    @staticmethod
    def _advance_to_next_level(
        db: Session,
        agent_id: str,
        current_progress: AgentProgress
    ) -> Optional[Tuple[CurriculumChallenge, AgentProgress]]:
        """Advance agent to the next curriculum level"""
        # Get current level
        current_level = db.query(CurriculumLevel).filter(
            CurriculumLevel.id == current_progress.curriculum_level_id
        ).first()
        
        if not current_level:
            return None
        
        # Get next level in the path
        next_level = db.query(CurriculumLevel).filter(
            CurriculumLevel.path_id == current_level.path_id,
            CurriculumLevel.order_index > current_level.order_index
        ).order_by(CurriculumLevel.order_index).first()
        
        if not next_level:
            # Path completed
            current_progress.status = "completed"
            current_progress.completed_at = datetime.now(timezone.utc)
            db.commit()
            return None
        
        # Get challenges for next level
        challenges = db.query(CurriculumChallenge).filter(
            CurriculumChallenge.level_id == next_level.id
        ).all()
        
        # Update progress to next level
        current_progress.curriculum_level_id = next_level.id
        current_progress.current_challenge_index = 0
        current_progress.total_challenges = len(challenges)
        current_progress.status = "in_progress"
        current_progress.last_activity_at = datetime.now(timezone.utc)
        
        db.commit()
        db.refresh(current_progress)
        
        # Get first challenge of next level
        first_challenge = db.query(CurriculumChallenge).filter(
            CurriculumChallenge.level_id == next_level.id
        ).order_by(CurriculumChallenge.order_index).first()
        
        return first_challenge, current_progress
    
    @staticmethod
    def submit_challenge_result(
        db: Session,
        agent_id: str,
        challenge_id: str,
        agent_response: Dict[str, Any],
        score: float,
        time_spent_minutes: int,
        evaluation_metrics: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Submit challenge result and update agent progress"""
        # Get challenge and progress
        challenge = db.query(CurriculumChallenge).filter(CurriculumChallenge.id == challenge_id).first()
        if not challenge:
            raise ValueError("Challenge not found")
        
        progress = db.query(AgentProgress).filter(
            AgentProgress.agent_id == agent_id,
            AgentProgress.curriculum_level_id == challenge.level_id
        ).first()
        
        if not progress:
            raise ValueError("Agent progress not found for this level")
        
        # Update progress
        if progress.current_challenge_index is None:
            current_index = 0
        else:
            current_index = progress.current_challenge_index
        
        # Add challenge result
        challenge_results = list(progress.challenge_results)
        challenge_results.append({
            "challenge_id": challenge_id,
            "challenge_index": current_index,
            "agent_response": agent_response,
            "score": score,
            "time_spent_minutes": time_spent_minutes,
            "evaluation_metrics": evaluation_metrics or {},
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        progress.challenge_results = challenge_results
        
        # Update progress metrics
        progress.current_challenge_index = current_index + 1
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
        
        progress.challenges_completed += 1
        progress.last_activity_at = datetime.now(timezone.utc)
        
        # Check if level is completed
        if progress.current_challenge_index >= progress.total_challenges:
            progress.status = "level_completed"
            progress.level_completed_at = datetime.now(timezone.utc)
        
        db.commit()
        db.refresh(progress)
        
        # Update agent competency based on performance
        agent = db.query(UniversityAgent).filter(UniversityAgent.id == agent_id).first()
        if agent:
            # Simple competency calculation based on average score
            new_competency = min(1.0, progress.average_score * 0.1)  # Scale to 0-1
            agent.competency_score = max(agent.competency_score or 0.0, new_competency)
            agent.training_hours = (agent.training_hours or 0.0) + (time_spent_minutes / 60.0)
            db.commit()
        
        return {
            "challenge_id": challenge_id,
            "score": score,
            "current_progress": {
                "challenges_completed": progress.challenges_completed,
                "total_challenges": progress.total_challenges,
                "average_score": progress.average_score,
                "best_score": progress.best_score,
                "time_spent_minutes": progress.time_spent_minutes
            },
            "level_status": progress.status
        }
    
    @staticmethod
    def get_agent_progress_summary(
        db: Session,
        agent_id: str
    ) -> Dict[str, Any]:
        """Get comprehensive progress summary for an agent"""
        # Get all progress records for the agent
        progress_records = db.query(AgentProgress).filter(
            AgentProgress.agent_id == agent_id
        ).all()
        
        if not progress_records:
            return {"agent_id": agent_id, "progress": []}
        
        summary = {
            "agent_id": agent_id,
            "total_paths_started": len(progress_records),
            "total_paths_completed": len([p for p in progress_records if p.status == "completed"]),
            "total_challenges_completed": sum(p.challenges_completed for p in progress_records),
            "total_time_spent_hours": sum(p.time_spent_minutes for p in progress_records) / 60.0,
            "overall_average_score": sum(p.average_score for p in progress_records) / len(progress_records) if progress_records else 0.0,
            "progress_by_path": []
        }
        
        for progress in progress_records:
            path = db.query(CurriculumPath).filter(CurriculumPath.id == progress.curriculum_path_id).first()
            level = db.query(CurriculumLevel).filter(CurriculumLevel.id == progress.curriculum_level_id).first()
            
            path_summary = {
                "path_id": progress.curriculum_path_id,
                "path_name": path.name if path else "Unknown",
                "current_level_id": progress.curriculum_level_id,
                "current_level_name": level.name if level else "Unknown",
                "challenges_completed": progress.challenges_completed,
                "total_challenges": progress.total_challenges,
                "completion_percentage": (progress.challenges_completed / progress.total_challenges * 100) if progress.total_challenges > 0 else 0,
                "average_score": progress.average_score,
                "best_score": progress.best_score,
                "time_spent_hours": progress.time_spent_minutes / 60.0,
                "status": progress.status,
                "last_activity": progress.last_activity_at.isoformat() if progress.last_activity_at else None
            }
            
            summary["progress_by_path"].append(path_summary)
        
        return summary
    
    @staticmethod
    def recommend_next_path(
        db: Session,
        agent_id: str,
        university_id: str
    ) -> Optional[CurriculumPath]:
        """Recommend the next curriculum path for an agent based on their progress and skills"""
        # Get agent's current skills and progress
        agent = db.query(UniversityAgent).filter(UniversityAgent.id == agent_id).first()
        if not agent:
            return None
        
        # Get all available paths in the university
        available_paths = db.query(CurriculumPath).filter(
            CurriculumPath.university_id == university_id,
            CurriculumPath.status == "active"
        ).all()
        
        if not available_paths:
            return None
        
        # Get agent's completed paths
        completed_paths = db.query(AgentProgress).filter(
            AgentProgress.agent_id == agent_id,
            AgentProgress.status == "completed"
        ).all()
        
        completed_path_ids = [p.curriculum_path_id for p in completed_paths]
        
        # Filter out completed paths
        candidate_paths = [p for p in available_paths if p.id not in completed_path_ids]
        
        if not candidate_paths:
            return None
        
        # Simple recommendation algorithm based on difficulty and prerequisites
        # In a real implementation, this would use ML to match agent skills with path requirements
        
        # Sort by difficulty (beginner first) and then by prerequisites match
        def path_score(path: CurriculumPath) -> Tuple[int, int]:
            # Difficulty score (lower is better)
            difficulty_scores = {"beginner": 0, "intermediate": 1, "advanced": 2, "expert": 3}
            difficulty_score = difficulty_scores.get(path.difficulty, 4)
            
            # Prerequisites match score (higher is better)
            prereq_match = 0
            if path.prerequisites:
                # Check how many prerequisites the agent has completed
                completed_prereqs = set(completed_path_ids) & set(path.prerequisites)
                prereq_match = len(completed_prereqs)
            
            return (difficulty_score, -prereq_match)  # Negative for reverse sort
        
        candidate_paths.sort(key=path_score)
        
        return candidate_paths[0] if candidate_paths else None
    
    @staticmethod
    def generate_learning_analytics(
        db: Session,
        university_id: str,
        time_period: str = "all"  # "day", "week", "month", "all"
    ) -> Dict[str, Any]:
        """Generate learning analytics for a university"""
        # Calculate time range based on period
        now = datetime.now(timezone.utc)
        if time_period == "day":
            start_time = now.replace(hour=0, minute=0, second=0, microsecond=0)
        elif time_period == "week":
            start_time = now - timedelta(days=7)
        elif time_period == "month":
            start_time = now - timedelta(days=30)
        else:  # "all"
            start_time = datetime.min.replace(tzinfo=timezone.utc)
        
        # Get all agents in the university
        agents = db.query(UniversityAgent).filter(
            UniversityAgent.university_id == university_id
        ).all()
        
        # Get all progress records for these agents
        agent_ids = [agent.id for agent in agents]
        progress_records = db.query(AgentProgress).filter(
            AgentProgress.agent_id.in_(agent_ids),
            AgentProgress.last_activity_at >= start_time
        ).all()
        
        # Calculate analytics
        total_agents = len(agents)
        active_agents = len([a for a in agents if a.status == "active"])
        
        total_challenges_completed = sum(p.challenges_completed for p in progress_records)
        total_time_spent_hours = sum(p.time_spent_minutes for p in progress_records) / 60.0
        
        average_scores = [p.average_score for p in progress_records if p.average_score > 0]
        overall_average_score = sum(average_scores) / len(average_scores) if average_scores else 0.0
        
        # Completion rates
        completed_paths = len([p for p in progress_records if p.status == "completed"])
        total_paths_started = len(progress_records)
        completion_rate = (completed_paths / total_paths_started * 100) if total_paths_started > 0 else 0
        
        return {
            "university_id": university_id,
            "time_period": time_period,
            "agent_statistics": {
                "total_agents": total_agents,
                "active_agents": active_agents,
                "active_percentage": (active_agents / total_agents * 100) if total_agents > 0 else 0
            },
            "learning_statistics": {
                "total_challenges_completed": total_challenges_completed,
                "total_time_spent_hours": total_time_spent_hours,
                "average_score": round(overall_average_score, 3),
                "completion_rate": round(completion_rate, 2)
            },
            "time_period_start": start_time.isoformat(),
            "generated_at": now.isoformat()
        }