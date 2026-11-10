"""Gate for the handover pack.

When nobody is answering the phone, what does this hospital need to run the software it
paid for? The pack is the answer, and it fails to build rather than shipping a partial
one - a missing document is a missing answer.
"""

from __future__ import annotations

import hashlib
import subprocess
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "handover_pack.py"

REQUIRED = (
    "README.md",
    "operations/OPERATIONS.md",
    "operations/role-guides/README.md",
    "compliance/NABH-MAPPING.md",
    "compliance/NABH-PSQ3.md",
    "reference/API_REFERENCE.md",
    "licence/EDITION.json",
    "integrity/VERIFY.md",
    "MANIFEST.sha256",
)


def _seal(tmp_path: Path) -> Path:
    """A seal, as a release would produce one."""

    seal = tmp_path / "SEAL.json"
    subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "seal_build.py"), "seal", str(ROOT),
         "--out", str(seal)],
        capture_output=True,
    )
    return seal


def _pack(tmp_path: Path, with_seal: bool = True) -> zipfile.ZipFile:
    out = tmp_path / "handover.zip"
    args = [sys.executable, str(SCRIPT), "--out", str(out)]
    if with_seal:
        args += ["--seal", str(_seal(tmp_path))]
    result = subprocess.run(args, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    return zipfile.ZipFile(out)


def test_the_pack_builds(tmp_path) -> None:
    archive = _pack(tmp_path)
    assert archive.namelist()


def test_every_required_document_is_present(tmp_path) -> None:
    names = set(_pack(tmp_path).namelist())
    missing = [name for name in REQUIRED if name not in names]
    assert not missing, f"the handover pack is missing: {missing}"


def test_every_role_guide_travels_with_it(tmp_path) -> None:
    """A hospital that cannot explain its own records has a problem the day the vendor leaves."""

    names = set(_pack(tmp_path).namelist())
    guides = [name for name in names if name.startswith("operations/role-guides/")]
    assert len(guides) >= 10


def test_the_manifest_hashes_every_other_file(tmp_path) -> None:
    archive = _pack(tmp_path)
    manifest = archive.read("MANIFEST.sha256").decode().strip().splitlines()

    listed = {}
    for line in manifest:
        digest, name = line.split("  ", 1)
        listed[name] = digest

    actual = {
        name for name in archive.namelist() if name != "MANIFEST.sha256"
    }
    assert set(listed) == actual

    for name, digest in listed.items():
        assert hashlib.sha256(archive.read(name)).hexdigest() == digest, (
            f"{name} does not match its manifest hash"
        )


def test_the_readme_says_what_to_do_first(tmp_path) -> None:
    """The one page somebody reads at 2am."""

    text = " ".join(_pack(tmp_path).read("README.md").decode().split())
    assert "When something breaks, in this order" in text
    assert "Read the log" in text
    assert "Do not restore over a running server" in text


def test_the_readme_names_the_edition_and_its_licence(tmp_path) -> None:
    text = _pack(tmp_path).read("README.md").decode()
    assert "Edition" in text
    assert "Licence" in text
    assert "Not included" in text


def test_it_names_the_three_things_worth_reading_first(tmp_path) -> None:
    text = " ".join(_pack(tmp_path).read("README.md").decode().split())
    assert "the backup drill" in text
    assert "absent" in text
    assert "role-guides" in text


def test_it_says_what_it_does_not_promise(tmp_path) -> None:
    """A pack that oversells itself is one a hospital stops trusting."""

    text = " ".join(_pack(tmp_path).read("README.md").decode().split())
    assert "What this pack does not promise" in text
    assert "does not promise the software is free of faults" in text


def test_the_pack_contains_no_patient_data_and_no_source(tmp_path) -> None:
    """The first is not ours to ship; the second is not what a handover is for."""

    archive = _pack(tmp_path)
    names = archive.namelist()
    assert not [name for name in names if name.endswith((".py", ".sqlite3", ".db", ".js"))]

    text = " ".join(_pack(tmp_path).read("README.md").decode().split())
    assert "no patient data and no source code" in text


def test_the_verify_note_says_what_a_match_proves(tmp_path) -> None:
    text = " ".join(_pack(tmp_path).read("integrity/VERIFY.md").decode().split())
    assert "It does not prove the software is correct" in text
    assert "published with the release" in text


def test_the_pack_carries_the_seal_when_it_is_given_one(tmp_path) -> None:
    archive = _pack(tmp_path)
    assert "integrity/SEAL.json" in archive.namelist()
    text = _pack(tmp_path).read("README.md").decode()
    assert "sealed" in text


def test_the_pack_says_so_when_no_seal_was_supplied(tmp_path) -> None:
    """A pack that quietly omits the seal looks like a pack that has one."""

    archive = _pack(tmp_path, with_seal=False)
    assert "integrity/SEAL.json" not in archive.namelist()
    text = " ".join(archive.read("README.md").decode().split())
    assert "No seal was included" in text


def test_the_edition_is_machine_readable(tmp_path) -> None:
    import json

    data = json.loads(_pack(tmp_path).read("licence/EDITION.json").decode())
    assert data["licence"]
    assert data["modules"]
    assert "not_included" in data


def test_a_missing_document_fails_the_build(tmp_path) -> None:
    """A partial pack is worse than none: it looks complete."""

    sys.path.insert(0, str(ROOT / "scripts"))
    import handover_pack

    original = dict(handover_pack.REQUIRED)
    try:
        handover_pack.REQUIRED["missing.md"] = "docs/does-not-exist.md"
        try:
            handover_pack.build(tmp_path / "should-not-exist.zip")
        except FileNotFoundError as exc:
            assert "missing required documents" in str(exc)
        else:
            raise AssertionError("the build should have refused")
    finally:
        handover_pack.REQUIRED.clear()
        handover_pack.REQUIRED.update(original)
