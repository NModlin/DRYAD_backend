"""Add Dryad tables

Revision ID: 001_add_dryad_tables
Revises: e4be642f139f
Create Date: 2025-10-03 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite

# revision identifiers, used by Alembic.
revision = '001_add_dryad_tables'
down_revision = 'e4be642f139f'
branch_labels = None
depends_on = None


def upgrade():
    """Create Dryad tables."""
    
    # Create dryad_groves table
    op.create_table('dryad_groves',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_accessed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_favorite', sa.Boolean(), nullable=True),
        sa.Column('template_metadata', sa.JSON(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_dryad_groves_id'), 'dryad_groves', ['id'], unique=False)
    op.create_index(op.f('ix_dryad_groves_name'), 'dryad_groves', ['name'], unique=False)
    
    # Create dryad_observation_points table
    op.create_table('dryad_observation_points',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('branch_id', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('context', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_dryad_observation_points_id'), 'dryad_observation_points', ['id'], unique=False)
    
    # Create dryad_branches table
    op.create_table('dryad_branches',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('grove_id', sa.String(), nullable=False),
        sa.Column('parent_id', sa.String(), nullable=True),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('path_depth', sa.Integer(), nullable=True),
        sa.Column('status', sa.Enum('ACTIVE', 'ARCHIVED', 'PRUNED', name='branchstatus'), nullable=True),
        sa.Column('priority', sa.Enum('HIGHEST', 'HIGH', 'MEDIUM', 'LOW', 'LOWEST', name='branchpriority'), nullable=True),
        sa.Column('observation_point_id', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True),
        sa.ForeignKeyConstraint(['grove_id'], ['dryad_groves.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['observation_point_id'], ['dryad_observation_points.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['parent_id'], ['dryad_branches.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_dryad_branches_id'), 'dryad_branches', ['id'], unique=False)
    op.create_index(op.f('ix_dryad_branches_grove_id'), 'dryad_branches', ['grove_id'], unique=False)
    op.create_index(op.f('ix_dryad_branches_parent_id'), 'dryad_branches', ['parent_id'], unique=False)
    
    # Create dryad_possibilities table
    op.create_table('dryad_possibilities',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('observation_point_id', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('probability_weight', sa.Float(), nullable=True),
        sa.Column('metadata', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True),
        sa.ForeignKeyConstraint(['observation_point_id'], ['dryad_observation_points.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_dryad_possibilities_id'), 'dryad_possibilities', ['id'], unique=False)
    
    # Create dryad_vessels table
    op.create_table('dryad_vessels',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('branch_id', sa.String(), nullable=False),
        sa.Column('storage_path', sa.String(length=500), nullable=False),
        sa.Column('content_hash', sa.String(length=64), nullable=False),
        sa.Column('file_references', sa.JSON(), nullable=True),
        sa.Column('is_compressed', sa.Boolean(), nullable=True),
        sa.Column('compressed_path', sa.String(length=500), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=True),
        sa.Column('generated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_updated', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_accessed', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['branch_id'], ['dryad_branches.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_dryad_vessels_branch_id'), 'dryad_vessels', ['branch_id'], unique=False)
    op.create_index(op.f('ix_dryad_vessels_id'), 'dryad_vessels', ['id'], unique=False)
    
    # Create dryad_dialogues table
    op.create_table('dryad_dialogues',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('branch_id', sa.String(), nullable=False),
        sa.Column('oracle_used', sa.String(length=100), nullable=False),
        sa.Column('insights', sa.JSON(), nullable=True),
        sa.Column('storage_path', sa.String(length=500), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True),
        sa.ForeignKeyConstraint(['branch_id'], ['dryad_branches.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_dryad_dialogues_branch_id'), 'dryad_dialogues', ['branch_id'], unique=False)
    op.create_index(op.f('ix_dryad_dialogues_id'), 'dryad_dialogues', ['id'], unique=False)
    
    # Create dryad_dialogue_messages table
    op.create_table('dryad_dialogue_messages',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('dialogue_id', sa.String(), nullable=False),
        sa.Column('role', sa.Enum('HUMAN', 'ORACLE', 'SYSTEM', name='messagerole'), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True),
        sa.ForeignKeyConstraint(['dialogue_id'], ['dryad_dialogues.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_dryad_dialogue_messages_dialogue_id'), 'dryad_dialogue_messages', ['dialogue_id'], unique=False)
    op.create_index(op.f('ix_dryad_dialogue_messages_id'), 'dryad_dialogue_messages', ['id'], unique=False)


def downgrade():
    """Drop Dryad tables."""
    
    # Drop tables in reverse order to handle foreign key constraints
    op.drop_index(op.f('ix_dryad_dialogue_messages_id'), table_name='dryad_dialogue_messages')
    op.drop_index(op.f('ix_dryad_dialogue_messages_dialogue_id'), table_name='dryad_dialogue_messages')
    op.drop_table('dryad_dialogue_messages')
    
    op.drop_index(op.f('ix_dryad_dialogues_id'), table_name='dryad_dialogues')
    op.drop_index(op.f('ix_dryad_dialogues_branch_id'), table_name='dryad_dialogues')
    op.drop_table('dryad_dialogues')
    
    op.drop_index(op.f('ix_dryad_vessels_id'), table_name='dryad_vessels')
    op.drop_index(op.f('ix_dryad_vessels_branch_id'), table_name='dryad_vessels')
    op.drop_table('dryad_vessels')
    
    op.drop_index(op.f('ix_dryad_possibilities_id'), table_name='dryad_possibilities')
    op.drop_table('dryad_possibilities')
    
    op.drop_index(op.f('ix_dryad_branches_parent_id'), table_name='dryad_branches')
    op.drop_index(op.f('ix_dryad_branches_grove_id'), table_name='dryad_branches')
    op.drop_index(op.f('ix_dryad_branches_id'), table_name='dryad_branches')
    op.drop_table('dryad_branches')
    
    op.drop_index(op.f('ix_dryad_observation_points_id'), table_name='dryad_observation_points')
    op.drop_table('dryad_observation_points')
    
    op.drop_index(op.f('ix_dryad_groves_name'), table_name='dryad_groves')
    op.drop_index(op.f('ix_dryad_groves_id'), table_name='dryad_groves')
    op.drop_table('dryad_groves')

    # Note: SQLite doesn't support DROP TYPE (enums are stored as strings)
    # Enums are automatically removed when tables are dropped
