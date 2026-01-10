"""add_agent_enhancements

Revision ID: 57ead06e34eb
Revises: g2a3b4c5d6e7
Create Date: 2025-10-09 16:32:21.569493

Adds four major enhancements to the agent system:
1. Tool Integration System - Comprehensive tool catalog with permissions
2. Dynamic Orchestration Patterns - Peer-to-peer and hybrid collaboration
3. Runtime Guardrails - Real-time safety monitoring during execution
4. Human-in-the-Loop (HITL) Workflow - Approval system for high-risk operations
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '57ead06e34eb'
down_revision: Union[str, Sequence[str], None] = 'g2a3b4c5d6e7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Detect database type
    bind = op.get_bind()
    is_postgresql = bind.dialect.name == 'postgresql'

    # Set appropriate types based on database
    if is_postgresql:
        json_type = postgresql.JSONB
        uuid_type = postgresql.UUID(as_uuid=True)
    else:
        json_type = sa.JSON
        uuid_type = sa.String(36)

    # ========================================================================
    # 1. TOOL INTEGRATION SYSTEM
    # ========================================================================

    # Agent Tool Catalog
    op.create_table(
        'agent_tool_catalog',
        sa.Column('id', uuid_type, primary_key=True),
        sa.Column('tool_id', sa.String(100), unique=True, nullable=False, index=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('display_name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text, nullable=False),
        sa.Column('category', sa.String(50), nullable=False, index=True),
        sa.Column('security_level', sa.String(50), nullable=False, index=True),
        sa.Column('configuration_schema', json_type, nullable=True),
        sa.Column('default_configuration', json_type, nullable=True),
        sa.Column('required_permissions', json_type, nullable=False),
        sa.Column('implementation_class', sa.String(500), nullable=True),
        sa.Column('implementation_function', sa.String(500), nullable=True),
        sa.Column('max_execution_time', sa.Integer, default=30),
        sa.Column('rate_limit', sa.Integer, default=10),
        sa.Column('requires_human_approval', sa.Boolean, default=False),
        sa.Column('enabled', sa.Boolean, default=True),
        sa.Column('deprecated', sa.Boolean, default=False),
        sa.Column('deprecation_message', sa.Text, nullable=True),
        sa.Column('version', sa.String(50), default='1.0.0'),
        sa.Column('documentation_url', sa.String(500), nullable=True),
        sa.Column('examples', json_type, nullable=True),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now())
    )

    # Tool Permissions
    op.create_table(
        'tool_permissions',
        sa.Column('id', uuid_type, primary_key=True),
        sa.Column('tool_id', uuid_type, nullable=False, index=True),
        sa.Column('agent_category', sa.String(100), nullable=True, index=True),
        sa.Column('agent_tier', sa.String(50), nullable=True),
        sa.Column('allowed', sa.Boolean, default=True),
        sa.Column('max_calls_per_execution', sa.Integer, nullable=True),
        sa.Column('additional_constraints', json_type, nullable=True),
        sa.Column('requires_approval_override', sa.Boolean, default=False),
        sa.Column('approval_reason', sa.Text, nullable=True),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now())
    )

    # Tool Usage Logs
    op.create_table(
        'tool_usage_logs',
        sa.Column('id', uuid_type, primary_key=True),
        sa.Column('execution_id', uuid_type, nullable=False, index=True),
        sa.Column('tool_id', uuid_type, nullable=False, index=True),
        sa.Column('agent_id', uuid_type, nullable=False, index=True),
        sa.Column('input_parameters', json_type, nullable=True),
        sa.Column('output_result', json_type, nullable=True),
        sa.Column('execution_time', sa.Integer, nullable=True),
        sa.Column('success', sa.Boolean, default=True),
        sa.Column('error_message', sa.Text, nullable=True),
        sa.Column('approved_by', uuid_type, nullable=True),
        sa.Column('approval_timestamp', sa.DateTime, nullable=True),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now())
    )

    # ========================================================================
    # 2. DYNAMIC ORCHESTRATION PATTERNS
    # ========================================================================

    # Collaboration Workflows
    op.create_table(
        'collaboration_workflows',
        sa.Column('id', uuid_type, primary_key=True),
        sa.Column('workflow_id', sa.String(100), unique=True, nullable=False, index=True),
        sa.Column('task_description', sa.Text, nullable=False),
        sa.Column('orchestration_pattern', sa.String(50), nullable=False),
        sa.Column('initiator_agent_id', sa.String(100), nullable=False, index=True),
        sa.Column('participating_agents', json_type, nullable=False),
        sa.Column('collaboration_graph', json_type, nullable=True),
        sa.Column('status', sa.String(50), nullable=False, server_default='initiated'),
        sa.Column('final_output', json_type, nullable=True),
        sa.Column('success', sa.Boolean, nullable=True),
        sa.Column('error_message', sa.Text, nullable=True),
        sa.Column('total_steps', sa.Integer, default=0),
        sa.Column('total_execution_time', sa.Integer, nullable=True),
        sa.Column('total_tokens_used', sa.Integer, default=0),
        sa.Column('started_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('completed_at', sa.DateTime, nullable=True)
    )

    # Collaboration Steps
    op.create_table(
        'collaboration_steps',
        sa.Column('id', uuid_type, primary_key=True),
        sa.Column('workflow_id', uuid_type, nullable=False, index=True),
        sa.Column('step_number', sa.Integer, nullable=False),
        sa.Column('agent_id', sa.String(100), nullable=False),
        sa.Column('action', sa.String(255), nullable=False),
        sa.Column('input_data', json_type, nullable=True),
        sa.Column('output_data', json_type, nullable=True),
        sa.Column('status', sa.String(50), nullable=False, server_default='pending'),
        sa.Column('parallel_group', sa.Integer, nullable=True),
        sa.Column('depends_on_steps', json_type, nullable=True),
        sa.Column('execution_time', sa.Integer, nullable=True),
        sa.Column('tokens_used', sa.Integer, default=0),
        sa.Column('error_message', sa.Text, nullable=True),
        sa.Column('started_at', sa.DateTime, nullable=True),
        sa.Column('completed_at', sa.DateTime, nullable=True)
    )

    # Collaboration Patterns
    op.create_table(
        'collaboration_patterns',
        sa.Column('id', uuid_type, primary_key=True),
        sa.Column('pattern_id', sa.String(100), unique=True, nullable=False, index=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text, nullable=False),
        sa.Column('pattern_type', sa.String(50), nullable=False),
        sa.Column('required_agents', json_type, nullable=False),
        sa.Column('optional_agents', json_type, nullable=True),
        sa.Column('workflow_steps', json_type, nullable=False),
        sa.Column('decision_points', json_type, nullable=True),
        sa.Column('max_steps', sa.Integer, default=20),
        sa.Column('max_execution_time', sa.Integer, default=300),
        sa.Column('enabled', sa.Boolean, default=True),
        sa.Column('usage_count', sa.Integer, default=0),
        sa.Column('success_count', sa.Integer, default=0),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now())
    )

    # Add orchestration fields to system_agents table
    with op.batch_alter_table('system_agents', schema=None) as batch_op:
        batch_op.add_column(sa.Column('orchestration_pattern', sa.String(50), nullable=False, server_default='hierarchical'))
        batch_op.add_column(sa.Column('can_collaborate_directly', sa.Boolean, server_default='0'))
        batch_op.add_column(sa.Column('preferred_collaborators', json_type, nullable=True))

    # ========================================================================
    # 3. RUNTIME GUARDRAILS
    # ========================================================================

    # Execution Guardrails
    op.create_table(
        'execution_guardrails',
        sa.Column('id', uuid_type, primary_key=True),
        sa.Column('execution_id', uuid_type, nullable=False, index=True),
        sa.Column('agent_id', uuid_type, nullable=False, index=True),
        sa.Column('guardrail_type', sa.String(50), nullable=False, index=True),
        sa.Column('severity', sa.String(50), nullable=False, index=True),
        sa.Column('action_taken', sa.String(50), nullable=False),
        sa.Column('violation_description', sa.Text, nullable=False),
        sa.Column('violation_data', json_type, nullable=True),
        sa.Column('threshold_value', sa.Float, nullable=True),
        sa.Column('actual_value', sa.Float, nullable=True),
        sa.Column('input_text', sa.Text, nullable=True),
        sa.Column('output_text', sa.Text, nullable=True),
        sa.Column('execution_context', json_type, nullable=True),
        sa.Column('resolved', sa.Boolean, default=False),
        sa.Column('resolution_action', sa.String(255), nullable=True),
        sa.Column('resolved_by', uuid_type, nullable=True),
        sa.Column('resolved_at', sa.DateTime, nullable=True),
        sa.Column('triggered_at', sa.DateTime, server_default=sa.func.now(), index=True)
    )

    # Guardrail Configurations
    op.create_table(
        'guardrail_configurations',
        sa.Column('id', uuid_type, primary_key=True),
        sa.Column('config_id', sa.String(100), unique=True, nullable=False, index=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text, nullable=False),
        sa.Column('guardrail_type', sa.String(50), nullable=False, index=True),
        sa.Column('enabled', sa.Boolean, default=True),
        sa.Column('threshold_config', json_type, nullable=False),
        sa.Column('severity', sa.String(50), nullable=False),
        sa.Column('action', sa.String(50), nullable=False),
        sa.Column('applies_to_agents', json_type, nullable=True),
        sa.Column('applies_to_categories', json_type, nullable=True),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now())
    )

    # Guardrail Metrics
    op.create_table(
        'guardrail_metrics',
        sa.Column('id', uuid_type, primary_key=True),
        sa.Column('date', sa.DateTime, nullable=False, index=True),
        sa.Column('guardrail_type', sa.String(50), nullable=False, index=True),
        sa.Column('total_checks', sa.Integer, default=0),
        sa.Column('total_violations', sa.Integer, default=0),
        sa.Column('info_count', sa.Integer, default=0),
        sa.Column('warning_count', sa.Integer, default=0),
        sa.Column('error_count', sa.Integer, default=0),
        sa.Column('critical_count', sa.Integer, default=0),
        sa.Column('logged_count', sa.Integer, default=0),
        sa.Column('warned_count', sa.Integer, default=0),
        sa.Column('stopped_count', sa.Integer, default=0),
        sa.Column('approval_requested_count', sa.Integer, default=0),
        sa.Column('avg_check_time_ms', sa.Float, default=0.0)
    )

    # ========================================================================
    # 4. HUMAN-IN-THE-LOOP (HITL) WORKFLOW
    # ========================================================================

    # Pending Approvals
    op.create_table(
        'pending_approvals',
        sa.Column('id', uuid_type, primary_key=True),
        sa.Column('approval_id', sa.String(100), unique=True, nullable=False, index=True),
        sa.Column('execution_id', uuid_type, nullable=False, index=True),
        sa.Column('agent_id', uuid_type, nullable=False, index=True),
        sa.Column('agent_name', sa.String(255), nullable=False),
        sa.Column('action_type', sa.String(50), nullable=False, index=True),
        sa.Column('action_description', sa.Text, nullable=False),
        sa.Column('action_details', json_type, nullable=False),
        sa.Column('risk_level', sa.String(50), nullable=False, index=True),
        sa.Column('risk_factors', json_type, nullable=True),
        sa.Column('impact_assessment', sa.Text, nullable=True),
        sa.Column('requested_by', uuid_type, nullable=True),
        sa.Column('requested_at', sa.DateTime, server_default=sa.func.now(), index=True),
        sa.Column('expires_at', sa.DateTime, nullable=True),
        sa.Column('status', sa.String(50), nullable=False, server_default='pending', index=True),
        sa.Column('reviewed_by', uuid_type, nullable=True),
        sa.Column('reviewed_at', sa.DateTime, nullable=True),
        sa.Column('approval_decision', sa.String(50), nullable=True),
        sa.Column('rejection_reason', sa.Text, nullable=True),
        sa.Column('reviewer_notes', sa.Text, nullable=True),
        sa.Column('executed', sa.Boolean, default=False),
        sa.Column('execution_result', json_type, nullable=True),
        sa.Column('execution_error', sa.Text, nullable=True),
        sa.Column('executed_at', sa.DateTime, nullable=True),
        sa.Column('priority', sa.Integer, default=5),
        sa.Column('notification_sent', sa.Boolean, default=False),
        sa.Column('notification_channels', json_type, nullable=True)
    )

    # Approval Policies
    op.create_table(
        'approval_policies',
        sa.Column('id', uuid_type, primary_key=True),
        sa.Column('policy_id', sa.String(100), unique=True, nullable=False, index=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text, nullable=False),
        sa.Column('action_types', json_type, nullable=False),
        sa.Column('agent_categories', json_type, nullable=True),
        sa.Column('agent_ids', json_type, nullable=True),
        sa.Column('requires_approval', sa.Boolean, default=True),
        sa.Column('min_risk_level', sa.String(50), nullable=False),
        sa.Column('approver_roles', json_type, nullable=False),
        sa.Column('approver_users', json_type, nullable=True),
        sa.Column('require_multiple_approvers', sa.Boolean, default=False),
        sa.Column('min_approvers', sa.Integer, default=1),
        sa.Column('approval_timeout_minutes', sa.Integer, default=60),
        sa.Column('notify_on_request', sa.Boolean, default=True),
        sa.Column('notification_channels', json_type, nullable=True),
        sa.Column('enabled', sa.Boolean, default=True),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now())
    )

    # Approval Audit Logs
    op.create_table(
        'approval_audit_logs',
        sa.Column('id', uuid_type, primary_key=True),
        sa.Column('approval_id', uuid_type, nullable=False, index=True),
        sa.Column('event_type', sa.String(100), nullable=False),
        sa.Column('event_description', sa.Text, nullable=False),
        sa.Column('event_data', json_type, nullable=True),
        sa.Column('actor_id', uuid_type, nullable=True),
        sa.Column('actor_role', sa.String(100), nullable=True),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now(), index=True)
    )


def downgrade() -> None:
    """Downgrade schema."""
    # Drop tables in reverse order (respecting foreign keys)
    op.drop_table('approval_audit_logs')
    op.drop_table('approval_policies')
    op.drop_table('pending_approvals')
    op.drop_table('guardrail_metrics')
    op.drop_table('guardrail_configurations')
    op.drop_table('execution_guardrails')

    # Remove orchestration fields from system_agents
    with op.batch_alter_table('system_agents', schema=None) as batch_op:
        batch_op.drop_column('preferred_collaborators')
        batch_op.drop_column('can_collaborate_directly')
        batch_op.drop_column('orchestration_pattern')

    op.drop_table('collaboration_patterns')
    op.drop_table('collaboration_steps')
    op.drop_table('collaboration_workflows')
    op.drop_table('tool_usage_logs')
    op.drop_table('tool_permissions')
    op.drop_table('agent_tool_catalog')
