"""Add Specialization Profiles - Phase 2

Revision ID: 002_specialization_profiles
Revises: 001_agent_enhancements_phase1
Create Date: 2025-10-23 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = '002_specialization_profiles'
down_revision = '001_agent_enhancements_phase1'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create specialization_profiles table."""
    
    # Create specialization_profiles table
    op.create_table(
        'specialization_profiles',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('agent_id', sa.String(), nullable=False),
        sa.Column('primary_specialization', sa.String(), nullable=False, server_default='data_science'),
        sa.Column('specialization_level', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('secondary_specializations', sa.JSON(), nullable=False, server_default='[]'),
        sa.Column('specialization_tools', sa.JSON(), nullable=False, server_default='[]'),
        sa.Column('specialization_curriculum', sa.String(), nullable=True),
        sa.Column('specialization_constraints', sa.JSON(), nullable=False, server_default='{}'),
        sa.Column('cross_specialization_enabled', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('cross_specialization_penalty', sa.Float(), nullable=False, server_default='0.2'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['agent_id'], ['agents.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('agent_id')
    )
    
    # Create indexes
    op.create_index(op.f('ix_specialization_profiles_agent_id'), 'specialization_profiles', ['agent_id'], unique=True)
    op.create_index(op.f('ix_specialization_profiles_primary_specialization'), 'specialization_profiles', ['primary_specialization'], unique=False)


def downgrade() -> None:
    """Drop specialization_profiles table."""
    op.drop_index(op.f('ix_specialization_profiles_primary_specialization'), table_name='specialization_profiles')
    op.drop_index(op.f('ix_specialization_profiles_agent_id'), table_name='specialization_profiles')
    op.drop_table('specialization_profiles')

