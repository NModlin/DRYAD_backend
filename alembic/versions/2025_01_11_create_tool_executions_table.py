"""Create tool_executions table for Level 1 Sandbox Environment

Revision ID: 2025_01_11_create_tool_executions_table
Revises: 2025_01_10_create_tool_registry_tables
Create Date: 2025-01-11 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '2025_01_11_create_tool_executions_table'
down_revision = '2025_01_10_logging'
branch_labels = None
depends_on = None


def upgrade():
    """Create tool_executions table for Level 1 Sandbox Environment."""

    # Detect database type for conditional type handling
    bind = op.get_bind()
    is_postgresql = bind.dialect.name == 'postgresql'

    # Set types based on database
    if is_postgresql:
        uuid_type = postgresql.UUID(as_uuid=True)
        json_type = postgresql.JSONB
        timestamp_default = sa.func.now()
    else:
        # SQLite fallback
        uuid_type = sa.String(36)
        json_type = sa.JSON
        timestamp_default = sa.func.now()

    # Create tool_executions table
    op.create_table(
        'tool_executions',
        sa.Column('id', uuid_type, primary_key=True),
        sa.Column('execution_id', sa.String(255), nullable=False, unique=True),
        sa.Column('session_id', sa.String(255), nullable=False),
        sa.Column('tool_id', uuid_type, nullable=False),
        sa.Column('agent_id', sa.String(255), nullable=False),

        # Execution details
        sa.Column('command', sa.Text, nullable=False),
        sa.Column('working_directory', sa.String(500), nullable=True),
        sa.Column('environment_variables', json_type, nullable=True),
        sa.Column('input_parameters', json_type, nullable=True),

        # Results
        sa.Column('stdout', sa.Text, nullable=True),
        sa.Column('stderr', sa.Text, nullable=True),
        sa.Column('exit_code', sa.Integer, nullable=True),
        sa.Column('success', sa.Boolean, nullable=False, default=False),
        sa.Column('error_message', sa.Text, nullable=True),

        # Performance metrics
        sa.Column('execution_time_ms', sa.Integer, nullable=True),
        sa.Column('memory_usage_mb', sa.Integer, nullable=True),
        sa.Column('cpu_usage_percent', sa.Integer, nullable=True),

        # Security and resource tracking
        sa.Column('resource_limits_enforced', sa.Boolean, default=True),
        sa.Column('security_violations', json_type, nullable=True),

        # Timestamps
        sa.Column('started_at', sa.DateTime, nullable=False, default=timestamp_default),
        sa.Column('completed_at', sa.DateTime, nullable=True),

        # Foreign key constraints (must be in create_table for SQLite)
        sa.ForeignKeyConstraint(['session_id'], ['tool_sessions.session_id'], ondelete='CASCADE', name='fk_tool_executions_session_id'),
        sa.ForeignKeyConstraint(['tool_id'], ['agent_tool_catalog.id'], ondelete='CASCADE', name='fk_tool_executions_tool_id'),
    )

    # Create indexes for performance
    op.create_index('ix_tool_executions_execution_id', 'tool_executions', ['execution_id'])
    op.create_index('ix_tool_executions_session_id', 'tool_executions', ['session_id'])
    op.create_index('ix_tool_executions_tool_id', 'tool_executions', ['tool_id'])
    op.create_index('ix_tool_executions_agent_id', 'tool_executions', ['agent_id'])
    op.create_index('ix_tool_executions_started_at', 'tool_executions', ['started_at'])
    op.create_index('ix_tool_executions_success', 'tool_executions', ['success'])


def downgrade():
    """Drop tool_executions table."""
    op.drop_table('tool_executions')
