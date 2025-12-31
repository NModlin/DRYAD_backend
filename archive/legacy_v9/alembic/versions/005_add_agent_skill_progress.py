"""Add Agent Skill Progress - Phase 2

Revision ID: 005_agent_skill_progress
Revises: 004_skill_nodes
Create Date: 2025-10-23 00:03:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = '005_agent_skill_progress'
down_revision = '004_skill_nodes'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create agent_skill_progress table."""
    
    # Create agent_skill_progress table
    op.create_table(
        'agent_skill_progress',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('agent_id', sa.String(), nullable=False),
        sa.Column('skill_node_id', sa.String(), nullable=False),
        sa.Column('current_level', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('current_experience', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('is_unlocked', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('unlocked_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['agent_id'], ['agents.id'], ),
        sa.ForeignKeyConstraint(['skill_node_id'], ['skill_nodes.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('agent_id', 'skill_node_id', name='uq_agent_skill')
    )
    
    # Create indexes
    op.create_index(op.f('ix_agent_skill_progress_agent_id'), 'agent_skill_progress', ['agent_id'], unique=False)
    op.create_index(op.f('ix_agent_skill_progress_skill_node_id'), 'agent_skill_progress', ['skill_node_id'], unique=False)


def downgrade() -> None:
    """Drop agent_skill_progress table."""
    op.drop_index(op.f('ix_agent_skill_progress_skill_node_id'), table_name='agent_skill_progress')
    op.drop_index(op.f('ix_agent_skill_progress_agent_id'), table_name='agent_skill_progress')
    op.drop_table('agent_skill_progress')

