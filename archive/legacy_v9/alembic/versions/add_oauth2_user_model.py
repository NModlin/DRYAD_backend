"""Add OAuth2 User model and user ownership to documents and conversations

Revision ID: add_oauth2_user_model
Revises: 
Create Date: 2025-01-27 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite

# revision identifiers, used by Alembic.
revision = 'add_oauth2_user_model'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create users table
    op.create_table('users',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('picture', sa.String(length=500), nullable=True),
        sa.Column('email_verified', sa.Boolean(), nullable=True),
        sa.Column('roles', sa.JSON(), nullable=True),
        sa.Column('permissions', sa.JSON(), nullable=True),
        sa.Column('provider', sa.String(length=50), nullable=True),
        sa.Column('provider_id', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True),
        sa.Column('last_login', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('is_verified', sa.Boolean(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    
    # Add user_id column to conversations table (if it exists)
    try:
        op.add_column('conversations', sa.Column('user_id', sa.String(), nullable=True))
        op.create_index(op.f('ix_conversations_user_id'), 'conversations', ['user_id'], unique=False)
        op.create_foreign_key(None, 'conversations', 'users', ['user_id'], ['id'])
    except Exception:
        # Table might not exist yet, create it
        op.create_table('conversations',
            sa.Column('id', sa.String(), nullable=False),
            sa.Column('user_id', sa.String(), nullable=False),
            sa.Column('title', sa.String(length=255), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True),
            sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True),
            sa.Column('is_active', sa.Boolean(), nullable=True),
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_conversations_user_id'), 'conversations', ['user_id'], unique=False)
    
    # Add user_id column to documents table (if it exists)
    try:
        op.add_column('documents', sa.Column('user_id', sa.String(), nullable=True))
        op.create_index(op.f('ix_documents_user_id'), 'documents', ['user_id'], unique=False)
        op.create_foreign_key(None, 'documents', 'users', ['user_id'], ['id'])
    except Exception:
        # Table might not exist yet, create it
        op.create_table('documents',
            sa.Column('id', sa.String(), nullable=False),
            sa.Column('user_id', sa.String(), nullable=False),
            sa.Column('title', sa.String(length=500), nullable=False),
            sa.Column('content', sa.Text(), nullable=False),
            sa.Column('content_type', sa.String(length=100), nullable=True),
            sa.Column('file_path', sa.String(length=1000), nullable=True),
            sa.Column('file_size', sa.Integer(), nullable=True),
            sa.Column('vector_id', sa.String(), nullable=True),
            sa.Column('embedding_model', sa.String(length=200), nullable=True),
            sa.Column('doc_metadata', sa.JSON(), nullable=True),
            sa.Column('tags', sa.JSON(), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True),
            sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True),
            sa.Column('is_active', sa.Boolean(), nullable=True),
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_documents_user_id'), 'documents', ['user_id'], unique=False)


def downgrade() -> None:
    # Remove foreign key constraints and indexes
    try:
        op.drop_constraint(None, 'documents', type_='foreignkey')
        op.drop_index(op.f('ix_documents_user_id'), table_name='documents')
        op.drop_column('documents', 'user_id')
    except Exception:
        pass
    
    try:
        op.drop_constraint(None, 'conversations', type_='foreignkey')
        op.drop_index(op.f('ix_conversations_user_id'), table_name='conversations')
        op.drop_column('conversations', 'user_id')
    except Exception:
        pass
    
    # Drop users table
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_table('users')
