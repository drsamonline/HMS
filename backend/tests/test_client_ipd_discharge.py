"""Contract tests for the client IPD discharge workflow."""
from pathlib import Path


def test_client_ipd_management_contains_discharge_workflow() -> None:
    path = Path(__file__).resolve().parents[2] / "frontend" / "js" / "ipd_management.js"
    text = path.read_text(encoding="utf-8")
    assert "data-discharge-form" in text
    assert "createDischarge" in text
    assert "discharged_by" in text
