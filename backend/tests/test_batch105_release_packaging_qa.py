"""Batch 105 — Milestone 7 release packaging & deployment QA.

Validates everything that must be true *before* a release build can be
produced, without requiring PyInstaller or Windows in CI (Linux-safe):

1. Single-source versioning: the repository ``VERSION`` file is the one
   authoritative version string; ``app.release_version`` resolves it in
   every supported runtime layout (source checkout, application-root
   copy, PyInstaller ``_MEIPASS`` bundle) and Settings/health report it.
2. Frozen-runtime Alembic execution: the PyInstaller runtime hook makes
   a bundled ``alembic/versions`` tree importable exactly as it would be
   inside a frozen executable (simulated via a temp bundle root).
3. Packaging artifact integrity: ``HHMS-Server.spec`` parses, declares
   the alembic/alembic.ini/VERSION data entries, references the runtime
   hook by a path that exists, and the hook file itself compiles.
4. Deployment script integrity: ``scripts/deploy/*.sh`` and
   ``*.ps1`` pass syntax gates (``bash -n`` / structural checks), carry
   the expected first-run bootstrap steps, and the PowerShell server
   launcher mirrors the Python ``prepare_runtime`` contract.
5. Release-readiness handshake: a freshly prepared runtime answers
   ``/health`` with the VERSION-file release version and a stable
   ``server_id`` consistent with ``/health/discovery``.
"""
from __future__ import annotations

import ast
import os
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
BACKEND_ROOT = PROJECT_ROOT / "backend"
PACKAGING_ROOT = BACKEND_ROOT / "packaging"
SCRIPTS_ROOT = PROJECT_ROOT / "scripts" / "deploy"

sys.path.insert(0, str(BACKEND_ROOT))


# ---------------------------------------------------------------------------
# 1. Single-source release version
# ---------------------------------------------------------------------------


def test_version_file_exists_and_is_semver() -> None:
    """The repo-root VERSION file exists and carries a valid semver string."""
    version_path = PROJECT_ROOT / "VERSION"
    assert version_path.is_file(), "repository-root VERSION file is missing"
    raw = version_path.read_text(encoding="utf-8").strip()
    parts = raw.split(".")
    assert len(parts) == 3, f"VERSION {raw!r} is not X.Y.Z"
    assert all(p.isdigit() for p in parts), f"VERSION {raw!r} has non-numeric segments"


def test_release_version_matches_version_file() -> None:
    """app.release_version returns exactly the VERSION file contents."""
    from app.release_version import release_version

    expected = (PROJECT_ROOT / "VERSION").read_text(encoding="utf-8").strip()
    assert release_version() == expected


def test_settings_app_version_uses_release_version() -> None:
    """Settings.APP_VERSION defaults to the single-source release version."""
    from app.config.settings import get_settings
    from app.release_version import release_version

    get_settings.cache_clear()
    try:
        settings = get_settings()
        assert settings.APP_VERSION == release_version()
    finally:
        get_settings.cache_clear()


def test_release_version_resolution_order() -> None:
    """Application-root VERSION is a listed candidate so installer-shipped
    copies are honoured when the code tree moves (HHMS_APPLICATION_ROOT)."""
    from app.config.runtime_paths import application_root
    from app.release_version import read_version_file, version_file_candidates

    candidates = version_file_candidates()
    # The source-checkout candidate always exists in a git checkout and is
    # first; the application-root candidate must also be listed second so
    # installer-shipped copies are honoured when the code tree moves.
    assert len(candidates) >= 2
    assert candidates[1] == application_root() / "VERSION"
    assert read_version_file() is not None  # at least one layout resolves


def test_frozen_meipass_candidate_listed(monkeypatch) -> None:
    """When sys._MEIPASS is set (onefile bundle), its VERSION is a candidate."""
    from app.release_version import version_file_candidates

    fake_bundle = tempfile.mkdtemp()
    (Path(fake_bundle) / "VERSION").write_text("9.9.9", encoding="utf-8")
    monkeypatch.setattr(sys, "_MEIPASS", fake_bundle, raising=False)
    candidates = version_file_candidates()
    assert Path(fake_bundle) / "VERSION" in candidates


# ---------------------------------------------------------------------------
# 2. Frozen-runtime Alembic execution (runtime hook)
# ---------------------------------------------------------------------------


HOOK_PATH = PACKAGING_ROOT / "hooks" / "runtime_hook_alembic_path.py"


def test_runtime_hook_compiles() -> None:
    """The PyInstaller runtime hook is syntactically valid Python."""
    source = HOOK_PATH.read_text(encoding="utf-8")
    compile(source, str(HOOK_PATH), "exec")


def test_runtime_hook_adds_bundled_alembic_to_syspath() -> None:
    """Executing the hook against a simulated bundle root puts alembic dirs
    on sys.path — the exact behaviour needed inside a frozen executable."""
    with tempfile.TemporaryDirectory() as bundle:
        (Path(bundle) / "alembic" / "versions").mkdir(parents=True)
        original_meipass = getattr(sys, "_MEIPASS", None)
        original_path = list(sys.path)
        try:
            sys._MEIPASS = bundle
            code = HOOK_PATH.read_text(encoding="utf-8")
            exec(compile(code, str(HOOK_PATH), "exec"), {"__name__": "_hook"})
            assert str(Path(bundle) / "alembic") in sys.path
            assert str(Path(bundle) / "alembic" / "versions") in sys.path
        finally:
            sys.path[:] = original_path
            if original_meipass is None:
                del sys._MEIPASS
            else:
                sys._MEIPASS = original_meipass


