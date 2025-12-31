"""Add self_healing_tasks table

Revision ID: 2025_10_01_self_healing
Revises: 2025_09_25_multi_client
Create Date: 2025-10-01 14:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite

# revision identifiers, used by Alembic.
revision = '2025_10_01_self_healing'
down_revision = '2025_09_25_multi_client'
branch_labels = None
depends_on = None


def upgrade():
    """Create self_healing_tasks table."""
    op.create_table(
        'self_healing_tasks',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('error_type', sa.String(100), nullable=False, index=True),
        sa.Column('error_message', sa.Text(), nullable=False),
        sa.Column('file_path', sa.String(500), nullable=False, index=True),
        sa.Column('line_number', sa.Integer(), nullable=False),
        sa.Column('stack_trace', sa.Text(), nullable=True),
        sa.Column('severity', sa.Enum('critical', 'high', 'medium', 'low', name='errorseverity'), nullable=False, index=True),
        sa.Column('error_hash', sa.String(32), nullable=False, index=True),
        sa.Column('goal', sa.Text(), nullable=False),
        sa.Column('plan', sa.JSON(), nullable=True),
        sa.Column('status', sa.Enum('pending_review', 'approved', 'rejected', 'executing', 'completed', 'failed', 'rolled_back', name='taskstatus'), nullable=False, index=True),
        sa.Column('reviewer', sa.String(255), nullable=True),
        sa.Column('review_comments', sa.Text(), nullable=True),
        sa.Column('reviewed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('execution_log', sa.JSON(), nullable=True),
        sa.Column('test_results', sa.JSON(), nullable=True),
        sa.Column('rollback_info', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('metadata_json', sa.JSON(), nullable=True)
    )
    
    # Create indexes for common queries
    op.create_index('idx_status_created', 'self_healing_tasks', ['status', 'created_at'])
    op.create_index('idx_severity_status', 'self_healing_tasks', ['severity', 'status'])
    op.create_index('idx_error_hash_created', 'self_healing_tasks', ['error_hash', 'created_at'])


def downgrade():
    """Drop self_healing_tasks table."""
    op.drop_index('idx_error_hash_created', 'self_healing_tasks')
    op.drop_index('idx_severity_status', 'self_healing_tasks')
    op.drop_index('idx_status_created', 'self_healing_tasks')
    op.drop_table('self_healing_tasks')

