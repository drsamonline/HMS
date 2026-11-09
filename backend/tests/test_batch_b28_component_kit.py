"""Gate tests for build-plan batch B28: the component kit.

The screens used window.prompt() for anything needing more than one field: creating
a user asked for a username, then a full name, then a password, in three browser
dialogs that cannot be styled, cannot be cancelled as a group, and cannot show a
validation message. Half-created records were the normal outcome of a change of mind
on the third prompt.

These tests are static analysis of the frontend, because that is where the contract
lives: the kit exists, the screens use it, and nothing falls back to a browser
dialog.
"""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
JS = ROOT / "frontend" / "js"
UI = JS / "ui"
CSS = ROOT / "frontend" / "css"

#: Every screen file, excluding the kit itself.
SCREENS = sorted(path for path in JS.glob("*.js"))

BROWSER_DIALOG = re.compile(r"(?<![\w.])(window\.)?(prompt|alert|confirm)\s*\(")


def test_the_kit_exists() -> None:
    for name in ("dialog.js", "states.js", "table.js", "patient-header.js"):
        assert (UI / name).is_file(), f"missing component: ui/{name}"


def test_no_screen_uses_a_browser_dialog() -> None:
    """A prompt cannot be styled, cancelled as a group, or validated."""

    offenders = []
    for path in SCREENS:
        source = path.read_text(encoding="utf-8")
        for match in BROWSER_DIALOG.finditer(source):
            # confirmDialog and notify are the kit's own names, not the browser's.
            line_start = source.rfind("\n", 0, match.start()) + 1
            line = source[line_start : source.find("\n", match.start())]
            if "confirmDialog" in line or "notify(" in line:
                continue
            offenders.append(f"{path.name}: {match.group(0)}")
    assert not offenders, f"browser dialogs remain: {offenders}"


def test_every_screen_that_replaced_a_dialog_imports_the_kit() -> None:
    for name in (
        "admin.js",
        "backups.js",
        "billing.js",
        "mrd.js",
        "print.js",
        "settings.js",
        "system_health.js",
    ):
        source = (JS / name).read_text(encoding="utf-8")
        assert "ui/dialog.js" in source, f"{name} does not import the dialog kit"


def test_the_dialog_returns_null_when_cancelled() -> None:
    """Returning undefined is how half-filled records used to get created."""

    source = (UI / "dialog.js").read_text(encoding="utf-8")
    assert "resolve(null)" in source or "? dialog.__values : null" in source
    assert 'dialog.close("__submitted__")' in source


def test_the_dialog_validates_before_closing() -> None:
    source = (UI / "dialog.js").read_text(encoding="utf-8")
    assert "is required." in source
    assert "event.preventDefault()" in source


def test_every_state_has_its_own_message() -> None:
    """Empty, no-results and error are three different situations."""

    source = (UI / "states.js").read_text(encoding="utf-8")
    for name in ("emptyState", "noResultsState", "loadingState", "errorState"):
        assert f"export function {name}" in source, f"missing {name}"
    assert "Nothing matched" in source
    assert "Could not load this" in source


def test_the_error_state_shows_the_real_message() -> None:
    """A hospital cannot act on 'an error occurred'."""

    source = (UI / "states.js").read_text(encoding="utf-8")
    assert "The server did not answer." in source
    assert "error.message" in source


def test_the_table_escapes_plain_values_and_trusts_render_functions() -> None:
    source = (UI / "table.js").read_text(encoding="utf-8")
    assert "column.render ? column.render(row) : escapeHtml(" in source


def test_the_patient_header_always_carries_the_identifier() -> None:
    """On a ward, the wrong-patient error is the one that matters most."""

    source = (UI / "patient-header.js").read_text(encoding="utf-8")
    assert "patient_number" in source
    assert 'patient.patient_number || "—"' in source


def test_the_kit_stylesheet_names_no_colour() -> None:
    """The moment ui.css names a colour, the palette has two sources of truth."""

    source = (CSS / "ui.css").read_text(encoding="utf-8")
    literals = re.findall(r"#[0-9a-fA-F]{3,8}\b|rgba?\([^)]*\)", source)
    assert not literals, f"ui.css carries literal colours: {sorted(set(literals))}"


def test_the_kit_stylesheet_is_linked_after_the_tokens() -> None:
    html = (ROOT / "frontend" / "index.html").read_text(encoding="utf-8")
    assert html.index("tokens.css") < html.index("ui.css")
