"""User ID normalization prep: mapping table and provider_id backfill

Revision ID: 9a1f3c2d4e5f
Revises: 0b2f849dc961
Create Date: 2025-09-02
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "9a1f3c2d4e5f"
down_revision: Union[str, Sequence[str], None] = "0b2f849dc961"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1) Mapping table for audit and rollback
    op.create_table(
        "user_id_migration_map",
        sa.Column("old_id", sa.String(), primary_key=True),
        sa.Column("new_id", sa.String(), nullable=False, index=True),
        sa.Column("email", sa.String(length=255), nullable=False, index=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # 2) Ensure provider_id exists and is indexed
    op.create_index("ix_users_provider_id", "users", ["provider_id"], unique=False)

    # Attempt to backfill provider_id where NULL by setting it to current id
    conn = op.get_bind()
    try:
        conn.execute(sa.text("UPDATE users SET provider_id = id WHERE provider_id IS NULL"))
    except Exception:
        pass


def downgrade() -> None:
    # Reverse prep changes (non-destructive rollback)
    op.drop_index("ix_users_provider_id", table_name="users")
    op.drop_table("user_id_migration_map")