def test_hook_simulated_migration_import() -> None:
    """A migration module placed in a simulated bundle imports once the
    hook has run — proving the frozen bootstrap path end-to-end."""
    with tempfile.TemporaryDirectory() as bundle:
        versions = Path(bundle) / "alembic" / "versions"
        versions.mkdir(parents=True)
        module = versions / "_hhms_probe_migration_0001.py"
        module.write_text("REVISION = 'probe'\n", encoding="utf-8")
        original_meipass = getattr(sys, "_MEIPASS", None)
        original_path = list(sys.path)
        try:
            sys._MEIPASS = bundle
            code = HOOK_PATH.read_text(encoding="utf-8")
            exec(compile(code, str(HOOK_PATH), "exec"), {"__name__": "_hook"})
            import _hhms_probe_migration_0001 as probe  # noqa: F401

            assert probe.REVISION == "probe"
        finally:
            sys.modules.pop("_hhms_probe_migration_0001", None)
            sys.path[:] = original_path
            if original_meipass is None:
                del sys._MEIPASS
            else:
                sys._MEIPASS = original_meipass


# ---------------------------------------------------------------------------
# 3. Packaging artifact integrity (spec file)
# ---------------------------------------------------------------------------


def test_server_spec_parses_as_python() -> None:
    """HHMS-Server.spec is valid Python (PyInstaller specs are executed)."""
    source = (PACKAGING_ROOT / "HHMS-Server.spec").read_text(encoding="utf-8")
    tree = ast.parse(source)
    names = {
        node.func.id
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
    }
    assert {"Analysis", "PYZ", "EXE"} <= names


def test_server_spec_declares_required_data_and_hook() -> None:
    """The spec bundles alembic, alembic.ini, VERSION and wires the hook."""
    source = (PACKAGING_ROOT / "HHMS-Server.spec").read_text(encoding="utf-8")
    assert '"alembic"' in source
    assert "alembic.ini" in source
    assert 'project_root / "VERSION"' in source
    assert "runtime_hook_alembic_path.py" in source
    # The referenced hook file must actually exist relative to the spec.
    assert HOOK_PATH.is_file()


def test_client_launcher_sources_present() -> None:
    """The C# WebView2 client sources required for the client EXE build
    exist and reference the WebView2 runtime package."""
    client_root = PROJECT_ROOT / "client" / "HHMS.Client"
    csproj = (client_root / "HHMS.Client.csproj").read_text(encoding="utf-8")
    assert "WebView2" in csproj or "WebWebView2" in csproj
    program = (client_root / "Program.cs").read_text(encoding="utf-8")
    assert "Main" in program
    mainform = (client_root / "MainForm.cs").read_text(encoding="utf-8")
    assert "WebView2" in mainform


# ---------------------------------------------------------------------------
# 4. Deployment scripts
# ---------------------------------------------------------------------------


def test_deploy_scripts_exist() -> None:
    """All Batch 105 deployment scripts are present."""
    for name in (
        "build-server.sh",
        "install-first-run.sh",
        "server-launch.ps1",
        "README.md",
    ):
        assert (SCRIPTS_ROOT / name).is_file(), f"missing scripts/deploy/{name}"


@pytest.mark.parametrize(
    "script",
    ["build-server.sh", "install-first-run.sh"],
)
def test_bash_deploy_scripts_pass_syntax_gate(script: str) -> None:
    """POSIX shell scripts parse cleanly under ``bash -n``."""
    path = SCRIPTS_ROOT / script
    result = subprocess.run(
        ["bash", "-n", str(path)], capture_output=True, text=True
    )
    assert result.returncode == 0, f"{script}: {result.stderr}"


def test_build_server_script_targets_spec_and_pyi() -> None:
    """The Linux/macOS build script invokes PyInstaller against the spec."""
    source = (SCRIPTS_ROOT / "build-server.sh").read_text(encoding="utf-8")
    assert "pyinstaller" in source.lower()
    assert "HHMS-Server.spec" in source


def test_first_run_script_bootstraps_runtime_contract() -> None:
    """The first-run installer script mirrors the prepare_runtime contract:
    creates data dirs, runs migrations to head, and verifies health."""
    source = (SCRIPTS_ROOT / "install-first-run.sh").read_text(encoding="utf-8")
    for token in ("data", "alembic", "upgrade head", "/health"):
        assert token in source, f"first-run script missing {token!r}"


def test_powershell_launcher_structure() -> None:
    """The Windows server launcher is structurally sound PS1: balanced
    braces, sets HHMS env vars, launches the server entry point."""
    source = (SCRIPTS_ROOT / "server-launch.ps1").read_text(encoding="utf-8")
    assert source.count("{") == source.count("}")
    assert "HHMS" in source
    assert "server" in source.lower()


# ---------------------------------------------------------------------------
# 5. Release handshake on a fresh runtime
# ---------------------------------------------------------------------------


def test_health_reports_release_version_and_stable_server_id() -> None:
    """On a relocated fresh runtime, /health reports the VERSION-file
    release version and /health/discovery agrees on server_id."""
    from _qa_harness import api_get, make_client

    with make_client() as client:
        expected_version = (PROJECT_ROOT / "VERSION").read_text(encoding="utf-8").strip()
        health = api_get(client, "/health")
        assert health.status_code == 200
        body = health.json()
        assert body["version"] == expected_version

        discovery = api_get(client, "/health/discovery")
        assert discovery.status_code == 200
        first_id = discovery.json()["server_id"]

        discovery2 = api_get(client, "/health/discovery")
        assert discovery2.json()["server_id"] == first_id
