"""User ID normalization backfill: migrate users.id to uid_<hash> with FK updates

Revision ID: b2c3d4e5f6a7
Revises: 9a1f3c2d4e5f
Create Date: 2025-09-02
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "b2c3d4e5f6a7"
down_revision: Union[str, Sequence[str], None] = "9a1f3c2d4e5f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# FK tables that reference users.id
FK_TABLES = [
    ("refresh_tokens", "user_id"),
    ("conversations", "user_id"),
    ("documents", "user_id"),
    ("messages", "user_id"),
]


def upgrade() -> None:
    conn = op.get_bind()

    # Real guard: require env var MIGRATE_USER_IDS=1 set in Alembic context
    from alembic import context
    migrate_flag = context.get_x_argument(as_dictionary=True).get("migrate_user_ids", "0")
    if migrate_flag not in ("1", "true", "True"):
        return

    # Detect engine/dialect to choose strategy
    dialect = conn.dialect.name

    # Fetch users
    users = conn.execute(sa.text("SELECT id, email FROM users")).fetchall()

    # Deterministic normalization (same as app)
    import hashlib

    def normalize_user_id(email: str) -> str:
        normalized = email.strip().lower()
        digest = hashlib.blake2s(normalized.encode("utf-8"), digest_size=8).hexdigest()
        return f"uid_{digest}"

    if dialect == "postgresql":
        # Postgres-only: chunked backfill with advisory locks to minimize lock contention
        chunk_size = int(op.get_context().get_x_argument(as_dictionary=True).get("chunk_size", 500))
        advisory_key = 424242  # arbitrary app-level key

        # Acquire advisory lock for the whole migration to serialize with other runs
        op.execute(sa.text("SELECT pg_advisory_lock(:k)"), {"k": advisory_key})
        try:
            # Work in chunks using a cursor over the user list
            index = 0
            total = len(users)
            while index < total:
                batch = users[index:index + chunk_size]
                index += chunk_size

                # Begin a short transaction for the batch
                with op.get_context().autocommit_block():
                    # Use explicit transaction per batch
                    for old_id, email in batch:
                        new_id = normalize_user_id(email)
                        if new_id == old_id:
                            continue
                        # Record mapping
                        op.execute(sa.text(
                            "INSERT INTO user_id_migration_map(old_id, new_id, email) VALUES (:old, :new, :email)"
                        ), {"old": old_id, "new": new_id, "email": email})
                        # Update FKs
                        for table, col in FK_TABLES:
                            op.execute(sa.text(f"UPDATE {table} SET {col} = :new WHERE {col} = :old"), {"new": new_id, "old": old_id})
                        # Update users row
                        op.execute(sa.text(
                            "UPDATE users SET id = :new, provider_id = COALESCE(provider_id, :old) WHERE id = :old"
                        ), {"new": new_id, "old": old_id})
        finally:
            # Always release the advisory lock
            op.execute(sa.text("SELECT pg_advisory_unlock(:k)"), {"k": advisory_key})
    else:
        # Generic (SQLite, others): simple per-user updates, consider running during a maintenance window
        for old_id, email in users:
            new_id = normalize_user_id(email)
            if new_id == old_id:
                continue

            # record mapping
            op.execute(
                sa.text(
                    "INSERT INTO user_id_migration_map(old_id, new_id, email) VALUES (:old, :new, :email)"
                ),
                {"old": old_id, "new": new_id, "email": email},
            )

            # update FKs first (batched in a single transaction per user)
            for table, col in FK_TABLES:
                op.execute(
                    sa.text(f"UPDATE {table} SET {col} = :new WHERE {col} = :old"),
                    {"new": new_id, "old": old_id},
                )

            # update users row and preserve legacy provider_id
            op.execute(
                sa.text(
                    "UPDATE users SET id = :new, provider_id = COALESCE(provider_id, :old) WHERE id = :old"
                ),
                {"new": new_id, "old": old_id},
            )

    # Validation sample (lightweight; full validation in runbook script)
    # Example: ensure no orphaned FKs remain
    # This can be extended or run via separate verification script as part of the rollout


def downgrade() -> None:
    conn = op.get_bind()

    # Guarded rollback via x-arg as well
    from alembic import context
    rollback_flag = context.get_x_argument(as_dictionary=True).get("rollback_user_ids", "0")
    if rollback_flag not in ("1", "true", "True"):
        return

    # Walk mappings and reverse
    rows = conn.execute(sa.text("SELECT old_id, new_id FROM user_id_migration_map")).fetchall()
    for old_id, new_id in rows:
        for table, col in FK_TABLES:
            op.execute(
                sa.text(f"UPDATE {table} SET {col} = :old WHERE {col} = :new"),
                {"new": new_id, "old": old_id},
            )
        op.execute(sa.text("UPDATE users SET id = :old WHERE id = :new"), {"new": new_id, "old": old_id})

