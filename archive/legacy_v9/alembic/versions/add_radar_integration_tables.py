"""Add RADAR integration tables

Revision ID: radar_integration_001
Revises: 
Create Date: 2025-10-03

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite

# revision identifiers, used by Alembic.
revision = 'radar_integration_001'
down_revision = None  # Update this to your latest migration
branch_labels = None
depends_on = None


def upgrade():
    """Create RADAR integration tables."""
    
    # Create radar_feedback table
    op.create_table(
        'radar_feedback',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('message_id', sa.String(), nullable=False),
        sa.Column('conversation_id', sa.String(), nullable=True),
        sa.Column('user_id', sa.String(), nullable=True),
        sa.Column('rating', sa.String(length=20), nullable=False),
        sa.Column('comment', sa.Text(), nullable=True),
        sa.Column('radar_user_id', sa.String(), nullable=True),
        sa.Column('radar_username', sa.String(), nullable=True),
        sa.Column('radar_context', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.ForeignKeyConstraint(['conversation_id'], ['conversations.id'], ),
        sa.ForeignKeyConstraint(['message_id'], ['messages.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for radar_feedback
    op.create_index('idx_radar_feedback_created', 'radar_feedback', ['created_at'], unique=False)
    op.create_index('idx_radar_feedback_rating', 'radar_feedback', ['rating'], unique=False)
    op.create_index('idx_radar_feedback_user', 'radar_feedback', ['radar_user_id'], unique=False)
    op.create_index(op.f('ix_radar_feedback_conversation_id'), 'radar_feedback', ['conversation_id'], unique=False)
    op.create_index(op.f('ix_radar_feedback_message_id'), 'radar_feedback', ['message_id'], unique=False)
    op.create_index(op.f('ix_radar_feedback_user_id'), 'radar_feedback', ['user_id'], unique=False)
    
    # Create radar_sync_status table
    op.create_table(
        'radar_sync_status',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('entity_type', sa.String(length=50), nullable=False),
        sa.Column('entity_id', sa.String(), nullable=False),
        sa.Column('sync_status', sa.String(length=20), nullable=False),
        sa.Column('last_sync_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('sync_attempts', sa.Float(), nullable=True),
        sa.Column('last_error', sa.Text(), nullable=True),
        sa.Column('error_count', sa.Float(), nullable=True),
        sa.Column('radar_metadata', sa.JSON(), nullable=True),
        sa.Column('dryad_metadata', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for radar_sync_status
    op.create_index('idx_radar_sync_entity', 'radar_sync_status', ['entity_type', 'entity_id'], unique=False)
    op.create_index('idx_radar_sync_status', 'radar_sync_status', ['sync_status'], unique=False)
    op.create_index('idx_radar_sync_updated', 'radar_sync_status', ['updated_at'], unique=False)
    op.create_index(op.f('ix_radar_sync_status_entity_id'), 'radar_sync_status', ['entity_id'], unique=False)
    op.create_index(op.f('ix_radar_sync_status_entity_type'), 'radar_sync_status', ['entity_type'], unique=False)
    
    # Create radar_context_logs table
    op.create_table(
        'radar_context_logs',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('conversation_id', sa.String(), nullable=True),
        sa.Column('message_id', sa.String(), nullable=True),
        sa.Column('radar_user_id', sa.String(), nullable=True),
        sa.Column('radar_username', sa.String(), nullable=True),
        sa.Column('department', sa.String(), nullable=True),
        sa.Column('user_context', sa.JSON(), nullable=True),
        sa.Column('session_context', sa.JSON(), nullable=True),
        sa.Column('environment_context', sa.JSON(), nullable=True),
        sa.Column('recent_actions', sa.JSON(), nullable=True),
        sa.Column('request_path', sa.String(), nullable=True),
        sa.Column('request_method', sa.String(), nullable=True),
        sa.Column('response_time_ms', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.ForeignKeyConstraint(['conversation_id'], ['conversations.id'], ),
        sa.ForeignKeyConstraint(['message_id'], ['messages.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for radar_context_logs
    op.create_index('idx_radar_context_created', 'radar_context_logs', ['created_at'], unique=False)
    op.create_index('idx_radar_context_dept', 'radar_context_logs', ['department'], unique=False)
    op.create_index('idx_radar_context_user', 'radar_context_logs', ['radar_user_id'], unique=False)
    op.create_index(op.f('ix_radar_context_logs_conversation_id'), 'radar_context_logs', ['conversation_id'], unique=False)
    op.create_index(op.f('ix_radar_context_logs_message_id'), 'radar_context_logs', ['message_id'], unique=False)
    op.create_index(op.f('ix_radar_context_logs_radar_user_id'), 'radar_context_logs', ['radar_user_id'], unique=False)


def downgrade():
    """Drop RADAR integration tables."""
    
    # Drop radar_context_logs
    op.drop_index(op.f('ix_radar_context_logs_radar_user_id'), table_name='radar_context_logs')
    op.drop_index(op.f('ix_radar_context_logs_message_id'), table_name='radar_context_logs')
    op.drop_index(op.f('ix_radar_context_logs_conversation_id'), table_name='radar_context_logs')
    op.drop_index('idx_radar_context_user', table_name='radar_context_logs')
    op.drop_index('idx_radar_context_dept', table_name='radar_context_logs')
    op.drop_index('idx_radar_context_created', table_name='radar_context_logs')
    op.drop_table('radar_context_logs')
    
    # Drop radar_sync_status
    op.drop_index(op.f('ix_radar_sync_status_entity_type'), table_name='radar_sync_status')
    op.drop_index(op.f('ix_radar_sync_status_entity_id'), table_name='radar_sync_status')
    op.drop_index('idx_radar_sync_updated', table_name='radar_sync_status')
    op.drop_index('idx_radar_sync_status', table_name='radar_sync_status')
    op.drop_index('idx_radar_sync_entity', table_name='radar_sync_status')
    op.drop_table('radar_sync_status')
    
    # Drop radar_feedback
    op.drop_index(op.f('ix_radar_feedback_user_id'), table_name='radar_feedback')
    op.drop_index(op.f('ix_radar_feedback_message_id'), table_name='radar_feedback')
    op.drop_index(op.f('ix_radar_feedback_conversation_id'), table_name='radar_feedback')
    op.drop_index('idx_radar_feedback_user', table_name='radar_feedback')
    op.drop_index('idx_radar_feedback_rating', table_name='radar_feedback')
    op.drop_index('idx_radar_feedback_created', table_name='radar_feedback')
    op.drop_table('radar_feedback')

