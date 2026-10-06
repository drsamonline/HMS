"""Batch 106 — Milestone 7 (part 2) EXE build execution & release materials QA.

Two layers:

1. Always-run static gates (Linux-safe, no PyInstaller required):
   - ``HHMS-Server.spec`` must resolve its paths via the PyInstaller-injected
     ``SPECPATH`` (NOT ``__file__`` — spec files are exec()'d without it),
     and must pin the lazily-imported SQLAlchemy dialect DBAPIs
     (``aiosqlite``, sqlite3 drivers) plus argon2 hashing backends as
     hidden imports.  Both defects were real, release-blocking frozen-build
     failures found by actually running the packaged server in Batch 106.
   - The Windows client project version is single-sourced from VERSION.

2. Opt-in frozen-executable smoke test: builds the one-dir bundle with
   PyInstaller (when installed) and boots the frozen ``HHMS-Server`` on an
   ephemeral port against a fresh application root, asserting the full
   first-run contract end to end: alembic 0001->head bootstrap, /health
   reporting the release version, structured 401 (not 500) on bad login
   (proves the lazily-bundled aiosqlite driver loads inside the exe), and a
   consistent discovery payload.  Skipped automatically when PyInstaller is
   unavailable or HHMS_SKIP_FROZEN_SMOKE=1.
"""
from __future__ import annotations

import ast
import json
import os
import re
import socket
import subprocess
import sys
import time
from pathlib import Path

import pytest

TESTS_DIR = Path(__file__).resolve().parent
BACKEND_ROOT = TESTS_DIR.parent
PROJECT_ROOT = BACKEND_ROOT.parent
SPEC_PATH = BACKEND_ROOT / "packaging" / "HHMS-Server.spec"
VERSION = (PROJECT_ROOT / "VERSION").read_text(encoding="utf-8").strip()


def _spec_source() -> str:
    return SPEC_PATH.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# 1. Spec-file defect regressions (found by executing the real build)
# ---------------------------------------------------------------------------


def test_spec_does_not_use_dunder_file() -> None:
    """PyInstaller exec()s specs without ``__file__``; using it crashes the
    build with NameError (release-blocking defect fixed in Batch 106)."""
    tree = ast.parse(_spec_source())
    offenders = [
        node.lineno
        for node in ast.walk(tree)
        if isinstance(node, ast.Name) and node.id == "__file__"
    ]
    assert not offenders, (
        f"HHMS-Server.spec uses __file__ at line(s) {offenders}; "
        "paths must resolve from SPECPATH instead"
    )
    assert "SPECPATH" in _spec_source()


def test_spec_parses_and_declares_speccomputed_roots() -> None:
    """Spec remains valid Python and derives backend/project roots from
    SPECPATH so it builds from any working directory."""
    tree = ast.parse(_spec_source())
    text = _spec_source()
    assert "Path(os.path.abspath(SPECPATH))" in text
    assert 'collect_submodules("app")' in text


@pytest.mark.parametrize(
    "driver",
    [
        "aiosqlite",                       # production async DBAPI (lazy import)
        "sqlalchemy.dialects.sqlite.aiosqlite",
        "sqlalchemy.dialects.sqlite.pysqlite",
        "pwdlib._argon2",                  # password hashing backend
    ],
)
def test_spec_pins_lazy_dbapi_hidden_imports(driver: str) -> None:
    """SQLAlchemy/pwdlib import dialect DBAPIs lazily at runtime; static
    analysis misses them, so frozen builds crashed on the FIRST database
    request with ModuleNotFoundError until pinned explicitly (Batch 106)."""
    tree = ast.parse(_spec_source())
    literals: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            literals.add(node.value)
    assert driver in literals, f"{driver} missing from spec hidden imports"


def test_client_csproj_version_single_sourced() -> None:
    """The Windows client assembly version must come from the root VERSION
    file (single-source release versioning extended to the C# project)."""
    csproj = (PROJECT_ROOT / "client" / "HHMS.Client" / "HHMS.Client.csproj").read_text(
        encoding="utf-8"
    )
    for tag, expected in (
        ("Version", VERSION),
        ("AssemblyVersion", f"{VERSION}.0"),  # 4-part Win32 version
        ("FileVersion", f"{VERSION}.0"),
    ):
        m = re.search(rf"<{tag}>([^<]+)</{tag}>", csproj)
        assert m, f"<{tag}> missing from HHMS.Client.csproj"
        assert m.group(1).strip() == expected, (
            f"<{tag}>={m.group(1).strip()} out of sync with VERSION ({expected})"
        )


