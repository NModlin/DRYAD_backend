"""Create memory guild tables

Revision ID: 2025_01_10_memory_guild
Revises: 2025_01_10_create_tool_registry_tables
Create Date: 2025-01-10 14:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '2025_01_10_memory_guild'
down_revision: Union[str, None] = '2025_01_10_tool_registry'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create Memory Guild tables."""

    # Detect database type for conditional type handling
    bind = op.get_bind()
    is_postgresql = bind.dialect.name == 'postgresql'

    # Set types based on database
    if is_postgresql:
        uuid_type = postgresql.UUID(as_uuid=True)
        json_type = postgresql.JSONB(astext_type=sa.Text())
        timestamp_default = sa.text('NOW()')
    else:
        # SQLite fallback
        uuid_type = sa.String(36)
        json_type = sa.JSON
        timestamp_default = sa.text("(datetime('now'))")

    # Create memory_records table
    op.create_table(
        'memory_records',
        sa.Column('memory_id', uuid_type, primary_key=True),
        sa.Column('agent_id', sa.String(255), nullable=False),
        sa.Column('tenant_id', sa.String(255), nullable=False),
        sa.Column('source_type', sa.String(50), nullable=False),
        sa.Column('content_text', sa.Text(), nullable=False),
        sa.Column('content_hash', sa.String(64), nullable=False),
        sa.Column('metadata', json_type, nullable=False, server_default='{}'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=timestamp_default),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=timestamp_default),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "source_type IN ('conversation', 'tool_output', 'document', 'observation', 'external')",
            name='check_source_type'
        ),
        sa.UniqueConstraint('agent_id', 'tenant_id', 'content_hash', name='unique_content_hash'),
    )

    # Create indexes for memory_records
    op.create_index('idx_memory_agent', 'memory_records', ['agent_id'])
    op.create_index('idx_memory_tenant', 'memory_records', ['tenant_id'])
    op.create_index('idx_memory_source', 'memory_records', ['source_type'])
    op.create_index('idx_memory_created', 'memory_records', ['created_at'])
    op.create_index('idx_memory_hash', 'memory_records', ['content_hash'])

    # Create partial index for active records (PostgreSQL only)
    if is_postgresql:
        op.create_index(
            'idx_memory_active',
            'memory_records',
            ['is_deleted'],
            postgresql_where=sa.text('is_deleted = false')
        )
    else:
        op.create_index('idx_memory_active', 'memory_records', ['is_deleted'])

    # Create memory_embeddings table
    op.create_table(
        'memory_embeddings',
        sa.Column('embedding_id', uuid_type, primary_key=True),
        sa.Column('memory_id', uuid_type, nullable=False),
        sa.Column('vector_id', sa.String(255), nullable=False),
        sa.Column('embedding_model', sa.String(100), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=timestamp_default),
        sa.ForeignKeyConstraint(['memory_id'], ['memory_records.memory_id'], ondelete='CASCADE'),
        sa.UniqueConstraint('memory_id', 'embedding_model', name='unique_memory_embedding'),
    )

    # Create indexes for memory_embeddings
    op.create_index('idx_embeddings_memory', 'memory_embeddings', ['memory_id'])
    op.create_index('idx_embeddings_vector', 'memory_embeddings', ['vector_id'])

    # Create memory_relationships table
    op.create_table(
        'memory_relationships',
        sa.Column('relationship_id', uuid_type, primary_key=True),
        sa.Column('source_memory_id', uuid_type, nullable=False),
        sa.Column('target_memory_id', uuid_type, nullable=False),
        sa.Column('relationship_type', sa.String(50), nullable=False),
        sa.Column('confidence_score', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=timestamp_default),
        sa.ForeignKeyConstraint(['source_memory_id'], ['memory_records.memory_id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['target_memory_id'], ['memory_records.memory_id'], ondelete='CASCADE'),
        sa.CheckConstraint(
            "relationship_type IN ('references', 'contradicts', 'supports', 'follows', 'related')",
            name='check_relationship_type'
        ),
        sa.CheckConstraint(
            'confidence_score >= 0 AND confidence_score <= 1',
            name='check_confidence_score'
        ),
        sa.CheckConstraint(
            'source_memory_id != target_memory_id',
            name='no_self_reference'
        ),
        sa.UniqueConstraint('source_memory_id', 'target_memory_id', 'relationship_type', name='unique_relationship'),
    )

    # Create indexes for memory_relationships
    op.create_index('idx_relationships_source', 'memory_relationships', ['source_memory_id'])
    op.create_index('idx_relationships_target', 'memory_relationships', ['target_memory_id'])
    op.create_index('idx_relationships_type', 'memory_relationships', ['relationship_type'])

    # Create data_sources table
    op.create_table(
        'data_sources',
        sa.Column('source_id', uuid_type, primary_key=True),
        sa.Column('source_name', sa.String(255), nullable=False, unique=True),
        sa.Column('source_type', sa.String(50), nullable=False),
        sa.Column('source_uri', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=timestamp_default),
        sa.Column('last_ingestion_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('metadata', json_type, nullable=False, server_default='{}'),
        sa.CheckConstraint(
            "source_type IN ('api', 'database', 'file_system', 'webhook', 'manual')",
            name='check_source_type'
        ),
    )

    # Create indexes for data_sources
    op.create_index('idx_sources_active', 'data_sources', ['is_active'])
    op.create_index('idx_sources_type', 'data_sources', ['source_type'])

    # Create memory_access_policies table
    op.create_table(
        'memory_access_policies',
        sa.Column('policy_id', uuid_type, primary_key=True),
        sa.Column('policy_name', sa.String(255), nullable=False, unique=True),
        sa.Column('policy_rules', json_type, nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=timestamp_default),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=timestamp_default),
    )

    # Create indexes for memory_access_policies
    op.create_index('idx_policies_active', 'memory_access_policies', ['is_active'])


def downgrade() -> None:
    """Drop Memory Guild tables."""
    
    # Drop tables in reverse order (respecting foreign keys)
    op.drop_table('memory_access_policies')
    op.drop_table('data_sources')
    op.drop_table('memory_relationships')
    op.drop_table('memory_embeddings')
    op.drop_table('memory_records')

