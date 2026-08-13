"""HHMS runtime filesystem paths for source and packaged deployments."""
from __future__ import annotations

import sys
from pathlib import Path


def application_root() -> Path:
    """Return the directory used as the HHMS application root."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parents[3]


def data_directory() -> Path:
    """Return and create the writable HHMS data directory."""
    path = application_root() / "data"
    path.mkdir(parents=True, exist_ok=True)
    return path


def logs_directory() -> Path:
    """Return and create the writable HHMS logs directory."""
    path = data_directory() / "logs"
    path.mkdir(parents=True, exist_ok=True)
    return path


def database_path() -> Path:
    """Return the default SQLite database path."""
    return data_directory() / "hhms.sqlite3"


def uploads_directory() -> Path:
    """Return and create the writable uploads directory."""
    path = data_directory() / "uploads"
    path.mkdir(parents=True, exist_ok=True)
    return path


def backups_directory() -> Path:
    """Return and create the writable backups directory."""
    path = data_directory() / "backups"
    path.mkdir(parents=True, exist_ok=True)
    return path

__all__ = [
    "application_root",
    "data_directory",
    "logs_directory",
    "database_path",
    "uploads_directory",
    "backups_directory",
]
