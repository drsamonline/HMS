"""Gate tests for the escaping check and the release gate.

The audit recorded F-05 as **unverified**: every frontend module had an escape helper,
and nobody had checked whether all of them used it. This batch answers the question with
a tool rather than an opinion.

The tool is deliberately two-sided. It flags an interpolation into markup that was not
escaped, and it carries a baseline of the ones that were reviewed and found safe - so a
new violation fails the build while a reviewed one does not. A checker that flags
everything is ignored within a week; one that flags nothing is decoration.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CHECKER = ROOT / "scripts" / "check_frontend_escaping.py"
RELEASE = ROOT / "scripts" / "check_release_ready.py"


def _run(script: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(script), *args], capture_output=True, text=True, cwd=ROOT
    )


# ------------------------------------------------------------- the escaping gate
def test_the_frontend_is_clean() -> None:
    result = _run(CHECKER, "--strict")
    assert result.returncode == 0, result.stdout + result.stderr


def test_the_gate_fails_on_a_planted_violation(tmp_path) -> None:
    """A check that has never failed is not a check (D-097)."""

    target = ROOT / "frontend" / "js" / "opd.js"
    original = target.read_text(encoding="utf-8")
    try:
        target.write_text(
            original + "\nfunction _probe(el, row){ el.innerHTML = `<b>${row.patient_name}</b>`; }\n",
            encoding="utf-8",
        )
        result = _run(CHECKER, "--strict")
        assert result.returncode == 1
        assert "row.patient_name" in result.stdout
    finally:
        target.write_text(original, encoding="utf-8")


def test_an_escaped_interpolation_is_not_flagged(tmp_path) -> None:
    target = ROOT / "frontend" / "js" / "opd.js"
    original = target.read_text(encoding="utf-8")
    try:
        target.write_text(
            original + "\nfunction _ok(el, row){ el.innerHTML = `<b>${esc(row.patient_name)}</b>`; }\n",
            encoding="utf-8",
        )
        assert _run(CHECKER, "--strict").returncode == 0
    finally:
        target.write_text(original, encoding="utf-8")


def test_the_baseline_says_why_each_entry_is_safe() -> None:
    """A baseline without reasons is a list of things nobody looked at."""

    data = json.loads((ROOT / "frontend" / ".escaping-baseline.json").read_text(encoding="utf-8"))
    assert data["reviewed"], "the baseline is empty"
    for entry in data["reviewed"]:
        assert entry["reason"].strip(), f"{entry['path']} has no reason recorded"
        assert len(entry["reason"]) > 20, f"{entry['path']}: {entry['reason']!r} is not a reason"


def test_every_baseline_entry_still_exists() -> None:
    """A stale entry hides a fix that was never made, or a file that was renamed."""

    data = json.loads((ROOT / "frontend" / ".escaping-baseline.json").read_text(encoding="utf-8"))
    for entry in data["reviewed"]:
        path = ROOT / entry["path"]
        assert path.is_file(), f"{entry['path']} no longer exists"
        assert entry["expression"].split("?")[0][:30] in path.read_text(
            encoding="utf-8", errors="ignore"
        ) or entry["expression"][:12] in path.read_text(encoding="utf-8", errors="ignore"), (
            f"the baseline entry for {entry['path']} no longer matches the file"
        )


def test_the_checker_ignores_a_markup_building_function() -> None:
    """False positives are what make a checker ignorable."""

    target = ROOT / "frontend" / "js" / "opd.js"
    original = target.read_text(encoding="utf-8")
    try:
        target.write_text(
            original + "\nfunction _m(el, p){ el.innerHTML = `<div>${patientHeader(p)}</div>`; }\n",
            encoding="utf-8",
        )
        assert _run(CHECKER, "--strict").returncode == 0
    finally:
        target.write_text(original, encoding="utf-8")


# ------------------------------------------------------------- the release gate
def test_the_release_gate_refuses_a_development_key() -> None:
    """This build carries one, so it must refuse - that is the whole point."""

    from app.core.licence_keys import IS_DEVELOPMENT_KEY

    result = _run(RELEASE)
    if IS_DEVELOPMENT_KEY:
        assert result.returncode == 1
        assert "NOT READY TO SHIP" in result.stdout
        assert "DEVELOPMENT licence public key" in result.stdout
    else:
        assert result.returncode == 0
        assert "ready" in result.stdout


def test_the_release_gate_says_how_to_fix_it() -> None:
    result = _run(RELEASE)
    if result.returncode == 1:
        assert "keygen" in result.stdout
        assert "licence_keys.py" in result.stdout


def test_a_zero_grace_period_would_also_block_a_release() -> None:
    """Bricking a hospital on an anniversary is a hazard, not a business model."""

    from app.core.licensing import GRACE_DAYS

    assert GRACE_DAYS > 0
