"""add agent registry tables

Revision ID: g2a3b4c5d6e7
Revises: f1a2b3c4d5e6
Create Date: 2025-10-08 23:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'g2a3b4c5d6e7'
down_revision = 'f1a2b3c4d5e6'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Detect database type
    bind = op.get_bind()
    is_postgresql = bind.dialect.name == 'postgresql'

    # Create enums for PostgreSQL only
    if is_postgresql:
        agent_tier_enum = postgresql.ENUM('orchestrator', 'specialist', 'execution', name='agenttier', create_type=False)
        agent_tier_enum.create(bind, checkfirst=True)

        agent_status_enum = postgresql.ENUM('active', 'inactive', 'maintenance', 'error', name='agentstatus', create_type=False)
        agent_status_enum.create(bind, checkfirst=True)

        tier_type = agent_tier_enum
        status_type = agent_status_enum
        json_type = postgresql.JSONB
        uuid_type = postgresql.UUID(as_uuid=True)
    else:
        # SQLite fallback
        tier_type = sa.String(50)
        status_type = sa.String(50)
        json_type = sa.JSON
        uuid_type = sa.String(36)

    # Create system_agents table
    op.create_table(
        'system_agents',
        sa.Column('id', uuid_type, primary_key=True),
        sa.Column('agent_id', sa.String(100), unique=True, nullable=False, index=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('display_name', sa.String(255), nullable=False),
        sa.Column('tier', tier_type, nullable=False, index=True),
        sa.Column('category', sa.String(100), nullable=False, index=True),
        sa.Column('capabilities', json_type, nullable=False, server_default='[]'),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('role', sa.Text, nullable=True),
        sa.Column('goal', sa.Text, nullable=True),
        sa.Column('backstory', sa.Text, nullable=True),
        sa.Column('configuration', json_type, nullable=False, server_default='{}'),
        sa.Column('llm_config', json_type, nullable=True),
        sa.Column('tools', json_type, nullable=False, server_default='[]'),
        sa.Column('status', status_type, nullable=False, server_default='active', index=True),
        sa.Column('health_check_url', sa.String(500), nullable=True),
        sa.Column('last_health_check', sa.DateTime(timezone=True), nullable=True),
        sa.Column('health_status', sa.String(50), nullable=True),
        sa.Column('total_tasks', sa.Integer, server_default='0'),
        sa.Column('successful_tasks', sa.Integer, server_default='0'),
        sa.Column('failed_tasks', sa.Integer, server_default='0'),
        sa.Column('avg_execution_time', sa.Float, server_default='0.0'),
        sa.Column('total_tokens_used', sa.Integer, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('last_used_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('extra_data', json_type, nullable=True),
    )

    # Create agent_capability_matches table
    op.create_table(
        'agent_capability_matches',
        sa.Column('id', uuid_type, primary_key=True),
        sa.Column('capability', sa.String(255), nullable=False, index=True),
        sa.Column('agent_id', sa.String(100), nullable=False, index=True),
        sa.Column('proficiency', sa.Float, server_default='1.0'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
    )

    # Create indexes
    op.create_index('ix_system_agents_tier_status', 'system_agents', ['tier', 'status'])
    op.create_index('ix_agent_capability_matches_capability_agent', 'agent_capability_matches', ['capability', 'agent_id'])


def downgrade() -> None:
    # Drop indexes
    op.drop_index('ix_agent_capability_matches_capability_agent', table_name='agent_capability_matches')
    op.drop_index('ix_system_agents_tier_status', table_name='system_agents')

    # Drop tables
    op.drop_table('agent_capability_matches')
    op.drop_table('system_agents')

    # Drop enums for PostgreSQL only
    bind = op.get_bind()
    if bind.dialect.name == 'postgresql':
        agent_status_enum = postgresql.ENUM('active', 'inactive', 'maintenance', 'error', name='agentstatus')
        agent_status_enum.drop(bind, checkfirst=True)

        agent_tier_enum = postgresql.ENUM('orchestrator', 'specialist', 'execution', name='agenttier')
        agent_tier_enum.drop(bind, checkfirst=True)

