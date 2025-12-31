import os
import sys
import logging
import subprocess

from scripts.migration_validation import validate_user_id_migration

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("run.user_id_migration")


def _run(cmd: list[str]) -> int:
    logger.info("Running: %s", " ".join(cmd))
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        logger.error("Command failed [%s]: %s\n%s", proc.returncode, " ".join(cmd), proc.stderr)
    else:
        logger.info(proc.stdout)
    return proc.returncode


def main() -> int:
    # Pre-flight checks
    if not (os.getenv("DATABASE_URL") or os.getenv("SQLALCHEMY_DATABASE_URI")):
        logger.error("Set DATABASE_URL or SQLALCHEMY_DATABASE_URI for migration")
        return 1

    logger.info("Pre-validation starting. Ensure you have a backup/snapshot before proceeding.")
    rc = validate_user_id_migration()
    if rc != 0:
        logger.error("Pre-validation failed. Aborting migration.")
        return rc

    # Run prep migration (creates mapping table, indexes)
    if _run(["alembic", "upgrade", "9a1f3c2d4e5f"]) != 0:
        return 1

    # Run backfill (guarded with x-arg)
    if _run(["alembic", "upgrade", "b2c3d4e5f6a7", "-x", "migrate_user_ids=1"]) != 0:
        logger.error("Backfill failed. Attempting rollback using Alembic downgrade.")
        _run(["alembic", "downgrade", "9a1f3c2d4e5f", "-x", "rollback_user_ids=1"])  # best-effort
        return 1

    # Post-validation
    rc = validate_user_id_migration()
    if rc != 0:
        logger.error("Post-validation failed. Attempting rollback.")
        _run(["alembic", "downgrade", "9a1f3c2d4e5f", "-x", "rollback_user_ids=1"])  # best-effort
        return rc

    logger.info("User ID migration completed successfully.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

