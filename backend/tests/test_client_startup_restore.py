"""Regression tests for client startup/session restoration behavior."""
from pathlib import Path


def test_client_startup_prefers_saved_server_before_discovery() -> None:
    source = Path("frontend/js/app.js").read_text(encoding="utf-8")
    assert "if(c.manualServerUrl){" in source
    assert "await connectTo(c.manualServerUrl)" in source


def test_client_startup_falls_back_to_discovery() -> None:
    source = Path("frontend/js/app.js").read_text(encoding="utf-8")
    assert "await discover();" in source
