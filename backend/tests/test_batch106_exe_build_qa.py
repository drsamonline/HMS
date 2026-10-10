"""Batch 106 — Milestone 7 EXE build execution & frozen-runtime smoke QA.

Batch 105 verified the packaging *infrastructure* statically; Batch 106 runs
the actual PyInstaller build and exercises the resulting executable.  To keep
CI cheap and hermetic, this suite is split in two tiers:

Tier 1 — static gates (always run):
    Defects found while executing the first real build are locked in here:
    * ``build-server.sh`` must not pass ``--specpath`` when invoking a .spec
      file (makespec-only option; PyInstaller rejects it), must target the
      one-file artifact path, and must chmod +x it.
    * ``HHMS-Server.spec`` must resolve its own directory via ``SPECPATH``
      (spec files are exec()'d without ``__file__``), must compute the
      project root as ``parents[1]`` of the packaging dir, and must list
      the lazily-imported DBAPI drivers (``aiosqlite``, ``sqlite3``) as
      hidden imports — SQLAlchemy imports them only at engine-creation
      time, so PyInstaller's static analysis misses them and every request
      500s with ModuleNotFoundError in the frozen server.

Tier 2 — real build + frozen smoke (opt-in via HHMS_RUN_EXE_BUILD=1):
    Runs scripts/deploy/build-server.sh end-to-end, launches the produced
    executable against a fresh HHMS_APPLICATION_ROOT, and asserts the full
    first-run contract over real HTTP: health handshake reports the VERSION
    release version, alembic chain reaches head 0028, bad-credential login
    returns a structured 401 (proves the async DB stack works in the frozen
    binary), and /health/discovery agrees with /health.
"""
from __future__ import annotations

import json
import os
import re
import sqlite3
import subprocess
import time
import urllib.error
import urllib.request
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
BACKEND_ROOT = PROJECT_ROOT / "backend"
SPEC_PATH = BACKEND_ROOT / "packaging" / "HHMS-Server.spec"
BUILD_SCRIPT = PROJECT_ROOT / "scripts" / "deploy" / "build-server.sh"

RUN_EXE_BUILD = os.environ.get("HHMS_RUN_EXE_BUILD") == "1"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# Tier 1: static gates locking in the defects found by the first real build
# ---------------------------------------------------------------------------


def test_build_script_does_not_pass_specpath_with_spec_file() -> None:
    """``--specpath`` is a makespec-only flag; PyInstaller rejects it when a
    .spec file is supplied directly.  The first real build failed on exactly
    this (batch 106 defect 1)."""
    text = _read(BUILD_SCRIPT)
    code = "\n".join(
        ln for ln in text.splitlines() if not ln.lstrip().startswith("#")
    )
    assert "--specpath" not in code, (
        "build-server.sh must not pass --specpath when running a .spec file"
    )
    # the spec is still the build input, and work/dist paths are controlled
    assert "${SPEC}" in text
    assert "--workpath" in text and "--distpath" in text


def test_build_script_targets_one_file_artifact_and_marks_executable() -> None:
    """The spec produces a ONE-FILE exe at dist/HHMS-Server (not a
    dist/HHMS-Server/ directory).  The original post-build check looked for
    the one-dir layout and failed a successful build (batch 106 defect 2)."""
    text = _read(BUILD_SCRIPT)
    assert re.search(r'BUNDLE_EXE="\$\{OUT_DIR\}/HHMS-Server"', text), (
        "post-build check must target the one-file artifact ${OUT_DIR}/HHMS-Server"
    )
    assert "chmod +x" in text


def test_spec_resolves_own_directory_via_specpath_not_dunder_file() -> None:
    """Spec files are exec()'d by PyInstaller without a ``__file__`` global;
    ``SPECPATH`` is the documented substitute.  The original spec used
    ``Path(__file__)`` and crashed the build (batch 106 defect 3)."""
    text = _read(SPEC_PATH)
    code_lines = [ln for ln in text.splitlines() if not ln.lstrip().startswith("#")]
    assert "__file__" not in "\n".join(code_lines), (
        "HHMS-Server.spec must not reference __file__ (undefined in spec namespace)"
    )
    assert "SPECPATH" in text


def test_spec_project_root_depth_is_correct() -> None:
    """Packaging dir is backend/packaging → parents[1] is the repo root.
    The original parents[2] pointed one level too high and PyInstaller
    reported 'script ... not found' (batch 106 defect 4)."""
    text = _read(SPEC_PATH)
    assert "_spec_dir.parents[1]" in text


