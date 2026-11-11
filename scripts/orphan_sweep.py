#!/usr/bin/env python3
"""Report every child row whose declared parent no longer exists.

Run this **before** enabling ``PRAGMA foreign_keys=ON`` on an existing
installation: a hospital database that has been running without the pragma can
already contain orphans, and turning enforcement on will start rejecting writes
that used to succeed.

The sweep reads the SQLAlchemy metadata rather than a hardcoded list, so a new
model is covered the day it is declared.

Usage
-----
    python scripts/orphan_sweep.py data/hhms.sqlite3
    python scripts/orphan_sweep.py data/hhms.sqlite3 --fail-on-orphans

Exit codes
----------
0   no orphans found (or orphans found without ``--fail-on-orphans``)
1   orphans found and ``--fail-on-orphans`` was requested
2   the database file does not exist

Project : Hospital Homoeopathic Management System (HHMS)
Author  : Dr. Sohil Momin
"""

from __future__ import annotations

import argparse
import sqlite3
import sys
from pathlib import Path


def _models():
    """Import every ORM model so ``Base.metadata`` is complete."""

    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
    from app.db.base import Base  # noqa: WPS433 - deliberate late import

    import app.models  # noqa: F401,WPS433 - registers every mapped class

    return Base.metadata


def sweep(database_path: Path) -> list[tuple[str, str, int]]:
    """Return ``(table, column, orphan_count)`` for every broken reference."""

    metadata = _models()
    connection = sqlite3.connect(f"file:{database_path}?mode=ro", uri=True)
    findings: list[tuple[str, str, int]] = []
    try:
        for table in metadata.sorted_tables:
            for fk in table.foreign_keys:
                parent = fk.column.table
                sql = (
                    f'SELECT COUNT(*) FROM "{table.name}" AS child '
                    f'WHERE child."{fk.parent.name}" IS NOT NULL '
                    f'AND NOT EXISTS ('
                    f'SELECT 1 FROM "{parent.name}" AS parent '
                    f'WHERE parent."{fk.column.name}" = child."{fk.parent.name}")'
                )
                try:
                    count = connection.execute(sql).fetchone()[0]
                except sqlite3.Error as exc:  # missing table on an older schema
                    print(f"  skipped {table.name}.{fk.parent.name}: {exc}")
                    continue
                if count:
                    findings.append((table.name, fk.parent.name, count))
    finally:
        connection.close()
    return findings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("database", type=Path, help="path to the SQLite file")
    parser.add_argument(
        "--fail-on-orphans",
        action="store_true",
        help="exit 1 when any orphan is found (use this in CI)",
    )
    args = parser.parse_args(argv)

    if not args.database.is_file():
        print(f"no such database: {args.database}", file=sys.stderr)
        return 2

    findings = sweep(args.database)
    if not findings:
        print("clean: no orphaned references")
        return 0

    print(f"{len(findings)} broken reference(s):")
    for table, column, count in findings:
        print(f"  {table}.{column}: {count} row(s) point at a missing parent")
    return 1 if args.fail_on_orphans else 0


if __name__ == "__main__":
    raise SystemExit(main())
