"""Add Skill Nodes - Phase 2

Revision ID: 004_skill_nodes
Revises: 003_skill_trees
Create Date: 2025-10-23 00:02:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = '004_skill_nodes'
down_revision = '003_skill_trees'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create skill_nodes table."""
    
    # Create skill_nodes table
    op.create_table(
        'skill_nodes',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('skill_tree_id', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('max_level', sa.Integer(), nullable=False, server_default='5'),
        sa.Column('experience_per_level', sa.Integer(), nullable=False, server_default='100'),
        sa.Column('prerequisites', sa.JSON(), nullable=False, server_default='[]'),
        sa.Column('capability_bonuses', sa.JSON(), nullable=False, server_default='{}'),
        sa.Column('personality_shifts', sa.JSON(), nullable=False, server_default='{}'),
        sa.Column('unlocks_tools', sa.JSON(), nullable=False, server_default='[]'),
        sa.Column('unlocks_competitions', sa.JSON(), nullable=False, server_default='[]'),
        sa.Column('tree_position_x', sa.Integer(), nullable=True),
        sa.Column('tree_position_y', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['skill_tree_id'], ['skill_trees.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes
    op.create_index(op.f('ix_skill_nodes_skill_tree_id'), 'skill_nodes', ['skill_tree_id'], unique=False)


def downgrade() -> None:
    """Drop skill_nodes table."""
    op.drop_index(op.f('ix_skill_nodes_skill_tree_id'), table_name='skill_nodes')
    op.drop_table('skill_nodes')

