"""Add Agent Enhancements Phase 1 - Visual and Behavioral Profiles

Revision ID: 001_agent_enhancements_phase1
Revises: 
Create Date: 2025-10-22 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = '001_agent_enhancements_phase1'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create visual and behavioral profile tables."""
    
    # Create visual_profiles table
    op.create_table(
        'visual_profiles',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('agent_id', sa.String(), nullable=False),
        sa.Column('avatar_style', sa.String(), nullable=False, server_default='abstract'),
        sa.Column('avatar_url', sa.String(500), nullable=True),
        sa.Column('primary_color', sa.String(7), nullable=False, server_default='#0066CC'),
        sa.Column('secondary_color', sa.String(7), nullable=False, server_default='#00CC66'),
        sa.Column('accent_color', sa.String(7), nullable=False, server_default='#FF6600'),
        sa.Column('visual_theme', sa.String(), nullable=False, server_default='professional'),
        sa.Column('animation_style', sa.String(50), nullable=True),
        sa.Column('particle_effects', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('glow_intensity', sa.Float(), nullable=False, server_default='0.5'),
        sa.Column('achievement_badges', sa.JSON(), nullable=False, server_default='[]'),
        sa.Column('specialization_badge', sa.String(100), nullable=True),
        sa.Column('university_badge', sa.String(100), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['agent_id'], ['agents.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('agent_id')
    )
    op.create_index(op.f('ix_visual_profiles_agent_id'), 'visual_profiles', ['agent_id'], unique=True)
    
    # Create behavioral_profiles table
    op.create_table(
        'behavioral_profiles',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('agent_id', sa.String(), nullable=False),
        sa.Column('learning_style', sa.String(), nullable=False, server_default='visual'),
        sa.Column('learning_pace', sa.Float(), nullable=False, server_default='1.0'),
        sa.Column('learning_retention', sa.Float(), nullable=False, server_default='0.8'),
        sa.Column('risk_tolerance', sa.Float(), nullable=False, server_default='0.5'),
        sa.Column('failure_recovery', sa.Float(), nullable=False, server_default='0.7'),
        sa.Column('decision_speed', sa.Float(), nullable=False, server_default='0.5'),
        sa.Column('decision_confidence', sa.Float(), nullable=False, server_default='0.6'),
        sa.Column('second_guessing', sa.Float(), nullable=False, server_default='0.3'),
        sa.Column('collaboration_style', sa.String(), nullable=False, server_default='equal'),
        sa.Column('communication_frequency', sa.Float(), nullable=False, server_default='0.6'),
        sa.Column('feedback_receptiveness', sa.Float(), nullable=False, server_default='0.8'),
        sa.Column('communication_tone', sa.String(), nullable=False, server_default='technical'),
        sa.Column('explanation_depth', sa.String(50), nullable=False, server_default='moderate'),
        sa.Column('question_asking', sa.Float(), nullable=False, server_default='0.6'),
        sa.Column('specialization_focus', sa.String(100), nullable=True),
        sa.Column('cross_specialization_interest', sa.Float(), nullable=False, server_default='0.3'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['agent_id'], ['agents.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('agent_id')
    )
    op.create_index(op.f('ix_behavioral_profiles_agent_id'), 'behavioral_profiles', ['agent_id'], unique=True)


def downgrade() -> None:
    """Drop visual and behavioral profile tables."""
    op.drop_index(op.f('ix_behavioral_profiles_agent_id'), table_name='behavioral_profiles')
    op.drop_table('behavioral_profiles')
    op.drop_index(op.f('ix_visual_profiles_agent_id'), table_name='visual_profiles')
    op.drop_table('visual_profiles')

