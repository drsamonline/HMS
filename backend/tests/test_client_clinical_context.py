"""Regression contract tests for shared client clinical context."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_clinical_context_helpers_exist() -> None:
    api = (ROOT / "frontend" / "js" / "api.js").read_text(encoding="utf-8")
    clinical = (ROOT / "frontend" / "js" / "clinical.js").read_text(encoding="utf-8")
    investigations = (ROOT / "frontend" / "js" / "investigations.js").read_text(encoding="utf-8")
    billing = (ROOT / "frontend" / "js" / "billing.js").read_text(encoding="utf-8")
    assert "saveClinicalContext" in api
    assert "loadClinicalContext" in api
    assert "saveClinicalContext" in clinical
    assert "visit_id" in investigations
    assert "admission_id" in investigations
    assert "loadClinicalContext" in billing
    assert "visit_id" in billing
