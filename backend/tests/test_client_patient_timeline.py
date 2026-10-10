"""Client patient timeline contract tests."""
from pathlib import Path

def test_timeline_module_and_workspace_hooks_exist() -> None:
    root = Path(__file__).parents[2]
    assert (root / "frontend/js/timeline.js").exists()
    app = (root / "frontend/js/app.js").read_text(encoding="utf-8")
    api = (root / "frontend/js/api.js").read_text(encoding="utf-8")
    assert "openPatientTimeline" in app
    assert "listVisits" in api
    assert "listAdmissions" in api

def test_timeline_is_empty_safe_by_design() -> None:
    source = (Path(__file__).parents[2] / "frontend/js/timeline.js").read_text(encoding="utf-8")
    assert "No clinical or administrative activity" in source
