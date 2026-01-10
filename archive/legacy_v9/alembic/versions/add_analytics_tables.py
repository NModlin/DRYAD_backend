"""Add analytics tables

Revision ID: add_analytics_tables
Revises: 
Create Date: 2024-01-01 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite

# revision identifiers, used by Alembic.
revision = 'add_analytics_tables'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Create document_analytics table
    op.create_table('document_analytics',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('document_id', sa.String(), nullable=False),
        sa.Column('view_count', sa.Integer(), nullable=True, default=0),
        sa.Column('search_count', sa.Integer(), nullable=True, default=0),
        sa.Column('download_count', sa.Integer(), nullable=True, default=0),
        sa.Column('share_count', sa.Integer(), nullable=True, default=0),
        sa.Column('avg_time_spent', sa.Float(), nullable=True, default=0.0),
        sa.Column('bounce_rate', sa.Float(), nullable=True, default=0.0),
        sa.Column('avg_search_rank', sa.Float(), nullable=True, default=0.0),
        sa.Column('click_through_rate', sa.Float(), nullable=True, default=0.0),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True),
        sa.ForeignKeyConstraint(['document_id'], ['documents.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create search_analytics table
    op.create_table('search_analytics',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('query', sa.String(length=1000), nullable=False),
        sa.Column('query_hash', sa.String(length=64), nullable=False),
        sa.Column('search_type', sa.String(length=50), nullable=True, default='semantic'),
        sa.Column('results_count', sa.Integer(), nullable=True, default=0),
        sa.Column('results_returned', sa.Integer(), nullable=True, default=0),
        sa.Column('execution_time_ms', sa.Float(), nullable=True, default=0.0),
        sa.Column('clicked_results', sa.JSON(), nullable=True),
        sa.Column('user_session', sa.String(length=100), nullable=True),
        sa.Column('filters_applied', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create index on query_hash for search_analytics
    op.create_index('ix_search_analytics_query_hash', 'search_analytics', ['query_hash'])
    
    # Create user_engagement table
    op.create_table('user_engagement',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('user_session', sa.String(length=100), nullable=False),
        sa.Column('user_agent', sa.String(length=500), nullable=True),
        sa.Column('action_type', sa.String(length=50), nullable=False),
        sa.Column('resource_type', sa.String(length=50), nullable=False),
        sa.Column('resource_id', sa.String(), nullable=True),
        sa.Column('duration_seconds', sa.Float(), nullable=True),
        sa.Column('metadata', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create index on user_session for user_engagement
    op.create_index('ix_user_engagement_user_session', 'user_engagement', ['user_session'])


def downgrade():
    # Drop indexes
    op.drop_index('ix_user_engagement_user_session', table_name='user_engagement')
    op.drop_index('ix_search_analytics_query_hash', table_name='search_analytics')
    
    # Drop tables
    op.drop_table('user_engagement')
    op.drop_table('search_analytics')
    op.drop_table('document_analytics')
