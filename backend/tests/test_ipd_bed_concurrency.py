from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

def test_admission_service_uses_locked_bed():
    source = (ROOT / "backend/app/services/admission.py").read_text(encoding="utf-8")
    assert "with_for_update" in source
    assert "already has an active admission" in source


def test_active_bed_database_guard_exists():
    source = (ROOT / "backend/alembic/versions/0019_ipd_active_bed_guard.py").read_text(encoding="utf-8")
    assert "uq_admission_active_bed" in source
    assert "admitted" in source and "active" in source
