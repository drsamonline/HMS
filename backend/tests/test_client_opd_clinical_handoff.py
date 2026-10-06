"""Regression checks for OPD-to-clinical client handoff wiring."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_opd_dispatches_clinical_handoff_event() -> None:
    source = (ROOT / "frontend/js/opd.js").read_text(encoding="utf-8")
    assert "hhms:open-patient-clinical" in source
    assert "CustomEvent" in source


def test_app_handles_clinical_handoff_event() -> None:
    source = (ROOT / "frontend/js/app.js").read_text(encoding="utf-8")
    assert '"hhms:open-patient-clinical"' in source
    assert 'renderRecordView("clinical"' in source
