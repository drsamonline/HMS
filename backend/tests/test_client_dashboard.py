"""Regression tests for unified client dashboard navigation."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

def test_dashboard_module_exists() -> None:
    assert (ROOT / "frontend" / "js" / "dashboard.js").is_file()

def test_dashboard_navigation_is_present() -> None:
    html = (ROOT / "frontend" / "index.html").read_text(encoding="utf-8")
    assert 'data-app-view="dashboard"' in html
    assert 'dashboard.js' in html
