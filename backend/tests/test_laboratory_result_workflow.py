from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SERVICE = ROOT / "app/services/investigation_result.py"


def test_laboratory_result_service_enforces_non_reversible_release():
    source = SERVICE.read_text(encoding="utf-8")
    assert "allowed_transitions" in source
    assert '"released":' not in source or '"released"' in source
    assert "cannot transition from" in source


def test_verified_and_released_reports_require_result_text():
    source = SERVICE.read_text(encoding="utf-8")
    assert "Result text is required before a laboratory report can be verified or released." in source
