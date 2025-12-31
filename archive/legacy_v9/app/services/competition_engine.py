"""
Competition Engine

Provides intelligent competition management for the Agentic University System.
Handles competition creation, agent matching, scoring, and ranking systems.
"""

import uuid
import random
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc

from app.database.models_university import (
    Competition, CompetitionParticipant, CompetitionMatch, 
    UniversityAgent, CompetitionLeaderboard
)


class CompetitionEngine:
    """Intelligent competition management engine"""
    
    @staticmethod
    def create_competition(
        db: Session,
        university_id: str,
        name: str,
        description: str,
        competition_type: str = "head_to_head",
        rules: Dict[str, Any] = None,
        scoring_system: Dict[str, Any] = None,
        max_participants: Optional[int] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Competition:
        """Create a new competition"""
        if rules is None:
            rules = {}
        if scoring_system is None:
            scoring_system = {}
            
        competition = Competition(
            id=str(uuid.uuid4()),
            university_id=university_id,
            name=name,
            description=description,
            competition_type=competition_type,
            rules=rules,
            scoring_system=scoring_system,
            max_participants=max_participants,
            start_time=start_time or datetime.now(timezone.utc),
            end_time=end_time,
            metadata=metadata or {},
            status="scheduled"
        )
        
        db.add(competition)
        db.commit()
        db.refresh(competition)
        
        return competition
    
    @staticmethod
    def register_agent(
        db: Session,
        competition_id: str,
        agent_id: str
    ) -> CompetitionParticipant:
        """Register an agent for a competition"""
        # Check if competition exists and is open for registration
        competition = db.query(Competition).filter(Competition.id == competition_id).first()
        if not competition:
            raise ValueError("Competition not found")
        
        if competition.status not in ["scheduled", "registration_open"]:
            raise ValueError("Competition is not open for registration")
        
        # Check if agent exists and is active
        agent = db.query(UniversityAgent).filter(UniversityAgent.id == agent_id).first()
        if not agent or agent.status != "active":
            raise ValueError("Agent not found or not active")
        
        # Check if agent is already registered
        existing = db.query(CompetitionParticipant).filter(
            CompetitionParticipant.competition_id == competition_id,
            CompetitionParticipant.agent_id == agent_id
        ).first()
        
        if existing:
            return existing
        
        # Check participant limit
        if competition.max_participants:
            current_participants = db.query(CompetitionParticipant).filter(
                CompetitionParticipant.competition_id == competition_id
            ).count()
            
            if current_participants >= competition.max_participants:
                raise ValueError("Competition is full")
        
        # Register agent
        participant = CompetitionParticipant(
            id=str(uuid.uuid4()),
            competition_id=competition_id,
            agent_id=agent_id,
            registration_time=datetime.now(timezone.utc),
            status="registered"
        )
        
        db.add(participant)
        db.commit()
        db.refresh(participant)
        
        return participant
    
    @staticmethod
    def start_competition(
        db: Session,
        competition_id: str
    ) -> Competition:
        """Start a competition"""
        competition = db.query(Competition).filter(Competition.id == competition_id).first()
        if not competition:
            raise ValueError("Competition not found")
        
        if competition.status != "scheduled":
            raise ValueError("Competition cannot be started in current state")
        
        # Check if there are enough participants
        participant_count = db.query(CompetitionParticipant).filter(
            CompetitionParticipant.competition_id == competition_id
        ).count()
        
        if participant_count < 2:
            raise ValueError("Competition requires at least 2 participants")
        
        # Update competition status
        competition.status = "in_progress"
        competition.actual_start_time = datetime.now(timezone.utc)
        db.commit()
        db.refresh(competition)
        
        # Create initial matches based on competition type
        CompetitionEngine._create_initial_matches(db, competition)
        
        return competition
    
    @staticmethod
    def _create_initial_matches(db: Session, competition: Competition) -> None:
        """Create initial matches for a competition based on its type"""
        participants = db.query(CompetitionParticipant).filter(
            CompetitionParticipant.competition_id == competition.id
        ).all()
        
        if competition.competition_type == "head_to_head":
            # Create round-robin or elimination matches
            CompetitionEngine._create_head_to_head_matches(db, competition, participants)
        elif competition.competition_type == "challenge_based":
            # Create challenge-based matches
            CompetitionEngine._create_challenge_based_matches(db, competition, participants)
        # Add more competition types as needed
    
    @staticmethod
    def _create_head_to_head_matches(db: Session, competition: Competition, participants: List[CompetitionParticipant]) -> None:
        """Create head-to-head matches (round-robin style)"""
        participant_ids = [p.agent_id for p in participants]
        
        # Simple round-robin pairing (for demonstration)
        # In a real implementation, this would use more sophisticated matching
        for i in range(0, len(participant_ids) - 1, 2):
            if i + 1 < len(participant_ids):
                match = CompetitionMatch(
                    id=str(uuid.uuid4()),
                    competition_id=competition.id,
                    participant1_id=participant_ids[i],
                    participant2_id=participant_ids[i + 1],
                    match_type="head_to_head",
                    status="scheduled",
                    scheduled_time=datetime.now(timezone.utc)
                )
                db.add(match)
        
        db.commit()
    
    @staticmethod
    def _create_challenge_based_matches(db: Session, competition: Competition, participants: List[CompetitionParticipant]) -> None:
        """Create challenge-based matches where agents compete against challenges"""
        for participant in participants:
            match = CompetitionMatch(
                id=str(uuid.uuid4()),
                competition_id=competition.id,
                participant1_id=participant.agent_id,
                match_type="challenge",
                status="scheduled",
                scheduled_time=datetime.now(timezone.utc)
            )
            db.add(match)
        
        db.commit()
    
    @staticmethod
    def submit_match_result(
        db: Session,
        match_id: str,
        participant1_score: float,
        participant2_score: Optional[float] = None,
        winner_id: Optional[str] = None,
        match_data: Dict[str, Any] = None
    ) -> CompetitionMatch:
        """Submit results for a competition match"""
        match = db.query(CompetitionMatch).filter(CompetitionMatch.id == match_id).first()
        if not match:
            raise ValueError("Match not found")
        
        if match.status != "scheduled" and match.status != "in_progress":
            raise ValueError("Match cannot be updated in current state")
        
        # Update match results
        match.participant1_score = participant1_score
        match.participant2_score = participant2_score
        match.winner_id = winner_id
        match.match_data = match_data or {}
        match.status = "completed"
        match.completed_time = datetime.now(timezone.utc)
        
        # Determine winner if not specified
        if not winner_id and participant2_score is not None:
            if participant1_score > participant2_score:
                match.winner_id = match.participant1_id
            elif participant2_score > participant1_score:
                match.winner_id = match.participant2_id
            # If scores are equal, winner remains None (draw)
        
        db.commit()
        db.refresh(match)
        
        # Update participant statistics
        CompetitionEngine._update_participant_stats(db, match)
        
        # Update leaderboard
        CompetitionEngine._update_leaderboard(db, match.competition_id)
        
        return match
    
    @staticmethod
    def _update_participant_stats(db: Session, match: CompetitionMatch) -> None:
        """Update participant statistics based on match results"""
        # Update participant 1 stats
        participant1 = db.query(CompetitionParticipant).filter(
            CompetitionParticipant.competition_id == match.competition_id,
            CompetitionParticipant.agent_id == match.participant1_id
        ).first()
        
        if participant1:
            participant1.matches_played += 1
            participant1.total_score += match.participant1_score or 0
            
            if match.winner_id == match.participant1_id:
                participant1.matches_won += 1
            elif match.winner_id == match.participant2_id:
                participant1.matches_lost += 1
            else:
                participant1.matches_drawn += 1
            
            # Update average score
            participant1.average_score = participant1.total_score / participant1.matches_played
        
        # Update participant 2 stats (if applicable)
        if match.participant2_id:
            participant2 = db.query(CompetitionParticipant).filter(
                CompetitionParticipant.competition_id == match.competition_id,
                CompetitionParticipant.agent_id == match.participant2_id
            ).first()
            
            if participant2:
                participant2.matches_played += 1
                participant2.total_score += match.participant2_score or 0
                
                if match.winner_id == match.participant2_id:
                    participant2.matches_won += 1
                elif match.winner_id == match.participant1_id:
                    participant2.matches_lost += 1
                else:
                    participant2.matches_drawn += 1
                
                # Update average score
                participant2.average_score = participant2.total_score / participant2.matches_played
        
        db.commit()
    
    @staticmethod
    def _update_leaderboard(db: Session, competition_id: str) -> None:
        """Update competition leaderboard"""
        participants = db.query(CompetitionParticipant).filter(
            CompetitionParticipant.competition_id == competition_id
        ).all()
        
        # Clear existing leaderboard entries
        db.query(CompetitionLeaderboard).filter(
            CompetitionLeaderboard.competition_id == competition_id
        ).delete()
        
        # Calculate rankings based on competition rules
        ranked_participants = CompetitionEngine._rank_participants(participants)
        
        # Create new leaderboard entries
        for rank, participant in enumerate(ranked_participants, 1):
            leaderboard_entry = CompetitionLeaderboard(
                id=str(uuid.uuid4()),
                competition_id=competition_id,
                agent_id=participant.agent_id,
                rank=rank,
                score=participant.total_score,
                matches_played=participant.matches_played,
                matches_won=participant.matches_won,
                updated_at=datetime.now(timezone.utc)
            )
            db.add(leaderboard_entry)
        
        db.commit()
    
    @staticmethod
    def _rank_participants(participants: List[CompetitionParticipant]) -> List[CompetitionParticipant]:
        """Rank participants based on competition rules"""
        # Simple ranking: by total score, then by win rate
        return sorted(
            participants,
            key=lambda p: (
                p.total_score,  # Primary: total score
                p.matches_won / max(p.matches_played, 1),  # Secondary: win rate
                p.average_score  # Tertiary: average score
            ),
            reverse=True
        )
    
    @staticmethod
    def get_competition_leaderboard(
        db: Session,
        competition_id: str,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get competition leaderboard"""
        leaderboard_entries = db.query(CompetitionLeaderboard).filter(
            CompetitionLeaderboard.competition_id == competition_id
        ).order_by(CompetitionLeaderboard.rank).limit(limit).all()
        
        leaderboard = []
        for entry in leaderboard_entries:
            agent = db.query(UniversityAgent).filter(UniversityAgent.id == entry.agent_id).first()
            participant = db.query(CompetitionParticipant).filter(
                CompetitionParticipant.competition_id == competition_id,
                CompetitionParticipant.agent_id == entry.agent_id
            ).first()
            
            leaderboard.append({
                "rank": entry.rank,
                "agent_id": entry.agent_id,
                "agent_name": agent.name if agent else "Unknown",
                "score": entry.score,
                "matches_played": participant.matches_played if participant else 0,
                "matches_won": participant.matches_won if participant else 0,
                "win_rate": (participant.matches_won / max(participant.matches_played, 1) * 100) if participant else 0,
                "average_score": participant.average_score if participant else 0.0
            })
        
        return leaderboard
    
    @staticmethod
    def end_competition(
        db: Session,
        competition_id: str
    ) -> Competition:
        """End a competition and declare winners"""
        competition = db.query(Competition).filter(Competition.id == competition_id).first()
        if not competition:
            raise ValueError("Competition not found")
        
        if competition.status != "in_progress":
            raise ValueError("Competition cannot be ended in current state")
        
        # Update competition status
        competition.status = "completed"
        competition.actual_end_time = datetime.now(timezone.utc)
        
        # Get top participants for winners
        leaderboard = CompetitionEngine.get_competition_leaderboard(db, competition_id, limit=3)
        
        if leaderboard:
            competition.winner_id = leaderboard[0]["agent_id"]
            competition.runner_up_id = leaderboard[1]["agent_id"] if len(leaderboard) > 1 else None
            competition.third_place_id = leaderboard[2]["agent_id"] if len(leaderboard) > 2 else None
        
        db.commit()
        db.refresh(competition)
        
        # Update agent competition statistics
        CompetitionEngine._update_agent_competition_stats(db, competition)
        
        return competition
    
    @staticmethod
    def _update_agent_competition_stats(db: Session, competition: Competition) -> None:
        """Update agent competition statistics after competition ends"""
        participants = db.query(CompetitionParticipant).filter(
            CompetitionParticipant.competition_id == competition.id
        ).all()
        
        for participant in participants:
            agent = db.query(UniversityAgent).filter(UniversityAgent.id == participant.agent_id).first()
            if agent:
                # Update competition statistics
                agent.competition_wins += participant.matches_won
                agent.competition_losses += participant.matches_lost
                agent.competition_draws += participant.matches_drawn
                
                # Update Elo rating (simplified)
                if participant.agent_id == competition.winner_id:
                    agent.elo_rating += 50  # Winner bonus
                elif participant.agent_id == competition.runner_up_id:
                    agent.elo_rating += 25  # Runner-up bonus
                elif participant.agent_id == competition.third_place_id:
                    agent.elo_rating += 10  # Third place bonus
                
                # Update average score
                total_matches = participant.matches_played
                if total_matches > 0:
                    agent.average_score = (
                        (agent.average_score * (agent.competition_wins + agent.competition_losses + agent.competition_draws - total_matches) + 
                         participant.total_score) / (agent.competition_wins + agent.competition_losses + agent.competition_draws)
                    )
                
                # Update highest score
                if participant.total_score > agent.highest_score:
                    agent.highest_score = participant.total_score
                
                agent.last_competed_at = datetime.now(timezone.utc)
        
        db.commit()
    
    @staticmethod
    def get_agent_competition_history(
        db: Session,
        agent_id: str,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get competition history for an agent"""
        participants = db.query(CompetitionParticipant).filter(
            CompetitionParticipant.agent_id == agent_id
        ).order_by(CompetitionParticipant.registration_time.desc()).limit(limit).all()
        
        history = []
        for participant in participants:
            competition = db.query(Competition).filter(Competition.id == participant.competition_id).first()
            leaderboard_entry = db.query(CompetitionLeaderboard).filter(
                CompetitionLeaderboard.competition_id == participant.competition_id,
                CompetitionLeaderboard.agent_id == agent_id
            ).first()
            
            history.append({
                "competition_id": participant.competition_id,
                "competition_name": competition.name if competition else "Unknown",
                "competition_type": competition.competition_type if competition else "Unknown",
                "rank": leaderboard_entry.rank if leaderboard_entry else None,
                "score": participant.total_score,
                "matches_played": participant.matches_played,
                "matches_won": participant.matches_won,
                "matches_lost": participant.matches_lost,
                "matches_drawn": participant.matches_drawn,
                "average_score": participant.average_score,
                "registration_time": participant.registration_time.isoformat(),
                "status": competition.status if competition else "Unknown"
            })
        
        return history
    
    @staticmethod
    def generate_competition_analytics(
        db: Session,
        university_id: str,
        time_period: str = "all"
    ) -> Dict[str, Any]:
        """Generate competition analytics for a university"""
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
        
        # Get competitions in the time period
        competitions = db.query(Competition).filter(
            Competition.university_id == university_id,
            Competition.start_time >= start_time
        ).all()
        
        # Calculate analytics
        total_competitions = len(competitions)
        active_competitions = len([c for c in competitions if c.status == "in_progress"])
        completed_competitions = len([c for c in competitions if c.status == "completed"])
        
        # Participant statistics
        total_participants = 0
        total_matches_played = 0
        for competition in competitions:
            participants = db.query(CompetitionParticipant).filter(
                CompetitionParticipant.competition_id == competition.id
            ).all()
            total_participants += len(participants)
            
            matches = db.query(CompetitionMatch).filter(
                CompetitionMatch.competition_id == competition.id,
                CompetitionMatch.status == "completed"
            ).all()
            total_matches_played += len(matches)
        
        return {
            "university_id": university_id,
            "time_period": time_period,
            "competition_statistics": {
                "total_competitions": total_competitions,
                "active_competitions": active_competitions,
                "completed_competitions": completed_competitions,
                "completion_rate": (completed_competitions / total_competitions * 100) if total_competitions > 0 else 0
            },
            "participation_statistics": {
                "total_participants": total_participants,
                "average_participants_per_competition": (total_participants / total_competitions) if total_competitions > 0 else 0,
                "total_matches_played": total_matches_played,
                "average_matches_per_competition": (total_matches_played / total_competitions) if total_competitions > 0 else 0
            },
            "time_period_start": start_time.isoformat(),
            "generated_at": now.isoformat()
        }