"""Regression tests for designation master API wiring."""
from pathlib import Path

def test_designation_endpoint_exists() -> None:
    path = Path(__file__).parents[1] / "app" / "api" / "v1" / "endpoints" / "designations.py"
    assert path.exists()
    assert "/designations" in path.read_text(encoding="utf-8")

def test_designation_migration_exists() -> None:
    path = Path(__file__).parents[1] / "alembic" / "versions" / "0009_designation_master.py"
    text = path.read_text(encoding="utf-8")
    assert "0009_designation_master" in text
    assert "designations" in text
