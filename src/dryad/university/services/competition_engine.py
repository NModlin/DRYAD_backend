"""
Competition Engine for Uni0 - Manages competitions and participant rankings
"""

from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
import logging
import random
import uuid

from dryad.university.database.models_university import Competition, CompetitionParticipant, UniversityAgent

logger = logging.getLogger(__name__)

class CompetitionEngine:
    """Engine for managing competitions and participant rankings"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def join_competition(self, agent_id: int, competition_id: int) -> bool:
        """Join an agent to a competition"""
        try:
            agent = self.db.query(UniversityAgent).filter(UniversityAgent.id == agent_id).first()
            competition = self.db.query(Competition).filter(Competition.id == competition_id).first()
            
            if not agent or not competition:
                logger.error(f"Agent {agent_id} or competition {competition_id} not found")
                return False
            
            # Verify agent and competition belong to same university
            if agent.university_id != competition.university_id:
                logger.error(f"Agent and competition belong to different universities")
                return False
            
            # Check if competition is active
            if competition.status != "active":
                logger.error(f"Competition {competition_id} is not active")
                return False
            
            # Check if agent is already participating
            existing_participation = self.db.query(CompetitionParticipant).filter(
                CompetitionParticipant.agent_id == agent_id,
                CompetitionParticipant.competition_id == competition_id
            ).first()
            
            if existing_participation:
                logger.info(f"Agent {agent_id} is already participating in competition {competition_id}")
                return True
            
            # Check if competition has reached maximum participants
            current_participants = self.db.query(CompetitionParticipant).filter(
                CompetitionParticipant.competition_id == competition_id,
                CompetitionParticipant.status == "active"
            ).count()
            
            if current_participants >= competition.max_participants:
                logger.error(f"Competition {competition_id} has reached maximum participants")
                return False
            
            # Create participation record
            participation = CompetitionParticipant(
                id=str(uuid.uuid4()),
                competition_id=competition_id,
                agent_id=agent_id,
                status="active"
            )
            
            self.db.add(participation)
            self.db.commit()
            logger.info(f"Agent {agent_id} joined competition {competition_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error joining competition: {str(e)}")
            self.db.rollback()
            return False
    
    def leave_competition(self, agent_id: int, competition_id: int) -> bool:
        """Remove an agent from a competition"""
        try:
            participation = self.db.query(CompetitionParticipant).filter(
                CompetitionParticipant.agent_id == agent_id,
                CompetitionParticipant.competition_id == competition_id
            ).first()
            
            if not participation:
                logger.error(f"Agent {agent_id} is not participating in competition {competition_id}")
                return False
            
            participation.status = "withdrawn"
            participation.last_updated = datetime.now(timezone.utc)
            
            self.db.commit()
            logger.info(f"Agent {agent_id} left competition {competition_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error leaving competition: {str(e)}")
            self.db.rollback()
            return False
    
    def update_score(self, agent_id: int, competition_id: int, score: float) -> bool:
        """Update an agent's score in a competition"""
        try:
            participation = self.db.query(CompetitionParticipant).filter(
                CompetitionParticipant.agent_id == agent_id,
                CompetitionParticipant.competition_id == competition_id,
                CompetitionParticipant.status == "active"
            ).first()
            
            if not participation:
                logger.error(f"Active participation not found for agent {agent_id} in competition {competition_id}")
                return False
            
            participation.score = score
            participation.last_updated = datetime.now(timezone.utc)
            
            self.db.commit()
            
            # Update rankings after score change
            self._update_rankings(competition_id)
            
            logger.info(f"Updated score for agent {agent_id} in competition {competition_id}: {score}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating score: {str(e)}")
            self.db.rollback()
            return False
    
    def _update_rankings(self, competition_id: int):
        """Update rankings for all participants in a competition"""
        try:
            # Get all active participants ordered by score (descending)
            participants = self.db.query(CompetitionParticipant).filter(
                CompetitionParticipant.competition_id == competition_id,
                CompetitionParticipant.status == "active"
            ).order_by(CompetitionParticipant.score.desc()).all()
            
            # Assign ranks
            for rank, participant in enumerate(participants, 1):
                participant.rank = rank
                participant.last_updated = datetime.now(timezone.utc)
            
            self.db.commit()
            logger.debug(f"Updated rankings for competition {competition_id}")
            
        except Exception as e:
            logger.error(f"Error updating rankings: {str(e)}")
            self.db.rollback()
    
    def get_leaderboard(self, competition_id: int, limit: int = 10) -> List[Dict[str, Any]]:
        """Get competition leaderboard"""
        competition = self.db.query(Competition).filter(Competition.id == competition_id).first()
        if not competition:
            return []
        
        participants = self.db.query(CompetitionParticipant).filter(
            CompetitionParticipant.competition_id == competition_id,
            CompetitionParticipant.status == "active"
        ).order_by(CompetitionParticipant.score.desc()).limit(limit).all()
        
        leaderboard = []
        for participant in participants:
            agent = self.db.query(UniversityAgent).filter(UniversityAgent.id == participant.agent_id).first()
            if agent:
                leaderboard.append({
                    "rank": participant.rank,
                    "agent_id": agent.id,
                    "agent_name": agent.name,
                    "score": participant.score,
                    "specialization": agent.specialization,
                    "joined_at": participant.joined_at.isoformat(),
                    "last_updated": participant.last_updated.isoformat()
                })
        
        return leaderboard
    
    def get_competition_stats(self, competition_id: int) -> Optional[Dict[str, Any]]:
        """Get detailed statistics for a competition"""
        competition = self.db.query(Competition).filter(Competition.id == competition_id).first()
        if not competition:
            return None
        
        # Get participant statistics
        total_participants = self.db.query(CompetitionParticipant).filter(
            CompetitionParticipant.competition_id == competition_id
        ).count()
        
        active_participants = self.db.query(CompetitionParticipant).filter(
            CompetitionParticipant.competition_id == competition_id,
            CompetitionParticipant.status == "active"
        ).count()
        
        withdrawn_participants = total_participants - active_participants
        
        # Get score statistics
        active_scores = self.db.query(CompetitionParticipant.score).filter(
            CompetitionParticipant.competition_id == competition_id,
            CompetitionParticipant.status == "active",
            CompetitionParticipant.score.isnot(None)
        ).all()
        
        scores = [score[0] for score in active_scores if score[0] is not None]
        
        if scores:
            avg_score = sum(scores) / len(scores)
            max_score = max(scores)
            min_score = min(scores)
        else:
            avg_score = max_score = min_score = 0
        
        return {
            "competition_id": competition_id,
            "name": competition.name,
            "statistics": {
                "participants": {
                    "total": total_participants,
                    "active": active_participants,
                    "withdrawn": withdrawn_participants,
                    "capacity_usage": f"{(active_participants / competition.max_participants * 100):.1f}%"
                },
                "scores": {
                    "average": avg_score,
                    "maximum": max_score,
                    "minimum": min_score,
                    "participants_with_scores": len(scores)
                },
                "duration": {
                    "start_date": competition.start_date.isoformat() if competition.start_date else "N/A",
                    "end_date": competition.end_date.isoformat() if competition.end_date else "N/A",
                    "status": competition.status
                }
            }
        }
    
    def start_competition(self, competition_id: int) -> bool:
        """Start a competition"""
        try:
            competition = self.db.query(Competition).filter(Competition.id == competition_id).first()
            if not competition:
                return False
            
            if competition.status != "pending":
                logger.error(f"Competition {competition_id} cannot be started from status {competition.status}")
                return False
            
            competition.status = "active"
            competition.start_date = datetime.now(timezone.utc)
            self.db.commit()
            
            logger.info(f"Competition {competition_id} started")
            return True
            
        except Exception as e:
            logger.error(f"Error starting competition: {str(e)}")
            self.db.rollback()
            return False
    
    def end_competition(self, competition_id: int) -> bool:
        """End a competition and distribute rewards"""
        try:
            competition = self.db.query(Competition).filter(Competition.id == competition_id).first()
            if not competition:
                return False
            
            if competition.status != "active":
                logger.error(f"Competition {competition_id} cannot be ended from status {competition.status}")
                return False
            
            competition.status = "completed"
            competition.end_date = datetime.now(timezone.utc)
            
            # Distribute rewards to top participants
            self._distribute_rewards(competition_id)
            
            self.db.commit()
            logger.info(f"Competition {competition_id} ended")
            return True
            
        except Exception as e:
            logger.error(f"Error ending competition: {str(e)}")
            self.db.rollback()
            return False
    
    def _distribute_rewards(self, competition_id: int):
        """Distribute rewards to competition winners"""
        competition = self.db.query(Competition).filter(Competition.id == competition_id).first()
        if not competition or not competition.rewards:
            return
        
        rewards = competition.rewards
        leaderboard = self.get_leaderboard(competition_id, limit=10)  # Top 10
        
        # Distribute rewards based on rank
        for participant in leaderboard:
            rank = participant["rank"]
            agent_id = participant["agent_id"]
            
            # Determine reward based on rank
            reward = self._calculate_reward(rank, rewards)
            
            if reward:
                # In a real implementation, you'd update agent's rewards/achievements
                logger.info(f"Distributed reward to agent {agent_id} (rank {rank}): {reward}")
    
    def _calculate_reward(self, rank: int, rewards: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Calculate reward based on rank and competition rewards configuration"""
        if not rewards:
            return None
        
        # Simple reward calculation based on rank
        reward_tiers = rewards.get("tiers", {})
        
        if rank == 1 and "first" in reward_tiers:
            return reward_tiers["first"]
        elif rank == 2 and "second" in reward_tiers:
            return reward_tiers["second"]
        elif rank == 3 and "third" in reward_tiers:
            return reward_tiers["third"]
        elif rank <= 10 and "top_10" in reward_tiers:
            return reward_tiers["top_10"]
        elif "participation" in reward_tiers:
            return reward_tiers["participation"]
        
        return None
    
    def generate_competition_challenge(self, competition_id: int, agent_id: int) -> Optional[Dict[str, Any]]:
        """Generate a challenge for an agent in a competition"""
        competition = self.db.query(Competition).filter(Competition.id == competition_id).first()
        if not competition:
            return None
        
        # Generate challenge based on competition type
        competition_type = competition.competition_type
        
        if competition_type == "skill_challenge":
            return self._generate_skill_challenge(competition, agent_id)
        elif competition_type == "problem_solving":
            return self._generate_problem_challenge(competition, agent_id)
        elif competition_type == "creative_task":
            return self._generate_creative_challenge(competition, agent_id)
        else:
            return self._generate_generic_challenge(competition, agent_id)
    
    def _generate_skill_challenge(self, competition: Competition, agent_id: int) -> Dict[str, Any]:
        """Generate a skill-based challenge"""
        return {
            "type": "skill_challenge",
            "description": f"Demonstrate your {competition.name} skills",
            "difficulty": "medium",
            "estimated_duration": "30 minutes",
            "evaluation_criteria": ["accuracy", "efficiency", "creativity"],
            "max_score": 100
        }
    
    def _generate_problem_challenge(self, competition: Competition, agent_id: int) -> Dict[str, Any]:
        """Generate a problem-solving challenge"""
        return {
            "type": "problem_solving",
            "description": f"Solve this complex problem related to {competition.name}",
            "difficulty": "hard",
            "estimated_duration": "60 minutes",
            "evaluation_criteria": ["solution_quality", "approach", "explanation"],
            "max_score": 100
        }
    
    def _generate_creative_challenge(self, competition: Competition, agent_id: int) -> Dict[str, Any]:
        """Generate a creative task challenge"""
        return {
            "type": "creative_task",
            "description": f"Create something innovative related to {competition.name}",
            "difficulty": "variable",
            "estimated_duration": "90 minutes",
            "evaluation_criteria": ["originality", "execution", "impact"],
            "max_score": 100
        }
    
    def _generate_generic_challenge(self, competition: Competition, agent_id: int) -> Dict[str, Any]:
        """Generate a generic challenge"""
        return {
            "type": "generic",
            "description": f"Participate in {competition.name}",
            "difficulty": "medium",
            "estimated_duration": "45 minutes",
            "evaluation_criteria": ["performance", "completion"],
            "max_score": 100
        }

# Utility functions
def create_competition_engine(db: Session) -> CompetitionEngine:
    """Factory function to create competition engine"""
    return CompetitionEngine(db)

def validate_competition_join(agent_id: int, competition_id: int, db: Session) -> bool:
    """Validate if an agent can join a competition"""
    engine = CompetitionEngine(db)
    
    # Check if agent exists and is active
    agent = db.query(UniversityAgent).filter(UniversityAgent.id == agent_id).first()
    if not agent or agent.status != "active":
        return False
    
    # Check if competition exists and is active
    competition = db.query(Competition).filter(Competition.id == competition_id).first()
    if not competition or competition.status != "active":
        return False
    
    # Check if agent already has a competition assigned
    existing_participation = db.query(CompetitionParticipant).filter(
        CompetitionParticipant.agent_id == agent_id,
        CompetitionParticipant.competition_id == competition_id
    ).first()
    
    if existing_participation:
        return False
    
    return True