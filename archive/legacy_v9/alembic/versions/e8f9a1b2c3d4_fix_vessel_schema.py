"""fix vessel schema

Revision ID: e8f9a1b2c3d4
Revises: d76c7d06a414
Create Date: 2025-10-06 21:30:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'e8f9a1b2c3d4'
down_revision = 'd76c7d06a414'
branch_labels = None
depends_on = None


def upgrade():
    # Check which columns exist
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    # Get existing columns
    existing_columns = {col['name'] for col in inspector.get_columns('dryad_vessels')}

    # Add missing columns to dryad_vessels table
    with op.batch_alter_table('dryad_vessels', schema=None) as batch_op:
        # Add compressed_path column if it doesn't exist
        if 'compressed_path' not in existing_columns:
            batch_op.add_column(sa.Column('compressed_path', sa.String(length=500), nullable=True))

        # Add generated_at column if it doesn't exist
        if 'generated_at' not in existing_columns:
            batch_op.add_column(sa.Column('generated_at', sa.DateTime(timezone=True), nullable=True))

        # Add last_updated column if it doesn't exist
        if 'last_updated' not in existing_columns:
            batch_op.add_column(sa.Column('last_updated', sa.DateTime(timezone=True), nullable=True))

        # Add last_accessed column if it doesn't exist
        if 'last_accessed' not in existing_columns:
            batch_op.add_column(sa.Column('last_accessed', sa.DateTime(timezone=True), nullable=True))

    # Copy data from old columns to new columns (only if columns were added)
    if 'generated_at' not in existing_columns or 'last_updated' not in existing_columns:
        op.execute("""
            UPDATE dryad_vessels
            SET generated_at = COALESCE(generated_at, created_at),
                last_updated = COALESCE(last_updated, updated_at),
                last_accessed = COALESCE(last_accessed, updated_at)
            WHERE generated_at IS NULL OR last_updated IS NULL OR last_accessed IS NULL
        """)


def downgrade():
    # Remove added columns
    with op.batch_alter_table('dryad_vessels', schema=None) as batch_op:
        batch_op.drop_column('last_accessed')
        batch_op.drop_column('last_updated')
        batch_op.drop_column('generated_at')
        batch_op.drop_column('compressed_path')

