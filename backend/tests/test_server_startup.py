"""Tests for HHMS standalone server startup helpers."""
from pathlib import Path

from app.config.runtime_paths import config_file_path, secret_key_path
from app.startup import migration_config


def test_secret_and_config_paths_are_local_paths() -> None:
    assert secret_key_path().name == "secret.key"
    assert config_file_path().name == ".env"


def test_migration_config_points_to_existing_project_files() -> None:
    config = migration_config()
    script_location = Path(config.get_main_option("script_location"))
    assert script_location.name == "alembic"
    assert script_location.exists()
