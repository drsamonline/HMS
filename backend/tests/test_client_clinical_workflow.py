"""Regression checks for client clinical workflow integration contracts."""
from pathlib import Path


def test_client_clinical_workspace_uses_visit_context() -> None:
    text = Path("frontend/js/clinical.js").read_text(encoding="utf-8")
    assert "createVisit" in text
    assert "visit_id" in text
    assert "getCurrentUserProfile" in text


def test_prescriptions_can_be_listed_by_visit() -> None:
    text = Path("backend/app/api/v1/endpoints/prescriptions.py").read_text(encoding="utf-8")
    assert '""' in text
    assert "visit_id" in text
