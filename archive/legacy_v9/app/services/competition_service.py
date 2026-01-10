"""
Competition Service

Provides business logic for competition management including:
- CRUD operations for competitions and rounds
- Leaderboard management
- Elo rating calculations
- Training data collection
"""

import uuid
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func, desc

from app.models.competition import (
    Competition,
    CompetitionRound,
    Leaderboard,
    LeaderboardRanking,
    CompetitionType,
    CompetitionStatus,
    ChallengeCategory,
    LeaderboardType,
    CompetitionCreate,
    CompetitionUpdate
)


class CompetitionService:
    """Service for managing competitions and leaderboards"""

    def __init__(self, db: AsyncSession):
        self.db = db

    # ==================== Competition Operations ====================

    async def create_competition(self, competition_data: CompetitionCreate) -> Competition:
        """
        Create a new competition.
        
        Args:
            competition_data: Competition creation data
            
        Returns:
            Created competition
        """
        competition = Competition(
            id=str(uuid.uuid4()),
            university_id=competition_data.university_id,
            name=competition_data.name,
            description=competition_data.description,
            competition_type=competition_data.competition_type.value,
            challenge_category=competition_data.challenge_category.value,
            participant_ids=competition_data.participant_ids,
            team_1_ids=competition_data.team_1_ids,
            team_2_ids=competition_data.team_2_ids,
            max_participants=competition_data.max_participants,
            rules=competition_data.rules,
            scoring_config=competition_data.scoring_config,
            time_limit_seconds=competition_data.time_limit_seconds,
            max_rounds=competition_data.max_rounds,
            scheduled_start=competition_data.scheduled_start,
            scheduled_end=competition_data.scheduled_end,
            status=CompetitionStatus.SCHEDULED.value,
            final_scores={},
            rankings=[],
            training_data_collected=0,
            tags=competition_data.tags,
            custom_metadata=competition_data.custom_metadata
        )
        
        self.db.add(competition)
        await self.db.commit()
        await self.db.refresh(competition)
        
        return competition

    async def get_competition(self, competition_id: str) -> Optional[Competition]:
        """Get a competition by ID"""
        stmt = select(Competition).where(Competition.id == competition_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_competitions_by_university(
        self,
        university_id: str,
        competition_type: Optional[CompetitionType] = None,
        category: Optional[ChallengeCategory] = None,
        status: Optional[CompetitionStatus] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Competition]:
        """Get competitions for a university with filters"""
        stmt = select(Competition).where(Competition.university_id == university_id)
        
        if competition_type:
            stmt = stmt.where(Competition.competition_type == competition_type.value)
        if category:
            stmt = stmt.where(Competition.challenge_category == category.value)
        if status:
            stmt = stmt.where(Competition.status == status.value)
        
        stmt = stmt.order_by(Competition.created_at.desc()).offset(skip).limit(limit)
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def update_competition(
        self,
        competition_id: str,
        update_data: CompetitionUpdate
    ) -> Optional[Competition]:
        """Update a competition"""
        stmt = select(Competition).where(Competition.id == competition_id)
        result = await self.db.execute(stmt)
        competition = result.scalar_one_or_none()
        
        if not competition:
            return None
        
        update_dict = update_data.model_dump(exclude_unset=True)
        
        for field, value in update_dict.items():
            if field in ['competition_type', 'challenge_category', 'status'] and value is not None:
                value = value.value if hasattr(value, 'value') else value
            
            setattr(competition, field, value)
        
        competition.updated_at = datetime.now(timezone.utc)
        
        await self.db.commit()
        await self.db.refresh(competition)
        
        return competition

    async def start_competition(self, competition_id: str) -> Optional[Competition]:
        """Start a competition"""
        stmt = select(Competition).where(Competition.id == competition_id)
        result = await self.db.execute(stmt)
        competition = result.scalar_one_or_none()
        
        if not competition:
            return None
        
        competition.status = CompetitionStatus.IN_PROGRESS.value
        competition.actual_start = datetime.now(timezone.utc)
        competition.updated_at = datetime.now(timezone.utc)
        
        await self.db.commit()
        await self.db.refresh(competition)
        
        return competition

    async def complete_competition(
        self,
        competition_id: str,
        winner_id: Optional[str] = None,
        final_scores: Optional[Dict[str, float]] = None
    ) -> Optional[Competition]:
        """
        Complete a competition and update leaderboards.
        
        Args:
            competition_id: Competition ID
            winner_id: Winner agent ID
            final_scores: Final scores for all participants
            
        Returns:
            Updated competition or None
        """
        stmt = select(Competition).where(Competition.id == competition_id)
        result = await self.db.execute(stmt)
        competition = result.scalar_one_or_none()
        
        if not competition:
            return None
        
        competition.status = CompetitionStatus.COMPLETED.value
        competition.actual_end = datetime.now(timezone.utc)
        competition.winner_id = winner_id
        
        if final_scores:
            competition.final_scores = final_scores
            
            # Generate rankings
            sorted_scores = sorted(final_scores.items(), key=lambda x: x[1], reverse=True)
            competition.rankings = [agent_id for agent_id, _ in sorted_scores]
        
        competition.updated_at = datetime.now(timezone.utc)
        
        await self.db.commit()
        await self.db.refresh(competition)
        
        # Update leaderboards
        if winner_id and final_scores:
            await self._update_leaderboards_after_competition(competition, final_scores)
        
        return competition

    async def cancel_competition(self, competition_id: str) -> Optional[Competition]:
        """Cancel a competition"""
        stmt = select(Competition).where(Competition.id == competition_id)
        result = await self.db.execute(stmt)
        competition = result.scalar_one_or_none()
        
        if not competition:
            return None
        
        competition.status = CompetitionStatus.CANCELLED.value
        competition.updated_at = datetime.now(timezone.utc)
        
        await self.db.commit()
        await self.db.refresh(competition)
        
        return competition

    # ==================== Competition Round Operations ====================

    async def create_round(
        self,
        competition_id: str,
        round_number: int,
        agent_actions: Dict[str, Any],
        agent_scores: Dict[str, float]
    ) -> CompetitionRound:
        """Create a new competition round"""
        competition_round = CompetitionRound(
            id=str(uuid.uuid4()),
            competition_id=competition_id,
            round_number=round_number,
            round_name=f"Round {round_number}",
            agent_actions=agent_actions,
            agent_scores=agent_scores,
            score_breakdown={},
            started_at=datetime.now(timezone.utc),
            training_data_points=0,
            custom_metadata={}
        )
        
        self.db.add(competition_round)
        await self.db.commit()
        await self.db.refresh(competition_round)
        
        return competition_round

    async def complete_round(
        self,
        round_id: str,
        winner_id: Optional[str] = None,
        training_data_points: int = 0
    ) -> Optional[CompetitionRound]:
        """Complete a competition round"""
        stmt = select(CompetitionRound).where(CompetitionRound.id == round_id)
        result = await self.db.execute(stmt)
        competition_round = result.scalar_one_or_none()
        
        if not competition_round:
            return None
        
        competition_round.completed_at = datetime.now(timezone.utc)
        competition_round.round_winner_id = winner_id
        competition_round.training_data_points = training_data_points
        
        if competition_round.started_at and competition_round.completed_at:
            # Handle potential naive vs aware mismatch (common with SQLite)
            start = competition_round.started_at
            end = competition_round.completed_at
            
            if start.tzinfo is None:
                start = start.replace(tzinfo=timezone.utc)
            if end.tzinfo is None:
                end = end.replace(tzinfo=timezone.utc)
                
            duration = end - start
            competition_round.duration_seconds = duration.total_seconds()
        
        # Update competition training data count
        stmt = select(Competition).where(Competition.id == competition_round.competition_id)
        result = await self.db.execute(stmt)
        competition = result.scalar_one_or_none()
        
        if competition:
            competition.training_data_collected += training_data_points
        
        await self.db.commit()
        await self.db.refresh(competition_round)
        
        return competition_round

    async def get_rounds_by_competition(self, competition_id: str) -> List[CompetitionRound]:
        """Get all rounds for a competition"""
        stmt = select(CompetitionRound).where(
            CompetitionRound.competition_id == competition_id
        ).order_by(CompetitionRound.round_number)
        
        result = await self.db.execute(stmt)
        return result.scalars().all()

    # ==================== Leaderboard Operations ====================

    async def create_leaderboard(
        self,
        name: str,
        university_id: Optional[str] = None,
        leaderboard_type: LeaderboardType = LeaderboardType.ELO,
        challenge_category: Optional[ChallengeCategory] = None,
        time_period: Optional[str] = None
    ) -> Leaderboard:
        """Create a new leaderboard"""
        leaderboard = Leaderboard(
            id=str(uuid.uuid4()),
            university_id=university_id,
            name=name,
            description=f"{name} leaderboard",
            leaderboard_type=leaderboard_type.value,
            challenge_category=challenge_category.value if challenge_category else None,
            time_period=time_period,
            is_active=True
        )
        
        self.db.add(leaderboard)
        await self.db.commit()
        await self.db.refresh(leaderboard)
        
        return leaderboard

    async def get_leaderboard(self, leaderboard_id: str) -> Optional[Leaderboard]:
        """Get a leaderboard by ID"""
        stmt = select(Leaderboard).where(Leaderboard.id == leaderboard_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_leaderboards_by_university(
        self,
        university_id: str,
        active_only: bool = True
    ) -> List[Leaderboard]:
        """Get leaderboards for a university"""
        stmt = select(Leaderboard).where(Leaderboard.university_id == university_id)
        
        if active_only:
            stmt = stmt.where(Leaderboard.is_active == True)
        
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def get_rankings(
        self,
        leaderboard_id: str,
        limit: int = 100
    ) -> List[LeaderboardRanking]:
        """Get rankings for a leaderboard"""
        stmt = select(LeaderboardRanking).where(
            LeaderboardRanking.leaderboard_id == leaderboard_id
        ).order_by(LeaderboardRanking.rank).limit(limit)
        
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def update_ranking(
        self,
        leaderboard_id: str,
        agent_id: str,
        score_change: float,
        won: bool = False,
        lost: bool = False,
        draw: bool = False
    ) -> LeaderboardRanking:
        """Update or create a ranking for an agent"""
        stmt = select(LeaderboardRanking).where(
            and_(
                LeaderboardRanking.leaderboard_id == leaderboard_id,
                LeaderboardRanking.agent_id == agent_id
            )
        )
        result = await self.db.execute(stmt)
        ranking = result.scalar_one_or_none()
        
        if not ranking:
            ranking = LeaderboardRanking(
                id=str(uuid.uuid4()),
                leaderboard_id=leaderboard_id,
                agent_id=agent_id,
                rank=0,
                score=1500.0,  # Default Elo rating
                wins=0,
                losses=0,
                draws=0,
                total_matches=0
            )
            self.db.add(ranking)
        
        # Update score
        ranking.previous_rank = ranking.rank
        ranking.score += score_change
        
        # Update match statistics
        if won:
            ranking.wins += 1
        if lost:
            ranking.losses += 1
        if draw:
            ranking.draws += 1
        
        ranking.total_matches += 1
        
        # Calculate metrics
        if ranking.total_matches > 0:
            ranking.win_rate = ranking.wins / ranking.total_matches
        
        ranking.last_match_at = datetime.now(timezone.utc)
        ranking.updated_at = datetime.now(timezone.utc)
        
        await self.db.commit()
        
        # Recalculate ranks for all agents in this leaderboard
        await self._recalculate_ranks(leaderboard_id)
        
        await self.db.refresh(ranking)
        
        return ranking

    async def _recalculate_ranks(self, leaderboard_id: str):
        """Recalculate ranks for all agents in a leaderboard"""
        stmt = select(LeaderboardRanking).where(
            LeaderboardRanking.leaderboard_id == leaderboard_id
        ).order_by(desc(LeaderboardRanking.score))
        
        result = await self.db.execute(stmt)
        rankings = result.scalars().all()
        
        for idx, ranking in enumerate(rankings, start=1):
            ranking.rank = idx
        
        await self.db.commit()

    async def _update_leaderboards_after_competition(
        self,
        competition: Competition,
        final_scores: Dict[str, float]
    ):
        """Update leaderboards after a competition completes"""
        # Find or create leaderboard for this university and category
        stmt = select(Leaderboard).where(
            and_(
                Leaderboard.university_id == competition.university_id,
                Leaderboard.challenge_category == competition.challenge_category,
                Leaderboard.is_active == True
            )
        )
        result = await self.db.execute(stmt)
        leaderboard = result.scalar_one_or_none()
        
        if not leaderboard:
            leaderboard = await self.create_leaderboard(
                name=f"{competition.challenge_category} Leaderboard",
                university_id=competition.university_id,
                challenge_category=ChallengeCategory(competition.challenge_category)
            )
        
        # Update rankings based on final scores
        sorted_agents = sorted(final_scores.items(), key=lambda x: x[1], reverse=True)
        
        for idx, (agent_id, score) in enumerate(sorted_agents):
            won = idx == 0
            lost = idx == len(sorted_agents) - 1 and len(sorted_agents) > 1
            
            # Simple Elo-like score change
            score_change = 10.0 if won else -5.0 if lost else 0.0
            
            await self.update_ranking(
                leaderboard.id, agent_id, score_change, won=won, lost=lost
            )
