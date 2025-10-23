"""Create university system tables

Revision ID: 001_create_university_tables
Revises: 
Create Date: 2025-10-23 06:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite

# revision identifiers, used by Alembic.
revision = '001_create_university_tables'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Create universities table
    op.create_table('universities',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('owner_user_id', sa.String(), nullable=False),
        sa.Column('client_app_id', sa.String(), nullable=True),
        sa.Column('tenant_id', sa.String(), nullable=True),
        sa.Column('organization_id', sa.String(), nullable=True),
        sa.Column('settings', sa.JSON(), nullable=True),
        sa.Column('max_agents', sa.Integer(), nullable=True),
        sa.Column('max_concurrent_competitions', sa.Integer(), nullable=True),
        sa.Column('storage_quota_mb', sa.Integer(), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_activity_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['client_app_id'], ['client_applications.id'], ),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ),
        sa.ForeignKeyConstraint(['owner_user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint("status IN ('active', 'suspended', 'archived')", name='ck_university_status'),
        sa.CheckConstraint('max_agents > 0', name='ck_university_max_agents'),
        sa.CheckConstraint('max_concurrent_competitions > 0', name='ck_university_max_competitions')
    )
    
    # Create university_agents table
    op.create_table('university_agents',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('university_id', sa.String(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('agent_type', sa.String(length=100), nullable=False),
        sa.Column('configuration', sa.JSON(), nullable=False),
        sa.Column('specialization', sa.String(length=100), nullable=True),
        sa.Column('current_curriculum_path_id', sa.String(), nullable=True),
        sa.Column('current_curriculum_level_id', sa.String(), nullable=True),
        sa.Column('current_challenge_index', sa.Integer(), nullable=True),
        sa.Column('competency_score', sa.Float(), nullable=True),
        sa.Column('training_hours', sa.Float(), nullable=True),
        sa.Column('training_data_collected', sa.Integer(), nullable=True),
        sa.Column('competition_wins', sa.Integer(), nullable=True),
        sa.Column('competition_losses', sa.Integer(), nullable=True),
        sa.Column('competition_draws', sa.Integer(), nullable=True),
        sa.Column('average_score', sa.Float(), nullable=True),
        sa.Column('highest_score', sa.Float(), nullable=True),
        sa.Column('elo_rating', sa.Float(), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_trained_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_competed_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['current_curriculum_level_id'], ['curriculum_levels.id'], ),
        sa.ForeignKeyConstraint(['current_curriculum_path_id'], ['curriculum_paths.id'], ),
        sa.ForeignKeyConstraint(['university_id'], ['universities.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint("agent_type IN ('student', 'instructor', 'researcher', 'specialist')", name='ck_agent_type'),
        sa.CheckConstraint("status IN ('active', 'training', 'competing', 'idle', 'archived')", name='ck_agent_status'),
        sa.CheckConstraint('competency_score >= 0.0 AND competency_score <= 1.0', name='ck_agent_competency')
    )
    
    # Create curriculum_paths table
    op.create_table('curriculum_paths',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('university_id', sa.String(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('difficulty_level', sa.String(length=50), nullable=True),
        sa.Column('estimated_duration_hours', sa.Integer(), nullable=True),
        sa.Column('prerequisites', sa.JSON(), nullable=True),
        sa.Column('version', sa.String(length=20), nullable=True),
        sa.Column('tags', sa.JSON(), nullable=True),
        sa.Column('is_public', sa.Boolean(), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['university_id'], ['universities.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint("difficulty_level IN ('beginner', 'intermediate', 'advanced', 'expert')", name='ck_path_difficulty'),
        sa.CheckConstraint("status IN ('active', 'draft', 'archived')", name='ck_path_status'),
        sa.CheckConstraint('estimated_duration_hours > 0', name='ck_path_duration')
    )
    
    # Create curriculum_levels table
    op.create_table('curriculum_levels',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('curriculum_path_id', sa.String(), nullable=False),
        sa.Column('level_number', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('learning_objectives', sa.JSON(), nullable=False),
        sa.Column('theoretical_content', sa.Text(), nullable=True),
        sa.Column('practical_exercises', sa.JSON(), nullable=True),
        sa.Column('challenges', sa.JSON(), nullable=False),
        sa.Column('challenge_count', sa.Integer(), nullable=True),
        sa.Column('passing_score', sa.Float(), nullable=True),
        sa.Column('time_limit_minutes', sa.Integer(), nullable=True),
        sa.Column('required_competency_score', sa.Float(), nullable=True),
        sa.Column('prerequisite_level_ids', sa.JSON(), nullable=True),
        sa.Column('tags', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['curriculum_path_id'], ['curriculum_paths.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('curriculum_path_id', 'level_number', name='uq_curriculum_level'),
        sa.CheckConstraint('level_number > 0', name='ck_level_number'),
        sa.CheckConstraint('passing_score >= 0.0 AND passing_score <= 1.0', name='ck_level_passing_score'),
        sa.CheckConstraint('time_limit_minutes > 0', name='ck_level_time_limit'),
        sa.CheckConstraint('challenge_count >= 0', name='ck_level_challenge_count')
    )
    
    # Create agent_progress table
    op.create_table('agent_progress',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('agent_id', sa.String(), nullable=False),
        sa.Column('curriculum_level_id', sa.String(), nullable=False),
        sa.Column('current_challenge_index', sa.Integer(), nullable=True),
        sa.Column('challenges_completed', sa.Integer(), nullable=True),
        sa.Column('total_challenges', sa.Integer(), nullable=False),
        sa.Column('current_score', sa.Float(), nullable=True),
        sa.Column('best_score', sa.Float(), nullable=True),
        sa.Column('average_score', sa.Float(), nullable=True),
        sa.Column('time_spent_minutes', sa.Integer(), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_activity_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('challenge_results', sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(['agent_id'], ['university_agents.id'], ),
        sa.ForeignKeyConstraint(['curriculum_level_id'], ['curriculum_levels.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('agent_id', 'curriculum_level_id', name='uq_agent_progress'),
        sa.CheckConstraint("status IN ('not_started', 'in_progress', 'completed', 'failed')", name='ck_progress_status'),
        sa.CheckConstraint('current_challenge_index >= 0', name='ck_progress_challenge_index'),
        sa.CheckConstraint('challenges_completed >= 0', name='ck_progress_completed'),
        sa.CheckConstraint('total_challenges > 0', name='ck_progress_total_challenges')
    )
    
    # Create competitions table
    op.create_table('competitions',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('university_id', sa.String(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('competition_type', sa.String(length=100), nullable=False),
        sa.Column('rules', sa.JSON(), nullable=False),
        sa.Column('benchmark_id', sa.String(length=255), nullable=True),
        sa.Column('evaluation_config', sa.JSON(), nullable=False),
        sa.Column('scheduled_start', sa.DateTime(timezone=True), nullable=True),
        sa.Column('scheduled_end', sa.DateTime(timezone=True), nullable=True),
        sa.Column('actual_start', sa.DateTime(timezone=True), nullable=True),
        sa.Column('actual_end', sa.DateTime(timezone=True), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=True),
        sa.Column('max_participants', sa.Integer(), nullable=True),
        sa.Column('winner_agent_id', sa.String(), nullable=True),
        sa.Column('results_published', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['university_id'], ['universities.id'], ),
        sa.ForeignKeyConstraint(['winner_agent_id'], ['university_agents.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint("competition_type IN ('solo', 'head_to_head', 'tournament', 'challenge')", name='ck_competition_type'),
        sa.CheckConstraint("status IN ('scheduled', 'active', 'completed', 'cancelled')", name='ck_competition_status'),
        sa.CheckConstraint('max_participants > 0', name='ck_competition_max_participants')
    )
    
    # Create competition_participants table
    op.create_table('competition_participants',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('competition_id', sa.String(), nullable=False),
        sa.Column('agent_id', sa.String(), nullable=False),
        sa.Column('participant_type', sa.String(length=50), nullable=True),
        sa.Column('seed_ranking', sa.Integer(), nullable=True),
        sa.Column('final_score', sa.Float(), nullable=True),
        sa.Column('ranking', sa.Integer(), nullable=True),
        sa.Column('execution_time_ms', sa.Integer(), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=True),
        sa.Column('joined_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['agent_id'], ['university_agents.id'], ),
        sa.ForeignKeyConstraint(['competition_id'], ['competitions.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('competition_id', 'agent_id', name='uq_competition_participant'),
        sa.CheckConstraint("participant_type IN ('competitor', 'observer', 'judge')", name='ck_participant_type'),
        sa.CheckConstraint("status IN ('registered', 'active', 'completed', 'disqualified')", name='ck_participant_status')
    )
    
    # Create competition_matches table
    op.create_table('competition_matches',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('competition_id', sa.String(), nullable=False),
        sa.Column('match_number', sa.Integer(), nullable=False),
        sa.Column('participant1_id', sa.String(), nullable=False),
        sa.Column('participant2_id', sa.String(), nullable=True),
        sa.Column('match_config', sa.JSON(), nullable=False),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('participant1_score', sa.Float(), nullable=True),
        sa.Column('participant2_score', sa.Float(), nullable=True),
        sa.Column('winner_participant_id', sa.String(), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=True),
        sa.Column('evaluation_run_id', sa.String(length=255), nullable=True),
        sa.Column('detailed_results', sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(['competition_id'], ['competitions.id'], ),
        sa.ForeignKeyConstraint(['participant1_id'], ['competition_participants.id'], ),
        sa.ForeignKeyConstraint(['participant2_id'], ['competition_participants.id'], ),
        sa.ForeignKeyConstraint(['winner_participant_id'], ['competition_participants.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint("status IN ('scheduled', 'active', 'completed', 'cancelled')", name='ck_match_status'),
        sa.CheckConstraint('match_number > 0', name='ck_match_number')
    )
    
    # Create training_data_collections table
    op.create_table('training_data_collections',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('university_id', sa.String(), nullable=False),
        sa.Column('agent_id', sa.String(), nullable=False),
        sa.Column('source_type', sa.String(length=100), nullable=False),
        sa.Column('source_id', sa.String(length=36), nullable=True),
        sa.Column('data_type', sa.String(length=100), nullable=False),
        sa.Column('raw_data', sa.JSON(), nullable=False),
        sa.Column('processed_data', sa.JSON(), nullable=True),
        sa.Column('metadata', sa.JSON(), nullable=True),
        sa.Column('quality_score', sa.Float(), nullable=True),
        sa.Column('completeness_score', sa.Float(), nullable=True),
        sa.Column('consistency_score', sa.Float(), nullable=True),
        sa.Column('validity_score', sa.Float(), nullable=True),
        sa.Column('validation_status', sa.String(length=50), nullable=True),
        sa.Column('privacy_level', sa.String(length=50), nullable=True),
        sa.Column('anonymized', sa.Boolean(), nullable=True),
        sa.Column('collected_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('validated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['agent_id'], ['university_agents.id'], ),
        sa.ForeignKeyConstraint(['university_id'], ['universities.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint("source_type IN ('competition', 'training', 'evaluation', 'interaction')", name='ck_training_source_type'),
        sa.CheckConstraint("data_type IN ('conversation', 'reasoning', 'tool_use', 'problem_solving')", name='ck_training_data_type'),
        sa.CheckConstraint("validation_status IN ('pending', 'validated', 'rejected', 'anonymized')", name='ck_training_validation_status'),
        sa.CheckConstraint("privacy_level IN ('private', 'shared', 'public')", name='ck_training_privacy_level'),
        sa.CheckConstraint('quality_score >= 0.0 AND quality_score <= 1.0', name='ck_training_quality')
    )
    
    # Create improvement_proposals table
    op.create_table('improvement_proposals',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('university_id', sa.String(), nullable=False),
        sa.Column('generated_by', sa.String(length=100), nullable=True),
        sa.Column('source_data_collection_id', sa.String(), nullable=True),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('implementation_details', sa.Text(), nullable=True),
        sa.Column('expected_improvement', sa.Float(), nullable=True),
        sa.Column('validation_results', sa.JSON(), nullable=True),
        sa.Column('validation_status', sa.String(length=50), nullable=True),
        sa.Column('validated_by', sa.String(length=255), nullable=True),
        sa.Column('validated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('implementation_status', sa.String(length=50), nullable=True),
        sa.Column('implemented_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['source_data_collection_id'], ['training_data_collections.id'], ),
        sa.ForeignKeyConstraint(['university_id'], ['universities.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint("generated_by IN ('professor_agent', 'human', 'system')", name='ck_proposal_generated_by'),
        sa.CheckConstraint("validation_status IN ('pending', 'approved', 'rejected', 'implemented')", name='ck_proposal_validation_status'),
        sa.CheckConstraint("implementation_status IN ('not_started', 'in_progress', 'completed', 'failed')", name='ck_proposal_implementation_status')
    )
    
    # Create achievements table (UniAugment gamification)
    op.create_table('achievements',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('category', sa.String(length=100), nullable=True),
        sa.Column('difficulty', sa.String(length=50), nullable=True),
        sa.Column('points', sa.Integer(), nullable=True),
        sa.Column('criteria', sa.JSON(), nullable=False),
        sa.Column('required_count', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint("difficulty IN ('easy', 'medium', 'hard', 'expert')", name='ck_achievement_difficulty'),
        sa.CheckConstraint('points > 0', name='ck_achievement_points'),
        sa.CheckConstraint('required_count > 0', name='ck_achievement_required_count')
    )
    
    # Create agent_achievements table
    op.create_table('agent_achievements',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('agent_id', sa.String(), nullable=False),
        sa.Column('achievement_id', sa.String(), nullable=False),
        sa.Column('earned_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('progress', sa.Integer(), nullable=True),
        sa.Column('is_completed', sa.Boolean(), nullable=True),
        sa.ForeignKeyConstraint(['achievement_id'], ['achievements.id'], ),
        sa.ForeignKeyConstraint(['agent_id'], ['university_agents.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint('progress >= 0', name='ck_agent_achievement_progress')
    )
    
    # Create indexes for performance
    op.create_index('idx_universities_owner', 'universities', ['owner_user_id'])
    op.create_index('idx_universities_tenant', 'universities', ['tenant_id'])
    op.create_index('idx_universities_org', 'universities', ['organization_id'])
    op.create_index('idx_universities_status', 'universities', ['status'])
    
    op.create_index('idx_agents_university', 'university_agents', ['university_id'])
    op.create_index('idx_agents_type', 'university_agents', ['agent_type'])
    op.create_index('idx_agents_competency', 'university_agents', ['competency_score'])
    op.create_index('idx_agents_status', 'university_agents', ['status'])
    
    op.create_index('idx_paths_university', 'curriculum_paths', ['university_id'])
    op.create_index('idx_paths_difficulty', 'curriculum_paths', ['difficulty_level'])
    
    op.create_index('idx_levels_path', 'curriculum_levels', ['curriculum_path_id'])
    op.create_index('idx_levels_number', 'curriculum_levels', ['level_number'])
    
    op.create_index('idx_progress_agent', 'agent_progress', ['agent_id'])
    op.create_index('idx_progress_level', 'agent_progress', ['curriculum_level_id'])
    op.create_index('idx_progress_status', 'agent_progress', ['status'])
    
    op.create_index('idx_competitions_university', 'competitions', ['university_id'])
    op.create_index('idx_competitions_status', 'competitions', ['status'])
    op.create_index('idx_competitions_schedule', 'competitions', ['scheduled_start'])
    
    op.create_index('idx_participants_competition', 'competition_participants', ['competition_id'])
    op.create_index('idx_participants_agent', 'competition_participants', ['agent_id'])
    
    op.create_index('idx_matches_competition', 'competition_matches', ['competition_id'])
    op.create_index('idx_matches_participants', 'competition_matches', ['participant1_id', 'participant2_id'])
    op.create_index('idx_matches_status', 'competition_matches', ['status'])
    
    op.create_index('idx_training_university', 'training_data_collections', ['university_id'])
    op.create_index('idx_training_agent', 'training_data_collections', ['agent_id'])
    op.create_index('idx_training_source', 'training_data_collections', ['source_type', 'source_id'])
    op.create_index('idx_training_validation', 'training_data_collections', ['validation_status'])
    
    op.create_index('idx_proposals_university', 'improvement_proposals', ['university_id'])
    op.create_index('idx_proposals_status', 'improvement_proposals', ['validation_status'])
    op.create_index('idx_proposals_implementation', 'improvement_proposals', ['implementation_status'])


def downgrade():
    # Drop tables in reverse order (respecting foreign keys)
    op.drop_table('agent_achievements')
    op.drop_table('achievements')
    op.drop_table('improvement_proposals')
    op.drop_table('training_data_collections')
    op.drop_table('competition_matches')
    op.drop_table('competition_participants')
    op.drop_table('competitions')
    op.drop_table('agent_progress')
    op.drop_table('curriculum_levels')
    op.drop_table('curriculum_paths')
    op.drop_table('university_agents')
    op.drop_table('universities')