# ---------------------------------------------------------------------------
# 2. Frozen executable smoke test (opt-out only when toolchain absent)
# ---------------------------------------------------------------------------


def _pyinstaller_available() -> bool:
    try:
        subprocess.run(
            [sys.executable, "-m", "PyInstaller", "--version"],
            capture_output=True,
            check=True,
        )
        return True
    except Exception:
        return False


def _free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return int(s.getsockname()[1])


# The spec builds a ONE-FILE executable (EXE() receives a.binaries/a.datas):
# dist/HHMS-Server is the single ~55 MB binary, not a directory.
DIST_EXE = BACKEND_ROOT / "packaging" / "dist" / "HHMS-Server"


@pytest.mark.skipif(
    os.environ.get("HHMS_SKIP_FROZEN_SMOKE") == "1" or not _pyinstaller_available(),
    reason="PyInstaller not installed (or frozen smoke explicitly skipped)",
)
def test_frozen_server_end_to_end_first_run(tmp_path: Path) -> None:
    """Build once per session, then boot the frozen exe on a fresh app root
    and verify the complete first-run release contract."""
    if not DIST_EXE.exists():
        subprocess.run(
            [
                sys.executable, "-m", "PyInstaller", "--noconfirm", "--clean",
                "--distpath", str(BACKEND_ROOT / "packaging" / "dist"),
                "--workpath", str(BACKEND_ROOT / "packaging" / "build"),
                str(SPEC_PATH),
            ],
            cwd=BACKEND_ROOT,
            check=True,
            capture_output=True,
            timeout=900,
        )
    assert DIST_EXE.exists()

    app_root = tmp_path / "clean-machine"
    app_root.mkdir()
    http_port = _free_port()
    env = {
        **os.environ,
        "HHMS_APPLICATION_ROOT": str(app_root),
        "SERVER_PORT": str(http_port),
        "DISCOVERY_ENABLED": "false",
    }
    proc = subprocess.Popen(
        [str(DIST_EXE)], env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True
    )
    base = f"http://127.0.0.1:{http_port}/api/v1"
    try:
        deadline = time.time() + 60
        health: dict | None = None
        while time.time() < deadline:
            if proc.poll() is not None:
                pytest.fail(f"frozen server exited early:\n{proc.stdout.read()[-2000:]}")
            try:
                out = subprocess.run(
                    ["curl", "-sf", f"{base}/health"], capture_output=True, text=True, timeout=5
                )
                if out.returncode == 0:
                    health = json.loads(out.stdout)
                    break
            except Exception:
                pass
            time.sleep(1.0)
        assert health is not None, "frozen server never became healthy"
        assert health["status"] == "healthy"
        assert health["version"] == VERSION

        # Fresh-install contract: migrations ran against the new app root.
        db_file = app_root / "data" / "hhms.sqlite3"
        assert db_file.exists(), "first run did not bootstrap the SQLite database"
        tables = subprocess.run(
            [sys.executable, "-c",
             "import sqlite3,sys;"
             "print(','.join(r[0] for r in sqlite3.connect(sys.argv[1])"
             ".execute(\"select name from sqlite_master where type='table'\")))",
             str(db_file)],
            capture_output=True, text=True, check=True,
        ).stdout.split(",")
        for expected in ("User", "Patient", "alembic_version"):
            assert expected in tables, f"{expected} missing after frozen bootstrap"

        # Release-blocking regression: bad login must be a structured 401
        # (proves aiosqlite + pwdlib/argon2 load inside the frozen exe).
        resp = subprocess.run(
            ["curl", "-s", "-o", "/dev/stdout", "-w", "\n%{http_code}",
             "-X", "POST", f"{base}/auth/login",
             "-H", "Content-Type: application/json",
             "-d", '{"username":"ghost","password":"wrong"}'],
            capture_output=True, text=True, timeout=15,
        )
        body, _, status = resp.stdout.rpartition("\n")
        assert status.strip() == "401", f"login returned {status}: {body}"
        payload = json.loads(body)
        assert payload["error"]["code"] == "AUTHENTICATION_ERROR"
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            proc.kill()
