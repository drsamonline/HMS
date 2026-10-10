"""Regression checks for the client IPD management contract."""
from pathlib import Path


def test_ipd_management_assets_exist():
    root = Path(__file__).parents[2]
    assert (root / "frontend/js/ipd_management.js").exists()
    assert (root / "docs/CLIENT_IPD_MANAGEMENT.md").exists()

