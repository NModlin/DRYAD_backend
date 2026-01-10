"""add universities

Revision ID: 007_add_universities
Revises: 006_progression_paths
Create Date: 2025-10-23 14:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite

# revision identifiers, used by Alembic.
revision = '007_add_universities'
down_revision = '006_progression_paths'
branch_labels = None
depends_on = None


def upgrade():
    """Create universities table"""
    
    # Determine JSON type based on dialect
    json_type = sa.JSON().with_variant(sa.Text(), 'sqlite')
    
    # Create universities table
    op.create_table(
        'universities',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        
        # Ownership and multi-tenancy
        sa.Column('owner_user_id', sa.String(), nullable=False),
        sa.Column('client_app_id', sa.String(), nullable=True),
        sa.Column('tenant_id', sa.String(), nullable=True),
        sa.Column('organization_id', sa.String(), nullable=True),
        
        # Configuration
        sa.Column('settings', json_type, nullable=False),
        sa.Column('isolation_level', sa.String(length=50), nullable=False),
        sa.Column('max_agents', sa.Integer(), nullable=False),
        sa.Column('max_concurrent_competitions', sa.Integer(), nullable=False),
        sa.Column('storage_quota_mb', sa.Integer(), nullable=False),
        
        # Specialization focus
        sa.Column('primary_specialization', sa.String(length=100), nullable=True),
        sa.Column('secondary_specializations', json_type, nullable=False),
        
        # Status and lifecycle
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_activity_at', sa.DateTime(timezone=True), nullable=True),
        
        # Statistics
        sa.Column('total_agents', sa.Integer(), nullable=False),
        sa.Column('active_agents', sa.Integer(), nullable=False),
        sa.Column('total_competitions', sa.Integer(), nullable=False),
        sa.Column('total_training_data_points', sa.Integer(), nullable=False),
        
        # Metadata
        sa.Column('tags', json_type, nullable=False),
        sa.Column('custom_metadata', json_type, nullable=False),
        
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes
    op.create_index('idx_university_name', 'universities', ['name'])
    op.create_index('idx_university_owner', 'universities', ['owner_user_id'])
    op.create_index('idx_university_tenant', 'universities', ['tenant_id'])
    op.create_index('idx_university_status', 'universities', ['status'])
    op.create_index('idx_university_owner_status', 'universities', ['owner_user_id', 'status'])
    op.create_index('idx_university_tenant_status', 'universities', ['tenant_id', 'status'])


def downgrade():
    """Drop universities table"""
    op.drop_index('idx_university_tenant_status', table_name='universities')
    op.drop_index('idx_university_owner_status', table_name='universities')
    op.drop_index('idx_university_status', table_name='universities')
    op.drop_index('idx_university_tenant', table_name='universities')
    op.drop_index('idx_university_owner', table_name='universities')
    op.drop_index('idx_university_name', table_name='universities')
    op.drop_table('universities')

