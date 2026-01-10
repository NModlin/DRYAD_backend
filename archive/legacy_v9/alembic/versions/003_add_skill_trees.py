"""Add Skill Trees - Phase 2

Revision ID: 003_skill_trees
Revises: 002_specialization_profiles
Create Date: 2025-10-23 00:01:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = '003_skill_trees'
down_revision = '002_specialization_profiles'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create skill_trees table."""
    
    # Create skill_trees table
    op.create_table(
        'skill_trees',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('specialization', sa.String(), nullable=False),
        sa.Column('is_custom', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('creator_id', sa.String(), nullable=True),
        sa.Column('is_public', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes
    op.create_index(op.f('ix_skill_trees_specialization'), 'skill_trees', ['specialization'], unique=False)
    op.create_index(op.f('ix_skill_trees_creator_id'), 'skill_trees', ['creator_id'], unique=False)


def downgrade() -> None:
    """Drop skill_trees table."""
    op.drop_index(op.f('ix_skill_trees_creator_id'), table_name='skill_trees')
    op.drop_index(op.f('ix_skill_trees_specialization'), table_name='skill_trees')
    op.drop_table('skill_trees')

