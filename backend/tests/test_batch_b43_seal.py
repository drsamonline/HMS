"""Gate tests for build-plan batch B43: build sealing.

A provenance mark proves the code came from here. A seal proves the copy is the code
that was distributed, unaltered. Both are needed: a copied-and-modified product
carries the mark and is not the product.

What these tests hold: the seal is deterministic, it notices each kind of change, and
it does not pretend to be signed.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "seal_build.py"


def _run(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args], capture_output=True, text=True
    )


def _tree(tmp_path: Path) -> Path:
    tree = tmp_path / "product"
    (tree / "backend" / "app" / "core").mkdir(parents=True)
    (tree / "frontend" / "js").mkdir(parents=True)
    (tree / "backend" / "app" / "main.py").write_text("app = 1\n", encoding="utf-8")
    (tree / "backend" / "app" / "core" / "provenance.py").write_text(
        'RELEASE = "0.0.2"\n', encoding="utf-8"
    )
    (tree / "frontend" / "js" / "app.js").write_text("const a = 1;\n", encoding="utf-8")
    return tree


def _seal(tree: Path, out: Path) -> dict:
    _run("seal", str(tree), "--out", str(out))
    return json.loads(out.read_text())


# ------------------------------------------------------------------- sealing
def test_a_seal_is_deterministic(tmp_path) -> None:
    """Two people sealing the same release must get the same answer."""

    tree = _tree(tmp_path)
    first = _seal(tree, tmp_path / "one.json")
    second = _seal(tree, tmp_path / "two.json")

    assert first["digest"] == second["digest"]
    assert first["files"] == second["files"]


def test_the_seal_carries_the_release(tmp_path) -> None:
    tree = _tree(tmp_path)
    seal = _seal(tree, tmp_path / "seal.json")
    assert seal["release"] == "0.0.2"


def test_the_seal_excludes_what_changes_without_the_source(tmp_path) -> None:
    tree = _tree(tmp_path)
    (tree / "__pycache__").mkdir()
    (tree / "__pycache__" / "x.pyc").write_text("cache", encoding="utf-8")
    (tree / "backend" / "app" / "data.sqlite3").write_text("db", encoding="utf-8")

    seal = _seal(tree, tmp_path / "seal.json")
    assert not any("__pycache__" in name for name in seal["files"])
    assert not any(name.endswith(".sqlite3") for name in seal["files"])


def test_the_seal_says_where_it_must_be_published(tmp_path) -> None:
    """A seal kept beside the code proves nothing against someone who can edit both."""

    tree = _tree(tmp_path)
    seal = _seal(tree, tmp_path / "seal.json")
    assert seal["publish_to"]
    assert "release" in seal["publish_to"]


# ----------------------------------------------------------------- verifying
def test_an_unaltered_tree_verifies(tmp_path) -> None:
    tree = _tree(tmp_path)
    seal = tmp_path / "seal.json"
    _seal(tree, seal)

    result = _run("verify", str(tree), "--seal", str(seal))
    assert result.returncode == 0, result.stdout


def test_a_modified_file_is_reported(tmp_path) -> None:
    tree = _tree(tmp_path)
    seal = tmp_path / "seal.json"
    _seal(tree, seal)

    (tree / "frontend" / "js" / "app.js").write_text("const a = 2;\n", encoding="utf-8")
    result = _run("verify", str(tree), "--seal", str(seal))

    assert result.returncode == 1
    assert "modified" in result.stdout
    assert "app.js" in result.stdout


def test_an_added_file_is_reported(tmp_path) -> None:
    tree = _tree(tmp_path)
    seal = tmp_path / "seal.json"
    _seal(tree, seal)

    (tree / "frontend" / "js" / "extra.js").write_text("// new\n", encoding="utf-8")
    result = _run("verify", str(tree), "--seal", str(seal))

    assert result.returncode == 1
    assert "added" in result.stdout


def test_a_removed_file_is_reported(tmp_path) -> None:
    tree = _tree(tmp_path)
    seal = tmp_path / "seal.json"
    _seal(tree, seal)

    (tree / "frontend" / "js" / "app.js").unlink()
    result = _run("verify", str(tree), "--seal", str(seal))

    assert result.returncode == 1
    assert "missing" in result.stdout


def test_a_whitespace_change_is_reported(tmp_path) -> None:
    """A reformatted copy is a modified copy, and the seal says so."""

    tree = _tree(tmp_path)
    seal = tmp_path / "seal.json"
    _seal(tree, seal)

    (tree / "backend" / "app" / "main.py").write_text("app  =  1\n", encoding="utf-8")
    result = _run("verify", str(tree), "--seal", str(seal))

    assert result.returncode == 1
    assert "main.py" in result.stdout


def test_a_missing_seal_is_an_error_not_a_pass(tmp_path) -> None:
    tree = _tree(tmp_path)
    result = _run("verify", str(tree), "--seal", str(tmp_path / "absent.json"))
    assert result.returncode == 2


def test_the_real_tree_seals_and_verifies(tmp_path) -> None:
    """The tool works on this repository, not only on fixtures."""

    seal = tmp_path / "seal.json"
    assert _run("seal", str(ROOT), "--out", str(seal)).returncode == 0
    assert _run("verify", str(ROOT), "--seal", str(seal)).returncode == 0
