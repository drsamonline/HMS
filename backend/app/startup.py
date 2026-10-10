"""HHMS server startup/bootstrap helpers."""
from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

from alembic import command
from alembic.config import Config

from app.config.runtime_paths import (
    application_root,
    backups_directory,
    data_directory,
    logs_directory,
    uploads_directory,
)
from app.config.settings import get_settings


def configure_logging() -> None:
    """Configure rotating file logging for the standalone server."""
    settings = get_settings()
    log_dir = logs_directory()
    log_path = log_dir / settings.LOG_FILE_NAME
    level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    if not any(isinstance(h, RotatingFileHandler) and Path(getattr(h, "baseFilename", "")) == log_path for h in root_logger.handlers):
        handler = RotatingFileHandler(log_path, maxBytes=5_000_000, backupCount=3, encoding="utf-8")
        handler.setLevel(level)
        handler.setFormatter(logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s"))
        root_logger.addHandler(handler)


def migration_config() -> Config:
    """Return Alembic configuration for source and packaged deployments."""
    root = application_root()
    # The backend source directory (…/backend) is a stable fallback for
    # installations whose writable data root differs from the code root.
    source_backend = Path(__file__).resolve().parents[1]
    candidates = [
        root / "alembic.ini",
        root / "backend" / "alembic.ini",
        source_backend / "alembic.ini",
    ]
    ini = next((path for path in candidates if path.exists()), candidates[0])
    script_candidates = [
        root / "alembic",
        root / "backend" / "alembic",
        source_backend / "alembic",
    ]
    script_location = next((path for path in script_candidates if path.exists()), script_candidates[0])
    config = Config(str(ini))
    config.set_main_option("script_location", str(script_location))
    return config


def run_pending_migrations() -> None:
    """Apply all pending Alembic migrations before serving requests."""
    command.upgrade(migration_config(), "head")


def prepare_runtime() -> None:
    """Prepare writable runtime directories, logging and database schema."""
    data_directory()
    logs_directory()
    uploads_directory()
    backups_directory()
    configure_logging()
    run_pending_migrations()


__all__ = ["configure_logging", "migration_config", "run_pending_migrations", "prepare_runtime"]
