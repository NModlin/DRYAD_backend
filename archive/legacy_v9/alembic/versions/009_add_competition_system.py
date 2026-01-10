"""add competition system

Revision ID: 009_add_competition_system
Revises: 008_add_curriculum_system
Create Date: 2025-10-23 14:40:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite

# revision identifiers, used by Alembic.
revision = '009_add_competition_system'
down_revision = '008_add_curriculum_system'
branch_labels = None
depends_on = None


def upgrade():
    """Create competition system tables"""
    
    # Determine JSON type based on dialect
    json_type = sa.JSON().with_variant(sa.Text(), 'sqlite')
    
    # Create competitions table
    op.create_table(
        'competitions',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('university_id', sa.String(), nullable=False),
        
        # Basic info
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        
        # Competition configuration
        sa.Column('competition_type', sa.String(length=50), nullable=False),
        sa.Column('challenge_category', sa.String(length=50), nullable=False),
        
        # Participants
        sa.Column('participant_ids', json_type, nullable=False),
        sa.Column('team_1_ids', json_type, nullable=True),
        sa.Column('team_2_ids', json_type, nullable=True),
        sa.Column('max_participants', sa.Integer(), nullable=True),
        
        # Rules and configuration
        sa.Column('rules', json_type, nullable=False),
        sa.Column('scoring_config', json_type, nullable=False),
        sa.Column('time_limit_seconds', sa.Integer(), nullable=True),
        sa.Column('max_rounds', sa.Integer(), nullable=True),
        
        # Scheduling
        sa.Column('scheduled_start', sa.DateTime(timezone=True), nullable=True),
        sa.Column('scheduled_end', sa.DateTime(timezone=True), nullable=True),
        sa.Column('actual_start', sa.DateTime(timezone=True), nullable=True),
        sa.Column('actual_end', sa.DateTime(timezone=True), nullable=True),
        
        # Status
        sa.Column('status', sa.String(length=50), nullable=False),
        
        # Results
        sa.Column('winner_id', sa.String(), nullable=True),
        sa.Column('winner_team_ids', json_type, nullable=True),
        sa.Column('final_scores', json_type, nullable=False),
        sa.Column('rankings', json_type, nullable=False),
        
        # Training data
        sa.Column('training_data_collected', sa.Integer(), nullable=False),
        sa.Column('data_quality_score', sa.Float(), nullable=True),
        
        # Metadata
        sa.Column('tags', json_type, nullable=False),
        sa.Column('custom_metadata', json_type, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['university_id'], ['universities.id'], ondelete='CASCADE')
    )
    
    # Create competition_rounds table
    op.create_table(
        'competition_rounds',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('competition_id', sa.String(), nullable=False),
        
        # Round info
        sa.Column('round_number', sa.Integer(), nullable=False),
        sa.Column('round_name', sa.String(length=255), nullable=True),
        
        # Actions
        sa.Column('agent_actions', json_type, nullable=False),
        
        # Scores
        sa.Column('agent_scores', json_type, nullable=False),
        sa.Column('score_breakdown', json_type, nullable=False),
        
        # Results
        sa.Column('round_winner_id', sa.String(), nullable=True),
        
        # Timing
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('duration_seconds', sa.Float(), nullable=True),
        
        # Training data
        sa.Column('training_data_points', sa.Integer(), nullable=False),
        
        # Metadata
        sa.Column('custom_metadata', json_type, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['competition_id'], ['competitions.id'], ondelete='CASCADE')
    )
    
    # Create leaderboards table
    op.create_table(
        'leaderboards',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('university_id', sa.String(), nullable=True),
        
        # Leaderboard info
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        
        # Configuration
        sa.Column('leaderboard_type', sa.String(length=50), nullable=False),
        sa.Column('challenge_category', sa.String(length=50), nullable=True),
        sa.Column('time_period', sa.String(length=50), nullable=True),
        
        # Status
        sa.Column('is_active', sa.Boolean(), nullable=False),
        
        # Metadata
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['university_id'], ['universities.id'], ondelete='CASCADE')
    )
    
    # Create leaderboard_rankings table
    op.create_table(
        'leaderboard_rankings',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('leaderboard_id', sa.String(), nullable=False),
        sa.Column('agent_id', sa.String(), nullable=False),
        
        # Ranking
        sa.Column('rank', sa.Integer(), nullable=False),
        sa.Column('previous_rank', sa.Integer(), nullable=True),
        
        # Scores
        sa.Column('score', sa.Float(), nullable=False),
        sa.Column('wins', sa.Integer(), nullable=False),
        sa.Column('losses', sa.Integer(), nullable=False),
        sa.Column('draws', sa.Integer(), nullable=False),
        sa.Column('total_matches', sa.Integer(), nullable=False),
        
        # Performance metrics
        sa.Column('win_rate', sa.Float(), nullable=True),
        sa.Column('average_score', sa.Float(), nullable=True),
        sa.Column('peak_score', sa.Float(), nullable=True),
        
        # Metadata
        sa.Column('last_match_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['leaderboard_id'], ['leaderboards.id'], ondelete='CASCADE')
    )
    
    # Create indexes for competitions
    op.create_index('idx_competition_university', 'competitions', ['university_id'])
    op.create_index('idx_competition_type', 'competitions', ['competition_type'])
    op.create_index('idx_competition_category', 'competitions', ['challenge_category'])
    op.create_index('idx_competition_status', 'competitions', ['status'])
    op.create_index('idx_competition_university_status', 'competitions', ['university_id', 'status'])
    op.create_index('idx_competition_type_category', 'competitions', ['competition_type', 'challenge_category'])
    op.create_index('idx_competition_scheduled', 'competitions', ['scheduled_start', 'status'])
    
    # Create indexes for competition_rounds
    op.create_index('idx_round_competition', 'competition_rounds', ['competition_id'])
    op.create_index('idx_round_competition_number', 'competition_rounds', ['competition_id', 'round_number'])
    
    # Create indexes for leaderboards
    op.create_index('idx_leaderboard_university', 'leaderboards', ['university_id'])
    op.create_index('idx_leaderboard_category', 'leaderboards', ['challenge_category'])
    op.create_index('idx_leaderboard_active', 'leaderboards', ['is_active'])
    op.create_index('idx_leaderboard_university_active', 'leaderboards', ['university_id', 'is_active'])
    
    # Create indexes for leaderboard_rankings
    op.create_index('idx_ranking_leaderboard', 'leaderboard_rankings', ['leaderboard_id'])
    op.create_index('idx_ranking_agent', 'leaderboard_rankings', ['agent_id'])
    op.create_index('idx_ranking_leaderboard_rank', 'leaderboard_rankings', ['leaderboard_id', 'rank'])
    op.create_index('idx_ranking_agent_leaderboard', 'leaderboard_rankings', ['agent_id', 'leaderboard_id'], unique=True)


def downgrade():
    """Drop competition system tables"""
    # Drop leaderboard_rankings indexes and table
    op.drop_index('idx_ranking_agent_leaderboard', table_name='leaderboard_rankings')
    op.drop_index('idx_ranking_leaderboard_rank', table_name='leaderboard_rankings')
    op.drop_index('idx_ranking_agent', table_name='leaderboard_rankings')
    op.drop_index('idx_ranking_leaderboard', table_name='leaderboard_rankings')
    op.drop_table('leaderboard_rankings')
    
    # Drop leaderboards indexes and table
    op.drop_index('idx_leaderboard_university_active', table_name='leaderboards')
    op.drop_index('idx_leaderboard_active', table_name='leaderboards')
    op.drop_index('idx_leaderboard_category', table_name='leaderboards')
    op.drop_index('idx_leaderboard_university', table_name='leaderboards')
    op.drop_table('leaderboards')
    
    # Drop competition_rounds indexes and table
    op.drop_index('idx_round_competition_number', table_name='competition_rounds')
    op.drop_index('idx_round_competition', table_name='competition_rounds')
    op.drop_table('competition_rounds')
    
    # Drop competitions indexes and table
    op.drop_index('idx_competition_scheduled', table_name='competitions')
    op.drop_index('idx_competition_type_category', table_name='competitions')
    op.drop_index('idx_competition_university_status', table_name='competitions')
    op.drop_index('idx_competition_status', table_name='competitions')
    op.drop_index('idx_competition_category', table_name='competitions')
    op.drop_index('idx_competition_type', table_name='competitions')
    op.drop_index('idx_competition_university', table_name='competitions')
    op.drop_table('competitions')

