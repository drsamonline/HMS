"""Gate tests for build-plan batches B04 and B05.

B04 - the fleet block injected into the served GUI shell is gone. It wrapped
``localStorage.setItem``, and HHMS keeps its auth token and autosave state in
``localStorage``, so the wrapper sat on live code paths.
B05 - the client fails closed when an account holds no permissions.
"""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ENTRY = ROOT / "frontend" / "index.html"
RBAC = ROOT / "frontend" / "js" / "rbac.js"


def test_injected_fleet_block_is_gone() -> None:
    html = ENTRY.read_text(encoding="utf-8")
    assert "THE FOUR THINGS" not in html
    assert "__exportAll" not in html
    assert "__importAll" not in html


def test_gui_shell_still_present_and_marked() -> None:
    """B04 must not repeat the page-sweep accident."""
    html = ENTRY.read_text(encoding="utf-8")
    assert "HHMS-PAGE-MARKER" in html
    assert '<main class="app-shell">' in html


def test_rbac_fails_closed() -> None:
    source = RBAC.read_text(encoding="utf-8")
    assert "if(!permissions.length)return false;" in source
    assert "if(!permissions.length)return true;" not in source


def test_empty_permission_notice_exists() -> None:
    """A user locked out must be told why, not shown an empty shell."""
    assert 'id="access-notice"' in ENTRY.read_text(encoding="utf-8")
    assert "access-notice" in RBAC.read_text(encoding="utf-8")
