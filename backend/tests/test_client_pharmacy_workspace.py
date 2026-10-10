"""Regression tests for the client pharmacy/dispensing workspace."""
from pathlib import Path

def test_pharmacy_module_exists() -> None:
    assert Path(__file__).resolve().parents[2].joinpath("frontend/js/pharmacy.js").exists()
