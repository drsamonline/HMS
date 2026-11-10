"""Gate tests for build-plan batch B45: the takedown evidence pack.

The pack is not a legal opinion. It is the bundle a lawyer needs in order to form one,
assembled so that nothing in it depends on the person who ran it.

Two properties carry that weight: a third party can reproduce the finding, and the
pack says in its own text what it does not prove.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "evidence_pack.py"


def _marker() -> str:
    sys.path.insert(0, str(ROOT / "backend"))
    from app.core.provenance import marker

    return marker()


def _run(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args], capture_output=True, text=True
    )


def _suspect(tmp_path: Path) -> Path:
    tree = tmp_path / "suspect"
    (tree / "src").mkdir(parents=True)
    (tree / "src" / "app.js").write_text(
        f'/* {_marker()} */\nconst t = localStorage.getItem("hhms_token");\n',
        encoding="utf-8",
    )
    return tree


# ---------------------------------------------------------------- the bundle
def test_the_pack_contains_the_four_pieces(tmp_path) -> None:
    tree = _suspect(tmp_path)
    out = tmp_path / "pack"

    assert _run(str(tree), "--out", str(out)).returncode == 0
    for name in ("README.md", "finding.md", "seal-comparison.md", "evidence.json", "MANIFEST.sha256"):
        assert (out / name).is_file(), f"{name} missing from the pack"


def test_the_manifest_hashes_every_other_file(tmp_path) -> None:
    """So the pack is tamper-evident: an altered finding no longer matches."""

    tree = _suspect(tmp_path)
    out = tmp_path / "pack"
    _run(str(tree), "--out", str(out))

    manifest = (out / "MANIFEST.sha256").read_text().strip().splitlines()
    listed = {line.split("  ", 1)[1] for line in manifest}

    assert listed == {"README.md", "finding.md", "seal-comparison.md", "evidence.json"}
    for line in manifest:
        digest, name = line.split("  ", 1)
        actual = hashlib.sha256((out / name).read_bytes()).hexdigest()
        assert digest == actual, f"{name} does not match its manifest hash"


def test_the_evidence_records_how_it_was_obtained(tmp_path) -> None:
    """A third party has to be able to re-run it."""

    tree = _suspect(tmp_path)
    out = tmp_path / "pack"
    _run(str(tree), "--out", str(out))

    evidence = json.loads((out / "evidence.json").read_text())
    assert evidence["tool"].startswith("hhms-evidence-pack/")
    assert evidence["captured_at"]
    assert evidence["target"] == str(tree)
    assert evidence["verdict"] == "copied"
    assert evidence["files_scanned"] > 0


def test_the_pack_names_the_licence_position(tmp_path) -> None:
    tree = _suspect(tmp_path)
    out = tmp_path / "pack"
    _run(str(tree), "--out", str(out))

    readme = (out / "README.md").read_text()
    assert "PolyForm Noncommercial" in readme
    assert "Licence position" in readme


# ------------------------------------------------------------- what it denies
def test_the_pack_states_what_it_does_not_prove(tmp_path) -> None:
    """The absence of a finding is not a finding of absence."""

    tree = _suspect(tmp_path)
    out = tmp_path / "pack"
    _run(str(tree), "--out", str(out))

    readme = " ".join((out / "README.md").read_text().split())
    assert "not a legal opinion" in readme
    assert "not a finding of absence" in readme


def test_the_pack_does_not_embed_the_suspect_material(tmp_path) -> None:
    """Embedding a copy would be a redistribution, and could be altered afterwards."""

    tree = _suspect(tmp_path)
    out = tmp_path / "pack"
    _run(str(tree), "--out", str(out))

    readme = (out / "README.md").read_text()
    assert "does not contain the material itself" in readme

    for path in out.iterdir():
        if path.is_file():
            assert "localStorage.getItem" not in path.read_text(errors="ignore"), (
                f"{path.name} embeds the suspect's source"
            )


# ------------------------------------------------------------------ verdicts
def test_a_clean_target_produces_a_pack_that_alleges_nothing(tmp_path) -> None:
    clean = tmp_path / "clean"
    clean.mkdir()
    (clean / "other.py").write_text("x = 1\n", encoding="utf-8")
    out = tmp_path / "pack"

    assert _run(str(clean), "--out", str(out)).returncode == 1
    evidence = json.loads((out / "evidence.json").read_text())
    assert evidence["verdict"] == "clean"
    assert "no licence claim" in evidence["licence_claim"]


def test_a_stripped_copy_is_alleged_as_removal_not_only_copying(tmp_path) -> None:
    tree = tmp_path / "stripped"
    tree.mkdir()
    (tree / "app.js").write_text(
        'localStorage.getItem("hhms_token");\n'
        'document.querySelector(".record-nav");\n'
        'x.dataset.appView;\n',
        encoding="utf-8",
    )
    out = tmp_path / "pack"

    assert _run(str(tree), "--out", str(out)).returncode == 0
    evidence = json.loads((out / "evidence.json").read_text())
    assert evidence["verdict"] == "marks stripped"
    assert "deliberate removal" in evidence["licence_claim"]


def test_a_missing_target_is_an_error_not_a_pack(tmp_path) -> None:
    result = _run(str(tmp_path / "nowhere"), "--out", str(tmp_path / "pack"))
    assert result.returncode == 2


# --------------------------------------------------------------------- seal
def test_a_supplied_seal_turns_the_comparison_into_evidence(tmp_path) -> None:
    tree = _suspect(tmp_path)
    seal_path = tmp_path / "SEAL.json"
    subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "seal_build.py"), "seal", str(tree),
         "--out", str(seal_path)],
        capture_output=True,
    )

    out = tmp_path / "pack"
    _run(str(tree), "--out", str(out), "--seal", str(seal_path))

    comparison = (out / "seal-comparison.md").read_text()
    assert "byte-identical" in comparison
    evidence = json.loads((out / "evidence.json").read_text())
    assert evidence["seal_comparison"]["identical"] is True


def test_an_altered_copy_is_reported_as_altered(tmp_path) -> None:
    tree = _suspect(tmp_path)
    seal_path = tmp_path / "SEAL.json"
    subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "seal_build.py"), "seal", str(tree),
         "--out", str(seal_path)],
        capture_output=True,
    )
    (tree / "src" / "app.js").write_text(f"/* {_marker()} */\naltered\n", encoding="utf-8")

    out = tmp_path / "pack"
    _run(str(tree), "--out", str(out), "--seal", str(seal_path))

    evidence = json.loads((out / "evidence.json").read_text())
    assert evidence["seal_comparison"]["modified"] == ["src/app.js"]
    assert "altered after distribution" in (out / "seal-comparison.md").read_text()
