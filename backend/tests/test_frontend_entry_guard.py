"""Guard: the served GUI entry file must exist and stay the server's shell.

On 2026-11-05 a page sweep deleted ``frontend/index.html`` (commit d07c56c,
"per the page audit") because it looked like a duplicate landing page. It is not
one: it is the client shell that ``backend/app/app.py`` mounts at ``/``, so the
deletion took the GUI the server serves (``GET /`` -> 404) and 17 contract tests
with it, and ``main`` went red.

The page audit's rule is about GitHub Pages roots, and this repository publishes
Pages from ``docs/`` only. These tests state that boundary so a future sweep has
something to break instead of a comment to skip.

They assert shape, never a page's content: any legitimate edit to the shell keeps
them green; deleting or relocating the entry, or pointing Pages at ``frontend/``,
turns them red.
"""

from pathlib import Path

from fastapi.testclient import TestClient

from app.app import create_application

ROOT = Path(__file__).resolve().parents[2]
FRONTEND_ENTRY = ROOT / "frontend" / "index.html"
PAGES_ROOT = ROOT / "docs" / "index.html"
MARKER = "HHMS-PAGE-MARKER"


def test_frontend_entry_file_exists():
    """The shell the server mounts must exist in the tree, not only in history."""
    assert FRONTEND_ENTRY.is_file(), (
        "frontend/index.html is the server's GUI entry; deleting it makes GET / 404. "
        "See the HHMS-PAGE-MARKER comment at the end of the file."
    )
    html = FRONTEND_ENTRY.read_text(encoding="utf-8")
    assert MARKER in html, (
        "frontend/index.html lost its HHMS-PAGE-MARKER comment, which is what tells a "
        "page sweep this file is the server shell and not a Pages page."
    )


def test_server_serves_the_entry_at_root():
    """A green file on disk is not a served GUI: ask the application for it."""
    application = create_application()
    with TestClient(application) as client:
        root = client.get("/")
        assert root.status_code == 200, "/ must serve the client shell"
        assert "app.js" in root.text, "the served root is not the HHMS client shell"
        # The shell's own assets must resolve through the same mount.
        assert client.get("/js/app.js").status_code == 200
        assert client.get("/css/app.css").status_code == 200


def test_pages_root_is_docs_and_not_the_frontend():
    """Pages publishes docs/; the frontend is server-served and must not be published."""
    assert PAGES_ROOT.is_file(), "the GitHub Pages landing page is docs/index.html"
    workflow_dir = ROOT / ".github" / "workflows"
    for workflow in sorted(workflow_dir.glob("*.yml")):
        text = workflow.read_text(encoding="utf-8")
        assert "path: frontend" not in text and "path: ./frontend" not in text, (
            f"{workflow.name} publishes the frontend as a Pages site; the client shell is "
            "served by the application, not by Pages"
        )