def test_spec_lists_lazy_dbapi_hidden_imports() -> None:
    """SQLAlchemy imports the DBAPI named by the URL scheme only at
    engine-creation time, so PyInstaller cannot see it; without the explicit
    hidden import the frozen server bootstrapped migrations but returned 500
    on every request with ModuleNotFoundError: No module named 'aiosqlite'
    (batch 106 defect 5 — found by the frozen smoke probe)."""
    text = _read(SPEC_PATH)
    assert '"aiosqlite"' in text and '"sqlite3"' in text


def test_build_script_syntax_gate() -> None:
    result = subprocess.run(
        ["bash", "-n", str(BUILD_SCRIPT)], capture_output=True, text=True
    )
    assert result.returncode == 0, result.stderr


# ---------------------------------------------------------------------------
# Tier 2: real build + frozen-executable first-run smoke (opt-in)
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def built_server_exe(tmp_path_factory) -> Path:
    if not RUN_EXE_BUILD:
        pytest.skip("set HHMS_RUN_EXE_BUILD=1 to run the real PyInstaller build")
    out_dir = tmp_path_factory.mktemp("exebuild-dist")
    result = subprocess.run(
        ["bash", str(BUILD_SCRIPT), str(out_dir)],
        capture_output=True,
        text=True,
        timeout=1800,
    )
    assert result.returncode == 0, (
        f"build failed:\n{result.stdout[-3000:]}\n{result.stderr[-3000:]}"
    )
    exe = out_dir / "HHMS-Server"
    assert exe.is_file() and os.access(exe, os.X_OK)
    return exe


def _get_json(url: str, timeout: float = 5.0) -> dict:
    req = urllib.request.Request(url, headers={"Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode())


def _post_json_expect_status(url: str, payload: dict, expected: int) -> dict:
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json", "Accept": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            status, body = resp.status, resp.read().decode()
    except urllib.error.HTTPError as exc:
        status, body = exc.code, exc.read().decode()
    assert status == expected, f"{url} -> {status}: {body[:300]}"
    return json.loads(body)


def test_frozen_exe_bootstraps_migrations_to_head(built_server_exe: Path, tmp_path) -> None:
    """First launch of the packaged server must create runtime dirs and run
    the full alembic chain 0001→0028 inside the frozen binary."""
    app_root = tmp_path / "runtime"
    env = {**os.environ, "HHMS_APPLICATION_ROOT": str(app_root), "SERVER_PORT": "8191"}
    proc = subprocess.Popen(
        [str(built_server_exe)], env=env,
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    try:
        deadline = time.time() + 60
        last: Exception | None = None
        health: dict = {}
        while time.time() < deadline:
            try:
                health = _get_json("http://127.0.0.1:8191/api/v1/health")
                break
            except Exception as exc:  # noqa: BLE001 - retry until up
                last = exc
                if proc.poll() is not None:
                    pytest.fail(f"frozen server exited early (rc={proc.returncode})")
                time.sleep(1.0)
        else:  # pragma: no cover
            pytest.fail(f"frozen server never became healthy: {last}")
        assert health["status"] == "healthy"
        assert health["version"] == _read(PROJECT_ROOT / "VERSION").strip()

        db = app_root / "data" / "hhms.sqlite3"
        assert db.exists(), "frozen first run did not create the SQLite database"
        version_rows = sqlite3.connect(db).execute(
            "select version_num from alembic_version"
        ).fetchall()
        assert [r[0] for r in version_rows] == [
            "0028_prescription_operational_year_lifecycle"
        ]

        # Async DB stack works in the frozen binary: bad-credential login
        # must be a structured 401, never a 500 (the aiosqlite defect).
        body = _post_json_expect_status(
            "http://127.0.0.1:8191/api/v1/auth/login",
            {"username": "nope", "password": "wrong"},
            401,
        )
        assert body["error"]["code"] == "AUTHENTICATION_ERROR"

        # Discovery payload agrees with the served port.
        disc = _get_json("http://127.0.0.1:8191/api/v1/health/discovery")
        assert disc["protocol"] == "hhms-lan-v1"
        assert disc["http_port"] == 8191
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=10)
        except subprocess.TimeoutExpired:  # pragma: no cover
            proc.kill()


def test_build_end_to_end_produces_runnable_artifact(built_server_exe: Path) -> None:
    """Smoke-level sanity independent of HTTP: the artifact is a real ELF/PE
    executable of meaningful size produced purely by the deploy script."""
    size = built_server_exe.stat().st_size
    assert size > 10_000_000, f"suspiciously small bundle: {size} bytes"
    magic = built_server_exe.read_bytes()[:4]
    assert magic.startswith(b"\x7fELF") or magic.startswith(b"MZ"), (
        f"unexpected artifact header: {magic!r}"
    )
