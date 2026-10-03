"""Contract tests for client print renderer batch."""
from pathlib import Path

def test_print_assets_present() -> None:
    root = Path(__file__).resolve().parents[2]
    assert (root / "frontend/js/print.js").exists()
    assert (root / "frontend/css/print.css").exists()
    assert "@page{size:A4 portrait" in (root / "frontend/css/print.css").read_text(encoding="utf-8")
