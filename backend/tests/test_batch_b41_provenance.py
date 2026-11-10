"""Gate tests for build-plan batch B41: provenance marks.

The purpose is narrow: if this source tree is copied into another product, the copy
should be identifiable as a copy. That is evidence for a lawyer and a deterrent to
the casual, not a technical control - anyone determined enough can strip the marks,
and these tests are written knowing that.

What they do hold: the mark is stable, it is harmless, it appears in more than one
kind of file, and it is published where anyone can read it.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_the_marker_is_stable() -> None:
    """A mark that changes on every build cannot be tied to a distributed release."""

    from app.core.provenance import marker

    assert marker() == marker()
    assert marker().startswith("HHMS-PROV-")


def test_the_marker_is_derived_from_the_facts_that_matter() -> None:
    from app.core.provenance import OWNER, RELEASE, marker

    assert RELEASE in marker()
    assert OWNER  # a marker with no owner attached proves nothing


def test_verify_accepts_the_real_marker_and_nothing_else() -> None:
    from app.core.provenance import marker, verify

    assert verify(f"/* {marker()} */")
    assert not verify("HHMS-PROV-0.0.1-deadbeef0000")
    assert not verify("")


def test_find_marks_reports_both_the_identifier_and_the_canary() -> None:
    from app.core.provenance import CANARY, marker, find_marks

    found = find_marks(f"{marker()} and {CANARY}")
    assert marker() in found
    assert CANARY in found


def test_the_mark_appears_in_more_than_one_kind_of_file() -> None:
    """One mark in one file is removed by one careless refactor."""

    from app.core.provenance import marker

    mark = marker()
    carriers = {
        "css": ROOT / "frontend" / "css" / "tokens.css",
        "js": ROOT / "frontend" / "js" / "ui" / "dialog.js",
        "python": ROOT / "backend" / "app" / "__init__.py",
        "backend entry": ROOT / "backend" / "app" / "main.py",
    }
    missing = [
        name for name, path in carriers.items()
        if mark not in path.read_text(encoding="utf-8")
    ]
    assert not missing, f"the mark is missing from: {missing}"


def test_the_mark_is_harmless_where_it_is_embedded() -> None:
    """A mark that broke the software when removed would be a defect."""

    css = (ROOT / "frontend" / "css" / "tokens.css").read_text(encoding="utf-8")
    assert "--provenance:" in css

    js = (ROOT / "frontend" / "js" / "ui" / "dialog.js").read_text(encoding="utf-8")
    assert "export const PROVENANCE" in js

    init = (ROOT / "backend" / "app" / "__init__.py").read_text(encoding="utf-8")
    assert "__provenance__" in init


def test_the_payload_says_what_a_copy_means() -> None:
    from app.core.provenance import payload

    body = payload()
    assert body["owner"]
    assert "proprietary" in body["notice"].lower()
    assert body["marker"] == payload()["marker"]


# ------------------------------------------------------------------ detector
def test_the_detector_finds_the_marks_in_this_tree() -> None:
    from app.core.provenance import marker

    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "detect_provenance.py"), str(ROOT),
         "--expect", marker(), "--quiet"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr


def test_the_detector_fails_on_a_tree_with_no_marks(tmp_path) -> None:
    """A detector that always passes is decoration."""

    (tmp_path / "clean.py").write_text("print('nothing to see')\n", encoding="utf-8")
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "detect_provenance.py"), str(tmp_path), "--quiet"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 1


def test_the_detector_fails_when_the_wrong_mark_is_expected() -> None:
    # Built by concatenation on purpose. A literal would sit in this file, and the
    # detector - which scans this repository - would find it and report success.
    # That happened on the first run, which is why the assertion is written this way.
    wrong = "HHMS-PROV" + "-9.9.9-" + "0" * 12

    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "detect_provenance.py"), str(ROOT),
         "--expect", wrong, "--quiet"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 2


def test_the_detector_finds_a_mark_in_a_renamed_copy(tmp_path) -> None:
    """The point of the exercise: a copy under another name is still a copy."""

    from app.core.provenance import marker

    (tmp_path / "someone_elses_product.py").write_text(
        f"# {marker()}\nprint('hello')\n", encoding="utf-8"
    )
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "detect_provenance.py"), str(tmp_path),
         "--expect", marker(), "--quiet"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0


# ------------------------------------------------------------------ endpoint
def test_the_provenance_claim_is_public() -> None:
    """A licence notice nobody can read is not a notice."""

    from app.dependencies.permissions import PUBLIC_PATHS

    assert "/api/v1/provenance" in PUBLIC_PATHS


def test_the_endpoint_serves_the_payload_without_a_token() -> None:
    from tests._qa_harness import make_client

    with make_client() as client:
        response = client.get("/api/v1/provenance")

    assert response.status_code == 200, response.text
    assert response.json()["marker"].startswith("HHMS-PROV-")
