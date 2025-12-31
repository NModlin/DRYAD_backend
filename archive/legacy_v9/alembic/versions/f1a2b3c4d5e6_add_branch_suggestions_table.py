"""add branch suggestions table

Revision ID: f1a2b3c4d5e6
Revises: e8f9a1b2c3d4
Create Date: 2025-10-07 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite

# revision identifiers, used by Alembic.
revision = 'f1a2b3c4d5e6'
down_revision = 'e8f9a1b2c3d4'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create branch_suggestions table."""
    op.create_table(
        'dryad_branch_suggestions',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('dialogue_id', sa.String(), nullable=False),
        sa.Column('branch_id', sa.String(), nullable=False),
        sa.Column('created_branch_id', sa.String(), nullable=True),
        sa.Column('suggestion_type', sa.String(length=50), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('source_text', sa.Text(), nullable=False),
        sa.Column('priority_score', sa.Float(), nullable=False),
        sa.Column('priority_level', sa.String(length=50), nullable=False),
        sa.Column('relevance_score', sa.Float(), nullable=False),
        sa.Column('confidence', sa.Float(), nullable=False),
        sa.Column('estimated_depth', sa.Integer(), nullable=False),
        sa.Column('keywords', sa.JSON(), nullable=True),
        sa.Column('extra_metadata', sa.JSON(), nullable=True),
        sa.Column('is_auto_created', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['branch_id'], ['dryad_branches.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['created_branch_id'], ['dryad_branches.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['dialogue_id'], ['dryad_dialogues.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes
    op.create_index('ix_dryad_branch_suggestions_id', 'dryad_branch_suggestions', ['id'])
    op.create_index('ix_dryad_branch_suggestions_dialogue_id', 'dryad_branch_suggestions', ['dialogue_id'])
    op.create_index('ix_dryad_branch_suggestions_branch_id', 'dryad_branch_suggestions', ['branch_id'])
    op.create_index('ix_dryad_branch_suggestions_created_branch_id', 'dryad_branch_suggestions', ['created_branch_id'])
    op.create_index('ix_dryad_branch_suggestions_suggestion_type', 'dryad_branch_suggestions', ['suggestion_type'])
    op.create_index('ix_dryad_branch_suggestions_priority_score', 'dryad_branch_suggestions', ['priority_score'])
    op.create_index('ix_dryad_branch_suggestions_priority_level', 'dryad_branch_suggestions', ['priority_level'])
    op.create_index('ix_dryad_branch_suggestions_is_auto_created', 'dryad_branch_suggestions', ['is_auto_created'])
    op.create_index('ix_dryad_branch_suggestions_created_at', 'dryad_branch_suggestions', ['created_at'])


def downgrade() -> None:
    """Drop branch_suggestions table."""
    op.drop_index('ix_dryad_branch_suggestions_created_at', table_name='dryad_branch_suggestions')
    op.drop_index('ix_dryad_branch_suggestions_is_auto_created', table_name='dryad_branch_suggestions')
    op.drop_index('ix_dryad_branch_suggestions_priority_level', table_name='dryad_branch_suggestions')
    op.drop_index('ix_dryad_branch_suggestions_priority_score', table_name='dryad_branch_suggestions')
    op.drop_index('ix_dryad_branch_suggestions_suggestion_type', table_name='dryad_branch_suggestions')
    op.drop_index('ix_dryad_branch_suggestions_created_branch_id', table_name='dryad_branch_suggestions')
    op.drop_index('ix_dryad_branch_suggestions_branch_id', table_name='dryad_branch_suggestions')
    op.drop_index('ix_dryad_branch_suggestions_dialogue_id', table_name='dryad_branch_suggestions')
    op.drop_index('ix_dryad_branch_suggestions_id', table_name='dryad_branch_suggestions')
    op.drop_table('dryad_branch_suggestions')

