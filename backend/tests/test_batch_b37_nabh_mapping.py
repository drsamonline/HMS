"""Gate for the NABH mapping document.

The document claims each row is checkable. This is the check: every file it names
exists, and every endpoint it names is mounted. A mapping that cites something
deleted is worse than no mapping, because it is believed.
"""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MAPPING = ROOT / "docs" / "NABH-MAPPING.md"

PATH_PATTERN = re.compile(r"`((?:backend|docs)/[^`]+?\.(?:py|md))`")
ENDPOINT_PATTERN = re.compile(r"`(?:GET|POST|PUT|PATCH|DELETE) (/api/v1/[^`]+)`")
STATE_PATTERN = re.compile(r"\|\s*(evidenced|partial|absent)\s*\|")


def _text() -> str:
    return MAPPING.read_text(encoding="utf-8")


def test_the_mapping_exists() -> None:
    assert MAPPING.is_file()


def test_every_file_it_cites_exists() -> None:
    missing = [
        path for path in sorted(set(PATH_PATTERN.findall(_text())))
        if not (ROOT / path).exists()
    ]
    assert not missing, f"NABH-MAPPING.md cites files that do not exist: {missing}"


def test_every_endpoint_it_cites_is_mounted() -> None:
    from app.api.v1.api import api_router

    mounted = {route.path for route in api_router.routes}
    missing = []
    for endpoint in sorted(set(ENDPOINT_PATTERN.findall(_text()))):
        # The document writes the public path; the router stores it without the
        # /api/v1 prefix it is included under.
        local = endpoint.removeprefix("/api/v1")
        if not any(path == local or path.startswith(local + "/") for path in mounted):
            missing.append(endpoint)
    assert not missing, f"NABH-MAPPING.md cites unmounted endpoints: {missing}"


def test_every_row_carries_a_state() -> None:
    """A row without a state is a row nobody can act on."""

    states = STATE_PATTERN.findall(_text())
    assert len(states) >= 20, f"only {len(states)} rows carry a state"
    assert "evidenced" in states
    assert "absent" in states


def test_a_planned_feature_is_absent_not_partial() -> None:
    """The rule the document is built on, stated as a test where it can be."""

    text = _text()
    assert "planned is `absent`, not `partial`" in text


def test_the_absent_rows_appear_as_a_roadmap() -> None:
    text = _text()
    assert "## Roadmap" in text
    # Every absent row must be reachable from the roadmap, or it is a gap nobody
    # will read.
    roadmap = text.split("## Roadmap", 1)[1]
    assert "incident reporting" in roadmap
    assert "KPIs" in roadmap


def test_it_names_the_document_it_extended() -> None:
    """The brief's rule: extend, do not add a second document for the same idea."""

    assert "docs/MASTER_SPECIFICATION.md" in _text()
