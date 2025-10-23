import os
import sys
import time
import logging
from typing import Dict, Tuple, List

from sqlalchemy import create_engine, text

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("pg.migration.monitor")


def _connect() -> tuple:
    url = os.getenv("DATABASE_URL") or os.getenv("SQLALCHEMY_DATABASE_URI")
    if not url:
        logger.error("Set DATABASE_URL/SQLALCHEMY_DATABASE_URI to a Postgres URL")
        sys.exit(1)
    engine = create_engine(url, future=True)
    return engine, engine.connect()


def _is_postgres(conn) -> bool:
    try:
        ver = conn.execute(text("select version()"))
        return True
    except Exception:
        return False


def _count_table(conn, table: str) -> int:
    return conn.execute(text(f"select count(*) from {table}")).scalar_one()


def _fk_orphans(conn, child: str, fk_col: str, parent: str) -> int:
    sql = f"""
    select count(*)
    from {child} c
    left join {parent} p on c.{fk_col} = p.id
    where p.id is null
    """
    return conn.execute(text(sql)).scalar_one()


def _mappings_progress(conn) -> Tuple[int, int]:
    total = conn.execute(text("select count(*) from users")).scalar_one()
    done = conn.execute(text("select count(*) from user_id_migration_map")).scalar_one_or_none() or 0
    return done, total


def monitor(interval_sec: int = 3) -> int:
    engine, conn = _connect()
    if not _is_postgres(conn):
        logger.error("This monitor is Postgres-only.")
        return 1

    logger.info("Starting Postgres migration monitor. Ctrl+C to stop.")
    try:
        while True:
            try:
                done, total = _mappings_progress(conn)
                users = _count_table(conn, "users")
                rt_orphans = _fk_orphans(conn, "refresh_tokens", "user_id", "users")
                conv_orphans = _fk_orphans(conn, "conversations", "user_id", "users")
                doc_orphans = _fk_orphans(conn, "documents", "user_id", "users")
                msg_orphans = _fk_orphans(conn, "messages", "user_id", "users")

                logger.info(
                    "progress: %s/%s mapped | users=%s | orphans rt=%s conv=%s doc=%s msg=%s",
                    done, total, users, rt_orphans, conv_orphans, doc_orphans, msg_orphans
                )
            except KeyboardInterrupt:
                raise
            except Exception as e:
                logger.warning("monitor iteration failed: %s", e)
            time.sleep(interval_sec)
    finally:
        conn.close()
        engine.dispose()


if __name__ == "__main__":
    sys.exit(monitor())

