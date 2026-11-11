"""Gate tests for build-plan batch B03: foreign keys are enforced.

SQLite defaults ``foreign_keys`` to OFF, so before this batch every
``ForeignKey`` in the models was documentation. The pragma is per connection,
which is why the test exercises the same helper the connect handler calls
rather than asserting on the string in the source.
"""

from __future__ import annotations

import sqlite3

import pytest

from app.db.session import apply_sqlite_pragmas


@pytest.fixture()
def connection(tmp_path):
    path = tmp_path / "fk.sqlite3"
    conn = sqlite3.connect(path)
    cursor = conn.cursor()
    apply_sqlite_pragmas(cursor)
    yield conn, cursor
    conn.close()


def test_pragma_is_on(connection) -> None:
    _conn, cursor = connection
    assert cursor.execute("PRAGMA foreign_keys").fetchone()[0] == 1


def test_other_pragmas_still_applied(connection) -> None:
    """The batch must not drop what the connect handler already did."""
    _conn, cursor = connection
    assert cursor.execute("PRAGMA journal_mode").fetchone()[0].lower() == "wal"
    assert cursor.execute("PRAGMA busy_timeout").fetchone()[0] == 5000


def test_orphan_child_is_rejected(connection) -> None:
    conn, cursor = connection
    cursor.execute("CREATE TABLE parent (id INTEGER PRIMARY KEY)")
    cursor.execute(
        "CREATE TABLE child (id INTEGER PRIMARY KEY, parent_id INTEGER NOT NULL "
        "REFERENCES parent(id))"
    )
    cursor.execute("INSERT INTO parent (id) VALUES (1)")
    cursor.execute("INSERT INTO child (id, parent_id) VALUES (1, 1)")

    with pytest.raises(sqlite3.IntegrityError):
        cursor.execute("INSERT INTO child (id, parent_id) VALUES (2, 999)")


def test_deleting_a_referenced_parent_is_rejected(connection) -> None:
    """The failure this batch exists to prevent: a parent vanishing silently."""
    conn, cursor = connection
    cursor.execute("CREATE TABLE parent (id INTEGER PRIMARY KEY)")
    cursor.execute(
        "CREATE TABLE child (id INTEGER PRIMARY KEY, parent_id INTEGER NOT NULL "
        "REFERENCES parent(id))"
    )
    cursor.execute("INSERT INTO parent (id) VALUES (1)")
    cursor.execute("INSERT INTO child (id, parent_id) VALUES (1, 1)")

    with pytest.raises(sqlite3.IntegrityError):
        cursor.execute("DELETE FROM parent WHERE id = 1")


def test_orphan_sweep_script_imports() -> None:
    """The sweep must be runnable before enforcement is switched on."""
    from pathlib import Path
    import importlib.util

    script = Path(__file__).resolve().parents[2] / "scripts" / "orphan_sweep.py"
    spec = importlib.util.spec_from_file_location("orphan_sweep", script)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    assert callable(module.sweep)
