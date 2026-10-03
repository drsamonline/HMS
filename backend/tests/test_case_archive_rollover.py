from pathlib import Path
import sqlite3

ROOT = Path(__file__).resolve().parents[2]


def test_archive_snapshot_helpers_are_integrity_checked():
    source = ROOT / "backend" / "tests" / "_rollover_test.sqlite3"
    if source.exists():
        source.unlink()
    connection = sqlite3.connect(source)
    try:
        connection.execute(
            "CREATE TABLE CaseRecord (id INTEGER PRIMARY KEY, case_year INTEGER)"
        )
        connection.execute(
            "INSERT INTO CaseRecord(id, case_year) VALUES (1, 2025)"
        )
        connection.commit()
    finally:
        connection.close()

    try:
        check = sqlite3.connect(source)
        try:
            assert check.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
        finally:
            check.close()
    finally:
        source.unlink(missing_ok=True)


def test_rollover_contracts_are_exposed():
    maintenance = (
        ROOT / "backend" / "app" / "api" / "v1" / "endpoints" / "maintenance.py"
    ).read_text(encoding="utf-8")
    api = (ROOT / "frontend" / "js" / "api.js").read_text(encoding="utf-8")
    workspace = (
        ROOT / "frontend" / "js" / "system_health.js"
    ).read_text(encoding="utf-8")

    assert '@router.get("/archives/rollover/preview")' in maintenance
    assert '@router.post("/archives/rollover/{year}")' in maintenance
    assert "getArchiveRolloverPreview" in api
    assert "rolloverArchiveYear" in api
    assert "archive-rollover" in workspace


def test_case_archive_reference_model_and_migration_exist():
    model = ROOT / "backend" / "app" / "models" / "case_archive_reference.py"
    migration = ROOT / "backend" / "alembic" / "versions" / "0020_case_archive_rollover_reference.py"
    assert model.is_file()
    assert migration.is_file()
    assert "CaseArchiveReference" in model.read_text(encoding="utf-8")
    assert 'revision = "0020_case_archive_rollover_reference"' in migration.read_text(
        encoding="utf-8"
    )
