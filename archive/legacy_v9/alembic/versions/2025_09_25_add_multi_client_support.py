"""add_multi_client_support

Revision ID: 2025_09_25_multi_client
Revises: 0b2f849dc961
Create Date: 2025-09-25 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite

# revision identifiers, used by Alembic.
revision = '2025_09_25_multi_client'
down_revision = '0b2f849dc961'
branch_labels = None
depends_on = None


def upgrade():
    # Create organizations table
    op.create_table('organizations',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('settings', sa.JSON(), nullable=True),
        sa.Column('isolation_level', sa.String(length=50), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create client_applications table
    op.create_table('client_applications',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('organization_id', sa.String(length=255), nullable=True),
        sa.Column('api_key_hash', sa.String(length=255), nullable=False),
        sa.Column('api_key_prefix', sa.String(length=20), nullable=False),
        sa.Column('permissions', sa.JSON(), nullable=True),
        sa.Column('isolation_level', sa.String(length=50), nullable=True),
        sa.Column('settings', sa.JSON(), nullable=True),
        sa.Column('mcp_enabled', sa.Boolean(), nullable=True),
        sa.Column('mcp_version', sa.String(length=20), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True),
        sa.Column('last_used', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_client_applications_api_key_hash'), 'client_applications', ['api_key_hash'], unique=True)
    op.create_index(op.f('ix_client_applications_organization_id'), 'client_applications', ['organization_id'], unique=False)
    
    # Create shared_knowledge table
    op.create_table('shared_knowledge',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('content_hash', sa.String(length=255), nullable=False),
        sa.Column('content_type', sa.String(length=50), nullable=False),
        sa.Column('anonymized_content', sa.Text(), nullable=False),
        sa.Column('embedding_vector', sa.JSON(), nullable=True),
        sa.Column('privacy_level', sa.String(length=50), nullable=True),
        sa.Column('contributing_clients', sa.JSON(), nullable=True),
        sa.Column('excluded_clients', sa.JSON(), nullable=True),
        sa.Column('tags', sa.JSON(), nullable=True),
        sa.Column('category', sa.String(length=100), nullable=True),
        sa.Column('confidence_score', sa.Float(), nullable=True),
        sa.Column('access_count', sa.Integer(), nullable=True),
        sa.Column('last_accessed', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_shared_knowledge_content_hash'), 'shared_knowledge', ['content_hash'], unique=True)
    
    # Add multi-client columns to users table
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.add_column(sa.Column('client_app_id', sa.String(length=255), nullable=True))
        batch_op.add_column(sa.Column('tenant_id', sa.String(length=255), nullable=True))
        batch_op.add_column(sa.Column('organization_id', sa.String(length=255), nullable=True))
        batch_op.create_index(batch_op.f('ix_users_client_app_id'), ['client_app_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_users_tenant_id'), ['tenant_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_users_organization_id'), ['organization_id'], unique=False)
        batch_op.create_foreign_key('fk_users_client_app_id', 'client_applications', ['client_app_id'], ['id'])
        batch_op.create_foreign_key('fk_users_organization_id', 'organizations', ['organization_id'], ['id'])


def downgrade():
    # Remove foreign keys and columns from users table
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.drop_constraint('fk_users_organization_id', type_='foreignkey')
        batch_op.drop_constraint('fk_users_client_app_id', type_='foreignkey')
        batch_op.drop_index(batch_op.f('ix_users_organization_id'))
        batch_op.drop_index(batch_op.f('ix_users_tenant_id'))
        batch_op.drop_index(batch_op.f('ix_users_client_app_id'))
        batch_op.drop_column('organization_id')
        batch_op.drop_column('tenant_id')
        batch_op.drop_column('client_app_id')
    
    # Drop tables
    op.drop_index(op.f('ix_shared_knowledge_content_hash'), table_name='shared_knowledge')
    op.drop_table('shared_knowledge')
    op.drop_index(op.f('ix_client_applications_organization_id'), table_name='client_applications')
    op.drop_index(op.f('ix_client_applications_api_key_hash'), table_name='client_applications')
    op.drop_table('client_applications')
    op.drop_table('organizations')
