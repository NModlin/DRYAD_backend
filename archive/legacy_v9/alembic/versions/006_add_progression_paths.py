"""Add Progression Paths - Phase 2

Revision ID: 006_progression_paths
Revises: 005_agent_skill_progress
Create Date: 2025-10-23 00:04:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = '006_progression_paths'
down_revision = '005_agent_skill_progress'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create progression_paths table."""
    
    # Create progression_paths table
    op.create_table(
        'progression_paths',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('skill_tree_id', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('skill_sequence', sa.JSON(), nullable=False),
        sa.Column('estimated_duration_weeks', sa.Integer(), nullable=True),
        sa.Column('specialization', sa.String(), nullable=False),
        sa.Column('is_custom', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('creator_id', sa.String(), nullable=True),
        sa.Column('is_public', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['skill_tree_id'], ['skill_trees.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes
    op.create_index(op.f('ix_progression_paths_skill_tree_id'), 'progression_paths', ['skill_tree_id'], unique=False)
    op.create_index(op.f('ix_progression_paths_specialization'), 'progression_paths', ['specialization'], unique=False)


def downgrade() -> None:
    """Drop progression_paths table."""
    op.drop_index(op.f('ix_progression_paths_specialization'), table_name='progression_paths')
    op.drop_index(op.f('ix_progression_paths_skill_tree_id'), table_name='progression_paths')
    op.drop_table('progression_paths')

