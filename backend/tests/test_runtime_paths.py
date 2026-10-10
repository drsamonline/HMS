"""Tests for source and packaged runtime path helpers."""
from pathlib import Path

from app.config.runtime_paths import application_root, database_path, data_directory, logs_directory


def test_runtime_paths_are_path_objects() -> None:
    assert isinstance(application_root(), Path)
    assert isinstance(data_directory(), Path)
    assert isinstance(database_path(), Path)
    assert isinstance(logs_directory(), Path)


def test_default_database_location_is_under_data_directory() -> None:
    assert database_path().parent == data_directory()
    assert database_path().name == "hhms.sqlite3"
