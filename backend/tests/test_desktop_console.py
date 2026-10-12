"""Regression tests for the Windows desktop console / data draft saver.

The GUI itself (Tk + pystray) only runs inside packaged Windows builds, so
these tests focus on the cross-platform contract:

* module imports cleanly headless (no Tk display, no tray);
* ``maybe_start_desktop_console`` stays a strict no-op outside frozen Windows;
* ``save_draft_on_exit`` produces a rolling backup via BackupService;
* the server wires the desktop console into its lifecycle (source contract).
"""
from __future__ import annotations

import asyncio
import sqlite3
import sys
from pathlib import Path

import pytest

from app import desktop_console


def test_module_imports_headless() -> None:
    # Importing must never require tkinter/pystray to be usable.
    assert hasattr(desktop_console, "DesktopConsole")
    assert callable(desktop_console.maybe_start_desktop_console)
    assert callable(desktop_console.save_draft_on_exit)


def test_maybe_start_is_noop_off_windows(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(desktop_console, "IS_WINDOWS", False)
    assert desktop_console.maybe_start_desktop_console() is None


def test_maybe_start_is_noop_for_source_runs(monkeypatch: pytest.MonkeyPatch) -> None:
    # Even pretending to be Windows, non-frozen (dev/CI) runs must not open UI.
    monkeypatch.setattr(desktop_console, "IS_WINDOWS", True)
    monkeypatch.delitem(sys.modules, "frozen", raising=False)
    was_frozen = getattr(sys, "frozen", False)
    if was_frozen:  # pragma: no cover - CI is never frozen
        monkeypatch.setattr(sys, "frozen", False, raising=False)
    assert desktop_console.maybe_start_desktop_console() is None


def test_hide_windows_console_noop_off_windows(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(desktop_console, "IS_WINDOWS", False)
    assert desktop_console.hide_windows_console() is False


def test_save_draft_on_exit_creates_rolling_backup(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from app.services.backup import BackupService

    created: list[tuple[str | None, bool]] = []

    class FakeBackupService:
        async def create_backup(self, name=None, *, overwrite=False):
            created.append((name, overwrite))
            return {"name": name, "size_bytes": 0}

    monkeypatch.setattr("app.services.backup.BackupService", FakeBackupService)
    desktop_console.save_draft_on_exit()
    assert created == [("hhms-shutdown-draft", True)]


def test_backup_service_overwrite_stamps_unique_names(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """overwrite=True keeps the requested stem but stamps the suffix so
    repeated shutdown drafts never collide with 'already exists'."""

    from app.config.runtime_paths import backups_directory
    from app.services.backup import BackupService

    # File-backed SQLite runtime like a packaged deployment (Batch 108 shape).
    db_file = tmp_path / "hhms-draft-test.sqlite3"
    sqlite3.connect(db_file).close()
    monkeypatch.setenv("HHMS_APPLICATION_ROOT", str(tmp_path))
    monkeypatch.setenv("DATABASE_URL", f"sqlite+aiosqlite:///{db_file}")
    from app.config.settings import get_settings

    get_settings.cache_clear()
    try:
        service = BackupService()
        first = asyncio.run(service.create_backup("hhms-shutdown-draft", overwrite=True))
        second = asyncio.run(service.create_backup("hhms-shutdown-draft", overwrite=True))
        assert first["name"] != second["name"]
        assert str(first["name"]).startswith("hhms-shutdown-draft-")
        assert (backups_directory() / first["name"]).exists()
        assert (backups_directory() / second["name"]).exists()
    finally:
        get_settings.cache_clear()


def test_server_wires_desktop_console_and_draft_saver() -> None:
    server_src = Path(__file__).resolve().parents[1] / "app" / "server.py"
    text = server_src.read_text(encoding="utf-8")
    assert "maybe_start_desktop_console" in text
    assert "save_draft_on_exit" in text
    # Draft saver must run both on tray exit and on any other process exit.
    assert text.count("save_draft_on_exit()") >= 2


def test_frontend_autosave_module_exists_and_is_wired() -> None:
    root = Path(__file__).resolve().parents[2]
    autosave = root / "frontend" / "js" / "autosave.js"
    assert autosave.exists(), "frontend draft autosave module missing"
    body = autosave.read_text(encoding="utf-8")
    assert "initAutosave" in body and "beforeunload" in body
    app_js = (root / "frontend" / "js" / "app.js").read_text(encoding="utf-8")
    assert "./autosave.js" in app_js and "initAutosave()" in app_js
