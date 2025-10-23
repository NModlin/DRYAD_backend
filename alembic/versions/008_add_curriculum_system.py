"""add curriculum system

Revision ID: 008_add_curriculum_system
Revises: 007_add_universities
Create Date: 2025-10-23 14:35:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite

# revision identifiers, used by Alembic.
revision = '008_add_curriculum_system'
down_revision = '007_add_universities'
branch_labels = None
depends_on = None


def upgrade():
    """Create curriculum system tables"""
    
    # Determine JSON type based on dialect
    json_type = sa.JSON().with_variant(sa.Text(), 'sqlite')
    
    # Create curriculum_paths table
    op.create_table(
        'curriculum_paths',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('university_id', sa.String(), nullable=False),
        
        # Basic info
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        
        # Path configuration
        sa.Column('difficulty_level', sa.String(length=50), nullable=False),
        sa.Column('estimated_duration_hours', sa.Integer(), nullable=False),
        sa.Column('prerequisites', json_type, nullable=False),
        
        # Specialization alignment
        sa.Column('specialization', sa.String(length=100), nullable=True),
        sa.Column('skill_tree_id', sa.String(), nullable=True),
        
        # Metadata
        sa.Column('version', sa.String(length=20), nullable=False),
        sa.Column('tags', json_type, nullable=False),
        sa.Column('is_public', sa.Boolean(), nullable=False),
        
        # Status
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        
        # Statistics
        sa.Column('total_enrollments', sa.Integer(), nullable=False),
        sa.Column('total_completions', sa.Integer(), nullable=False),
        sa.Column('average_completion_time_hours', sa.Float(), nullable=True),
        sa.Column('average_score', sa.Float(), nullable=True),
        
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['university_id'], ['universities.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['skill_tree_id'], ['skill_trees.id'], ondelete='SET NULL')
    )
    
    # Create curriculum_levels table
    op.create_table(
        'curriculum_levels',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('curriculum_path_id', sa.String(), nullable=False),
        
        # Level info
        sa.Column('level_number', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        
        # Learning objectives
        sa.Column('objectives', json_type, nullable=False),
        
        # Challenges and tasks
        sa.Column('challenges', json_type, nullable=False),
        sa.Column('required_challenges', sa.Integer(), nullable=False),
        
        # Evaluation criteria
        sa.Column('evaluation_criteria', json_type, nullable=False),
        sa.Column('required_score', sa.Float(), nullable=False),
        
        # Resources
        sa.Column('learning_resources', json_type, nullable=False),
        
        # Estimated time
        sa.Column('estimated_hours', sa.Integer(), nullable=False),
        
        # Metadata
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['curriculum_path_id'], ['curriculum_paths.id'], ondelete='CASCADE')
    )
    
    # Create agent_curriculum_progress table
    op.create_table(
        'agent_curriculum_progress',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('agent_id', sa.String(), nullable=False),
        sa.Column('curriculum_path_id', sa.String(), nullable=False),
        
        # Progress tracking
        sa.Column('current_level_number', sa.Integer(), nullable=False),
        sa.Column('completed_levels', json_type, nullable=False),
        
        # Status
        sa.Column('status', sa.String(length=50), nullable=False),
        
        # Scores and performance
        sa.Column('overall_score', sa.Float(), nullable=True),
        sa.Column('level_scores', json_type, nullable=False),
        
        # Time tracking
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('total_time_hours', sa.Float(), nullable=True),
        sa.Column('last_activity_at', sa.DateTime(timezone=True), nullable=True),
        
        # Attempts
        sa.Column('total_attempts', sa.Integer(), nullable=False),
        sa.Column('failed_attempts', sa.Integer(), nullable=False),
        
        # Metadata
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('custom_metadata', json_type, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['curriculum_path_id'], ['curriculum_paths.id'], ondelete='CASCADE')
    )
    
    # Create indexes for curriculum_paths
    op.create_index('idx_curriculum_university', 'curriculum_paths', ['university_id'])
    op.create_index('idx_curriculum_difficulty', 'curriculum_paths', ['difficulty_level'])
    op.create_index('idx_curriculum_specialization', 'curriculum_paths', ['specialization'])
    op.create_index('idx_curriculum_status', 'curriculum_paths', ['status'])
    op.create_index('idx_curriculum_university_status', 'curriculum_paths', ['university_id', 'status'])
    op.create_index('idx_curriculum_spec_diff', 'curriculum_paths', ['specialization', 'difficulty_level'])
    
    # Create indexes for curriculum_levels
    op.create_index('idx_level_curriculum', 'curriculum_levels', ['curriculum_path_id'])
    op.create_index('idx_level_curriculum_number', 'curriculum_levels', ['curriculum_path_id', 'level_number'])
    
    # Create indexes for agent_curriculum_progress
    op.create_index('idx_progress_agent', 'agent_curriculum_progress', ['agent_id'])
    op.create_index('idx_progress_curriculum', 'agent_curriculum_progress', ['curriculum_path_id'])
    op.create_index('idx_progress_status', 'agent_curriculum_progress', ['status'])
    op.create_index('idx_progress_agent_status', 'agent_curriculum_progress', ['agent_id', 'status'])
    op.create_index('idx_progress_agent_curriculum', 'agent_curriculum_progress', ['agent_id', 'curriculum_path_id'], unique=True)


def downgrade():
    """Drop curriculum system tables"""
    # Drop agent_curriculum_progress indexes and table
    op.drop_index('idx_progress_agent_curriculum', table_name='agent_curriculum_progress')
    op.drop_index('idx_progress_agent_status', table_name='agent_curriculum_progress')
    op.drop_index('idx_progress_status', table_name='agent_curriculum_progress')
    op.drop_index('idx_progress_curriculum', table_name='agent_curriculum_progress')
    op.drop_index('idx_progress_agent', table_name='agent_curriculum_progress')
    op.drop_table('agent_curriculum_progress')
    
    # Drop curriculum_levels indexes and table
    op.drop_index('idx_level_curriculum_number', table_name='curriculum_levels')
    op.drop_index('idx_level_curriculum', table_name='curriculum_levels')
    op.drop_table('curriculum_levels')
    
    # Drop curriculum_paths indexes and table
    op.drop_index('idx_curriculum_spec_diff', table_name='curriculum_paths')
    op.drop_index('idx_curriculum_university_status', table_name='curriculum_paths')
    op.drop_index('idx_curriculum_status', table_name='curriculum_paths')
    op.drop_index('idx_curriculum_specialization', table_name='curriculum_paths')
    op.drop_index('idx_curriculum_difficulty', table_name='curriculum_paths')
    op.drop_index('idx_curriculum_university', table_name='curriculum_paths')
    op.drop_table('curriculum_paths')

