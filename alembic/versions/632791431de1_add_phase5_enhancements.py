"""add_phase5_enhancements

Revision ID: 632791431de1
Revises: 57ead06e34eb
Create Date: 2025-10-09 19:25:11.614578

Phase 5 Enhancements:
- Task Force Collaboration (Task Force Messages table)
- Interactive HITL Consultation (Consultation Messages table)
- Stateful Sandboxed Tool Execution (Tool Sessions table)
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '632791431de1'
down_revision: Union[str, Sequence[str], None] = '57ead06e34eb'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema for Phase 5 enhancements."""

    # Detect database type
    bind = op.get_bind()
    is_postgresql = bind.dialect.name == 'postgresql'

    # Set database-agnostic types
    if is_postgresql:
        uuid_type = postgresql.UUID(as_uuid=True)
        json_type = postgresql.JSONB(astext_type=sa.Text())
    else:
        uuid_type = sa.String(36)
        json_type = sa.JSON

    # ========================================================================
    # Task 1: Task Force Collaboration
    # ========================================================================

    # Add workflow_type and terminal_state to collaboration_workflows
    op.add_column('collaboration_workflows',
        sa.Column('workflow_type', sa.String(50), nullable=False, server_default='standard'))
    op.add_column('collaboration_workflows',
        sa.Column('terminal_state', sa.String(50), nullable=True))

    # Create task_force_messages table
    op.create_table(
        'task_force_messages',
        sa.Column('id', uuid_type, primary_key=True),
        sa.Column('workflow_id', uuid_type, nullable=False),
        sa.Column('agent_id', sa.String(255), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('message_type', sa.String(50), nullable=False),
        sa.Column('metadata', json_type, nullable=True),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['workflow_id'], ['collaboration_workflows.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_task_force_messages_workflow_id', 'task_force_messages', ['workflow_id'])
    op.create_index('ix_task_force_messages_agent_id', 'task_force_messages', ['agent_id'])

    # ========================================================================
    # Task 2: Interactive HITL Consultation
    # ========================================================================

    # Add consultation fields to pending_approvals
    op.add_column('pending_approvals',
        sa.Column('consultation_active', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('pending_approvals',
        sa.Column('consultation_started_at', sa.DateTime(), nullable=True))
    op.add_column('pending_approvals',
        sa.Column('consultation_ended_at', sa.DateTime(), nullable=True))

    # Create consultation_messages table
    op.create_table(
        'consultation_messages',
        sa.Column('id', uuid_type, primary_key=True),
        sa.Column('approval_id', uuid_type, nullable=False),
        sa.Column('sender_id', sa.String(255), nullable=False),
        sa.Column('sender_type', sa.String(50), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('metadata', json_type, nullable=True),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['approval_id'], ['pending_approvals.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_consultation_messages_approval_id', 'consultation_messages', ['approval_id'])
    op.create_index('ix_consultation_messages_sender_id', 'consultation_messages', ['sender_id'])

    # ========================================================================
    # Task 3: Stateful Sandboxed Tool Execution
    # ========================================================================

    # Add stateful execution fields to agent_tool_catalog
    op.add_column('agent_tool_catalog',
        sa.Column('stateful', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('agent_tool_catalog',
        sa.Column('requires_sandbox', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('agent_tool_catalog',
        sa.Column('sandbox_image', sa.String(255), nullable=True))
    op.add_column('agent_tool_catalog',
        sa.Column('max_session_duration', sa.Integer(), nullable=True, server_default='300'))

    # Create tool_sessions table
    op.create_table(
        'tool_sessions',
        sa.Column('id', uuid_type, primary_key=True),
        sa.Column('session_id', sa.String(255), nullable=False, unique=True),
        sa.Column('tool_id', uuid_type, nullable=False),
        sa.Column('agent_id', sa.String(255), nullable=False),
        sa.Column('execution_id', sa.String(255), nullable=True),
        sa.Column('sandbox_id', sa.String(255), nullable=True),
        sa.Column('sandbox_status', sa.String(50), nullable=True),
        sa.Column('status', sa.String(50), nullable=False, server_default='active'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('expires_at', sa.DateTime(), nullable=True),
        sa.Column('closed_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['tool_id'], ['agent_tool_catalog.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_tool_sessions_session_id', 'tool_sessions', ['session_id'])
    op.create_index('ix_tool_sessions_tool_id', 'tool_sessions', ['tool_id'])
    op.create_index('ix_tool_sessions_agent_id', 'tool_sessions', ['agent_id'])
    op.create_index('ix_tool_sessions_execution_id', 'tool_sessions', ['execution_id'])


def downgrade() -> None:
    """Downgrade schema for Phase 5 enhancements."""

    # Drop tool_sessions table
    op.drop_index('ix_tool_sessions_execution_id', 'tool_sessions')
    op.drop_index('ix_tool_sessions_agent_id', 'tool_sessions')
    op.drop_index('ix_tool_sessions_tool_id', 'tool_sessions')
    op.drop_index('ix_tool_sessions_session_id', 'tool_sessions')
    op.drop_table('tool_sessions')

    # Remove stateful execution fields from agent_tool_catalog
    op.drop_column('agent_tool_catalog', 'max_session_duration')
    op.drop_column('agent_tool_catalog', 'sandbox_image')
    op.drop_column('agent_tool_catalog', 'requires_sandbox')
    op.drop_column('agent_tool_catalog', 'stateful')

    # Drop consultation_messages table
    op.drop_index('ix_consultation_messages_sender_id', 'consultation_messages')
    op.drop_index('ix_consultation_messages_approval_id', 'consultation_messages')
    op.drop_table('consultation_messages')

    # Remove consultation fields from pending_approvals
    op.drop_column('pending_approvals', 'consultation_ended_at')
    op.drop_column('pending_approvals', 'consultation_started_at')
    op.drop_column('pending_approvals', 'consultation_active')

    # Drop task_force_messages table
    op.drop_index('ix_task_force_messages_agent_id', 'task_force_messages')
    op.drop_index('ix_task_force_messages_workflow_id', 'task_force_messages')
    op.drop_table('task_force_messages')

    # Remove workflow_type and terminal_state from collaboration_workflows
    op.drop_column('collaboration_workflows', 'terminal_state')
    op.drop_column('collaboration_workflows', 'workflow_type')
