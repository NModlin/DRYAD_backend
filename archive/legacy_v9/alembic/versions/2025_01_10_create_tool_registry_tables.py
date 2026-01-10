"""create tool registry tables

Revision ID: 2025_01_10_tool_registry
Revises: f1a2b3c4d5e6
Create Date: 2025-01-10 00:00:00.000000

Level 0 Component: Tool Registry Service
Part of DRYAD.AI Agent Evolution Architecture
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '2025_01_10_tool_registry'
down_revision = 'f1a2b3c4d5e6'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create tool registry tables."""

    # Detect database type for conditional type handling
    bind = op.get_bind()
    is_postgresql = bind.dialect.name == 'postgresql'

    # Set types based on database
    if is_postgresql:
        uuid_type = postgresql.UUID(as_uuid=True)
        json_type = postgresql.JSONB(astext_type=sa.Text())
        timestamp_default = sa.text('now()')
    else:
        # SQLite fallback
        uuid_type = sa.String(36)
        json_type = sa.JSON
        timestamp_default = sa.text("(datetime('now'))")

    # Create tools table
    op.create_table(
        'tools',
        sa.Column('tool_id', uuid_type, primary_key=True, nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('version', sa.String(50), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('schema_json', json_type, nullable=False),
        sa.Column('docker_image_uri', sa.String(500), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=timestamp_default, nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=timestamp_default, nullable=False),
        sa.Column('is_active', sa.Boolean(), default=True, nullable=False),
        sa.UniqueConstraint('name', 'version', name='unique_tool_version'),
    )

    # Create indexes for tools table
    op.create_index('idx_tools_name', 'tools', ['name'])
    op.create_index('idx_tools_version', 'tools', ['version'])
    op.create_index('idx_tools_active', 'tools', ['is_active'])

    # Create index with PostgreSQL-specific options if available
    if is_postgresql:
        op.create_index('idx_tools_created', 'tools', ['created_at'], postgresql_ops={'created_at': 'DESC'})
    else:
        op.create_index('idx_tools_created', 'tools', ['created_at'])

    # Create tool_permissions table
    op.create_table(
        'tool_permissions',
        sa.Column('permission_id', uuid_type, primary_key=True, nullable=False),
        sa.Column('principal_id', sa.String(255), nullable=False),
        sa.Column('principal_type', sa.String(20), nullable=False),
        sa.Column('tool_id', uuid_type, nullable=False),
        sa.Column('allow_stateful_execution', sa.Boolean(), default=False, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=timestamp_default, nullable=False),
        sa.Column('created_by', sa.String(255), nullable=True),
        sa.ForeignKeyConstraint(['tool_id'], ['tools.tool_id'], ondelete='CASCADE'),
        sa.UniqueConstraint('principal_id', 'principal_type', 'tool_id', name='unique_principal_tool'),
        sa.CheckConstraint("principal_type IN ('agent', 'role')", name='check_principal_type'),
    )

    # Create indexes for tool_permissions table
    op.create_index('idx_tool_permissions_principal', 'tool_permissions', ['principal_id', 'principal_type'])
    op.create_index('idx_tool_permissions_tool', 'tool_permissions', ['tool_id'])


def downgrade() -> None:
    """Drop tool registry tables."""
    
    # Drop indexes first
    op.drop_index('idx_tool_permissions_tool', table_name='tool_permissions')
    op.drop_index('idx_tool_permissions_principal', table_name='tool_permissions')
    op.drop_index('idx_tools_created', table_name='tools')
    op.drop_index('idx_tools_active', table_name='tools')
    op.drop_index('idx_tools_version', table_name='tools')
    op.drop_index('idx_tools_name', table_name='tools')
    
    # Drop tables
    op.drop_table('tool_permissions')
    op.drop_table('tools')

