"""Create tool registry and memory guild tables

Revision ID: 001_create_tool_registry_tables
Revises: 
Create Date: 2025-10-28 20:15:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '001_create_tool_registry_tables'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create all tables for tool registry and memory guild system"""
    
    # Tool Registry Table
    op.create_table('tool_registry',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('version', sa.String(50), nullable=False, server_default='1.0.0'),
        sa.Column('function_signature', sa.JSON, nullable=False),
        sa.Column('permissions', sa.JSON, nullable=False, server_default='{}'),
        sa.Column('requires_sandbox', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('sandbox_image', sa.String(255), nullable=True),
        sa.Column('max_session_duration', sa.Integer(), nullable=False, server_default='300'),
        sa.Column('stateful', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )
    
    # Tool Permissions Table
    op.create_table('tool_permissions',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('tool_id', sa.String(36), nullable=False),
        sa.Column('agent_id', sa.String(36), nullable=True),
        sa.Column('user_id', sa.String(36), nullable=True),
        sa.Column('permission_level', sa.String(50), nullable=False, server_default='read'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['tool_id'], ['tool_registry.id'], ondelete='CASCADE')
    )
    
    # Tool Sessions Table
    op.create_table('tool_sessions',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('tool_id', sa.String(36), nullable=False),
        sa.Column('agent_id', sa.String(36), nullable=False),
        sa.Column('session_state', sa.JSON, nullable=True),
        sa.Column('execution_id', sa.String(36), nullable=True),
        sa.Column('sandbox_id', sa.String(255), nullable=True),
        sa.Column('sandbox_status', sa.String(50), nullable=True),
        sa.Column('status', sa.String(50), nullable=False, server_default='active'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('expires_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['tool_id'], ['tool_registry.id'], ondelete='CASCADE')
    )
    
    # Tool Executions Table
    op.create_table('tool_executions',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('session_id', sa.String(36), nullable=False),
        sa.Column('input_data', postgresql.JSONB, nullable=False),
        sa.Column('output_data', postgresql.JSONB, nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('execution_time_ms', sa.Integer(), nullable=True),
        sa.Column('resource_usage', postgresql.JSONB, nullable=True),
        sa.Column('status', sa.String(50), nullable=False, server_default='pending'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['session_id'], ['tool_sessions.id'], ondelete='CASCADE')
    )
    
    # Memory Contexts Table
    op.create_table('memory_contexts',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('agent_id', sa.String(36), nullable=False),
        sa.Column('context_data', sa.JSON, nullable=False),
        sa.Column('parent_context_id', sa.String(36), nullable=True),
        sa.Column('context_type', sa.String(50), nullable=False, server_default='general'),
        sa.Column('priority', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('expires_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['parent_context_id'], ['memory_contexts.id'], ondelete='SET NULL')
    )
    
    # Error Logs Table
    op.create_table('error_logs',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('error_type', sa.String(255), nullable=False),
        sa.Column('error_message', sa.Text(), nullable=False),
        sa.Column('component', sa.String(255), nullable=False),
        sa.Column('fix_applied', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('fix_details', sa.JSON, nullable=True),
        sa.Column('severity', sa.String(50), nullable=False, server_default='medium'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('resolved_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for better performance
    op.create_index('idx_tool_registry_name', 'tool_registry', ['name'])
    op.create_index('idx_tool_permissions_tool_id', 'tool_permissions', ['tool_id'])
    op.create_index('idx_tool_sessions_tool_id', 'tool_sessions', ['tool_id'])
    op.create_index('idx_tool_sessions_agent_id', 'tool_sessions', ['agent_id'])
    op.create_index('idx_tool_executions_session_id', 'tool_executions', ['session_id'])
    op.create_index('idx_memory_contexts_agent_id', 'memory_contexts', ['agent_id'])
    op.create_index('idx_memory_contexts_parent_id', 'memory_contexts', ['parent_context_id'])
    op.create_index('idx_error_logs_component', 'error_logs', ['component'])
    op.create_index('idx_error_logs_created_at', 'error_logs', ['created_at'])


def downgrade() -> None:
    """Drop all tables created in this migration"""
    op.drop_index('idx_error_logs_created_at')
    op.drop_index('idx_error_logs_component')
    op.drop_index('idx_memory_contexts_parent_id')
    op.drop_index('idx_memory_contexts_agent_id')
    op.drop_index('idx_tool_executions_session_id')
    op.drop_index('idx_tool_sessions_agent_id')
    op.drop_index('idx_tool_sessions_tool_id')
    op.drop_index('idx_tool_permissions_tool_id')
    op.drop_index('idx_tool_registry_name')
    
    op.drop_table('error_logs')
    op.drop_table('memory_contexts')
    op.drop_table('tool_executions')
    op.drop_table('tool_sessions')
    op.drop_table('tool_permissions')
    op.drop_table('tool_registry')