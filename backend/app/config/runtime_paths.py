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
    """Return and create the writable HHMS log directory."""
    path = data_directory() / "logs"
    path.mkdir(parents=True, exist_ok=True)
    return path


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


def config_file_path() -> Path:
    """Return the optional server configuration file path."""
    return application_root() / ".env"


def database_path() -> Path:
    """Return the default SQLite database path."""
    return data_directory() / "hhms.sqlite3"


def secret_key_path() -> Path:
    """Return the persisted local JWT secret path."""
    return data_directory() / "secret.key"

__all__ = [
    "application_root",
    "data_directory",
    "logs_directory",
    "uploads_directory",
    "backups_directory",
    "config_file_path",
    "database_path",
    "secret_key_path",
]
