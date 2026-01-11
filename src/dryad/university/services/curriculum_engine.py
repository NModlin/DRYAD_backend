"""
Curriculum Engine for Uni0 - Manages curriculum progression and learning paths
"""

from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
import logging

from dryad.university.database.models_university import CurriculumPath, UniversityAgent, SkillTree, SkillNode, SkillProgress

logger = logging.getLogger(__name__)

class CurriculumEngine:
    """Engine for managing curriculum progression and learning paths"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def assign_curriculum(self, agent_id: int, curriculum_id: int) -> bool:
        """Assign a curriculum to an agent"""
        try:
            agent = self.db.query(UniversityAgent).filter(UniversityAgent.id == agent_id).first()
            curriculum = self.db.query(CurriculumPath).filter(CurriculumPath.id == curriculum_id).first()
            
            if not agent or not curriculum:
                logger.error(f"Agent {agent_id} or curriculum {curriculum_id} not found")
                return False
            
            # Verify agent and curriculum belong to same university
            if agent.university_id != curriculum.university_id:
                logger.error(f"Agent and curriculum belong to different universities")
                return False
            
            # Assign curriculum to agent
            agent.current_curriculum_id = curriculum_id
            agent.status = "learning"
            agent.updated_at = datetime.now(timezone.utc)
            
            # Initialize curriculum progress
            self._initialize_curriculum_progress(agent_id, curriculum_id)
            
            self.db.commit()
            logger.info(f"Curriculum {curriculum_id} assigned to agent {agent_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error assigning curriculum: {str(e)}")
            self.db.rollback()
            return False
    
    def _initialize_curriculum_progress(self, agent_id: int, curriculum_id: int):
        """Initialize curriculum progress tracking"""
        # This would set up initial progress tracking for the curriculum
        # For now, we'll just log the initialization
        logger.info(f"Initializing curriculum progress for agent {agent_id}, curriculum {curriculum_id}")
    
    def get_curriculum_progress(self, agent_id: int) -> Optional[Dict[str, Any]]:
        """Get current curriculum progress for an agent"""
        agent = self.db.query(UniversityAgent).filter(UniversityAgent.id == agent_id).first()
        if not agent or not agent.current_curriculum_id:
            return None
        
        curriculum = self.db.query(CurriculumPath).filter(CurriculumPath.id == agent.current_curriculum_id).first()
        if not curriculum:
            return None
        
        # Calculate progress based on completed skills/tasks
        # This is a simplified implementation
        total_skills = self.db.query(SkillNode).filter(
            SkillNode.skill_tree_id == curriculum.skill_tree_id
        ).count()
        
        completed_skills = self.db.query(SkillProgress).filter(
            SkillProgress.agent_id == agent_id,
            SkillProgress.status == "completed"
        ).count()
        
        progress_percentage = (completed_skills / total_skills * 100) if total_skills > 0 else 0
        
        return {
            "curriculum_id": curriculum.id,
            "curriculum_name": curriculum.name,
            "total_skills": total_skills,
            "completed_skills": completed_skills,
            "progress_percentage": progress_percentage,
            "estimated_remaining_hours": self._calculate_remaining_hours(
                curriculum.estimated_duration_hours, progress_percentage
            ),
            "current_difficulty": curriculum.difficulty_level
        }
    
    def _calculate_remaining_hours(self, total_hours: int, progress_percentage: float) -> float:
        """Calculate remaining hours based on progress"""
        completed_hours = (progress_percentage / 100) * total_hours
        return max(0, total_hours - completed_hours)
    
    def complete_skill(self, agent_id: int, skill_node_id: int) -> bool:
        """Mark a skill as completed for an agent"""
        try:
            # Check if skill exists and is part of agent's current curriculum
            agent = self.db.query(UniversityAgent).filter(UniversityAgent.id == agent_id).first()
            if not agent or not agent.current_curriculum_id:
                return False
            
            skill_node = self.db.query(SkillNode).filter(SkillNode.id == skill_node_id).first()
            if not skill_node or skill_node.skill_tree_id != curriculum.skill_tree_id:
                return False
            
            # Check if skill is already completed
            existing_progress = self.db.query(SkillProgress).filter(
                SkillProgress.agent_id == agent_id,
                SkillProgress.skill_node_id == skill_node_id
            ).first()
            
            if existing_progress:
                if existing_progress.status == "completed":
                    logger.info(f"Skill {skill_node_id} already completed for agent {agent_id}")
                    return True
                # Update existing progress
                existing_progress.status = "completed"
                existing_progress.completed_at = datetime.now(timezone.utc)
            else:
                # Create new progress record
                progress = SkillProgress(
                    agent_id=agent_id,
                    skill_node_id=skill_node_id,
                    status="completed",
                    completed_at=datetime.now(timezone.utc)
                )
                self.db.add(progress)
            
            self.db.commit()
            logger.info(f"Skill {skill_node_id} completed by agent {agent_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error completing skill: {str(e)}")
            self.db.rollback()
            return False
    
    def get_recommended_curricula(self, agent_id: int, limit: int = 5) -> List[Dict[str, Any]]:
        """Get recommended curricula for an agent based on their current skills and specialization"""
        agent = self.db.query(UniversityAgent).filter(UniversityAgent.id == agent_id).first()
        if not agent:
            return []
        
        # Get agent's current specialization
        specialization = agent.specialization
        
        # Query curricula that match the agent's specialization and difficulty level
        # This is a simplified recommendation algorithm
        recommended = self.db.query(CurriculumPath).filter(
            CurriculumPath.university_id == agent.university_id,
            CurriculumPath.status == "active"
        ).order_by(CurriculumPath.difficulty_level).limit(limit).all()
        
        recommendations = []
        for curriculum in recommended:
            # Calculate match score based on specialization and difficulty
            match_score = self._calculate_curriculum_match_score(curriculum, agent)
            
            recommendations.append({
                "curriculum_id": curriculum.id,
                "name": curriculum.name,
                "description": curriculum.description,
                "difficulty_level": curriculum.difficulty_level,
                "estimated_duration_hours": curriculum.estimated_duration_hours,
                "match_score": match_score,
                "prerequisites": curriculum.prerequisites or []
            })
        
        # Sort by match score (descending)
        recommendations.sort(key=lambda x: x["match_score"], reverse=True)
        return recommendations
    
    def _calculate_curriculum_match_score(self, curriculum: CurriculumPath, agent: UniversityAgent) -> float:
        """Calculate how well a curriculum matches an agent's profile"""
        score = 0.0
        
        # Base score for active curriculum
        if curriculum.status == "active":
            score += 0.3
        
        # Difficulty level matching (simplified)
        difficulty_bonus = {
            "beginner": 0.1,
            "intermediate": 0.2,
            "advanced": 0.3,
            "expert": 0.4
        }
        score += difficulty_bonus.get(curriculum.difficulty_level, 0.1)
        
        # Specialization matching (if curriculum has specialization requirements)
        # This would be more sophisticated in a real implementation
        
        return min(1.0, score)
    
    def generate_learning_path(self, curriculum_id: int) -> List[Dict[str, Any]]:
        """Generate a learning path for a curriculum"""
        curriculum = self.db.query(CurriculumPath).filter(CurriculumPath.id == curriculum_id).first()
        if not curriculum:
            return []
        
        # Get all skill nodes for this curriculum, ordered by prerequisite dependencies
        skill_nodes = self.db.query(SkillNode).filter(
            SkillNode.skill_tree_id == curriculum.skill_tree_id
        ).order_by(SkillNode.order_index).all()
        
        learning_path = []
        for skill_node in skill_nodes:
            learning_path.append({
                "skill_node_id": skill_node.id,
                "name": skill_node.name,
                "description": skill_node.description,
                "skill_type": skill_node.skill_type,
                "prerequisites": skill_node.prerequisites or [],
                "estimated_duration_hours": skill_node.estimated_duration_hours,
                "order_index": skill_node.order_index
            })
        
        return learning_path
    
    def assess_curriculum_completion(self, agent_id: int) -> bool:
        """Assess if an agent has completed their current curriculum"""
        progress = self.get_curriculum_progress(agent_id)
        if not progress:
            return False
        
        # Consider curriculum completed if progress is 100%
        if progress["progress_percentage"] >= 100:
            agent = self.db.query(UniversityAgent).filter(UniversityAgent.id == agent_id).first()
            if agent:
                agent.status = "completed"
                agent.updated_at = datetime.now(timezone.utc)
                self.db.commit()
                logger.info(f"Agent {agent_id} completed curriculum {agent.current_curriculum_id}")
                return True
        
        return False

# Utility functions
def create_curriculum_engine(db: Session) -> CurriculumEngine:
    """Factory function to create curriculum engine"""
    return CurriculumEngine(db)

def validate_curriculum_assignment(agent_id: int, curriculum_id: int, db: Session) -> bool:
    """Validate if an agent can be assigned to a curriculum"""
    engine = CurriculumEngine(db)
    
    # Check if agent exists and is active
    agent = db.query(UniversityAgent).filter(UniversityAgent.id == agent_id).first()
    if not agent or agent.status != "active":
        return False
    
    # Check if curriculum exists and is active
    curriculum = db.query(CurriculumPath).filter(CurriculumPath.id == curriculum_id).first()
    if not curriculum or curriculum.status != "active":
        return False
    
    # Check if agent already has a curriculum assigned
    if agent.current_curriculum_id:
        return False
    
    return True