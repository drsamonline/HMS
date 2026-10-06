"""Regression tests for client request timeout contract."""
from pathlib import Path


def test_api_request_timeout_is_configured_and_clears_timer() -> None:
    source = Path("frontend/js/api.js").read_text(encoding="utf-8")
    assert "AbortController" in source
    assert "timeoutMs" in source
    assert "clearTimeout(timeoutId)" in source
    assert "hhms:request-timeout" in source


def test_app_surfaces_request_timeout_without_logging_out() -> None:
    source = Path("frontend/js/app.js").read_text(encoding="utf-8")
    assert "hhms:request-timeout" in source
    assert "showConnectionBanner" in source
    assert "enterSignedOutState" in source
