"""Create logging tables

Revision ID: 2025_01_10_logging
Revises: 2025_01_10_memory_guild
Create Date: 2025-01-10 15:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '2025_01_10_logging'
down_revision: Union[str, None] = '2025_01_10_memory_guild'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create logging tables."""

    # Detect database type for conditional type handling
    bind = op.get_bind()
    is_postgresql = bind.dialect.name == 'postgresql'

    # Set types based on database
    if is_postgresql:
        json_type = postgresql.JSONB(astext_type=sa.Text())
        timestamp_default = sa.text('NOW()')
    else:
        # SQLite fallback
        json_type = sa.JSON
        timestamp_default = sa.text("(datetime('now'))")

    # Create system_logs table
    op.create_table(
        'system_logs',
        sa.Column('log_id', sa.BigInteger(), autoincrement=True, primary_key=True),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False, server_default=timestamp_default),
        sa.Column('level', sa.String(20), nullable=False),
        sa.Column('component', sa.String(100), nullable=False),
        sa.Column('event_type', sa.String(100), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('metadata', json_type, nullable=False, server_default='{}'),
        sa.Column('trace_id', sa.String(255), nullable=True),
        sa.Column('span_id', sa.String(255), nullable=True),
        sa.Column('agent_id', sa.String(255), nullable=True),
        sa.Column('task_id', sa.String(255), nullable=True),
        sa.CheckConstraint(
            "level IN ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL')",
            name='check_log_level'
        ),
    )

    # Create indexes for system_logs
    if is_postgresql:
        op.create_index('idx_logs_timestamp', 'system_logs', ['timestamp'], postgresql_using='btree')
    else:
        op.create_index('idx_logs_timestamp', 'system_logs', ['timestamp'])

    op.create_index('idx_logs_level', 'system_logs', ['level'])
    op.create_index('idx_logs_component', 'system_logs', ['component'])
    op.create_index('idx_logs_event_type', 'system_logs', ['event_type'])
    op.create_index('idx_logs_trace', 'system_logs', ['trace_id'])
    op.create_index('idx_logs_agent', 'system_logs', ['agent_id'])
    op.create_index('idx_logs_task', 'system_logs', ['task_id'])


def downgrade() -> None:
    """Drop logging tables."""
    
    op.drop_table('system_logs')

