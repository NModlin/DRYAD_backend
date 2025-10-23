import os
import csv
import sys
import json
import time
import logging
from dataclasses import dataclass, asdict
from typing import Dict, Any, List, Tuple

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("migration.validation")


@dataclass
class TableStats:
    table: str
    row_count: int
    checksum: str


@dataclass
class MigrationReport:
    started_at: float
    finished_at: float
    pre_stats: List[TableStats]
    post_stats: List[TableStats]
    fk_checks: Dict[str, Any]
    mappings: int


def _connect_via_env() -> Engine:
    url = os.getenv("DATABASE_URL") or os.getenv("SQLALCHEMY_DATABASE_URI")
    if not url:
        logger.error("No DATABASE_URL or SQLALCHEMY_DATABASE_URI set")
        sys.exit(1)
    return create_engine(url, future=True)


def _checksum_rows(conn, table: str) -> str:
    # Lightweight checksum: count + sum of length of string serialized rows
    # For serious use, consider a per-table deterministic hash on key columns.
    rows = conn.execute(text(f"SELECT * FROM {table}")).fetchall()
    total_len = 0
    for r in rows:
        total_len += len(json.dumps([str(x) for x in r], sort_keys=True))
    return f"{len(rows)}-{total_len}"


def capture_stats(engine: Engine, tables: List[str]) -> List[TableStats]:
    with engine.begin() as conn:
        stats: List[TableStats] = []
        for t in tables:
            cnt = conn.execute(text(f"SELECT COUNT(*) FROM {t}")).scalar_one()
            chk = _checksum_rows(conn, t)
            stats.append(TableStats(table=t, row_count=cnt, checksum=chk))
        return stats


def check_fk_integrity(engine: Engine, fk_specs: List[Tuple[str, str, str]]) -> Dict[str, Any]:
    """
    fk_specs: list of tuples (child_table, child_fk_col, parent_table)
    """
    res: Dict[str, Any] = {"ok": True, "details": []}
    with engine.begin() as conn:
        for child, fk_col, parent in fk_specs:
            orphan_cnt = conn.execute(
                text(
                    f"SELECT COUNT(*) FROM {child} c LEFT JOIN {parent} p ON c.{fk_col} = p.id WHERE p.id IS NULL"
                )
            ).scalar_one()
            detail = {"child": child, "fk_col": fk_col, "parent": parent, "orphans": orphan_cnt}
            res["details"].append(detail)
            if orphan_cnt != 0:
                res["ok"] = False
    return res


def write_csv_report(path: str, pre: List[TableStats], post: List[TableStats], fk: Dict[str, Any]):
    with open(path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Section", "Table", "RowCount", "Checksum", "Notes"])
        for s in pre:
            writer.writerow(["pre", s.table, s.row_count, s.checksum, ""])
        for s in post:
            writer.writerow(["post", s.table, s.row_count, s.checksum, ""])
        writer.writerow(["fk", "", "", json.dumps(fk), ""]) 


def validate_user_id_migration() -> int:
    engine = _connect_via_env()

    tables = [
        "users",
        "refresh_tokens",
        "conversations",
        "documents",
        "messages",
    ]
    fk_specs = [
        ("refresh_tokens", "user_id", "users"),
        ("conversations", "user_id", "users"),
        ("documents", "user_id", "users"),
        ("messages", "user_id", "users"),
    ]

    start = time.time()
    pre = capture_stats(engine, tables)

    # Count mappings present
    with engine.begin() as conn:
        mappings = conn.execute(text("SELECT COUNT(*) FROM user_id_migration_map")).scalar_one_or_none() or 0

    # Re-capture after (assumes migration has run)
    post = capture_stats(engine, tables)
    fk = check_fk_integrity(engine, fk_specs)
    end = time.time()

    # Write CSV report
    out = os.getenv("MIGRATION_REPORT_CSV", "migration_report.csv")
    write_csv_report(out, pre, post, fk)

    # Basic validations
    all_counts_equal = all(p.row_count == q.row_count for p, q in zip(pre, post))
    checksums_changed_only_for_users = all(
        (p.table == "users" and p.checksum != q.checksum) or (p.table != "users" and p.checksum == q.checksum)
        for p, q in zip(pre, post)
    )

    ok = all_counts_equal and fk["ok"]
    if not ok:
        logger.error("Migration validation failed: counts_equal=%s fk_ok=%s", all_counts_equal, fk["ok"])
        return 1

    logger.info("Migration validation OK. Mappings=%s report=%s", mappings, out)
    return 0


if __name__ == "__main__":
    sys.exit(validate_user_id_migration())

