"""Gate for the operations runbook.

A runbook is the one document where being wrong costs somebody's afternoon. Every
command in it must exist, every document it points at must exist, and it must not
duplicate the documents it points at - because two copies of an instruction is how
one of them goes stale.
"""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DOC = ROOT / "docs" / "OPERATIONS.md"


def _text() -> str:
    return DOC.read_text(encoding="utf-8")


def _flat() -> str:
    return " ".join(_text().split())


def test_the_runbook_exists() -> None:
    assert DOC.is_file()


def test_every_file_it_points_at_exists() -> None:
    """A runbook that sends an operator to a missing script wastes their evening."""

    cited = set(re.findall(r"`((?:docs|scripts)/[^`]+?\.(?:md|py|sh|ps1))`", _text()))
    missing = [path for path in sorted(cited) if not (ROOT / path).exists()]
    assert not missing, f"OPERATIONS.md points at files that do not exist: {missing}"


def test_every_cli_module_it_names_exists() -> None:
    modules = set(re.findall(r"python -m (app\.cli\.[a-z_]+)", _text()))
    assert modules, "the runbook should name at least one CLI module"

    missing = [
        name
        for name in modules
        if not (ROOT / "backend" / "app" / "cli" / f"{name.rsplit('.', 1)[1]}.py").is_file()
    ]
    assert not missing, f"OPERATIONS.md names CLI modules that do not exist: {missing}"


def test_it_points_at_the_documents_that_own_each_subject() -> None:
    """Two copies of an instruction is how one of them goes stale."""

    flat = _flat()
    for document in (
        "scripts/deploy/README.md",
        "docs/SECRET_ROTATION_RUNBOOK.md",
        "docs/ARCHIVE_RETENTION_TIERS.md",
        "docs/ANNUAL_CASE_ROLLOVER.md",
        "docs/ADMIN_TRAINING.md",
    ):
        assert document in flat, f"the runbook does not point at {document}"


def test_it_says_a_backup_is_not_a_backup_until_restored() -> None:
    """The drill is the point of the backup section; the schedule is secondary."""

    assert "A backup nobody has restored is a file, not a backup" in _flat()


def test_the_troubleshooting_table_names_real_endpoints() -> None:
    from app.api.v1.api import api_router

    mounted = {route.path for route in api_router.routes}
    cited = set(re.findall(r"GET (/api/v1/[a-z/-]+)", _text()))

    missing = [
        path
        for path in sorted(cited)
        if not any(
            route == path.removeprefix("/api/v1")
            or route.startswith(path.removeprefix("/api/v1") + "/")
            for route in mounted
        )
    ]
    assert not missing, f"the runbook names endpoints that are not mounted: {missing}"


def test_it_states_what_it_does_not_cover() -> None:
    """A runbook that describes unsupported deployments is fiction."""

    flat = _flat()
    assert "does not cover a multi-site deployment" in flat


def test_the_setup_code_instruction_matches_the_behaviour() -> None:
    """The code goes to the log, locks after five attempts, and dies at completion."""

    flat = _flat()
    assert "six-digit code" in flat
    assert "five wrong attempts" in flat
    assert "stops working" in flat
