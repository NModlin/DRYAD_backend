"""enhance university system

Revision ID: 010_enhance_university_system
Revises: 009_add_competition_system
Create Date: 2025-10-23 15:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite

# revision identifiers, used by Alembic.
revision = '010_enhance_university_system'
down_revision = '009_add_competition_system'
branch_labels = None
depends_on = None


def upgrade():
    """Enhance university system with additional features"""
    
    # Determine JSON type based on dialect
    json_type = sa.JSON().with_variant(sa.Text(), 'sqlite')
    
    # Create university_agents table (enhanced agent model)
    op.create_table(
        'university_agents',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('university_id', sa.String(), ForeignKey("universities.id", ondelete="CASCADE"), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        
        # Agent configuration and type
        sa.Column('agent_type', sa.String(length=100), nullable=False),
        sa.Column('configuration', json_type, nullable=False),
        sa.Column('specialization', sa.String(length=100), nullable=True),
        
        # Training state and progression
        sa.Column('current_curriculum_path_id', sa.String(), ForeignKey("curriculum_paths.id"), nullable=True),
        sa.Column('current_curriculum_level_id', sa.String(), ForeignKey("curriculum_levels.id"), nullable=True),
        sa.Column('current_challenge_index', sa.Integer(), default=0),
        
        # Competency metrics
        sa.Column('competency_score', sa.Float(), default=0.0),
        sa.Column('training_hours', sa.Float(), default=0.0),
        sa.Column('training_data_collected', sa.Integer(), default=0),
        
        # Competition performance
        sa.Column('competition_wins', sa.Integer(), default=0),
        sa.Column('competition_losses', sa.Integer(), default=0),
        sa.Column('competition_draws', sa.Integer(), default=0),
        sa.Column('average_score', sa.Float(), default=0.0),
        sa.Column('highest_score', sa.Float(), default=0.0),
        sa.Column('elo_rating', sa.Float(), default=1000.0),
        
        # Status and timestamps
        sa.Column('status', sa.String(length=50), default='active'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), onupdate=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('last_trained_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_competed_at', sa.DateTime(timezone=True), nullable=True),
        
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['university_id'], ['universities.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['current_curriculum_path_id'], ['curriculum_paths.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['current_curriculum_level_id'], ['curriculum_levels.id'], ondelete='SET NULL'),
        sa.CheckConstraint("agent_type IN ('student', 'instructor', 'researcher', 'specialist')", name="ck_agent_type"),
        sa.CheckConstraint("status IN ('active', 'training', 'competing', 'idle', 'archived')", name="ck_agent_status"),
        sa.CheckConstraint("competency_score >= 0.0 AND competency_score <= 1.0", name="ck_agent_competency")
    )
    
    # Create agent_progress table (detailed progress tracking)
    op.create_table(
        'agent_progress',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('agent_id', sa.String(), ForeignKey("university_agents.id", ondelete="CASCADE"), nullable=False),
        sa.Column('curriculum_level_id', sa.String(), ForeignKey("curriculum_levels.id", ondelete="CASCADE"), nullable=False),
        
        # Progress state
        sa.Column('current_challenge_index', sa.Integer(), default=0),
        sa.Column('challenges_completed', sa.Integer(), default=0),
        sa.Column('total_challenges', sa.Integer(), nullable=False),
        
        # Performance metrics
        sa.Column('current_score', sa.Float(), default=0.0),
        sa.Column('best_score', sa.Float(), default=0.0),
        sa.Column('average_score', sa.Float(), default=0.0),
        sa.Column('time_spent_minutes', sa.Integer(), default=0),
        
        # Status and completion
        sa.Column('status', sa.String(length=50), default='not_started'),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_activity_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
        
        # Detailed challenge results
        sa.Column('challenge_results', json_type, default=dict),
        
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['agent_id'], ['university_agents.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['curriculum_level_id'], ['curriculum_levels.id'], ondelete='CASCADE'),
        sa.CheckConstraint("status IN ('not_started', 'in_progress', 'completed', 'failed')", name="ck_progress_status"),
        sa.CheckConstraint("current_challenge_index >= 0", name="ck_progress_challenge_index"),
        sa.CheckConstraint("challenges_completed >= 0", name="ck_progress_completed"),
        sa.CheckConstraint("total_challenges > 0", name="ck_progress_total_challenges")
    )
    
    # Create training_data_collections table
    op.create_table(
        'training_data_collections',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('university_id', sa.String(), ForeignKey("universities.id", ondelete="CASCADE"), nullable=False),
        sa.Column('agent_id', sa.String(), ForeignKey("university_agents.id", ondelete="CASCADE"), nullable=False),
        
        # Data source
        sa.Column('source_type', sa.String(length=100), nullable=False),
        sa.Column('source_id', sa.String(), nullable=True),
        
        # Data content
        sa.Column('data_type', sa.String(length=100), nullable=False),
        sa.Column('raw_data', json_type, nullable=False),
        sa.Column('processed_data', json_type, nullable=True),
        sa.Column('metadata', json_type, nullable=True),
        
        # Quality metrics
        sa.Column('quality_score', sa.Float(), default=0.0),
        sa.Column('completeness_score', sa.Float(), default=0.0),
        sa.Column('consistency_score', sa.Float(), default=0.0),
        sa.Column('validity_score', sa.Float(), default=0.0),
        sa.Column('validation_status', sa.String(length=50), default='pending'),
        
        # Privacy and sharing
        sa.Column('privacy_level', sa.String(length=50), default='private'),
        sa.Column('anonymized', sa.Boolean(), default=False),
        
        sa.Column('collected_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('validated_at', sa.DateTime(timezone=True), nullable=True),
        
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['university_id'], ['universities.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['agent_id'], ['university_agents.id'], ondelete='CASCADE'),
        sa.CheckConstraint("source_type IN ('competition', 'training', 'evaluation', 'interaction')", name="ck_training_source_type"),
        sa.CheckConstraint("data_type IN ('conversation', 'reasoning', 'tool_use', 'problem_solving')", name="ck_training_data_type"),
        sa.CheckConstraint("validation_status IN ('pending', 'validated', 'rejected', 'anonymized')", name="ck_training_validation_status"),
        sa.CheckConstraint("privacy_level IN ('private', 'shared', 'public')", name="ck_training_privacy_level"),
        sa.CheckConstraint("quality_score >= 0.0 AND quality_score <= 1.0", name="ck_training_quality")
    )
    
    # Create improvement_proposals table
    op.create_table(
        'improvement_proposals',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('university_id', sa.String(), ForeignKey("universities.id", ondelete="CASCADE"), nullable=False),
        
        # Proposal source
        sa.Column('generated_by', sa.String(length=100), default='professor_agent'),
        sa.Column('source_data_collection_id', sa.String(), ForeignKey("training_data_collections.id"), nullable=True),
        
        # Proposal content
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('implementation_details', sa.Text(), nullable=True),
        sa.Column('expected_improvement', sa.Float(), nullable=True),
        
        # Validation
        sa.Column('validation_results', json_type, nullable=True),
        sa.Column('validation_status', sa.String(length=50), default='pending'),
        sa.Column('validated_by', sa.String(length=255), nullable=True),
        sa.Column('validated_at', sa.DateTime(timezone=True), nullable=True),
        
        # Implementation
        sa.Column('implementation_status', sa.String(length=50), default='not_started'),
        sa.Column('implemented_at', sa.DateTime(timezone=True), nullable=True),
        
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), onupdate=sa.text('CURRENT_TIMESTAMP')),
        
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['university_id'], ['universities.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['source_data_collection_id'], ['training_data_collections.id'], ondelete='SET NULL'),
        sa.CheckConstraint("generated_by IN ('professor_agent', 'human', 'system')", name="ck_proposal_generated_by"),
        sa.CheckConstraint("validation_status IN ('pending', 'approved', 'rejected', 'implemented')", name="ck_proposal_validation_status"),
        sa.CheckConstraint("implementation_status IN ('not_started', 'in_progress', 'completed', 'failed')", name="ck_proposal_implementation_status")
    )
    
    # Create achievements table (gamification)
    op.create_table(
        'achievements',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('category', sa.String(length=100), nullable=True),
        sa.Column('difficulty', sa.String(length=50), default='easy'),
        sa.Column('points', sa.Integer(), default=10),
        
        # Achievement criteria
        sa.Column('criteria', json_type, nullable=False),
        sa.Column('required_count', sa.Integer(), default=1),
        
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
        
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint("difficulty IN ('easy', 'medium', 'hard', 'expert')", name="ck_achievement_difficulty"),
        sa.CheckConstraint("points > 0", name="ck_achievement_points"),
        sa.CheckConstraint("required_count > 0", name="ck_achievement_required_count")
    )
    
    # Create agent_achievements table
    op.create_table(
        'agent_achievements',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('agent_id', sa.String(), ForeignKey("university_agents.id", ondelete="CASCADE"), nullable=False),
        sa.Column('achievement_id', sa.String(), ForeignKey("achievements.id", ondelete="CASCADE"), nullable=False),
        
        sa.Column('earned_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('progress', sa.Integer(), default=0),
        sa.Column('is_completed', sa.Boolean(), default=False),
        
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['agent_id'], ['university_agents.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['achievement_id'], ['achievements.id'], ondelete='CASCADE'),
        sa.CheckConstraint("progress >= 0", name="ck_agent_achievement_progress")
    )
    
    # Create indexes for enhanced performance
    op.create_index('idx_agent_university', 'university_agents', ['university_id'])
    op.create_index('idx_agent_type', 'university_agents', ['agent_type'])
    op.create_index('idx_agent_status', 'university_agents', ['status'])
    op.create_index('idx_agent_curriculum', 'university_agents', ['current_curriculum_path_id'])
    op.create_index('idx_agent_elo', 'university_agents', ['elo_rating'])
    
    op.create_index('idx_progress_agent', 'agent_progress', ['agent_id'])
    op.create_index('idx_progress_level', 'agent_progress', ['curriculum_level_id'])
    op.create_index('idx_progress_status', 'agent_progress', ['status'])
    
    op.create_index('idx_training_university', 'training_data_collections', ['university_id'])
    op.create_index('idx_training_agent', 'training_data_collections', ['agent_id'])
    op.create_index('idx_training_source', 'training_data_collections', ['source_type'])
    op.create_index('idx_training_quality', 'training_data_collections', ['quality_score'])
    
    op.create_index('idx_proposal_university', 'improvement_proposals', ['university_id'])
    op.create_index('idx_proposal_status', 'improvement_proposals', ['validation_status'])
    op.create_index('idx_proposal_implementation', 'improvement_proposals', ['implementation_status'])
    
    op.create_index('idx_achievement_category', 'achievements', ['category'])
    op.create_index('idx_achievement_difficulty', 'achievements', ['difficulty'])
    
    op.create_index('idx_agent_achievement_agent', 'agent_achievements', ['agent_id'])
    op.create_index('idx_agent_achievement_completed', 'agent_achievements', ['is_completed'])


def downgrade():
    """Remove enhanced university system features"""
    
    # Drop indexes
    op.drop_index('idx_agent_achievement_completed', table_name='agent_achievements')
    op.drop_index('idx_agent_achievement_agent', table_name='agent_achievements')
    op.drop_index('idx_achievement_difficulty', table_name='achievements')
    op.drop_index('idx_achievement_category', table_name='achievements')
    op.drop_index('idx_proposal_implementation', table_name='improvement_proposals')
    op.drop_index('idx_proposal_status', table_name='improvement_proposals')
    op.drop_index('idx_proposal_university', table_name='improvement_proposals')
    op.drop_index('idx_training_quality', table_name='training_data_collections')
    op.drop_index('idx_training_source', table_name='training_data_collections')
    op.drop_index('idx_training_agent', table_name='training_data_collections')
    op.drop_index('idx_training_university', table_name='training_data_collections')
    op.drop_index('idx_progress_status', table_name='agent_progress')
    op.drop_index('idx_progress_level', table_name='agent_progress')
    op.drop_index('idx_progress_agent', table_name='agent_progress')
    op.drop_index('idx_agent_elo', table_name='university_agents')
    op.drop_index('idx_agent_curriculum', table_name='university_agents')
    op.drop_index('idx_agent_status', table_name='university_agents')
    op.drop_index('idx_agent_type', table_name='university_agents')
    op.drop_index('idx_agent_university', table_name='university_agents')
    
    # Drop tables in reverse order of dependencies
    op.drop_table('agent_achievements')
    op.drop_table('achievements')
    op.drop_table('improvement_proposals')
    op.drop_table('training_data_collections')
    op.drop_table('agent_progress')
    op.drop_table('university_agents')