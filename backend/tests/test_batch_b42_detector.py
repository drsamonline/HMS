"""Gate tests for build-plan batch B42: the detector as a usable tool.

Three inputs, one question: did this come from HHMS? A directory, a zip, or a served
copy.

The verdict that matters most is the one that is easy to get wrong: a copy with the
marks removed. Without a fingerprint list it would read as clean, which is the one
answer that would be actively misleading in a letter to a lawyer.
"""

from __future__ import annotations

import json
import subprocess
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "detect_provenance.py"


def _marker() -> str:
    sys.path.insert(0, str(ROOT / "backend"))
    from app.core.provenance import marker

    return marker()


def _run(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args], capture_output=True, text=True
    )


# --------------------------------------------------------------- three inputs
def test_it_scans_a_directory() -> None:
    result = _run(str(ROOT), "--quiet")
    assert result.returncode == 0


def test_it_scans_a_zip(tmp_path) -> None:
    archive = tmp_path / "leak.zip"
    with zipfile.ZipFile(archive, "w") as bundle:
        bundle.writestr("someone/module.py", f"# {_marker()}\nprint('hi')\n")

    result = _run(str(archive), "--quiet")
    assert result.returncode == 0


def test_it_scans_a_file(tmp_path) -> None:
    single = tmp_path / "copy.css"
    single.write_text(f"/* {_marker()} */\nbody{{}}\n", encoding="utf-8")
    assert _run(str(single), "--quiet").returncode == 0


# ------------------------------------------------------------------ verdicts
def test_a_marked_copy_is_called_copied(tmp_path) -> None:
    (tmp_path / "product.py").write_text(f"# {_marker()}\n", encoding="utf-8")
    result = _run(str(tmp_path), "--json", str(tmp_path / "out.json"), "--quiet")

    assert result.returncode == 0
    data = json.loads((tmp_path / "out.json").read_text())
    assert data["verdict"] == "copied"
    assert _marker() in data["marks"]


def test_a_stripped_copy_is_not_called_clean(tmp_path) -> None:
    """The verdict that would otherwise mislead."""

    (tmp_path / "app.js").write_text(
        'const t = localStorage.getItem("hhms_token");\n'
        'document.querySelector(".record-nav");\n'
        'const view = node.dataset.appView;\n'
        'shell.className = "print-preview-shell";\n',
        encoding="utf-8",
    )
    result = _run(str(tmp_path), "--json", str(tmp_path / "out.json"), "--quiet")

    assert result.returncode == 2
    data = json.loads((tmp_path / "out.json").read_text())
    assert data["verdict"] == "marks stripped"
    assert data["fingerprints"]


def test_an_unrelated_tree_is_called_clean(tmp_path) -> None:
    (tmp_path / "other.py").write_text("def add(a, b):\n    return a + b\n", encoding="utf-8")
    result = _run(str(tmp_path), "--quiet")
    assert result.returncode == 1


def test_one_fingerprint_is_not_enough(tmp_path) -> None:
    """A tree that merely mentions 'homoeopathic' is not this software."""

    (tmp_path / "notes.md").write_text("# A homoeopathic clinic\n", encoding="utf-8")
    result = _run(str(tmp_path), "--json", str(tmp_path / "out.json"), "--quiet")

    data = json.loads((tmp_path / "out.json").read_text())
    assert data["verdict"] == "clean"


# ------------------------------------------------------------------- finding
def test_the_finding_names_the_release(tmp_path) -> None:
    """The release column is what ties a copy to a version."""

    (tmp_path / "product.py").write_text(f"# {_marker()}\n", encoding="utf-8")
    out = tmp_path / "finding.md"
    _run(str(tmp_path), "--out", str(out), "--quiet")

    text = out.read_text()
    assert "# Provenance finding" in text
    assert "the marks are present" in text
    assert "Release" in text


def test_the_stripped_finding_says_absence_is_evidence(tmp_path) -> None:
    (tmp_path / "app.js").write_text(
        'localStorage.getItem("hhms_token");\n'
        'document.querySelector(".record-nav");\n'
        'x.dataset.appView;\n'
        'y = "print-preview-shell";\n',
        encoding="utf-8",
    )
    out = tmp_path / "finding.md"
    _run(str(tmp_path), "--out", str(out), "--quiet")

    text = out.read_text()
    assert "the marks have been removed" in text
    assert "itself evidence" in text


def test_the_clean_finding_states_its_own_limit(tmp_path) -> None:
    """A clean result is a statement about the files read, not the product."""

    (tmp_path / "other.py").write_text("x = 1\n", encoding="utf-8")
    out = tmp_path / "finding.md"
    _run(str(tmp_path), "--out", str(out), "--quiet")

    text = out.read_text()
    assert "sufficiently rewritten copy would produce the same finding" in text


def test_a_missing_target_is_an_error_not_a_clean_result() -> None:
    result = _run("/nonexistent/path/for/hhms", "--quiet")
    assert result.returncode == 3


def test_the_json_output_is_machine_readable(tmp_path) -> None:
    (tmp_path / "product.py").write_text(f"# {_marker()}\n", encoding="utf-8")
    out = tmp_path / "result.json"
    _run(str(tmp_path), "--json", str(out), "--quiet")

    data = json.loads(out.read_text())
    assert set(data) >= {"kind", "target", "files_scanned", "marks", "verdict"}
